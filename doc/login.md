# Instagram login & sessions

insta2tg never stores Instagram credentials. Authentication is delegated
entirely to instaloader's session management. Sessions are attached in this
order (first match wins):

| Priority | Method | Flags |
|---|---|---|
| 1 | Browser cookie import | `-b/--load-cookies BROWSER` (+ optional `-B/--cookiefile`) |
| 2 | Named session file | `-l/--login USER` (+ optional `-p/--password`, `-f/--sessionfile`) |
| 3 | Auto-detected session | any `~/.config/instaloader/session-*` file |

## Method 1 — import cookies from a browser

```bash
uv run insta2tg <username> --channel @chan -b firefox
uv run insta2tg <username> --channel @chan -b chrome -B /path/to/cookies.txt
```

Reads the instagram.com cookies from the given browser's profile. Supported
browsers include Chrome, Chromium, Edge, Brave, Opera, Vivaldi, Firefox (and
Safari on macOS). Close the browser first if the cookie database is locked.

`-B/--cookiefile` alone (without `-b`) expects a Netscape-format HTTP cookie
file:

```
.instagram.com	TRUE	/	TRUE	0	sessionid	...
```

## Method 2 — named login

```bash
uv run insta2tg <username> --channel @chan -l my_account
```

- If a session for `my_account` exists → it is loaded.
- Otherwise: with `-p SECRET` the password is used non-interactively;
  without it you are prompted (and 2FA is handled interactively).
- The new session is saved and reused from then on.

`-f/--sessionfile PATH` points at a custom session file instead of the default
location.

## Method 3 — auto-detection

If no flags are given, insta2tg looks for existing instaloader sessions in

```
$XDG_CONFIG_HOME/instaloader/session-*     (default ~/.config/instaloader/)
```

Create one once with instaloader itself:

```bash
uv run instaloader --login <your_username>
```

## What requires a session?

| Feature | Anonymous | Session |
|---|---|---|
| Public profile posts/reels/tagged/igtv | ✔ (rate-limited) | ✔ |
| Private profiles | ✗ | required |
| `--content stories,highlights` | ✗ | required |
| `@followees`, `:feed`, `:stories`, `:saved`, `%location` | ✗ | required |
| `-G/--geotags`, `-C/--comments` enrichment | ✗ | required |

Anonymous access works but hits Instagram rate limits much sooner; a session
is recommended for anything beyond occasional small syncs.
