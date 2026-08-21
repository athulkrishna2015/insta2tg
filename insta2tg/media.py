"""Media file collection and filtering after download."""

import re
from pathlib import Path

VID_EXT = {".mp4", ".mkv", ".mov", ".webm"}
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}
MEDIA_EXT = IMG_EXT | VID_EXT

IDX_RE = re.compile(r"_(\d+)$")


def collect_media(folder: Path, args) -> list[Path]:
    files = [p for p in folder.iterdir() if p.suffix.lower() in MEDIA_EXT]

    video_stems = {p.stem for p in files if p.suffix.lower() in VID_EXT}
    out = []
    for p in files:
        ext = p.suffix.lower()
        if ext in VID_EXT and args.no_videos:
            continue
        if ext in IMG_EXT:
            if args.no_pictures:
                continue
            if args.no_video_thumbnails and p.stem in video_stems:
                continue
        out.append(p)

    if args.slide is not None:  # keep only the requested sidecar slide
        out = [p for p in out if p.stem.endswith(f"_{args.slide}")]

    def order(p: Path):
        m = IDX_RE.search(p.stem)
        return (int(m.group(1)) if m else -1, p.name)

    return sorted(out, key=order)
