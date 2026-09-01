"""Posted-item history (replaces fast-update / latest-stamps / resume files)."""

import hashlib
import json
import time
from pathlib import Path


def load_state(path: str) -> dict:
    p = Path(path)
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        if "resume" not in data:
            data["resume"] = {}
        if "dp" not in data:
            data["dp"] = {}
        return data
    return {"uploaded": {}, "resume": {}, "dp": {}}


def save_state(path: str, state: dict) -> None:
    Path(path).write_text(
        json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def mark_seen(state: dict, shortcode: str, ok: bool) -> None:
    # value 0 marks a failed attempt so we don't retry it forever
    state["uploaded"][shortcode] = int(time.time()) if ok else 0


def file_hash(path: str | Path) -> str:
    """Return sha256 hash of a file's contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def save_resume(state: dict, channel: str, target: str,
                shortcode: str, date_ts: int) -> None:
    """Record the last uploaded post per telegram channel per instagram target."""
    if "resume" not in state:
        state["resume"] = {}
    chan_key = channel if channel.startswith("@") else str(channel)
    state["resume"].setdefault(chan_key, {})[target] = {
        "last_shortcode": shortcode,
        "last_date": date_ts,
    }


def load_resume(state: dict, channel: str, target: str) -> int | None:
    """Return the last uploaded post's date for this channel+target, or None."""
    if "resume" not in state:
        return None
    chan_key = channel if channel.startswith("@") else str(channel)
    entry = state["resume"].get(chan_key, {}).get(target)
    if entry:
        return entry["last_date"]
    return None


def save_dp(state: dict, channel: str, target: str, file_hash_val: str) -> None:
    """Record the last uploaded profile picture hash per channel per target."""
    if "dp" not in state:
        state["dp"] = {}
    chan_key = channel if channel.startswith("@") else str(channel)
    state["dp"].setdefault(chan_key, {})[target] = {
        "hash": file_hash_val,
        "date": int(time.time()),
    }


def load_dp(state: dict, channel: str, target: str) -> dict | None:
    """Return the last uploaded dp entry for this channel+target, or None."""
    if "dp" not in state:
        return None
    chan_key = channel if channel.startswith("@") else str(channel)
    return state["dp"].get(chan_key, {}).get(target)
