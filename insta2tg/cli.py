"""Command line interface."""

import argparse

from .runner import run

EPILOG = """
targets:
  username              profile posts/reels/tagged/igtv/stories/highlights (--content)
  @username             posts of everyone @username follows (login)
  "#hashtag"            hashtag posts
  %location_id          location posts (login)
  :feed                 your feed (login)
  :stories              stories of your followees (login)
  :saved                posts you saved (login)
  -shortcode            single post (put it after '--' so it is not read as a flag)
  +args.txt             one target per line

--channel accepts an @name or an id: marked -1001234567890, raw 1234567890,
or legacy -1234567890.

examples:
  uv run insta2tg <username> --channel @mychan --loop
  uv run insta2tg <username> --channel -1001234567890 --content reels,stories
  uv run insta2tg <username> someuser '#cats' --channel @mychan -c 10
  uv run insta2tg --channel @mychan -- -CxYz123
  uv run insta2tg <username> --channel @mychan --post-filter 'is_video and likes > 100'
"""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="insta2tg",
        description="Mirror Instagram content to a Telegram channel "
                    "(instaloader-compatible targets & flags)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG)

    p.add_argument("targets", nargs="+", metavar="target",
                   help="profile | @followees | #hashtag | %%location | "
                        ":feed | :stories | :saved | -shortcode | +argsfile")
    p.add_argument("--channel",
                   help="Telegram channel: @name or id (-100..., raw, legacy)")

    g = p.add_argument_group("content selection (profile targets)")
    g.add_argument("--content", default="posts",
                   help="comma-separated: posts,reels,tagged,igtv,stories,highlights "
                        "(default: posts). stories/highlights need login")

    g = p.add_argument_group("what to download of each item")
    g.add_argument("--slide", type=int, metavar="SLIDE",
                   help="only this image/interval of a sidecar")
    g.add_argument("--no-pictures", action="store_true")
    g.add_argument("-V", "--no-videos", action="store_true")
    g.add_argument("--no-video-thumbnails", action="store_true")
    g.add_argument("-G", "--geotags", action="store_true",
                   help="append location + map link to the caption (login)")
    g.add_argument("-C", "--comments", action="store_true",
                   help="append top comments to the caption (login)")

    g = p.add_argument_group("which items")
    g.add_argument("-c", "--count", type=int, default=None,
                   help="max items per target per cycle (default: --scan)")
    g.add_argument("--post-filter", "--only-if", dest="post_filter",
                   metavar="EXPR", help="python expr over Post attributes")
    g.add_argument("--storyitem-filter", dest="storyitem_filter",
                   metavar="EXPR", help="python expr over StoryItem attributes")

    g = p.add_argument_group("login (managed by instaloader)")
    g.add_argument("-l", "--login", metavar="USERNAME",
                   help="login name; loads existing session or creates one")
    g.add_argument("-p", "--password", help="password (only if no session yet)")
    g.add_argument("-b", "--load-cookies", metavar="BROWSER",
                   help="import session from a browser (firefox/chrome/...)")
    g.add_argument("-B", "--cookiefile", metavar="COOKIE-FILE",
                   help="cookie file to import instead of a browser")
    g.add_argument("-f", "--sessionfile", metavar="SESSIONFILE",
                   help="custom instaloader session file path")

    g = p.add_argument_group("download mechanics")
    g.add_argument("--user-agent", metavar="UA")
    g.add_argument("--max-connection-attempts", type=int, default=3, metavar="N")
    g.add_argument("--request-timeout", type=int, default=300, metavar="N")
    g.add_argument("--abort-on", metavar="STATUS_CODES",
                   help="comma-separated HTTP codes that abort everything")
    g.add_argument("--no-iphone", action="store_true",
                   help="do not request iPhone versions of media")

    g = p.add_argument_group("mirror behaviour")
    g.add_argument("--tg-session", default="insta2tg",
                   help="Telethon session name (default: insta2tg)")
    g.add_argument("--state", default="state.json",
                   help="state file path (default: state.json)")
    g.add_argument("--loop", action="store_true",
                   help="keep checking for new items forever")
    g.add_argument("--interval", type=int, default=900,
                   help="poll interval seconds when --loop (default: 900)")
    g.add_argument("--scan", type=int, default=30,
                   help="items checked per target per cycle (default: 30)")
    g.add_argument("--backfill", type=int, default=0,
                   help="on first run upload the N most recent per target "
                        "instead of none (-1 = all scanned)")
    g.add_argument("--since", metavar="URL_OR_SHORTCODE",
                   help="upload every item published after this post")
    g.add_argument("--delay", type=int, default=3,
                   help="seconds between uploads (default: 3)")
    g.add_argument("--no-source", action="store_true",
                   help="omit the instagram source link from the caption")
    g.add_argument("--ignore-seen", action="store_true",
                   help="upload regardless of what was already posted and "
                        "do not record these uploads in the state file")
    g.add_argument("-q", "--quiet", action="store_true",
                   help="suppress informational output")
    g.add_argument("--dry-run", action="store_true",
                   help="list what would be posted, without uploading")
    return p.parse_args()


def main() -> None:
    import asyncio
    try:
        asyncio.run(run(parse_args()))
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
