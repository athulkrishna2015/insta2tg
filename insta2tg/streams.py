"""Build download streams from parsed targets."""

from itertools import islice

import instaloader

from .config import log

POST_LIKE = ("posts", "reels", "tagged", "igtv")   # Post objects
STORY_LIKE = ("stories", "highlights")             # StoryItem objects
ALL_KINDS = POST_LIKE + STORY_LIKE


def require_login(L) -> None:
    if L.context.username is None:
        raise SystemExit(
            "[ig] this target/content requires login. Create a session once:\n"
            "    uv run insta2tg --login <your_username>")


def iter_post_like(profile, kind: str):
    if kind == "posts":
        return profile.get_posts()
    if kind == "reels":
        return profile.get_reels()
    if kind == "tagged":
        return profile.get_tagged_posts()
    if kind == "igtv":
        return profile.get_igtv_posts()
    raise ValueError(kind)


def profile_streams(L, profile, kinds, label: str, window: int) -> list[dict]:
    """Build download streams for one profile according to --content."""
    streams = []
    for k in [k for k in kinds if k in POST_LIKE]:
        streams.append({"label": f"{label}/{k}",
                        "items": islice(iter_post_like(profile, k), window),
                        "kind": "post"})
    for k in [k for k in kinds if k in STORY_LIKE]:
        if k == "stories":
            items = [i for s in L.get_stories(userids=[profile.userid])
                     for i in s.get_items()]
        else:  # highlights
            items = [i for h in L.get_highlights(profile) for i in h.get_items()]
        streams.append({"label": f"{label}/{k}", "items": items,
                        "kind": "storyitem"})
    return streams


def build_streams(L, targets, kinds, window: int) -> list[dict]:
    streams: list[dict] = []
    for t in targets:
        try:
            if t.kind == "profile":
                prof = instaloader.Profile.from_username(L.context, t.value)
                streams += profile_streams(L, prof, kinds, t.value, window)

            elif t.kind == "followees":
                require_login(L)
                prof = instaloader.Profile.from_username(L.context, t.value)
                fe = list(prof.get_followees())
                log(f"[ig] @{t.value}: {len(fe)} followees")
                for f in fe:
                    streams += profile_streams(L, f, kinds, f.username, window)

            elif t.kind == "hashtag":
                h = instaloader.Hashtag.from_name(L.context, t.value)
                streams.append({"label": f"#{t.value}",
                                "items": islice(h.get_posts(), window),
                                "kind": "post"})

            elif t.kind == "location":
                require_login(L)
                streams.append({"label": f"%{t.value}",
                                "items": islice(
                                    L.get_location_posts(t.value), window),
                                "kind": "post"})

            elif t.kind == "feed":
                require_login(L)
                streams.append({"label": ":feed",
                                "items": islice(L.get_feed_posts(), window),
                                "kind": "post"})

            elif t.kind == "stories":          # :stories -> all followees
                require_login(L)
                items = [i for s in L.get_stories() for i in s.get_items()]
                streams.append({"label": ":stories", "items": items,
                                "kind": "storyitem"})

            elif t.kind == "saved":
                require_login(L)
                me = instaloader.Profile.from_username(
                    L.context, L.context.username)
                streams.append({"label": ":saved",
                                "items": islice(me.get_saved_posts(), window),
                                "kind": "post"})

            elif t.kind == "shortcode":
                try:
                    post = instaloader.Post.from_shortcode(L.context, t.value)
                except instaloader.exceptions.PostNotFoundException:
                    log(f"[!] shortcode not found: {t.value}")
                    continue
                streams.append({"label": f"-{t.value}", "items": [post],
                                "kind": "post"})
        except instaloader.exceptions.ProfileNotExistsException:
            log(f"[!] profile does not exist: {t.value}")
        except instaloader.exceptions.LoginRequiredException:
            raise SystemExit("[ig] login required. Create a session: "
                             "uv run insta2tg --login <user>")
    return streams
