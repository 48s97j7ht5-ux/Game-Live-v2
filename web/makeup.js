/**
 * Makeup on the official hm08 UV — not vertex colours.
 *
 * Official default.mhmat: shaderConfig vertexColors false.
 * Official skin shader samples texture2D on the body UV.
 * Which pixels: official mouth lip-volume + lateral width/angles-up,
 * packed as UV triangles (ext-up skipped on hm08 — chin falloff).
 */
const SKIN_HEX = 0xffd7b8;
const MAP_SIZE = 1024;

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

function hexToRgb(hex) {
  return [((hex >> 16) & 255) / 255, ((hex >> 8) & 255) / 255, (hex & 255) / 255];
}

function lerp3(a, b, t) {
  return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
}

function mapTint(skin, makeup, amount) {
  const desired = lerp3(skin, makeup, amount);
  return [
    desired[0] / Math.max(skin[0], 1e-4),
    desired[1] / Math.max(skin[1], 1e-4),
    desired[2] / Math.max(skin[2], 1e-4),
  ];
}

export function createMakeupStudio({ THREE }) {
  const skinRgb = hexToRgb(SKIN_HEX);
  const state = { lip: 0, cheek: 0 };
  let zonesPromise = null;
  let material = null;
  let lipUv = [];
  let cheekUv = [];
  let mapCanvas = null;
  let mapCtx = null;
  let mapTexture = null;
  let requestRedraw = () => {};

  async function loadZones(cache) {
    if (!zonesPromise) {
      const url = new URL(`./data/makeup-zones.json?v=${cache || "0"}`, import.meta.url);
      zonesPromise = fetch(url)
        .then((r) => {
          if (!r.ok) throw new Error("нет зон мейкапа");
          return r.json();
        })
        .catch(() => ({ lipUv: [], cheekUv: [] }));
    }
    return zonesPromise;
  }

  function ensureMap() {
    if (mapTexture) return;
    mapCanvas = document.createElement("canvas");
    mapCanvas.width = MAP_SIZE;
    mapCanvas.height = MAP_SIZE;
    mapCtx = mapCanvas.getContext("2d");
    mapTexture = new THREE.CanvasTexture(mapCanvas);
    mapTexture.colorSpace = THREE.SRGBColorSpace;
    mapTexture.flipY = true;
  }

  function fillTris(tris, rgb) {
    const ctx = mapCtx;
    const s = MAP_SIZE;
    const css = `rgb(${Math.round(rgb[0] * 255)} ${Math.round(rgb[1] * 255)} ${Math.round(rgb[2] * 255)})`;
    ctx.fillStyle = css;
    ctx.strokeStyle = css;
    ctx.lineWidth = 1.1;
    ctx.lineJoin = "round";
    for (const t of tris) {
      ctx.beginPath();
      ctx.moveTo(t[0] * s, (1 - t[1]) * s);
      ctx.lineTo(t[2] * s, (1 - t[3]) * s);
      ctx.lineTo(t[4] * s, (1 - t[5]) * s);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }
  }

  async function bind(opts) {
    material = opts.material || opts.bodyMesh?.material || null;
    requestRedraw = opts.requestRedraw || requestRedraw;
    const zones = await loadZones(opts.cache);
    lipUv = zones.lipUv || [];
    cheekUv = zones.cheekUv || [];
    apply();
  }

  function apply() {
    if (!material) return;
    const lipHex = LIP_COLORS[state.lip].hex;
    const cheekHex = CHEEK_COLORS[state.cheek].hex;
    if (lipHex == null && cheekHex == null) {
      if (material.map) {
        material.map = null;
        material.needsUpdate = true;
      }
      requestRedraw();
      return;
    }
    ensureMap();
    mapCtx.fillStyle = "#ffffff";
    mapCtx.fillRect(0, 0, MAP_SIZE, MAP_SIZE);
    if (cheekHex != null) fillTris(cheekUv, mapTint(skinRgb, hexToRgb(cheekHex), 0.5));
    if (lipHex != null) fillTris(lipUv, mapTint(skinRgb, hexToRgb(lipHex), 0.88));
    mapTexture.needsUpdate = true;
    if (material.map !== mapTexture) {
      material.map = mapTexture;
      material.needsUpdate = true;
    }
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
    if (material?.map === mapTexture) {
      material.map = null;
      material.needsUpdate = true;
    }
    material = null;
    lipUv = [];
    cheekUv = [];
  }

  return { bind, apply, floorsFor, statusLine, dispose, state };
}
