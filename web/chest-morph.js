const SIZE_T = [0.42, 0.56, 0.70, 0.85, 1];
const FIRMNESS = 0.5;
const SHAPE_DETAIL = [
  { pointDecr: 0.7, volUp: 0.22 },
  { volDown: 0.85, transDown: 0.42, pointDecr: 0.18 },
  { pointIncr: 0.9, distDecr: 0.22, volUp: 0.12 },
  { distIncr: 0.85, pointDecr: 0.32 },
];

function key3(x, y, z) {
  return `${x.toFixed(4)},${y.toFixed(4)},${z.toFixed(4)}`;
}

function addWeighted(out, source, weight) {
  if (!weight) return;
  for (let i = 0; i < out.length; i += 1) {
    out[i] += source[i] * weight;
  }
}

export function mixChestDeltas(targets, sizeIndex, shapeIndex) {
  const sizeT = SIZE_T[sizeIndex];
  const firm = FIRMNESS;
  const mixed = new Float32Array(targets.minCupMinFirm.length);
  addWeighted(mixed, targets.minCupMinFirm, (1 - sizeT) * (1 - firm));
  addWeighted(mixed, targets.minCupMaxFirm, (1 - sizeT) * firm);
  addWeighted(mixed, targets.maxCupMinFirm, sizeT * (1 - firm));
  addWeighted(mixed, targets.maxCupMaxFirm, sizeT * firm);
  const shapeScale = 0.22 + 0.78 * sizeT;
  const detail = SHAPE_DETAIL[shapeIndex];
  for (const [name, amount] of Object.entries(detail)) {
    addWeighted(mixed, targets[name], amount * shapeScale);
  }
  return mixed;
}

export async function loadChestTargets(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`chest targets ${response.status}`);
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

export function applyChestMorph(bound, sizeIndex, shapeIndex) {
  if (!bound) return;
  const deltas = mixChestDeltas(bound.packed.targets, sizeIndex, shapeIndex);
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
