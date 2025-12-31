"""
importer.py

The main import pipeline — glues everything else together.

Steps, in order:
  1. Parse the .c2m binary
  2. Import and configure all textures
  3. Create UE5 Material assets
  4. Build UE5 StaticMesh assets (BSP geometry + XModel props)
  5. Spawn static mesh actors into the current level
  6. Spawn lights

See README.md for usage examples.
"""

from __future__ import annotations
import os
import unreal
from typing import Dict, Optional

from .reader.c2m_reader import CoDMap
from .mesh_builder import build_static_mesh
from .material_builder import create_material
from .light_builder import spawn_light
from .coords import to_ue5_location, to_ue5_quaternion, inch_to_cm


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def import_c2m(
    c2m_path: str,
    content_path: str = "/Game/CoDMaps",
    import_props: bool = True,
    import_materials: bool = True,
    import_lights: bool = True,
) -> None:
    """
    Parse a .c2m file and populate the current UE5 level with its contents.

    c2m_path         -- absolute path to the .c2m file on disk
    content_path     -- Content Browser destination; a sub-folder named after
                        the map will be created inside this path
    import_props     -- whether to import and place XModel prop instances
    import_materials -- whether to create Material assets and assign them
    import_lights    -- whether to spawn light actors

    Raises FileNotFoundError if the file doesn't exist, or ValueError if
    the magic header is wrong (i.e. not a valid .c2m file).

    Example usage from the UE5 Python console:

        from C2MImporter import import_c2m
        import_c2m(
            c2m_path=r"C:/Exports/exported/mp_rust.c2m",
            content_path="/Game/CoDMaps/mp_rust",
        )
    """
    if not os.path.isfile(c2m_path):
        raise FileNotFoundError(f"C2M file not found: {c2m_path}")

    unreal.log(f"[C2M] ── Starting import: {c2m_path}")

    # ── 1. Parse .c2m ─────────────────────────────────────────────────────
    cod_map = CoDMap.from_file(c2m_path)
    unreal.log(f"[C2M]\n{cod_map.summary()}")

    # Try to find the exported_images directory that Greyhound puts next to
    # the 'exported' folder. If the .c2m isn't in an 'exported' subdirectory
    # we just look in a sibling folder from wherever the file lives.
    c2m_dir = os.path.dirname(c2m_path)
    if "exported" in c2m_dir:
        root_dir = c2m_dir[: c2m_dir.find("exported")]
    else:
        root_dir = c2m_dir
    images_path = os.path.join(root_dir, "exported_images", cod_map.version)

    if not os.path.isdir(images_path):
        unreal.log_warning(
            f"[C2M] Texture directory not found: {images_path}\n"
            "       Materials will be created without textures."
        )

    map_pkg = f"{content_path.rstrip('/')}/{cod_map.name}"

    # ── 2. Materials ──────────────────────────────────────────────────────
    ue5_materials: Dict[str, unreal.Material] = {}
    if import_materials and cod_map.materials:
        mats = list(cod_map.materials.items())
        with unreal.ScopedSlowTask(len(mats), "C2M: Importing materials") as task:
            task.make_dialog(True)
            for mat_name, cod_mat in mats:
                if task.should_cancel():
                    unreal.log_warning("[C2M] Import cancelled by user.")
                    return
                task.enter_progress_frame(1, mat_name)
                try:
                    mat = create_material(cod_mat, images_path, map_pkg)
                    if mat:
                        ue5_materials[mat_name] = mat
                except Exception as exc:
                    unreal.log_warning(f"[C2M] Material '{mat_name}' failed: {exc}")

    # ── 3. Map geometry (Objects[0]) ──────────────────────────────────────
    map_geo_mesh: Optional[unreal.StaticMesh] = None
    if cod_map.map_geometry:
        unreal.log("[C2M] Building map geometry...")
        try:
            map_geo_mesh = build_static_mesh(
                cod_map.map_geometry,
                f"{cod_map.name}_geo",
                f"{map_pkg}/Meshes",
                cod_map.materials,
            )
        except Exception as exc:
            unreal.log_error(f"[C2M] Map geometry failed: {exc}")

    # Spawn map geo actor
    if map_geo_mesh:
        _spawn_static_mesh_actor(
            mesh=map_geo_mesh,
            label=f"{cod_map.name}_Geometry",
            position=unreal.Vector(0, 0, 0),
            rotation=unreal.Rotator(0, 0, 0),
            scale=unreal.Vector(1, 1, 1),
            ue5_materials=ue5_materials if import_materials else {},
            cod_mesh=cod_map.map_geometry,
        )

    # ── 4. XModel assets (Objects[1:]) ────────────────────────────────────
    xmodel_meshes: Dict[str, unreal.StaticMesh] = {}
    if import_props and cod_map.xmodels:
        xmodels = cod_map.xmodels
        with unreal.ScopedSlowTask(len(xmodels), "C2M: Building XModel assets") as task:
            task.make_dialog(True)
            for xmodel in xmodels:
                if task.should_cancel():
                    return
                task.enter_progress_frame(1, xmodel.name)
                try:
                    mesh = build_static_mesh(
                        xmodel,
                        xmodel.name,
                        f"{map_pkg}/XModels",
                        cod_map.materials,
                    )
                    if mesh:
                        xmodel_meshes[xmodel.name] = mesh
                except Exception as exc:
                    unreal.log_warning(f"[C2M] XModel '{xmodel.name}' failed: {exc}")

    # ── 5. Model instances ────────────────────────────────────────────────
    if import_props and cod_map.instances:
        valid = [i for i in cod_map.instances if not i.is_at_origin]
        with unreal.ScopedSlowTask(len(valid), "C2M: Spawning instances") as task:
            task.make_dialog(True)
            for idx, inst in enumerate(valid):
                if task.should_cancel():
                    return
                task.enter_progress_frame(1, inst.name)

                mesh = xmodel_meshes.get(inst.name)
                if mesh is None:
                    continue

                px, py, pz = to_ue5_location(*inst.position)
                pos = unreal.Vector(px, py, pz)

                if inst.rotation_mode == 0:
                    rot = unreal.Quat(*to_ue5_quaternion(*inst.rotation)).rotator()
                else:
                    rx, ry, rz = inst.rotation
                    rot = unreal.Rotator(rx, -ry, rz)

                sx, sy, sz = inst.scale
                scale = unreal.Vector(sx, sy, sz)

                cod_mesh_obj = next(
                    (o for o in cod_map.xmodels if o.name == inst.name), None
                )
                _spawn_static_mesh_actor(
                    mesh=mesh,
                    label=f"{inst.name}_{idx}",
                    position=pos,
                    rotation=rot,
                    scale=scale,
                    ue5_materials=ue5_materials if import_materials else {},
                    cod_mesh=cod_mesh_obj,
                )

    # ── 6. Lights ─────────────────────────────────────────────────────────
    if import_lights and cod_map.lights:
        with unreal.ScopedSlowTask(len(cod_map.lights), "C2M: Spawning lights") as task:
            task.make_dialog(True)
            for light in cod_map.lights:
                if task.should_cancel():
                    return
                task.enter_progress_frame(1, light.light_type)
                try:
                    spawn_light(light)
                except Exception as exc:
                    unreal.log_warning(f"[C2M] Light spawn failed: {exc}")

    unreal.log(f"[C2M] ── Import complete: {cod_map.name}")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _spawn_static_mesh_actor(
    mesh: unreal.StaticMesh,
    label: str,
    position: unreal.Vector,
    rotation: unreal.Rotator,
    scale: unreal.Vector,
    ue5_materials: Dict[str, unreal.Material],
    cod_mesh,
) -> Optional[unreal.Actor]:
    """Spawn a StaticMeshActor and assign materials per surface slot."""
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, position, rotation
    )
    if actor is None:
        unreal.log_warning(f"[C2M] Failed to spawn actor: {label}")
        return None

    actor.set_actor_label(label)
    actor.set_actor_scale3d(scale)

    smc: unreal.StaticMeshComponent = actor.get_component_by_class(
        unreal.StaticMeshComponent
    )
    if smc:
        smc.set_static_mesh(mesh)

        if cod_mesh and ue5_materials:
            # Rebuild the same slot ordering that build_static_mesh used — surfaces
            # that share a material map to the same slot, so we can't just enumerate
            # surfaces directly and use the surface index as the slot number.
            seen: Dict[str, int] = {}
            slot_names: list = []
            for surf in cod_mesh.surfaces:
                if surf.materials:
                    primary = surf.materials[0]
                    if primary not in seen:
                        seen[primary] = len(slot_names)
                        slot_names.append(primary)
            for slot_idx, mat_name in enumerate(slot_names):
                mat = ue5_materials.get(mat_name)
                if mat:
                    smc.set_material(slot_idx, mat)

    return actor
