/**
 * MakeHuman clothes proxy (MHCLO). Hair is clothes.
 *
 * Clothes vertex = w0*h[v0] + w1*h[v1] + w2*h[v2] + scale*offset
 * See makehuman/shared/proxy.py ProxyRefVert.fromTriple.
 */
export function parseMhclo(text) {
  const proxy = { verts: [], x: null, y: null, z: null };
  for (const line of text.split(/\r?\n/)) {
    const parts = line.trim().split(/\s+/);
    if (!parts[0] || parts[0][0] === "#") continue;
    if (parts[0] === "x_scale") proxy.x = [+parts[1], +parts[2], +parts[3]];
    else if (parts[0] === "y_scale") proxy.y = [+parts[1], +parts[2], +parts[3]];
    else if (parts[0] === "z_scale") proxy.z = [+parts[1], +parts[2], +parts[3]];
    else if (/^\d+$/.test(parts[0]) && parts.length >= 9) {
      proxy.verts.push({
        i: [+parts[0], +parts[1], +parts[2]],
        w: [+parts[3], +parts[4], +parts[5]],
        o: [+parts[6], +parts[7], +parts[8]],
      });
    }
  }
  return proxy;
}

export function parseObjMesh(text) {
  const verts = [];
  const faces = [];
  for (const line of text.split(/\r?\n/)) {
    const parts = line.trim().split(/\s+/);
    if (parts[0] === "v") verts.push([+parts[1], +parts[2], +parts[3]]);
    else if (parts[0] === "f") {
      const corners = parts.slice(1).map((item) => parseInt(item, 10) - 1);
      for (let i = 1; i < corners.length - 1; i += 1) {
        faces.push([corners[0], corners[i], corners[i + 1]]);
      }
    }
  }
  return { verts, faces };
}

export function parseObjVerts(text) {
  const verts = [];
  for (const line of text.split(/\r?\n/)) {
    if (!line.startsWith("v ")) continue;
    const parts = line.split(/\s+/);
    verts.push(+parts[1], +parts[2], +parts[3]);
  }
  return new Float32Array(verts);
}

function axisScale(human, rule, axis) {
  if (!rule) return 1;
  const a = rule[0] * 3 + axis;
  const b = rule[1] * 3 + axis;
  return Math.abs((human[b] - human[a]) / rule[2]);
}

export function fitProxy(proxy, human) {
  const scale = [axisScale(human, proxy.x, 0), axisScale(human, proxy.y, 1), axisScale(human, proxy.z, 2)];
  return proxy.verts.map((vert) => {
    const out = [0, 0, 0];
    for (let n = 0; n < 3; n += 1) {
      const k = vert.i[n] * 3;
      const w = vert.w[n];
      out[0] += human[k] * w;
      out[1] += human[k + 1] * w;
      out[2] += human[k + 2] * w;
    }
    return [out[0] + vert.o[0] * scale[0], out[1] + vert.o[1] * scale[1], out[2] + vert.o[2] * scale[2]];
  });
}

export function applyDeltasToHuman(restHuman, packed, deltas) {
  const human = restHuman.slice();
  const index = packed.index;
  for (let i = 0; i < index.length; i += 1) {
    const o = index[i] * 3;
    const d = i * 3;
    human[o] = restHuman[o] + deltas[d];
    human[o + 1] = restHuman[o + 1] + deltas[d + 1];
    human[o + 2] = restHuman[o + 2] + deltas[d + 2];
  }
  return human;
}
