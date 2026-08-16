/**
 * Body poses: official MakeHuman arms/legs targets (factory/pack_poses.py).
 */

export function createPoseStudio({ applyBody, morphBoundRef, poseBoundRef, bodyStateRef, recipeRef, refit }) {
  const state = { index: 0 };
  let poses = [{ id: "rest", label: "стоя", key: null }];
  let loaded = null;

  async function load(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error("нет поз");
    loaded = await response.json();
    poses = loaded.poses || poses;
    state.index = 0;
    return loaded;
  }

  function setCatalog(list) {
    if (list?.length) poses = list;
    state.index = 0;
  }

  function current() {
    return poses[state.index] || poses[0];
  }

  function apply() {
    const morphBound = morphBoundRef();
    const poseBound = poseBoundRef();
    const bodyState = bodyStateRef();
    const recipe = recipeRef();
    const key = current()?.key || null;
    applyBody(morphBound, bodyState, recipe, poseBound, key, null);
    refit();
  }

  function cycle(delta) {
    if (poses.length < 2) return;
    state.index = (state.index + delta + poses.length) % poses.length;
    apply();
  }

  function statusLine() {
    const pose = current();
    return pose ? `поза · ${pose.label}` : "";
  }

  const row = {
    id: "pose",
    label: "поза",
    kind: "choice",
    hint: () => current()?.label || "",
    onStep: cycle,
    atMin: () => state.index === 0,
    atMax: () => state.index >= poses.length - 1,
  };

  function floorsFor(id) {
    return id === "pose" ? [row] : [];
  }

  function reset() {
    state.index = 0;
  }

  return { load, setCatalog, apply, cycle, statusLine, floorsFor, reset, current, state, get poses() {
    return poses;
  } };
}
