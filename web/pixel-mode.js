/**
 * Optional pixel look: 300px grid, nearest upscale.
 * No palette crush — that turned fair skin into dark blobs.
 *
 * Remove later: delete this file, #pixelToggle, and attachPixelFilter() in viewer.js.
 */
import * as THREE from "three";

const PIXEL_HEIGHT = 300;

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
  const material = new THREE.MeshBasicMaterial({ map: rt.texture, depthTest: false, depthWrite: false });
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
