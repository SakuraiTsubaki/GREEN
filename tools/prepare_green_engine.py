#!/usr/bin/env python3
"""Verify and prepare GREEN's pinned pokeemerald-expansion checkout."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

PIN = "75b806a3ab57a81ff1eb6179288981f0b3cc3050"
ROOT = Path(__file__).resolve().parents[1]
PATCH_DIR = ROOT / "patches" / "pokeemerald-expansion"


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def patch_state(engine_dir: Path, patch: Path) -> str:
    if git(engine_dir, "apply", "--check", str(patch), check=False).returncode == 0:
        return "pending"
    if git(engine_dir, "apply", "--reverse", "--check", str(patch), check=False).returncode == 0:
        return "already-applied"
    return "conflict"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine-dir", type=Path, required=True)
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()

    engine = args.engine_dir.resolve()
    head = git(engine, "rev-parse", "HEAD").stdout.strip()
    if head != PIN:
        raise SystemExit(f"wrong engine ref: expected {PIN}, got {head}")

    rows = []
    for patch in sorted(PATCH_DIR.glob("*.patch")):
        state = patch_state(engine, patch.resolve())
        if state == "conflict":
            raise SystemExit(f"patch does not apply cleanly: {patch.name}")
        if state == "pending" and not args.check_only:
            git(engine, "apply", str(patch.resolve()))
            state = "applied"
        rows.append({"patch": patch.name, "state": state})

    print(json.dumps({
        "engine": "rh-hideout/pokeemerald-expansion",
        "ref": head,
        "build": "leafgreen",
        "check_only": args.check_only,
        "patches": rows,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
