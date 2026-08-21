"""Telegram side: entity resolution (name or id) and item upload."""

import re
import shutil
import tempfile
import time
from pathlib import Path

from telethon import TelegramClient, errors
from telethon.tl.types import PeerChannel, PeerChat

import instaloader

from .caption import enrich_caption
from .config import log
from .fetch import post_date
from .media import collect_media
from .state import mark_seen, save_state

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


async def handle_item(tg, channel, L, item, state, args) -> None:
    sc = item.shortcode
    tmp = Path(tempfile.mkdtemp(prefix=f"i2t_{sc}_", dir="tmp_downloads"))
    try:
        log(f"[dl] {sc} ({post_date(item):%Y-%m-%d %H:%M}) ...")
        if isinstance(item, instaloader.StoryItem):
            L.download_storyitem(item, target=tmp)
        else:
            L.download_post(item, target=tmp)

        media = collect_media(tmp, args)
        if not media:
            log(f"[!] no media for {sc} (filtered or empty), skipping")
            mark_seen(state, sc, False)
            return

        caption = enrich_caption(item, args)
        await tg.send_file(channel, [str(f) for f in media],
                           caption=caption, supports_streaming=True)
        mark_seen(state, sc, True)
        log(f"[tg] uploaded {sc} ({len(media)} file(s))")
    except Exception as e:
        log(f"[!] failed on {sc}: {e}")
        mark_seen(state, sc, False)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        save_state(args.state, state)
        time.sleep(args.delay)
