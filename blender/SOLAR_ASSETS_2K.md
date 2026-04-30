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

## Normalized celestial body size and distance reference

Sun visual scale is normalized to `1.0`.

- `size_normalized` = `body_radius_km / sun_radius_km`
- `distance_normalized` = `orbit_distance_km / sun_radius_km`
- Reference constants:
  - `sun_radius_km = 696340.0`
  - `1 AU = 149600000.0 km`

| Body | Radius (km) | Orbit (AU) | Size Normalized (Sun = 1) | Orbit Distance (km) | Distance Normalized (Sun radius = 1) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Sun | 696340.0 | 0.00 | 1.000000 | 0.0 | 0.00 |
| Mercury | 2439.7 | 0.39 | 0.003504 | 58344000.0 | 83.79 |
| Venus | 6051.8 | 0.72 | 0.008691 | 107712000.0 | 154.68 |
| Earth | 6371.0 | 1.00 | 0.009149 | 149600000.0 | 214.84 |
| Mars | 3389.5 | 1.52 | 0.004868 | 227392000.0 | 326.55 |
| Jupiter | 69911.0 | 5.20 | 0.100398 | 777920000.0 | 1117.16 |
| Saturn | 58232.0 | 9.58 | 0.083626 | 1433168000.0 | 2058.14 |
| Uranus | 25362.0 | 19.20 | 0.036422 | 2872320000.0 | 4124.88 |
| Neptune | 24622.0 | 30.05 | 0.035359 | 4495480000.0 | 6455.87 |
| Pluto | 1188.3 | 39.48 | 0.001706 | 5906208000.0 | 8481.79 |
