export const locations = {
  yard: {
    id: "yard",
    place: "ДВОР · ДОМ 17",
    title: "Твой новый дом",
    scene: "yard",
    text: "Ты стоишь во дворе старой пятиэтажки. Вещи уже занесены в квартиру. Дом живёт своей обычной утренней жизнью.",
    actions: [
      { id: "look", label: "Осмотреться", primary: true },
      { id: "enter", label: "Зайти в подъезд" },
    ],
  },
  entrance: {
    id: "entrance",
    place: "ПОДЪЕЗД · 1 ЭТАЖ",
    title: "Подъезд",
    scene: "stairwell",
    text: "Пахнет прохладным бетоном и утренним кофе из одной из квартир. Почтовые ящики ещё закрыты.",
    actions: [
      { id: "upstairs", label: "Подняться домой", primary: true },
      { id: "outside", label: "Выйти во двор" },
    ],
  },
  apartment: {
    id: "apartment",
    place: "КВАРТИРА · 17",
    title: "Квартира",
    scene: "indoor",
    text: "Коробки ещё стоят у стены. Из окна видно двор и соседний дом. Здесь тихо и немного пусто.",
    actions: [
      { id: "look-home", label: "Осмотреться", primary: true },
      { id: "leave", label: "Выйти в подъезд" },
    ],
  },
};

export function handleWorldAction(locationId, actionId) {
  if (locationId === "yard" && actionId === "look") {
    return {
      minutes: 1,
      energy: 1,
      text: "У подъезда пусто. В нескольких окнах горит свет, где-то наверху хлопнула дверь.",
    };
  }
  if (locationId === "yard" && actionId === "enter") {
    return { minutes: 2, energy: 1, locationId: "entrance", toast: "Локация изменена" };
  }
  if (locationId === "entrance" && actionId === "upstairs") {
    return { minutes: 3, energy: 2, locationId: "apartment", toast: "Ты дома" };
  }
  if (locationId === "entrance" && actionId === "outside") {
    return { minutes: 1, energy: 1, locationId: "yard" };
  }
  if (locationId === "apartment" && actionId === "look-home") {
    return {
      minutes: 2,
      energy: 1,
      text: "На кухне пустой чайник. В спальне ещё нет штор. С балкона слышно, как кто-то выходит из подъезда.",
    };
  }
  if (locationId === "apartment" && actionId === "leave") {
    return { minutes: 1, energy: 1, locationId: "entrance" };
  }
  return {};
}
