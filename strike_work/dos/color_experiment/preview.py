"""Build hardware-constrained graphics candidates and NTSC filter comparisons."""
import ctypes
import json
import struct
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / 'unpacked/jungle'
OUT = ROOT / 'color_experiment/output'
DAC = np.array([0, 52, 87, 116, 144, 172, 206, 255])
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def palette(data):
    start = data.index(b'PALETTE ') + 32
    count = struct.unpack_from('<H', data, start-24)[0] + 1
    return np.rint(np.frombuffer(data[start:start+count*3], dtype=np.uint8).reshape(-1, 3)* (255/63)).astype(np.uint8)


def sprite(name, frame):
    data = (RES / name).read_bytes()
    section = data.index(b'BLOCKS  ')
    count = struct.unpack_from('<H', data, section+8)[0]
    tiles = [np.zeros((16, 16), dtype=np.uint8)]
    pointers = struct.unpack_from('<' + str(count) + 'I', data, section+16)
    for tile_number, pointer in enumerate(pointers):
        pos = section + (pointer & 0x7fffffff)
        if pointer & 0x80000000:
            pixels = []
            for group in range(32):
                mask = data[pos]
                pos += 1
                for bit in range(7, -1, -1):
                    value = 0
                    if mask & (1 << bit):
                        value = data[pos]
                        pos += 1
                    pixels.append(value)
            following = [section+(p & 0x7fffffff) for p in pointers if (p >> 31) and section+(p & 0x7fffffff) > section+(pointer & 0x7fffffff)]
            end = min(following) if following else data.index(b'PALETTE ')
            assert pos == end if following else 0 <= end-pos < 16
            tiles.append(np.array(pixels, dtype=np.uint8).reshape(16, 16))
        else:
            tiles.append(np.frombuffer(data[pos:pos+256], dtype=np.uint8).reshape(16, 16))
    canvas_w, canvas_h, x, y, width, height, table = struct.unpack_from('<6HI', data, 48+16*frame)
    assert width % 16 == height % 16 == 0
    ids = struct.unpack_from('<' + str(width*height//256) + 'H', data, 32+table)
    image = np.zeros((height, width), dtype=np.uint8)
    for i, value in enumerate(ids):
        assert value <= count
        image[(i//(width//16))*16:(i//(width//16)+1)*16, (i%(width//16))*16:(i%(width//16)+1)*16] = tiles[value]
    colors = palette(data)
    assert image.max() < len(colors)
    return image, colors


def quantize_palette(indices, colors):
    visible = colors[indices[indices != 0]]
    unique, counts = np.unique(visible, axis=0, return_counts=True)
    if len(unique) > 15:
        sample = Image.fromarray(visible.reshape(1, -1, 3))
        quantized = sample.quantize(colors=15, method=Image.Quantize.MEDIANCUT)
        unique = np.array(quantized.getpalette()[:45], dtype=np.uint8).reshape(15, 3)
    levels = np.abs(unique[:, :, None].astype(float) - DAC).argmin(axis=2)
    levels = np.unique(levels, axis=0)
    return np.vstack([np.zeros((1, 3), dtype=int), levels])


def candidates(indices, source, levels):
    colors = DAC[levels].astype(float)
    pairs = [(i, i) for i in range(1, len(colors))]
    pairs += [(i, j) for i in range(1, len(colors)) for j in range(i+1, len(colors))]
    mix = np.array([(colors[a]+colors[b])/2 for a, b in pairs])
    # Favor a small contrast between the pair to limit visible grain in RGB.
    penalty = np.array([np.sum((colors[a]-colors[b])**2)*0.025 for a, b in pairs])
    error = ((source[:, None].astype(float)-mix)**2).sum(axis=2) + penalty
    chosen = np.array(pairs)[error.argmin(axis=1)]
    nearest = ((source[:, None].astype(float)-colors[None, 1:])**2).sum(axis=2).argmin(axis=1)+1
    yy, xx = np.indices(indices.shape)
    results = [nearest[indices], np.where(xx % 2, chosen[indices, 1], chosen[indices, 0]),
               np.where((xx+yy) % 2, chosen[indices, 1], chosen[indices, 0])]
    for result in results:
        result[indices == 0] = 0
    return results


def ntsc(indices, levels):
    # Frame the crop at a real 320-pixel line width. This is the GX NTSC
    # composite preset, not a capture of a PAL console or a CRT phosphor model.
    h, w = indices.shape
    width = ((w+15)//4)*4
    codes = levels[:, 0] | (levels[:, 1]<<3) | (levels[:, 2]<<6)
    frame = np.zeros((h, width), dtype=np.uint16)
    frame[:, 4:4+w] = codes[indices]
    output = np.zeros((h, width*2), dtype=np.uint16)
    lib = ctypes.CDLL(str(Path(__file__).with_name('preview.so')))
    lib.preview.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
    lib.preview(frame.ctypes.data, output.ctypes.data, width, h)
    rgb = np.stack([((output>>11)&31)*255//31, ((output>>5)&63)*255//63, (output&31)*255//31], axis=2).astype(np.uint8)
    return Image.fromarray(rgb[:, 8:8+w*2]).resize((w*2, h*2), Image.Resampling.NEAREST)


def export(name, indices, levels):
    height, width = indices.shape
    padded = np.zeros(((height+7)//8*8, (width+7)//8*8), dtype=np.uint8)
    padded[:height, :width] = indices
    patterns, words, lookup = [], [], {}
    for y in range(0, padded.shape[0], 8):
        for x in range(0, padded.shape[1], 8):
            tile = padded[y:y+8, x:x+8].tobytes()
            if tile not in lookup:
                index = len(patterns)
                patterns.append(tile)
                tile_array = np.frombuffer(tile, dtype=np.uint8).reshape(8, 8)
                for horizontal, vertical in [(0, 0), (1, 0), (0, 1), (1, 1)]:
                    view = tile_array[::(-1 if vertical else 1), ::(-1 if horizontal else 1)]
                    lookup.setdefault(view.tobytes(), index | horizontal*0x800 | vertical*0x1000)
            words.append(lookup[tile])
    assert len(patterns) <= 2048
    packed = bytes((tile[i]<<4)|tile[i+1] for tile in patterns for i in range(0, 64, 2))
    base = OUT / name
    base.mkdir(exist_ok=True)
    (base/'patterns.bin').write_bytes(packed)
    (base/'map.bin').write_bytes(struct.pack('>'+str(len(words))+'H', *words))
    cram = [int(r*2 | g*32 | b*512) for r, g, b in levels]
    (base/'palette.bin').write_bytes(struct.pack('>16H', *(cram+[0]*(16-len(cram)))))
    # Reconstruct every tile from the emitted pattern and map to catch flips.
    for i, word in enumerate(words):
        tile = np.array(list(patterns[word&2047]), dtype=np.uint8).reshape(8, 8)
        if word&2048: tile = tile[:, ::-1]
        if word&4096: tile = tile[::-1, :]
        y, x = divmod(i, padded.shape[1]//8)
        assert np.array_equal(tile, padded[y*8:y*8+8, x*8:x*8+8])
    return {'size': [width, height], 'colors_including_transparent': len(levels),
            'unique_tiles_with_flips': len(patterns), 'pattern_bytes': len(packed)}


def sheet(rows, filename, filtered=False):
    cw = 620 if filtered else 320
    titles = ['DOS', 'Genesis без дизеринга', 'Полосы 1 px', 'Шахматка 2×2']
    if filtered: titles = ['NTSC без дизеринга', 'NTSC полосы', 'NTSC шахматка']
    gap = 16
    heights = [max(im.height for im in row[1])+48 for row in rows]
    canvas = Image.new('RGB', (gap+(cw+gap)*len(titles), 72+sum(heights)+42), '#19202b')
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(FONT, 19)
    small = ImageFont.truetype(FONT, 16)
    for col, title in enumerate(titles): draw.text((gap+col*(cw+gap), 18), title, font=font, fill='white')
    y = 60
    for (name, images), rh in zip(rows, heights):
        draw.text((gap, y), name, font=small, fill='#cad9e5')
        for col, image in enumerate(images):
            canvas.paste(image, (gap+col*(cw+gap)+(cw-image.width)//2, y+30))
        y += rh
    text = 'NTSC-модель Genesis Plus GX. ЭЛТ и PAL здесь не моделируются.' if filtered else 'RGB по нелинейной шкале DAC. Варианты используют одну палитру на объект.'
    draw.text((gap, canvas.height-30), text, font=small, fill='#cad9e5')
    canvas.save(OUT / filename)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    objects = []
    reports = {}
    for name, frame, title in [('AWAC', 0, 'Сбитый AWAC'), ('TANK1', 4, 'Целевой танкер'), ('F217', 0, 'Четырёхэтажная башня')]:
        indices, source = sprite(name, frame)
        levels = quantize_palette(indices, source)
        variants = candidates(indices, source, levels)
        pictures = [Image.fromarray(source[indices])]+[Image.fromarray(DAC[levels][v].astype(np.uint8)) for v in variants]
        objects.append((title, pictures))
        reports[name] = {mode: export(name+'_'+mode, v, levels) for mode, v in zip(['nearest', 'stripes', 'checker'], variants)}
    sheet(objects, 'Eco_Threat_objects_RGB.png')
    filtered = []
    for name, frame, title in [('AWAC', 0, 'Сбитый AWAC'), ('TANK1', 4, 'Целевой танкер'), ('F217', 0, 'Четырёхэтажная башня')]:
        indices, source = sprite(name, frame)
        levels = quantize_palette(indices, source)
        filtered.append((title, [ntsc(v, levels) for v in candidates(indices, source, levels)]))
    sheet(filtered, 'Eco_Threat_objects_NTSC.png', True)
    blocks = (RES/'BLOCKS10').read_bytes()
    tiles = np.frombuffer(blocks[48:48+32768], dtype=np.uint8).reshape(128,16,16)
    raw = np.frombuffer((RES/'MAP10').read_bytes(), dtype='<u2').reshape(224,320)
    world = np.empty((3584,5120), dtype=np.uint8)
    for y in range(224):
        for x in range(320):
            value = int(raw[y,x]); tile = tiles[value&255]
            if value&256: tile=tile[:,::-1]
            if value&512: tile=tile[::-1,:]
            world[y*16:y*16+16,x*16:x*16+16]=tile
    source = palette(blocks)
    levels = quantize_palette(tiles, source)
    rows, filtered = [], []
    for title,x,y in [('Остров',560,240), ('Берег',560,2496), ('Вода',2000,1496)]:
        crop = world[y:y+80,x:x+128]
        variants = candidates(crop,source,levels)
        pictures=[Image.fromarray(source[crop])]+[Image.fromarray(DAC[levels][v].astype(np.uint8)) for v in variants]
        rows.append((title,[im.resize((256,160),Image.Resampling.NEAREST) for im in pictures]))
        filtered.append((title,[ntsc(v,levels) for v in variants]))
    sheet(rows,'Eco_Threat_terrain_RGB.png')
    sheet(filtered,'Eco_Threat_terrain_NTSC.png',True)
    (OUT/'report.json').write_text(json.dumps(reports,indent=2)+'\n')
    print(json.dumps(reports,indent=2))


if __name__ == '__main__': main()
