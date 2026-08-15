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

export function tapZones(catalog) {
  return catalog.parts.filter((part) => part.yFrac != null && (part.floors || []).length);
}

export function overlays(catalog) {
  return catalog.parts.filter((part) => part.kind === "overlay" && part.model);
}

export function morphRecipe(catalog) {
  const axes = [];
  let macro = null;
  for (const part of catalog.parts) {
    if (part.kind && part.kind !== "morph") continue;
    if (part.macro) macro = part.macro;
    for (const floor of part.floors || []) {
      if (floor.decr && floor.incr) axes.push({ id: floor.id, decr: floor.decr, incr: floor.incr });
    }
  }
  return { macro, axes };
}

export function defaultState(catalog) {
  const recipe = morphRecipe(catalog);
  const state = {};
  if (recipe.macro?.sizeIndex) state.sizeIndex = recipe.macro.sizeIndex.default ?? 2;
  for (const axis of recipe.axes) state[axis.id] = 3;
  return state;
}

export function sizeLabels(catalog) {
  return morphRecipe(catalog).macro?.sizeIndex?.labels || ["A", "B", "C", "D", "E"];
}
