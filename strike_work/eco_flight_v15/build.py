"""Build Eco Threat v15 from the verified v14 and local DOS resources."""
import csv
import hashlib
import json
from pathlib import Path
import runpy
import struct
import numpy as np
from PIL import Image

root = Path(__file__).resolve().parent
work = root.parent
previous = work / 'eco_flight_v14'
rom = bytearray(next(previous.glob('*.bin')).read_bytes())
assert hashlib.sha256(rom).hexdigest() == json.loads((previous/'build_report.json').read_text())['sha256']
stock = Path('strikehd/rom/jungle_strike.bin').read_bytes()
dos = work/'dos/unpacked/jungle'
rows = list(csv.DictReader((work/'dos/eco_dynamic.csv').open()))
layout = (dos/'LEVELA').read_bytes()
def w(p): return struct.unpack_from('>H', rom, p)[0]
def u(p): return struct.unpack_from('>I', rom, p)[0]
def put(p, fmt, *values): struct.pack_into('>'+fmt, rom, p, *values)
def copy(dst, src, length): rom[dst:dst+length] = rom[src:src+length]
def members(table, sector):
    p = u(table+4*sector)
    return [u(p+2+4*j) for j in range(w(p))] if p else []

assert rom[0x2d0000:0x2e0000] == b'\xff'*65536
player = next(r for r in rows if int(r['index'])==158)
at = int(player['level_offset'],16)
assert layout[at+12:at+16] == bytes.fromhex('2800130f')
rom[0x210912] = layout[at+18]
rom[0x210916] = int(player['sector'])

# The station now uses its native tiles including the shared ground crater.
# Snap both to the same tile grid, one pixel above the v14 alignment.
station = 0x279490
for rec,donor in [(station,0x1ad332),(station-16,0x1ad332-16)]:
    g = u(donor)
    put(rec,'I',g)
    put(rec+8,'H',w(rec+4)+w(g+2))
put(station+16,'H',w(station+16)-1)
for rec in [0x27a570,0x27a5d0,0x27a630]:
    left = w(rec+6)
    put(rec-10,'H',left)
    put(rec-6,'H',left+w(u(rec-16)))
# Keep the stock bank unchanged up to its last tile and append just the wire.
bank = u(0x210100+68)
native = u(u(0x525b6+20)+68)
tile_count = w(native+34)//32
tiles = bytearray(rom[u(bank+42):u(bank+42)+tile_count*32])
indices = {}
wire = 0x2c4800
for j in range(w(wire)*w(wire+2)):
    entry = u(wire+22)+2*j
    attr = w(entry)
    idx = attr&2047
    if idx>=tile_count:
        if idx not in indices:
            indices[idx] = len(tiles)//32
            tile = u(bank+42)+32*idx
            tiles.extend(rom[tile:tile+32])
        put(entry,'H',(attr&0xf800)|indices[idx])
put(bank+34,'HHII',len(tiles),2,len(tiles),0x2c5000)
rom[0x2c5000:0x2c5000+len(tiles)] = tiles

# A sector requests banks for its anchors and the tile rectangles it intersects.
masks = [0x200]*70
def request(rec, owner):
    g = u(rec)
    if not 0<g<len(rom)-32: return
    offset = w(g+4)
    if not offset or offset%4 or offset>128: return
    top,left,bottom,right = struct.unpack_from('>4H',rom,rec+4)
    if not (0<=top<bottom<=448 and 0<=left<right<=640): return
    bit = 1<<(offset//4-1)
    masks[owner] |= bit
    for y in range(top//64,(bottom-1)//64+1):
        for x in range(left//64,(right-1)//64+1):
            masks[10*y+x] |= bit
for s in range(70):
    for rec in members(0x210500,s):
        request(rec,s)
        if rom[rec+22]&4: request(rec-16,s)
for rec in [0x2503e8]+[u(0x27f100+4*j) for j in range(7)]:
    request(rec,10*(w(rec+16)//512)+w(rec+18)//512)
for s,mask in enumerate(masks):
    put(0x21400c+16*s,'I',mask)

# Mission overlays, category filtering, blink timing and positioning remain native.
rom[0x39784:0x3978e] = bytes.fromhex('4ef90027a1804e714e71')
menu = 0x2d0000
old = u(0x212480+36)
copy(menu,old,98)
snow = u(0x212480+20)
copy(menu+98,snow+2+11*12,48)
put(menu,'H',12)
put(0x212480+36,'I',menu)
for index in range(8):
    rom[u(menu+2+12*index)]=0x60+index
put(u(menu+2)+2,'I',0x18e1f8)

# Every installed waterborne ammo drop uses campaign two's floating ammo art.
floating = 0x2d0800
copy(floating,0x18e5d6,66)
put(floating+10,'H',18)
report11 = json.loads((work/'eco_flight_v11/build_report.json').read_text())
for j,row in enumerate(report11['mission1']):
    if row['id'] in (20,21):
        put(0x291000+64*j,'I',floating)

# Install supplies present at mission start as well as the native landing zone.
known = {r['dos_index'] for r in json.loads((work/'eco_flight_v10/build_report.json').read_text())['actors']}
known.update(r['id'] for r in report11['mission1'])
known.update([18,*range(25,37),*json.loads((previous/'build_report.json').read_text())['actors']])
types = {0x9fe2:0x18e594,0xa014:0x18e618,0xa046:0x18e65a,0xaf74:0x18f6d4}
table = u(0x210242)
groups = [members(table,s) for s in range(70)]
count = w(0x210226)
slots = list(struct.unpack_from('>'+str(count)+'h',rom,u(0x21024c)))
used = u(0x210250)
added = []
for row in rows:
    i,typ = int(row['index']),int(row['type_ds'],16)
    p = int(row['level_offset'],16)
    if typ not in types or i in known or not layout[p+20]&8: continue
    assert not layout[p+21]&128
    rec = 0x2d4000+32*len(added)
    put(rec,'IIIHHh',types[typ],u(0x19ab8a+4) if typ==0xaf74 else 0,0xfffba6-used,*struct.unpack_from('<HHh',layout,p+12))
    rom[rec+18:rec+28] = layout[p+18:p+23]+bytes(5)
    groups[int(row['sector'])].append(rec)
    slots.append(-used)
    used += 14
    added.append(i)
ptr = 0x2d5000
for s,group in enumerate(groups):
    put(table+4*s,'I',ptr if group else 0)
    if group:
        put(ptr,'H'+'I'*len(group),len(group),*group)
        ptr+=2+4*len(group)
assert ptr<0x2d5800
put(0x2d5800,'h'*len(slots),*slots)
put(0x21024c,'II',0x2d5800,used)
put(0x210226,'H',len(slots))

# Snow Fortress uses this patrol for extended (mobile) helicopter slots.
# A null route is used by its stationary, short-slot counterparts.
patrol=u(0x1adfa6+4)
for group in groups:
    for rec in group:
        if u(rec)==0x18de14 and rom[rec+21]&0x80 and u(rec+4)==0:
            put(rec+4,'I',patrol)
# Share the two pattern addresses for larger Eco actors. Leave the second
# allocation pointer null, as in v13, so cleanup releases the storage once.
import subprocess, tempfile
for address in (0x43276,0x43396):
    rom[address:address+8]=stock[address:address+8]
gfx_set=set()
for group in groups:
    for rec in group:
        actor=u(rec)
        for j in range(w(actor)+1):
            g=u(actor+54+12*j)
            if g and w(g+2)>=256: gfx_set.add(g)
put(0x2dd100,'I'*(len(gfx_set)+1),*sorted(gfx_set),0)
with tempfile.TemporaryDirectory() as tmp:
    output=Path(tmp)/'sprite.bin'
    subprocess.run(['vasm/vasmm68k_mot','-quiet','-Fbin','-o',str(output),str(root/'sprites.asm')],check=True)
    code=output.read_bytes()
rom[0x2dd000:0x2dd000+len(code)]=code
for site in (0x43276,0x43396):
    rom[site:site+8]=bytes.fromhex('4e714eb9002dd000')
exec(compile((root/'cards.py').read_text(),'cards.py','exec'))
# Keep the grid bank resident across the short gap between the pad and
# the station; unloading and reallocating it here fragments pattern space.
for sector in (40,41,42,50,51,52,60,61):
    addr=0x21400c+16*sector
    put(addr,'I',u(addr)|(1<<16))
runpy.run_path(str(work/'eco_flight_v4/build.py'))['checksum'](rom)
(root/'Jungle_Strike_Eco_Threat_Flight_TEST_v15.bin').write_bytes(rom)
(root/'build_report.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),added=added,station_tiles=len(tiles)//32,heading=rom[0x210912]),indent=2))
