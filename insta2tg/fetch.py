"""Item metadata helpers and the new-item fetch pipeline."""

import re

import instaloader

from .config import log
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
    except instaloader.exceptions.PostNotFoundException:
        raise SystemExit(f"[ig] --since post '{sc}' not found")
    log(f"[ig] will upload everything newer than {sc} "
        f"({post_date(post):%Y-%m-%d %H:%M})")
    return post_date(post)


def fetch_new_items(L, targets, state, kinds, window, backfill,
                    post_filter, story_filter, since_dt=None) -> list:
    known = state["uploaded"]
    first_run = not known
    new = []

    for stream in build_streams(L, targets, kinds, window):
        flt = story_filter if stream["kind"] == "storyitem" else post_filter
        try:
            items = [i for i in stream["items"] if flt(i)]
        except Exception as e:
            log(f"[!] stream {stream['label']} failed: {e}")
            continue

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
        new.extend(fresh)

    return sorted(new, key=lambda i: post_date(i) or 0)  # oldest first
