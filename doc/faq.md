# FAQ

## Uploads

**How do I upload a single post?**

```bash
uv run insta2tg --channel @my_channel --ignore-seen -- -CxYz123
```

`-shortcode` goes after `--` so it is not read as a flag. Add `-l USER` to use
your Instagram session and `--no-source` to drop the caption link.

**How do I upload everything after a specific post?**

```bash
uv run insta2tg <username> --channel @my_channel \
    --since https://www.instagram.com/<username>/p/CxYz123/
```

A bare shortcode (`--since CxYz123`) works too. Add `-c 100` if more than 30
posts exist after it, and `--dry-run` to preview first.

**Are multi-image / multi-video posts sent as one message?**

Yes — every file of a post is uploaded as a single Telegram album/group
(photos, videos and mixed carousels), with one shared caption.

**What does "seen" mean?**

`state.json` remembers every shortcode that was uploaded (with a timestamp;
`0` = failed attempt). Seen items are skipped on later runs so nothing is
posted twice — across cycles, overlapping sources and restarts.

**How do I re-upload something that is already seen?**

Use `--ignore-seen`: it ignores the seen-history entirely and does **not**
record the new uploads either — ideal for explicit one-off reposts.

**Why did my run upload nothing even though there are new posts?**

After the very first run everything current is marked seen; without
`--backfill`/`--since` only *newly published* items get posted. Use
`--backfill N`, `--since POST` or `--ignore-seen` to post existing ones.

## Captions

**Can I remove the Instagram link at the end of captions?**

Yes: `--no-source`. The freed space goes back to the caption text (Telegram's
1024-char limit still applies).

**How much caption text fits?**

1024 characters (Telegram limit). With the source link enabled the text is
truncated just enough to keep the link; with `--no-source` you get the full
budget.

## Sessions & rate limits

**Do I need an Instagram session?**

Not for public profiles/posts, but it raises rate limits and is required for
private profiles, stories/highlights, feed/saved/location/followee targets.
See [Login](login.md).

**Instagram answers 429 Too Many Requests on the first request**

The bundled instaloader in `.venv` is patched to speak HTTP/2 (upstream PR
[instaloader#2730](https://github.com/instaloader/instaloader/pull/2730)),
which fixes this. If it ever comes back after a dependency reinstall, see
[Installation](installation.md#the-http2-patch).

## State

**Where is the state stored and how do I reset it?**

`state.json` in the working directory (`--state PATH` to change). Delete it
for a clean slate — the next run then behaves like a first run. See
[State management](state-management.md).

**An item failed mid-run — will it retry?**

Failed items are marked `0` and not retried automatically. Remove their key
from `state.json`, or simply re-run with `--ignore-seen`.
