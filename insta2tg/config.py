"""Global runtime config and logging helpers."""

import os
from pathlib import Path

QUIET = False


def set_quiet(q: bool) -> None:
    global QUIET
    QUIET = q


def log(msg: str) -> None:
    if not QUIET:
        print(msg)


def load_env(path: str = ".env") -> None:
    """Tiny .env loader (no external dependency)."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        os.environ.setdefault(key.strip(), val.strip().strip("'\""))
