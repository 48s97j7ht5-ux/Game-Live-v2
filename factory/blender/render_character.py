"""Render a character in Blender (front 3/4, Cycles) for the pixel factory."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def argv_value(flag: str, default: str) -> str:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv):
            return argv[i + 1]
    return default


def clear_scene() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for light in list(bpy.data.lights):
        bpy.data.lights.remove(light)
    for cam in list(bpy.data.cameras):
        bpy.data.cameras.remove(cam)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)
    for img in list(bpy.data.images):
        bpy.data.images.remove(img)


def setup_world() -> None:
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 48
    scene.cycles.use_denoising = False
    scene.render.resolution_x = 500
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    world = bpy.data.worlds.new("studio")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.22, 0.23, 0.26, 1)
    bg.inputs["Strength"].default_value = 1.0

    sun = bpy.data.lights.new("key", "SUN")
    sun.energy = 3.2
    sun.angle = math.radians(12)
    sun_obj = bpy.data.objects.new("key", sun)
    sun_obj.rotation_euler = (math.radians(60), math.radians(-8), math.radians(155))
    scene.collection.objects.link(sun_obj)

    fill = bpy.data.lights.new("fill", "SUN")
    fill.energy = 0.9
    fill_obj = bpy.data.objects.new("fill", fill)
    fill_obj.rotation_euler = (math.radians(70), math.radians(20), math.radians(-40))
    scene.collection.objects.link(fill_obj)


def import_character(path: Path, yaw_degrees: float) -> None:
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    bpy.context.view_layer.update()
    imported = [obj for obj in bpy.context.scene.objects if obj not in before]
    skip = {"key", "fill", "cam"}
    anchor = bpy.data.objects.new("character_root", None)
    bpy.context.scene.collection.objects.link(anchor)
    for obj in imported:
        if obj.name in skip:
            continue
        if obj.parent is None:
            world = obj.matrix_world.copy()
            obj.parent = anchor
            obj.matrix_parent_inverse = anchor.matrix_world.inverted()
            obj.matrix_world = world
        if obj.type == "ARMATURE":
            obj.hide_render = True
    anchor.rotation_euler.z = math.radians(yaw_degrees)
    bpy.context.view_layer.update()


def scene_bounds() -> tuple[Vector, Vector]:
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mins = Vector((math.inf, math.inf, math.inf))
    maxs = Vector((-math.inf, -math.inf, -math.inf))
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.hide_render:
            continue
        evaluated = obj.evaluated_get(depsgraph)
        for corner in evaluated.bound_box:
            world = evaluated.matrix_world @ Vector(corner)
            mins.x, mins.y, mins.z = min(mins.x, world.x), min(mins.y, world.y), min(mins.z, world.z)
            maxs.x, maxs.y, maxs.z = max(maxs.x, world.x), max(maxs.y, world.y), max(maxs.z, world.z)
    return mins, maxs


def setup_camera() -> None:
    mins, maxs = scene_bounds()
    center = (mins + maxs) * 0.5
    size = maxs - mins
    scene = bpy.context.scene
    aspect = scene.render.resolution_x / scene.render.resolution_y
    padding = 1.12
    needed_height = size.z * padding
    needed_width = max(size.x, size.y) * 1.2 * padding
    ortho_scale = max(needed_height, needed_width / aspect)

    cam = bpy.data.cameras.new("cam")
    cam.type = "ORTHO"
    cam.ortho_scale = ortho_scale
    obj = bpy.data.objects.new("cam", cam)
    offset = Vector((0.35, 1.6, 0.08)).normalized() * max(3.0, size.length)
    obj.location = center + offset
    direction = center - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(obj)
    scene.camera = obj


def render_to(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main() -> None:
    out = Path(argv_value("--out", "factory/out/render.png")).resolve()
    model = Path(argv_value("--model", "factory/models/michelle.glb"))
    yaw = float(argv_value("--yaw", "0"))
    if not model.is_file():
        raise FileNotFoundError(f"character model missing: {model}")
    clear_scene()
    setup_world()
    import_character(model, yaw)
    setup_camera()
    render_to(out)
    print(f"wrote {out} from {model} yaw={yaw}")


if __name__ == "__main__":
    main()
