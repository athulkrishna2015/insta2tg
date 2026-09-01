"""Item metadata helpers and the new-item fetch pipeline."""

import re

import instaloader

from .config import debug, log
from .state import mark_seen
from .streams import build_streams

SHORTCODE_RE = re.compile(r"(?:p|reel|tv)/([A-Za-z0-9_-]+)")


def post_date(item) -> object:
    return getattr(item, "date_utc", None) or getattr(item, "date", None)


def post_link(item) -> str:
    if isinstance(item, instaloader.StoryItem):
        return (f"https://www.instagram.com/stories/"
                f"{item.owner_username}/{item.shortcode}/")
    return f"https://www.instagram.com/p/{item.shortcode}/"


def resolve_since_post(L, value: str):
    m = SHORTCODE_RE.search(value)
    sc = m.group(1) if m else value.strip().strip("/")
    try:
        post = instaloader.Post.from_shortcode(L.context, sc)
    except (instaloader.exceptions.PostChangedException,
            instaloader.exceptions.ConnectionException,
            Exception) as e:
        raise SystemExit(f"[ig] --since post '{sc}' not found or unavailable: {e}")
    log(f"[ig] will upload everything newer than {sc} "
        f"({post_date(post):%Y-%m-%d %H:%M})")
    return post_date(post)


def _base_target(label: str) -> str:
    """Extract the base target from a stream label (strip /kind suffix)."""
    return label.split("/")[0]


def fetch_new_items(L, targets, state, kinds, window, backfill,
                    post_filter, story_filter, since_dt=None,
                    ignore_seen=False, resume_dates=None) -> tuple:
    known = state["uploaded"]
    first_run = not known
    new = []
    sc_to_target: dict[str, str] = {}
    debug(f"[fetch] targets={targets}, kinds={kinds}, window={window}, backfill={backfill}")
    debug(f"[fetch] since_dt={since_dt}, ignore_seen={ignore_seen}, resume_dates={resume_dates}")
    debug(f"[fetch] known shortcodes: {list(known.keys())}")

    for stream in build_streams(L, targets, kinds, window):
        base = _base_target(stream["label"])
        flt = story_filter if stream["kind"] == "storyitem" else post_filter
        try:
            items = [i for i in stream["items"] if flt(i)]
        except Exception as e:
            log(f"[!] stream {stream['label']} failed: {e}")
            continue

        for i in items:
            sc_to_target[i.shortcode] = base

        if ignore_seen:
            fresh = list(items)
        else:
            fresh = [i for i in items if i.shortcode not in known]
            if since_dt is not None:
                fresh = [i for i in fresh
                         if post_date(i) and post_date(i) > since_dt]
            elif first_run and backfill == 0:
                for i in items:
                    mark_seen(state, i.shortcode, True)
                log(f"[ig] {stream['label']}: marked {len(items)} existing as seen")
                fresh = []
            elif backfill >= 0:
                fresh = fresh[:backfill]

        # --resume: filter out items older than the recorded resume point
        if resume_dates and base in resume_dates:
            resume_dt = resume_dates[base]
            fresh = [i for i in fresh
                     if post_date(i) and post_date(i) > resume_dt]
            log(f"[ig] {stream['label']}: resume from "
                f"{resume_dt:%Y-%m-%d %H:%M}, {len(fresh)} newer item(s)")

        if since_dt is not None and ignore_seen:
            fresh = [i for i in fresh
                     if post_date(i) and post_date(i) > since_dt]
        new.extend(fresh)

    new.sort(key=lambda i: post_date(i) or 0)  # oldest first
    return new, sc_to_target
