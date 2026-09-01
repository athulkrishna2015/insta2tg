"""Local tests - no Instagram, no Telegram. Run: uv run python tests/test_local.py"""

import asyncio
import os
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from insta2tg.caption import CAPTION_LIMIT, enrich_caption          # noqa: E402
from insta2tg.config import human_size                              # noqa: E402
from insta2tg.fetch import fetch_new_items                          # noqa: E402
from insta2tg.state import load_state                               # noqa: E402
from insta2tg.telegram import finish_item, prepare_item             # noqa: E402

PASS = 0


def ok(cond, name):
    global PASS
    if not cond:
        print(f"FAIL  {name}")
        sys.exit(1)
    PASS += 1
    print(f"ok    {name}")


def cap_args(**kw):
    d = dict(geotags=False, comments=False, no_source=False, append_text="")
    d.update(kw)
    return SimpleNamespace(**d)


def item(sc, days=0, caption="cap"):
    return SimpleNamespace(
        shortcode=sc, caption=caption,
        date_utc=datetime.now(timezone.utc) - timedelta(days=days))


# ---------------------------------------------------------------- helpers --
ok(human_size(512) == "512 B", "human_size B")
ok(human_size(2048) == "2.0 KB", "human_size KB")
ok(human_size(3 * 1024 ** 2) == "3.0 MB", "human_size MB")

# ---------------------------------------------------------------- captions -
it = item("AbC123", caption="hello")
out = enrich_caption(it, cap_args())
ok(out == "hello\n\nhttps://www.instagram.com/p/AbC123/", "caption keeps link")

out = enrich_caption(it, cap_args(no_source=True))
ok(out == "hello", "--no-source drops link")

out = enrich_caption(it, cap_args(append_text="via @chan"))
ok(out.endswith("via @chan\n\nhttps://www.instagram.com/p/AbC123/")
   and out.startswith("hello"), "--append-text before link")

out = enrich_caption(it, cap_args(no_source=True, append_text="via @chan"))
ok(out == "hello\n\nvia @chan", "--no-source + --append-text")

long = "x" * (CAPTION_LIMIT + 50)
out = enrich_caption(item("AbC123", caption=long), cap_args())
ok(len(out) <= CAPTION_LIMIT and "…" in out, "truncation to 1024 (with link)")
out = enrich_caption(item("AbC123", caption=long), cap_args(no_source=True))
ok(len(out) <= CAPTION_LIMIT and out.endswith("…"),
   "truncation to 1024 (no source)")

# ------------------------------------------------------------------- fetch -
import insta2tg.fetch as F                                            # noqa: E402

items = [item("aaa", 30), item("bbb", 20), item("ccc", 10)]
orig_build_streams = F.build_streams
F.build_streams = lambda *a, **k: [{"label": "t/posts", "items": items,
                                    "kind": "post"}]
try:
    st = {"uploaded": {}}
    got, _ = fetch_new_items(None, ["t"], st, ["posts"], 10, 0,
                             lambda i: True, lambda i: True)
    ok(got == [] and set(st["uploaded"]) == {"aaa", "bbb", "ccc"},
       "first run marks everything seen, posts nothing")

    st = {"uploaded": {"bbb": 1}}
    got, _ = fetch_new_items(None, ["t"], st, ["posts"], 10, 0,
                             lambda i: True, lambda i: True)
    ok([i.shortcode for i in got] == [], "backfill 0 -> nothing on later runs")

    got, _ = fetch_new_items(None, ["t"], st, ["posts"], 10, 1,
                             lambda i: True, lambda i: True)
    ok([i.shortcode for i in got] == ["aaa"], "backfill 1")

    got, _ = fetch_new_items(None, ["t"], st, ["posts"], 10, -1,
                             lambda i: True, lambda i: True)
    ok([i.shortcode for i in got] == ["aaa", "ccc"],
       "backfill -1 -> all unseen, oldest first")

    since = datetime.now(timezone.utc) - timedelta(days=15)
    got, _ = fetch_new_items(None, ["t"], st, ["posts"], 10, 0,
                             lambda i: True, lambda i: True, since_dt=since)
    ok([i.shortcode for i in got] == ["ccc"], "--since filters older")

    st = {"uploaded": {"ccc": 1}}
    got, _ = fetch_new_items(None, ["t"], st, ["posts"], 10, 0,
                             lambda i: True, lambda i: True, since_dt=since)
    ok([i.shortcode for i in got] == [], "seen item skipped even with --since")

    got, _ = fetch_new_items(None, ["t"], st, ["posts"], 10, 0,
                             lambda i: True, lambda i: True, since_dt=since,
                             ignore_seen=True)
    ok([i.shortcode for i in got] == ["ccc"],
       "--ignore-seen bypasses history (still respects --since)")

    # --resume tests (non-first-run: state already has some uploaded items)
    st = {"uploaded": {"aaa": 1}, "resume": {}}
    resume_ts = (datetime.now(timezone.utc) - timedelta(days=25)).timestamp()
    got, _ = fetch_new_items(None, ["t"], st, ["posts"], 10, -1,
                             lambda i: True, lambda i: True,
                             resume_dates={"t": datetime.fromtimestamp(resume_ts, tz=timezone.utc)})
    ok([i.shortcode for i in got] == ["bbb", "ccc"],
       "--resume filters items older than last upload")
finally:
    F.build_streams = orig_build_streams

# ------------------------------------------------------- download / upload -
class FakeL:
    def __init__(self, files=3, delay=0.0):
        self.files, self.delay = files, delay
        self.events = []

    def download_post(self, it, target):
        self.events.append(("dl_start", it.shortcode, time.monotonic()))
        time.sleep(self.delay)
        for n in range(self.files):
            ext = ".mp4" if n == self.files - 1 else ".jpg"
            (Path(target) / f"2026_01_01_{n}{ext}").write_bytes(b"x" * 100)
        return True

    download_storyitem = download_post


class FakeTG:
    def __init__(self, delay=0.0):
        self.delay = delay
        self.sent = []
        self.events = []

    async def send_file(self, channel, files, caption="", supports_streaming=True):
        self.events.append(("ul_start", len(self.sent), time.monotonic()))
        await asyncio.sleep(self.delay)
        self.sent.append((list(files), caption))
        self.events.append(("ul_end", len(self.sent) - 1, time.monotonic()))


def dl_args():
    return SimpleNamespace(no_videos=False, no_pictures=False,
                           no_video_thumbnails=False, slide=None,
                           geotags=False, comments=False, no_source=False,
                           append_text="")


async def test_stages():
    with tempfile.TemporaryDirectory() as td:
        os.chdir(td)
        (Path("tmp_downloads")).mkdir()
        L = FakeL(files=3)
        prepped = prepare_item(L, item("xyz1", caption="hi"), dl_args())
        ok(len(prepped["media"]) == 3 and prepped["size"] == 300
           and prepped["caption"].startswith("hi"),
           "prepare downloads, collects media, builds caption")

        state = load_state("state.json")
        tg = FakeTG()
        fin_args = SimpleNamespace(ignore_seen=False, delay=0,
                                   state="state.json")
        ok(await finish_item(tg, None, prepped, state, fin_args),
           "upload succeeds")
        ok(state["uploaded"]["xyz1"] > 0, "success recorded as seen")
        ok(not Path("tmp_downloads").exists()
           or not any(Path("tmp_downloads").iterdir()), "temp dir cleaned")

        empty = {"sc": "emp", "tmp": Path(tempfile.mkdtemp(dir="tmp_downloads")),
                 "media": [], "size": 0, "caption": ""}
        ok(not await finish_item(tg, None, empty, state, fin_args),
           "no-media item reported as skipped")

        prepped2 = prepare_item(FakeL(), item("xyz2"), dl_args())
        await finish_item(tg, None, prepped2, state,
                          SimpleNamespace(ignore_seen=True, delay=0,
                                          state="state.json"))
        ok("xyz2" not in state["uploaded"], "--ignore-seen records nothing")


async def test_pipeline():
    from insta2tg.runner import mirror_items
    with tempfile.TemporaryDirectory() as td:
        os.chdir(td)
        (Path("tmp_downloads")).mkdir()
        L = FakeL(files=2, delay=0.15)
        tg = FakeTG(delay=0.35)
        state = {"uploaded": {}}
        args = SimpleNamespace(**{**vars(dl_args()),
                                  "ignore_seen": True, "delay": 0,
                                  "state": "state.json", "channel": "@test"})
        news = [item("p1"), item("p2"), item("p3")]
        sc_to_target = {"p1": "t", "p2": "t", "p3": "t"}
        await mirror_items(tg, None, L, news, state, args, sc_to_target)

        ok(len(tg.sent) == 3, "pipeline uploaded all 3")
        ev = {e[0]: e for e in L.events}
        starts = {sc: t for _, sc, t in L.events}
        ends = {}
        for kind, idx, t in tg.events:
            if kind == "ul_end":
                ends[idx] = t
        # overlap: download of item N+1 must begin before upload of N finished
        overlap = all(starts[f"p{i + 2}"] < ends[i] for i in range(2))
        ok(overlap, "download overlaps previous upload")


asyncio.run(test_stages())
asyncio.run(test_pipeline())

print(f"\nall {PASS} checks passed")
