# Telegram channels

## `--channel` forms

| Form | Example |
|---|---|
| Public @name | `@my_channel` |
| Marked channel id | `-1001234567890` |
| Raw channel id | `1234567890` |
| Legacy chat/group id | `-1234567890` |

Numeric ids are resolved from Telethon's session cache. If resolution fails:

```
[tg] cannot resolve channel '...'. Use an @name, the marked -100... id, or
forward any message of that channel to yourself once so it lands in the
session cache.
```

**Fix:** forward any post of that channel to your own *Saved Messages*, run the
command again — the entity is now cached and the id resolves.

## Permissions

Your Telegram account (the userbot) must be able to **post** in the channel:

- For channels: add your account as an admin with *Post Messages* right.
- Anonymous admins: if you post as the channel itself, enable that in channel
  admin settings; otherwise posts appear under your personal name.

## Finding a channel id

1. Forward any message from the channel to `@userinfobot` / `@getidsbot`, or
2. Forward it to your Saved Messages and inspect with any "ids" bot, or
3. Use the @name form — simplest when the channel is public.

Private channels have no @name; use the id form there.
