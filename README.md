# insta2tg

Mirror Instagram posts — media **and** captions — straight into a Telegram channel.

Downloads posts with [instaloader](https://instaloader.github.io/) and publishes them
with a [Telethon](https://docs.telethon.dev/) userbot (your own Telegram account),
so no bot token is needed.

## Features

- Single photos, videos, and carousels (uploaded as one album)
- Content types: posts, reels, tagged, IGTV, stories, and highlights (`--content`)
- Original caption included, post link appended automatically
- Tracks what's already been posted in `state.json` — no duplicates
- One-shot sync or continuous `--loop` polling mode
- `--dry-run` preview before anything goes live
- Optional Instagram login for private profiles / higher rate limits

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- A Telegram account that is an **admin** of the target channel (with post rights)
- [Telegram API credentials](https://my.telegram.org) → *API development tools* → `api_id` + `api_hash`

## Setup

```bash
uv sync                # installs deps from pyproject.toml into .venv
cp .env.example .env   # then fill in your values
```

### Configuration (`.env`)

| Variable | Required | Description |
|---|---|---|
| `TG_API_ID` | yes | Numeric API ID from my.telegram.org |
| `TG_API_HASH` | yes | API hash from my.telegram.org |
| `TG_CHANNEL` | yes | Channel to post into: public `@name` or numeric id |
| `IG_TARGET` | yes | Instagram username to mirror |
| `IG_USERNAME` | no | IG account for login (recommended; required for private profiles) |
| `IG_PASSWORD` | no | IG password (only needed on first login if no saved session) |

Every value can also be passed as a CLI flag (`--channel`, `--target`, ...) which takes priority.

## Usage

```bash
# first run: creates telegram session (asks phone + code), records IG history, posts nothing
uv run insta2tg.py --dry-run          # preview what would be posted
uv run insta2tg.py --backfill 3       # first run: also post the 3 most recent posts

# watch for new posts every 15 min
uv run insta2tg.py --loop --interval 900

# one-shot sync of anything new since last run
uv run insta2tg.py

# upload EVERYTHING posted after a specific post (URL or shortcode)
uv run insta2tg.py --since https://www.instagram.com/p/CxYz123/
uv run insta2tg.py --since CxYz123 --dry-run   # preview first (recommended)

# mirror everything: posts + reels + stories + highlights + tagged + igtv
uv run insta2tg.py --content posts,reels,stories,highlights,tagged,igtv --loop

# only stories and highlights (requires IG login)
uv run insta2tg.py --content stories,highlights --loop --interval 1800
```

Run it forever in the background:

```bash
nohup uv run insta2tg.py --loop > insta2tg.log 2>&1 &
```

### CLI options

| Flag | Default | Description |
|---|---|---|
| `--target` | `IG_TARGET` | Instagram username |
| `--channel` | `TG_CHANNEL` | Telegram channel @name or id |
| `--api-id` / `--api-hash` | env | Telegram credentials |
| `--session` | `insta2tg` | Telethon session file name |
| `--state` | `state.json` | Where posted-post history is kept |
| `--content` | `posts` | Comma-separated: `posts`, `reels`, `tagged`, `igtv`, `stories`, `highlights`. Stories/highlights require IG login |
| `--loop` | off | Keep checking forever |
| `--interval` | `900` | Seconds between checks when looping |
| `--scan` | `30` | How many of the newest posts to inspect each cycle |
| `--backfill` | `0` | On first run, post the N newest posts instead of none (`-1` = everything scanned) |
| `--since` | — | Post URL or shortcode; uploads every post published **after** it, oldest first |
| `--delay` | `3` | Seconds between uploads (be gentle) |
| `--dry-run` | off | List what would be posted without uploading |

## How it works

1. Fetches the newest `--scan` posts of `IG_TARGET` via instaloader.
2. Skips any shortcode already present in `state.json`.
3. Downloads each new post into a temp folder.
4. Uploads the media to `TG_CHANNEL` with the caption + source link.
5. Records the shortcode in `state.json` and cleans up.

On the very first run (empty `state.json`) existing posts are marked as seen
without posting, so you don't accidentally flood the channel — use `--backfill`
if you want recent history.

## Troubleshooting

- **`login required`** — Instagram is rate-limiting anonymous access or the profile
  is private. Set `IG_USERNAME` in `.env`, or create a session once manually:
  `uv run instaloader --login <your_username>`
- **Wrong channel / no permission** — make sure your user account is an admin of
  the channel and `TG_CHANNEL` matches exactly (`@name` or `-100…` id).
- **Stuck state / want a clean slate** — delete `state.json`.
- **A post failed** — it's marked in `state.json` and skipped afterwards;
  remove its entry there to retry.

## Notes

- Captions are truncated to Telegram's 1024-char limit; the post link is always appended.
- Videos are sent with streaming support so they play inline.
- Stories expire after 24h — use a short `--interval` (e.g. 300–900s) if you don't want to miss any.
- Reels often also appear in the regular posts feed; enabling both is safe —
  duplicates are prevented via `state.json`.
- Bulk runs (`--since`, large `--backfill`) can take a while — each upload waits
  `--delay` seconds and Instagram rate-limits aggressive scraping. Preview with
  `--dry-run` first.
- Only mirror content you have the right to republish.
