/**
 * Official MakeHuman HighPolyEyes on the clay. Not helper-l-eye / helper-r-eye.
 * Same MHCLO fit as hair. Texture is the official brown iris, not clay matcap.
 */
import { applyDeltasToHuman, fitProxy, parseMhclo, parseObjTextured } from "./mhclo.js?v=c43";
import { mixDeltas } from "./chest-morph.js?v=c43";

export function createEyes({ THREE }) {
  let dummy = null;
  let restHuman = null;
  let packed = null;
  let recipe = null;
  let bodyState = null;
  let cacheToken = "0";
  let asset = null;
  let texture = null;
  let mesh = null;
  let loadToken = 0;

  function bind(opts) {
    dummy = opts.dummy;
    restHuman = opts.restHuman;
    packed = opts.packed || packed;
    recipe = opts.recipe || recipe;
    bodyState = opts.bodyState || bodyState;
    if (opts.cache) cacheToken = opts.cache;
  }

  function humanNow() {
    if (!restHuman) return null;
    if (!packed || !bodyState) return restHuman;
    return applyDeltasToHuman(restHuman, packed, mixDeltas(packed.targets, bodyState, packed.index.length * 3, recipe));
  }

  async function loadAsset() {
    if (asset) return asset;
    const base = new URL("../models/eyes/high-poly", import.meta.url);
    const [mhcloText, objText] = await Promise.all([
      fetch(`${base.href}.mhclo?v=${cacheToken}`).then((r) => {
        if (!r.ok) throw new Error("нет глаз");
        return r.text();
      }),
      fetch(`${base.href}.obj?v=${cacheToken}`).then((r) => {
        if (!r.ok) throw new Error("нет глаз");
        return r.text();
      }),
    ]);
    asset = { proxy: parseMhclo(mhcloText), obj: parseObjTextured(objText) };
    return asset;
  }

  async function loadTexture() {
    if (texture) return texture;
    const url = new URL(`../models/eyes/brown_eye.png?v=${cacheToken}`, import.meta.url).href;
    const loader = new THREE.TextureLoader();
    texture = await new Promise((resolve, reject) => {
      loader.load(url, resolve, undefined, reject);
    });
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.flipY = true;
    return texture;
  }

  function buildGeometry(data, fitted) {
    const positions = [];
    const uv = [];
    for (const face of data.obj.faces) {
      for (const corner of face) {
        const vert = fitted[corner.v] || data.obj.verts[corner.v];
        if (!vert) continue;
        positions.push(vert[0], vert[1], vert[2]);
        const t = data.obj.uvs[corner.vt] || [0, 0];
        uv.push(t[0], t[1]);
      }
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
    geometry.computeVertexNormals();
    return geometry;
  }

  function detach() {
    if (!mesh || !dummy) {
      mesh = null;
      return;
    }
    dummy.remove(mesh);
    if (mesh.geometry) mesh.geometry.dispose();
    if (mesh.material && mesh.material.dispose) mesh.material.dispose();
    mesh = null;
  }

  async function wear() {
    if (!dummy) return;
    const token = (loadToken += 1);
    const data = await loadAsset();
    const map = await loadTexture();
    if (token !== loadToken || !dummy) return;
    const human = humanNow();
    if (!human) throw new Error("нет тела");
    const fitted = fitProxy(data.proxy, human);
    detach();
    mesh = new THREE.Mesh(
      buildGeometry(data, fitted),
      new THREE.MeshPhongMaterial({
        map,
        color: 0xffffff,
        specular: 0x333333,
        shininess: 70,
        transparent: true,
        alphaTest: 0.04,
      }),
    );
    mesh.name = "eyes";
    mesh.renderOrder = 3;
    dummy.add(mesh);
  }

  function refit() {
    if (!mesh || !dummy || !asset) return;
    const fitted = fitProxy(asset.proxy, humanNow());
    mesh.geometry.dispose();
    mesh.geometry = buildGeometry(asset, fitted);
  }

  function dispose() {
    loadToken += 1;
    detach();
  }

  return { bind, wear, refit, dispose };
}
