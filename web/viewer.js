import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";
import { applyChestMorph, bindChestMorph, loadChestTargets } from "./chest-morph.js";

const SIZES = ["A", "B", "C", "D", "E"];
const SHAPES = ["круглая", "капля", "коническая", "широкая"];
const FLOORS = [
  { id: "size", label: "размер" },
  { id: "shape", label: "форма" },
];

const sideLeft = document.querySelector("#sideLeft");
const sideRight = document.querySelector("#sideRight");
const canvas = document.querySelector("#view");
const statusEl = document.querySelector("#status");
const stage = document.querySelector(".stage");
const floorButtons = [];

let chestMode = false;
let sizeIndex = 2;
let shapeIndex = 1;

function idleStatus() {
  return chestMode ? `грудь · ${SIZES[sizeIndex]} · ${SHAPES[shapeIndex]}` : "нажми на грудь";
}

function buildSideBars() {
  for (const floor of FLOORS) {
    const left = document.createElement("button");
    left.type = "button";
    left.dataset.floor = floor.id;
    left.dataset.dir = "left";
    left.setAttribute("aria-label", `${floor.label} меньше`);
    left.textContent = "←";
    left.addEventListener("click", (event) => {
      event.stopPropagation();
      stepFloor(floor.id, -1);
    });
    sideLeft.appendChild(left);

    const right = document.createElement("button");
    right.type = "button";
    right.dataset.floor = floor.id;
    right.dataset.dir = "right";
    right.setAttribute("aria-label", `${floor.label} больше`);
    right.textContent = "→";
    right.addEventListener("click", (event) => {
      event.stopPropagation();
      stepFloor(floor.id, 1);
    });
    sideRight.appendChild(right);

    floorButtons.push({ floor: floor.id, left, right });
  }
}

function stepFloor(floor, delta) {
  if (floor === "size") {
    sizeIndex = Math.max(0, Math.min(SIZES.length - 1, sizeIndex + delta));
  } else {
    shapeIndex = Math.max(0, Math.min(SHAPES.length - 1, shapeIndex + delta));
  }
  statusEl.textContent = idleStatus();
  updateFloorDisabled();
  applyChestMorph(chestBound, sizeIndex, shapeIndex);
}

function updateFloorDisabled() {
  for (const item of floorButtons) {
    const atStart = item.floor === "size" ? sizeIndex === 0 : shapeIndex === 0;
    const atEnd =
      item.floor === "size" ? sizeIndex === SIZES.length - 1 : shapeIndex === SHAPES.length - 1;
    item.left.disabled = atStart;
    item.right.disabled = atEnd;
  }
}

function setChestMode(on) {
  chestMode = on;
  sideLeft.classList.toggle("open", on);
  sideRight.classList.toggle("open", on);
  statusEl.textContent = dummy ? idleStatus() : statusEl.textContent;
  updateFloorDisabled();
  layoutFloorButtons();
}

function worldToCanvasY(worldY) {
  const point = new THREE.Vector3(0, worldY, 0);
  point.project(camera);
  return (-point.y * 0.5 + 0.5) * canvas.clientHeight;
}

function layoutFloorButtons() {
  if (!chestMode) return;
  const height = Math.max(canvas.clientHeight, 1);
  const buttonSize = 42;
  const gap = 12;
  const chestY = worldToCanvasY(bodyHeight * 0.73);
  const topY = Math.max(buttonSize / 2 + 8, chestY - (buttonSize + gap) / 2);
  const bottomY = Math.min(height - buttonSize / 2 - 8, topY + buttonSize + gap);
  const ys = { size: topY, shape: bottomY };
  for (const item of floorButtons) {
    const y = ys[item.floor];
    item.left.style.top = `${y}px`;
    item.right.style.top = `${y}px`;
    item.left.style.transform = "translateY(-50%)";
    item.right.style.transform = "translateY(-50%)";
  }
}

function inChestBand(clientY) {
  const rect = canvas.getBoundingClientRect();
  const y = clientY - rect.top;
  const chestY = worldToCanvasY(bodyHeight * 0.73);
  const half = Math.max(56, canvas.clientHeight * 0.09);
  return Math.abs(y - chestY) <= half;
}
const MODEL_URLS = [
  "./models/base.obj",
  "https://cdn.jsdelivr.net/gh/48s97j7ht5-ux/Game-Live-Web@main/engine/anny/mpfb2/3dobjs/base.obj",
];

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x2a2c31);

const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.01, 2000);
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.enableZoom = false;
controls.enablePan = false;
controls.screenSpacePanning = false;
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
let chestBound = null;
let radius = 1.7;
let bodyHeight = 1.6;
let targetPx = 400;
let currentView = "front";

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

function applyScale() {
  const width = Math.max(canvas.clientWidth, 1);
  const height = Math.max(canvas.clientHeight, 1);
  const worldH = bodyHeight * (height / targetPx);
  const worldW = worldH * (width / height);
  camera.left = -worldW / 2;
  camera.right = worldW / 2;
  camera.top = worldH / 2;
  camera.bottom = -worldH / 2;
  camera.updateProjectionMatrix();
  layoutFloorButtons();
}

function resize() {
  renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);
  applyScale();
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
  bodyHeight = Math.max(size.y, 0.01);
  radius = Math.max(size.y, size.x, size.z);
  camera.near = Math.max(radius / 200, 0.01);
  camera.far = Math.max(radius * 40, 200);
  controls.minDistance = radius * 0.8;
  controls.maxDistance = radius * 12;
  controls.target.set(0, size.y * 0.5, 0);
  key.position.set(-radius, radius * 1.4, radius);
  fill.position.set(radius * 0.9, radius * 0.4, radius * 0.5);
  setHeight(targetPx);
  setView("front");
}

function lockCenter() {
  const y = bodyHeight * 0.5;
  controls.target.set(0, y, 0);
  if (dummy) {
    dummy.position.x = 0;
    dummy.position.z = 0;
  }
}

function setHeight(px) {
  targetPx = px;
  applyScale();
  document.querySelectorAll(".heights button").forEach((button) => {
    button.classList.toggle("active", Number(button.dataset.height) === targetPx);
  });
}

function setView(name) {
  currentView = name;
  const height = controls.target.y;
  const distance = radius * 3.4;
  const views = {
    front: new THREE.Vector3(0, height, distance),
    three: new THREE.Vector3(distance * 0.55, height * 1.05, distance * 0.9),
    side: new THREE.Vector3(distance, height, 0.001),
    back: new THREE.Vector3(0, height, -distance),
  };
  camera.position.copy(views[name]);
  camera.up.set(0, 1, 0);
  lockCenter();
  controls.update();
  document.querySelectorAll(".bottom button").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === name);
  });
}

async function loadModel() {
  const loader = new OBJLoader();
  const targetsPromise = loadChestTargets(new URL("./data/chest-targets.json?v=chest-firm", import.meta.url));
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
      try {
        chestBound = bindChestMorph(dummy, await targetsPromise);
        applyChestMorph(chestBound, sizeIndex, shapeIndex);
      } catch (error) {
        console.error(error);
      }
      statusEl.textContent = idleStatus();
      return;
    } catch (error) {
      lastError = error;
    }
  }
  statusEl.textContent = "не удалось загрузить тело";
  throw lastError;
}

document.querySelectorAll(".bottom button").forEach((button) => {
  button.addEventListener("click", () => setView(button.dataset.view));
});
document.querySelectorAll(".heights button").forEach((button) => {
  button.addEventListener("click", () => setHeight(Number(button.dataset.height)));
});

let pointerStart = null;
stage.addEventListener("pointerdown", (event) => {
  if (event.target.closest("button")) return;
  pointerStart = { x: event.clientX, y: event.clientY };
});
stage.addEventListener("pointerup", (event) => {
  if (!pointerStart) return;
  const dx = event.clientX - pointerStart.x;
  const dy = event.clientY - pointerStart.y;
  pointerStart = null;
  if (event.target.closest("button")) return;
  if (Math.hypot(dx, dy) > 12) return;
  if (!dummy) return;
  if (inChestBand(event.clientY)) {
    setChestMode(!chestMode);
    return;
  }
  if (chestMode) setChestMode(false);
});
stage.addEventListener("pointercancel", () => {
  pointerStart = null;
});

function tick() {
  controls.update();
  lockCenter();
  renderer.render(scene, camera);
  layoutFloorButtons();
  requestAnimationFrame(tick);
}

buildSideBars();
updateFloorDisabled();
window.addEventListener("resize", resize);
resize();
loadModel().catch((error) => console.error(error));
tick();
