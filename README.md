# CODToUE5

Importer for **Call of Duty C2M maps into Unreal Engine 5**.

This tool reads C2M map data and reconstructs the level inside UE5 by generating meshes, materials, and lighting using the Unreal Python API.

The project is **ported and extended from**
[SHEILAN's Blender C2M Importer](https://github.com/sheilan102/C2M?tab=readme-ov-file).

Assets required for importing maps are typically extracted using
[Greyhound](https://github.com/Scobalula/Greyhound).

---

## Features

* Import **C2M map geometry** into Unreal Engine 5
* Automatically generate **UE5 meshes and materials**
* Build **map lighting and scene structure**
* Python-based importer designed to run inside **Unreal Engine**
* Works with assets extracted using **Greyhound**

---

## Requirements

Before using the importer you will need:

* **Unreal Engine 5**
* **Python scripting enabled in UE**
* Map assets extracted using **Greyhound**
* The C2M map file you want to import

---

## Installation

1. Download the latest release from the **Releases** page.

2. Extract the contents into your Unreal project:

```
<ProjectFolder>/Plugins/
```

3. Launch Unreal Engine.

4. Enable the plugin if required and run the importer script.

---

## Usage

1. Extract the map assets using **Greyhound**.
2. Place the extracted files and C2M map into your project directory.
3. Run the importer Python script inside Unreal Engine.
4. The importer will:

* Read the C2M data
* Generate meshes
* Create materials
* Build lighting
* Assemble the level in UE5

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

Key components:

| File                  | Purpose                               |
| --------------------- | ------------------------------------- |
| `c2m_reader.py`       | Reads and parses C2M map data         |
| `mesh_builder.py`     | Builds UE meshes from parsed geometry |
| `material_builder.py` | Generates Unreal materials            |
| `light_builder.py`    | Reconstructs lighting                 |
| `coords.py`           | Handles coordinate system conversion  |

---

## Releases

Compiled packages of the importer are available under:

```
Releases → Download ZIP
```

Each release contains the importer ready to be added to an Unreal Engine project.

---

## Credits

This project builds upon the work of the following tools and contributors:

* **SHEILAN** – Original Blender C2M Importer
  https://github.com/sheilan102/C2M

* **Scobalula** – Greyhound asset extraction tool
  https://github.com/Scobalula/Greyhound

---

## Disclaimer

This project is intended for **research and educational purposes**.
All game assets belong to their respective owners.

---

## License

See the `LICENSE` file for details.
