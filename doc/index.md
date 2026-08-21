# Documentation

Complete documentation for **insta2tg** — mirror Instagram content into Telegram channels.

| Document | Contents |
|---|---|
| [Installation](installation.md) | Requirements, installing uv, setting up `.env`, first verification |
| [Login & sessions](login.md) | Instagram authentication: sessions, browser cookies, cookie files |
| [Targets](targets.md) | Everything you can mirror: profiles, followees, hashtags, locations, feed, stories, saved, single posts |
| [Telegram channels](telegram-channels.md) | `--channel` forms (@name, ids), permissions, resolving ids |
| [CLI reference](cli-reference.md) | Every flag, grouped, with defaults |
| [Examples](examples.md) | Copy-paste recipes: first run, loops, filters, background service |
| [State management](state-management.md) | `state.json`, first-run behavior, `--backfill`, `--since`, dedupe |
| [instaloader parity](instaloader-parity.md) | Which instaloader features are supported, mapped, or N/A |
| [Troubleshooting](troubleshooting.md) | Common errors and fixes |

## Quick start

```bash
uv sync                          # install dependencies
cp .env.example .env             # add TG_API_ID / TG_API_HASH
uv run insta2tg <username> --channel @my_channel --dry-run   # preview
uv run insta2tg <username> --channel @my_channel --loop      # mirror forever
```

See [Installation](installation.md) for details.
