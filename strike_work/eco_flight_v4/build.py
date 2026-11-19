"""Build Eco Threat v4 on the reproducible v3 test ROM, using local DOS assets."""
from pathlib import Path
import hashlib
import json
import struct
import textwrap

ROOT = Path(__file__).resolve().parent
V3 = ROOT.parent / 'eco_flight_v3'
DOS = ROOT.parent / 'dos/unpacked/jungle'
NAME = 'Jungle_Strike_Eco_Threat_Flight_TEST_v4'

def checksum(b):
    internal = sum(v for (v,) in struct.iter_unpack('>I', b[:2093788])) - int.from_bytes(b[0x18c:0x190], 'big')
    struct.pack_into('>I', b, 2093816, internal & 0xffffffff)
    struct.pack_into('>H', b, 0x18e, sum(v for (v,) in struct.iter_unpack('>H',b[512:])) & 0xffff)

def build():
    b = bytearray(next(V3.glob('*v3.bin')).read_bytes())
    assert hashlib.sha256(b).hexdigest() == '3be3c8dd5d6d1ae080abacc252f9d922f79501dbfc0a38c89a4f422fcb5027fc'
    # Front-end text commands (ink, column, row, C string); keep CAMPAIGN alone.
    title = b'\x00\x1a\x08  \0\x02\x09\x0a10.ECO THREAT\0\xff'
    b[0x213f00:0x213f00+len(title)] = title
    level = (DOS/'LEVELA').read_bytes()
    objs = json.loads((V3/'object_positions.json').read_text())
    for i, row in enumerate(objs):
        record = 0x250000 + i*40
        gfx = struct.unpack_from('>I',b,record)[0]
        width,height = struct.unpack_from('>HH',b,gfx)
        top,left = struct.unpack_from('<HH',level,row['offset']+4)
        struct.pack_into('>4H', b,record+4,top,left,top+height,left+width)
    # The DOS resource holds three NUL-separated strings for each objective.
    data = (DOS/'FLICDATA').read_bytes()
    start = data.index(b'RADAR STATIONS\0EARLY WARNING MOBILE RADAR\x001. Destroy the radar stations')
    fields = data[start:].split(b'\0',24)[:24]
    thresholds = json.loads((ROOT.parent/'dos/eco_objectives.json').read_text())['objective_thresholds']
    payload = bytearray()
    base = 0x270000
    def append(value):
        if len(payload)%2: payload.append(0)
        offset = base+len(payload)
        payload.extend(value)
        return offset
    counts = append(struct.pack('>8H',*thresholds))
    struct.pack_into('>I', b,0x21022a,counts)
    b[0x210222] |= 2   # sequential disclosure used by Return Home
    entries = bytearray(struct.pack('>H',8))
    status = bytearray(struct.pack('>H',7))
    for i in range(8):
        name,brief,full = (s.decode('ascii') for s in fields[i*3:i*3+3])
        assert full.startswith(f'{i+1}. ')
        label = append(bytes([max(0,(16-len(name)-2)//2)])+f'{i+1}.{name}'.encode()+b'\0')
        # Native map icon descriptor is shared; no map targets exist yet.
        desc = bytearray(struct.pack('>BBII',0,2,0x18e342,0))
        for style,x,y,width,value in [(2,19,5,12,brief),(3,7,15,24,full)]:
            lines = textwrap.wrap(value,width)
            assert len(lines)<=9
            for j,line in enumerate(lines):
                desc.extend(bytes([style,x,y+j])+line.encode()+b'\0')
        desc.append(255)
        entries.extend(struct.pack('>II4B',append(desc),label,i+1,0,3,0))
        status.extend(bytes([0,7,7+2*i])+name.encode()+b':\0'+bytes([2,1,1,0,thresholds[i],255]))
    entries_ptr = append(entries)
    status_ptr = append(status)
    struct.pack_into('>I',b,0x212480+36,entries_ptr)
    struct.pack_into('>I',b,0x212280+36,status_ptr)
    assert all(v==255 for v in b[base:base+len(payload)])
    b[base:base+len(payload)] = payload
    assert b[0x3fd26:0x3fd2c]==bytes.fromhex('0c6e001a0010')
    # Assembled from wrap.asm with vasmm68k_mot -Fbin.
    seam = bytes.fromhex('bdfc00260100665c2f073e000247003f444706470040be426c1c3f072e2f000248e7fffe342f003c61d64cdf7fff3e1fd047d84794473e010247003f444706470040be436c1c3f072e2f000248e7fffe362f003c610e4cdf7fff3e1fd247da4796472e1f0c6e001a00104ef90003fd2c')
    assert all(v==255 for v in b[0x272000:0x272000+len(seam)])
    b[0x272000:0x272000+len(seam)] = seam
    b[0x3fd26:0x3fd2c] = bytes.fromhex('4ef900272000')
    checksum(b)
    (ROOT/(NAME+'.bin')).write_bytes(b)
    (ROOT/'build_report.json').write_text(json.dumps(dict(sha256=hashlib.sha256(b).hexdigest(),size=len(b),objects=len(objs),objectives=8),indent=2)+'\n')
if __name__=='__main__':
    build()
