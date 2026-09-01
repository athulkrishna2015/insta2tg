"""Main orchestration loop."""

import asyncio
import os
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import instaloader
from telethon import TelegramClient

from .config import load_env, log, set_quiet, warn
from .fetch import fetch_new_items, post_date, resolve_since_post
from .filters import build_filter
from .session import build_loader
from .state import file_hash, load_dp, load_resume, load_state, mark_seen, save_dp, save_state
from .streams import ALL_KINDS
from .targets import expand_targets
from .telegram import finish_item, prepare_item, resolve_channel


def _dur(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h{m:02d}m{s:02d}s"
    if m:
        return f"{m}m{s:02d}s"
    return f"{s}s"


def _download_dp(L, profile, tmp_dir) -> Path | None:
    """Download profile picture to tmp_dir. Returns path or None on failure."""
    try:
        url = profile.profile_pic_url
        if not url:
            return None
        import urllib.request
        ext = ".jpg"
        if ".png" in url:
            ext = ".png"
        out = Path(tmp_dir) / f"dp_{profile.username}{ext}"
        urllib.request.urlretrieve(url, out)
        if out.exists() and out.stat().st_size > 0:
            return out
        return None
    except Exception as e:
        warn(f"[!] dp download failed for {profile.username}: {e}")
        return None


async def _upload_dp(tg, channel, L, target, state, args) -> bool:
    """Check if profile picture changed (hash-based) and upload if needed."""
    chan_key = args.channel
    try:
        profile = instaloader.Profile.from_username(L.context, target)
        url = profile.profile_pic_url
        if not url:
            return False

        # download current dp to compute hash
        log(f"[dp] {target}: checking profile picture...")
        tmp = Path(tempfile.mkdtemp(prefix=f"i2t_dp_{target}_", dir="tmp_downloads"))
        try:
            dp_path = await asyncio.to_thread(_download_dp, L, profile, tmp)
            if not dp_path:
                return False

            # compute hash and compare with stored
            current_hash = file_hash(dp_path)
            last_dp = load_dp(state, chan_key, target)
            if last_dp and last_dp.get("hash") == current_hash:
                return False  # unchanged

            log(f"[dp] {target}: profile picture changed, uploading...")
            caption = f"📷 New profile picture for {target}"
            await tg.send_file(channel, str(dp_path), caption=caption)
            log(f"[tg] uploaded dp for {target}")

            save_dp(state, chan_key, target, current_hash)
            save_state(args.state, state)
            return True
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            await asyncio.sleep(args.delay)
    except Exception as e:
        warn(f"[!] dp upload failed for {target}: {e}")
        return False


async def mirror_items(tg, channel, L, new, state, args, sc_to_target) -> None:
    """Download and upload overlap: while one item is uploading to Telegram,
    the next one is already downloading from Instagram.

    Downloads stay sequential (one worker thread); uploads stay sequential;
    the two stages run concurrently with backpressure (queue size 1)."""
    q: asyncio.Queue = asyncio.Queue(maxsize=1)
    stats = {"uploaded": 0, "skipped": 0, "failed": 0}
    t0 = time.monotonic()
    chan_key = args.channel

    async def produce() -> None:
        for item in new:
            try:
                prepped = await asyncio.to_thread(prepare_item, L, item, args)
                prepped["_item"] = item
                await q.put(prepped)
            except Exception as e:
                warn(f"[!] download failed on {item.shortcode}: {e}")
                stats["failed"] += 1
                if not args.ignore_seen:
                    mark_seen(state, item.shortcode, False)
                    save_state(args.state, state)
        await q.put(None)                      # sentinel

    async def consume() -> None:
        while True:
            prepped = await q.get()
            if prepped is None:
                break
            ok = await finish_item(tg, channel, prepped, state, args,
                                   sc_to_target, chan_key)
            if ok:
                stats["uploaded"] += 1
            elif prepped["media"]:
                stats["failed"] += 1
            else:
                stats["skipped"] += 1

    prod = asyncio.create_task(produce())
    cons = asyncio.create_task(consume())
    try:
        await cons
        dt = time.monotonic() - t0
        log(f"[✓] {stats['uploaded']}/{len(new)} uploaded, "
            f"{stats['skipped']} skipped, {stats['failed']} failed "
            f"in {_dur(dt)}")
    finally:
        prod.cancel()
        try:
            await prod
        except asyncio.CancelledError:
            pass


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

    # build resume date lookup per instagram source target
    resume_dates = None
    if args.resume:
        resume_dates = {}
        for t in targets:
            rd = load_resume(state, args.channel, t.value)
            if rd is not None:
                resume_dates[t.value] = datetime.fromtimestamp(rd, tz=timezone.utc)
                log(f"[ig] resume {t.value}: last upload @ "
                    f"{resume_dates[t.value]:%Y-%m-%d %H:%M}")

    tg = None
    channel = None
    if not args.dry_run:
        tg = TelegramClient(args.tg_session, int(api_id), api_hash)
        await tg.start()  # asks phone/code on first run, then reuses session
        channel = await resolve_channel(tg, args.channel)
        me = await tg.get_me()
        log(f"[tg] connected as {me.username} -> {args.channel}")

    while True:
        new, sc_to_target = fetch_new_items(
            L, targets, state, kinds, window, args.backfill,
            post_filter, story_filter, since_dt=since_dt,
            ignore_seen=args.ignore_seen, resume_dates=resume_dates)
        if new:
            log(f"[ig] {len(new)} item(s) to upload")
        for item in new:
            if args.dry_run:
                cap = (item.caption or "").replace("\n", " ")[:60]
                log(f"[dry] {item.shortcode} {post_date(item):%Y-%m-%d} | {cap}")
                if not args.ignore_seen:
                    mark_seen(state, item.shortcode, True)
                    save_state(args.state, state)

        if new and not args.dry_run:
            await mirror_items(tg, channel, L, new, state, args, sc_to_target)

        # check for dp changes if --dp flag is set
        if args.dp and not args.dry_run:
            for t in targets:
                if t.kind == "profile":
                    await _upload_dp(tg, channel, L, t.value, state, args)

        if not args.loop:
            break
        log(f"...sleeping {args.interval}s")
        await asyncio.sleep(args.interval)
