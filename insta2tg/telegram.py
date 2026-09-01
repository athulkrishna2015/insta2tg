"""Telegram side: entity resolution (name or id) and item upload."""

import asyncio
import re
import shutil
import tempfile
import time
from pathlib import Path

from telethon import TelegramClient, errors
from telethon.tl.types import PeerChannel, PeerChat

import instaloader

from .caption import enrich_caption
from .config import human_size, log, warn
from .fetch import post_date
from .media import collect_media
from .state import mark_seen, save_resume, save_state

NUM_RE = re.compile(r"^-?\d+$")


async def resolve_channel(tg: TelegramClient, value: str):
    """Accept @username or a channel id: raw 123..., marked -100... or legacy -n."""
    v = value.strip()
    if not NUM_RE.match(v):
        return await tg.get_entity(v)

    cid = int(v)
    ids = [cid]
    if cid <= -10**12:                            # marked -100... -> also try raw
        ids.append(cid + 10**12)                  # -100123... -> -123...
    try:
        return await tg.get_entity(cid)               # marked id (-100...)
    except (ValueError, errors.RPCError):
        pass
    for i in ids:
        for peer in (PeerChannel(abs(i)), PeerChat(abs(i))):
            try:
                return await tg.get_entity(peer)      # raw/legacy id from cache
            except (ValueError, errors.RPCError):
                continue
    async for d in tg.iter_dialogs():                 # last resort: scan dialogs
        if d.id in ids:
            return d.entity
    raise SystemExit(
        f"[tg] cannot resolve channel '{value}'. Use an @name, the marked "
        f"-100... id, or forward any message of that channel to yourself "
        f"once so it lands in the session cache.")


def prepare_item(L, item, args) -> dict:
    """Blocking download stage: fetch one item's media into a temp dir.

    Runs in a worker thread (see runner.mirror_items) so it can overlap
    with the Telegram upload of the previous item."""
    sc = item.shortcode
    tmp = Path(tempfile.mkdtemp(prefix=f"i2t_{sc}_", dir="tmp_downloads"))
    try:
        log(f"[dl] {sc} ({post_date(item):%Y-%m-%d %H:%M}) downloading ...")
        if isinstance(item, instaloader.StoryItem):
            L.download_storyitem(item, target=tmp)
        else:
            L.download_post(item, target=tmp)
        media = collect_media(tmp, args)
        size = sum(p.stat().st_size for p in media)
        log(f"[dl] {sc} ready - {len(media)} file(s), {human_size(size)}")
        return {"sc": sc, "tmp": tmp, "media": media, "size": size,
                "caption": enrich_caption(item, args)}
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


async def finish_item(tg, channel, prepped: dict, state, args,
                       sc_to_target: dict | None = None, chan_key: str = "") -> bool:
    """Async upload stage: send a prepared item and record/clean up."""
    sc = prepped["sc"]
    record = not args.ignore_seen
    t0 = time.monotonic()
    try:
        if not prepped["media"]:
            warn(f"[!] no media for {sc} (filtered or empty), skipping")
            if record:
                mark_seen(state, sc, False)
            return False

        await tg.send_file(channel, [str(f) for f in prepped["media"]],
                           caption=prepped["caption"],
                           supports_streaming=True)
        dt = time.monotonic() - t0
        log(f"[tg] uploaded {sc} - {len(prepped['media'])} file(s), "
            f"{human_size(prepped['size'])} in {dt:.1f}s")
        if record:
            mark_seen(state, sc, True)
            # save resume point immediately after marking as seen
            if sc_to_target and chan_key:
                target = sc_to_target.get(sc)
                if target:
                    item = prepped.get("_item")
                    item_date = post_date(item) if item else None
                    date_ts = int(item_date.timestamp()) if item_date else int(time.time())
                    save_resume(state, chan_key, target, sc, date_ts)
        return True
    except Exception as e:
        warn(f"[!] upload failed on {sc}: {e}")
        if record:
            mark_seen(state, sc, False)
        return False
    finally:
        shutil.rmtree(prepped["tmp"], ignore_errors=True)
        save_state(args.state, state)
        await asyncio.sleep(args.delay)
