#!/usr/bin/env bash
# Build overview/overview.pdf from the sources in overview/src/.
#
#   1. tools/gen_overview.py expands the sources with tables and numbers
#      generated from P1's data/*.csv and the pinned P2 snapshot in
#      overview/p2-snapshot/, and writes each Mermaid block to a file;
#   2. mermaid-cli renders each diagram to SVG;
#   3. render.mjs turns the Markdown into HTML and prints it to PDF in Chrome.
#
# Tool versions are pinned by overview/package-lock.json (the same mermaid-cli
# and puppeteer as brief/). Needs Node 22+, Python 3.11+, git, and Chrome or
# Chromium in CHROME_PATH. Output: overview/overview.pdf. Intermediate files
# go to overview/build/, which git ignores.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
: "${CHROME_PATH:?set CHROME_PATH to a Chrome or Chromium binary}"
export CHROME_PATH PUPPETEER_SKIP_DOWNLOAD=1

cd "$HERE"
[ -d node_modules ] || npm ci --ignore-scripts --no-audit --no-fund

rm -rf build
python3 "$ROOT/tools/gen_overview.py" --out build

printf '{"executablePath": "%s", "args": ["--no-sandbox"]}\n' "$CHROME_PATH" > build/puppeteer.json
for src in build/diagrams/*.mmd; do
    npx --no-install mmdc -q -p build/puppeteer.json -c mermaid.json -i "$src" -o "${src%.mmd}.svg" -b white
done

node render.mjs
