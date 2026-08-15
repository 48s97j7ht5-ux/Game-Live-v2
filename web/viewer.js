import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";

const canvas = document.querySelector("#view");
const statusEl = document.querySelector("#status");
const MODEL_URLS = [
  "./models/base.obj",
  "https://cdn.jsdelivr.net/gh/48s97j7ht5-ux/Game-Live-Web@main/engine/anny/mpfb2/3dobjs/base.obj",
];

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x2a2c31);

const camera = new THREE.PerspectiveCamera(32, 1, 0.01, 2000);
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.target.set(0, 0.9, 0);

scene.add(new THREE.HemisphereLight(0xffffff, 0x334455, 1.1));
const key = new THREE.DirectionalLight(0xffffff, 1.4);
key.position.set(-1.2, 2.2, 1.8);
scene.add(key);
const fill = new THREE.DirectionalLight(0x99aacc, 0.45);
fill.position.set(1.4, 0.6, 0.8);
scene.add(fill);

const skin = new THREE.MeshToonMaterial({ color: 0xdbb396 });
let dummy = null;
let radius = 1.7;

function partName(object) {
  let node = object;
  while (node) {
    const name = (node.name || "").toLowerCase().trim();
    if (name) return name;
    node = node.parent;
  }
  return "";
}

function hideHelpers(group) {
  group.traverse((child) => {
    if (!child.isMesh) return;
    const name = partName(child);
    child.visible = name === "body" || name.startsWith("body");
  });
}

function resize() {
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  camera.aspect = width / Math.max(height, 1);
  camera.updateProjectionMatrix();
  renderer.setSize(width, height, false);
}

function frameObject(object) {
  const box = new THREE.Box3();
  object.updateWorldMatrix(true, true);
  object.traverse((child) => {
    if (child.isMesh && child.visible) {
      box.expandByObject(child);
    }
  });
  if (box.isEmpty()) box.setFromObject(object);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  object.position.sub(center);
  object.position.y += size.y * 0.5;
  radius = Math.max(size.y, size.x, size.z);
  camera.near = Math.max(radius / 200, 0.01);
  camera.far = Math.max(radius * 40, 200);
  camera.updateProjectionMatrix();
  controls.minDistance = radius * 1.2;
  controls.maxDistance = radius * 8;
  controls.target.set(0, size.y * 0.52, 0);
  key.position.set(-radius, radius * 1.4, radius);
  fill.position.set(radius * 0.9, radius * 0.4, radius * 0.5);
  setView("front");
}

function setView(name) {
  const height = controls.target.y;
  const distance = radius * 3.4;
  const views = {
    front: new THREE.Vector3(0, height, distance),
    three: new THREE.Vector3(distance * 0.55, height * 1.05, distance * 0.9),
    side: new THREE.Vector3(distance, height, 0.001),
    back: new THREE.Vector3(0, height, -distance),
  };
  camera.position.copy(views[name]);
  controls.update();
  document.querySelectorAll("nav button").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === name);
  });
}

async function loadModel() {
  const loader = new OBJLoader();
  let lastError = null;
  for (const url of MODEL_URLS) {
    try {
      const group = await loader.loadAsync(url);
      group.traverse((child) => {
        if (child.isMesh) {
          child.material = skin;
          child.geometry.computeVertexNormals();
        }
      });
      hideHelpers(group);
      dummy = group;
      scene.add(dummy);
      frameObject(dummy);
      statusEl.textContent = "крути пальцем";
      return;
    } catch (error) {
      lastError = error;
    }
  }
  statusEl.textContent = "не удалось загрузить тело";
  throw lastError;
}

document.querySelectorAll("nav button").forEach((button) => {
  button.addEventListener("click", () => setView(button.dataset.view));
});

window.addEventListener("resize", resize);
resize();
loadModel().catch((error) => console.error(error));

function tick() {
  controls.update();
  renderer.render(scene, camera);
  requestAnimationFrame(tick);
}
tick();
