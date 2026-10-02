#!/usr/bin/env bash
# Build brief/pdr-brief.pdf from brief/pdr-brief.md.
#
# The deck's diagrams are rendered from the docs' own Mermaid sources, so the
# brief cannot drift from the architecture. Tool versions are pinned by
# brief/package-lock.json. Needs Node 22+ and Chrome or Chromium in CHROME_PATH.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
: "${CHROME_PATH:?set CHROME_PATH to a Chrome or Chromium binary}"
export CHROME_PATH PUPPETEER_SKIP_DOWNLOAD=1

cd "$HERE"
[ -d node_modules ] || npm ci --ignore-scripts --no-audit --no-fund

# Diagram sources: <output name> <markdown file> <index of its mermaid block>.
python3 - "$ROOT" <<'PY'
import re, sys
from pathlib import Path
root = Path(sys.argv[1])
sources = {
    "context": ("docs/04-architecture.md", 0),
    "c2-layers": ("README.md", 0),
}
for name, (md, index) in sources.items():
    blocks = re.findall(r"```mermaid\n(.*?)```", (root / md).read_text(encoding="utf-8"), re.S)
    (root / "brief/assets" / f"{name}.mmd").write_text(blocks[index], encoding="utf-8")
PY

printf '{"executablePath": "%s", "args": ["--no-sandbox"]}\n' "$CHROME_PATH" > puppeteer.json
for src in assets/*.mmd; do
    npx --no-install mmdc -q -p puppeteer.json -i "$src" -o "${src%.mmd}.png" -s 2 -b white
done
rm puppeteer.json

npx --no-install marp --no-stdin pdr-brief.md --pdf --allow-local-files -o pdr-brief.pdf
