"""Global runtime config and logging helpers."""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

QUIET = False
VERBOSE = False


def set_quiet(q: bool) -> None:
    global QUIET
    QUIET = q


def set_verbose(v: bool) -> None:
    global VERBOSE
    VERBOSE = v
    if v:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s")
        # suppress noisy third-party loggers
        for logger in ("httpx", "httpcore", "telethon", "urllib3"):
            logging.getLogger(logger).setLevel(logging.WARNING)


def log(msg: str) -> None:
    if not QUIET:
        print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def debug(msg: str) -> None:
    if VERBOSE:
        logging.debug(msg)


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
