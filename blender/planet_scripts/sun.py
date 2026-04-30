"""
Enhanced Sun Simulation for Blender 5.1
Includes realistic flare, atmosphere, and rotation.

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
SUN_TEXTURE = "2k_sun.jpg"

# Physical constants (scaled for scene units)
PLANET_RADIUS_SCALE = 0.25
SUN_VISUAL_SCALE = 1
SUN_RADIUS_KM = 696340.0

# Animation
FPS = 24
SIM_DAYS = 365
SUN_ROTATION_DAYS = 25.38  # Realistic solar rotation period (Earth days)

# Emission tuning
SUN_EMISSION_STRENGTH = 2.2
CORONA_EMISSION_STRENGTH = 2.5
FLARE_SHELL_SCALE = 1.15

# Quality tuning to reduce shimmer and pixelation in motion.
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

    # Safely clear orphaned datablocks after objects are removed.
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
    bg.inputs[0].default_value = (0.01, 0.01, 0.02, 1.0)  # Very dark blue-black
    bg.inputs[1].default_value = 0.15  # Slightly brighter to help render
    links.new(bg.outputs[0], out.inputs[0])


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

    # Populate UVs explicitly so image textures do not fall back to invalid mapping.
    for face in bm.faces:
        for loop in face.loops:
            luv = loop[uv_layer]
            co = loop.vert.co.normalized()
            # Move the UV seam to the far side so it stays out of the main camera view.
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


def build_sun_material_simple(texture_path):
    """Build a minimal sun material that only uses the base texture."""
    mat = bpy.data.materials.new("Sun_Mat")
    mat.use_nodes = True
    mat.use_backface_culling = False

    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    emission = nodes.new("ShaderNodeEmission")
    add_shader = nodes.new("ShaderNodeAddShader")

    # Keep most of the original texture appearance and add only a gentle glow.
    _set_input_value(bsdf, "Roughness", 1.0)
    if bsdf.inputs.get("Specular IOR Level"):
        _set_input_value(bsdf, "Specular IOR Level", 0.0)
    elif bsdf.inputs.get("Specular"):
        _set_input_value(bsdf, "Specular", 0.0)

    _set_input_value(emission, "Strength", SUN_EMISSION_STRENGTH)
    _set_input_value(emission, "Color", (1.0, 0.75, 0.2, 1.0))

    print(f"[DEBUG] Created emission node with strength {SUN_EMISSION_STRENGTH}")

    # Try to load texture and override color
    if texture_path and os.path.exists(texture_path):
        try:
            texcoord = nodes.new("ShaderNodeTexCoord")
            tex = nodes.new("ShaderNodeTexImage")

            texcoord.location = (-400, 0)
            tex.location = (-200, 0)
            bsdf.location = (50, 80)
            emission.location = (50, -80)
            add_shader.location = (250, 0)
            out.location = (450, 0)

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
            _link_if_possible(links, tex.outputs.get("Color"), emission.inputs.get("Color"))
            print(f"[INFO] Sun texture loaded: {texture_path}")
        except Exception as ex:
            print(f"[WARN] Could not load texture: {ex}")
    else:
        print(f"[INFO] Using fallback yellow-orange color (no texture)")
        _set_input_value(bsdf, "Base Color", (1.0, 0.75, 0.2, 1.0))

    # Wire principled surface plus a small emission lift to preserve texture detail.
    _link_if_possible(links, bsdf.outputs.get("BSDF"), add_shader.inputs[0])
    _link_if_possible(links, emission.outputs.get("Emission"), add_shader.inputs[1])
    _link_if_possible(links, add_shader.outputs.get("Shader"), out.inputs.get("Surface"))
    print(f"[DEBUG] Material wired: Principled + Emission -> Output")

    return mat


def make_camera_and_lights():
    """Setup camera and fill lights for solar rendering."""
    cam_data = bpy.data.cameras.new("SolarCam_Data")
    cam_data.clip_start = CAMERA_CLIP_START
    cam_data.clip_end = CAMERA_CLIP_END
    cam = bpy.data.objects.new("SolarCam", cam_data)
    target_collection = bpy.context.collection or bpy.context.scene.collection
    target_collection.objects.link(cam)
    cam.location = (0.0, -34.0, 13.0)
    cam.rotation_euler = (math.radians(74), 0.0, 0.0)
    bpy.context.scene.camera = cam

    # Key light: subtle fill to avoid complete darkness on backfaces
    light_key = bpy.data.lights.new("SolarKeyLight", type="AREA")
    light_key.energy = 200
    light_key.size = 50.0
    light_obj_key = bpy.data.objects.new("SolarKeyLight", light_key)
    target_collection.objects.link(light_obj_key)
    light_obj_key.location = (15.0, -25.0, 20.0)

    # Rim light: subtle back-lighting for depth
    light_rim = bpy.data.lights.new("SolarRimLight", type="AREA")
    light_rim.energy = 100
    light_rim.size = 30.0
    light_obj_rim = bpy.data.objects.new("SolarRimLight", light_rim)
    target_collection.objects.link(light_obj_rim)
    light_obj_rim.location = (-20.0, 20.0, -5.0)


def setup_sun_rotation(sun_obj):
    """Setup realistic solar rotation animation."""
    scene = bpy.context.scene
    start_frame = 1
    end_frame = SIM_DAYS * FPS
    scene.frame_start = start_frame
    scene.frame_end = end_frame

    # Sun rotation: complete rotation every 25.38 Earth days
    spin_cycles = SIM_DAYS / SUN_ROTATION_DAYS
    
    sun_obj.rotation_euler = (0.0, 0.0, 0.0)
    sun_obj.keyframe_insert(data_path="rotation_euler", frame=start_frame)
    sun_obj.rotation_euler[2] = spin_cycles * 2.0 * math.pi
    sun_obj.keyframe_insert(data_path="rotation_euler", frame=end_frame)

    # Set interpolation to linear for consistent speed
    if sun_obj.animation_data and sun_obj.animation_data.action:
        for fcurve in sun_obj.animation_data.action.fcurves:
            for kp in fcurve.keyframe_points:
                kp.interpolation = "LINEAR"


def configure_render():
    """Configure render engine and settings."""
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = SIM_DAYS * FPS

    # Use Cycles (most reliable for emission)
    try:
        scene.render.engine = "CYCLES"
        print("[INFO] Using Cycles render engine")
        
        # Cycles settings for faster preview
        scene.cycles.preview_samples = CYCLES_PREVIEW_SAMPLES
        scene.cycles.samples = CYCLES_RENDER_SAMPLES
        scene.cycles.use_denoising = True
        if hasattr(scene.cycles, "use_preview_denoising"):
            scene.cycles.use_preview_denoising = True
        if hasattr(scene.cycles, "pixel_filter_type"):
            scene.cycles.pixel_filter_type = "GAUSSIAN"
        if hasattr(scene.cycles, "filter_width"):
            scene.cycles.filter_width = 1.5
    except Exception as ex:
        print(f"[WARN] Cycles not available, trying Eevee: {ex}")
        try:
            scene.render.engine = "BLENDER_EEVEE_NEXT"
        except:
            scene.render.engine = "BLENDER_EEVEE"
        if hasattr(scene, "eevee"):
            if hasattr(scene.eevee, "taa_samples"):
                scene.eevee.taa_samples = EEVEE_TAA_VIEWPORT_SAMPLES
            if hasattr(scene.eevee, "taa_render_samples"):
                scene.eevee.taa_render_samples = EEVEE_TAA_RENDER_SAMPLES


def build_sun_scene(clear_existing=True):
    """Main function to build enhanced sun scene."""
    print("[START] Building sun scene...")
    if clear_existing:
        clear_scene()
        print("[INFO] Scene cleared")

    world_setup()
    print("[INFO] World setup complete")

    # Create sun sphere with realistic radius
    sun_radius_scene = (SUN_RADIUS_KM / 6371.0) * PLANET_RADIUS_SCALE * SUN_VISUAL_SCALE
    print(f"[DEBUG] Sun radius: {sun_radius_scene} units")
    
    sun = create_uv_sphere("Sun", sun_radius_scene, (0.0, 0.0, 0.0), segments=128)
    print(f"[INFO] Sun sphere created: {sun.name}")
    print(f"[DEBUG] Sun location: {sun.location}, dimensions: {sun.dimensions}")

    # Build material with proper emission
    texture_path = os.path.join(TEXTURE_BASE_DIR, SUN_TEXTURE)
    sun_mat = build_sun_material_simple(texture_path)
    sun.data.materials.append(sun_mat)
    print(f"[INFO] Sun material applied: {sun_mat.name}")

    # Setup animation
    setup_sun_rotation(sun)
    print("[INFO] Animation setup complete")

    # Camera and lights
    make_camera_and_lights()
    print("[INFO] Camera and lights created")

    # Render config
    configure_render()
    print("[INFO] Render configured")

    # Final scene check
    print(f"[DEBUG] Total objects in scene: {len(bpy.context.scene.objects)}")
    for obj in bpy.context.scene.objects:
        print(f"  - {obj.name} at {obj.location}")

    print("[SUCCESS] Sun scene built successfully!")


if __name__ == "__main__":
    try:
        build_sun_scene(clear_existing=True)
    except Exception as ex:
        print(f"[ERROR] Failed to build sun scene: {ex}")
        traceback.print_exc()
