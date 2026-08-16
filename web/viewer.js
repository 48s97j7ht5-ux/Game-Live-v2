import * as THREE from "three";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";
import { applyBody, bindMorph, loadTargets } from "./chest-morph.js?v=c44";
import { createHairStudio, parseObjVerts } from "./hair.js?v=c44";
import { createEyes } from "./eye-wear.js?v=c44";
import { createMakeupStudio } from "./makeup.js?v=c44";
import { createPoseStudio } from "./pose.js?v=c44";
import {
  bodyModel,
  bodyPart,
  bodyParts,
  defaultState,
  loadCatalog,
  morphRecipe,
  overlays,
  sizeLabels,
  tapZones,
} from "./registry.js?v=c44";

const AXIS_STEPS = 7;
// Tap skull: body → hair → face. Tap not-skull: one step back. Face crop is for makeup later.
const FOCUS = {
  body: { yFrac: 0.5, span: 1 },
  head: { yFrac: 0.8, span: 0.46 },
  face: { yFrac: 0.9, span: 0.16 },
};
const HEAD_Y_FRAC = 0.84;
const POSE_PART_ID = "pose";

const sideLeft = document.querySelector("#sideLeft");
const sideRight = document.querySelector("#sideRight");
const canvas = document.querySelector("#view");
const statusEl = document.querySelector("#status");
const stage = document.querySelector(".stage");
const poseBar = document.querySelector("#poseBar");
const poseLabel = document.querySelector("#poseLabel");
const poseLeftBtn = document.querySelector("#poseLeft");
const poseRightBtn = document.querySelector("#poseRight");
const floorButtons = [];

let catalog = { manifest: { hints: {} }, parts: [] };
let recipe = { axes: [] };
let sizes = ["A", "B", "C", "D", "E"];
let bodyState = {};
let zones = [];
let editZone = null;
let lastFloor = "";
let currentBody = "clay";
let currentVariant = "";
let bodyLoad = 0;
let focusMode = "body";
const hairStudio = createHairStudio({ THREE });
const eyes = createEyes({ THREE });
const makeupStudio = createMakeupStudio({ THREE });
let poseBound = null;
const poseStudio = createPoseStudio({
  applyBody,
  morphBoundRef: () => morphBound,
  poseBoundRef: () => poseBound,
  bodyStateRef: () => bodyState,
  recipeRef: () => recipe,
  refit: () => {
    hairStudio.refit();
    eyes.refit();
  },
});

function zoneById(id) {
  return zones.find((zone) => zone.id === id);
}

// Body: tap one zone, one arrow row. Head/face are zoomed crops, so their rows stay on screen together.
const HAIR_HEAD_IDS = ["hair-color", "hair-style", "hair-shelf"];
const MAKEUP_FACE_IDS = ["makeup-lips", "makeup-cheeks"];

function isHairZone(id) {
  return typeof id === "string" && id.startsWith("hair-");
}

function isMakeupZone(id) {
  return typeof id === "string" && id.startsWith("makeup-");
}

function applyShape() {
  const key = poseStudio.current()?.key || null;
  applyBody(morphBound, bodyState, recipe, poseBound, key);
  hairStudio.refit();
  eyes.refit();
}

function currentFloors() {
  if (focusMode === "head") {
    return HAIR_HEAD_IDS.flatMap((id) => hairStudio.floorsFor(id));
  }
  if (focusMode === "face") {
    return MAKEUP_FACE_IDS.flatMap((id) => makeupStudio.floorsFor(id));
  }
  if (focusMode === "body" && editZone) {
    return zoneById(editZone)?.floors || [];
  }
  return [];
}

function syncPoseBar() {
  const onBody = focusMode === "body";
  if (poseBar) poseBar.hidden = !onBody;
  if (!onBody) return;
  const pose = poseStudio.current();
  if (poseLabel) poseLabel.textContent = pose ? `поза · ${pose.label}` : "поза";
  const count = poseStudio.poses?.length || 1;
  const index = poseStudio.state.index;
  if (poseLeftBtn) poseLeftBtn.disabled = index <= 0;
  if (poseRightBtn) poseRightBtn.disabled = index >= count - 1;
}

function stepPose(delta) {
  poseStudio.cycle(delta);
  syncPoseBar();
  statusEl.textContent = idleStatus();
}

function openHairStudio() {
  const first = HAIR_HEAD_IDS.find((id) => zoneById(id));
  if (first) setEditZone(first);
}

function openMakeupStudio() {
  const first = MAKEUP_FACE_IDS.find((id) => zoneById(id));
  if (first) setEditZone(first);
}

function floorValue(floor) {
  if (typeof floor.hint === "function") return floor.hint();
  if (floor.kind === "size") return `${sizes[bodyState.sizeIndex] || ""}`;
  return `${bodyState[floor.id] + 1}/${AXIS_STEPS}`;
}

function idleStatus() {
  if (focusMode === "face") return makeupStudio.statusLine();
  if (focusMode === "head") return hairStudio.statusLine();
  if (focusMode === "body" && !editZone) return poseStudio.statusLine();
  if (!editZone) {
    const hints = catalog.manifest.hints || {};
    return hints[currentView()] || hints.default || "";
  }
  const floor = currentFloors().find((item) => item.id === lastFloor) || currentFloors()[0];
  const zone = zoneById(editZone);
  if (!zone || !floor) return "";
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
  if (typeof floor.onStep === "function") {
    floor.onStep(delta);
    statusEl.textContent = idleStatus();
    updateFloorDisabled();
    syncPoseBar();
    return;
  }
  if (floor.kind === "size") {
    bodyState.sizeIndex = Math.max(0, Math.min(sizes.length - 1, bodyState.sizeIndex + delta));
  } else {
    const now = Number.isFinite(bodyState[floor.id]) ? bodyState[floor.id] : 3;
    bodyState[floor.id] = Math.max(0, Math.min(AXIS_STEPS - 1, now + delta));
  }
  statusEl.textContent = idleStatus();
  updateFloorDisabled();
  applyShape();
}

function updateFloorDisabled() {
  for (const item of floorButtons) {
    if (item.floor.kind === "size") {
      item.left.disabled = bodyState.sizeIndex === 0;
      item.right.disabled = bodyState.sizeIndex === sizes.length - 1;
    } else if (typeof item.floor.atMin === "function") {
      item.left.disabled = item.floor.atMin();
      item.right.disabled = item.floor.atMax();
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
  const height = Math.max(canvas.clientHeight, 1);
  const count = floorButtons.length;
  if (!count) return;
  if (focusMode === "head" || focusMode === "face") {
    const buttonSize = Math.min(44, Math.max(32, height / (count + 2)));
    for (let i = 0; i < count; i += 1) {
      const y = ((i + 1) / (count + 1)) * height;
      const item = floorButtons[i];
      item.left.style.top = `${y}px`;
      item.right.style.top = `${y}px`;
      item.left.style.height = `${buttonSize}px`;
      item.right.style.height = `${buttonSize}px`;
      item.left.style.transform = "translateY(-50%)";
      item.right.style.transform = "translateY(-50%)";
    }
    return;
  }
  if (!editZone) return;
  const zone = zoneById(editZone);
  if (!zone || zone.yFrac == null) return;
  const gap = 3;
  const buttonSize = Math.min(40, Math.max(30, (height - 16 - gap * (count - 1)) / count));
  const stack = count * buttonSize + (count - 1) * gap;
  const zoneY = worldToCanvasY(bodyHeight * zone.yFrac);
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

function hitDummy(clientX, clientY) {
  if (!dummy) return null;
  const rect = canvas.getBoundingClientRect();
  pointerNdc.set(
    ((clientX - rect.left) / rect.width) * 2 - 1,
    -((clientY - rect.top) / rect.height) * 2 + 1,
  );
  raycaster.setFromCamera(pointerNdc, camera);
  for (const hit of raycaster.intersectObject(dummy, true)) {
    if (hit.object.visible) return hit;
  }
  return null;
}

function isHeadHit(hit) {
  const name = partName(hit.object);
  if (name === "hair" || name === "hair-scalp" || name === "eyes") return true;
  return hit.point.y >= bodyHeight * HEAD_Y_FRAC;
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
const raycaster = new THREE.Raycaster();
const pointerNdc = new THREE.Vector2();

scene.add(new THREE.HemisphereLight(0xffffff, 0x334455, 1.1));
const key = new THREE.DirectionalLight(0xffffff, 1.4);
key.position.set(-1.2, 2.2, 1.8);
scene.add(key);
const fill = new THREE.DirectionalLight(0x99aacc, 0.45);
fill.position.set(1.4, 0.6, 0.8);
scene.add(fill);

const SKIN_HEX = 0xffd7b8;
const clayMatcap = makeClayMatcap();
const skin = new THREE.MeshMatcapMaterial({
  color: SKIN_HEX,
  matcap: clayMatcap,
});
let dummy = null;
let bodyMesh = null;
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
    child.visible = name === "body" || name.startsWith("body") || name === "hair" || name === "hair-scalp" || name === "eyes";
  });
}

function applyScale() {
  const width = Math.max(canvas.clientWidth, 1);
  const height = Math.max(canvas.clientHeight, 1);
  const span = FOCUS[focusMode]?.span ?? 1;
  const worldH = bodyHeight * span * (height / targetPx);
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
  const y = bodyHeight * (FOCUS[focusMode]?.yFrac ?? 0.5);
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

function setFocus(mode) {
  focusMode = mode in FOCUS ? mode : "body";
  const strayZone =
    (focusMode !== "head" && isHairZone(editZone)) || (focusMode !== "face" && isMakeupZone(editZone));
  if (strayZone) {
    editZone = null;
    lastFloor = "";
    clearSideBars();
    sideLeft.classList.remove("open");
    sideRight.classList.remove("open");
  }
  zones = tapZones(catalog, currentBody, focusMode);
  applyScale();
  placeCamera();
  if (focusMode === "head") openHairStudio();
  else if (focusMode === "face") openMakeupStudio();
  syncPoseBar();
  if (dummy && focusMode === "body" && !editZone) statusEl.textContent = idleStatus();
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
  for (const part of overlays(catalog, currentBody)) {
    try {
      const group = await loader.loadAsync(`${part.model}?v=${catalog.manifest.cache}`);
      group.name = part.id;
      parent.add(group);
    } catch (error) {
      console.warn("overlay skip", part.id, error);
    }
  }
}

function disposeDummy() {
  hairStudio.dispose();
  eyes.dispose();
  makeupStudio.dispose();
  bodyMesh = null;
  if (!dummy) return;
  scene.remove(dummy);
  dummy.traverse((child) => {
    if (child.geometry) child.geometry.dispose();
  });
  dummy = null;
  morphBound = null;
  poseBound = null;
}

function syncBodyUi() {
  document.querySelectorAll("#bodies button").forEach((button) => {
    button.classList.toggle("active", button.dataset.body === currentBody);
  });
  const body = bodyPart(catalog, currentBody);
  const variants = body?.variants || [];
  const row = document.querySelector("#variants");
  if (!row) return;
  row.innerHTML = "";
  row.hidden = variants.length === 0;
  for (const variant of variants) {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.variant = variant.id;
    button.textContent = variant.label;
    button.classList.toggle("active", variant.id === currentVariant || (!currentVariant && variant.model === body.model));
    button.addEventListener("click", () => switchBody(currentBody, variant.id));
    row.appendChild(button);
  }
}

async function switchBody(bodyId, variantId) {
  const body = bodyPart(catalog, bodyId);
  if (!body) return;
  const token = (bodyLoad += 1);
  currentBody = body.id;
  const variants = body.variants || [];
  currentVariant = variantId || variants[0]?.id || "";
  recipe = morphRecipe(catalog, currentBody);
  sizes = sizeLabels(catalog, currentBody);
  bodyState = defaultState(catalog, currentBody);
  zones = tapZones(catalog, currentBody, focusMode);
  setEditZone(null);
  syncBodyUi();
  statusEl.textContent = "гружу тело…";
  const loader = new OBJLoader();
  const model = bodyModel(body, currentVariant);
  const group = await loader.loadAsync(`${model}?v=${catalog.manifest.cache}`);
  if (token !== bodyLoad) {
    group.traverse((child) => {
      if (child.geometry) child.geometry.dispose();
    });
    return;
  }
  group.traverse((child) => {
    if (!child.isMesh) return;
    child.material = skin;
    child.geometry.computeVertexNormals();
  });
  hideHelpers(group);
  disposeDummy();
  dummy = group;
  bodyMesh = null;
  dummy.traverse((child) => {
    if (!bodyMesh && child.isMesh && partName(child) === "body") bodyMesh = child;
  });
  scene.add(dummy);
  frameObject(dummy);
  statusEl.textContent = idleStatus();
  syncPoseBar();
  await loadOverlays(dummy);
  const morphFile = body.morphs || (currentBody === "clay" ? catalog.manifest.morphs : "");
  if (!morphFile) return;
  try {
    const morphUrl = new URL(`${morphFile}?v=${catalog.manifest.cache}`, import.meta.url);
    const packed = await loadTargets(morphUrl);
    morphBound = bindMorph(dummy, packed);
    try {
      const poseUrl = new URL(`./data/body-poses.json?v=${catalog.manifest.cache}`, import.meta.url);
      const posePacked = await loadTargets(poseUrl);
      poseStudio.setCatalog(posePacked.poses);
      poseBound = bindMorph(dummy, posePacked);
      poseStudio.reset();
    } catch (poseError) {
      console.warn("poses skip", poseError);
      poseBound = null;
      poseStudio.reset();
    }
    applyShape();
    const restHuman = parseObjVerts(await (await fetch(`${model}?v=${catalog.manifest.cache}`)).text());
    hairStudio.bind({
      dummy,
      restHuman,
      packed,
      recipe,
      bodyState,
      setStatus: (text) => {
        statusEl.textContent = text;
      },
      requestRedraw: () => {
        if (dummy) statusEl.textContent = idleStatus();
      },
    });
    eyes.bind({ dummy, restHuman, packed, recipe, bodyState, cache: catalog.manifest.cache });
    await hairStudio.loadExtra();
    await hairStudio.apply();
    try {
      await eyes.wear();
    } catch (eyeError) {
      console.warn("eyes skip", eyeError);
    }
    await makeupStudio.bind({
      bodyMesh,
      material: skin,
      restHuman,
      cache: catalog.manifest.cache,
      requestRedraw: () => {
        if (dummy) statusEl.textContent = idleStatus();
      },
    });
    if (focusMode === "head") openHairStudio();
    else if (focusMode === "face") openMakeupStudio();
    syncPoseBar();
  } catch (error) {
    console.error(error);
    statusEl.textContent = "тело есть, правки формы не загрузились";
    syncPoseBar();
  }
}

function buildBodySwitcher() {
  const row = document.querySelector("#bodies");
  if (!row) return;
  row.innerHTML = "";
  const parts = bodyParts(catalog);
  row.hidden = parts.length < 2;
  if (parts.length < 2) return;
  for (const part of parts) {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.body = part.id;
    button.textContent = part.label;
    button.addEventListener("click", () => switchBody(part.id));
    row.appendChild(button);
  }
  syncBodyUi();
}

document.querySelector("#turnLeft").addEventListener("click", (event) => {
  event.stopPropagation();
  stepTurn(1);
});
document.querySelector("#turnRight").addEventListener("click", (event) => {
  event.stopPropagation();
  stepTurn(-1);
});
poseLeftBtn?.addEventListener("click", (event) => {
  event.stopPropagation();
  stepPose(-1);
});
poseRightBtn?.addEventListener("click", (event) => {
  event.stopPropagation();
  stepPose(1);
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
  if (focusMode === "face") {
    setFocus("head");
    return;
  }
  if (focusMode === "head") {
    const hit = hitDummy(event.clientX, event.clientY);
    if (hit && isHeadHit(hit)) {
      setFocus("face");
      return;
    }
    setFocus("body");
    return;
  }
  const hit = hitDummy(event.clientX, event.clientY);
  if (hit && isHeadHit(hit)) {
    setFocus("head");
    return;
  }
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
    const mod = await import("./pixel-mode.js?v=c44");
    pixelFilter = mod.createPixelFilter(renderer);
    box.addEventListener("change", () => pixelFilter.setEnabled(box.checked));
  } catch (error) {
    console.warn("pixel filter skipped", error);
    document.querySelector("#pixelToggle")?.remove();
  }
}

async function boot() {
  catalog = await loadCatalog(new URL("./parts/manifest.json?v=c44", import.meta.url));
  currentBody = catalog.manifest.defaultBody || bodyParts(catalog)[0]?.id || "clay";
  buildBodySwitcher();
  await switchBody(currentBody);
  syncPoseBar();
}

window.addEventListener("resize", resize);
resize();
attachPixelFilter();
boot().catch((error) => {
  console.error(error);
  statusEl.textContent = "не удалось загрузить модули станка";
});
tick();
