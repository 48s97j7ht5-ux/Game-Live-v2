const WEEKDAYS = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"];

export const state = {
  minutes: 490,
  speed: 1,
  money: 24500,
  locationId: "yard",
  energy: 100,
  hunger: 76,
  hygiene: "Чисто",
  mood: "Спокойно",
  condition: "Нормально",
  weekdayIndex: 0,
  dateLabel: "1 сентября",
  weather: "☁ +18° · прохладно",
};

const listeners = new Set();

export function subscribe(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

export function notify() {
  for (const fn of listeners) fn(state);
}

export function formatTime(minutes = state.minutes) {
  const hours = Math.floor(minutes / 60) % 24;
  const mins = minutes % 60;
  return `${String(hours).padStart(2, "0")}:${String(mins).padStart(2, "0")}`;
}

export function formatMoney(value = state.money) {
  return `${value.toLocaleString("ru-RU")} ₽`;
}

export function weekdayName() {
  return WEEKDAYS[state.weekdayIndex];
}

export function advance(minutes) {
  const next = state.minutes + minutes;
  const days = Math.floor(next / 1440);
  state.minutes = ((next % 1440) + 1440) % 1440;
  if (days) state.weekdayIndex = (state.weekdayIndex + days) % 7;
  notify();
}

export function setSpeed(speed) {
  state.speed = speed;
  notify();
}

export function setLocation(locationId) {
  state.locationId = locationId;
  notify();
}

export function spendEnergy(amount) {
  state.energy = Math.max(0, state.energy - amount);
  notify();
}
