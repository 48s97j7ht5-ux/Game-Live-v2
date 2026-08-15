/**
 * Optional pixel look: render the current view to a 300px-tall grid, then
 * nearest-neighbour upscale. Does not change morphs or zones.
 *
 * Remove later: delete this file, the #pixelMode label, and attachPixelFilter()
 * in viewer.js. The workbench still runs without it.
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
