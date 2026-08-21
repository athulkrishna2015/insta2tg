"""Sandboxed attribute filters (--post-filter / --storyitem-filter)."""


def build_filter(expr: str | None):
    """Evaluate a python expression against item attributes, instaloader-style."""
    if not expr:
        return lambda _item: True
    code = compile(expr, "<filter>", "eval")

    def f(item) -> bool:
        ns = {}
        for name in code.co_names:
            if name not in ns:
                try:
                    ns[name] = getattr(item, name)
                except AttributeError:
                    raise SystemExit(
                        f"[!] filter references unknown attribute '{name}'")
        return bool(eval(code, {"__builtins__": {}}, ns))
    return f
