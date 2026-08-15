/** Fair warm skin from the pixel-art character sheet. */

export const SCENE_BG = 0x1a1c22;
export const SKIN = {
  hi: 0xf8e6dc,
  light: 0xf0d4c4,
  mid: 0xe2bba8,
  shadow: 0xc49280,
  deep: 0x9a6a58,
  cavity: 0x6a463c,
};
export const LIGHT = {
  hemiSky: 0xfff8f2,
  hemiGround: 0x4a403c,
  key: 0xfff8f2,
  fill: 0xe8e4e0,
};
export const PIXEL_COLORS = [SCENE_BG, SKIN.deep, SKIN.shadow, SKIN.mid, SKIN.light, SKIN.hi];

export function hexRgb(hex) {
  return [(hex >> 16) & 255, (hex >> 8) & 255, hex & 255];
}
