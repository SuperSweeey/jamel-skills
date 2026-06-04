#!/usr/bin/env python3
"""Score and grade material candidates from a CSV log."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


SCORE_FIELDS = [
    "score_script_fit",
    "score_visual_clarity",
    "score_cleanliness",
    "score_credibility",
    "score_editing_utility",
]


def parse_score(value: str) -> int:
    value = (value or "").strip()
    if not value:
        return 0
    return int(value)


def grade_row(row: dict[str, str]) -> tuple[str, int, str]:
    scores = {field: parse_score(row.get(field, "")) for field in SCORE_FIELDS}
    total = sum(scores.values())

    hard_fail_reasons = []
    if scores["score_script_fit"] < 4:
        hard_fail_reasons.append("script fit below 4")
    if scores["score_visual_clarity"] < 4:
        hard_fail_reasons.append("visual clarity below 4")

    notes = (row.get("why_it_matches", "") + " " + row.get("core_message", "")).lower()
    for marker in ["title-only", "misaligned", "heavy ads", "unreadable", "blocked"]:
        if marker in notes:
            hard_fail_reasons.append(f"hard filter: {marker}")

    if hard_fail_reasons:
        return "C", total, "; ".join(hard_fail_reasons)
    if total >= 21:
        return "A", total, "passes A-grade threshold"
    if total >= 16:
        return "B", total, "backup-grade threshold"
    return "C", total, "score threshold below 16"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Score and grade material candidates in a CSV log.")
    parser.add_argument("--csv", required=True, help="Path to material-log.csv or a compatible CSV file.")
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Update the input CSV directly. If omitted, a graded copy is written next to it.",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv).expanduser().resolve()
    rows = read_rows(csv_path)
    if not rows:
        print("No data rows found. Nothing to score.")
        return 0

    fieldnames = list(rows[0].keys())
    if "score_total" not in fieldnames:
        fieldnames.append("score_total")
    if "grade_reason" not in fieldnames:
        fieldnames.append("grade_reason")

    for row in rows:
        grade, total, reason = grade_row(row)
        row["quality_grade"] = grade
        row["score_total"] = str(total)
        row["grade_reason"] = reason
        if not row.get("status"):
            row["status"] = "selected" if grade == "A" else "backup" if grade == "B" else "rejected"

    output_path = csv_path if args.in_place else csv_path.with_name(csv_path.stem + "-graded.csv")
    write_rows(output_path, rows, fieldnames)
    print(f"Wrote graded CSV to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
