# Targets

insta2tg uses the same target syntax as the instaloader CLI. You can pass
**multiple targets** in one run; every target contributes its own download
stream each cycle.

```
uv run insta2tg [options] target [target ...]
```

| Target | Mirrors | Login |
|---|---|---|
| `username` | profile content per `--content` | — |
| `@username` | posts of everyone that account follows | ✔ |
| `"#hashtag"` | hashtag feed | — |
| `%location_id` | location feed | ✔ |
| `:feed` | your home feed | ✔ |
| `:stories` | stories of all your followees | ✔ |
| `:saved` | posts you saved | ✔ |
| `-shortcode` | exactly one post | — |
| `+args.txt` | targets read from a file, one per line | — |

## Notes per target

- **profile** — what gets mirrored is controlled by `--content`
  (`posts,reels,tagged,igtv,stories,highlights`). See below.
- **@followees** — expands to every account the given user follows and builds
  the selected content streams for each. Can be large; combine with
  `-c/--count` to cap items per cycle.
- **#hashtag** — quotes are only needed so your shell doesn't interpret `#`.
- **%location_id** — numeric location id (from the Instagram location page URL).
- **-shortcode** — starts with a dash, so put it after `--` to keep argparse
  from reading it as a flag:
  ```bash
  uv run insta2tg --channel @my_channel -- -CxYz123
  ```
- **+argsfile** — one target per line; blank lines and `#comments` are ignored:
  ```
  # my sources
  <username>
  "#cats"
  :saved
  ```

## Content selection (`--content`, profile targets)

Comma-separated list, default `posts`:

| Kind | Source | Login |
|---|---|---|
| `posts` | regular profile feed | — |
| `reels` | reels tab | — |
| `tagged` | posts the profile is tagged in | — |
| `igtv` | IGTV videos | — |
| `stories` | live stories (expire after 24h!) | ✔ |
| `highlights` | archived story highlights | ✔ |

Reels usually also appear in the regular posts feed. Enabling both is safe —
duplicates are prevented via [state](state-management.md).
