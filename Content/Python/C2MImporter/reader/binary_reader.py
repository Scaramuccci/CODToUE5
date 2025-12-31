"""
binary_reader.py

Tiny helpers for reading the primitive types you'll find in a .c2m file.
Everything is little-endian. Floats are standard IEEE 754 single-precision.

C2M strings have a quirky format: one length-prefix byte (which we skip —
it doesn't seem to match the actual string length reliably), followed by
null-terminated UTF-8 bytes.
"""

import struct

__all__ = [
    "read_byte", "read_bool", "read_short", "read_ushort",
    "read_int", "read_uint", "read_float", "read_double",
    "read_ulong", "read_bytes", "read_string",
]


def read_byte(file) -> int:
    return struct.unpack("<B", file.read(1))[0]


def read_bool(file) -> bool:
    return struct.unpack("<?", file.read(1))[0]


def read_short(file) -> int:
    return struct.unpack("<h", file.read(2))[0]


def read_ushort(file) -> int:
    return struct.unpack("<H", file.read(2))[0]


def read_int(file) -> int:
    return struct.unpack("<i", file.read(4))[0]


def read_uint(file) -> int:
    return struct.unpack("<I", file.read(4))[0]


def read_float(file) -> float:
    return struct.unpack("<f", file.read(4))[0]


def read_double(file) -> float:
    return struct.unpack("<d", file.read(8))[0]


def read_ulong(file) -> int:
    return struct.unpack("<Q", file.read(8))[0]


def read_bytes(file, count: int) -> list:
    return [struct.unpack("<B", file.read(1))[0] for _ in range(count)]


def read_string(file) -> str:
    """Read a C2M null-terminated UTF-8 string, skipping the leading length byte."""
    read_byte(file)  # length prefix — not reliable, just skip it
    buf = b""
    while True:
        ch = file.read(1)
        if ch == b"\x00":
            break
        buf += ch
    return buf.decode("utf-8", errors="replace")
