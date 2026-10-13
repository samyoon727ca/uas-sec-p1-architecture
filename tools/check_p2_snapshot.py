#!/usr/bin/env python3
"""Check that overview/p2-snapshot/ holds byte-for-byte copies of P2 at the pinned commit.

Reads the repo and commit from overview/p2-snapshot/pin.txt. Every other file
in that folder must equal the file at the same path in P2 at that commit,
fetched from raw.githubusercontent.com. Needs network access; CI runs it.
Exits 1 on any mismatch. Standard library only.

Usage:
    python tools/check_p2_snapshot.py
"""
from __future__ import annotations

import hashlib
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "overview" / "p2-snapshot"
COMMIT = re.compile(r"^[0-9a-f]{40}$")


def read_pin(path: Path) -> tuple[str, str]:
    fields = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    repo, commit = fields.get("repo", ""), fields.get("commit", "")
    if not re.match(r"^[\w.-]+/[\w.-]+$", repo) or not COMMIT.match(commit):
        raise SystemExit(f"{path.name}: needs 'repo: owner/name' and a full 40-character 'commit'")
    return repo, commit


def snapshot_files(folder: Path = SNAPSHOT) -> list[str]:
    """Paths of the copied files, relative to the snapshot folder (pin.txt excluded)."""
    return sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*")
                  if p.is_file() and p != folder / "pin.txt")


def main() -> int:
    repo, commit = read_pin(SNAPSHOT / "pin.txt")
    files = snapshot_files()
    if not files:
        raise SystemExit("overview/p2-snapshot holds no files")
    bad = 0
    for rel in files:
        url = f"https://raw.githubusercontent.com/{repo}/{commit}/{rel}"
        local = (SNAPSHOT / rel).read_bytes()
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                upstream = resp.read()
        except urllib.error.HTTPError as exc:
            print(f"MISSING {rel}: HTTP {exc.code} for P2 {commit[:7]}")
            bad += 1
            continue
        same = upstream == local
        bad += not same
        print(f"{'OK   ' if same else 'DIFF '} {rel} sha256 {hashlib.sha256(local).hexdigest()[:16]}"
              + ("" if same else f" (P2 {commit[:7]}: {hashlib.sha256(upstream).hexdigest()[:16]})"))
    print(f"{'PASS' if not bad else 'FAIL'}: overview/p2-snapshot vs {repo}@{commit[:7]}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
