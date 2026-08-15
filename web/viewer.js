import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";
import { applyChestMorph, bindChestMorph, defaultChestState, loadChestTargets } from "./chest-morph.js";

const SIZES = ["A", "B", "C", "D", "E"];
const AXIS_STEPS = 7;
const FLOORS = [
  { id: "size", label: "чашка", kind: "size" },
  { id: "dist", label: "шире", kind: "axis" },
  { id: "point", label: "острее", kind: "axis" },
  { id: "trans", label: "выше", kind: "axis" },
  { id: "vol", label: "низ", kind: "axis" },
  { id: "nipple", label: "сосок", kind: "axis" },
  { id: "nipplePoint", label: "выступ", kind: "axis" },
];

const sideLeft = document.querySelector("#sideLeft");
const sideRight = document.querySelector("#sideRight");
const canvas = document.querySelector("#view");
const statusEl = document.querySelector("#status");
const stage = document.querySelector(".stage");
const floorButtons = [];
const chestState = defaultChestState();

let chestMode = false;
let lastFloor = "size";

function floorValue(floor) {
  if (floor.kind === "size") return `${SIZES[chestState.sizeIndex]}`;
  return `${chestState[floor.id] + 1}/${AXIS_STEPS}`;
}

function idleStatus() {
  if (!chestMode) return "нажми на грудь";
  const floor = FLOORS.find((item) => item.id === lastFloor) || FLOORS[0];
  return `грудь · ${SIZES[chestState.sizeIndex]} · ${floor.label} ${floorValue(floor)}`;
}

function buildSideBars() {
  for (const floor of FLOORS) {
    const left = document.createElement("button");
    left.type = "button";
    left.dataset.floor = floor.id;
    left.innerHTML = `<span>${floor.label}</span><span class="arr">←</span>`;
    left.setAttribute("aria-label", `${floor.label} меньше`);
    left.addEventListener("click", (event) => {
      event.stopPropagation();
      stepFloor(floor, -1);
    });
    sideLeft.appendChild(left);

    const right = document.createElement("button");
    right.type = "button";
    right.dataset.floor = floor.id;
    right.innerHTML = `<span>${floor.label}</span><span class="arr">→</span>`;
    right.setAttribute("aria-label", `${floor.label} больше`);
    right.addEventListener("click", (event) => {
      event.stopPropagation();
      stepFloor(floor, 1);
    });
    sideRight.appendChild(right);

    floorButtons.push({ floor, left, right });
  }
}

function stepFloor(floor, delta) {
  lastFloor = floor.id;
  if (floor.kind === "size") {
    chestState.sizeIndex = Math.max(0, Math.min(SIZES.length - 1, chestState.sizeIndex + delta));
  } else {
    chestState[floor.id] = Math.max(0, Math.min(AXIS_STEPS - 1, chestState[floor.id] + delta));
  }
  statusEl.textContent = idleStatus();
  updateFloorDisabled();
  applyChestMorph(chestBound, chestState);
}

function updateFloorDisabled() {
  for (const item of floorButtons) {
    if (item.floor.kind === "size") {
      item.left.disabled = chestState.sizeIndex === 0;
      item.right.disabled = chestState.sizeIndex === SIZES.length - 1;
    } else {
      item.left.disabled = chestState[item.floor.id] === 0;
      item.right.disabled = chestState[item.floor.id] === AXIS_STEPS - 1;
    }
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
  const count = floorButtons.length;
  const gap = 3;
  const buttonSize = Math.min(40, Math.max(30, (height - 16 - gap * (count - 1)) / count));
  const stack = count * buttonSize + (count - 1) * gap;
  const chestY = worldToCanvasY(bodyHeight * 0.73);
  let start = chestY - stack / 2;
  start = Math.max(8, Math.min(height - stack - 8, start));
  for (let i = 0; i < floorButtons.length; i += 1) {
    const y = start + i * (buttonSize + gap) + buttonSize / 2;
    const item = floorButtons[i];
    item.left.style.top = `${y}px`;
    item.right.style.top = `${y}px`;
    item.left.style.height = `${buttonSize}px`;
    item.right.style.height = `${buttonSize}px`;
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
  const targetsPromise = loadChestTargets(new URL("./data/chest-targets.json?v=chest-axes", import.meta.url));
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
        applyChestMorph(chestBound, chestState);
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
