export const clothingLayers = [
  {
    name: "Тело · слой 0",
    slots: [
      { anchor: "chest-left" },
      { anchor: "waist-left" },
      { anchor: "thigh-right" },
      { anchor: "foot-right" },
    ],
  },
  {
    name: "Нижнее бельё · слой 10",
    slots: [
      { anchor: "chest-left", icon: "◒", name: "Бельё" },
      { anchor: "waist-left", icon: "▱", name: "Трусы" },
      { anchor: "chest-right" },
      { anchor: "waist-right" },
    ],
  },
  {
    name: "Чулочно-носочный · слой 20",
    slots: [
      { anchor: "thigh-left", icon: "▥", name: "Колготки" },
      { anchor: "calf-left", icon: "▥", name: "Носки" },
      { anchor: "thigh-right" },
      { anchor: "calf-right" },
    ],
  },
  {
    name: "Основная одежда · слой 40",
    slots: [
      { anchor: "chest-left", icon: "T", name: "Футболка" },
      { anchor: "waist-left", icon: "Ⅱ", name: "Джинсы" },
      { anchor: "chest-right" },
      { anchor: "waist-right" },
    ],
  },
  {
    name: "Дополнительный · слой 50",
    slots: [
      { anchor: "chest-left", icon: "⌑", name: "Худи" },
      { anchor: "chest-right" },
      { anchor: "waist-left" },
      { anchor: "waist-right" },
    ],
  },
  {
    name: "Верхняя одежда · слой 60",
    slots: [
      { anchor: "chest-left", icon: "▤", name: "Куртка" },
      { anchor: "chest-right" },
      { anchor: "waist-left" },
      { anchor: "waist-right" },
    ],
  },
  {
    name: "Аксессуары · слой 70",
    slots: [
      { anchor: "head-left", icon: "○", name: "Очки" },
      { anchor: "head-right" },
      { anchor: "chest-left", icon: "○", name: "Цепочка" },
      { anchor: "waist-right", icon: "○", name: "Часы" },
    ],
  },
];

export const meTabs = {
  overview: "Сейчас на персонаже повседневный комплект. Здесь будет краткое состояние внешности и заметные эффекты.",
  clothes: "Гардероб показывает надетые предметы по слоям. Ячейки располагаются прямо над соответствующими зонами тела.",
  body: "Здесь будут параметры тела и физиологические состояния, которые персонаж способен оценить сам.",
};
