"""Posted-item history (replaces fast-update / latest-stamps / resume files)."""

import json
import time
from pathlib import Path


def load_state(path: str) -> dict:
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"uploaded": {}}


def save_state(path: str, state: dict) -> None:
    Path(path).write_text(
        json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def mark_seen(state: dict, shortcode: str, ok: bool) -> None:
    # value 0 marks a failed attempt so we don't retry it forever
    state["uploaded"][shortcode] = int(time.time()) if ok else 0
