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
if [[ -d "$ROOT/models/mblab" ]]; then
  cp -a "$ROOT/models/mblab" "$DEST/models/mblab"
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
  web/parts/manifest.json
  web/data/body-targets.json
  web/vendor/three.module.js
  web/vendor/loaders/OBJLoader.js
  models/base.obj
  models/mblab/f_an01.obj
  models/mblab/f_an02.obj
  models/mblab/m_an01.obj
  models/hair/short.obj
  models/hair/bob.obj
  models/hair/long.obj
  index.html
)
for rel in "${required[@]}"; do
  if [[ ! -f "$DEST/$rel" ]]; then
    echo "pages artifact missing $rel" >&2
    exit 1
  fi
done

echo "assembled $DEST"
