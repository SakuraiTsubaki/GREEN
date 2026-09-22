#!/usr/bin/env python3
"""Validate committed GREEN baseline metadata without requiring ROM binaries."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINES = ROOT / "research" / "green-baselines.csv"

EXPECTED = {
    "green-jp-rev0-rom": (524288, "6576b4e0979e93d4a6fa02db893c294b7aeab3b841b1acc8658bc10b3554f33c"),
    "green-jp-reva-rom": (524288, "3f0dc460ca8d06be1c9ac96307c939c0ea7baa366b40c2f1f4ad63242b6c4816"),
    "green-jp-rev0-save-snapshot": (32768, "34cf10beeb0a9a2659178ce1a809f25ccabcdee32468171147068da916ad556b"),
    "green-jp-reva-save-snapshot": (32768, "b59e8c4eb1e0ac8b0bfeb859c322d5c2402c259be616a0a2a7f2ffcae1cc2fb2"),
}


def main() -> int:
    with BASELINES.open(newline="", encoding="utf-8") as f:
        rows = {row["id"]: row for row in csv.DictReader(f)}

    if set(rows) != set(EXPECTED):
        raise SystemExit(f"baseline IDs changed: {sorted(rows)}")

    for key, (size, sha256) in EXPECTED.items():
        row = rows[key]
        if int(row["size"]) != size:
            raise SystemExit(f"{key}: unexpected size")
        if row["sha256"] != sha256:
            raise SystemExit(f"{key}: unexpected sha256")

    print("GREEN baseline metadata: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
