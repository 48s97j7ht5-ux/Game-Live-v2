/** Load workbench parts. Add a JSON file and list it in manifest.parts to attach a module. */

export async function loadCatalog(manifestUrl) {
  const response = await fetch(manifestUrl);
  if (!response.ok) throw new Error(`manifest ${response.status}`);
  const manifest = await response.json();
  const base = new URL("./", manifestUrl);
  const cache = manifest.cache || "0";
  const parts = [];
  for (const id of manifest.parts) {
    const url = new URL(`${id}.json?v=${cache}`, base);
    const partResponse = await fetch(url);
    if (!partResponse.ok) throw new Error(`part ${id} ${partResponse.status}`);
    const part = await partResponse.json();
    if (part.enabled === false) continue;
    parts.push(part);
  }
  return { manifest, parts };
}

function onBody(part, bodyId) {
  const bodies = part.bodies || (part.kind === "body" ? [part.id] : ["clay"]);
  return bodies.includes(bodyId);
}

export function bodyParts(catalog) {
  return catalog.parts.filter((part) => part.kind === "body");
}

export function bodyPart(catalog, bodyId) {
  return bodyParts(catalog).find((part) => part.id === bodyId) || bodyParts(catalog)[0];
}

export function bodyModel(part, variantId) {
  if (!part) return "./models/base.obj";
  const variant = (part.variants || []).find((item) => item.id === variantId);
  return variant?.model || part.model;
}

export function tapZones(catalog, bodyId = "clay", focusMode = "body") {
  return catalog.parts.filter((part) => {
    if (part.yFrac == null || !(part.floors || []).length) return false;
    if (!onBody(part, bodyId)) return false;
    return (part.focus || "body") === focusMode;
  });
}

export function overlays(catalog, bodyId = "clay") {
  return catalog.parts.filter(
    (part) => part.kind === "overlay" && part.model && !part.choices && onBody(part, bodyId),
  );
}

export function hairPart(catalog, bodyId = "clay") {
  return catalog.parts.find((part) => part.id === "hair" && part.kind === "overlay" && onBody(part, bodyId));
}

export function morphRecipe(catalog, bodyId = "clay") {
  const axes = [];
  let macro = null;
  for (const part of catalog.parts) {
    if (part.kind && part.kind !== "morph") continue;
    if (!onBody(part, bodyId)) continue;
    if (part.macro) macro = part.macro;
    for (const floor of part.floors || []) {
      if (floor.decr && floor.incr) axes.push({ id: floor.id, decr: floor.decr, incr: floor.incr });
    }
  }
  return { macro, axes };
}

export function defaultState(catalog, bodyId = "clay") {
  const recipe = morphRecipe(catalog, bodyId);
  const state = {};
  if (recipe.macro?.sizeIndex) state.sizeIndex = recipe.macro.sizeIndex.default ?? 2;
  for (const axis of recipe.axes) state[axis.id] = 3;
  for (const part of catalog.parts) {
    if (!onBody(part, bodyId)) continue;
    for (const floor of part.floors || []) {
      if (floor.kind === "choice") state[floor.id] = floor.default ?? 0;
    }
  }
  return state;
}

export function sizeLabels(catalog, bodyId = "clay") {
  return morphRecipe(catalog, bodyId).macro?.sizeIndex?.labels || ["A", "B", "C", "D", "E"];
}
