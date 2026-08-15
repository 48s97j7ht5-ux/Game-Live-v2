/**
 * Optional pixel look: 300px grid + snap to the character-render palette.
 * Morphs and zones stay untouched.
 *
 * Remove later: delete this file, #pixelToggle, and attachPixelFilter() in viewer.js.
 */
import * as THREE from "three";
import { PIXEL_COLORS } from "./palette.js?v=c7";

const PIXEL_HEIGHT = 300;

function paletteVectors() {
  return PIXEL_COLORS.map((hex) => new THREE.Color(hex));
}

export function createPixelFilter(renderer) {
  const rt = new THREE.WebGLRenderTarget(1, 1, {
    minFilter: THREE.NearestFilter,
    magFilter: THREE.NearestFilter,
    generateMipmaps: false,
    depthBuffer: true,
  });
  rt.texture.colorSpace = renderer.outputColorSpace;

  const blitScene = new THREE.Scene();
  const blitCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const pal = paletteVectors();
  const material = new THREE.ShaderMaterial({
    uniforms: {
      tDiffuse: { value: rt.texture },
      pal: { value: pal },
    },
    vertexShader: `
      varying vec2 vUv;
      void main() {
        vUv = uv;
        gl_Position = vec4(position.xy, 0.0, 1.0);
      }
    `,
    fragmentShader: `
      uniform sampler2D tDiffuse;
      uniform vec3 pal[${pal.length}];
      varying vec2 vUv;
      void main() {
        vec3 c = texture2D(tDiffuse, vUv).rgb;
        float best = 1.0e9;
        vec3 picked = pal[0];
        for (int i = 0; i < ${pal.length}; i++) {
          vec3 d = c - pal[i];
          float dist = dot(d, d);
          if (dist < best) {
            best = dist;
            picked = pal[i];
          }
        }
        gl_FragColor = vec4(picked, 1.0);
      }
    `,
    depthTest: false,
    depthWrite: false,
  });
  blitScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), material));

  let enabled = false;

  return {
    setEnabled(on) {
      enabled = Boolean(on);
    },
    render(mainScene, camera) {
      if (!enabled) {
        renderer.setRenderTarget(null);
        renderer.render(mainScene, camera);
        return;
      }
      const canvas = renderer.domElement;
      const height = PIXEL_HEIGHT;
      const width = Math.max(1, Math.round((height * canvas.clientWidth) / Math.max(canvas.clientHeight, 1)));
      if (rt.width !== width || rt.height !== height) rt.setSize(width, height);
      renderer.setRenderTarget(rt);
      renderer.render(mainScene, camera);
      renderer.setRenderTarget(null);
      renderer.render(blitScene, blitCamera);
    },
  };
}
