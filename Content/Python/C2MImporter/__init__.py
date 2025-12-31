"""
C2MImporter — UE5 Python plugin for importing .c2m map files exported by
Greyhound / CoDMap tools.

Quick start:

    from C2MImporter import import_c2m

    import_c2m(
        c2m_path=r"C:/Exports/exported/mp_rust.c2m",
        content_path="/Game/CoDMaps/mp_rust",
        import_props=True,
        import_materials=True,
        import_lights=True,
    )

Module overview:
  importer.py         full import pipeline
  mesh_builder.py     StaticMesh construction
  material_builder.py Material + texture import
  light_builder.py    light actor spawning
  coords.py           CoD ↔ UE5 coordinate conversion
  reader/             binary .c2m parser
"""

__version__ = "1.0.0"
__author__ = "C2M UE5 Importer contributors"

from .importer import import_c2m
from .reader import CoDMap

__all__ = ["import_c2m", "CoDMap", "__version__"]
