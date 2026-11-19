from pathlib import Path
import hashlib
import importlib.util
import json
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
V5 = ROOT.parent / 'eco_flight_v5'
NAME = 'Jungle_Strike_Eco_Threat_Flight_TEST_v6'
spec = importlib.util.spec_from_file_location('v4_builder', ROOT.parent / 'eco_flight_v4/build.py')
v4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v4)

def build():
    b = bytearray((V5 / (NAME.replace('v6','v5') + '.bin')).read_bytes())
    assert hashlib.sha256(b).hexdigest() == '550d141349f2ba1474f21046e37c3191d86f1792a25b0a28ebffe3e67f1ab737'
    def word(p): return struct.unpack_from('>H', b, p)[0]
    def ptr(p): return struct.unpack_from('>I', b, p)[0]
    def put(p, hexcode): b[p:p+len(hexcode)//2] = bytes.fromhex(hexcode)
    with tempfile.TemporaryDirectory() as tmp:
        binary = Path(tmp)/'hooks.bin'
        subprocess.run(['vasm/vasmm68k_mot','-quiet','-Fbin','-o',str(binary),str(ROOT/'hooks.asm')],check=True)
        code = binary.read_bytes()
    b[0x278000:0x278000+len(code)] = code
    put(0x3fd26,'4ef900278000')
    put(0x3ff8a,'4ef9002781004e71')
    put(0x40592,'41ea0010224a') # remove v5's extra redraw of one landing pad
    put(0x3db02,'4eb9002781204e71')
    put(0x3ddd2,'4ef900278150')

    # Preserve every Snow Fortress color used by the native cabins. The terrain
    # remaps its nibble indices and shares only the cabin palette's free slots.
    snow = ptr(ptr(0x192942)+0x46)+32
    terrain = 0x210420
    b[terrain:terrain+32] = b[snow:snow+32]
    put(terrain+26,'0640')
    put(terrain+30,'0660')
    lut = [0,13,13,15,4,2,4,3,5,13,15,15,10,5,6,8]
    start = 0x220000
    end = start + word(0x210022)
    b[start:end] = bytes(lut[v>>4]*16+lut[v&15] for v in b[start:end])

    ids = json.loads((V5/'build_report.json').read_text())['new_ids']
    for i, ident in enumerate(ids):
        rec = 0x276000 + 64*i
        # Native armor and collision descriptor retained. Existing ruin
        # descriptors are loaded with the same bank as the player/level defaults.
        if ident in range(43,50) or ident in (67,83,84):
            donor = 0x1abaf2 if ident in range(43,50) else 0x1abed0
            assert ptr(donor-16)==0x103c4e
            b[rec-16:rec] = b[donor-16:donor]
            struct.pack_into('>4H',b,rec-12,word(rec+4),word(rec+6),word(rec+4)+word(0x103c50),word(rec+6)+word(0x103c4e))
            b[rec+22]=0x4f
        else:
            b[rec+22]=0x43 if ident==6 else 0x4b
    # Remove record 42 from the sector-owned list. The init hook installs it once.
    sector = 4*10
    listing = ptr(0x210500+sector*4)
    entries = [ptr(listing+2+4*i) for i in range(word(listing))]
    assert entries.count(0x2503e8)==1
    entries.remove(0x2503e8)
    if entries:
        struct.pack_into('>H'+'I'*len(entries),b,listing,len(entries),*entries)
    else:
        struct.pack_into('>I',b,0x210500+sector*4,0)
    put(0x3c2b4,'4eb9002782004e714e71')
    v4.checksum(b)
    (ROOT/(NAME+'.bin')).write_bytes(b)
    (ROOT/'build_report.json').write_text(json.dumps({'sha256':hashlib.sha256(b).hexdigest(),'objects':60},indent=2)+'\n')

if __name__ == '__main__':
    build()
