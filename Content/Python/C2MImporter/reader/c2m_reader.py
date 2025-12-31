"""
c2m_reader.py

Parses the binary .c2m format produced by Greyhound / CoDMap extraction tools.

File layout (roughly):
  - 3 magic bytes: 'C2M' (0x43 0x32 0x4D)
  - 1 byte file format version  (we read but don't use this)
  - 1 byte CoD game version index  (maps to a string via COD_VERSIONS)
  - map name string
  - skybox name string
  - uint: object count, then that many CoDMesh blocks
  - uint: material count, then that many CoDMaterial blocks
  - uint: model instance count, then that many CoDModelInstance blocks
  - uint: light count, then that many CoDLight blocks

All strings are C2M format (see binary_reader.py).
All coordinates are in inches, CoD left-handed space (X=forward, Y=left, Z=up).
The caller is responsible for converting to the target coordinate system.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import IO, Dict, List, Optional, Tuple
from .binary_reader import (
    read_byte, read_bool, read_uint, read_float, read_string, read_bytes
)


# ---------------------------------------------------------------------------
# Game version lookup table
# ---------------------------------------------------------------------------
COD_VERSIONS: Dict[int, str] = {
    0:  "modern_warfare",
    1:  "world_at_war",
    2:  "modern_warfare_2",
    3:  "black_ops",
    4:  "modern_warfare_3",
    5:  "black_ops_2",
    6:  "ghosts",
    7:  "advanced_warfare",
    8:  "black_ops_3",
    9:  "modern_warfare_rm",
    10: "infinite_warfare",
    11: "world_war_2",
    12: "black_ops_4",
    13: "modern_warfare_4",
    14: "modern_warfare_2_rm",
    15: "black_ops_5",
}

COD_LIGHT_TYPES: Dict[int, str] = {
    1: "SUN",
    2: "SPOT",
    3: "SPOT",
    4: "SPOT",
    5: "POINT",
}

COD_MATERIAL_SETTINGS: Dict[int, str] = {
    0: "colorTint",
    1: "detailScale",
    2: "detailScale1",
    3: "detailScale2",
    4: "detailScale3",
    5: "specColorTint",
    6: "rowCount",
    7: "columnCount",
    8: "imageTime",
}

C2M_MAGIC = (67, 50, 77)  # "C2M"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CoDTexture:
    """A single texture reference within a CoDMaterial."""
    name: str
    tex_type: str

    @classmethod
    def read(cls, file: IO) -> "CoDTexture":
        return cls(name=read_string(file), tex_type=read_string(file))


@dataclass
class CoDMaterial:
    """
    A CoD material definition including its techset, sort order,
    texture list, and material settings.

    Attributes
    ----------
    name     : Material asset name.
    tech_set : Shader/technique set name (e.g. "lit", "reveal", "glass").
    sort_key : 0 = opaque, >0 = transparent (higher = drawn later).
    textures : Ordered list of texture references.
    settings : Key-value material settings (colorTint, detailScale, etc.)
    """
    name: str
    tech_set: str
    sort_key: int
    textures: List[CoDTexture] = field(default_factory=list)
    settings: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def read(cls, file: IO) -> "CoDMaterial":
        name = read_string(file)
        tech_set = read_string(file)
        sort_key = read_byte(file)

        textures = []
        for _ in range(read_byte(file)):
            textures.append(CoDTexture.read(file))

        settings = {}
        for _ in range(read_byte(file)):
            key = COD_MATERIAL_SETTINGS.get(read_byte(file), "unknown")
            settings[key] = read_string(file)

        return cls(name=name, tech_set=tech_set, sort_key=sort_key,
                   textures=textures, settings=settings)

    @property
    def is_transparent(self) -> bool:
        return self.sort_key > 0

    @property
    def is_glass(self) -> bool:
        return "glass" in self.name or "glass" in self.tech_set

    @property
    def is_emissive(self) -> bool:
        return "emissive" in self.tech_set and "lit" not in self.tech_set

    @property
    def is_reveal(self) -> bool:
        return "reveal" in self.tech_set or "_mask" in self.tech_set


@dataclass
class CoDSurface:
    """
    One draw call within a CoDMesh.

    Each surface references a slice of the parent mesh's vertex pool via
    triangle face indices and uses one or more materials. When there are
    multiple materials, vertex colours (R/G/B) act as blend weights for
    layers 1-3.
    """
    name: str
    materials: List[str] = field(default_factory=list)
    faces: List[Tuple[int, int, int]] = field(default_factory=list)

    @classmethod
    def read(cls, file: IO) -> "CoDSurface":
        name = read_string(file)
        materials = [read_string(file) for _ in range(read_uint(file))]
        faces = []
        for _ in range(read_uint(file)):
            i0, i1, i2 = read_uint(file), read_uint(file), read_uint(file)
            faces.append((i0, i1, i2))
        return cls(name=name, materials=materials, faces=faces)


@dataclass
class CoDMesh:
    """
    A mesh object with shared vertex data and one or more surfaces.

    Vertex data is stored per-vertex (not per-loop), so positions, normals,
    UVs, and colours can all be shared across multiple triangles.

    objects[0] is always the BSP world geometry; everything after that is a
    unique XModel asset.

    uvs[i] is a list of (u, v) pairs — one per UV channel for that vertex.
    colors[i] is (r, g, b, a) as floats in [0, 1].
    """
    name: str
    is_xmodel: bool
    vertices: List[Tuple[float, float, float]] = field(default_factory=list)
    normals: List[Tuple[float, float, float]] = field(default_factory=list)
    uvs: List[List[Tuple[float, float]]] = field(default_factory=list)
    colors: List[Tuple[float, float, float, float]] = field(default_factory=list)
    surfaces: List[CoDSurface] = field(default_factory=list)

    @classmethod
    def read(cls, file: IO) -> "CoDMesh":
        name = read_string(file)
        is_xmodel = read_bool(file)

        vertices = [(read_float(file), read_float(file), read_float(file))
                    for _ in range(read_uint(file))]

        normals = [(read_float(file), read_float(file), read_float(file))
                   for _ in range(read_uint(file))]

        uvs = []
        for _ in range(read_uint(file)):
            uv_set_count = read_uint(file)
            uvs.append([(read_float(file), read_float(file))
                        for _ in range(uv_set_count)])

        colors = []
        for _ in range(read_uint(file)):
            colors.append((
                read_byte(file) / 255.0,
                read_byte(file) / 255.0,
                read_byte(file) / 255.0,
                read_byte(file) / 255.0,
            ))

        surfaces = [CoDSurface.read(file) for _ in range(read_uint(file))]

        return cls(name=name, is_xmodel=is_xmodel, vertices=vertices,
                   normals=normals, uvs=uvs, colors=colors, surfaces=surfaces)


@dataclass
class CoDModelInstance:
    """
    A placed XModel in the world — basically a transform referencing a named asset.

    rotation_mode == 0 means the rotation is stored as a quaternion (XYZW).
    rotation_mode == 1 means it's Euler degrees; rotation_euler has the same
    values converted to radians for convenience.
    """
    name: str
    position: Tuple[float, float, float]
    rotation_mode: int
    rotation: tuple
    rotation_euler: Optional[Tuple[float, float, float]]
    scale: Tuple[float, float, float]

    @classmethod
    def read(cls, file: IO) -> "CoDModelInstance":
        name = read_string(file)
        position = (read_float(file), read_float(file), read_float(file))
        rotation_mode = read_byte(file)

        if rotation_mode == 0:
            # Quaternion stored as XYZW
            qx = read_float(file)
            qy = read_float(file)
            qz = read_float(file)
            qw = read_float(file)
            rotation = (qx, qy, qz, qw)
            rotation_euler = None
        else:
            rx, ry, rz = read_float(file), read_float(file), read_float(file)
            rotation = (rx, ry, rz)
            rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz))

        scale = (read_float(file), read_float(file), read_float(file))
        return cls(name=name, position=position, rotation_mode=rotation_mode,
                   rotation=rotation, rotation_euler=rotation_euler, scale=scale)

    @property
    def is_at_origin(self) -> bool:
        return self.position == (0.0, 0.0, 0.0)


@dataclass
class CoDLight:
    """
    A dynamic light from the CoD map.

    cos_half_fov_outer / cos_half_fov_inner store the cone angles as cosines
    of the half-angle, so to get degrees you need acos() * 2.
    d_attenuation overrides the radius for distance falloff when non-zero.
    """
    light_type: str
    origin: Tuple[float, float, float]
    direction: Tuple[float, float, float]
    angles: Tuple[float, float, float]
    color: Tuple[float, float, float, float]
    radius: float
    cos_half_fov_outer: float
    cos_half_fov_inner: float
    d_attenuation: float

    @classmethod
    def read(cls, file: IO) -> "CoDLight":
        light_type = COD_LIGHT_TYPES.get(read_byte(file), "POINT")
        origin = (read_float(file), read_float(file), read_float(file))
        direction = (read_float(file), read_float(file), read_float(file))
        angles = (read_float(file), read_float(file), read_float(file))
        color = (read_float(file), read_float(file), read_float(file), read_float(file))
        radius = read_float(file)
        cos_half_fov_outer = read_float(file)
        cos_half_fov_inner = read_float(file)
        d_attenuation = read_float(file)
        return cls(light_type=light_type, origin=origin, direction=direction,
                   angles=angles, color=color, radius=radius,
                   cos_half_fov_outer=cos_half_fov_outer,
                   cos_half_fov_inner=cos_half_fov_inner,
                   d_attenuation=d_attenuation)


@dataclass
class CoDMap:
    """
    Everything parsed out of a .c2m file.

    objects[0] is always the BSP world geometry. objects[1:] are the unique
    XModel assets referenced by instances. The materials dict is keyed by
    material name. instances lists every placed prop transform.
    """
    name: str
    skybox: str
    version: str
    objects: List[CoDMesh] = field(default_factory=list)
    materials: Dict[str, CoDMaterial] = field(default_factory=dict)
    instances: List[CoDModelInstance] = field(default_factory=list)
    lights: List[CoDLight] = field(default_factory=list)

    @classmethod
    def from_file(cls, path: str) -> "CoDMap":
        """Parse a .c2m file from a filesystem path."""
        with open(path, "rb") as f:
            return cls.read(f)

    @classmethod
    def read(cls, file: IO) -> "CoDMap":
        """Parse a .c2m file from an open binary stream."""
        magic = read_bytes(file, 3)
        if tuple(magic) != C2M_MAGIC:
            raise ValueError(
                f"Invalid C2M magic: {magic}. Expected {list(C2M_MAGIC)} ('C2M'). "
                "Make sure the file was exported by Greyhound/CoDMap."
            )

        _file_ver = read_byte(file)
        game_index = read_byte(file)
        version = COD_VERSIONS.get(game_index, f"unknown_{game_index}")
        name = read_string(file)
        skybox = read_string(file)

        objects = [CoDMesh.read(file) for _ in range(read_uint(file))]

        materials = {}
        for _ in range(read_uint(file)):
            mat = CoDMaterial.read(file)
            materials[mat.name] = mat

        instances = [CoDModelInstance.read(file) for _ in range(read_uint(file))]
        lights = [CoDLight.read(file) for _ in range(read_uint(file))]

        return cls(name=name, skybox=skybox, version=version,
                   objects=objects, materials=materials,
                   instances=instances, lights=lights)

    @property
    def map_geometry(self) -> Optional[CoDMesh]:
        """The BSP world geometry mesh (always objects[0])."""
        return self.objects[0] if self.objects else None

    @property
    def xmodels(self) -> List[CoDMesh]:
        """All prop XModel meshes (objects[1:])."""
        return self.objects[1:]

    def summary(self) -> str:
        return (
            f"CoDMap '{self.name}' [{self.version}]\n"
            f"  Objects   : {len(self.objects)} ({len(self.xmodels)} XModels)\n"
            f"  Materials : {len(self.materials)}\n"
            f"  Instances : {len(self.instances)}\n"
            f"  Lights    : {len(self.lights)}\n"
            f"  Skybox    : {self.skybox or '(none)'}"
        )
