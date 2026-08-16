/**
 * Hair studio — MakeHuman clothes type Hair.
 *
 * Official rules (makehumancommunity docs):
 * - Hair is clothes (data/hair), not a body morph and not helper-hair.
 * - Each style is a mesh + MHCLO proxy. Helper-hair is a fitting cage only
 *   and is never drawn.
 * - Bangs are a second clothes layer in community packs, not part of the bob.
 * - MPFB Hair Editor drives Blender curves (frizz, curl, clump…). Those
 *   knobs are not applied to a mesh shell.
 *
 * This module loads the packed OBJ shells, tints them, and applies length /
 * volume as a small look around the crown pivot — not as fake physics.
 */

export const HAIR_CACHE = "c20";

const COLORS = {
  black: { hex: 0x1a1412, label: "чёрный" },
  chestnut: { hex: 0x3d2418, label: "каштан" },
  russet: { hex: 0x6b4a2b, label: "русый" },
  blond: { hex: 0xc4a066, label: "блонд" },
  ginger: { hex: 0xa85a28, label: "рыжий" },
  gray: { hex: 0x9a9590, label: "седой" },
};

const STYLES = [
  { id: "short", label: "короткая" },
  { id: "bob", label: "каре" },
  { id: "long", label: "длинная" },
  { id: "none", label: "нет" },
];

const BANGS = [
  { id: "none", label: "нет", file: "" },
  { id: "brow", label: "брови", file: "bangs_brow" },
  { id: "face", label: "в лицо", file: "bangs_face" },
];

const COLOR_KEYS = Object.keys(COLORS);
const AXIS_STEPS = 7;
const STYLE_PIVOT_Y = 8.2;
const BANGS_PIVOT_Y = 7.95;

function axisAmount(step) {
  return (step / (AXIS_STEPS - 1)) * 2 - 1;
}

export function createHairStudio({ THREE }) {
  const state = {
    style: 1,
    bangs: 0,
    color: 1,
    length: 3,
    volume: 3,
  };

  let dummy = null;
  let loader = null;
  let getBodyKind = () => "clay";
  let setStatus = () => {};
  let requestRedraw = () => {};
  const cache = new Map();
  const attached = { style: null, bangs: null };
  let loadToken = 0;

  function bind(opts) {
    dummy = opts.dummy;
    loader = opts.loader;
    getBodyKind = opts.getBodyKind || getBodyKind;
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

  function loadMesh(file) {
    if (cache.has(file)) return Promise.resolve(cache.get(file).clone());
    const url = new URL(`../models/hair/${file}.obj?v=${HAIR_CACHE}`, import.meta.url).href;
    return new Promise((resolve, reject) => {
      loader.load(
        url,
        (group) => {
          cache.set(file, group);
          resolve(group.clone());
        },
        undefined,
        reject
      );
    });
  }

  function tint(root) {
    const hex = COLORS[COLOR_KEYS[state.color]].hex;
    const mat = new THREE.MeshMatcapMaterial({
      color: hex,
      matcap: matcapFromDummy(),
      side: THREE.DoubleSide,
      flatShading: true,
    });
    root.traverse((child) => {
      if (child.isMesh) {
        child.material = mat;
        child.renderOrder = 2;
        child.visible = true;
        if (child.geometry?.computeVertexNormals) child.geometry.computeVertexNormals();
      }
    });
  }

  function applyLook(pivot, { lengthGain, volumeGain }) {
    const length = axisAmount(state.length);
    const volume = axisAmount(state.volume);
    pivot.scale.set(1 + volume * volumeGain, 1 + length * lengthGain, 1 + volume * volumeGain * 0.55);
  }

  function detach(slot) {
    const mesh = attached[slot];
    if (!mesh || !dummy) {
      attached[slot] = null;
      return;
    }
    dummy.remove(mesh);
    mesh.traverse((child) => {
      if (child.geometry) child.geometry.dispose();
    });
    attached[slot] = null;
  }

  async function attach(slot, file, pivotY, lookOpts, token) {
    const group = await loadMesh(file);
    if (token !== loadToken || !dummy) {
      group.traverse((child) => {
        if (child.geometry) child.geometry.dispose();
      });
      return false;
    }
    detach(slot);
    tint(group);
    const pivot = new THREE.Group();
    pivot.name = slot === "style" ? "hair" : "bangs";
    pivot.position.set(0, pivotY, 0);
    group.position.set(0, -pivotY, 0);
    pivot.add(group);
    applyLook(pivot, lookOpts);
    dummy.add(pivot);
    attached[slot] = pivot;
    return true;
  }

  async function apply() {
    if (!dummy) return;
    const token = (loadToken += 1);
    if (getBodyKind() !== "clay") {
      detach("style");
      detach("bangs");
      requestRedraw();
      return;
    }
    try {
      const style = STYLES[state.style];
      if (!style || style.id === "none") detach("style");
      else {
        const ok = await attach(
          "style",
          style.id,
          STYLE_PIVOT_Y,
          { lengthGain: 0.28, volumeGain: 0.2 },
          token
        );
        if (!ok) return;
      }
      const bangs = BANGS[state.bangs];
      if (!bangs?.file || style?.id === "none") detach("bangs");
      else {
        const ok = await attach(
          "bangs",
          bangs.file,
          BANGS_PIVOT_Y,
          { lengthGain: 0.08, volumeGain: 0.1 },
          token
        );
        if (!ok) return;
      }
    } catch (err) {
      setStatus("причёска: " + (err.message || err));
    }
    requestRedraw();
  }

  function statusLine() {
    if (getBodyKind() !== "clay") return "причёска: только глина";
    const style = STYLES[state.style];
    const bangs = BANGS[state.bangs];
    const color = COLORS[COLOR_KEYS[state.color]];
    if (style.id === "none") return "причёска · нет";
    const fringe = bangs.id !== "none" ? ` · чёлка ${bangs.label}` : "";
    return `причёска · ${style.label} · ${color.label}${fringe}`;
  }

  function cycle(key, list, dir) {
    const next = state[key] + dir;
    if (next < 0 || next >= list.length) return;
    state[key] = next;
    apply();
  }

  function stepAxis(key, dir) {
    state[key] = Math.max(0, Math.min(AXIS_STEPS - 1, state[key] + dir));
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
        id: "hair-bangs",
        label: "чёлка",
        kind: "choice",
        hint: () => BANGS[state.bangs].label,
        onStep: (dir) => cycle("bangs", BANGS, dir),
        atMin: () => state.bangs === 0,
        atMax: () => state.bangs === BANGS.length - 1,
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
      {
        id: "hair-length",
        label: "длина",
        kind: "axis",
        hint: () => `${state.length + 1}/${AXIS_STEPS}`,
        onStep: (dir) => stepAxis("length", dir),
        atMin: () => state.length === 0,
        atMax: () => state.length === AXIS_STEPS - 1,
      },
      {
        id: "hair-volume",
        label: "объём",
        kind: "axis",
        hint: () => `${state.volume + 1}/${AXIS_STEPS}`,
        onStep: (dir) => stepAxis("volume", dir),
        atMin: () => state.volume === 0,
        atMax: () => state.volume === AXIS_STEPS - 1,
      },
    ];
  }

  function dispose() {
    loadToken += 1;
    detach("style");
    detach("bangs");
  }

  return { bind, apply, statusLine, floors, dispose, state };
}
