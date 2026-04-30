"""
Mercury-Only Simulation for Blender 5.1

Builds a scene with only Mercury, its orbit guide, and lighting.
The script uses a separate tilt parent so Mercury's axial tilt,
spin direction, and revolution direction stay physically consistent.

Run in Blender Text Editor:
1) Open this file.
2) Set TEXTURE_BASE_DIR to your texture folder.
3) Run Script.
"""

import bpy
import bmesh
import math
import os
import traceback

# Update this to your local texture path.
TEXTURE_BASE_DIR = r"D:\Solar_Texture_2k"

# Timeline
FPS = 24
SIM_DAYS = 365

# Scene scale
PLANET_RADIUS_SCALE = 0.25
ORBIT_DISTANCE_SCALE = 0.06

# Mercury physical/orbital data
MERCURY_RADIUS_KM = 2439.7
MERCURY_ORBIT_AU = 0.39
MERCURY_ROTATION_DAYS = 58.6
MERCURY_ORBITAL_DAYS = 88.0
MERCURY_AXIS_TILT_DEG = 0.034
MERCURY_TEXTURE = "2k_mercury.jpg"

# Positive Z rotation in Blender is counterclockwise when viewed from above.
# Mercury rotates prograde and revolves prograde, so both stay positive.
MERCURY_SPIN_DIRECTION = 1.0
MERCURY_REVOLUTION_DIRECTION = 1.0

# Quality tuning
TEXTURE_INTERPOLATION = "Cubic"
CYCLES_PREVIEW_SAMPLES = 128
CYCLES_RENDER_SAMPLES = 256
EEVEE_TAA_VIEWPORT_SAMPLES = 32
EEVEE_TAA_RENDER_SAMPLES = 128
CAMERA_CLIP_START = 0.01
CAMERA_CLIP_END = 5000.0


def _set_input_value(node, socket_name, value):
    sock = node.inputs.get(socket_name)
    if not sock:
        return
    try:
        sock.default_value = value
    except Exception:
        pass


def _link_if_possible(links, from_socket, to_socket):
    if from_socket is None or to_socket is None:
        return
    try:
        links.new(from_socket, to_socket)
    except Exception:
        pass


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    for block in list(bpy.data.meshes):
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in list(bpy.data.curves):
        if block.users == 0:
            bpy.data.curves.remove(block)
    for block in list(bpy.data.materials):
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in list(bpy.data.lights):
        if block.users == 0:
            bpy.data.lights.remove(block)
    for block in list(bpy.data.cameras):
        if block.users == 0:
            bpy.data.cameras.remove(block)


def world_setup():
    world = bpy.data.worlds.get("SpaceWorld")
    if world is None:
        world = bpy.data.worlds.new("SpaceWorld")
    bpy.context.scene.world = world
    world.use_nodes = True

    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputWorld")
    bg = nodes.new("ShaderNodeBackground")
    bg.inputs[0].default_value = (0.0, 0.0, 0.0, 1.0)
    bg.inputs[1].default_value = 0.03
    links.new(bg.outputs[0], out.inputs[0])


def build_mercury_material(texture_path):
    mat = bpy.data.materials.new("Mercury_Mat")
    mat.use_nodes = True

    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    _set_input_value(bsdf, "Roughness", 0.82)
    if bsdf.inputs.get("Specular IOR Level"):
        _set_input_value(bsdf, "Specular IOR Level", 0.08)
    elif bsdf.inputs.get("Specular"):
        _set_input_value(bsdf, "Specular", 0.08)

    if texture_path and os.path.exists(texture_path):
        try:
            texcoord = nodes.new("ShaderNodeTexCoord")
            tex = nodes.new("ShaderNodeTexImage")
            texcoord.location = (-400, 0)
            tex.location = (-200, 0)

            img = bpy.data.images.load(texture_path, check_existing=True)
            tex.image = img
            tex.extension = "REPEAT"
            tex.interpolation = TEXTURE_INTERPOLATION
            if hasattr(img, "colorspace_settings"):
                img.colorspace_settings.name = "sRGB"
            if hasattr(img, "alpha_mode"):
                img.alpha_mode = "NONE"

            _link_if_possible(links, texcoord.outputs.get("UV"), tex.inputs.get("Vector"))
            _link_if_possible(links, tex.outputs.get("Color"), bsdf.inputs.get("Base Color"))
            print(f"[INFO] Mercury texture loaded: {texture_path}")
        except Exception as ex:
            print(f"[WARN] Mercury texture load failed: {ex}")
            _set_input_value(bsdf, "Base Color", (0.55, 0.52, 0.48, 1.0))
    else:
        print("[INFO] Mercury texture not found, using fallback color")
        _set_input_value(bsdf, "Base Color", (0.55, 0.52, 0.48, 1.0))

    _link_if_possible(links, bsdf.outputs.get("BSDF"), out.inputs.get("Surface"))
    return mat


def create_uv_sphere(name, radius, location=(0.0, 0.0, 0.0), segments=96):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    bmesh.ops.create_uvsphere(
        bm,
        u_segments=max(12, segments),
        v_segments=max(8, segments // 2),
        radius=radius,
    )

    for face in bm.faces:
        for loop in face.loops:
            luv = loop[uv_layer]
            co = loop.vert.co.normalized()
            u = 0.5 + math.atan2(co.x, -co.y) / (2.0 * math.pi)
            v = 0.5 - math.asin(max(-1.0, min(1.0, co.z))) / math.pi
            luv.uv = (u, v)

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    target_collection = bpy.context.collection or bpy.context.scene.collection
    target_collection.objects.link(obj)
    obj.location = location

    for poly in mesh.polygons:
        poly.use_smooth = True

    return obj


def create_orbit_curve(name, radius):
    curve_data = bpy.data.curves.new(name + "_Curve", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 64
    curve_data.bevel_depth = 0.008

    spline = curve_data.splines.new(type="POLY")
    points_count = 144
    spline.points.add(points_count - 1)
    for i in range(points_count):
        angle = (i / points_count) * (2.0 * math.pi)
        spline.points[i].co = (
            math.cos(angle) * radius,
            math.sin(angle) * radius,
            0.0,
            1.0,
        )
    spline.use_cyclic_u = True

    orbit = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(orbit)

    mat = bpy.data.materials.new(name + "_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    _set_input_value(emission, "Color", (0.35, 0.35, 0.4, 1.0))
    _set_input_value(emission, "Strength", 0.15)
    links.new(emission.outputs[0], out.inputs[0])
    curve_data.materials.append(mat)
    return orbit


def make_camera_and_light():
    cam_data = bpy.data.cameras.new("MercuryCam_Data")
    cam_data.clip_start = CAMERA_CLIP_START
    cam_data.clip_end = CAMERA_CLIP_END
    cam = bpy.data.objects.new("MercuryCam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = (0.0, -15.0, 6.5)
    cam.rotation_euler = (math.radians(68), 0.0, 0.0)
    bpy.context.scene.camera = cam

    sun_light_data = bpy.data.lights.new("MercurySunLight_Data", type="SUN")
    sun_light_data.energy = 4.0
    sun_light = bpy.data.objects.new("MercurySunLight", sun_light_data)
    bpy.context.collection.objects.link(sun_light)
    sun_light.rotation_euler = (math.radians(55), math.radians(0), math.radians(35))

    fill_data = bpy.data.lights.new("MercuryFill_Data", type="AREA")
    fill_data.energy = 150
    fill_data.size = 14.0
    fill = bpy.data.objects.new("MercuryFill", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = (-5.0, -10.0, 8.0)


def configure_render():
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = SIM_DAYS * FPS

    try:
        scene.render.engine = "CYCLES"
        scene.cycles.preview_samples = CYCLES_PREVIEW_SAMPLES
        scene.cycles.samples = CYCLES_RENDER_SAMPLES
        scene.cycles.use_denoising = True
        if hasattr(scene.cycles, "use_preview_denoising"):
            scene.cycles.use_preview_denoising = True
        if hasattr(scene.cycles, "pixel_filter_type"):
            scene.cycles.pixel_filter_type = "GAUSSIAN"
        if hasattr(scene.cycles, "filter_width"):
            scene.cycles.filter_width = 1.5
        print("[INFO] Using Cycles render engine")
    except Exception:
        if "BLENDER_EEVEE_NEXT" in scene.render.bl_rna.properties["engine"].enum_items.keys():
            scene.render.engine = "BLENDER_EEVEE_NEXT"
        else:
            scene.render.engine = "BLENDER_EEVEE"
        if hasattr(scene, "eevee"):
            if hasattr(scene.eevee, "taa_samples"):
                scene.eevee.taa_samples = EEVEE_TAA_VIEWPORT_SAMPLES
            if hasattr(scene.eevee, "taa_render_samples"):
                scene.eevee.taa_render_samples = EEVEE_TAA_RENDER_SAMPLES
        print(f"[INFO] Using {scene.render.engine} render engine")


def setup_animation(orbit_empty, tilt_empty, planet):
    scene = bpy.context.scene
    start_frame = 1
    end_frame = SIM_DAYS * FPS
    scene.frame_start = start_frame
    scene.frame_end = end_frame

    tilt_empty.rotation_euler = (math.radians(MERCURY_AXIS_TILT_DEG), 0.0, 0.0)

    spin_cycles = SIM_DAYS / abs(MERCURY_ROTATION_DAYS)
    planet.rotation_euler = (0.0, 0.0, 0.0)
    planet.keyframe_insert(data_path="rotation_euler", frame=start_frame)
    planet.rotation_euler[2] = MERCURY_SPIN_DIRECTION * spin_cycles * 2.0 * math.pi
    planet.keyframe_insert(data_path="rotation_euler", frame=end_frame)

    orbit_cycles = SIM_DAYS / MERCURY_ORBITAL_DAYS
    orbit_empty.rotation_euler = (0.0, 0.0, 0.0)
    orbit_empty.keyframe_insert(data_path="rotation_euler", frame=start_frame)
    orbit_empty.rotation_euler[2] = MERCURY_REVOLUTION_DIRECTION * orbit_cycles * 2.0 * math.pi
    orbit_empty.keyframe_insert(data_path="rotation_euler", frame=end_frame)

    for obj in (planet, orbit_empty):
        if obj.animation_data and obj.animation_data.action:
            for fcurve in obj.animation_data.action.fcurves:
                for kp in fcurve.keyframe_points:
                    kp.interpolation = "LINEAR"


def build_mercury_scene(clear_existing=True):
    print("[START] Building Mercury-only scene...")
    if clear_existing:
        clear_scene()
        print("[INFO] Scene cleared")

    world_setup()

    earth_radius_scene = 1.0 * PLANET_RADIUS_SCALE
    mercury_radius_scene = (MERCURY_RADIUS_KM / 6371.0) * earth_radius_scene
    mercury_distance_scene = MERCURY_ORBIT_AU * (149.6 * ORBIT_DISTANCE_SCALE)

    orbit_empty = bpy.data.objects.new("Mercury_Orbit", None)
    bpy.context.collection.objects.link(orbit_empty)
    orbit_empty.location = (0.0, 0.0, 0.0)

    tilt_empty = bpy.data.objects.new("Mercury_AxisTilt", None)
    bpy.context.collection.objects.link(tilt_empty)
    tilt_empty.parent = orbit_empty
    tilt_empty.location = (mercury_distance_scene, 0.0, 0.0)

    mercury = create_uv_sphere("Mercury", mercury_radius_scene, (0.0, 0.0, 0.0), segments=96)
    mercury.parent = tilt_empty
    mercury_mat = build_mercury_material(os.path.join(TEXTURE_BASE_DIR, MERCURY_TEXTURE))
    mercury.data.materials.append(mercury_mat)

    create_orbit_curve("Mercury_OrbitPath", mercury_distance_scene)
    setup_animation(orbit_empty, tilt_empty, mercury)

    make_camera_and_light()
    configure_render()

    print(f"[INFO] Mercury radius in scene: {mercury_radius_scene}")
    print(f"[INFO] Mercury orbit distance in scene: {mercury_distance_scene}")
    print(f"[INFO] Mercury axis tilt: {MERCURY_AXIS_TILT_DEG} degrees")
    print("[SUCCESS] Mercury-only scene built successfully")


if __name__ == "__main__":
    try:
        build_mercury_scene(clear_existing=True)
    except Exception as ex:
        print(f"[ERROR] Failed to build Mercury-only scene: {ex}")
        traceback.print_exc()
