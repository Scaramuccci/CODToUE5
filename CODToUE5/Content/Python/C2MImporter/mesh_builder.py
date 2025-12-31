"""
mesh_builder.py

Converts parsed CoDMesh data into UE5 StaticMesh assets via the Unreal
Python scripting API.

A few things worth knowing before reading this code:

Transparent surfaces — CoD keeps transparent geometry at the same world
position as the opaque surface underneath. To prevent Z-fighting we nudge
verts a tiny amount along their normal, proportional to sort_key.

UVs — V is flipped (1 - v) because CoD's UV origin is bottom-left while
UE5 expects top-left. UV channel 0 is the primary texture; channel 1+
are blend/decal layers used when a surface references multiple materials.

Winding order — CoD and UE5 both use counter-clockwise front faces, but
negating the Y axis during coordinate conversion flips the apparent winding,
so we reverse every triangle (i0, i1, i2) → (i0, i2, i1) to compensate.
"""

from __future__ import annotations
import unreal
from typing import Dict, Optional

from .reader.c2m_reader import CoDMesh, CoDMaterial
from .coords import to_ue5_location, to_ue5_normal, inch_to_cm


def build_static_mesh(
    cod_mesh: CoDMesh,
    asset_name: str,
    package_path: str,
    map_materials: Dict[str, CoDMaterial],
) -> Optional[unreal.StaticMesh]:
    """
    Build and save a UE5 StaticMesh from a CoDMesh.

    Returns the created StaticMesh asset, or None if something went wrong.
    If the asset already exists at the target path it's returned as-is without
    being rebuilt — so re-running the importer on the same map is safe.
    """
    # Sanitise asset name for UE5 (no colons, slashes, spaces)
    safe_name = _sanitise_name(asset_name)
    full_path = f"{package_path}/{safe_name}"

    # Return existing asset rather than rebuilding
    if unreal.EditorAssetLibrary.does_asset_exist(full_path):
        return unreal.EditorAssetLibrary.load_asset(full_path)

    # ── Collect geometry ──────────────────────────────────────────────────
    positions = []
    normals = []
    uv_channels: list[list] = []   # uv_channels[ch][vert_idx]
    colors = []
    triangles = []          # (i0, i1, i2, mat_slot_idx)
    mat_slot_map: dict[str, int] = {}
    mat_slot_names: list[str] = []

    for surface in cod_mesh.surfaces:
        if not surface.materials:
            continue

        primary_mat_name = surface.materials[0]
        sort_key = 0
        if primary_mat_name in map_materials:
            sort_key = map_materials[primary_mat_name].sort_key

        # Assign material slot
        if primary_mat_name not in mat_slot_map:
            mat_slot_map[primary_mat_name] = len(mat_slot_names)
            mat_slot_names.append(primary_mat_name)
        slot_idx = mat_slot_map[primary_mat_name]

        for face in surface.faces:
            tri_indices = []
            for cod_idx in face:
                # Fetch raw vertex data with safe fallbacks
                cx, cy, cz = cod_mesh.vertices[cod_idx]
                nx, ny, nz = (cod_mesh.normals[cod_idx]
                              if cod_idx < len(cod_mesh.normals) else (0.0, 0.0, 1.0))
                uv_sets = (cod_mesh.uvs[cod_idx]
                           if cod_idx < len(cod_mesh.uvs) else [(0.0, 0.0)])
                vc = (cod_mesh.colors[cod_idx]
                      if cod_idx < len(cod_mesh.colors) else (1.0, 1.0, 1.0, 1.0))

                # Nudge transparent verts along their normal to avoid Z-fighting
                # with the opaque geometry sitting at the same world position.
                if sort_key > 0:
                    offset = sort_key * 0.001
                    cx += nx * offset
                    cy += ny * offset
                    cz += nz * offset

                # Convert to UE5 space
                ux, uy, uz = to_ue5_location(cx, cy, cz)
                unx, uny, unz = to_ue5_normal(nx, ny, nz)

                local_idx = len(positions)
                positions.append(unreal.Vector(ux, uy, uz))
                normals.append(unreal.Vector(unx, uny, unz))
                colors.append(unreal.LinearColor(vc[0], vc[1], vc[2], vc[3]))

                # UV channels — flip V for UE5
                for ch, (u, v) in enumerate(uv_sets):
                    while len(uv_channels) <= ch:
                        uv_channels.append([])
                    uv_channels[ch].append(unreal.Vector2D(u, 1.0 - v))

                # Pad missing UV channels
                for ch in range(len(uv_sets), len(uv_channels)):
                    uv_channels[ch].append(unreal.Vector2D(0.0, 0.0))

                tri_indices.append(local_idx)

            # Reverse winding for Y-axis flip
            i0, i1, i2 = tri_indices
            triangles.append((i0, i2, i1, slot_idx))

    if not positions:
        unreal.log_warning(f"[C2M] Mesh '{asset_name}' produced no geometry — skipped.")
        return None

    # Pad all UV channels to full vertex count
    num_verts = len(positions)
    for ch in uv_channels:
        while len(ch) < num_verts:
            ch.append(unreal.Vector2D(0.0, 0.0))

    # ── Build MeshDescription ─────────────────────────────────────────────
    mesh_desc = unreal.MeshDescription()
    sma = unreal.StaticMeshAttributes(mesh_desc)
    sma.register()

    pos_attr = sma.get_vertex_positions()
    norm_attr = sma.get_vertex_instance_normals()
    uv_attr_0 = sma.get_vertex_instance_u_vs(0)
    uv_attr_1 = sma.get_vertex_instance_u_vs(1) if len(uv_channels) > 1 else None
    col_attr = sma.get_vertex_instance_colors()

    # Create polygon groups (one per material slot)
    poly_groups = [mesh_desc.create_polygon_group() for _ in mat_slot_names]

    # Create vertices and vertex instances
    v_ids = []
    vi_ids = []
    for i in range(num_verts):
        v_id = mesh_desc.create_vertex()
        pos_attr.set(v_id, [], positions[i])
        v_ids.append(v_id)

        vi_id = mesh_desc.create_vertex_instance(v_id)
        norm_attr.set(vi_id, [], normals[i])
        uv_attr_0.set(vi_id, [], uv_channels[0][i] if uv_channels else unreal.Vector2D(0, 0))
        if uv_attr_1:
            uv_attr_1.set(vi_id, [], uv_channels[1][i])
        col_attr.set(vi_id, [], colors[i])
        vi_ids.append(vi_id)

    # Create triangles
    for i0, i1, i2, slot in triangles:
        mesh_desc.create_polygon(poly_groups[slot], [vi_ids[i0], vi_ids[i1], vi_ids[i2]])

    # ── Create and save StaticMesh asset ─────────────────────────────────
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

    static_mesh: unreal.StaticMesh = asset_tools.create_asset(
        safe_name, package_path, unreal.StaticMesh, None
    )
    if static_mesh is None:
        unreal.log_error(f"[C2M] Failed to create StaticMesh asset at: {full_path}")
        return None

    with unreal.ScopedEditorTransaction(f"C2M Build Mesh: {safe_name}"):
        static_mesh.modify()

        build_settings = unreal.MeshBuildSettings()
        build_settings.recompute_normals = False
        build_settings.recompute_tangents = True
        build_settings.remove_degenerates = True
        build_settings.use_mikk_t_space = True

        lod = unreal.StaticMeshSourceModel()
        lod.build_settings = build_settings
        static_mesh.set_editor_property("source_models", [lod])

        static_mesh.commit_mesh_description(0, mesh_desc)

        # Assign material slot names
        slots = []
        for slot_name in mat_slot_names:
            sm = unreal.StaticMaterial()
            sm.material_slot_name = slot_name
            slots.append(sm)
        static_mesh.set_editor_property("static_materials", slots)

        static_mesh.set_editor_property("light_map_resolution", 64)
        static_mesh.build()

    unreal.EditorAssetLibrary.save_asset(full_path)
    unreal.log(f"[C2M] ✓ Mesh: {full_path}")
    return static_mesh


def _sanitise_name(name: str) -> str:
    """Replace characters that are invalid in UE5 asset names."""
    for ch in ("::", ":", "/", "\\", " ", ".", "#"):
        name = name.replace(ch, "_")
    return name.strip("_") or "unnamed"
