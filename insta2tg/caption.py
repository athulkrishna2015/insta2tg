"""Caption assembly - text, geotag, comments, source link."""

import instaloader

from .fetch import post_link

CAPTION_LIMIT = 1024


def enrich_caption(item, args) -> str:
    parts = [(item.caption or "").strip()]
    is_story = isinstance(item, instaloader.StoryItem)

    if args.geotags and not is_story:
        try:
            loc = item.get_location()
            if loc:
                maps = f"https://maps.google.com/?q={loc.lat},{loc.lng}"
                parts.append(f"📍 {loc.name} ({maps})")
        except Exception:
            pass

    if args.comments and not is_story:
        try:
            top = sorted(item.get_comments(),
                         key=lambda c: c.votes, reverse=True)[:3]
            parts.extend(f"👤 {c.owner.username}: {c.text}" for c in top)
        except Exception:
            pass

    link = None if getattr(args, "no_source", False) else post_link(item)
    text = "\n\n".join(p for p in parts if p)
    room = CAPTION_LIMIT if link is None else CAPTION_LIMIT - len(link) - 2
    if len(text) > room:
        text = text[:room].rstrip() + "…"
    if link is None:
        return text
    return f"{text}\n\n{link}" if text else link
