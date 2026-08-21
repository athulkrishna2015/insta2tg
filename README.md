# insta2tg

Mirror Instagram content — media **and** captions — into Telegram channels,
with near-full [instaloader](https://instaloader.github.io/) CLI parity.
Publishing is done by a [Telethon](https://docs.telethon.dev/) userbot (your
own Telegram account), so no bot token is needed. Instagram login is handled
entirely by instaloader's session management — no credentials are stored in
this project.

## Quick start

```bash
uv sync                          # install dependencies (Python + libs)
cp .env.example .env             # fill in TG_API_ID / TG_API_HASH

uv run insta2tg <username> --channel @my_channel --dry-run   # preview
uv run insta2tg <username> --channel @my_channel --loop      # mirror forever
```

## Documentation

Full documentation lives in [`doc/`](doc/index.md):

| Document | Contents |
|---|---|
| [Installation](doc/installation.md) | Requirements, uv setup, Telegram API credentials |
| [Login & sessions](doc/login.md) | Instagram auth: sessions, browser cookies, cookie files |
| [Targets](doc/targets.md) | Profiles, followees, hashtags, locations, feed, stories, saved, single posts |
| [Telegram channels](doc/telegram-channels.md) | `--channel` forms (@name / ids), permissions |
| [CLI reference](doc/cli-reference.md) | Every flag with defaults |
| [Examples](doc/examples.md) | Copy-paste recipes & background service setup |
| [State management](doc/state-management.md) | `state.json`, first run, `--backfill`, `--since`, dedupe |
| [instaloader parity](doc/instaloader-parity.md) | Supported / mapped / N/A features |
| [Troubleshooting](doc/troubleshooting.md) | Common errors and fixes |

## Project structure

```
insta2tg/
├── cli.py        argument parsing + entry point (uv run insta2tg)
├── runner.py     main orchestration loop
├── targets.py    instaloader target syntax parsing (+argsfile)
├── streams.py    target -> item iterators (profiles, hashtags, feed, ...)
├── fetch.py      new-item detection, --since, dedupe via state
├── filters.py    sandboxed --post-filter / --storyitem-filter
├── session.py    instaloader loader + session/cookie attachment
├── caption.py    caption assembly (text, geotag, comments, link)
├── media.py      post-download media filtering (--slide, --no-*)
├── telegram.py   channel resolution (@name or id) + upload
├── state.py      posted-item history
└── config.py     .env loading, logging, quiet mode
```
