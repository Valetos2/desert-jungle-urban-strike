"""Build a Jungle Strike DOS exploration DAT from the original retail CD file."""
import argparse
import hashlib
from pathlib import Path
import struct

from unpack_dat import unpack

DAT_SHA256 = '393216dea78d712e63d1466df58bf44d78d564fd126ca5bb5932c3587bb8df65'


def jump(at, target):
    return b'\xe9' + struct.pack('<H', (target - at - 3) & 0xffff)


def patch_executable(data):
    exe = bytearray(data)
    code = struct.unpack_from('<H', exe, 8)[0] * 16

    def write(at, expected, patch):
        start = code + at
        expected = bytes.fromhex(expected)
        if exe[start:start + len(expected)] != expected:
            raise ValueError(f'Unexpected original instructions at {at:#x}')
        if len(patch) > len(expected):
            raise ValueError(f'Patch exceeds its range at {at:#x}')
        exe[start:start + len(patch)] = patch

    # Reuse the native cheat toggle path. Entitlement and other cheat keys are separate.
    write(0x887f, '803e', bytes.fromhex('eb33'))
    # Both damage entry points still apply the original routine to all other objects.
    guard = bytes.fromhex('8b36d21f3b36fe5c7501c3')
    guard += jump(0x8881 + len(guard), 0xc9ca)
    write(0x8881, '311f00742ef6069504017427c606', guard)
    guard = bytes.fromhex('8b36fe5c85f6740a8b74043b36d21f7501c38b36d21f')
    guard += jump(0x888f + len(guard), 0xc9f4)
    write(0x888f, '950480f6169055803e9055007508c706165cd18deb06c70616', guard)
    write(0xc9c6, '8b36d21f', jump(0xc9c6, 0x8881) + b'\x90')
    write(0xc9f0, '8b36d21f', jump(0xc9f0, 0x888f) + b'\x90')

    # Keep the current maximum fuel, even if a mission loads a lower current value.
    fuel = bytes.fromhex('a1103fa37d3e') + jump(0xafc9, 0xaff6)
    write(0xafc3, '29067d3e7f070fba6c', fuel)

    # The now unreachable low-fuel warning block holds the player-only ammo guard.
    ammo = bytes.fromhex('a1c81f3b06fe5c740b803e9055ff7404836c0c01')
    ammo += jump(0xafd7 + len(ammo), 0x7eb3)
    write(0xafd7, '66833e7c5a027c0f66c7067c5a88ffffffc706165c7202', ammo)
    write(0x7ea8, '803e9055ff7404836c0c01', jump(0x7ea8, 0xafd7))
    return bytes(exe)


def encode_literal(data):
    stream = bytearray(b'\0\0')
    for start in range(0, len(data), 4096):
        chunk = data[start:start + 4096]
        stream.extend(struct.pack('>H', 0x4000 | len(chunk)))
        stream.extend(chunk)
    return bytes(stream + b'\0')


def build(dat):
    if hashlib.sha256(dat).hexdigest() != DAT_SHA256:
        raise ValueError('Wrong original JUNGLE.DAT revision')
    count = struct.unpack_from('<I', dat)[0]
    directory_end = 16 + count * 16
    directory = bytearray(dat[:directory_end])
    if directory[16:24].strip() != b'!':
        raise ValueError('Expected executable to be the first entry')
    start, = struct.unpack_from('<I', directory, 24)
    stop, = struct.unpack_from('<I', directory, 40)
    original, used = unpack(dat[start:stop])
    if used != stop - start or not original.startswith(b'MZ'):
        raise ValueError('Malformed original executable resource')
    patched = patch_executable(original)
    packed = encode_literal(patched)
    if unpack(packed) != (patched, len(packed)):
        raise ValueError('Executable failed to round-trip')
    delta = len(packed) - (stop - start)
    struct.pack_into('<H', directory, 28, (len(packed) + 15) // 16)
    for i in range(1, count):
        field = 24 + i * 16
        offset, = struct.unpack_from('<I', directory, field)
        struct.pack_into('<I', directory, field, offset + delta)
    return bytes(directory) + dat[directory_end:start] + packed + dat[stop:]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.resolve() == args.original.resolve():
        raise SystemExit('Choose a separate output file')
    args.output.write_bytes(build(args.original.read_bytes()))
