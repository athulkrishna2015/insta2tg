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
  }
}
```

Keys are Instagram shortcodes (unique across posts, reels, stories, highlights).
Values are unix timestamps of when the item was handled. A value of `0` marks a
**failed attempt** — the item will not be retried automatically.

## Behaviours

| Situation | Behaviour |
|---|---|
| Shortcode in state | Skipped — no duplicates, even across overlapping sources |
| First run (empty state) | Existing items are marked seen, nothing is posted |
| `--backfill N` | On first run, upload the N newest per target instead |
| `--backfill -1` | On first run, upload everything in the scan window |
| `--since POST` | Upload every item newer than that post (overrides first-run rule) |
| Download/upload error | Item marked with `0`, run continues with the next one |

Because dedupe is shortcode-based, overlapping sources are safe: e.g. mirroring
both `posts` and `reels` of the same account, or the same account into runs
with different filters, never double-posts.

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
