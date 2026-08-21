# Troubleshooting

## Instagram errors

**`login required`** — anonymous access was refused (rate limit) or the
content requires a session. Create one:

```bash
uv run instaloader --login <your_username>
# or per-run:
uv run insta2tg ... -l <your_username>
```

**`profile 'x' does not exist`** — typo, or the account renamed/removed.
Private profiles you cannot see also fail this way; log in with an account
that follows them.

**429 / QueryReturnedBadRequest / throttling** — Instagram rejects plain
HTTP/1.1 API calls with 429 even on the first request of a fresh session.
The instaloader copy inside `.venv` is patched to send Instagram API requests
over HTTP/2 (upstream [PR #2730](https://github.com/instaloader/instaloader/pull/2730)),
which fixes this — see [Installation](installation.md#the-http2-patch).
If it still happens: use a session, raise `--delay`, lower `--scan/-c`,
increase `--interval`, and don't run multiple instances in parallel.

**`no media for <shortcode> (filtered or empty), skipping`** — everything was
filtered out (`-V`, `--no-pictures`, `--slide`, filters). The item is marked
as failed in `state.json`; remove its entry if you change your mind.

## Telegram errors

**`cannot resolve channel '...'`** — numeric id not in the session cache.
Forward any message of that channel to your Saved Messages once, then retry.
Or simply use the `@name` form for public channels.

**Wrong channel / no permission** — your account must be an admin with *Post
Messages* right. `--channel` must match exactly (`@name` or id).

**Telethon asks for phone/code every run** — the session file
(`insta2tg.session`) must stay writable in the working directory; don't delete
it between runs.

**`sqlite3.OperationalError: database is locked`** — another instance of
insta2tg (or an old stuck run) still holds `insta2tg.session`. Stop the other
process first: `ps aux | grep insta2tg`, then `kill <pid>`.

**`RPCError 500: FILE_WRITE_FAILED`** — transient Telegram server-side error
during a large upload. The item is marked failed; just re-run later (it will
be retried since it was not recorded as uploaded), or use `--ignore-seen` for
an explicit re-post.

## State issues

**Want a clean slate** — `rm state.json`. Next run records current history as
seen (posts nothing) unless `--backfill`/`--since` is given.

**Retry a failed item** — remove its shortcode key from `state.json`
(see [State management](state-management.md)).

## General notes

- Captions are truncated to Telegram's 1024-char limit; the post link is kept
  at the end unless `--no-source` is given.
- Multi-file posts are uploaded as a single Telegram album with one caption.
- Videos are sent with streaming support so they play inline.
- Stories expire after 24h — poll with a short `--interval` (300–900s).
- Reels often also appear in the regular posts feed; enabling both is safe,
  duplicates are prevented via `state.json`.
- Only mirror content you have the right to republish.
