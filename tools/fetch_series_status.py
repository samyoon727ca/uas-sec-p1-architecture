#!/usr/bin/env python3
"""Fetch each series repo's series-status.json into data/series-status/<repo>.json.

For every row of data/series.csv except P1, downloads
<base-url>/<repo>/HEAD/series-status.json and writes it unchanged, so
tools/check_series_status.py can check it and tools/render_views.py can use
it. A missing file (HTTP 404) is a warning and leaves any existing snapshot
alone; any other HTTP or network error fails. A snapshot whose repo is no
longer a non-P1 row of series.csv is removed, so a stale file can't keep
failing the checker. The files are not validated here: run
check_series_status.py on them next. Exits 1 on any failure.
Standard library only.

Usage:
    python tools/fetch_series_status.py [--base-url URL] [--data-dir data] [--out-dir data/series-status]
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://raw.githubusercontent.com/samyoon727ca"
REPO_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")
MAX_BYTES = 1 << 20  # a status file is a few KB; refuse anything absurd


def series_repos(data_dir: Path) -> list[str]:
    """Repo names from series.csv, excluding P1 itself."""
    with (data_dir / "series.csv").open(newline="", encoding="utf-8-sig") as f:
        repos = [row["repo"] for row in csv.DictReader(f) if row["p_id"] != "P1"]
    for repo in repos:
        # The name becomes part of a URL and a file name; refuse anything that could escape either.
        if not REPO_NAME.match(repo) or repo.strip(".") == "":
            raise SystemExit(f"series.csv: repo {repo!r} is not a plain repository name")
    return repos


def fetch(url: str) -> bytes | None:
    """The body at url, or None if it does not exist (HTTP 404, or a missing file:// path)."""
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            body = resp.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, FileNotFoundError):
            return None
        raise
    if len(body) > MAX_BYTES:
        raise ValueError(f"larger than {MAX_BYTES} bytes")
    return body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default=BASE_URL,
                        help=f"URL that <repo>/HEAD/series-status.json is appended to (default {BASE_URL})")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data" / "series-status")
    args = parser.parse_args(argv)

    base = args.base_url.rstrip("/")
    repos = series_repos(args.data_dir)
    failed = 0
    if args.out_dir.is_dir():
        for stale in sorted(args.out_dir.glob("*.json")):
            if stale.stem not in repos:
                stale.unlink()
                print(f"REMOVED {stale}: {stale.stem} is not a series repo in series.csv")
    for repo in repos:
        url = f"{base}/{repo}/HEAD/series-status.json"
        out = args.out_dir / f"{repo}.json"
        try:
            body = fetch(url)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            print(f"ERROR   {repo}: {url}: {exc}")
            failed += 1
            continue
        if body is None:
            kept = "kept the existing snapshot" if out.is_file() else "no snapshot"
            print(f"WARNING {repo}: {url} not found; {kept}")
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(body)
        print(f"WROTE   {out}")
    print(f"{'FAIL' if failed else 'PASS'}: {failed} fetch error(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
