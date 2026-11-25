"""Correct Eco Threat collision counts and use native relocation for boat drops."""
from pathlib import Path
import csv
import hashlib
import json
import runpy
import struct

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent/'eco_flight_v11'
NAME = 'Jungle_Strike_Eco_Threat_Flight_TEST_v12'
rom = bytearray(next(OLD.glob('*.bin')).read_bytes())
report = json.loads((OLD/'build_report.json').read_text())
assert hashlib.sha256(rom).hexdigest() == report['sha256']

def word(a):
    return struct.unpack_from('>H', rom, a)[0]

def put(a, fmt, value):
    struct.pack_into('>'+fmt, rom, a, value)

for i, item in enumerate(report['icebergs']['objects']):
    descriptor = 0x292030 + i*96
    assert struct.unpack_from('>7h', rom, descriptor+20) == (0,*item['box'])
    put(descriptor+20, 'H', 1)

# The player, moving boats and relocatable crates need contiguous 42-byte
# slots for the stock engine. All other actors retain their 14-byte slots.
actors = {a['id']:a for a in report['mission1']}
crates = [actors[i]['slot'] for i in (21,20)]
longs = [0]+[actors[i]['slot'] for i in (12,13,23)]+crates
count = word(0x210226)
slots = longs+[i for i in range(count) if i not in longs]
offsets = {}
offset = 0
for slot in slots:
    offsets[slot] = -offset
    offset += 42 if slot in longs else 14
    put(0x291400+slot*2,'h',offsets[slot])
put(0x210250,'I',offset)
for slot in range(1, min(a['slot'] for a in actors.values())):
    put(0x27f400+(slot-1)*32+8,'I',0xfffba6+offsets[slot])
for i, actor in enumerate(report['mission1']):
    record = 0x291000+64*i
    slot = actor['slot']
    put(record+8,'I',0xfffba6+offsets[slot])
    if slot in crates:
        rom[record+21] |= 0x80
    if actor['id'] in (12,13):
        at = record+26
        crate = crates[(12,13).index(actor['id'])]
        original = bytes([0x16,4,2,0x1a,1,1,0x16,4,6,6,1,crate,0,0])
        assert rom[at:at+14] == original
        rom[at:at+20] = bytes([0x16,4,6,0x42,1,crate])+original
# The stock boat sprite list starts with its turret, followed by its hull.
# Give the three Eco boats the dish component of the native mobile radar.
boat = 0x298000
assert rom[boat:boat+96] == bytes([255])*96
rom[boat:boat+96] = rom[0x18dc5a:0x18dc5a+96]
# The DOS radar boat has group 61 and no weapon controller.
put(boat+6,"H",61)
put(boat+10,"H",0)
put(boat+28,"H",0)
put(boat+30,"I",0)
rom[boat+54:boat+66] = rom[0x18cde6+54:0x18cde6+66]
for i in range(3):
    put(0x291000+64*i,'I',boat)
def ptr(address):
    return struct.unpack_from('>I', rom, address)[0]

# The original DOS far pointer resolves into the MZ load image.
exe = (ROOT.parent/'dos/unpacked/jungle/EXECUTABLE').read_bytes()
mz = exe[16*struct.unpack_from('<H',exe,8)[0]:]
route = mz[0x26837:0x26837+36]
assert route == rom[0x1927aa:0x1927aa+36]
for i in range(3):
    put(0x291000+64*i+4,'I',0x1927aa)
card = ptr(ptr(0x212480+36)+2)
put(card+6,'I',boat)
# DOS and Genesis share the same rectangular Danger Zone command.
level = (ROOT.parent/'dos/unpacked/jungle/LEVELA').read_bytes()
with (ROOT.parent/'dos/eco_dynamic.csv').open() as source:
    dos = {int(r['index']): r for r in csv.DictReader(source)}
for i, actor in enumerate(report['mission1']):
    ident = actor['id']
    if ident not in (5,9,12,13,23):
        continue
    old = 0x291000+i*64
    cursor = old+26
    while rom[cursor]:
        cursor += 2+rom[cursor+1]
    definition = bytearray(rom[old:cursor])
    cursor = int(dos[ident]['script_offset'],16)
    while level[cursor]:
        event,length = level[cursor:cursor+2]
        data = level[cursor+2:cursor+2+length]
        if data[:2] == bytes([2,0x26]):
            fields = struct.unpack('<HBBHHII',data[2:])
            definition.extend(bytes([event,length,2,0x26])+struct.pack('>HBBHHII',*fields))
        cursor += 2+length
    definition.extend(bytes(2))
    new = 0x298200+i*128
    assert len(definition)<=128 and rom[new:new+128] == bytes([255])*128
    rom[new:new+len(definition)] = definition
    group = ptr(ptr(0x210242)+4*actor['sector'])
    entries = [group+2+4*j for j in range(word(group))]
    address, = (entry for entry in entries if ptr(entry)==old)
    put(address,'I',new)
runpy.run_path(str(ROOT.parent/'eco_flight_v4/build.py'))['checksum'](rom)
(ROOT/(NAME+'.bin')).write_bytes(rom)
(ROOT/'build_report.json').write_text(json.dumps({'sha256':hashlib.sha256(rom).hexdigest(),'offsets':offsets},indent=2))
