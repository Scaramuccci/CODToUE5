# CODToUE5

![GitHub release](https://img.shields.io/github/v/release/Scaramuccci/CODToUE5)
![GitHub downloads](https://img.shields.io/github/downloads/Scaramuccci/CODToUE5/total)
![License](https://img.shields.io/github/license/Scaramuccci/CODToUE5)
![Unreal Engine](https://img.shields.io/badge/Unreal%20Engine-5-blue)

Importer for **Call of Duty C2M maps into Unreal Engine 5**.

This tool reads **C2M map data** and reconstructs the level inside Unreal Engine by generating meshes, materials, and lighting using the **Unreal Engine Python API**.

The project is **ported and extended from**
[SHEILAN's Blender C2M Importer](https://github.com/sheilan102/C2M?tab=readme-ov-file).

Assets required for importing maps are typically extracted using
[Greyhound](https://github.com/Scobalula/Greyhound).

---

# Features

* Import **C2M map geometry** into Unreal Engine 5
* Automatically generate **UE5 meshes**
* Create **materials from map assets**
* Rebuild **lighting information**
* Python-based importer designed to run inside **Unreal Engine**
* Compatible with assets extracted using **Greyhound**

---

# Requirements

Before using the importer you will need:

* **Unreal Engine 5**
* **Python scripting enabled in Unreal Engine**
* **Greyhound** to extract game assets
* A **C2M map file**

---

# Installation

1. Download the latest release from the **Releases** page.

2. Extract the release package into your Unreal Engine project:

```
<ProjectDirectory>/Plugins/
```

3. Launch Unreal Engine.

4. Enable Python scripting if it is not already enabled.

5. Run the importer script.

---

# Usage

1. Extract map assets using **Greyhound**.
2. Place the extracted assets and the **C2M map file** inside your project directory.
3. Run the importer Python script from Unreal Engine.
4. The importer will automatically:

* Parse the C2M map data
* Generate meshes
* Create materials
* Build lighting
* Assemble the level in UE5

---

# Project Structure

```
Content/
 └── Python/
     └── C2MImporter/
         ├── importer.py
         ├── mesh_builder.py
         ├── material_builder.py
         ├── light_builder.py
         ├── coords.py
         └── reader/
             ├── c2m_reader.py
             └── binary_reader.py
```

### Key Components

| File                  | Purpose                              |
| --------------------- | ------------------------------------ |
| `c2m_reader.py`       | Parses C2M map data                  |
| `binary_reader.py`    | Handles binary file parsing          |
| `mesh_builder.py`     | Generates Unreal meshes              |
| `material_builder.py` | Builds Unreal materials              |
| `light_builder.py`    | Recreates map lighting               |
| `coords.py`           | Handles coordinate system conversion |

---

# Releases

Compiled importer packages are available under:

```
Releases → Download ZIP
```

Each release contains a ready-to-use importer package.

---

# Credits

This project builds upon the work of the following tools and contributors:

**SHEILAN**
Original Blender C2M Importer
https://github.com/sheilan102/C2M

**Scobalula**
Greyhound Asset Extraction Tool
https://github.com/Scobalula/Greyhound

---

# Disclaimer

This project is intended for **research and educational purposes**.

All game assets and intellectual property belong to their respective owners.

---

# License

See the **LICENSE** file for details.
