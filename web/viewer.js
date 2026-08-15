import * as THREE from "three";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";
import { applyMorph, bindMorph, loadTargets } from "./chest-morph.js?v=c13";
import { defaultState, loadCatalog, morphRecipe, overlays, sizeLabels, tapZones } from "./registry.js?v=c13";

const AXIS_STEPS = 7;

const sideLeft = document.querySelector("#sideLeft");
const sideRight = document.querySelector("#sideRight");
const canvas = document.querySelector("#view");
const statusEl = document.querySelector("#status");
const stage = document.querySelector(".stage");
const floorButtons = [];

let catalog = { manifest: { hints: {} }, parts: [] };
let recipe = { axes: [] };
let sizes = ["A", "B", "C", "D", "E"];
let bodyState = {};
let zones = [];
let editZone = null;
let lastFloor = "";

function zoneById(id) {
  return zones.find((zone) => zone.id === id);
}

function currentFloors() {
  return zoneById(editZone)?.floors || [];
}

function floorValue(floor) {
  if (floor.kind === "size") return `${sizes[bodyState.sizeIndex] || ""}`;
  return `${bodyState[floor.id] + 1}/${AXIS_STEPS}`;
}

function idleStatus() {
  if (!editZone) {
    const hints = catalog.manifest.hints || {};
    return hints[currentView()] || hints.default || "";
  }
  const floor = currentFloors().find((item) => item.id === lastFloor) || currentFloors()[0];
  const zone = zoneById(editZone);
  const cup = floor?.kind === "size" || editZone === "chest" ? ` · ${sizes[bodyState.sizeIndex]}` : "";
  return `${zone.label}${cup} · ${floor.label} ${floorValue(floor)}`;
}

function clearSideBars() {
  sideLeft.innerHTML = "";
  sideRight.innerHTML = "";
  floorButtons.length = 0;
}

function buildSideBars() {
  clearSideBars();
  for (const floor of currentFloors()) {
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
    bodyState.sizeIndex = Math.max(0, Math.min(sizes.length - 1, bodyState.sizeIndex + delta));
  } else {
    const now = Number.isFinite(bodyState[floor.id]) ? bodyState[floor.id] : 3;
    bodyState[floor.id] = Math.max(0, Math.min(AXIS_STEPS - 1, now + delta));
  }
  statusEl.textContent = idleStatus();
  updateFloorDisabled();
  applyMorph(morphBound, bodyState, recipe);
}

function updateFloorDisabled() {
  for (const item of floorButtons) {
    if (item.floor.kind === "size") {
      item.left.disabled = bodyState.sizeIndex === 0;
      item.right.disabled = bodyState.sizeIndex === sizes.length - 1;
    } else {
      item.left.disabled = bodyState[item.floor.id] === 0;
      item.right.disabled = bodyState[item.floor.id] === AXIS_STEPS - 1;
    }
  }
}

function setEditZone(name) {
  editZone = name;
  lastFloor = currentFloors()[0]?.id || "";
  buildSideBars();
  const open = Boolean(name);
  sideLeft.classList.toggle("open", open);
  sideRight.classList.toggle("open", open);
  statusEl.textContent = dummy ? idleStatus() : statusEl.textContent;
  updateFloorDisabled();
  layoutFloorButtons();
}

function toggleZone(name) {
  setEditZone(editZone === name ? null : name);
}

function worldToCanvasY(worldY) {
  const point = new THREE.Vector3(0, worldY, 0);
  point.project(camera);
  return (-point.y * 0.5 + 0.5) * canvas.clientHeight;
}

function layoutFloorButtons() {
  if (!editZone) return;
  const height = Math.max(canvas.clientHeight, 1);
  const count = floorButtons.length;
  if (!count) return;
  const gap = 3;
  const buttonSize = Math.min(40, Math.max(30, (height - 16 - gap * (count - 1)) / count));
  const stack = count * buttonSize + (count - 1) * gap;
  const zoneY = worldToCanvasY(bodyHeight * zoneById(editZone).yFrac);
  let start = zoneY - stack / 2;
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

function hitZone(clientY) {
  const rect = canvas.getBoundingClientRect();
  const y = clientY - rect.top;
  const half = Math.max(52, canvas.clientHeight * 0.08);
  let best = null;
  let bestDist = half;
  for (const zone of zones) {
    if (!zoneAllowed(zone.id)) continue;
    const dist = Math.abs(y - worldToCanvasY(bodyHeight * zone.yFrac));
    if (dist <= bestDist) {
      best = zone.id;
      bestDist = dist;
    }
  }
  return best;
}

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
let morphBound = null;
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

function currentView() {
  const yaw = TURN_STOPS[yawIndex].yaw;
  if (yaw === 0) return "front";
  if (yaw === 22.5 || yaw === 337.5) return "front34";
  if (yaw === 45 || yaw === 315) return "frontHalf";
  if (yaw === 90 || yaw === 270) return "side";
  if (yaw === 135 || yaw === 225) return "backHalf";
  if (yaw === 157.5 || yaw === 202.5) return "back34";
  if (yaw === 180) return "back";
  return "front";
}

function zoneAllowed(name) {
  return Boolean(zoneById(name)?.views?.includes(currentView()));
}

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
  if (editZone && !zoneAllowed(editZone)) setEditZone(null);
  else if (dummy) statusEl.textContent = idleStatus();
}

function setHeight(px) {
  targetPx = px;
  applyScale();
  document.querySelectorAll(".heights button").forEach((button) => {
    button.classList.toggle("active", Number(button.dataset.height) === targetPx);
  });
  placeCamera();
}

async function loadOverlays(parent) {
  const loader = new OBJLoader();
  for (const part of overlays(catalog)) {
    try {
      const group = await loader.loadAsync(`${part.model}?v=${catalog.manifest.cache}`);
      group.name = part.id;
      parent.add(group);
    } catch (error) {
      console.warn("overlay skip", part.id, error);
    }
  }
}

async function loadModel() {
  const loader = new OBJLoader();
  const bodyUrl = `${catalog.manifest.body || "./models/base.obj"}?v=${catalog.manifest.cache}`;
  const group = await loader.loadAsync(bodyUrl);
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
  statusEl.textContent = idleStatus();
  await loadOverlays(dummy);
  try {
    const morphUrl = new URL(
      `${catalog.manifest.morphs || "./data/body-targets.json"}?v=${catalog.manifest.cache}`,
      import.meta.url,
    );
    const packed = await loadTargets(morphUrl);
    morphBound = bindMorph(dummy, packed);
    applyMorph(morphBound, bodyState, recipe);
  } catch (error) {
    console.error(error);
    statusEl.textContent = "тело есть, правки формы не загрузились";
  }
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
  const zone = hitZone(event.clientY);
  if (zone) {
    toggleZone(zone);
    return;
  }
  if (editZone) setEditZone(null);
});
stage.addEventListener("pointercancel", () => {
  pointerStart = null;
});

function tick() {
  lockCenter();
  pixelFilter.render(scene, camera, targetPx);
  layoutFloorButtons();
  requestAnimationFrame(tick);
}

let pixelFilter = {
  render(mainScene, mainCamera) {
    renderer.render(mainScene, mainCamera);
  },
};

async function attachPixelFilter() {
  const box = document.querySelector("#pixelMode");
  if (!box) return;
  try {
    const mod = await import("./pixel-mode.js?v=c13");
    pixelFilter = mod.createPixelFilter(renderer);
    box.addEventListener("change", () => pixelFilter.setEnabled(box.checked));
  } catch (error) {
    console.warn("pixel filter skipped", error);
    document.querySelector("#pixelToggle")?.remove();
  }
}

async function boot() {
  catalog = await loadCatalog(new URL("./parts/manifest.json?v=c13", import.meta.url));
  recipe = morphRecipe(catalog);
  sizes = sizeLabels(catalog);
  bodyState = defaultState(catalog);
  zones = tapZones(catalog);
  await loadModel();
}

buildSideBars();
window.addEventListener("resize", resize);
resize();
attachPixelFilter();
boot().catch((error) => {
  console.error(error);
  statusEl.textContent = "не удалось загрузить модули станка";
});
tick();
