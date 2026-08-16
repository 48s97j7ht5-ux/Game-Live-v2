/**
 * Official MakeHuman hm08 skeleton: default.mhskel + default_weights.mhw.
 * Poses from body-poseunits.json (bone quaternions + mirror), not vertex hacks.
 */

import * as THREE from "three";

const BODY_VERTS = 13380;
const SKIP_POSE_KEYS = new Set(["name", "copyright", "license", "version"]);

function key3(x, y, z) {
  return `${x.toFixed(4)},${y.toFixed(4)},${z.toFixed(4)}`;
}

function mirrorBoneName(name) {
  if (name.endsWith(".L")) return `${name.slice(0, -2)}.R`;
  if (name.endsWith(".R")) return `${name.slice(0, -2)}.L`;
  return null;
}

function mirrorQuat(q) {
  return new THREE.Quaternion(-q.x, q.y, -q.z, q.w);
}

function matsFromFlat(flat) {
  const out = [];
  for (let i = 0; i < flat.length; i += 16) {
    const m = new THREE.Matrix4();
    m.fromArray(flat, i);
    out.push(m);
  }
  return out;
}

function buildBoneHierarchy(packed) {
  const { bones: names, parents } = packed;
  const threeBones = names.map((name) => {
    const bone = new THREE.Bone();
    bone.name = name;
    return bone;
  });
  const roots = [];
  for (let i = 0; i < names.length; i += 1) {
    const parent = parents[i];
    if (parent >= 0) threeBones[parent].add(threeBones[i]);
    else roots.push(threeBones[i]);
  }
  const invBind = matsFromFlat(packed.inverseBindMatrices);
  const globalRest = invBind.map((ibm) => ibm.clone().invert());
  for (let i = 0; i < names.length; i += 1) {
    const g = globalRest[i];
    if (parents[i] >= 0) {
      const local = new THREE.Matrix4().copy(globalRest[parents[i]]).invert().multiply(g);
      threeBones[i].matrix.copy(local);
    } else {
      threeBones[i].matrix.copy(g);
    }
    threeBones[i].matrix.decompose(threeBones[i].position, threeBones[i].quaternion, threeBones[i].scale);
    threeBones[i].updateMatrixWorld(true);
  }
  const skeleton = new THREE.Skeleton(threeBones);
  skeleton.boneInverses = invBind;
  return { skeleton, roots, threeBones, restLocalQuat: threeBones.map((b) => b.quaternion.clone()) };
}

function attachSkinAttributes(bodyMesh, packed, restHuman) {
  const globalByPos = new Map();
  for (let g = 0; g < Math.min(BODY_VERTS, restHuman.length); g += 1) {
    const p = restHuman[g];
    globalByPos.set(key3(p.x, p.y, p.z), g);
  }
  const pos = bodyMesh.geometry.getAttribute("position");
  const count = pos.count;
  const skinIndex = new Uint16Array(count * 4);
  const skinWeight = new Float32Array(count * 4);
  const srcIndex = packed.skinIndex;
  const srcWeight = packed.skinWeight;
  for (let i = 0; i < count; i += 1) {
    const o = i * 3;
    const g = globalByPos.get(key3(pos.array[o], pos.array[o + 1], pos.array[o + 2]));
    const d = i * 4;
    if (g === undefined) {
      skinIndex[d] = 0;
      skinWeight[d] = 1;
      continue;
    }
    const s = g * 4;
    for (let k = 0; k < 4; k += 1) {
      skinIndex[d + k] = srcIndex[s + k];
      skinWeight[d + k] = srcWeight[s + k];
    }
  }
  bodyMesh.geometry.setAttribute("skinIndex", new THREE.BufferAttribute(skinIndex, 4));
  bodyMesh.geometry.setAttribute("skinWeight", new THREE.BufferAttribute(skinWeight, 4));
}

export async function loadBodyRig(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`skeleton ${response.status}`);
  return response.json();
}

export async function loadPoseUnits(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`poseunits ${response.status}`);
  return response.json();
}

/** Replace hm08 body Mesh with SkinnedMesh bound to official MH skeleton. */
export function bindBodyRig({ bodyMesh, parent, packed, restHuman, material }) {
  if (!bodyMesh?.geometry || !bodyMesh.parent) return null;
  attachSkinAttributes(bodyMesh, packed, restHuman);
  const { skeleton, roots, threeBones, restLocalQuat } = buildBoneHierarchy(packed);
  const skinned = new THREE.SkinnedMesh(bodyMesh.geometry, material);
  skinned.name = bodyMesh.name;
  const root = new THREE.Group();
  root.name = "body-rig";
  for (const r of roots) root.add(r);
  parent.add(root);
  parent.add(skinned);
  parent.remove(bodyMesh);
  skinned.bind(skeleton);
  skinned.frustumCulled = false;
  if (material) material.skinning = true;
  return {
    skinnedMesh: skinned,
    skeleton,
    bones: threeBones,
    restLocalQuat,
    boneByName: new Map(threeBones.map((b) => [b.name, b])),
    dispose() {
      parent.remove(root);
      parent.remove(skinned);
    },
  };
}

export function createPoseDriver({ rig, poseUnits, recipes }) {
  const unitPoses = poseUnits?.poses || {};

  function resetBones() {
    rig.bones.forEach((bone, i) => {
      bone.quaternion.copy(rig.restLocalQuat[i]);
      bone.updateMatrix();
    });
    rig.skeleton.pose();
    rig.skeleton.update();
  }

  function applyUnit(unitName, strength, mirror) {
    const frame = unitPoses[unitName];
    if (!frame) return;
    for (const [boneName, quatArr] of Object.entries(frame)) {
      if (SKIP_POSE_KEYS.has(boneName) || !Array.isArray(quatArr) || quatArr.length < 4) continue;
      const bone = rig.boneByName.get(boneName);
      if (!bone) continue;
      const q = new THREE.Quaternion(quatArr[1], quatArr[2], quatArr[3], quatArr[0]);
      if (strength !== 1) q.slerp(new THREE.Quaternion(), 1 - strength);
      bone.quaternion.multiply(q);
      if (mirror) {
        const otherName = mirrorBoneName(boneName);
        const other = otherName ? rig.boneByName.get(otherName) : null;
        if (other) other.quaternion.multiply(mirrorQuat(q));
      }
    }
  }

  function applyRecipe(key) {
    resetBones();
    if (!key || !recipes?.[key]) {
      rig.skeleton.update();
      return;
    }
    const recipe = recipes[key];
    const strength = recipe.strength ?? 1;
    if (recipe.units) {
      for (const unit of recipe.units) applyUnit(unit, strength, recipe.mirror);
    }
    if (recipe.units_left) {
      for (const unit of recipe.units_left) applyUnit(unit, strength, false);
    }
    if (recipe.units_right) {
      for (const unit of recipe.units_right) {
        const mirrored = unit.replace("Left", "Right");
        if (unitPoses[mirrored]) applyUnit(mirrored, strength, false);
        else applyUnit(unit, strength, true);
      }
    }
    rig.skeleton.update();
  }

  return { applyRecipe, resetBones };
}
