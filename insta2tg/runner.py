"""Main orchestration loop."""

import asyncio
import os
from pathlib import Path

from telethon import TelegramClient

from .config import load_env, log, set_quiet
from .fetch import fetch_new_items, post_date, resolve_since_post
from .filters import build_filter
from .session import build_loader
from .state import load_state, mark_seen, save_state
from .streams import ALL_KINDS
from .targets import expand_targets
from .telegram import handle_item, resolve_channel


async def run(args) -> None:
    set_quiet(args.quiet)
    load_env()

    api_id = os.environ.get("TG_API_ID")
    api_hash = os.environ.get("TG_API_HASH")

    kinds = [k.strip().lower() for k in args.content.split(",") if k.strip()]
    bad = [k for k in kinds if k not in ALL_KINDS]
    if bad:
        raise SystemExit(f"[!] unknown content type(s): {', '.join(bad)}\n"
                         f"    choose from: {', '.join(ALL_KINDS)}")

    targets = expand_targets(args.targets)
    if not targets:
        raise SystemExit("[!] no targets given")

    if not args.dry_run:
        if not (api_id and api_hash and args.channel):
            raise SystemExit("Set TG_API_ID/TG_API_HASH in .env and pass "
                             "--channel (or use --dry-run)")

    Path("tmp_downloads").mkdir(exist_ok=True)
    state = load_state(args.state)
    L = build_loader(args)

    window = args.count if args.count is not None else args.scan
    since_dt = resolve_since_post(L, args.since) if args.since else None
    post_filter = build_filter(args.post_filter)
    story_filter = build_filter(args.storyitem_filter)

    tg = None
    channel = None
    if not args.dry_run:
        tg = TelegramClient(args.tg_session, int(api_id), api_hash)
        await tg.start()  # asks phone/code on first run, then reuses session
        channel = await resolve_channel(tg, args.channel)
        me = await tg.get_me()
        log(f"[tg] connected as {me.username} -> {args.channel}")

    while True:
        new = fetch_new_items(L, targets, state, kinds, window, args.backfill,
                              post_filter, story_filter, since_dt=since_dt)
        if new:
            log(f"[ig] {len(new)} item(s) to upload")
        for item in new:
            if args.dry_run:
                cap = (item.caption or "").replace("\n", " ")[:60]
                log(f"[dry] {item.shortcode} {post_date(item):%Y-%m-%d} | {cap}")
                mark_seen(state, item.shortcode, True)
                save_state(args.state, state)
            else:
                await handle_item(tg, channel, L, item, state, args)

        if not args.loop:
            break
        log(f"...sleeping {args.interval}s")
        await asyncio.sleep(args.interval)
