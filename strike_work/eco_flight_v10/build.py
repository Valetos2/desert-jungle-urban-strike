"""Build the Eco Threat v10 flight test on the verified v9 prototype."""
import csv
import hashlib
import json
from pathlib import Path
import runpy
import struct
import subprocess
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent
NAME = 'Jungle_Strike_Eco_Threat_Flight_TEST_v10'
PREVIOUS = ROOT.parent / 'eco_flight_v9' / 'Jungle_Strike_Eco_Threat_Flight_TEST_v9.bin'
CHECKSUM = runpy.run_path(str(ROOT.parent / 'eco_flight_v4/build.py'))['checksum']
WIRES = tuple(0x27a690 + i * 96 for i in range(6))
ACTOR_TYPES = {
    0xa4e6: 0x1add6e,  # Rocket infantry
    0xa55e: 0x1adee0,  # Ground infantry
    0xb0a8: 0x1ada98,  # Elevated tower gunner
    0x9fe2: 0x1adf3a,  # Ammo
    0xa014: 0x1adf1e,  # Fuel
}
ACTORS = (0, 2, 3, 77, 99, 100, 107, 130, 131, 136, 137, 145, 159, 160)


def build():
    rom = bytearray(PREVIOUS.read_bytes())
    assert hashlib.sha256(rom).hexdigest() == '88266c5ffb1fb3a5390cfa7d452d251d14bc3a36bc314f8cdc28d65c07466717'

    def word(p):
        return struct.unpack_from('>H', rom, p)[0]

    def long(p):
        return struct.unpack_from('>I', rom, p)[0]

    def put(p, fmt, *values):
        struct.pack_into('>' + fmt, rom, p, *values)

    def free(p, data):
        assert rom[p:p+len(data)] == b'\xff' * len(data), hex(p)
        rom[p:p+len(data)] = data

    # Restore the original special player icon. The v9 numbered-target filter
    # at $39784 is separate and still blocks the selected-category overlay.
    assert rom[0x39b7c:0x39b82] == bytes.fromhex('4ef90027b0c0')
    rom[0x39b7c:0x39b82] = bytes.fromhex('207c0018e0f0')

    # A wire can cross sector boundaries. Keep its live slot in the static
    # renderer, like v6 does for the wide landing pad. Destruction still clears
    # the original live entry through the existing pylon scripts.
    with TemporaryDirectory() as tmp:
        binary = Path(tmp) / 'hooks.bin'
        subprocess.run(['vasm/vasmm68k_mot', '-quiet', '-Fbin', '-o', str(binary),
                        str(ROOT / 'hooks.asm')], check=True)
        free(0x27f000, binary.read_bytes())
    assert rom[0x3c2b4:0x3c2ba] == bytes.fromhex('4eb900278200')
    put(0x3c2b6, 'I', 0x27f000)
    free(0x27f100, struct.pack('>6I', *WIRES))
    moved = []
    for sector in range(70):
        entry = long(0x210500+4*sector)
        if not entry:
            continue
        records = struct.unpack_from(f'>{word(entry)}I', rom, entry+2)
        kept = [record for record in records if record not in WIRES]
        if len(kept) != len(records):
            moved.extend(record for record in records if record in WIRES)
            if kept:
                put(entry, f'H{len(kept)}I', len(kept), *kept)
            else:
                put(0x210500+4*sector, 'I', 0)
    assert sorted(moved) == list(WIRES)

    # Copy each native actor definition without its campaign scripts. The
    # DOS coordinates, activation flag and headings are read from Eco Threat.
    with (ROOT.parent / 'dos/eco_dynamic.csv').open(newline='') as stream:
        rows = {int(row['index']): row for row in csv.DictReader(stream)}
    layout = (ROOT.parent / 'dos/unpacked/jungle/LEVELA').read_bytes()
    assert hashlib.sha256(layout).hexdigest() == '942ce5a037ceb034ca16af09fb76c665b00579100c8260fbf8e958c157d5740c'
    player_list = long(0x210700+7*4)
    assert word(player_list) == 1
    groups = {7: [long(player_list+2)]}
    actor_report = []
    for slot, index in enumerate(ACTORS, 1):
        row = rows[index]
        typ = int(row['type_ds'], 16)
        donor = ACTOR_TYPES[typ]
        offset = int(row['level_offset'], 16)
        y, x, z = struct.unpack_from('<HHh', layout, offset+12)
        flags = (rom[donor+20] & ~8) | (layout[offset+20] & 8)
        record = 0x27f400 + (slot-1)*0x20
        # The player occupies the first $2a-byte slot, these use $0e.
        delta = -0x2a-0x0e*(slot-1)
        free(record, struct.pack('>IIIHHh6BH', long(donor), 0, 0xfffba6+delta,
                                 y, x, z, layout[offset+18], layout[offset+19],
                                 flags, rom[donor+21], y//512*10+x//512, 0, 0) + b'\0\0\0\0')
        groups.setdefault(y//512*10+x//512, []).append(record)
        actor_report.append({'dos_index': index, 'slot': slot, 'offset': delta,
                             'xy': [x,y], 'height': z, 'type': f'{typ:04x}'})

    dynamic_table = 0x27f800
    start = dynamic_table + 70*4
    table = [0]*70
    for sector, records in sorted(groups.items()):
        data = struct.pack(f'>H{len(records)}I', len(records), *records)
        free(start, data)
        table[sector] = start
        start += len(data)
    free(dynamic_table, struct.pack('>70I', *table))
    put(0x210242, 'I', dynamic_table)
    slot_table = 0x27f980
    free(slot_table, struct.pack(f'>{len(ACTORS)+1}h', 0, *(r['offset'] for r in actor_report)))
    put(0x21024c, 'I', slot_table)
    put(0x210226, 'H', len(ACTORS)+1)
    put(0x210250, 'I', 0x2a+0x0e*len(ACTORS))

    # Mission-independent pickups inside mounds use the native activation
    # command. The tower destroys its own gunner when the structure collapses.
    for record, indices, operation in (
        (0x279410, (77,), 0x12),
        (0x276000, (99,100), 6),
        (0x276080, (107,), 6),
    ):
        if record != 0x279410:
            assert long(record) == 0x10f484
        assert rom[record+34:record+36] == b'\0\0'
        script = bytes([0x16, 4+len(indices), 6, operation, len(indices),
                        *(ACTORS.index(i)+1 for i in indices), 0, 0])
        rom[record+34:record+34+len(script)] = script

    CHECKSUM(rom)
    (ROOT / (NAME+'.bin')).write_bytes(rom)
    report = {'sha256': hashlib.sha256(rom).hexdigest(), 'actors': actor_report,
              'persistent_wire_slots': [rom[record+23] for record in WIRES]}
    (ROOT/'build_report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    build()
