/**
 * UniversalModifier mixer: value -1..+1, weight = |value|, no gain, no mask.
 * Body poses: same packed target format (official-targets-v1).
 */

function key3(x, y, z) {
  return `${x.toFixed(4)},${y.toFixed(4)},${z.toFixed(4)}`;
}

function addWeighted(out, source, weight) {
  if (!weight || !source) return;
  if (source.s && source.d) {
    const slots = source.s;
    const deltas = source.d;
    for (let i = 0; i < slots.length; i += 1) {
      const o = slots[i] * 3;
      const p = i * 3;
      out[o] += deltas[p] * weight;
      out[o + 1] += deltas[p + 1] * weight;
      out[o + 2] += deltas[p + 2] * weight;
    }
    return;
  }
  for (let i = 0; i < out.length; i += 1) {
    out[i] += source[i] * weight;
  }
}

export function axisAmount(step, steps = 7) {
  return (step / (steps - 1)) * 2 - 1;
}

export function mixDeltas(targets, state, restCount, recipe) {
  const mixed = new Float32Array(restCount);
  const macro = recipe?.macro;
  if (macro?.corners && macro.sizeIndex) {
    const table = macro.sizeIndex.t || [];
    const sizeT = table[state.sizeIndex] ?? table[table.length - 1] ?? 1;
    const firm = macro.firmness ?? 0.5;
    const [a, b, c, d] = macro.corners;
    addWeighted(mixed, targets[a], (1 - sizeT) * (1 - firm));
    addWeighted(mixed, targets[b], (1 - sizeT) * firm);
    addWeighted(mixed, targets[c], sizeT * (1 - firm));
    addWeighted(mixed, targets[d], sizeT * firm);
  }
  for (const axis of recipe?.axes || []) {
    const amount = axisAmount(state[axis.id] ?? 3);
    if (!amount) continue;
    const source = amount < 0 ? targets[axis.decr] : targets[axis.incr];
    addWeighted(mixed, source, Math.abs(amount));
  }
  return mixed;
}

export async function loadTargets(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`targets ${response.status}`);
  return response.json();
}

export function bindMorph(group, packed) {
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
  });
  return { packed, bindings };
}

export function applyMorph(bound, state, recipe, poseBound = null, poseKey = null) {
  applyBody(bound, state, recipe, poseBound, poseKey);
}

export function applyBody(morphBound, state, recipe, poseBound = null, poseKey = null, poseDriver = null) {
  if (!morphBound) return;
  const morphDeltas = mixDeltas(
    morphBound.packed.targets,
    state,
    morphBound.packed.index.length * 3,
    recipe,
  );
  let poseDeltas = null;
  if (!poseDriver && poseBound?.packed?.targets && poseKey && poseBound.packed.targets[poseKey]) {
    poseDeltas = new Float32Array(poseBound.packed.index.length * 3);
    addWeighted(poseDeltas, poseBound.packed.targets[poseKey], 1);
  }
  const poseByMesh = poseBound ? new Map(poseBound.bindings.map((item) => [item.mesh, item])) : null;
  for (const item of morphBound.bindings) {
    const poseItem = poseByMesh?.get(item.mesh);
    const position = item.mesh.geometry.getAttribute("position");
    const out = position.array;
    for (let i = 0; i < position.count; i += 1) {
      const o = i * 3;
      out[o] = item.rest[o];
      out[o + 1] = item.rest[o + 1];
      out[o + 2] = item.rest[o + 2];
      const slot = item.slots[i];
      if (slot >= 0) {
        const d = slot * 3;
        out[o] += morphDeltas[d];
        out[o + 1] += morphDeltas[d + 1];
        out[o + 2] += morphDeltas[d + 2];
      }
      if (poseDeltas && poseItem) {
        const pSlot = poseItem.slots[i];
        if (pSlot >= 0) {
          const d = pSlot * 3;
          out[o] += poseDeltas[d];
          out[o + 1] += poseDeltas[d + 1];
          out[o + 2] += poseDeltas[d + 2];
        }
      }
    }
    position.needsUpdate = true;
    if (!poseDriver || !item.mesh.isSkinnedMesh) {
      item.mesh.geometry.computeVertexNormals();
    }
  }
  if (poseDriver) poseDriver.applyRecipe(poseKey);
}
