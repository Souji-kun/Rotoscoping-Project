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
# Mercury physical/orbital data
MERCURY_RADIUS_KM = 2439.7
MERCURY_ROTATION_DAYS = 58.6
MERCURY_AXIS_TILT_DEG = 0.034
MERCURY_TEXTURE = "2k_mercury.jpg"
MILKYWAY_TEXTURE = "2k_Milkyway.jpg"

# Mercury rotates prograde. We animate the spin on local Y so the
# visible presentation axis matches this standalone shot setup.
MERCURY_SPIN_DIRECTION = 1.0
SHOW_AXIS_GUIDE = True
AXIS_GUIDE_RADIUS = 0.02
AXIS_GUIDE_LENGTH_SCALE = 2.6
AXIS_GUIDE_COLOR = (0.35, 0.8, 1.0, 1.0)

# Quality tuning
TEXTURE_INTERPOLATION = "Cubic"
CYCLES_PREVIEW_SAMPLES = 128
CYCLES_RENDER_SAMPLES = 256
EEVEE_TAA_VIEWPORT_SAMPLES = 32
EEVEE_TAA_RENDER_SAMPLES = 128
CAMERA_CLIP_START = 0.01
CAMERA_CLIP_END = 5000.0
CAMERA_LENS_MM = 70
CAMERA_DISTANCE = 6.0
CAMERA_HEIGHT = 0.35
CAMERA_X_ANGLE_DEG = 0.0
CAMERA_Y_ANGLE_DEG = 0.0
CAMERA_Z_ANGLE_DEG = 0.0
MERCURY_MODEL_Z_ANGLE_DEG = 18.0
OUTPUT_FILEPATH = "//renders/mercury_only.mp4"
WORLD_BACKGROUND_STRENGTH = 0.8
MERCURY_SHELL_SCALE = 1.01
MERCURY_SHELL_EMISSION_STRENGTH = 0.35
MERCURY_SHELL_ALPHA = 0.18
LIGHT_Y_OFFSET = 1.0
LIGHT_Z_OFFSET = 0.6
LIGHT_ENERGY = 2500
LIGHT_SIZE = 3.0


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


def _scene_collection():
    return bpy.context.scene.collection


def _link_object(obj):
    _scene_collection().objects.link(obj)


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
    env = nodes.new("ShaderNodeTexEnvironment")
    mapping = nodes.new("ShaderNodeMapping")
    texcoord = nodes.new("ShaderNodeTexCoord")

    texcoord.location = (-800, 0)
    mapping.location = (-600, 0)
    env.location = (-400, 0)
    bg.location = (-150, 0)
    out.location = (100, 0)

    bg.inputs[1].default_value = WORLD_BACKGROUND_STRENGTH

    texture_path = os.path.join(TEXTURE_BASE_DIR, MILKYWAY_TEXTURE)
    if os.path.exists(texture_path):
        try:
            img = bpy.data.images.load(texture_path, check_existing=True)
            env.image = img
            if hasattr(img, "colorspace_settings"):
                img.colorspace_settings.name = "sRGB"
            _link_if_possible(links, texcoord.outputs.get("Generated"), mapping.inputs.get("Vector"))
            _link_if_possible(links, mapping.outputs.get("Vector"), env.inputs.get("Vector"))
            _link_if_possible(links, env.outputs.get("Color"), bg.inputs.get("Color"))
            print(f"[INFO] Milky Way world texture loaded: {texture_path}")
        except Exception as ex:
            print(f"[WARN] Milky Way world texture load failed: {ex}")
            bg.inputs[0].default_value = (0.02, 0.02, 0.03, 1.0)
    else:
        print("[INFO] Milky Way texture not found, using fallback world color")
        bg.inputs[0].default_value = (0.02, 0.02, 0.03, 1.0)

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


def build_mercury_shell_material(texture_path):
    mat = bpy.data.materials.new("Mercury_Shell_Mat")
    mat.use_nodes = True
    mat.use_backface_culling = False
    mat.blend_method = "BLEND"
    if hasattr(mat, "shadow_method"):
        mat.shadow_method = "NONE"

    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    texcoord = nodes.new("ShaderNodeTexCoord")
    tex = nodes.new("ShaderNodeTexImage")
    emission = nodes.new("ShaderNodeEmission")
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")

    texcoord.location = (-800, 0)
    tex.location = (-600, 0)
    transparent.location = (-350, -120)
    emission.location = (-350, 80)
    mix.location = (-80, 0)
    out.location = (150, 0)

    _set_input_value(mix, "Fac", MERCURY_SHELL_ALPHA)
    _set_input_value(emission, "Strength", MERCURY_SHELL_EMISSION_STRENGTH)

    if texture_path and os.path.exists(texture_path):
        try:
            img = bpy.data.images.load(texture_path, check_existing=True)
            tex.image = img
            tex.extension = "REPEAT"
            tex.interpolation = TEXTURE_INTERPOLATION
            if hasattr(img, "colorspace_settings"):
                img.colorspace_settings.name = "sRGB"
            if hasattr(img, "alpha_mode"):
                img.alpha_mode = "NONE"

            _link_if_possible(links, texcoord.outputs.get("UV"), tex.inputs.get("Vector"))
            _link_if_possible(links, tex.outputs.get("Color"), emission.inputs.get("Color"))
        except Exception as ex:
            print(f"[WARN] Mercury shell texture load failed: {ex}")
            _set_input_value(emission, "Color", (0.55, 0.52, 0.48, 1.0))
    else:
        _set_input_value(emission, "Color", (0.55, 0.52, 0.48, 1.0))

    _link_if_possible(links, transparent.outputs.get("BSDF"), mix.inputs[1])
    _link_if_possible(links, emission.outputs.get("Emission"), mix.inputs[2])
    _link_if_possible(links, mix.outputs.get("Shader"), out.inputs.get("Surface"))
    return mat


def build_mercury_shell_material(texture_path):
    mat = bpy.data.materials.new("Mercury_Shell_Mat")
    mat.use_nodes = True
    mat.use_backface_culling = False

    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    emission = nodes.new("ShaderNodeEmission")
    _set_input_value(emission, "Strength", MERCURY_SHELL_EMISSION_STRENGTH)

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
            _link_if_possible(links, tex.outputs.get("Color"), emission.inputs.get("Color"))
        except Exception as ex:
            print(f"[WARN] Mercury shell texture load failed: {ex}")
            _set_input_value(emission, "Color", (0.55, 0.52, 0.48, 1.0))
    else:
        _set_input_value(emission, "Color", (0.55, 0.52, 0.48, 1.0))

    _link_if_possible(links, emission.outputs.get("Emission"), out.inputs.get("Surface"))
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
    _link_object(obj)
    obj.location = location

    for poly in mesh.polygons:
        poly.use_smooth = True

    return obj


def create_axis_guide(name, planet_radius):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=24,
        radius1=AXIS_GUIDE_RADIUS,
        radius2=AXIS_GUIDE_RADIUS,
        depth=planet_radius * AXIS_GUIDE_LENGTH_SCALE,
    )
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    axis_obj = bpy.data.objects.new(name, mesh)
    _link_object(axis_obj)

    # Blender cylinders/cones are aligned to local Z by default.
    # Rotate so the guide follows Mercury's spin axis on local Y.
    axis_obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    mat = bpy.data.materials.new(name + "_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    _set_input_value(bsdf, "Base Color", AXIS_GUIDE_COLOR)
    _set_input_value(bsdf, "Roughness", 0.5)
    links.new(bsdf.outputs[0], out.inputs[0])
    mesh.materials.append(mat)

    return axis_obj


def make_camera_and_light(target_obj=None):
    cam_data = bpy.data.cameras.new("MercuryCam_Data")
    cam_data.clip_start = CAMERA_CLIP_START
    cam_data.clip_end = CAMERA_CLIP_END
    cam_data.lens = CAMERA_LENS_MM
    cam = bpy.data.objects.new("MercuryCam", cam_data)
    _link_object(cam)
    cam.location = (CAMERA_DISTANCE, 0.0, CAMERA_HEIGHT)
    cam.rotation_euler = (
        math.radians(CAMERA_X_ANGLE_DEG),
        math.radians(CAMERA_Y_ANGLE_DEG),
        math.radians(CAMERA_Z_ANGLE_DEG),
    )
    bpy.context.scene.camera = cam

    if target_obj is not None:
        track = cam.constraints.new(type="TRACK_TO")
        track.target = target_obj
        track.track_axis = "TRACK_NEGATIVE_Z"
        track.up_axis = "UP_Y"

    light_data = bpy.data.lights.new("MercuryLight_Data", type="AREA")
    light_data.energy = LIGHT_ENERGY
    light_data.size = LIGHT_SIZE
    light = bpy.data.objects.new("MercuryLight", light_data)
    _link_object(light)

    if target_obj is not None:
        light.location = (
            target_obj.location.x,
            target_obj.location.y + LIGHT_Y_OFFSET,
            target_obj.location.z + LIGHT_Z_OFFSET,
        )
        track = light.constraints.new(type="TRACK_TO")
        track.target = target_obj
        track.track_axis = "TRACK_NEGATIVE_Z"
        track.up_axis = "UP_Y"
    else:
        light.location = (0.0, LIGHT_Y_OFFSET, LIGHT_Z_OFFSET)

    return cam


def configure_render():
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = SIM_DAYS * FPS
    scene.render.fps = FPS
    scene.render.filepath = OUTPUT_FILEPATH
    scene.render.image_settings.file_format = "FFMPEG"
    if hasattr(scene.render, "ffmpeg"):
        scene.render.ffmpeg.format = "MPEG4"
        scene.render.ffmpeg.codec = "H264"
        if hasattr(scene.render.ffmpeg, "constant_rate_factor"):
            scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
        if hasattr(scene.render.ffmpeg, "ffmpeg_preset"):
            scene.render.ffmpeg.ffmpeg_preset = "GOOD"
        if hasattr(scene.render.ffmpeg, "audio_codec"):
            scene.render.ffmpeg.audio_codec = "NONE"

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


def setup_animation(tilt_empty, planet):
    scene = bpy.context.scene
    start_frame = 1
    end_frame = SIM_DAYS * FPS
    scene.frame_start = start_frame
    scene.frame_end = end_frame

    tilt_empty.rotation_euler = (math.radians(MERCURY_AXIS_TILT_DEG), 0.0, 0.0)
    planet.rotation_euler = (0.0, 0.0, math.radians(MERCURY_MODEL_Z_ANGLE_DEG))

    spin_cycles = SIM_DAYS / abs(MERCURY_ROTATION_DAYS)
    planet.keyframe_insert(data_path="rotation_euler", frame=start_frame)
    planet.rotation_euler[1] = MERCURY_SPIN_DIRECTION * spin_cycles * 2.0 * math.pi
    planet.keyframe_insert(data_path="rotation_euler", frame=end_frame)

    for obj in (planet,):
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

    tilt_empty = bpy.data.objects.new("Mercury_AxisTilt", None)
    _link_object(tilt_empty)
    tilt_empty.location = (0.0, 0.0, 0.0)

    mercury = create_uv_sphere("Mercury", mercury_radius_scene, (0.0, 0.0, 0.0), segments=96)
    mercury.parent = tilt_empty
    texture_path = os.path.join(TEXTURE_BASE_DIR, MERCURY_TEXTURE)
    mercury_mat = build_mercury_material(texture_path)
    mercury.data.materials.append(mercury_mat)

    mercury_shell = create_uv_sphere(
        "Mercury_Shell",
        mercury_radius_scene * MERCURY_SHELL_SCALE,
        (0.0, 0.0, 0.0),
        segments=96,
    )
    mercury_shell.parent = tilt_empty
    mercury_shell_mat = build_mercury_shell_material(texture_path)
    mercury_shell.data.materials.append(mercury_shell_mat)

    mercury_shell = create_uv_sphere(
        "Mercury_Shell",
        mercury_radius_scene * MERCURY_SHELL_SCALE,
        (0.0, 0.0, 0.0),
        segments=96,
    )
    mercury_shell.parent = tilt_empty
    mercury_shell_mat = build_mercury_shell_material(texture_path)
    mercury_shell.data.materials.append(mercury_shell_mat)

    if SHOW_AXIS_GUIDE:
        axis_guide = create_axis_guide("Mercury_AxisGuide", mercury_radius_scene)
        axis_guide.parent = tilt_empty
        axis_guide.location = (0.0, 0.0, 0.0)

    setup_animation(tilt_empty, mercury)

    cam = make_camera_and_light(mercury)
    configure_render()
    bpy.context.scene.camera = cam
    if bpy.context.view_layer.objects.active is None:
        bpy.context.view_layer.objects.active = cam

    print(f"[INFO] Mercury radius in scene: {mercury_radius_scene}")
    print(f"[INFO] Mercury axis tilt: {MERCURY_AXIS_TILT_DEG} degrees")
    print(f"[INFO] Camera location: ({CAMERA_DISTANCE}, 0.0, {CAMERA_HEIGHT})")
    print(f"[INFO] Camera Y angle: {CAMERA_Y_ANGLE_DEG} degrees")
    print(f"[INFO] Mercury spin axis: local Y")
    print(f"[INFO] Mercury model Z angle: {MERCURY_MODEL_Z_ANGLE_DEG} degrees")
    print(f"[INFO] Axis guide enabled: {SHOW_AXIS_GUIDE}")
    print(f"[INFO] Mercury shell emission strength: {MERCURY_SHELL_EMISSION_STRENGTH}")
    print(f"[INFO] Output path: {OUTPUT_FILEPATH}")
    print(f"[INFO] Active scene camera: {bpy.context.scene.camera.name}")
    print("[SUCCESS] Mercury-only scene built successfully")


if __name__ == "__main__":
    try:
        build_mercury_scene(clear_existing=True)
    except Exception as ex:
        print(f"[ERROR] Failed to build Mercury-only scene: {ex}")
        traceback.print_exc()
