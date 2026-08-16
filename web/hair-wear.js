/**
 * Put a MakeHuman wig on the clay. Not helper-hair. Not Hair Editor curves.
 * Color tint is a separate paint step so dye never reloads the mesh.
 */
import { applyDeltasToHuman, fitProxy, parseMhclo, parseObjMesh } from "./mhclo.js?v=c45";
import { mixDeltas } from "./chest-morph.js?v=c45";
import { HAIR_CACHE } from "./hair-catalog.js?v=c45";

export function createWear({ THREE }) {
  const cache = new Map();
  let dummy = null;
  let restHuman = null;
  let packed = null;
  let recipe = null;
  let bodyState = null;
  let mesh = null;
  let scalp = null;
  let loadToken = 0;

  function bind(opts) {
    dummy = opts.dummy;
    restHuman = opts.restHuman;
    packed = opts.packed || packed;
    recipe = opts.recipe || recipe;
    bodyState = opts.bodyState || bodyState;
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
    const obj = parseObjMesh(
      await fetch(url).then((r) => {
        if (!r.ok) throw new Error("нет шапочки");
        return r.text();
      }),
    );
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

  function dye(hex) {
    if (mesh?.material?.color) mesh.material.color.setHex(hex);
    if (scalp?.material?.color) scalp.material.color.setHex(hex);
  }

  async function wear(styleId, hex) {
    if (!dummy) return;
    const token = (loadToken += 1);
    if (!styleId || styleId === "none") {
      detach();
      return;
    }
    const [asset, scalpObj] = await Promise.all([loadStyle(styleId), loadScalp().catch(() => null)]);
    if (token !== loadToken || !dummy) return;
    const human = humanNow();
    if (!human) throw new Error("нет тела");
    const fitted = fitProxy(asset.proxy, human);
    const geometry = buildGeometry(asset, fitted);
    const matcap = matcapFromDummy();
    detach();
    mesh = new THREE.Mesh(geometry, new THREE.MeshMatcapMaterial({ color: hex, matcap, side: THREE.DoubleSide }));
    mesh.name = "hair";
    mesh.renderOrder = 2;
    dummy.add(mesh);
    if (scalpObj) {
      scalp = new THREE.Mesh(
        buildGeometry({ obj: scalpObj }, scalpObj.verts),
        new THREE.MeshMatcapMaterial({
          color: hex,
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
  }

  function refit(styleId) {
    if (!mesh || !dummy || !styleId || styleId === "none") return;
    const asset = cache.get(styleId);
    if (!asset) return;
    const fitted = fitProxy(asset.proxy, humanNow());
    mesh.geometry.dispose();
    mesh.geometry = buildGeometry(asset, fitted);
  }

  function dispose() {
    loadToken += 1;
    detach();
  }

  return { bind, wear, dye, refit, dispose };
}
