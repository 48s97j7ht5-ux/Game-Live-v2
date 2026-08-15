/** Colors from the pixel-art character render (fair warm skin, dark charcoal scene). */

export const SCENE_BG = 0x1a1c22;
export const SKIN = {
  hi: 0xf7e0d2,
  light: 0xe8c4b0,
  mid: 0xd2a48c,
  shadow: 0xb07c64,
  deep: 0x7a4e40,
  cavity: 0x4a3028,
};
export const LIGHT = {
  hemiSky: 0xfff4ec,
  hemiGround: 0x3a322e,
  key: 0xfff6ee,
  fill: 0xd4d8dc,
};
export const PIXEL_COLORS = [
  SCENE_BG,
  SKIN.cavity,
  SKIN.deep,
  SKIN.shadow,
  SKIN.mid,
  SKIN.light,
  SKIN.hi,
];

export function hexRgb(hex) {
  return [(hex >> 16) & 255, (hex >> 8) & 255, hex & 255];
}
