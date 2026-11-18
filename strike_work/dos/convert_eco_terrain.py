"""Convert reconstructed DOS Eco Threat ground into Mega Drive tile data.

The 320x224 DOS map layout and flip interpretation follow the reconstructed
preview. Output is a ground-only intermediate, with VRAM tile base zero and
palette line zero. The Genesis loader still needs to assign VRAM and ROM space.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def flip(tile, horizontal=False, vertical=False):
    rows = [tile[y*8:(y+1)*8] for y in range(8)]
    if horizontal:
        rows = [row[::-1] for row in rows]
    if vertical:
        rows.reverse()
    return b''.join(rows)


def convert(root):
    blocks = (root / 'BLOCKS10').read_bytes()
    raw_map = (root / 'MAP10').read_bytes()
    if len(raw_map) != 320*224*2 or struct.unpack_from('<H', blocks, 40)[0] != 128:
        raise ValueError('Unexpected Eco Threat terrain dimensions')
    pixels = blocks[48:48+128*256]
    if len(pixels) != 128*256 or max(pixels) > 15:
        raise ValueError('Terrain does not fit one Mega Drive palette')
    marker = blocks.index(b'PALETTE ')
    rgb = blocks[marker+32:marker+32+48]
    if len(rgb) != 48 or max(rgb) > 63:
        raise ValueError('Invalid VGA palette')
    palette = []
    for i in range(16):
        red, green, blue = [(c*7+31)//63*2 for c in rgb[3*i:3*i+3]]
        palette.append((blue << 8) | (green << 4) | red)
    unique = []
    lookup = {}
    quads = []
    for index in range(128):
        block = pixels[index*256:(index+1)*256]
        words = []
        for y0, x0 in [(0, 0), (0, 8), (8, 0), (8, 8)]:
            tile = b''.join(block[(y0+y)*16+x0:(y0+y)*16+x0+8] for y in range(8))
            if tile not in lookup:
                tile_id = len(unique)
                unique.append(tile)
                # A stored tile and its reflections share one VRAM pattern.
                for horizontal, vertical in [(False, False), (True, False), (False, True), (True, True)]:
                    lookup.setdefault(flip(tile, horizontal, vertical), tile_id | horizontal*0x800 | vertical*0x1000)
            words.append(lookup[tile])
        quads.append(words)
    if len(unique) > 2048:
        raise ValueError('Pattern indices exceed VDP name-table range')
    names = [0] * (640*448)
    for index, value in enumerate(struct.unpack('<71680H', raw_map)):
        if value & ~0x3ff or (value & 255) >= 128:
            raise ValueError(f'Invalid DOS map cell {index}: {value:#x}')
        horizontal, vertical = bool(value & 256), bool(value & 512)
        quad = quads[value & 255]
        x, y = (index % 320)*2, (index // 320)*2
        for dy in range(2):
            for dx in range(2):
                source = (dy ^ vertical)*2 + (dx ^ horizontal)
                names[(y+dy)*640+x+dx] = quad[source] ^ horizontal*0x800 ^ vertical*0x1000
    packed = bytes((tile[i] << 4) | tile[i+1] for tile in unique for i in range(0, 64, 2))
    return packed, struct.pack('>286720H', *names), struct.pack('>16H', *palette), {
        'source_sha256': {name: hashlib.sha256(data).hexdigest() for name, data in [('BLOCKS10', blocks), ('MAP10', raw_map)]},
        'world_pixels': [5120, 3584], 'map_tiles': [640, 448],
        'used_source_colors': len(set(pixels)), 'source_blocks_16x16': 128,
        'unique_patterns_8x8_with_flips': len(unique), 'pattern_bytes': len(packed),
        'map_bytes': len(names)*2, 'palette_bytes': 32,
        'layout_status': 'Reconstructed DOS layout, pending native renderer verification',
        'vram_status': 'Indices start at zero. Assign a VRAM base and palette line in the Genesis loader.',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('resources', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    patterns, names, palette, report = convert(args.resources)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, data in [('patterns.bin', patterns), ('map.bin', names), ('palette.bin', palette)]:
        (args.output / name).write_bytes(data)
    (args.output / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
