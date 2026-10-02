#!/usr/bin/env bash
# Validate model/sysml/*.sysml with the OMG SysML v2 Pilot Implementation.
#
# Downloads the pinned Jupyter SysML kernel release (it bundles the Pilot
# Implementation and the standard library) into .cache/sysml, verifies its
# SHA-256, and runs tools/sysml/ValidateSysML.java over the model files.
# Requires Java 21+, curl, unzip and sha256sum.
set -euo pipefail

RELEASE="2026-08"
KERNEL="jupyter-sysml-kernel-0.62.0"
SHA256="5a015ed3f2b3d2dae14e9c3fb9602d9e1fef5f9ce33cf396c422329405cc3cb2"
URL="https://github.com/Systems-Modeling/SysML-v2-Pilot-Implementation/releases/download/${RELEASE}/${KERNEL}.zip"

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CACHE="${SYSML_CACHE:-$ROOT/.cache/sysml}"
JAR="$CACHE/sysml/${KERNEL}-all.jar"
LIBRARY="$CACHE/sysml/sysml.library/"

if [ ! -f "$JAR" ]; then
    mkdir -p "$CACHE"
    echo "Downloading ${KERNEL} (Pilot Implementation ${RELEASE})"
    curl -sSfL --retry 3 -o "$CACHE/${KERNEL}.zip" "$URL"
    echo "${SHA256}  $CACHE/${KERNEL}.zip" | sha256sum --check --quiet
    unzip -q -o "$CACHE/${KERNEL}.zip" -d "$CACHE"
    rm "$CACHE/${KERNEL}.zip"
fi

# Order matters: the security model imports the architecture.
FILES=("$ROOT/model/sysml/uas_architecture.sysml")
if [ -f "$ROOT/model/sysml/uas_security.sysml" ]; then
    FILES+=("$ROOT/model/sysml/uas_security.sysml")
fi

# The library loader prints one "Reading ..." line per library file; drop them.
java -cp "$JAR" "$ROOT/tools/sysml/ValidateSysML.java" "$LIBRARY" "${FILES[@]}" 2>/dev/null \
    | grep -v '^Reading ' | sed "s#$ROOT/##"
exit "${PIPESTATUS[0]}"
