"""Global runtime config and logging helpers."""

import os
import sys
from datetime import datetime
from pathlib import Path

QUIET = False


def set_quiet(q: bool) -> None:
    global QUIET
    QUIET = q


def log(msg: str) -> None:
    if not QUIET:
        print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def warn(msg: str) -> None:
    """Errors and warnings - always shown, even with -q."""
    print(f"[{datetime.now():%H:%M:%S}] {msg}", file=sys.stderr, flush=True)


def human_size(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{int(n)} B" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


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
