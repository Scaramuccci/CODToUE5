"""
coords.py

Coordinate system conversion between CoD and Unreal Engine 5.

CoD uses inches with a left-handed system where Y points left.
UE5 uses centimetres with a left-handed system where Y points right.
So the conversion is:

    ue5_x =  cod_x * 2.54
    ue5_y = -cod_y * 2.54   (Y flipped for handedness)
    ue5_z =  cod_z * 2.54

Quaternions need their Y component negated for the same reason.

Normal maps: CoD uses DirectX convention (green channel points down) and
UE5 uses OpenGL convention (green channel points up), so we set
flip_green_channel = True on every imported normal texture.
"""

from __future__ import annotations
import math
from typing import Tuple

INCH_TO_CM: float = 2.54


def to_ue5_location(x: float, y: float, z: float) -> Tuple[float, float, float]:
    """Convert a CoD world position (inches, Y-left) to UE5 (cm, Y-right)."""
    return (x * INCH_TO_CM, -y * INCH_TO_CM, z * INCH_TO_CM)


def to_ue5_normal(nx: float, ny: float, nz: float) -> Tuple[float, float, float]:
    """Flip the Y component of a normal to account for the axis handedness change."""
    return (nx, -ny, nz)


def to_ue5_quaternion(qx: float, qy: float, qz: float, qw: float) -> Tuple[float, float, float, float]:
    """Convert a CoD quaternion (XYZW) to UE5 — just negate Y for the axis flip."""
    return (qx, -qy, qz, qw)


def to_ue5_rotator_from_euler(rx_deg: float, ry_deg: float, rz_deg: float) -> Tuple[float, float, float]:
    """
    Convert CoD Euler angles (degrees, Y-left) to a UE5 FRotator (pitch, yaw, roll).
    Returns degrees.
    """
    return (rx_deg, -ry_deg, rz_deg)


def direction_to_rotator(direction: Tuple) -> Tuple[float, float, float]:
    """
    Turn a CoD direction vector into a UE5 FRotator (pitch, yaw, roll in degrees).
    Used to orient directional and spot lights.
    """
    dx, dy, dz = direction[0], -direction[1], direction[2]  # flip Y
    pitch = math.degrees(math.asin(max(-1.0, min(1.0, -dz))))
    yaw = math.degrees(math.atan2(dy, dx))
    return (pitch, yaw, 0.0)


def inch_to_cm(value: float) -> float:
    return value * INCH_TO_CM
