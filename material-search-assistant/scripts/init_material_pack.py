#!/usr/bin/env python3
"""Initialize a material-pack folder structure and starter log file."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


DEFAULT_SEGMENTS = [
    "opening_heat_proof",
    "concept_definition",
    "capability_demo",
    "real_experience",
    "risk_warning",
    "skill_ecosystem",
    "closing_cta",
]


LOG_HEADERS = [
    "file_name",
    "segment_id",
    "segment_label",
    "source_platform",
    "source_url",
    "asset_type",
    "core_message",
    "why_it_matches",
    "quality_grade",
    "score_script_fit",
    "score_visual_clarity",
    "score_cleanliness",
    "score_credibility",
    "score_editing_utility",
    "suggested_use",
    "status",
]


def slugify(text: str) -> str:
    chars = []
    for ch in text.strip().lower():
        if ch.isalnum():
            chars.append(ch)
        elif ch in {" ", "-", "_"}:
            chars.append("_")
    slug = "".join(chars)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_") or "segment"


def parse_segments(raw: str | None) -> list[str]:
    if not raw:
        return DEFAULT_SEGMENTS
    parts = [slugify(item) for item in raw.split(",")]
    return [item for item in parts if item]


def write_log(path: Path) -> None:
    if path.exists():
        return
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(LOG_HEADERS)


def write_notes(path: Path, segments: list[str]) -> None:
    if path.exists():
        return
    lines = [
        "# Material Notes",
        "",
        "## Coverage summary",
        "",
        "Fill after collection.",
        "",
        "## Strongest materials",
        "",
        "Fill after scoring.",
        "",
        "## Weak or missing segments",
        "",
        "Fill after review.",
        "",
        "## Source limitations",
        "",
        "Note login walls, missing public evidence, or weak coverage here.",
        "",
        "## Suggested next search moves",
        "",
        "Use this section to track the next best search path.",
        "",
        "## Segment list",
        "",
    ]
    for index, segment in enumerate(segments, start=1):
        lines.append(f"- {index:02d}_{segment}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a material-pack folder scaffold and starter log."
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where the material-pack scaffold should be created.",
    )
    parser.add_argument(
        "--segments",
        help="Comma-separated segment labels. Defaults to the built-in starter list.",
    )
    args = parser.parse_args()

    segments = parse_segments(args.segments)
    root = Path(args.output_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    for index, segment in enumerate(segments, start=1):
        (root / f"{index:02d}_{segment}").mkdir(exist_ok=True)

    (root / "infographics").mkdir(exist_ok=True)
    (root / "99_backup_unused").mkdir(exist_ok=True)
    write_log(root / "material-log.csv")
    write_notes(root / "material-notes.md", segments)

    print(f"Initialized material pack at: {root}")
    print("Segments:")
    for index, segment in enumerate(segments, start=1):
        print(f"  {index:02d}_{segment}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
