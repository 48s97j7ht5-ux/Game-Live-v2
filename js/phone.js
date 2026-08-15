export const apps = [
  { id: "messages", name: "Сообщения", icon: "●", style: "messages" },
  { id: "contacts", name: "Контакты", icon: "♟", style: "contacts" },
  { id: "navigator", name: "Навигатор", icon: "⌖", style: "maps" },
  { id: "bank", name: "Банк", icon: "₽", style: "bank" },
  { id: "shops", name: "Магазины", icon: "▱", style: "shop" },
  { id: "social", name: "Соцсеть", icon: "◎", style: "social" },
  { id: "camera", name: "Камера", icon: "◉", style: "camera" },
  { id: "settings", name: "Настройки", icon: "⚙", style: "settings" },
];

export const dock = [
  { id: "phone", name: "Телефон", icon: "☎", style: "messages" },
  { id: "browser", name: "Браузер", icon: "◉", style: "maps" },
  { id: "music", name: "Музыка", icon: "♪", style: "social" },
  { id: "camera-dock", name: "Камера", icon: "◉", style: "camera" },
];

export function appMessage(app, location) {
  if (app.id === "navigator") {
    return `Навигатор: сейчас ${location.place.toLowerCase()}`;
  }
  if (app.id === "bank") {
    return "Банк: баланс пока только на главном экране";
  }
  return `${app.name} — приложение появится позже`;
}
