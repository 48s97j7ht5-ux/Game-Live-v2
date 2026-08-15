import * as THREE from "three";
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
const MODEL_URLS = ["./models/base.obj?v=local"];

function makeClayMatcap() {
  const size = 256;
  const board = document.createElement("canvas");
  board.width = size;
  board.height = size;
  const ctx = board.getContext("2d");
  const img = ctx.createImageData(size, size);
  const data = img.data;
  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      const nx = (x / (size - 1)) * 2 - 1;
      const ny = 1 - (y / (size - 1)) * 2;
      const r2 = nx * nx + ny * ny;
      const i = (y * size + x) * 4;
      if (r2 > 1) {
        data[i] = 32;
        data[i + 1] = 30;
        data[i + 2] = 28;
        data[i + 3] = 255;
        continue;
      }
      const nz = Math.sqrt(1 - r2);
      const wrap = Math.max(0, nx * -0.32 + ny * 0.48 + nz * 0.78);
      const spec = Math.pow(Math.max(0, nx * -0.18 + ny * 0.42 + nz * 0.88), 28) * 0.4;
      const rim = Math.pow(1 - nz, 1.6) * 0.22;
      const t = Math.min(1, wrap * 0.82 + 0.16 + spec - rim);
      data[i] = Math.round(88 + t * 152);
      data[i + 1] = Math.round(68 + t * 128);
      data[i + 2] = Math.round(54 + t * 108);
      data[i + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
  const texture = new THREE.CanvasTexture(board);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1c1e24);

const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.01, 2000);
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

scene.add(new THREE.HemisphereLight(0xffffff, 0x334455, 1.1));
const key = new THREE.DirectionalLight(0xffffff, 1.4);
key.position.set(-1.2, 2.2, 1.8);
scene.add(key);
const fill = new THREE.DirectionalLight(0x99aacc, 0.45);
fill.position.set(1.4, 0.6, 0.8);
scene.add(fill);

const skin = new THREE.MeshMatcapMaterial({
  color: 0xffd7b8,
  matcap: makeClayMatcap(),
});
let dummy = null;
let chestBound = null;
let radius = 1.7;
let bodyHeight = 1.6;
let targetPx = 400;
let yawIndex = 0;
const TURN_STOPS = [
  { yaw: 0, name: "перед" },
  { yaw: 22.5, name: "¾" },
  { yaw: 45, name: "½" },
  { yaw: 90, name: "бок" },
  { yaw: 135, name: "½" },
  { yaw: 157.5, name: "¾" },
  { yaw: 180, name: "зад" },
  { yaw: 202.5, name: "¾" },
  { yaw: 225, name: "½" },
  { yaw: 270, name: "бок" },
  { yaw: 315, name: "½" },
  { yaw: 337.5, name: "¾" },
];
const turnLabel = document.querySelector("#turnLabel");

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
  key.position.set(-radius, radius * 1.4, radius);
  fill.position.set(radius * 0.9, radius * 0.4, radius * 0.5);
  setHeight(targetPx);
  yawIndex = 0;
  placeCamera();
}

function lockCenter() {
  if (dummy) {
    dummy.position.x = 0;
    dummy.position.z = 0;
  }
}

function lookAtYaw(yawDeg, lift = 1) {
  const y = bodyHeight * 0.5;
  const distance = radius * 3.4;
  const yaw = (yawDeg * Math.PI) / 180;
  camera.position.set(Math.sin(yaw) * distance, y * lift, Math.cos(yaw) * distance);
  camera.up.set(0, 1, 0);
  camera.lookAt(0, y, 0);
}

function placeCamera() {
  const stop = TURN_STOPS[yawIndex];
  lookAtYaw(stop.yaw);
  lockCenter();
  if (turnLabel) turnLabel.textContent = stop.name;
}

function stepTurn(delta) {
  yawIndex = (yawIndex + delta + TURN_STOPS.length) % TURN_STOPS.length;
  placeCamera();
}

function setHeight(px) {
  targetPx = px;
  applyScale();
  document.querySelectorAll(".heights button").forEach((button) => {
    button.classList.toggle("active", Number(button.dataset.height) === targetPx);
  });
  placeCamera();
}

async function loadModel() {
  const loader = new OBJLoader();
  const targetsPromise = loadChestTargets(new URL("./data/chest-targets.json?v=turn-arrows", import.meta.url));
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

document.querySelector("#turnLeft").addEventListener("click", (event) => {
  event.stopPropagation();
  stepTurn(1);
});
document.querySelector("#turnRight").addEventListener("click", (event) => {
  event.stopPropagation();
  stepTurn(-1);
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
