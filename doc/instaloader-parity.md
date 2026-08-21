# instaloader parity

insta2tg aims for near-full [instaloader](https://instaloader.github.io/)
CLI parity. Same targets, same flags — but instead of archiving to disk,
items are published to a Telegram channel.

## Targets

| instaloader target | Supported | Notes |
|---|---|---|
| `profile` | ✔ | content per `--content` |
| `@profile` (followees) | ✔ | login required |
| `"#hashtag"` | ✔ | |
| `%location_id` | ✔ | login required |
| `:feed` | ✔ | login required |
| `:stories` | ✔ | login required, all followees |
| `:saved` | ✔ | login required, your own saved posts |
| `-- -shortcode` | ✔ | single post |
| `filename.json` re-download | ✗ | not applicable |

## Flags

### What to download of each post
| instaloader flag | Behaviour here |
|---|---|
| `--slide SLIDE` | ✔ only that sidecar slide is uploaded |
| `--no-pictures` | ✔ applied at download time |
| `-V/--no-videos` | ✔ applied at download time |
| `--no-video-thumbnails` | ✔ thumbnails filtered before upload |
| `-G/--geotags` | mapped → 📍 location + Maps link appended to caption |
| `-C/--comments` | mapped → top-3 comments appended to caption |
| `--post-metadata-txt`, `--storyitem-metadata-txt`, `--no-captions` | N/A — captions come from the objects and are always included |

### Per-profile switches
| instaloader flag | Equivalent |
|---|---|
| `--stories`, `--highlights`, `--tagged`, `--reels`, `--igtv` | combined into `--content posts,reels,tagged,igtv,stories,highlights` |
| `--no-posts` | omit `posts` from `--content` |
| `--no-profile-pic` | N/A — profile pictures are never mirrored |

### Which posts to download
| instaloader flag | Equivalent |
|---|---|
| `-F/--fast-update` | automatic via `state.json` dedupe |
| `--latest-stamps FILE` | replaced by `state.json` |
| `--post-filter`, `--storyitem-filter` | ✔ identical expressions |
| `-c/--count COUNT` | ✔ per target per cycle |

### Login
| instaloader flag | Supported |
|---|---|
| `-l/--login USER` | ✔ |
| `-p/--password PASS` | ✔ (only used when no session exists) |
| `-b/--load-cookies BROWSER` | ✔ |
| `-B/--cookiefile FILE` | ✔ |
| `-f/--sessionfile PATH` | ✔ |

### Download mechanics
| instaloader flag | Supported |
|---|---|
| `--user-agent UA` | ✔ |
| `--max-connection-attempts N` | ✔ |
| `--request-timeout N` | ✔ |
| `--abort-on STATUS_CODES` | ✔ |
| `--no-iphone` | ✔ |
| `-q/--quiet` | ✔ suppresses insta2tg output and instaloader interaction |
| `--dirname-pattern`, `--filename-pattern`, `--title-pattern` | ✗ items go to a temp dir deleted after upload |
| `--resume-prefix`, `--no-resume`, `--sanitize-paths` | ✗ no local archive; `state.json` survives restarts |

## Intentional differences

instaloader archives to disk; this tool publishes to Telegram:

- No metadata JSON/txt files — captions are taken directly from the objects.
- Comments/geotags are folded into the caption instead of separate files.
- `filename.json` re-download target is not applicable.
- Everything else (targets, filters, media selection, login, mechanics)
  behaves like instaloader.
