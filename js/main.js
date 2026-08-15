import { advance, formatMoney, formatTime, setLocation, setSpeed, spendEnergy, state, subscribe, weekdayName } from "./state.js";
import { handleWorldAction, locations } from "./world.js";
import { appMessage, apps, dock } from "./phone.js";
import { clothingLayers, meTabs } from "./character.js";

const toastEl = document.querySelector("#toast");
const sceneEl = document.querySelector("#scene");
const worldActionsEl = document.querySelector("#worldActions");
const clothingSlotsEl = document.querySelector("#clothingSlots");
const layerControlEl = document.querySelector("#layerControl");
const toggleSlotsEl = document.querySelector("#toggleSlots");
const meDetailEl = document.querySelector("#meDetail");
const statusRowEl = document.querySelector("#statusRow");

let timer = null;
let clothingLayerIndex = 3;
let clothingSlotsVisible = true;
let meTab = "overview";
let worldOverrideText = "";

function say(text) {
  toastEl.textContent = text;
  toastEl.classList.add("show");
  clearTimeout(say.t);
  say.t = setTimeout(() => toastEl.classList.remove("show"), 1400);
}

function currentLocation() {
  return locations[state.locationId];
}

function renderHud() {
  const time = formatTime();
  document.querySelector("#clock").textContent = time;
  document.querySelector("#phoneTime").textContent = time;
  document.querySelector("#phoneBigTime").textContent = time;
  document.querySelector("#weekday").textContent = weekdayName();
  document.querySelector("#dateLabel").textContent = state.dateLabel;
  document.querySelector("#money").textContent = formatMoney();
  document.querySelector("#weather").textContent = state.weather;
  document.querySelector("#phoneMeta").textContent = `${weekdayName()}, ${state.dateLabel} · +18°`;
}

function renderWorld() {
  const location = currentLocation();
  sceneEl.className = `scene ${location.scene}`;
  document.querySelector("#place").textContent = location.place;
  document.querySelector("#worldTitle").textContent = location.title;
  document.querySelector("#worldText").textContent = worldOverrideText || location.text;
  worldActionsEl.innerHTML = "";
  location.actions.forEach((action) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = action.label;
    if (action.primary) button.className = "primary";
    button.addEventListener("click", () => onWorldAction(action.id));
    worldActionsEl.appendChild(button);
  });
}

function onWorldAction(actionId) {
  const result = handleWorldAction(state.locationId, actionId);
  if (result.minutes) advance(result.minutes);
  if (result.energy) spendEnergy(result.energy);
  if (result.locationId) {
    worldOverrideText = "";
    setLocation(result.locationId);
  }
  if (result.text) {
    worldOverrideText = result.text;
    renderWorld();
  }
  if (result.toast) say(result.toast);
}

function renderPhone() {
  const grid = document.querySelector("#phoneApps");
  const dockEl = document.querySelector("#phoneDock");
  grid.innerHTML = "";
  dockEl.innerHTML = "";
  apps.forEach((app) => grid.appendChild(appButton(app, true)));
  dock.forEach((app) => dockEl.appendChild(appButton(app, false)));
}

function appButton(app, withLabel) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "ios-app";
  button.innerHTML = `<span class="appicon ${app.style}">${app.icon}</span>${withLabel ? `<small>${app.name}</small>` : ""}`;
  button.addEventListener("click", () => say(appMessage(app, currentLocation())));
  return button;
}

function renderStatus() {
  const chips = [
    [state.energy + "%", "энергия"],
    [state.hunger + "%", "сытость"],
    [state.hygiene, "гигиена"],
    [state.mood, "настроение"],
  ];
  statusRowEl.innerHTML = chips
    .map(([value, label]) => `<div class="status-chip"><b>${value}</b><span>${label}</span></div>`)
    .join("");
  document.querySelector("#condition").textContent = `● ${state.condition}`;
}

function applySlotVisibility() {
  clothingSlotsEl.classList.toggle("hidden-by-user", !clothingSlotsVisible);
  toggleSlotsEl.classList.toggle("active", clothingSlotsVisible);
  toggleSlotsEl.setAttribute("aria-pressed", String(clothingSlotsVisible));
  toggleSlotsEl.setAttribute("aria-label", clothingSlotsVisible ? "Скрыть ячейки" : "Показать ячейки");
  toggleSlotsEl.textContent = clothingSlotsVisible ? "◉" : "○";
}

function setClothingMode(enabled) {
  layerControlEl.classList.toggle("visible", enabled);
  clothingSlotsEl.classList.toggle("visible", enabled);
  if (enabled) renderLayer();
}

function renderLayer() {
  const layer = clothingLayers[clothingLayerIndex];
  clothingSlotsEl.innerHTML = "";
  layer.slots.forEach((slot) => {
    const button = document.createElement("button");
    const filled = Boolean(slot.name);
    button.type = "button";
    button.className = `clothing-slot ${filled ? "filled" : "empty"} anchor-${slot.anchor}`;
    button.innerHTML = filled
      ? `<span class="item-icon">${slot.icon}</span><span class="item-name">${slot.name}</span>`
      : `<span class="item-icon">＋</span><span class="item-name">Пусто</span>`;
    button.addEventListener("click", () => say(filled ? `${slot.name} · текущий предмет` : "Свободная ячейка"));
    clothingSlotsEl.appendChild(button);
  });
  applySlotVisibility();
}

function changeLayer(delta) {
  const next = Math.max(0, Math.min(clothingLayers.length - 1, clothingLayerIndex + delta));
  if (next === clothingLayerIndex) {
    say(delta > 0 ? "Это самый внешний слой" : "Это слой тела");
    return;
  }
  clothingLayerIndex = next;
  renderLayer();
  say(clothingLayers[clothingLayerIndex].name);
}

function setMeTab(tab) {
  meTab = tab;
  document.querySelectorAll("#meTabs button").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === tab);
  });
  meDetailEl.textContent = meTabs[tab];
  setClothingMode(tab === "clothes");
}

function bindUi() {
  document.querySelectorAll("#speedControl button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll("#speedControl button").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      setSpeed(Number(button.dataset.speed));
      runClock();
    });
  });

  document.querySelectorAll("#nav button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll("#nav button").forEach((item) => item.classList.remove("active"));
      document.querySelectorAll(".screen").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      document.querySelector("#" + button.dataset.screen).classList.add("active");
    });
  });

  document.querySelectorAll("#meTabs button").forEach((button) => {
    button.addEventListener("click", () => setMeTab(button.dataset.tab));
  });

  document.querySelector("#layerUp").addEventListener("click", (event) => {
    event.preventDefault();
    changeLayer(1);
  });
  document.querySelector("#layerDown").addEventListener("click", (event) => {
    event.preventDefault();
    changeLayer(-1);
  });
  toggleSlotsEl.addEventListener("click", (event) => {
    event.preventDefault();
    clothingSlotsVisible = !clothingSlotsVisible;
    applySlotVisibility();
    say(clothingSlotsVisible ? "Ячейки показаны" : "Ячейки скрыты");
  });
}

function runClock() {
  clearInterval(timer);
  if (!state.speed) return;
  timer = setInterval(() => advance(state.speed), 1500);
}

function render() {
  renderHud();
  renderWorld();
  renderStatus();
}

bindUi();
renderPhone();
renderLayer();
setMeTab("overview");
subscribe(render);
render();
runClock();
