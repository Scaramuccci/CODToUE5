"""
run_import.py
-------------
Configure the paths below and run this script from the UE5 Python console
to import a C2M map.

How to run
----------
1. Open Unreal Engine 5
2. Open the Output Log  (Window → Output Log)
3. Change the input mode dropdown from "Cmd" to "Python"
4. Type:  exec(open(r"C:/YourProject/Content/Python/run_import.py").read())

Or use an Editor Utility Widget with an "Execute Python Script" node
pointing at this file.
"""

# ── Configure these paths ─────────────────────────────────────────────────

# Full path to the .c2m file exported by Greyhound
C2M_FILE_PATH = r"C:/Exports/exported/mp_rust.c2m"

# Content Browser destination (a sub-folder per map will be created here)
UE5_CONTENT_PATH = "/Game/CoDMaps/mp_rust"

# What to import
IMPORT_PROPS     = True   # XModel prop instances
IMPORT_MATERIALS = True   # Textures and materials
IMPORT_LIGHTS    = True   # Dynamic lights

# ─────────────────────────────────────────────────────────────────────────

import sys, os

_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from C2MImporter import import_c2m

import_c2m(
    c2m_path=C2M_FILE_PATH,
    content_path=UE5_CONTENT_PATH,
    import_props=IMPORT_PROPS,
    import_materials=IMPORT_MATERIALS,
    import_lights=IMPORT_LIGHTS,
)
