# Examples / cookbook

All examples assume `uv run insta2tg` and a configured `.env`
(see [Installation](installation.md)). Replace `<username>` with any target and
`@my_channel` with your channel.

## First run

```bash
# 1. preview what WOULD be posted (records history, uploads nothing)
uv run insta2tg <username> --channel @my_channel --dry-run

# 2. first real run: also publish the 3 most recent posts
uv run insta2tg <username> --channel @my_channel --backfill 3
```

## Continuous mirroring

```bash
# check every 15 minutes (default interval)
uv run insta2tg <username> --channel @my_channel --loop

# stories expire after 24h -> poll faster
uv run insta2tg <username> --channel @my_channel \
    --content stories,highlights --loop --interval 600

# multiple sources, one channel
uv run insta2tg <username> someuser '#cats' --channel @my_channel --loop
```

## History import

```bash
# everything published after a specific post (oldest first)
uv run insta2tg <username> --channel @my_channel \
    --since https://www.instagram.com/p/CxYz123/

# same, by bare shortcode, previewed first
uv run insta2tg <username> --channel @my_channel --since CxYz123 --dry-run

# a single post only
uv run insta2tg --channel @my_channel -- -CxYz123
```

## Filtering

```bash
# only videos
uv run insta2tg <username> --channel @my_channel --post-filter 'is_video'

# popular posts only
uv run insta2tg <username> --channel @my_channel --post-filter 'likes > 1000'

# skip pinned posts, cap at 10 per cycle
uv run insta2tg <username> --channel @my_channel --post-filter 'not is_pinned' -c 10

# story items without audio
uv run insta2tg <username> --channel @my_channel \
    --content stories --storyitem-filter 'not has_audio'
```

## Media selection

```bash
# videos only (skip pictures)
uv run insta2tg <username> --channel @my_channel --no-pictures

# images only (skip videos and their thumbnail twins)
uv run insta2tg <username> --channel @my_channel -V --no-video-thumbnails
```

Only slide 2 of every carousel:

```bash
uv run insta2tg <username> --channel @my_channel --slide 2
```

## Caption enrichment

```bash
# append location + map link and top comments to every caption
uv run insta2tg <username> --channel @my_channel -G -C
```

## Login variants

```bash
uv run insta2tg <username> --channel @my_channel -l my_ig_account   # named session
uv run insta2tg <username> --channel @my_channel -b firefox         # browser cookies
uv run insta2tg <username> --channel @my_channel -B cookies.txt     # cookie file
```

## Run as a background service

```bash
nohup uv run insta2tg <username> --channel @my_channel --loop > insta2tg.log 2>&1 &
tail -f insta2tg.log
```

Or as a systemd user unit (`~/.config/systemd/user/insta2tg.service`):

```ini
[Unit]
Description=Instagram -> Telegram mirror

[Service]
WorkingDirectory=%h/path/to/insta-to-tele
ExecStart=/usr/bin/env uv run insta2tg <username> --channel @my_channel --loop -q
Restart=always
RestartSec=30

[Install]
WantedBy=default.target
```

```bash
systemctl --user enable --now insta2tg
journalctl --user -u insta2tg -f
```
