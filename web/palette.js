/** Fair warm skin with punchy shadows, like the pixel-art courtyard/stairwell ramps. */

export const SCENE_BG = 0x1a1c22;
export const SKIN = {
  hi: 0xf8e6dc,
  light: 0xebcbb8,
  mid: 0xd4a894,
  shadow: 0x9a6a58,
  deep: 0x5c3a32,
  cavity: 0x2e1c18,
};
export const LIGHT = {
  hemiSky: 0xfff4ec,
  hemiGround: 0x2a221f,
  key: 0xfff6ee,
  fill: 0xb8b0aa,
};
export const PIXEL_COLORS = [SCENE_BG, SKIN.cavity, SKIN.deep, SKIN.shadow, SKIN.mid, SKIN.light, SKIN.hi];

export function hexRgb(hex) {
  return [(hex >> 16) & 255, (hex >> 8) & 255, hex & 255];
}
