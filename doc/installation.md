# Installation

## Requirements

- [uv](https://docs.astral.sh/uv/) — installs Python and dependencies automatically
- A Telegram account that is an **admin** of the target channel (with post rights)
- Telegram API credentials (`api_id` + `api_hash`) — see below
- Optional: an Instagram session for private profiles, stories/highlights,
  feed/saved/location/followee targets, and higher rate limits (see [Login](login.md))

## Install

```bash
uv sync    # creates .venv, installs Python 3.14 if needed, installs deps
```

Verify:

```bash
uv run insta2tg --help
```

## Telegram API credentials

1. Visit <https://my.telegram.org> → **API development tools**
2. Create an application (any name/platform works)
3. Copy `api_id` (number) and `api_hash` (hex string)

```bash
cp .env.example .env
```

Fill in:

```ini
TG_API_ID=1234567
TG_API_HASH=0123456789abcdef0123456789abcdef
```

These are read automatically from `.env` on every run. They are only used to
log your *own* Telegram account in as a userbot — never share them.

## First Telegram login

The first real (non `--dry-run`) run opens an interactive Telethon login:

1. Enter your phone number (international format, e.g. `+49170...`)
2. Enter the code Telegram sends you
3. If you have 2FA enabled, enter your cloud password

A session file (`insta2tg.session`) is created and reused afterwards — this is
a one-time step. Delete that file to log in as a different account.
