"""Target parsing - same syntax as the instaloader CLI."""

from pathlib import Path
import sys


class Target:
    def __init__(self, kind: str, value: str = ""):
        self.kind = kind      # profile|followees|hashtag|location|feed|stories|saved|shortcode
        self.value = value

    def __repr__(self):
        return f"{self.kind}:{self.value}"


def parse_target(tok: str) -> Target:
    if tok.startswith("@"):
        return Target("followees", tok[1:])
    if tok.startswith("#"):
        return Target("hashtag", tok.lstrip("#"))
    if tok.startswith("%"):
        return Target("location", tok[1:])
    if tok in (":feed", ":stories", ":saved"):
        return Target(tok[1:])
    if tok.startswith("-") and len(tok) > 1:
        return Target("shortcode", tok[1:])
    return Target("profile", tok)


def expand_targets(tokens: list[str]) -> list[Target]:
    """Expand +argsfile entries and parse every token."""
    out: list[Target] = []
    for tok in tokens:
        if tok.startswith("+"):
            f = Path(tok[1:])
            if not f.exists():
                sys.exit(f"[!] argsfile not found: {f}")
            lines = [l.strip() for l in f.read_text(encoding="utf-8").splitlines()]
            out.extend(expand_targets(
                [l for l in lines if l and not l.startswith("#")]))
        else:
            out.append(parse_target(tok))
    return out
