# State management

insta2tg tracks what it already uploaded in `state.json` (configurable via
`--state`). This replaces instaloader's `--fast-update`, `--latest-stamps`,
and resume files.

## Schema

```json
{
  "uploaded": {
    "CxYz123": 1724220000,
    "CwAbc99": 0
  },
  "resume": {
    "@telegram_channel": {
      "instagram_target": {
        "last_shortcode": "CxYz123",
        "last_date": 1724220000
      }
    }
  },
  "dp": {
    "@telegram_channel": {
      "instagram_target": {
        "url": "https://...profile_pic.jpg",
        "hash": "sha256_hex_digest",
        "date": 1724220000
      }
    }
  }
}
```

### `uploaded`

Keys are Instagram shortcodes (unique across posts, reels, stories, highlights).
Values are unix timestamps of when the item was handled. A value of `0` marks a
**failed attempt** — the item will not be retried automatically.

### `resume`

Stores the last uploaded post per Instagram source per Telegram channel. Used
with the `--resume` flag to continue from where the previous run left off. Updated
automatically after each successful upload.

### `dp`

Stores the last uploaded profile picture per Instagram source per Telegram channel.
Uses **SHA-256 hash** of the image file for reliable change detection (URLs can
change due to CDN rotation even when the image is the same). Updated after each
successful DP upload.

## Behaviours

| Situation | Behaviour |
|---|---|
| Shortcode in state | Skipped — no duplicates, even across overlapping sources |
| First run (empty state) | Existing items are marked seen, nothing is posted |
| `--backfill N` | On first run, upload the N newest per target instead |
| `--backfill -1` | On first run, upload everything in the scan window |
| `--since POST` | Upload every item newer than that post (overrides first-run rule) |
| `--ignore-seen` | Ignore the history completely: upload everything matching the filters and record nothing — for explicit one-off uploads/reposts |
| `--resume` | Resume from the last uploaded post per source per channel (see below) |
| Download/upload error | Item marked with `0`, run continues with the next one |

`--ignore-seen` also bypasses the `--backfill` cap, so a single post can be
re-posted at any time:

```bash
uv run insta2tg --channel @my_channel --ignore-seen -- -CxYz123
```

Because dedupe is shortcode-based, overlapping sources are safe: e.g. mirroring
both `posts` and `reels` of the same account, or the same account into runs
with different filters, never double-posts.

## --resume

The `--resume` flag enables per-source, per-channel resume. When passed, insta2tg
looks up the last uploaded post for each Instagram source target in the current
Telegram channel and only uploads posts newer than that point.

```bash
# first run: upload recent posts
uv run insta2tg <username> --channel @my_channel --backfill 5

# subsequent runs: only upload what's new since the last upload
uv run insta2tg <username> --channel @my_channel --resume --loop
```

This is tracked separately from `--since` (which is a one-time cutoff) and
`--ignore-seen` (which bypasses history entirely). The resume point is updated
after each successful upload, so interrupting and restarting a run continues
exactly where it left off.

## --dp

The `--dp` flag enables profile picture change detection. When passed, insta2tg
downloads the current profile picture, computes its SHA-256 hash, and compares it
with the stored hash. If different, it uploads the new picture to the Telegram
channel with a caption like "📷 New profile picture for \<target\>".

```bash
# upload posts + detect dp changes
uv run insta2tg <username> --channel @mychan --dp --loop

# combine with --resume for full state tracking
uv run insta2tg <username> --channel @mychan --resume --dp --loop
```

Hash-based detection is more reliable than URL comparison because Instagram CDNs
may rotate URLs even when the image hasn't changed.

## Reset / retry

```bash
# full reset - next run behaves like a fresh first run
rm state.json

# retry one failed item: remove its key from state.json
python3 - <<'EOF'
import json
s = json.load(open("state.json"))
s["uploaded"].pop("CxYz123", None)   # <- shortcode to retry
json.dump(s, open("state.json", "w"), indent=2)
EOF
```

State is saved after every item, so an interrupted run resumes where it left
off on the next start.
