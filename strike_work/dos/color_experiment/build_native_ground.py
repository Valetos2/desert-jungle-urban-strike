"""Package Eco Threat checkerboard ground in Jungle's native map-block layout.

This emits a relocatable ROM data candidate. It does not alter a ROM or allocate
VRAM. Descriptors inherit the level-2 ground template. Runtime loading of tiles,
palettes and level registration remains to be integrated.
"""
import argparse
import json
import struct
from pathlib import Path
import numpy as np
from preview import RES, OUT, palette, quantize_palette, candidates, export


def build(rom, rom_base):
    blocks = (RES/'BLOCKS10').read_bytes()
    tiles = np.frombuffer(blocks[48:48+32768], dtype=np.uint8).reshape(128, 16, 16)
    source = palette(blocks)
    levels = quantize_palette(tiles, source)
    checker = candidates(tiles.reshape(128*16, 16), source, levels)[2].reshape(128, 16, 16)
    raw = np.frombuffer((RES/'MAP10').read_bytes(), dtype='<u2').reshape(224, 320)
    world = np.empty((3584, 5120), dtype=np.uint8)
    # Reflect source tiles first, then apply checker phase in world coordinates.
    # A reflected 16-pixel tile reverses the phase on that axis.
    # Recreate the opposite phase from the original source by shifting its
    # position in the candidate image by one row, keeping each source pixel.
    source_rows = np.zeros((128*16+1, 16), dtype=np.uint8)
    source_rows[1:] = tiles.reshape(128*16, 16)
    opposite = candidates(source_rows, source, levels)[2][1:].reshape(128, 16, 16)
    for value in np.unique(raw):
        horizontal, vertical = bool(value & 256), bool(value & 512)
        original = tiles[value & 255]
        actual = (opposite if horizontal != vertical else checker)[value & 255]
        if horizontal:
            original, actual = original[:, ::-1], actual[:, ::-1]
        if vertical:
            original, actual = original[::-1, :], actual[::-1, :]
        assert np.array_equal(actual, candidates(original, source, levels)[2])
    for y in range(224):
        for x in range(320):
            value = int(raw[y, x])
            horizontal, vertical = bool(value & 256), bool(value & 512)
            tile = (opposite if horizontal != vertical else checker)[value & 255]
            if horizontal: tile = tile[:, ::-1]
            if vertical: tile = tile[::-1, :]
            world[y*16:y*16+16, x*16:x*16+16] = tile
    report = export('ground_checker', world, levels)
    map_data = (OUT/'ground_checker/map.bin').read_bytes()
    names = np.frombuffer(map_data, dtype='>u2').reshape(448, 640)
    word = lambda at: int.from_bytes(rom[at:at+2], 'big')
    pointer = lambda at: int.from_bytes(rom[at:at+4], 'big') & 0xffffff
    level = pointer(0x19292e+4)
    template = bytearray(rom[pointer(pointer(level+0x5c)):pointer(pointer(level+0x5c))+32])
    assert word(level+6) == 20 and len(template) == 32
    unique, lookup, sectors = [], {}, []
    for y in range(28):
        for x in range(20):
            block = names[y*16:y*16+16, x*32:x*32+32].tobytes()
            if block not in lookup:
                lookup[block] = len(unique)
                unique.append(block)
            sectors.append(lookup[block])
    size = len(sectors)*4
    blob = bytearray(size)
    for index, block in enumerate(unique):
        descriptor = template.copy()
        struct.pack_into('>H', descriptor, 0x10, 2)  # native word map
        struct.pack_into('>I', descriptor, 0x16, rom_base+size+index*1056+32)
        struct.pack_into('>H', descriptor, 0x1e, 0)  # tile-set-relative base
        blob.extend(descriptor)
        blob.extend(block)
    for i, block in enumerate(sectors):
        struct.pack_into('>I', blob, i*4, rom_base+size+block*1056)
    # Read all entries through the same block/row arithmetic as ground_cell.
    for block_y in range(28):
        for block_x in range(20):
            p = struct.unpack_from('>I', blob, (block_y*20+block_x)*4)[0]-rom_base
            assert struct.unpack_from('>H', blob, p+0x10)[0] == 2
            data = struct.unpack_from('>I', blob, p+0x16)[0]-rom_base
            decoded = np.frombuffer(blob[data:data+1024], dtype='>u2').reshape(16, 32)
            assert np.array_equal(decoded, names[block_y*16:block_y*16+16, block_x*32:block_x*32+32])
    (OUT/'ground_checker/native_ground.bin').write_bytes(blob)
    report.update({'world_pixels': [5120, 3584], 'native_block_grid': [20, 28],
                   'unique_native_blocks': len(unique), 'native_blob_bytes': len(blob),
                   'candidate_rom_base': hex(rom_base), 'word_map_template_level': 2,
                   'status': 'All 286720 map entries verified. ROM loader integration pending.'})
    (OUT/'ground_checker/native_report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original_jungle_rom', type=Path)
    parser.add_argument('--rom-base', type=lambda s: int(s, 0), default=0x300000)
    args = parser.parse_args()
    if args.rom_base < 0 or args.rom_base % 2:
        raise SystemExit('Choose an even, nonnegative ROM base')
    build(args.original_jungle_rom.read_bytes(), args.rom_base)
