"""instaloader session handling - credentials stay inside instaloader."""

import os
from pathlib import Path

import instaloader

from .config import log


def find_session_file() -> Path | None:
    """Locate an existing instaloader session file (default config dir)."""
    cfg = Path(os.environ.get("XDG_CONFIG_HOME",
                              Path.home() / ".config")) / "instaloader"
    sessions = sorted(cfg.glob("session-*"))
    return sessions[0] if sessions else None


def build_loader(args) -> instaloader.Instaloader:
    """Create loader honoring instaloader-parity flags, then attach a session."""
    abort_codes = ([int(c) for c in args.abort_on.split(",")]
                   if args.abort_on else None)
    L = instaloader.Instaloader(
        quiet=args.quiet,
        user_agent=args.user_agent,
        download_pictures=not args.no_pictures,
        download_videos=not args.no_videos,
        download_video_thumbnails=not args.no_video_thumbnails,
        slide=args.slide,
        save_metadata=False,
        compress_json=False,
        download_comments=False,
        post_metadata_txt_pattern="",   # captions come from the objects
        storyitem_metadata_txt_pattern="",
        max_connection_attempts=args.max_connection_attempts,
        request_timeout=float(args.request_timeout),
        fatal_status_codes=abort_codes,
        iphone_support=not args.no_iphone,
    )

    # Route instaloader's chatter through our logger; drop raw file-path
    # dumps (insta2tg logs its own download/upload summaries).
    def _ig_log(*msg, sep='', end='\n', flush=False):
        text = sep.join(str(m) for m in msg)
        if "tmp_downloads" in text or ".jpg" in text or ".mp4" in text:
            return
        if text.strip():
            log(f"[ig] {text}")

    L.context.log = _ig_log

    # ---- session attachment (first match wins) --------------------------
    if args.load_cookies:
        try:
            from instaloader.utils import get_cookies_from_instagram
            cookie = get_cookies_from_instagram(
                "instagram", args.load_cookies.lower(), args.cookiefile)
            L.context.update_cookies(cookie)
            log(f"[ig] session imported from browser '{args.load_cookies}'")
        except ImportError:
            raise SystemExit("[!] this instaloader version cannot import "
                             "browser cookies; use --login instead")
        return L

    if args.login:
        try:
            L.load_session_from_file(args.login, args.sessionfile)
            log(f"[ig] loaded instaloader session of '{args.login}'")
        except FileNotFoundError:
            if args.password:
                L.login(args.login, args.password)
                L.save_session_to_file(args.sessionfile)
            else:
                L.interactive_login(args.login)
                L.save_session_to_file(args.sessionfile)
            log(f"[ig] logged in as {args.login} (session saved)")
        return L

    session = find_session_file()
    if session:
        user = session.name.removeprefix("session-")
        try:
            L.load_session_from_file(user)
            log(f"[ig] auto-detected instaloader session of '{user}'")
        except FileNotFoundError:
            log(f"[!] session file for '{user}' not loadable, going anonymous")
    else:
        log("[ig] no session -> anonymous access "
            "(create one: uv run insta2tg --login <user>)")
    return L
