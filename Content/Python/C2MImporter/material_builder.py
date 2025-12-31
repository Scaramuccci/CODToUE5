"""
material_builder.py

Creates UE5 Material assets from parsed CoDMaterial data.

Texture type → UE5 material input mapping:
  colorMap / colorOpacity  → BaseColor  (alpha → Opacity)
  colorGloss               → BaseColor  (alpha → 1-Roughness)
  normalMap / bumpMap      → Normal     (flip_green_channel on the texture)
  specularMap / specGloss  → Specular + Roughness (1 - alpha)
  glossMap                 → Roughness (1 - value)
  emissionMap / emissiveMap → EmissiveColor
  revealMap                → Opacity

Blend modes:
  sort_key == 0, no special keywords → Masked (alpha clip at 0.5)
  sort_key > 0                       → Translucent
  "glass" in name/techset            → Translucent + two-sided
  is_emissive (techset)              → Unlit shading model

Normal maps in CoD use DirectX convention (green channel = down). UE5 expects
OpenGL convention (green = up). We set flip_green_channel = True on every
imported normal texture to handle this.

If a material has a colorTint setting, those RGB values get multiplied over
the base colour output via a Multiply node.
"""

from __future__ import annotations
import os
import unreal
from typing import Dict, Optional

from .reader.c2m_reader import CoDMaterial


# Texture types that should be imported as sRGB
_SRGB_TEX_TYPES = {
    "colorMap", "colorOpacity", "colorGloss",
    "emissionMap", "emissiveMap", "emissionMap0",
}

# Texture types that are normal maps (need flip green + NormalMap compression)
_NORMAL_TEX_TYPES = {"normalMap", "bumpMap"}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def import_textures_for_material(
    cod_material: CoDMaterial,
    images_path: str,
    textures_package: str,
) -> Dict[str, unreal.Texture2D]:
    """
    Import all .tga textures referenced by a material that exist on disk.
    Returns a dict of tex_type → UTexture2D. Missing textures are silently skipped.
    """
    imported: Dict[str, unreal.Texture2D] = {}
    for texture in cod_material.textures:
        if "$black" in texture.name or "identitynormal" in texture.name:
            continue
        tex = _find_or_import_texture(texture.name, texture.tex_type, images_path, textures_package)
        if tex:
            imported[texture.tex_type] = tex
    return imported


def create_material(
    cod_material: CoDMaterial,
    images_path: str,
    package_path: str,
) -> Optional[unreal.Material]:
    """
    Create a UE5 Material asset for the given CoDMaterial.

    images_path should point to the exported_images/<game>/ directory so we
    can find the .tga files. package_path is the Content Browser root — we'll
    create Materials/ and Textures/ subfolders inside it.

    Returns the created UMaterial, or None if creation failed. If the asset
    already exists it's returned as-is.
    """
    safe_name = _sanitise_name(cod_material.name)
    mats_package = f"{package_path}/Materials"
    full_path = f"{mats_package}/{safe_name}"
    textures_package = f"{package_path}/Textures"

    # Return existing asset
    if unreal.EditorAssetLibrary.does_asset_exist(full_path):
        return unreal.EditorAssetLibrary.load_asset(full_path)

    # Import textures first
    tex_assets = import_textures_for_material(cod_material, images_path, textures_package)

    # Create material asset
    factory = unreal.MaterialFactoryNew()
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    material: unreal.Material = asset_tools.create_asset(safe_name, mats_package, unreal.Material, factory)
    if material is None:
        unreal.log_error(f"[C2M] Failed to create material: {full_path}")
        return None

    mel = unreal.MaterialEditingLibrary

    with unreal.ScopedEditorTransaction(f"C2M Material: {safe_name}"):
        material.modify()
        _configure_blend_mode(material, cod_material)

    # Build material expressions
    _build_expressions(material, cod_material, tex_assets, mel)

    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(full_path)
    unreal.log(f"[C2M] ✓ Material: {full_path}")
    return material


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _configure_blend_mode(material: unreal.Material, cod_material: CoDMaterial):
    """Set the material blend mode based on CoD material properties."""
    if cod_material.is_glass:
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        material.set_editor_property("two_sided", True)
    elif cod_material.is_transparent or cod_material.is_reveal:
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    else:
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
        material.set_editor_property("opacity_mask_clip_value", 0.5)

    if cod_material.is_emissive:
        material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)


def _build_expressions(
    material: unreal.Material,
    cod_material: CoDMaterial,
    tex_assets: Dict[str, unreal.Texture2D],
    mel,
):
    """Wire up material expression nodes for all available textures."""
    node_y = 0
    last_color_node = None

    for texture in cod_material.textures:
        if "$black" in texture.name or "identitynormal" in texture.name:
            continue
        if texture.tex_type not in tex_assets:
            continue

        tex_asset = tex_assets[texture.tex_type]
        node_x = -900

        tex_node = mel.create_material_expression(
            material, unreal.MaterialExpressionTextureSample, node_x, node_y
        )
        tex_node.set_editor_property("texture", tex_asset)

        t = texture.tex_type

        # ── Base Colour ────────────────────────────────────────────────────
        if t in ("colorMap", "colorOpacity", "colorGloss") or t.startswith("color"):
            mel.connect_material_property(tex_node, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
            last_color_node = tex_node

            if t == "colorOpacity":
                mel.connect_material_property(tex_node, "A", unreal.MaterialProperty.MP_OPACITY)
            elif t == "colorGloss":
                inv = mel.create_material_expression(material, unreal.MaterialExpressionOneMinus, node_x + 250, node_y)
                mel.connect_material_expressions(tex_node, "A", inv, "")
                mel.connect_material_property(inv, "", unreal.MaterialProperty.MP_ROUGHNESS)

        # ── Normal Map ─────────────────────────────────────────────────────
        elif t in _NORMAL_TEX_TYPES:
            mel.connect_material_property(tex_node, "RGB", unreal.MaterialProperty.MP_NORMAL)

        # ── Specular / Gloss ───────────────────────────────────────────────
        elif t in ("specularMap", "specGloss"):
            mel.connect_material_property(tex_node, "RGB", unreal.MaterialProperty.MP_SPECULAR)
            inv = mel.create_material_expression(material, unreal.MaterialExpressionOneMinus, node_x + 250, node_y)
            mel.connect_material_expressions(tex_node, "A", inv, "")
            mel.connect_material_property(inv, "", unreal.MaterialProperty.MP_ROUGHNESS)

        # ── Gloss (roughness inverse) ──────────────────────────────────────
        elif t == "glossMap":
            inv = mel.create_material_expression(material, unreal.MaterialExpressionOneMinus, node_x + 250, node_y)
            mel.connect_material_expressions(tex_node, "RGB", inv, "")
            mel.connect_material_property(inv, "", unreal.MaterialProperty.MP_ROUGHNESS)

        # ── Emissive ───────────────────────────────────────────────────────
        elif t in ("emissionMap", "emissiveMap", "emissionMap0"):
            mel.connect_material_property(tex_node, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

        # ── Reveal / Opacity Mask ──────────────────────────────────────────
        elif t == "revealMap":
            mel.connect_material_property(tex_node, "RGB", unreal.MaterialProperty.MP_OPACITY)

        node_y -= 280

    # ── colorTint setting ─────────────────────────────────────────────────
    if "colorTint" in cod_material.settings and last_color_node is not None:
        parts = cod_material.settings["colorTint"].split()
        if len(parts) >= 3:
            try:
                r, g, b = float(parts[0]), float(parts[1]), float(parts[2])
                tint = mel.create_material_expression(
                    material, unreal.MaterialExpressionConstant3Vector, -500, node_y
                )
                tint.set_editor_property("constant", unreal.LinearColor(r, g, b, 1.0))
                mul = mel.create_material_expression(
                    material, unreal.MaterialExpressionMultiply, -300, node_y
                )
                mel.connect_material_expressions(last_color_node, "RGB", mul, "A")
                mel.connect_material_expressions(tint, "", mul, "B")
                mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_BASE_COLOR)
            except ValueError:
                pass


def _find_or_import_texture(
    name: str,
    tex_type: str,
    images_path: str,
    textures_package: str,
) -> Optional[unreal.Texture2D]:
    """Find an existing texture asset or import the .tga from disk."""
    safe_name = _sanitise_name(name)
    asset_path = f"{textures_package}/{safe_name}"

    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return unreal.EditorAssetLibrary.load_asset(asset_path)

    tga_path = os.path.join(images_path, name + ".tga")
    if not os.path.isfile(tga_path):
        return None

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", tga_path)
    task.set_editor_property("destination_path", textures_package)
    task.set_editor_property("destination_name", safe_name)
    task.set_editor_property("replace_existing", False)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    texture = unreal.EditorAssetLibrary.load_asset(asset_path)
    if texture is None:
        return None

    _configure_texture(texture, tex_type)
    return texture


def _configure_texture(texture: unreal.Texture2D, tex_type: str):
    """Set sRGB, compression, and DirectX→OpenGL normal map flip."""
    with unreal.ScopedEditorTransaction("C2M Configure Texture"):
        texture.modify()
        is_normal = tex_type in _NORMAL_TEX_TYPES
        if is_normal:
            texture.set_editor_property("srgb", False)
            texture.set_editor_property("compression_settings",
                                        unreal.TextureCompressionSettings.TC_NORMALMAP)
            texture.set_editor_property("flip_green_channel", True)  # DX → GL
        elif tex_type in _SRGB_TEX_TYPES:
            texture.set_editor_property("srgb", True)
            texture.set_editor_property("compression_settings",
                                        unreal.TextureCompressionSettings.TC_DEFAULT)
        else:
            texture.set_editor_property("srgb", False)
            texture.set_editor_property("compression_settings",
                                        unreal.TextureCompressionSettings.TC_DEFAULT)
        texture.update_resource()


def _sanitise_name(name: str) -> str:
    for ch in ("::", ":", "/", "\\", " ", ".", "#", "$"):
        name = name.replace(ch, "_")
    return name.strip("_") or "unnamed"
