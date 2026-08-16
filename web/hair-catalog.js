/**
 * Hair lists only. Official system wigs, community pack catalog, dye colors.
 * Wearing the wig is hair-wear.js. Buttons are three head parts, not this file.
 */
export const HAIR_CACHE = "c31";

export const OFFICIAL = [
  { id: "none", label: "нет" },
  { id: "short04", label: "ёжик" },
  { id: "short01", label: "стрижка" },
  { id: "short02", label: "короткая" },
  { id: "short03", label: "пикси" },
  { id: "bob01", label: "каре" },
  { id: "bob02", label: "ровное каре" },
  { id: "afro01", label: "афро" },
  { id: "ponytail01", label: "хвост" },
  { id: "braid01", label: "коса" },
  { id: "long01", label: "длинная" },
];

export const DEFAULT_OFFICIAL_STYLE = 5;

export const COLORS = {
  black: { hex: 0x1a1412, label: "чёрный" },
  chestnut: { hex: 0x3d2418, label: "каштан" },
  russet: { hex: 0x6b4a2b, label: "русый" },
  blond: { hex: 0xc4a066, label: "блонд" },
  ginger: { hex: 0xa85a28, label: "рыжий" },
  gray: { hex: 0x9a9590, label: "седой" },
};

export const COLOR_KEYS = Object.keys(COLORS);

export const SHELVES = [
  { id: "official", label: "официальная" },
  { id: "community", label: "общая" },
];

export async function loadCommunity() {
  const res = await fetch(new URL(`./parts/hair-community.json?v=${HAIR_CACHE}`, import.meta.url));
  if (!res.ok) return [];
  const data = await res.json();
  return (data.styles || [])
    .map((item) => (typeof item === "string" ? { id: item, label: item } : item))
    .filter((item) => item && item.id && item.label);
}
