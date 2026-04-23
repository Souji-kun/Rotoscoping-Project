# Solar System Assets (2K) for Blender 5.1

Use these textures with `solar_system_sim_51.py`.
Place downloaded files in your local folder (example):
`D:\solar_textures_2k`

## Planet textures (Solar System Scope 2K)

- Sun: https://www.solarsystemscope.com/textures/download/2k_sun.jpg
- Mercury: https://www.solarsystemscope.com/textures/download/2k_mercury.jpg
- Venus: https://www.solarsystemscope.com/textures/download/2k_venus_surface.jpg
- Earth: https://www.solarsystemscope.com/textures/download/2k_earth_daymap.jpg
- Mars: https://www.solarsystemscope.com/textures/download/2k_mars.jpg
- Jupiter: https://www.solarsystemscope.com/textures/download/2k_jupiter.jpg
- Saturn: https://www.solarsystemscope.com/textures/download/2k_saturn.jpg
- Uranus: https://www.solarsystemscope.com/textures/download/2k_uranus.jpg
- Neptune: https://www.solarsystemscope.com/textures/download/2k_neptune.jpg
- Pluto: https://www.solarsystemscope.com/textures/download/2k_pluto.jpg

## Optional advanced maps

- Earth clouds: https://www.solarsystemscope.com/textures/download/2k_earth_clouds.jpg
- Earth night lights: https://www.solarsystemscope.com/textures/download/2k_earth_nightmap.jpg
- Moon (if you want to extend): https://www.solarsystemscope.com/textures/download/2k_moon.jpg
- Saturn ring texture: https://www.solarsystemscope.com/textures/download/2k_saturn_ring_alpha.png

## Sun flare / corona options

The script already generates a procedural flare shell (`Sun_Flare_Shell`) with animated emission.

If you want stronger VFX:

1. Add Glow/Bloom in Eevee Next (Render Properties -> Bloom).
2. Add a noise displacement modifier on `Sun_Flare_Shell`.
3. Add animated color ramp on emission strength.
4. Use a star HDRI for background (optional):
   - https://polyhaven.com/hdris (search: space, stars)

## File naming required by script

Ensure these exact filenames exist in your texture folder:

- `2k_sun.jpg`
- `2k_mercury.jpg`
- `2k_venus_surface.jpg`
- `2k_earth_daymap.jpg`
- `2k_mars.jpg`
- `2k_jupiter.jpg`
- `2k_saturn.jpg`
- `2k_uranus.jpg`
- `2k_neptune.jpg`
- `2k_pluto.jpg`

## Quick run

1. Open Blender 5.1
2. Open `blender/solar_system_sim_51.py`
3. Edit `TEXTURE_BASE_DIR`
4. Run Script
5. Press Play to watch spin + revolution animation
