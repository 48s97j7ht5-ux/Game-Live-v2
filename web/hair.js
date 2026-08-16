/**
 * Hair studio: three head modules (shelf, style, color) share one worn wig.
 * Each floorsFor(id) returns that one row. The head screen concatenates all three.
 * Not helper-hair. Not Blender Hair Editor curves.
 */
import {
  COLOR_KEYS,
  COLORS,
  DEFAULT_OFFICIAL_STYLE,
  HAIR_CACHE,
  OFFICIAL,
  SHELVES,
  loadCommunity,
} from "./hair-catalog.js?v=c40";
import { createWear } from "./hair-wear.js?v=c40";
import { parseObjVerts } from "./mhclo.js?v=c40";

export { HAIR_CACHE, parseObjVerts };

export function createHairStudio({ THREE }) {
  const wear = createWear({ THREE });
  const state = { shelf: 0, style: DEFAULT_OFFICIAL_STYLE, color: 1 };
  let extra = [];
  let setStatus = () => {};
  let requestRedraw = () => {};

  function bind(opts) {
    wear.bind(opts);
    setStatus = opts.setStatus || setStatus;
    requestRedraw = opts.requestRedraw || requestRedraw;
  }

  async function loadExtra() {
    try {
      extra = await loadCommunity();
    } catch {
      extra = [];
    }
  }

  function shelfStyles() {
    return state.shelf === 1 ? extra : OFFICIAL;
  }

  function currentStyle() {
    return shelfStyles()[state.style];
  }

  function currentHex() {
    return COLORS[COLOR_KEYS[state.color]].hex;
  }

  async function apply() {
    const style = currentStyle();
    try {
      await wear.wear(style?.id, currentHex());
    } catch (err) {
      setStatus("причёска: " + (err.message || err));
    }
    requestRedraw();
  }

  function refit() {
    wear.refit(currentStyle()?.id);
  }

  function statusLine() {
    const style = currentStyle();
    const color = COLORS[COLOR_KEYS[state.color]];
    if (!style || style.id === "none") return "голова · без волос";
    const shelf = SHELVES[state.shelf]?.label || "";
    return `голова · ${shelf} · ${style.label} · ${color.label}`;
  }

  function cycleShelf(dir) {
    const next = state.shelf + dir;
    if (next < 0 || next > 1) return;
    if (next === 1 && !extra.length) return;
    state.shelf = next;
    state.style = next === 0 ? DEFAULT_OFFICIAL_STYLE : 0;
    apply();
  }

  function cycleStyle(dir) {
    const list = shelfStyles();
    const next = state.style + dir;
    if (next < 0 || next >= list.length) return;
    state.style = next;
    apply();
  }

  function cycleColor(dir) {
    const next = state.color + dir;
    if (next < 0 || next >= COLOR_KEYS.length) return;
    state.color = next;
    wear.dye(currentHex());
    requestRedraw();
  }

  const modules = {
    "hair-shelf": {
      id: "hair-shelf",
      label: "полка",
      kind: "choice",
      hint: () => SHELVES[state.shelf].label,
      onStep: cycleShelf,
      atMin: () => state.shelf === 0,
      atMax: () => state.shelf === 1 || !extra.length,
    },
    "hair-style": {
      id: "hair-style",
      label: "стиль",
      kind: "choice",
      hint: () => currentStyle()?.label || "",
      onStep: cycleStyle,
      atMin: () => state.style === 0,
      atMax: () => state.style === shelfStyles().length - 1,
    },
    "hair-color": {
      id: "hair-color",
      label: "цвет",
      kind: "choice",
      hint: () => COLORS[COLOR_KEYS[state.color]].label,
      onStep: cycleColor,
      atMin: () => state.color === 0,
      atMax: () => state.color === COLOR_KEYS.length - 1,
    },
  };

  function floorsFor(id) {
    const row = modules[id];
    return row ? [row] : [];
  }

  function dispose() {
    wear.dispose();
  }

  return { bind, loadExtra, apply, refit, statusLine, floorsFor, dispose, state };
}
