export const SIZE_T = [0.42, 0.56, 0.7, 0.85, 1];
export const FIRMNESS = 0.5;
export const AXIS_STEPS = 7;
export const AXIS_MID = 3;

const CHEST_AXES = [
  { id: "dist", decr: "distDecr", incr: "distIncr" },
  { id: "point", decr: "pointDecr", incr: "pointIncr" },
  { id: "trans", decr: "transDown", incr: "transUp" },
  { id: "vol", decr: "volUp", incr: "volDown" },
  { id: "nipple", decr: "nippleSizeDecr", incr: "nippleSizeIncr" },
  { id: "nipplePoint", decr: "nipplePointDecr", incr: "nipplePointIncr" },
];
const STOMACH_AXES = [
  { id: "belly", decr: "stomachBellyDecr", incr: "stomachBellyIncr" },
  { id: "tone", decr: "stomachToneDecr", incr: "stomachToneIncr" },
  { id: "navelY", decr: "navelDown", incr: "navelUp" },
  { id: "navelZ", decr: "navelIn", incr: "navelOut" },
];
const AXES = [...CHEST_AXES, ...STOMACH_AXES];

function key3(x, y, z) {
  return `${x.toFixed(4)},${y.toFixed(4)},${z.toFixed(4)}`;
}

function addWeighted(out, source, weight) {
  if (!weight || !source) return;
  for (let i = 0; i < out.length; i += 1) {
    out[i] += source[i] * weight;
  }
}

export function axisAmount(step) {
  return (step / (AXIS_STEPS - 1)) * 2 - 1;
}

export function defaultChestState() {
  return {
    sizeIndex: 2,
    dist: AXIS_MID,
    point: AXIS_MID,
    trans: AXIS_MID,
    vol: AXIS_MID,
    nipple: AXIS_MID,
    nipplePoint: AXIS_MID,
    belly: AXIS_MID,
    tone: AXIS_MID,
    navelY: AXIS_MID,
    navelZ: AXIS_MID,
  };
}

export function mixChestDeltas(targets, state) {
  const sizeT = SIZE_T[state.sizeIndex];
  const firm = FIRMNESS;
  const mixed = new Float32Array(targets.minCupMinFirm.length);
  addWeighted(mixed, targets.minCupMinFirm, (1 - sizeT) * (1 - firm));
  addWeighted(mixed, targets.minCupMaxFirm, (1 - sizeT) * firm);
  addWeighted(mixed, targets.maxCupMinFirm, sizeT * (1 - firm));
  addWeighted(mixed, targets.maxCupMaxFirm, sizeT * firm);
  for (const axis of AXES) {
    const amount = axisAmount(state[axis.id]);
    if (amount < 0) addWeighted(mixed, targets[axis.decr], -amount);
    else if (amount > 0) addWeighted(mixed, targets[axis.incr], amount);
  }
  return mixed;
}

export async function loadChestTargets(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`body targets ${response.status}`);
  return response.json();
}

export function bindChestMorph(group, packed) {
  const lookup = new Map();
  for (let i = 0; i < packed.index.length; i += 1) {
    const o = i * 3;
    lookup.set(key3(packed.rest[o], packed.rest[o + 1], packed.rest[o + 2]), i);
  }
  const bindings = [];
  group.traverse((child) => {
    if (!child.isMesh || !child.visible || !child.geometry?.getAttribute("position")) return;
    const position = child.geometry.getAttribute("position");
    const rest = position.array.slice();
    const slots = new Int32Array(position.count);
    let hits = 0;
    for (let i = 0; i < position.count; i += 1) {
      const o = i * 3;
      const slot = lookup.get(key3(rest[o], rest[o + 1], rest[o + 2]));
      slots[i] = slot === undefined ? -1 : slot;
      if (slot !== undefined) hits += 1;
    }
    if (hits) bindings.push({ mesh: child, rest, slots });
    else console.warn("chest morph: no matching verts on", child.name);
  });
  return { packed, bindings };
}

export function applyChestMorph(bound, state) {
  if (!bound) return;
  const deltas = mixChestDeltas(bound.packed.targets, state);
  for (const item of bound.bindings) {
    const position = item.mesh.geometry.getAttribute("position");
    const out = position.array;
    for (let i = 0; i < position.count; i += 1) {
      const o = i * 3;
      const slot = item.slots[i];
      out[o] = item.rest[o];
      out[o + 1] = item.rest[o + 1];
      out[o + 2] = item.rest[o + 2];
      if (slot < 0) continue;
      const d = slot * 3;
      out[o] += deltas[d];
      out[o + 1] += deltas[d + 1];
      out[o + 2] += deltas[d + 2];
    }
    position.needsUpdate = true;
    item.mesh.geometry.computeVertexNormals();
  }
}
