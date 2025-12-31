# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] — 2024-01-01

### Added
- Full `.c2m` binary format parser supporting all 16 CoD game versions
  (CoD4 through Black Ops Cold War)
- StaticMesh builder: converts CoD BSP geometry and XModel props to UE5
  `UStaticMesh` assets with correct normals, UVs, and vertex colours
- Material builder: creates UE5 `UMaterial` assets with proper PBR node graphs
  for all CoD texture types (colorMap, normalMap, specularMap, glossMap,
  emissionMap, revealMap)
- Automatic DirectX → OpenGL normal map conversion (`flip_green_channel = True`)
- Texture importer: imports `.tga` files with correct sRGB / linear settings
- Light builder: spawns `DirectionalLight`, `SpotLight`, and `PointLight` actors
  with converted intensity, cone angles, and attenuation radii
- Transparent surface handling: vertex normal offset for `sort_key > 0` surfaces
- Coordinate system conversion: CoD inches / Y-left → UE5 centimetres / Y-right
- UV V-coordinate flip (CoD bottom-left → UE5 top-left origin)
- Triangle winding order correction for Y-axis handedness change
- `colorTint` material setting applied as a multiply node over base colour
- Progress dialogs with cancellation support for all long-running operations
- Duplicate-safe: re-running on the same map skips already-imported assets
- `run_import.py` user script for easy configuration
- Full docstrings, type hints, and inline code comments throughout

### Known Limitations
- Blend material surfaces (multi-material per surface with vertex colour weights)
  are imported using the primary material only; full blend graph is not yet wired
- Animated sprite sheet materials (`rowCount` / `columnCount` settings) are
  imported as static materials without animation
- Skybox texture import is not yet implemented
- Very large maps (20,000+ meshes) may take several minutes to import
