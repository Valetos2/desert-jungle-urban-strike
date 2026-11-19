from pathlib import Path
import hashlib
import importlib.util
import json
import struct
import subprocess
import tempfile
from terrain import recolor
from briefing import install
from scenery import install as install_scenery

ROOT=Path(__file__).resolve().parent
PREV=ROOT.parent/'eco_flight_v6'
V3=ROOT.parent/'eco_flight_v3'
V5=ROOT.parent/'eco_flight_v5'
NAME='Jungle_Strike_Eco_Threat_Flight_TEST_v7'
spec=importlib.util.spec_from_file_location('v4_builder',ROOT.parent/'eco_flight_v4/build.py')
v4=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v4)

def build():
    rom=bytearray((PREV/(NAME.replace('v7','v6')+'.bin')).read_bytes())
    assert hashlib.sha256(rom).hexdigest()=='348cfe1e35c91897e1537490868f26acf696b36e1a6aa52875c3874d76b05c98'
    def long(p,v): struct.pack_into('>I',rom,p,v)
    def word(p,v): struct.pack_into('>H',rom,p,v)
    with tempfile.TemporaryDirectory() as tmp:
        out=Path(tmp)/'hooks.bin'
        subprocess.run(['vasm/vasmm68k_mot','-quiet','-Fbin','-o',str(out),str(ROOT/'hooks.asm')],check=True)
        payload=out.read_bytes()
    rom[0x279000:0x279000+len(payload)]=payload
    long(0x3ddd4,0x279000)
    # Replace the ammo decrement and leave the original branch target intact.
    assert rom[0x44bd8:0x44be6]==bytes.fromhex('082b0004001466000006536b0012')
    rom[0x44bde:0x44be6]=bytes.fromhex('66064eb900279080')

    rows=json.loads((V3/'object_positions.json').read_text())
    extra=json.loads((V5/'build_report.json').read_text())['new_ids']
    for i in range(len(rows)+len(extra)):
        record=0x250000+40*i if i<len(rows) else 0x276000+64*(i-len(rows))
        # The collision renderer writes this byte into the broad-phase grid,
        # which resolves it against this level's 30-byte runtime slots.
        rom[record+23]=i
    long(0x210100+18*4,0x71560)
    for i,row in enumerate(rows):
        if row['name']=='F174': long(0x250000+40*i,0x10f8f4)
    # Standard Snow Fortress palette, with independent static sea and wave colors.
    word(0x210420+26,0x0440)
    word(0x210420+30,0x0640)
    patterns,terrain=recolor(rom,V3)
    rom[0x220000:0x220000+len(patterns)]=patterns
    word(0x210022,len(patterns))
    long(0x210026,len(patterns))
    rom[0x300000:0x300000+len(terrain)]=terrain
    install(rom)
    table_operand = rom.index(bytes.fromhex("0019292e"), 0x200600, 0x200800)
    long(table_operand, 0x212000)
    added = install_scenery(rom, V3, (ROOT.parent/"dos/unpacked/jungle/LEVELA").read_bytes())
    v4.checksum(rom)
    (ROOT/(NAME+'.bin')).write_bytes(rom)
    (ROOT/'build_report.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),terrain_tiles=len(patterns)//32, new_objects=added),indent=2)+'\n')

if __name__=='__main__':
    build()
