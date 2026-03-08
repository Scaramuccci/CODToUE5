# CODToUE5

![GitHub release](https://img.shields.io/github/v/release/Scaramuccci/CODToUE5)
![GitHub downloads](https://img.shields.io/github/downloads/Scaramuccci/CODToUE5/total)
![License](https://img.shields.io/github/license/Scaramuccci/CODToUE5)
![Unreal Engine](https://img.shields.io/badge/Unreal%20Engine-5-blue)

CODToUE5 is a small hobby project that explores importing **Call of Duty C2M map data into Unreal Engine 5**.

The goal of this tool is to read C2M map files and reconstruct the level inside Unreal Engine by automatically generating meshes, materials and lighting using Python scripts.

This project is **ported and extended from**
[SHEILAN's Blender C2M Importer](https://github.com/sheilan102/C2M?tab=readme-ov-file).

Assets required for importing maps are usually extracted using
[Greyhound](https://github.com/Scobalula/Greyhound).

---

## Features

* Import **C2M map geometry** into Unreal Engine 5
* Automatically generate **UE5 meshes**
* Create **materials from map assets**
* Rebuild **lighting information**
* Python-based importer designed to run inside **Unreal Engine**
* Works with assets extracted using **Greyhound**

---

## VR Compatibility

Although this project mainly focuses on importing maps into **Unreal Engine 5**, the workflow can also be useful for **VR modding environments**.

Because the importer reconstructs map geometry inside Unreal, the resulting levels can be adapted for use in **Pavlov VR modding workflows**.

Typical workflow:

1. Extract assets using **Greyhound**
2. Import the map into **Unreal Engine 5** using this tool
3. Adjust and optimise the level for VR performance
4. Integrate the environment using **Pavlov's modding tools**

This makes the project useful for experimenting with:

* VR map reconstruction
* Pavlov VR modding
* learning how game asset pipelines work

---

## Requirements

Before using the importer you will need:

* **Unreal Engine 5**
* **Python scripting enabled in Unreal Engine**
* **Greyhound** to extract game assets
* A **C2M map file**

---

## Installation

1. Download the latest release from the **Releases** page.

2. Extract the package into your Unreal Engine project:

```
<ProjectDirectory>/Plugins/
```

3. Launch Unreal Engine.

4. Enable Python scripting if it is not already enabled.

5. Run the importer script.

---

## Usage

1. Extract map assets using **Greyhound**
2. Place the extracted assets and the **C2M map file** inside your project
3. Run the importer script inside Unreal Engine

The importer will then:

* Parse the C2M map data
* Generate meshes
* Create materials
* Rebuild lighting
* Assemble the level inside Unreal Engine

---

## Project Structure

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

| File                  | Purpose                       |
| --------------------- | ----------------------------- |
| `c2m_reader.py`       | Parses C2M map data           |
| `binary_reader.py`    | Handles binary file parsing   |
| `mesh_builder.py`     | Generates Unreal meshes       |
| `material_builder.py` | Builds Unreal materials       |
| `light_builder.py`    | Recreates map lighting        |
| `coords.py`           | Handles coordinate conversion |

---

## Releases

Pre-packaged versions of the importer are available in the **Releases** section.

Each release contains a ready-to-use version of the importer that can be dropped directly into an Unreal Engine project.

---

## Credits

This project builds on the work of several tools and contributors.

**SHEILAN**
Original Blender C2M Importer
https://github.com/sheilan102/C2M

**Scobalula**
Greyhound Asset Extraction Tool
https://github.com/Scobalula/Greyhound

---

## Disclaimer

This project is intended for **research, learning and experimentation**.

All game assets and intellectual property belong to their respective owners.

---

## License

See the **LICENSE** file for details.
