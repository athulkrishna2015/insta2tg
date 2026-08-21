#!/usr/bin/env python3
"""insta2tg - mirror Instagram content to a Telegram channel.

Downloads posts/reels/tagged/igtv/stories/highlights from an Instagram
profile with instaloader and uploads them (media + caption) to a Telegram
channel using a Telethon userbot.
"""

import argparse
import asyncio
import json
import os
import re
import shutil
import sys
import tempfile
import time
from itertools import islice
from pathlib import Path

try:
    import instaloader
    from telethon import TelegramClient
except ImportError:
    sys.exit("Missing dependencies. Run: uv sync")

MEDIA_EXT = {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mkv"}
CAPTION_LIMIT = 1024

POST_LIKE = ("posts", "reels", "tagged", "igtv")   # Post objects -> download_post
STORY_LIKE = ("stories", "highlights")             # StoryItem objects -> download_storyitem
ALL_KINDS = POST_LIKE + STORY_LIKE

IDX_RE = re.compile(r"_(\d+)$")


# --------------------------------------------------------------------------- config

def load_env(path: str = ".env") -> None:
    """Tiny .env loader (no external dependency)."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        os.environ.setdefault(key.strip(), val.strip().strip("'\""))


def build_loader(ig_user: str | None) -> instaloader.Instaloader:
    L = instaloader.Instaloader(
        save_metadata=False,
        compress_json=False,
        download_comments=False,
        post_metadata_txt_pattern="",  # caption taken from Post object instead
    )
    if ig_user:
        try:
            L.load_session_from_file(ig_user)
            print(f"[ig] loaded existing session for {ig_user}")
        except FileNotFoundError:
            password = os.environ.get("IG_PASSWORD")
            if password:
                L.login(ig_user, password)
            else:
                L.interactive_login(ig_user)
            print(f"[ig] logged in as {ig_user} (session saved)")
    return L


# --------------------------------------------------------------------------- state

def load_state(path: str) -> dict:
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"uploaded": {}}


def save_state(path: str, state: dict) -> None:
    Path(path).write_text(
        json.dumps(state, indent=2, sort_keys=True), encoding="utf-8"
    )


def mark_seen(state: dict, shortcode: str, ok: bool) -> None:
    # value 0 marks a failed attempt so we don't retry it forever
    state["uploaded"][shortcode] = int(time.time()) if ok else 0


# --------------------------------------------------------------------------- ig fetch

def post_date(post) -> object:
    return getattr(post, "date_utc", None) or post.date


def resolve_since_post(L, value: str):
    """Accept a post URL or bare shortcode; return its upload date."""
    m = re.search(r"(?:p|reel|tv)/([A-Za-z0-9_-]+)", value)
    sc = m.group(1) if m else value.strip().strip("/")
    try:
        post = instaloader.Post.from_shortcode(L.context, sc)
    except instaloader.exceptions.PostNotFoundException:
        sys.exit(f"[ig] --since post '{sc}' not found")
    print(f"[ig] will upload everything newer than {sc} "
          f"({post_date(post):%Y-%m-%d %H:%M})")
    return post_date(post)


def iter_post_like(profile, kind: str):
    if kind == "posts":
        return profile.get_posts()
    if kind == "reels":
        return profile.get_reels()
    if kind == "tagged":
        return profile.get_tagged_posts()
    if kind == "igtv":
        return profile.get_igtv_posts()
    raise ValueError(kind)


def collect_story_items(L, profile, kind: str) -> list:
    """StoryItems from live stories or from highlights. Requires login."""
    items = []
    if kind == "stories":
        for story in L.get_stories(userids=[profile.userid]):
            items.extend(story.get_items())
    else:  # highlights
        for hl in L.get_highlights(profile):
            items.extend(hl.get_items())
    return items


def require_login(L) -> None:
    if L.context.username is None:
        sys.exit("[ig] stories/highlights require login: set IG_USERNAME in .env "
                 "(or run once: uv run instaloader --login <user>)")


def fetch_new_posts(L, target: str, state: dict, kinds: list, scan: int,
                    backfill: int, since_dt=None) -> list:
    try:
        profile = instaloader.Profile.from_username(L.context, target)
    except instaloader.exceptions.ProfileNotExistsException:
        sys.exit(f"[ig] profile '{target}' does not exist")
    except instaloader.exceptions.LoginRequiredException:
        sys.exit("[ig] login required (private profile / rate limit). "
                 "Set IG_USERNAME in .env or run: instaloader --login <user>")

    known = state["uploaded"]
    first_run = not known
    new = []

    for kind in [k for k in kinds if k in POST_LIKE]:
        posts = list(islice(iter_post_like(profile, kind), scan))
        fresh = [p for p in posts if p.shortcode not in known]
        if since_dt is not None:
            # --since overrides first-run/backfill logic for feed content
            fresh = [p for p in fresh if post_date(p) > since_dt]
        elif first_run and backfill == 0:
            # first run: record history, upload nothing (use --backfill N to change)
            for p in posts:
                mark_seen(state, p.shortcode, True)
            print(f"[ig] {kind}: marked {len(posts)} existing as seen")
            fresh = []
        elif backfill >= 0:
            fresh = fresh[:backfill]
        new.extend(fresh)

    for kind in [k for k in kinds if k in STORY_LIKE]:
        require_login(L)
        items = collect_story_items(L, profile, kind)
        fresh = [i for i in items if i.shortcode not in known]
        if first_run and since_dt is None:
            for i in items:
                mark_seen(state, i.shortcode, True)
            print(f"[ig] {kind}: marked {len(items)} existing as seen")
            fresh = []
        new.extend(fresh)

    return sorted(new, key=post_date)  # oldest first -> chronological channel


def post_link(post) -> str:
    if isinstance(post, instaloader.StoryItem):
        return (f"https://www.instagram.com/stories/"
                f"{post.owner_username}/{post.shortcode}/")
    return f"https://www.instagram.com/p/{post.shortcode}/"


def build_caption(post) -> str:
    link = post_link(post)
    cap = (post.caption or "").strip()
    if not cap:
        return link
    room = CAPTION_LIMIT - len(link) - 2
    if len(cap) > room:
        cap = cap[:room].rstrip() + "…"
    return f"{cap}\n\n{link}"


def collect_media(folder: Path) -> list[Path]:
    files = [p for p in folder.iterdir() if p.suffix.lower() in MEDIA_EXT]

    def order(p: Path):
        m = IDX_RE.search(p.stem)
        return (int(m.group(1)) if m else -1, p.name)

    return sorted(files, key=order)


# --------------------------------------------------------------------------- upload

async def upload_post(tg, channel, media: list[Path], caption: str) -> None:
    paths = [str(f) for f in media]
    await tg.send_file(channel, paths, caption=caption, supports_streaming=True)


async def handle_post(tg, channel, post, state, args) -> None:
    sc = post.shortcode
    tmp = Path(tempfile.mkdtemp(prefix=f"i2t_{sc}_", dir="tmp_downloads"))
    try:
        print(f"[dl] {sc} ({post_date(post):%Y-%m-%d %H:%M}) ...")
        if isinstance(post, instaloader.StoryItem):
            L.download_storyitem(post, target=tmp)
        else:
            L.download_post(post, target=tmp)

        media = collect_media(tmp)
        if not media:
            print(f"[!] no media downloaded for {sc}, skipping")
            mark_seen(state, sc, False)
            return

        caption = build_caption(post)
        await upload_post(tg, channel, media, caption)
        mark_seen(state, sc, True)
        print(f"[tg] uploaded {sc} ({len(media)} file(s))")
    except Exception as e:
        print(f"[!] failed on {sc}: {e}")
        mark_seen(state, sc, False)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        save_state(args.state, state)
        time.sleep(args.delay)


# --------------------------------------------------------------------------- main

async def run(args) -> None:
    load_env()

    api_id = args.api_id or os.environ.get("TG_API_ID")
    api_hash = args.api_hash or os.environ.get("TG_API_HASH")
    channel = args.channel or os.environ.get("TG_CHANNEL")
    target = args.target or os.environ.get("IG_TARGET")

    if not (api_id and api_hash and channel and target):
        sys.exit("Set TG_API_ID, TG_API_HASH, TG_CHANNEL, IG_TARGET "
                 "(in .env or via CLI flags). See .env.example")

    Path("tmp_downloads").mkdir(exist_ok=True)
    state = load_state(args.state)
    L = build_loader(os.environ.get("IG_USERNAME"))

    kinds = [k.strip().lower() for k in args.content.split(",") if k.strip()]
    bad = [k for k in kinds if k not in ALL_KINDS]
    if bad:
        sys.exit(f"[!] unknown content type(s): {', '.join(bad)}\n"
                 f"    choose from: {', '.join(ALL_KINDS)}")
    print(f"[ig] mirroring: {', '.join(kinds)}")

    since_dt = resolve_since_post(L, args.since) if args.since else None

    tg = None
    if not args.dry_run:
        tg = TelegramClient(args.session, int(api_id), api_hash)
        await tg.start()  # asks phone/code on first run, then reuses session
        channel = await tg.get_entity(channel)
        print(f"[tg] connected as {(await tg.get_me()).username}")

    while True:
        new = fetch_new_posts(L, target, state, kinds, args.scan,
                              args.backfill, since_dt=since_dt)
        if new:
            print(f"[ig] {len(new)} post(s) to upload")
        for post in new:
            if args.dry_run:
                cap = (post.caption or "").replace("\n", " ")[:60]
                print(f"[dry] {post.shortcode} {post_date(post):%Y-%m-%d} | {cap}")
                mark_seen(state, post.shortcode, True)
                save_state(args.state, state)
            else:
                await handle_post(tg, channel, post, state, args)

        if not args.loop:
            break
        print(f"...sleeping {args.interval}s")
        await asyncio.sleep(args.interval)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Mirror Instagram posts to a Telegram channel")
    p.add_argument("--target", help="Instagram username (default: IG_TARGET)")
    p.add_argument("--channel", help="Telegram channel @name or id (default: TG_CHANNEL)")
    p.add_argument("--api-id", dest="api_id", help="Telegram api_id (default: TG_API_ID)")
    p.add_argument("--api-hash", dest="api_hash", help="Telegram api_hash (default: TG_API_HASH)")
    p.add_argument("--session", default="insta2tg", help="Telethon session name (default: insta2tg)")
    p.add_argument("--state", default="state.json", help="state file path (default: state.json)")
    p.add_argument("--content", default="posts",
                   help="comma-separated content to mirror: posts,reels,tagged,igtv,stories,highlights "
                        "(default: posts). stories/highlights need IG login")
    p.add_argument("--loop", action="store_true", help="keep checking for new posts forever")
    p.add_argument("--interval", type=int, default=900, help="poll interval seconds when --loop (default: 900)")
    p.add_argument("--scan", type=int, default=30, help="how many newest posts to check each cycle (default: 30)")
    p.add_argument("--backfill", type=int, default=0,
                   help="on first run upload the N most recent posts instead of none (-1 = all scanned)")
    p.add_argument("--since", metavar="URL_OR_SHORTCODE",
                   help="upload every post published after this post (URL or shortcode)")
    p.add_argument("--delay", type=int, default=3, help="seconds between uploads (default: 3)")
    p.add_argument("--dry-run", action="store_true", help="list what would be posted, without uploading")
    return p.parse_args()


if __name__ == "__main__":
    try:
        asyncio.run(run(parse_args()))
    except KeyboardInterrupt:
        print("\nbye")
