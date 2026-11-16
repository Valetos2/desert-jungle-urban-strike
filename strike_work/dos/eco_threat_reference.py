"""Build private reference images and text from a local Jungle DOS copy."""
import argparse
from collections import defaultdict
from functools import lru_cache
import json
from pathlib import Path
import re
import struct

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent


def word(data, offset):
    return struct.unpack_from('<H', data, offset)[0]


def long(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def palette(data):
    start = data.index(b'PALETTE ') + 32
    values = [round(min(value, 63) * 255 / 63) for value in data[start:]]
    return (values + [0] * 768)[:768]


def sprite(data, frame):
    section = data.index(b'SPRITES ')
    blocks = data.find(b'BLOCKS  ')
    if frame >= word(data, section + 8):
        raise ValueError(f'Frame {frame} out of range')
    header = section + 16 + 16 * frame
    width, height = struct.unpack_from('<HH', data, header + 8)
    tilemap = section + long(data, header + 12)
    image = Image.new('RGBA', (width, height))
    colors = palette(data)
    if blocks < 0:
        pixels = image.load()
        pos = tilemap
        for y in range(height):
            for x in range(0, width, 8):
                bits = data[pos]
                pos += 1
                for bit in range(min(8, width - x)):
                    if bits & (0x80 >> bit):
                        index = 3 * data[pos]
                        pixels[x + bit, y] = (*colors[index:index + 3], 255)
                        pos += 1
        return image
    count = word(data, blocks + 8)

    @lru_cache
    def tile(index):
        if index >= count:
            raise ValueError(f'Invalid tile index {index}')
        entry = long(data, blocks + 16 + 4 * index)
        start = blocks + (entry & 0x7fffffff)
        mask = bytearray([255] * 256)
        if entry >> 31:
            pixels = bytearray(256)
            mask = bytearray(256)
            pos = start
            for group in range(32):
                bits = data[pos]
                pos += 1
                for bit in range(8):
                    if bits & (0x80 >> bit):
                        i = 8 * group + bit
                        pixels[i] = data[pos]
                        mask[i] = 255
                        pos += 1
        else:
            pixels = data[start:start + 256]
        result = Image.frombytes('P', (16, 16), bytes(pixels))
        result.putpalette(colors)
        result = result.convert('RGBA')
        result.putalpha(Image.frombytes('L', (16, 16), bytes(mask)))
        return result

    for y in range(height // 16):
        for x in range(width // 16):
            index = word(data, tilemap + 2 * (y * (width // 16) + x))
            number = index & 0x3fff
            if not number:
                continue
            art = tile(number - 1)
            if index & 0x4000:
                art = art.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            if index & 0x8000:
                art = art.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            image.paste(art, (16 * x, 16 * y))
    bounds = image.getbbox()
    return image.crop(bounds) if bounds else image


def write_briefing(resources, output):
    data = (resources / 'FLICDATA').read_bytes()

    def record(index):
        return data[word(data, index * 2):word(data, (index + 1) * 2)]

    exe = (resources / 'EXECUTABLE').read_bytes()
    assert b'10 ECO THREAT\0' in exe
    brief = re.findall(rb'[ -~]{20,}', record(190))
    lines = ['# 10 ECO THREAT', '', '## Opening briefing', '']
    lines += [line.decode('ascii') + '\n' for line in brief]
    lines += ['## Objectives', '']
    for i in range(93, 101):
        label, title, body, *_ = record(i).split(b'\0')
        lines += [f'### {label.decode()} — {title.decode()}', '', body.decode(), '']
    lines += ['## In-mission messages (FLICDATA 175–181)', '']
    for i in range(175, 182):
        lines += [record(i).split(b'\0')[0].decode('ascii'), '']
    output.write_text('\n'.join(lines), encoding='utf-8')


def write_objects(resources, terrain_path, output):
    records = json.loads((ROOT / 'object_correspondence.json').read_text())['A']['objects']
    names = json.loads((ROOT / 'object_resources.json').read_text())['A']['objects']
    by_offset = {row['object_offset']: row for row in names}
    terrain = Image.open(terrain_path).convert('RGB').resize((1600, 1120))
    draw = ImageDraw.Draw(terrain)
    font = ImageFont.truetype('DejaVuSans.ttf', 15)
    groups = defaultdict(list)
    positions = []
    for i, row in enumerate(records, 1):
        descriptor = by_offset[row['offset']]
        groups[descriptor['resource'], descriptor['byte2']].append(i)
        y, x = row['position_yx']
        positions.append((x * 1600 / 5120, y * 1120 / 3584, str(i)))
    # Place labels near their exact point while keeping labels readable in tight clusters.
    placed = []
    for x, y, number in positions:
        for distance in (12, 24, 36, 48, 64, 88, 112):
            candidates = [(x + dx * distance, y + dy * distance)
                          for dx, dy in ((1, -1), (-1, -1), (1, 1), (-1, 1),
                                         (1, 0), (-1, 0), (0, 1), (0, -1))]
            box = next(((a - 13, b - 10, a + 13, b + 10) for a, b in candidates
                        if 14 <= a <= 1586 and 11 <= b <= 1109
                        and all(a + 14 < l or a - 14 > r or b + 11 < t or b - 11 > bot
                                for l, t, r, bot in placed)), None)
            if box:
                break
        if box is None:
            raise ValueError(f'No space for label {number}')
        placed.append(box)
        center = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
        draw.line((x, y, *center), fill='#ffe278', width=1)
        draw.ellipse((x-2, y-2, x+2, y+2), fill='#ffe278')
        draw.rounded_rectangle(box, radius=4, fill='#182733', outline='#ffe278')
        draw.text(center, number, anchor='mm', font=font, fill='white')
    terrain.save(output / 'Eco_Threat_map.png')

    cells = sorted(groups.items(), key=lambda pair: pair[1][0])
    gallery = Image.new('RGB', (1200, 55 + ((len(cells) + 3) // 4) * 176), '#172a36')
    draw = ImageDraw.Draw(gallery)
    draw.text((20, 17), 'ECO THREAT | Map IDs and original DOS sprites', font=font, fill='white')
    missing = []
    for i, ((resource, frame), ids) in enumerate(cells):
        x, y = i % 4 * 300, 55 + i // 4 * 176
        draw.rectangle((x+6, y+3, x+294, y+168), fill='#233f50', outline='#516b77')
        draw.text((x+15, y+10), f'{resource} / {frame}', font=font, fill='white')
        try:
            art = sprite((resources / resource.upper()).read_bytes(), frame)
            art.thumbnail((260, 106), Image.Resampling.NEAREST)
            gallery.paste(art, (x+(300-art.width)//2, y+35+(106-art.height)//2), art)
        except (FileNotFoundError, ValueError, IndexError) as error:
            missing.append((resource, frame, str(error)))
            draw.text((x+15, y+65), 'Preview unavailable', font=font, fill='white')
        draw.text((x+15, y+145), ', '.join(map(str, ids)),
                  font=ImageFont.truetype('DejaVuSans.ttf', 12), fill='#ffe278')
    gallery.save(output / 'Eco_Threat_objects.png')
    return len(records), len(cells), missing


def write_naval(resources, output):
    names = ['TANK1', 'TANK2', 'BOATPT', 'SUBSPRY', 'SUBTUR', 'FRIGATE']
    gallery = Image.new('RGB', (1250, 900), '#233f50')
    draw = ImageDraw.Draw(gallery)
    font = ImageFont.truetype('DejaVuSans.ttf', 15)
    for row, name in enumerate(names):
        data = (resources / name).read_bytes()
        count = word(data, data.index(b'SPRITES ') + 8)
        for frame in range(min(count, 5)):
            x, y = 250 * frame, 150 * row
            art = sprite(data, frame)
            art.thumbnail((235, 119), Image.Resampling.NEAREST)
            gallery.paste(art, (x + (250-art.width)//2, y + 24), art)
            draw.text((x+12, y+6), f'{name} / {frame}', font=font, fill='white')
    gallery.save(output / 'Eco_Threat_naval.png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--terrain', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    write_briefing(args.input, args.output / 'Eco_Threat_briefing.md')
    print(write_objects(args.input, args.terrain, args.output))
    write_naval(args.input, args.output)
