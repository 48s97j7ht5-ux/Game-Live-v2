/**
 * Lips/cheeks tint on the clay body itself — not a decal, not a texture.
 * Two face modules (lips, cheeks) paint vertex colors on fixed raw-vertex
 * zones (web/data/makeup-zones.json). Matches vertex positions the same
 * way chest-morph.js binds morphs: round-key lookup, not the OBJLoader's
 * reordered buffer index.
 */
const SKIN_HEX = 0xffd7b8;

const LIP_COLORS = [
  { key: "none", label: "без", hex: null },
  { key: "nude", label: "нюд", hex: 0xcf9a86 },
  { key: "pink", label: "розовая", hex: 0xd9647d },
  { key: "coral", label: "коралловая", hex: 0xe06a5a },
  { key: "red", label: "красная", hex: 0xb01f2e },
  { key: "wine", label: "вишнёвая", hex: 0x7a1f34 },
];

const CHEEK_COLORS = [
  { key: "none", label: "без", hex: null },
  { key: "pink", label: "розовые", hex: 0xe58aa0 },
  { key: "coral", label: "коралловые", hex: 0xe8927a },
  { key: "peach", label: "персиковые", hex: 0xf0a888 },
];

function key3(x, y, z) {
  return `${x.toFixed(4)},${y.toFixed(4)},${z.toFixed(4)}`;
}

function hexToRgb(hex) {
  return [((hex >> 16) & 255) / 255, ((hex >> 8) & 255) / 255, (hex & 255) / 255];
}

function lerp3(a, b, t) {
  return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
}

export function createMakeupStudio({ THREE }) {
  const skinRgb = hexToRgb(SKIN_HEX);
  const state = { lip: 0, cheek: 0 };
  let zonesPromise = null;
  let bodyMesh = null;
  let lipBufferIdx = [];
  let cheekBufferIdx = [];
  let requestRedraw = () => {};

  async function loadZones(cache) {
    if (!zonesPromise) {
      const url = new URL(`./data/makeup-zones.json?v=${cache || "0"}`, import.meta.url);
      zonesPromise = fetch(url)
        .then((r) => {
          if (!r.ok) throw new Error("нет зон мейкапа");
          return r.json();
        })
        .catch(() => ({ lips: [], cheeks: [] }));
    }
    return zonesPromise;
  }

  function findBufferIndices(restHuman, rawIds) {
    if (!bodyMesh) return [];
    const wanted = new Set(rawIds);
    const lookup = new Map();
    for (const id of wanted) {
      const o = id * 3;
      lookup.set(key3(restHuman[o], restHuman[o + 1], restHuman[o + 2]), true);
    }
    const position = bodyMesh.geometry.getAttribute("position");
    const out = [];
    for (let i = 0; i < position.count; i += 1) {
      const o = i * 3;
      if (lookup.has(key3(position.array[o], position.array[o + 1], position.array[o + 2]))) out.push(i);
    }
    return out;
  }

  async function bind(opts) {
    bodyMesh = opts.bodyMesh || null;
    requestRedraw = opts.requestRedraw || requestRedraw;
    if (!bodyMesh || !opts.restHuman) {
      lipBufferIdx = [];
      cheekBufferIdx = [];
      return;
    }
    const zones = await loadZones(opts.cache);
    lipBufferIdx = findBufferIndices(opts.restHuman, zones.lips || []);
    cheekBufferIdx = findBufferIndices(opts.restHuman, zones.cheeks || []);
    apply();
  }

  function paint(indices, hex, amount) {
    if (!bodyMesh) return;
    const color = bodyMesh.geometry.getAttribute("color");
    if (!color) return;
    const rgb = hex == null ? skinRgb : lerp3(skinRgb, hexToRgb(hex), amount);
    for (const i of indices) {
      const o = i * 3;
      color.array[o] = rgb[0];
      color.array[o + 1] = rgb[1];
      color.array[o + 2] = rgb[2];
    }
    color.needsUpdate = true;
  }

  function apply() {
    paint(cheekBufferIdx, CHEEK_COLORS[state.cheek].hex, 0.35);
    paint(lipBufferIdx, LIP_COLORS[state.lip].hex, 0.6);
    requestRedraw();
  }

  function cycleLip(dir) {
    const next = state.lip + dir;
    if (next < 0 || next >= LIP_COLORS.length) return;
    state.lip = next;
    apply();
  }

  function cycleCheek(dir) {
    const next = state.cheek + dir;
    if (next < 0 || next >= CHEEK_COLORS.length) return;
    state.cheek = next;
    apply();
  }

  function statusLine() {
    return `лицо · губы ${LIP_COLORS[state.lip].label} · щёки ${CHEEK_COLORS[state.cheek].label}`;
  }

  const modules = {
    "makeup-lips": {
      id: "makeup-lips",
      label: "губы",
      kind: "choice",
      hint: () => LIP_COLORS[state.lip].label,
      onStep: cycleLip,
      atMin: () => state.lip === 0,
      atMax: () => state.lip === LIP_COLORS.length - 1,
    },
    "makeup-cheeks": {
      id: "makeup-cheeks",
      label: "щёки",
      kind: "choice",
      hint: () => CHEEK_COLORS[state.cheek].label,
      onStep: cycleCheek,
      atMin: () => state.cheek === 0,
      atMax: () => state.cheek === CHEEK_COLORS.length - 1,
    },
  };

  function floorsFor(id) {
    const row = modules[id];
    return row ? [row] : [];
  }

  function dispose() {
    bodyMesh = null;
    lipBufferIdx = [];
    cheekBufferIdx = [];
  }

  return { bind, apply, floorsFor, statusLine, dispose, state };
}
