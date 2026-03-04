# C2M → UE5 Importer

<div align="center">

![License](https://img.shields.io/github/license/yourusername/c2m-ue5-importer?style=flat-square)
![UE5](https://img.shields.io/badge/Unreal_Engine-5.1%2B-blue?style=flat-square&logo=unrealengine)
![Python](https://img.shields.io/badge/Python-3.9%2B-yellow?style=flat-square&logo=python)
![Status](https://img.shields.io/badge/status-stable-brightgreen?style=flat-square)

**Import Call of Duty map files (.c2m) directly into Unreal Engine 5.**

Ported and extended from [SHEILAN's Blender C2M Importer](https://github.com/sheilan102/C2M?tab=readme-ov-file).

</div>

---

## What is C2M?

`.c2m` is a binary map format exported by **[Greyhound](https://github.com/dtzxporter/Greyhound)** and **CoDMap** tools. It packages all geometry, materials, prop instances, and lights from a Call of Duty level into a single file ready for import into 3D applications.

This plugin reads that binary format and reconstructs the full map inside an Unreal Engine 5 level — geometry, textures, materials, prop placement, and lights.

---

## Supported Games

| # | Game |
|---|------|
| 0 | Call of Duty 4: Modern Warfare |
| 1 | Call of Duty: World at War |
| 2 | Modern Warfare 2 |
| 3 | Black Ops |
| 4 | Modern Warfare 3 |
| 5 | Black Ops 2 |
| 6 | Ghosts |
| 7 | Advanced Warfare |
| 8 | Black Ops 3 |
| 9 | Modern Warfare Remastered |
| 10 | Infinite Warfare |
| 11 | WWII |
| 12 | Black Ops 4 |
| 13 | Modern Warfare (2019) |
| 14 | Modern Warfare 2 Campaign Remastered |
| 15 | Black Ops Cold War |

---

## Features

- ✅ Full map BSP geometry import
- ✅ XModel prop placement with correct position, rotation, and scale
- ✅ Automatic texture import (.tga → UTexture2D) with correct sRGB/linear settings
- ✅ DirectX normal maps auto-converted to OpenGL (flip green channel)
- ✅ Material creation for all CoD shader types (opaque, transparent, glass, emissive, reveal)
- ✅ `colorTint` material setting applied as multiply node
- ✅ Sun, Spot, and Point light spawning with correct intensity and cone angles
- ✅ Correct CoD → UE5 coordinate conversion (inches→cm, Y-axis handedness)
- ✅ Progress dialogs with cancellation support
- ✅ Duplicate-safe (re-running on the same map skips already-imported assets)

---

## Requirements

- **Unreal Engine 5.1** or newer
- **Python Editor Script Plugin** enabled in UE5
- **Greyhound** (to export `.c2m` files from a CoD game)

---

## Installation

1. **Download** the latest release zip from the [Releases](../../releases) page.

2. **Copy** the `Content/Python/` folder into your UE5 project:
   ```
   YourUE5Project/
   └── Content/
       └── Python/
           ├── C2MImporter/       ← plugin package
           └── run_import.py      ← configure and run this
   ```

3. **Enable Python** in UE5:
   - `Edit` → `Plugins` → search **"Python Editor Script Plugin"** → ✅ Enable
   - Restart the editor

4. *(Optional)* Add `Content/Python` to your Python path in Project Settings:
   - `Edit` → `Project Settings` → `Plugins` → `Python` → **Additional Paths** → add `$(ProjectDir)/Content/Python`

---

## Usage

### Step 1 — Export from Greyhound

1. Launch the CoD game and open **Greyhound**
2. Find your map (e.g. `mp_rust`)
3. Export as **C2M** format

Your output should look like:
```
C:/MyExports/
├── exported/
│   └── mp_rust.c2m
└── exported_images/
    └── modern_warfare/
        ├── texture_name.tga
        └── ...
```

### Step 2 — Configure `run_import.py`

Open `Content/Python/run_import.py` and set your paths:

```python
C2M_FILE_PATH    = r"C:/MyExports/exported/mp_rust.c2m"
UE5_CONTENT_PATH = "/Game/CoDMaps/mp_rust"
IMPORT_PROPS     = True
IMPORT_MATERIALS = True
IMPORT_LIGHTS    = True
```

### Step 3 — Run

In UE5, open the **Output Log** (`Window → Output Log`), switch the dropdown to **Python**, then type:

```python
exec(open(r"C:/YourProject/Content/Python/run_import.py").read())
```

Or call the API directly:

```python
import sys
sys.path.insert(0, r"C:/YourProject/Content/Python")

from C2MImporter import import_c2m

import_c2m(
    c2m_path=r"C:/MyExports/exported/mp_rust.c2m",
    content_path="/Game/CoDMaps/mp_rust",
    import_props=True,
    import_materials=True,
    import_lights=True,
)
```

---

## What Gets Imported

| C2M Data | UE5 Asset / Actor |
|----------|-------------------|
| `Objects[0]` — BSP world geometry | `StaticMesh` → `StaticMeshActor` at origin |
| `Objects[1:]` — XModel props | `StaticMesh` assets saved to `/XModels/` |
| `ModelInstances` — placed props | `StaticMeshActor` with transform applied |
| `Materials` | `Material` assets saved to `/Materials/` |
| Textures (`.tga`) | `Texture2D` assets saved to `/Textures/` |
| `Lights` — SUN | `DirectionalLight` actor |
| `Lights` — SPOT | `SpotLight` actor with cone angles |
| `Lights` — POINT | `PointLight` actor |

---

## Coordinate System

| | CoD | UE5 |
|--|-----|-----|
| Units | Inches | Centimetres |
| Forward | +X | +X |
| Right | −Y (left-handed) | +Y |
| Up | +Z | +Z |

Conversion formulas applied automatically:
```
ue5_x =  cod_x × 2.54
ue5_y = −cod_y × 2.54   ← Y negated for handedness
ue5_z =  cod_z × 2.54

quaternion_y = −quaternion_y
```

---

## Material Notes

| Texture Type | UE5 Connection |
|---|---|
| `colorMap`, `colorOpacity` | BaseColor (alpha → Opacity) |
| `colorGloss` | BaseColor (alpha → Roughness inverted) |
| `normalMap`, `bumpMap` | Normal (flip green channel = DirectX→OpenGL) |
| `specularMap`, `specGloss` | Specular + Roughness (1 − alpha) |
| `glossMap` | Roughness (1 − value) |
| `emissionMap` | EmissiveColor |
| `revealMap` | Opacity |

**Blend modes:**
- `sort_key == 0` → Masked
- `sort_key > 0` → Translucent
- `"glass"` in name/techset → Translucent
- `"emissive"` in techset → Unlit shading model

---

## Project Structure

```
Content/Python/
├── run_import.py               ← Edit paths here and run
└── C2MImporter/
    ├── __init__.py             ← Public API: import_c2m()
    ├── importer.py             ← Full import pipeline
    ├── mesh_builder.py         ← StaticMesh construction
    ├── material_builder.py     ← Material + texture import
    ├── light_builder.py        ← Light actor spawning
    ├── coords.py               ← CoD ↔ UE5 coordinate conversion
    └── reader/
        ├── __init__.py
        ├── c2m_reader.py       ← .c2m binary parser
        └── binary_reader.py    ← Low-level binary helpers
```

---

## Troubleshooting

**No textures appear on materials**
→ Check that `exported_images/<game_version>/` exists next to the `exported/` folder containing your `.c2m` file.

**Import fails with "Invalid C2M magic"**
→ The file was not exported correctly. Re-export from Greyhound.

**StaticMesh has no geometry / "zero verts" warning**
→ A surface had no valid face data. This is normal for very small or degenerate CoD brushes. Check the Output Log for which surfaces were skipped.

**Materials look incorrect**
→ Blend mode or normal map direction may need manual adjustment for some older game versions. The importer creates a best approximation.

**UE5 is slow / editor freezes during large map import**
→ This is expected — large maps (BO3, MW2019) can have 5,000–20,000 meshes. The progress dialog allows cancellation. Consider splitting into multiple sessions.

**"Python Editor Script Plugin not found"**
→ Make sure you're running Unreal Engine 5.1 or newer and have enabled the plugin under `Edit → Plugins → Python Editor Script Plugin`.

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Credits

- Original Blender C2M Importer by **SHEILAN**
- [Greyhound](https://github.com/dtzxporter/Greyhound) by **DTZxPorter** — C2M extraction tool
- [Cast](https://github.com/dtzxporter/Cast) — intermediate model format used by Greyhound

---

## License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

> **Note:** This tool is for personal, educational, and modding purposes only.
> Call of Duty assets are the property of Activision / Infinity Ward / Treyarch.
> Do not redistribute extracted game assets.
