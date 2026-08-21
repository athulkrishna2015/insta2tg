# CLI reference

```
uv run insta2tg [options] target [target ...]
```

Full flag list is also available via `uv run insta2tg --help`.

## Content selection (profile targets)

| Flag | Default | Description |
|---|---|---|
| `--content LIST` | `posts` | Comma-separated: `posts`, `reels`, `tagged`, `igtv`, `stories`, `highlights`. Stories/highlights need login |

## What to download of each item

| Flag | Description |
|---|---|
| `--slide SLIDE` | Only upload this image/interval of a sidecar (carousel) |
| `--no-pictures` | Skip images |
| `-V`, `--no-videos` | Skip videos |
| `--no-video-thumbnails` | Drop the `.jpg` twin of every video |
| `-G`, `--geotags` | Append 📍 location + Google Maps link to caption (login) |
| `-C`, `--comments` | Append top-3 comments (by votes) to caption (login) |

## Which items

| Flag | Default | Description |
|---|---|---|
| `-c`, `--count N` | `--scan` value | Max items per target per cycle |
| `--post-filter EXPR` | — | Python expression over `Post` attributes |
| `--storyitem-filter EXPR` | — | Same for story items |
| `--scan N` | `30` | Items inspected per target per cycle |
| `--backfill N` | `0` | First run: upload N newest per target (`-1` = all scanned) |
| `--since URL\|SHORTCODE` | — | Upload everything published after that post |

Filter examples — attributes are instaloader `Post`/`StoryItem` fields:

```bash
--post-filter 'is_video'                       # only videos
--post-filter 'likes > 1000'                   # popular only
--post-filter 'not is_pinned'                  # skip pinned
--storyitem-filter 'not has_audio'
```

## Login (managed by instaloader)

| Flag | Description |
|---|---|
| `-l/--login USER` | Load or create the named session |
| `-p/--password PASS` | Password, only used if no session exists yet |
| `-b/--load-cookies BROWSER` | Import instagram cookies from a browser |
| `-B/--cookiefile FILE` | Import cookies from a Netscape-format file |
| `-f/--sessionfile PATH` | Custom session file path |

See [Login](login.md) for details and priority order.

## Download mechanics

| Flag | Default | Description |
|---|---|---|
| `--user-agent UA` | instaloader default | Custom user agent |
| `--max-connection-attempts N` | `3` | Retries per request (`0` = infinite) |
| `--request-timeout N` | `300` | Seconds before a request times out |
| `--abort-on CODES` | — | Comma-separated HTTP codes that abort everything |
| `--no-iphone` | off | Don't request iPhone media versions |
| `-q`, `--quiet` | off | Suppress informational output |

## Mirror behaviour (insta2tg-specific)

| Flag | Default | Description |
|---|---|---|
| `--channel CH` | — | Telegram channel: `@name` or id — see [channels](telegram-channels.md) |
| `--tg-session NAME` | `insta2tg` | Telethon session file name |
| `--state PATH` | `state.json` | Posted-item history |
| `--loop` | off | Keep checking forever |
| `--interval SEC` | `900` | Sleep between cycles when looping |
| `--delay SEC` | `3` | Pause between uploads |
| `--no-source` | off | Omit the Instagram source link from the caption |
| `--ignore-seen` | off | Upload regardless of seen-history; record nothing in state |
| `--dry-run` | off | List what would be posted without uploading |
