"""Build Eco Threat v9 from the hash-verified v8 test image."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import runpy
import struct
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
V3 = ROOT.parent / 'eco_flight_v3'
V8 = ROOT.parent / 'eco_flight_v8'
NAME = 'Jungle_Strike_Eco_Threat_Flight_TEST_v9'
sys.path.insert(0, str(ROOT.parent / 'eco_flight_v7'))
from terrain import recolor
from water import restore_static_lines, unpack_tiles

CHECKSUM = runpy.run_path(str(ROOT.parent / 'eco_flight_v4/build.py'))['checksum']


def build():
    rom = bytearray((V8 / (NAME.replace('v9', 'v8') + '.bin')).read_bytes())
    assert hashlib.sha256(rom).hexdigest() == 'e95acc6fcba04d7edda9ac047d33a3888ee5f50949f22821c9e6b5f9b7b4d482'

    def w(at):
        return struct.unpack_from('>H', rom, at)[0]

    def u(at):
        return struct.unpack_from('>I', rom, at)[0]

    def word(at, value):
        struct.pack_into('>H', rom, at, value)

    def long(at, value):
        struct.pack_into('>I', rom, at, value)

    def free(at, data):
        assert rom[at:at+len(data)] == b'\xff' * len(data), hex(at)
        rom[at:at+len(data)] = data

    def jump(at, expected, target, pad=''):
        replacement = bytes.fromhex('4ef9') + struct.pack('>I', target) + bytes.fromhex(pad)
        assert rom[at:at+len(replacement)] == bytes.fromhex(expected), hex(at)
        rom[at:at+len(replacement)] = replacement

    with TemporaryDirectory() as tmp:
        hooks = Path(tmp) / 'hooks.bin'
        subprocess.run(['vasm/vasmm68k_mot', '-quiet', '-Fbin', '-o', str(hooks),
                        str(ROOT / 'hooks.asm')], check=True)
        free(0x27b000, hooks.read_bytes())
    jump(0x3b8, '4ef900203480', 0x27b000)
    jump(0x39784, '4ef90027a1804e714e71', 0x27b080, '4e714e71')
    jump(0x39b7c, '207c0018e0f0', 0x27b0c0)

    rows = {row['id']: row for row in json.loads((V3 / 'dos_static.json').read_text())}
    layout = (ROOT.parent / 'dos/unpacked/jungle/LEVELA').read_bytes()
    sectors = []
    for index in range(70):
        at = u(0x210500 + 4 * index)
        sectors.append(list(struct.unpack_from(f'>{w(at)}I', rom, at + 2)) if at else [])

    def place_ruin(record, donor):
        y0, x0 = struct.unpack_from('>hh', rom, donor - 12)
        y1, x1 = struct.unpack_from('>hh', rom, donor + 4)
        top, left = struct.unpack_from('>hh', rom, record + 4)
        top += y0 - y1
        left += x0 - x1
        ruin = u(donor - 16)
        struct.pack_into('>4h', rom, record - 12, top, left, top+w(ruin+2), left+w(ruin))
        return [(x0-x1)*8, (y0-y1)*8]

    repaired = {}
    ruin_records = [
        (1, 0x279410, 0x1ab9ae), (82, 0x279490, 0x1ad332),
        (74, 0x27a570, 0x1ad0d4), (89, 0x27a5d0, 0x1ad0d4), (90, 0x27a630, 0x1ad0d4),
    ]
    v5_ids = json.loads((V3.parent / "eco_flight_v5/build_report.json").read_text())["new_ids"]
    ruin_records.extend((ident, 0x276000+64*i, 0x1abaf2)
                        for i, ident in enumerate(v5_ids) if 43 <= ident <= 49)
    for ident, record, donor in ruin_records:
        assert u(record) == u(donor) and u(record - 16) == u(donor - 16)
        repaired[ident] = place_ruin(record, donor)

    # Bank 16 was unused by v8 statics. Append the tower's ruin tiles to
    # its intact bank because the original ruin bank number already holds trees.
    tower_bank = 0x40
    assert not any(w(u(record)+4)==tower_bank for entries in sectors for record in entries)
    donor = 0x1b4938
    gfx, ruin_gfx = u(donor), u(donor-16)
    bank_table = u(0x525b6+7*4)
    intact_bank, ruin_bank = u(bank_table+tower_bank), u(bank_table+w(ruin_gfx+4))
    assert w(intact_bank+36) == w(ruin_bank+36) == 0x12 and w(ruin_gfx+16) == 0x1a
    graphics = unpack_tiles(rom, u(intact_bank+42), w(intact_bank+34))
    ruin_tiles = unpack_tiles(rom, u(ruin_bank+42), w(ruin_bank+34))
    source = u(ruin_gfx+22)
    aliases, attributes = {}, []
    for code in rom[source+2:source+2+w(ruin_gfx)*w(ruin_gfx+2)]:
        if code == 0:
            attributes.append(0)
            continue
        tile = (code & 63) + w(source)
        if tile not in aliases:
            aliases[tile] = len(graphics)//32
            graphics.extend(ruin_tiles[tile*32:tile*32+32])
        attributes.append(aliases[tile] | ((code&192)<<5))
    combined_bank = bytearray(rom[intact_bank:intact_bank+46])
    struct.pack_into('>HHII', combined_bank, 34, len(graphics), 2, len(graphics), 0x27d040)
    free(0x27d000, combined_bank)
    free(0x27d040, graphics)
    long(0x210100+tower_bank, 0x27d000)
    ruin_descriptor = bytearray(rom[ruin_gfx:ruin_gfx+32])
    struct.pack_into('>H', ruin_descriptor, 4, tower_bank)
    struct.pack_into('>HII', ruin_descriptor, 16, 2, 2*len(attributes), 0x27e840)
    free(0x27e800, ruin_descriptor)
    free(0x27e840, struct.pack(f'>{len(attributes)}H', *attributes))
    first_slot = w(0x210228)
    tower_ids = (38, 41, 61)
    for index, ident in enumerate(tower_ids):
        row = rows[ident]
        record = 0x27b210+64*index
        slot = first_slot+index
        free(record-16, rom[donor-16:donor+34] + b'\0\0')
        top, left = struct.unpack_from('<HH', layout, row['offset']+4)
        struct.pack_into('>4H', rom, record+4, top, left, top+w(gfx+2), left+w(gfx))
        struct.pack_into('>HHh', rom, record+16, row['y'], row['x'], row['z'])
        rom[record+22:record+25] = bytes([0x4d, slot, 0])
        long(record+30, 0xff391e+30*slot)
        place_ruin(record, donor)
        long(record-16, 0x27e800)
        sx, sy = row['x']//512, row['y']//512
        sectors[sy*10+sx].append(record)
        for ny in range(max(0,sy-1), min(7,sy+2)):
            for nx in range(max(0,sx-1), min(10,sx+2)):
                flag = 0x21400c+16*(ny*10+nx)
                long(flag, u(flag) | (1 << (tower_bank//4-1)))

    # The native event handler checks when the objective count crosses zero.
    # A/36 sets static armor to 8 times the script's value and enables damage.
    assert u(0x273100+5*4) == 0
    # Each command gets a fresh armor input: $40b96 scales D0 in place.
    script = b''.join(bytes([0, 6, 10, 0x36, 50, 1, slot, 0])
                      for slot in range(first_slot, first_slot+len(tower_ids))) + b'\0\0'
    free(0x27b340, script)
    long(0x273100+5*4, 0x27b340)
    word(0x210228, first_slot+len(tower_ids))
    at = 0x27b400
    for index, entries in enumerate(sectors):
        if entries:
            block = struct.pack(f'>H{len(entries)}I', len(entries), *entries)
            free(at, block)
            long(0x210500+4*index, at)
            at += len(block)

    terrain_tiles = restore_static_lines(rom, V3, recolor, sectors, free)
    CHECKSUM(rom)
    (ROOT / (NAME+'.bin')).write_bytes(rom)
    report = {'sha256': hashlib.sha256(rom).hexdigest(), 'ruin_offset_xy_px': repaired,
              'new_objects': list(tower_ids), 'terrain_tiles': terrain_tiles,
              'static_water_color': '0640', 'static_water_palette_slot': '1/E'}
    (ROOT / 'build_report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    build()
