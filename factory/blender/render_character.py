"""Render a procedural mannequin in Blender (Cycles Toon, 3/4 camera)."""

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


def toon_material(name: str, color: tuple[float, float, float], size: float = 0.35) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    toon = nodes.new("ShaderNodeBsdfToon")
    toon.component = "DIFFUSE"
    toon.inputs["Color"].default_value = (*color, 1.0)
    toon.inputs["Size"].default_value = size
    toon.inputs["Smooth"].default_value = 0.08
    links.new(toon.outputs["BSDF"], output.inputs["Surface"])
    return mat


def cylinder(name: str, radius: float, depth: float, location: Vector, material: bpy.types.Material, rotation=(0.0, 0.0, 0.0)) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius,
        depth=depth,
        location=location,
        rotation=rotation,
        vertices=24,
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj


def sphere(name: str, radius: float, location: Vector, material: bpy.types.Material, scale=None) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location, segments=24, ring_count=16)
    obj = bpy.context.active_object
    obj.name = name
    if scale:
        obj.scale = scale
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj


def build_mannequin() -> None:
    skin = toon_material("skin", (0.72, 0.55, 0.47), size=0.42)
    hair = toon_material("hair", (0.04, 0.04, 0.05), size=0.5)
    shirt = toon_material("shirt", (0.07, 0.07, 0.08), size=0.38)
    pants = toon_material("pants", (0.09, 0.09, 0.11), size=0.38)
    boots = toon_material("boots", (0.03, 0.03, 0.03), size=0.45)

    sphere("head", 0.11, Vector((0, 0.02, 1.52)), skin, scale=(0.95, 0.95, 1.12))
    sphere("hair", 0.125, Vector((0, -0.08, 1.58)), hair, scale=(1.08, 0.9, 1.0))
    sphere("eye_l", 0.024, Vector((-0.04, 0.11, 1.545)), toon_material("eye", (0.05, 0.05, 0.05), size=0.55))
    sphere("eye_r", 0.024, Vector((0.04, 0.11, 1.545)), toon_material("eye", (0.05, 0.05, 0.05), size=0.55))
    cylinder("neck", 0.04, 0.08, Vector((0, 0, 1.38)), skin)
    cylinder("torso", 0.13, 0.38, Vector((0, 0, 1.14)), shirt)
    cylinder("hips", 0.12, 0.14, Vector((0, 0, 0.90)), pants)
    cylinder("leg_l", 0.055, 0.42, Vector((-0.07, 0, 0.62)), pants)
    cylinder("leg_r", 0.055, 0.42, Vector((0.07, 0, 0.62)), pants)
    cylinder("boot_l", 0.06, 0.16, Vector((-0.07, 0.02, 0.34)), boots)
    cylinder("boot_r", 0.06, 0.16, Vector((0.07, 0.02, 0.34)), boots)
    cylinder("arm_l", 0.04, 0.36, Vector((-0.20, 0, 1.12)), skin, rotation=(0, math.radians(12), 0))
    cylinder("arm_r", 0.04, 0.36, Vector((0.20, 0, 1.12)), skin, rotation=(0, math.radians(-12), 0))
    sphere("hand_l", 0.045, Vector((-0.27, 0, 0.92)), skin)
    sphere("hand_r", 0.045, Vector((0.27, 0, 0.92)), skin)


def setup_world() -> None:
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 24
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
    sun.energy = 4.5
    sun.angle = math.radians(8)
    sun_obj = bpy.data.objects.new("key", sun)
    sun_obj.rotation_euler = (math.radians(55), math.radians(-10), math.radians(135))
    scene.collection.objects.link(sun_obj)

    fill = bpy.data.lights.new("fill", "SUN")
    fill.energy = 0.8
    fill_obj = bpy.data.objects.new("fill", fill)
    fill_obj.rotation_euler = (math.radians(70), math.radians(-20), math.radians(-50))
    scene.collection.objects.link(fill_obj)


def scene_bounds() -> tuple[Vector, Vector]:
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mins = Vector((math.inf, math.inf, math.inf))
    maxs = Vector((-math.inf, -math.inf, -math.inf))
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
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
    padding = 1.16
    needed_height = size.z * padding
    needed_width = max(size.x, size.y) * 1.35 * padding
    ortho_scale = max(needed_height, needed_width / aspect)

    cam = bpy.data.cameras.new("cam")
    cam.type = "ORTHO"
    cam.ortho_scale = ortho_scale
    obj = bpy.data.objects.new("cam", cam)
    offset = Vector((0.45, 1.5, 0.12)).normalized() * 3.0
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
    clear_scene()
    setup_world()
    build_mannequin()
    setup_camera()
    render_to(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
