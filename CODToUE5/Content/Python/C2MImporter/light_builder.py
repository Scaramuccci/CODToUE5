"""
light_builder.py

Spawns CoD lights as UE5 light actors in the current level.

CoD SUN  → DirectionalLight
CoD SPOT → SpotLight
CoD POINT → PointLight

Intensity: CoD stores it as the alpha channel of the light colour (0..1+).
UE5 uses physical units, so we scale up:
  - Sun:   × 100,000 Lux   (roughly outdoor daylight)
  - Spot:  × 500 Candelas
  - Point: × 500 Candelas

These multipliers were tuned to visually match the Blender importer output.
Tweak SUN_MULTIPLIER / SPOT_MULTIPLIER / POINT_MULTIPLIER at the top of this
file if your scene looks too bright or too dark.

Spot cone angles are stored as cos(half_angle) in the .c2m file, so
outer_angle_deg = degrees(acos(cos_half_fov_outer)) * 2.
"""

from __future__ import annotations
import math
import unreal
from typing import Optional

from .reader.c2m_reader import CoDLight
from .coords import to_ue5_location, direction_to_rotator, inch_to_cm


# Energy multipliers — bump these up or down if your scene looks wrong
SUN_MULTIPLIER   = 100_000.0   # Lux
SPOT_MULTIPLIER  = 500.0       # Candelas
POINT_MULTIPLIER = 500.0       # Candelas


def spawn_light(cod_light: CoDLight) -> Optional[unreal.Actor]:
    """Spawn the appropriate UE5 light actor for this CoDLight and return it."""
    x, y, z = to_ue5_location(*cod_light.origin)
    pos = unreal.Vector(x, y, z)
    pit, yaw, rol = direction_to_rotator(cod_light.direction)
    rot = unreal.Rotator(pit, yaw, rol)
    r, g, b, intensity = cod_light.color
    color = unreal.LinearColor(r, g, b, 1.0)

    if cod_light.light_type == "SUN":
        return _spawn_directional(pos, rot, color, intensity)
    elif cod_light.light_type == "SPOT":
        return _spawn_spot(pos, rot, color, intensity, cod_light)
    elif cod_light.light_type == "POINT":
        return _spawn_point(pos, color, intensity, cod_light)
    else:
        unreal.log_warning(f"[C2M] Unknown light type: {cod_light.light_type}")
        return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _spawn_directional(
    pos: unreal.Vector,
    rot: unreal.Rotator,
    color: unreal.LinearColor,
    intensity: float,
) -> Optional[unreal.Actor]:
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.DirectionalLight, pos, rot
    )
    if actor is None:
        return None
    comp: unreal.DirectionalLightComponent = actor.get_component_by_class(
        unreal.DirectionalLightComponent
    )
    if comp:
        comp.set_light_color(color)
        comp.set_intensity(intensity * SUN_MULTIPLIER)
        comp.set_editor_property("cascade_shadow_distance_fade_out_fraction", 0.1)
    return actor


def _spawn_spot(
    pos: unreal.Vector,
    rot: unreal.Rotator,
    color: unreal.LinearColor,
    intensity: float,
    cod_light: CoDLight,
) -> Optional[unreal.Actor]:
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SpotLight, pos, rot
    )
    if actor is None:
        return None
    comp: unreal.SpotLightComponent = actor.get_component_by_class(
        unreal.SpotLightComponent
    )
    if comp:
        comp.set_light_color(color)
        comp.set_intensity(intensity * SPOT_MULTIPLIER)

        # Attenuation radius
        radius_cm = inch_to_cm(cod_light.d_attenuation if cod_light.d_attenuation > 0.0
                               else cod_light.radius)
        comp.set_editor_property("attenuation_radius", max(radius_cm, 50.0))

        # Cone angles from cos(half_fov)
        if cod_light.cos_half_fov_outer > 0.0:
            outer = math.degrees(math.acos(
                max(-1.0, min(1.0, cod_light.cos_half_fov_outer))
            )) * 2.0
            comp.set_outer_cone_angle(outer)
        if cod_light.cos_half_fov_inner > 0.0:
            inner = math.degrees(math.acos(
                max(-1.0, min(1.0, cod_light.cos_half_fov_inner))
            )) * 2.0
            comp.set_inner_cone_angle(inner)

        comp.set_editor_property("source_radius", inch_to_cm(cod_light.radius) * 0.1)
        comp.set_editor_property("use_inverse_squared_falloff", True)
    return actor


def _spawn_point(
    pos: unreal.Vector,
    color: unreal.LinearColor,
    intensity: float,
    cod_light: CoDLight,
) -> Optional[unreal.Actor]:
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PointLight, pos, unreal.Rotator(0, 0, 0)
    )
    if actor is None:
        return None
    comp: unreal.PointLightComponent = actor.get_component_by_class(
        unreal.PointLightComponent
    )
    if comp:
        comp.set_light_color(color)
        comp.set_intensity(intensity * POINT_MULTIPLIER)
        comp.set_editor_property(
            "attenuation_radius",
            max(inch_to_cm(cod_light.radius), 50.0)
        )
        comp.set_editor_property("source_radius", inch_to_cm(cod_light.radius) * 0.05)
        comp.set_editor_property("use_inverse_squared_falloff", True)
    return actor
