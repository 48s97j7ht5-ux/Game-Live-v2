/**
 * Hair is MakeHuman clothes: a wig mesh + MHCLO sitting on the clay.
 * Not helper-hair (that cage is never drawn). Not Blender Hair Editor curves.
 *
 * These wigs are hair cards, not a knit cap. A same-color scalp.obj sits
 * under them so the clay skull does not show through the gaps.
 *
 * First shelf: five CC0 system wigs (bob, long, ponytail, short, braid).
 */
import { applyDeltasToHuman, fitProxy, parseMhclo, parseObjMesh, parseObjVerts } from "./mhclo.js?v=c25";
import { mixDeltas } from "./chest-morph.js?v=c25";

export const HAIR_CACHE = "c25";

const STYLES = [
  { id: "none", label: "нет" },
  { id: "short02", label: "короткая" },
  { id: "bob01", label: "каре" },
  { id: "ponytail01", label: "хвост" },
  { id: "long01", label: "длинная" },
  { id: "braid01", label: "коса" },
];

const COLORS = {
  black: { hex: 0x1a1412, label: "чёрный" },
  chestnut: { hex: 0x3d2418, label: "каштан" },
  russet: { hex: 0x6b4a2b, label: "русый" },
  blond: { hex: 0xc4a066, label: "блонд" },
  ginger: { hex: 0xa85a28, label: "рыжий" },
  gray: { hex: 0x9a9590, label: "седой" },
};

const COLOR_KEYS = Object.keys(COLORS);

export function createHairStudio({ THREE }) {
  const state = { style: 2, color: 1 };
  const cache = new Map();
  let dummy = null;
  let restHuman = null;
  let packed = null;
  let recipe = null;
  let bodyState = null;
  let mesh = null;
  let scalp = null;
  let loadToken = 0;
  let setStatus = () => {};
  let requestRedraw = () => {};

  function bind(opts) {
    dummy = opts.dummy;
    restHuman = opts.restHuman;
    packed = opts.packed || packed;
    recipe = opts.recipe || recipe;
    bodyState = opts.bodyState || bodyState;
    setStatus = opts.setStatus || setStatus;
    requestRedraw = opts.requestRedraw || requestRedraw;
  }

  function matcapFromDummy() {
    let matcap = null;
    dummy?.traverse((child) => {
      if (!matcap && child.isMesh && child.material?.matcap) matcap = child.material.matcap;
    });
    return matcap;
  }

  function humanNow() {
    if (!restHuman) return null;
    if (!packed || !bodyState) return restHuman;
    return applyDeltasToHuman(restHuman, packed, mixDeltas(packed.targets, bodyState, packed.index.length * 3, recipe));
  }

  async function loadStyle(id) {
    if (cache.has(id)) return cache.get(id);
    const base = new URL(`../models/hair/${id}/${id}`, import.meta.url);
    const [mhcloText, objText] = await Promise.all([
      fetch(`${base.href}.mhclo?v=${HAIR_CACHE}`).then((r) => {
        if (!r.ok) throw new Error("нет " + id);
        return r.text();
      }),
      fetch(`${base.href}.obj?v=${HAIR_CACHE}`).then((r) => {
        if (!r.ok) throw new Error("нет " + id);
        return r.text();
      }),
    ]);
    const asset = { proxy: parseMhclo(mhcloText), obj: parseObjMesh(objText) };
    cache.set(id, asset);
    return asset;
  }

  async function loadScalp() {
    if (cache.has("scalp")) return cache.get("scalp");
    const url = new URL(`../models/hair/scalp.obj?v=${HAIR_CACHE}`, import.meta.url).href;
    const obj = parseObjMesh(await fetch(url).then((r) => {
      if (!r.ok) throw new Error("нет шапочки");
      return r.text();
    }));
    cache.set("scalp", obj);
    return obj;
  }

  function detach() {
    for (const item of [mesh, scalp]) {
      if (!item || !dummy) continue;
      dummy.remove(item);
      if (item.geometry) item.geometry.dispose();
      if (item.material && item.material.dispose) item.material.dispose();
    }
    mesh = null;
    scalp = null;
  }

  function buildGeometry(asset, fitted) {
    const positions = [];
    for (const face of asset.obj.faces) {
      for (const index of face) {
        const vert = fitted[index] || asset.obj.verts[index];
        if (!vert) continue;
        positions.push(vert[0], vert[1], vert[2]);
      }
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geometry.computeVertexNormals();
    return geometry;
  }

  async function apply() {
    if (!dummy) return;
    const token = (loadToken += 1);
    const style = STYLES[state.style];
    if (!style || style.id === "none") {
      detach();
      requestRedraw();
      return;
    }
    try {
      const [asset, scalpObj] = await Promise.all([loadStyle(style.id), loadScalp().catch(() => null)]);
      if (token !== loadToken || !dummy) return;
      const human = humanNow();
      if (!human) throw new Error("нет тела");
      const fitted = fitProxy(asset.proxy, human);
      const geometry = buildGeometry(asset, fitted);
      const matcap = matcapFromDummy();
      const color = COLORS[COLOR_KEYS[state.color]].hex;
      detach();
      mesh = new THREE.Mesh(
        geometry,
        new THREE.MeshMatcapMaterial({ color, matcap, side: THREE.DoubleSide }),
      );
      mesh.name = "hair";
      mesh.renderOrder = 2;
      dummy.add(mesh);
      if (scalpObj) {
        scalp = new THREE.Mesh(
          buildGeometry({ obj: scalpObj }, scalpObj.verts),
          new THREE.MeshMatcapMaterial({
            color,
            matcap,
            side: THREE.FrontSide,
            polygonOffset: true,
            polygonOffsetFactor: -1,
            polygonOffsetUnits: -1,
          }),
        );
        scalp.name = "hair-scalp";
        scalp.renderOrder = 1;
        dummy.add(scalp);
      }
    } catch (err) {
      setStatus("причёска: " + (err.message || err));
    }
    requestRedraw();
  }

  function refit() {
    if (!mesh || !dummy) return;
    const style = STYLES[state.style];
    if (!style || style.id === "none") return;
    const asset = cache.get(style.id);
    if (!asset) return;
    const fitted = fitProxy(asset.proxy, humanNow());
    mesh.geometry.dispose();
    mesh.geometry = buildGeometry(asset, fitted);
  }

  function statusLine() {
    const style = STYLES[state.style];
    const color = COLORS[COLOR_KEYS[state.color]];
    if (style.id === "none") return "голова · без волос";
    return `голова · ${style.label} · ${color.label}`;
  }

  function cycle(key, list, dir) {
    const next = state[key] + dir;
    if (next < 0 || next >= list.length) return;
    state[key] = next;
    apply();
  }

  function floors() {
    return [
      {
        id: "hair-style",
        label: "стиль",
        kind: "choice",
        hint: () => STYLES[state.style].label,
        onStep: (dir) => cycle("style", STYLES, dir),
        atMin: () => state.style === 0,
        atMax: () => state.style === STYLES.length - 1,
      },
      {
        id: "hair-color",
        label: "цвет",
        kind: "choice",
        hint: () => COLORS[COLOR_KEYS[state.color]].label,
        onStep: (dir) => cycle("color", COLOR_KEYS, dir),
        atMin: () => state.color === 0,
        atMax: () => state.color === COLOR_KEYS.length - 1,
      },
    ];
  }

  function dispose() {
    loadToken += 1;
    detach();
  }

  return { bind, apply, refit, statusLine, floors, dispose, state };
}

export { parseObjVerts };
