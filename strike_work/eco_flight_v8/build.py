from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import struct
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parent
V3=ROOT.parent/'eco_flight_v3'
V7=ROOT.parent/'eco_flight_v7'
DOS=ROOT.parent/'dos/unpacked/jungle'
NAME='Jungle_Strike_Eco_Threat_Flight_TEST_v8'
spec=importlib.util.spec_from_file_location('v4_builder',ROOT.parent/'eco_flight_v4/build.py')
v4=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v4)

def build(cycle=True):
    rom=bytearray((V7/(NAME.replace('v8','v7')+'.bin')).read_bytes())
    assert hashlib.sha256(rom).hexdigest()=='9abdb30c8f6ecca13d61da2aa12e67f6677680558bff78d103735d4e6ebfd43f'
    def w(p): return struct.unpack_from('>H',rom,p)[0]
    def u(p): return struct.unpack_from('>I',rom,p)[0]
    def word(p,v): struct.pack_into('>H',rom,p,v)
    def long(p,v): struct.pack_into('>I',rom,p,v)
    def patch(p,old,new):
        expected=bytes.fromhex(old)
        assert rom[p:p+len(expected)]==expected,hex(p)
        replacement=bytes.fromhex(new)
        assert len(replacement)==len(expected)
        rom[p:p+len(expected)]=replacement
    with tempfile.TemporaryDirectory() as tmp:
        out=Path(tmp)/'hooks.bin'
        subprocess.run(['vasm/vasmm68k_mot','-quiet','-Fbin','-o',str(out),str(ROOT/'hooks.asm')],check=True)
        code=out.read_bytes()
    rom[0x27a000:0x27a000+len(code)]=code
    if cycle:
        patch(0x39392,'610058fa4a00','4eb90027a000')
    patch(0x3db78,'4eb900211000','4eb90027a080')
    patch(0x3c62c,'917900ff10c6','4eb90027a140')
    patch(0x4192e,'082d0001000f','4ef90027a0c0')
    patch(0x41762,'082d00060008','4ef90027a100')
    patch(0x279080,'0c79000900ff139e','4e714e714e714e71')
    patch(0x39784,'48e7fffc303900ff1022','4ef90027a1804e714e71')

    static_rows={r['id']:r for r in json.loads((V3/'dos_static.json').read_text())}
    tree_and_pad=json.loads((V3/'object_positions.json').read_text())
    extra=json.loads((ROOT.parent/'eco_flight_v5/build_report.json').read_text())['new_ids']
    records={r['id']:0x250000+i*40 for i,r in enumerate(tree_and_pad)}
    records.update({ident:0x276000+i*64 for i,ident in enumerate(extra)})
    records.update({ident:0x279410+64*i for i,ident in enumerate([1,73,82])})
    layout=(DOS/'LEVELA').read_bytes()
    table=0x210500
    sector_lists=[]
    for sector in range(70):
        p=u(table+4*sector)
        sector_lists.append([u(p+2+4*j) for j in range(w(p))] if p else [])

    wire_types={0xb136:0x1acf2c,0xb151:0x1ad058,0xb16c:0x1acf50}
    additions={5:0x1ac33e,74:0x1ad0d4,89:0x1ad0d4,90:0x1ad0d4}
    for ident in (65,66,85,86,87,88):
        additions[ident]=wire_types[static_rows[ident]['type']]
    slots={}
    for i,(ident,donor) in enumerate(additions.items()):
        row=static_rows[ident]
        record=0x27a510+i*96
        slots[ident]=64+i
        records[ident]=record
        gfx=u(donor)
        top,left=struct.unpack_from('<HH',layout,row['offset']+4)
        rom[record:record+34]=rom[donor:donor+34]
        # Keep the native anchor relative to the graphic so the collision
        # definition stays lined up, including pylons with shifted DOS origins.
        x=w(donor+18)+8*(left-w(donor+6))
        y=w(donor+16)+8*(top-w(donor+4))
        struct.pack_into('>4H',rom,record+4,top,left,top+w(gfx+2),left+w(gfx))
        struct.pack_into('>HH',rom,record+16,y,x)
        destructible=ident in (74,89,90)
        rom[record+22]=0x4f if destructible else (0x40 if ident==5 else 0x49)
        rom[record+23]=slots[ident]
        long(record+30,0xff391e+30*slots[ident])
        word(record+34,0)
        if destructible:
            ruin=u(donor-16)
            rom[record-16:record]=rom[donor-16:donor]
            struct.pack_into('>4H',rom,record-12,top,left,top+w(ruin+2),left+w(ruin))
        bank=w(gfx+4)
        long(0x210100+bank,u(u(0x525b6+20)+bank))
        sx,sy=x//512,y//512
        sector_lists[10*sy+sx].append(record)
        for ny in range(max(0,sy-1),min(7,sy+2)):
            for nx in range(max(0,sx-1),min(10,sx+2)):
                mask=0x21400c+16*(10*ny+nx)
                long(mask,u(mask)|(1<<(bank//4-1)))

    # These natives consume references to Eco Threat's live static indices.
    object_links=json.loads((ROOT.parent/'dos/eco_objectives.json').read_text())['object_links']
    for ident in (74,89,90):
        p=records[ident]+34
        links={}
        for event in object_links[str(ident)]:
            if event['event']==22 and event['operation'].startswith('0a'):
                op=int(event['operation'][-2:],16)
                if op==0x16: op=0x0a  # Genesis deactivates passive wire tiles without a nested destruction event
                links.setdefault(op,set()).update(event['map_ids'])
        script=bytearray()
        for op,targets in links.items():
            for target in sorted(targets):
                script.extend(bytes([0x16,4,0x0a,op,1,rom[records[target]+23]]))
        script.extend(b'\0\0')
        assert len(script)<=46
        rom[p:p+len(script)]=script
    p=records[6]+34
    rom[p:p+8]=bytes([0x16,4,0x0a,6,1,slots[5],0,0])
    address=0x27a900
    for sector,entries in enumerate(sector_lists):
        if entries:
            packed=struct.pack('>H'+'I'*len(entries),len(entries),*entries)
            rom[address:address+len(packed)]=packed
            long(table+4*sector,address)
            address+=len(packed)
    word(0x210228,64+len(additions))

    # DOS menu entries (DS:3f64), overlay table (DS:3f78), renderer 5420.
    # Only two of the fixed DOS targets have an equivalent live object here.
    exe=(DOS/'EXECUTABLE').read_bytes()
    def le(b,p): return struct.unpack_from('<H',b,p)[0]
    image=exe[16*le(exe,8):]
    ds=image[16*le(image,4):]
    menu=le(ds,0x3f64+18)
    overlay=le(ds,0x3f78+18)
    assert le(ds,menu-2)==8
    menu_gen=u(0x212480+36)
    for record in records.values():
        rom[record+24]=0
    targets={2:(42,(470,2540)),3:(82,(432,3337))}
    for mission,(ident,position) in targets.items():
        i=ds[menu+2+8*(mission-1)+7]
        rom[menu_gen+2+12*(mission-1)+9]=ds[menu+2+8*(mission-1)+5]
        entry=le(ds,overlay+4*i)
        assert le(ds,entry)==1
        _,x,y,flags=struct.unpack_from('<hhhh',ds,entry+2)
        assert (x,y)==position and flags&0x100
        rom[records[ident]+24]=mission
    v4.checksum(rom)
    (ROOT/(NAME+'.bin')).write_bytes(rom)
    (ROOT/'build_report.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),campaign_cycle=cycle,new_objects=list(additions),map_targets=list(targets)),indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--without-campaign-cycle',action='store_true')
    build(not parser.parse_args().without_campaign_cycle)
