#!/usr/bin/env bash
# Build the GitHub Pages tree. The workflow and tests must use this script
# so the live site cannot silently drop morphs, vendor, or data.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-"$ROOT/dist"}"

rm -rf "$DEST"
mkdir -p "$DEST/models" "$DEST/factory/out"
cp "$ROOT/index.html" "$DEST/"
if [[ -f "$ROOT/.nojekyll" ]]; then
  cp "$ROOT/.nojekyll" "$DEST/"
else
  touch "$DEST/.nojekyll"
fi
cp -a "$ROOT/web" "$DEST/web"
if [[ -f "$ROOT/models/base.obj" ]]; then
  cp "$ROOT/models/base.obj" "$DEST/models/base.obj"
else
  echo "missing models/base.obj" >&2
  exit 1
fi
if [[ -d "$ROOT/models/hair" ]]; then
  cp -a "$ROOT/models/hair" "$DEST/models/hair"
fi
if [[ -f "$ROOT/factory/out/front.png" ]]; then
  cp "$ROOT/factory/out/front.png" "$DEST/factory/out/front.png"
fi

required=(
  web/viewer.js
  web/viewer.css
  web/chest-morph.js
  web/registry.js
  web/hair.js
  web/mhclo.js
  web/parts/manifest.json
  web/data/body-targets.json
  web/vendor/three.module.js
  web/vendor/loaders/OBJLoader.js
  models/base.obj
  models/hair/bob01/bob01.obj
  models/hair/bob01/bob01.mhclo
  models/hair/scalp.obj
  models/hair/short01/short01.obj
  models/hair/short02/short02.obj
  models/hair/short03/short03.obj
  models/hair/short04/short04.obj
  models/hair/bob02/bob02.obj
  models/hair/afro01/afro01.obj
  models/hair/long01/long01.obj
  models/hair/ponytail01/ponytail01.obj
  models/hair/braid01/braid01.obj
  index.html
)
for rel in "${required[@]}"; do
  if [[ ! -f "$DEST/$rel" ]]; then
    echo "pages artifact missing $rel" >&2
    exit 1
  fi
done

echo "assembled $DEST"
