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

**429 / QueryReturnedBadRequest / throttling** — Instagram rate limiting.
Use a session, raise `--delay`, lower `--scan/-c`, and increase `--interval`.

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

## State issues

**Want a clean slate** — `rm state.json`. Next run records current history as
seen (posts nothing) unless `--backfill`/`--since` is given.

**Retry a failed item** — remove its shortcode key from `state.json`
(see [State management](state-management.md)).

## General notes

- Captions are truncated to Telegram's 1024-char limit; the post link is
  always kept at the end.
- Videos are sent with streaming support so they play inline.
- Stories expire after 24h — poll with a short `--interval` (300–900s).
- Reels often also appear in the regular posts feed; enabling both is safe,
  duplicates are prevented via `state.json`.
- Only mirror content you have the right to republish.
