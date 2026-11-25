"""Build the next Eco Threat flight prototype from the verified v10 ROM."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import struct

import numpy as np

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
DOS = WORK/'dos/unpacked/jungle'
NAME = 'Jungle_Strike_Eco_Threat_Flight_TEST_v11'
BASE = WORK/'eco_flight_v10'/f'{NAME[:-2]}10.bin'
CHECKSUM = runpy.run_path(str(WORK/'eco_flight_v4/build.py'))['checksum']
TARGETS = (5, 9, 12, 13, 23)
SUPPORT = (6, 7, 10, 11, 20, 21)
ICE = ((9, 10), (26, 27), (76, 77), (94, 95))


def build():
    rom = bytearray(BASE.read_bytes())
    assert hashlib.sha256(rom).hexdigest()=='b62757f308158d61af9edea0d36b62723d8c9f8864fa113ab87033fbeeca0603'
    layout=(DOS/'LEVELA').read_bytes()
    assert hashlib.sha256(layout).hexdigest()=='942ce5a037ceb034ca16af09fb76c665b00579100c8260fbf8e958c157d5740c'

    def w(at):
        return struct.unpack_from('>H',rom,at)[0]

    def u(at):
        return struct.unpack_from('>I',rom,at)[0]

    def put(at, fmt, *values):
        struct.pack_into('>'+fmt,rom,at,*values)

    def free(at, data):
        assert rom[at:at+len(data)]==b'\xff'*len(data),hex(at)
        rom[at:at+len(data)]=data

    # The Genesis collision descriptor is relative to the donor's anchor.
    pads = json.loads((WORK/'eco_flight_v3/object_positions.json').read_text())
    pad_offsets = {}
    for i,row in enumerate(pads):
        if row['name']!='F174':
            continue
        rec=0x250000+40*i
        donor=row['donor']
        dy=(w(rec+4)-w(donor+4))*8
        dx=(w(rec+6)-w(donor+6))*8
        y,x=w(donor+16)+dy,w(donor+18)+dx
        pad_offsets[row['id']]=[x-w(rec+18),y-w(rec+16)]
        put(rec+16,'HH',y,x)

    # Recolour tower tiles containing windows through palette 2. Only those
    # tiles switch palettes. The rest of the tower keeps its v10 colours.
    gfx=0x112e8c
    bank=0x27d000
    art=0x27d040
    size=w(bank+34)
    patterns=np.frombuffer(rom[art:art+size],np.uint8)
    pixels=np.stack((patterns>>4,patterns&15),axis=-1).reshape(-1,64)
    tilemap=u(gfx+22)
    attrs=list(struct.unpack_from('>320H',rom,tilemap))
    alternate=[]
    # 0 is transparent. Greens in row 2 are slots 9 ($0242) and A ($0464).
    convert=np.array([0,1,1,1,1,2,2,3,4,5,10,10,11,3,10,9],np.uint8)
    converted={}
    for i,attr in enumerate(attrs):
        tile=attr&0x7ff
        if not np.isin(pixels[tile],(14,15)).any():
            continue
        if tile not in converted:
            px=convert[pixels[tile]]
            converted[tile]=size//32+len(alternate)
            alternate.append((px[::2]*16+px[1::2]).tobytes())
        attrs[i]=(attr&0xf800)+0x2000+converted[tile]
    assert converted
    extra=b''.join(alternate)
    free(art+size,extra)
    put(bank+34,'HHI',size+len(extra),2,size+len(extra))
    new_gfx=0x290000
    desc=bytearray(rom[gfx:gfx+32])
    struct.pack_into('>I',desc,22,0x290040)
    free(new_gfx,desc)
    free(0x290040,struct.pack('>320H',*attrs))
    for rec in (0x27b210,0x27b250,0x27b290):
        put(rec,'I',new_gfx)

    # The objective counter is incremented by each of the five DOS script
    # contributors. Support units do not increment that counter.
    with (WORK/'dos/eco_dynamic.csv').open(newline='') as stream:
        rows={int(r['index']):r for r in csv.DictReader(stream)}
    dynamic=[]
    prior=u(0x210242)
    for sector in range(70):
        entry=u(prior+4*sector)
        dynamic.append(list(struct.unpack_from(f'>{w(entry)}I',rom,entry+2)) if entry else [])
    slots=u(0x21024c)
    count=w(0x210226)
    offsets=list(struct.unpack_from(f'>{count}h',rom,slots))
    used=u(0x210250)
    # The native map walks 42-byte live slots before 14-byte ones. Allocate
    # a new contiguous block after the player, and relocate the v10 short slots.
    moving=(12,13,23)
    for i in range(1,count):
        offsets[i]-=len(moving)*42
        put(0x27f400+0x20*(i-1)+8,'I',0xfffba6+offsets[i])
    used+=len(moving)*42
    indices={}
    actor_info=[]
    new_ids=moving+(5,9)+SUPPORT
    links={5:(6,),9:(10,),12:(21,),13:(20,)}
    for i,index in enumerate(new_ids):
        row=rows[index]
        at=int(row['level_offset'],16)
        y,x,z=struct.unpack_from('<HHh',layout,at+12)
        if index in moving:
            delta=-42*(moving.index(index)+1)
        else:
            delta=-used
            used+=14
        indices[index]=len(offsets)
        offsets.append(delta)
        sector=10*(y//512)+x//512
        record=0x291000+64*i
        dynamic[sector].append(record)
        natives={5:0x18cde6,9:0x18cde6,6:0x18edb4,10:0x18d9c2,
                 7:0x190150,11:0x190150,20:0x18e594,21:0x18e594}
        native=0x18dc5a if index in moving else natives[index]
        route=0
        if index in moving:
            route=0x291500+32*moving.index(index)
            # Short repeating native boat patrol. Use different initial
            # headings so all three targets do not steer in lockstep.
            patrol=struct.pack('>24x4H',0x4001,0x2805,0x4001,0)
            free(route,bytes([1,255])+patrol[2:])
        flags=0x4b if layout[at+20]&8 else 0x43
        properties=0x80 if index in moving else 0
        content=struct.pack('>IIIHHh6B2B',native,route,0xfffba6+delta,y,x,z,*layout[at+18:at+20],flags,properties,sector,int(index in TARGETS),0,0)
        script=bytearray()
        if index in TARGETS:
            script.extend(bytes([0x16,4,2,0x1a,1,1]))
        if index in links:
            target=links[index][0]
            event=0x0e if index in (5,9) else 0x16
            script.extend(bytes([event,4,6,6,1,count+new_ids.index(target)]))
        free(record,content+script+b'\0\0')
        actor_info.append({'id':index,'position':[x,y,z],'slot':indices[index],'offset':delta,'sector':sector})

    offset_at=0x291400
    free(offset_at,struct.pack(f'>{len(offsets)}h',*offsets))
    put(0x21024c,'I',offset_at)
    put(0x210226,'H',len(offsets))
    put(0x210250,'I',used)
    cursor=0x291600
    for sector, entries in enumerate(dynamic):
        if entries:
            entry=struct.pack(f'>H{len(entries)}I',len(entries),*entries)
            free(cursor,entry)
            put(prior+4*sector,'I',cursor)
            cursor+=len(entry)

    # Use the stock radar preview in the information card and preserve DOS text.
    menu=u(0x212480+36)
    card=u(menu+2)
    native_card=0xe9d40  # Snow Fortress: RADAR SITES
    assert u(native_card+6)==0x18cde6
    put(card+6,'I',u(native_card+6))

    stats=json.loads((WORK/'eco_flight_v3/dos_static.json').read_text())
    iceberg_info=install_ice(rom,layout,stats,free,put,w,u)
    CHECKSUM(rom)
    (ROOT/(NAME+'.bin')).write_bytes(rom)
    report={'sha256':hashlib.sha256(rom).hexdigest(),'pad_offsets':pad_offsets,
            'tower_window_tiles':len(converted),'mission1':actor_info,'icebergs':iceberg_info}
    (ROOT/'build_report.json').write_text(json.dumps(report,indent=2)+'\n')


def install_ice(rom,layout,stats,free,put,w,u):
    spec=importlib.util.spec_from_file_location('dos_graphics',WORK/'dos/color_experiment/preview.py')
    converter=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(converter)

    # Snow terrain palette has the closest ice shades with no animated slots.
    colors=np.array([[(w(0x210400+2*i)>>j)&7 for j in (1,5,9)] for i in range(16)])
    rgb=converter.DAC[colors].astype(int)
    tiles=[bytes(32)]
    aliases={tiles[0]:0}
    sizes=[]
    bank_slot=12
    bank_mask=1<<(bank_slot-1)
    assert all(not u(0x21400c+s*16)&bank_mask for s in range(70))
    desc_address=0x293000
    raw_address=0x294000
    records={r['id']:r for r in stats}
    things=(DOS/'THINGS').read_bytes()
    for frame in range(3):
        art,palette=converter.sprite('ICEBERGS',frame)
        nearest=((palette.astype(int)[:,None,:]-rgb[None,1:,:])**2).sum(axis=2).argmin(axis=1)+1
        nearest[0]=0
        image=nearest[art].astype(np.uint8)
        h,ww=image.shape
        words=[]
        for y in range(0,h,8):
            for x in range(0,ww,8):
                px=image[y:y+8,x:x+8].ravel()
                packed=(px[::2]*16+px[1::2]).tobytes()
                if packed not in aliases:
                    aliases[packed]=len(tiles)
                    tiles.append(packed)
                words.append(aliases[packed])
        addr=desc_address+frame*0x300
        source=addr+0x40
        gfx=bytearray(rom[0x112e8c:0x112e8c+32])
        struct.pack_into('>HHH',gfx,0,ww//8,h//8,bank_slot*4)
        struct.pack_into('>HII',gfx,16,2,len(words)*2,source)
        struct.pack_into('>H',gfx,30,0)
        free(addr,gfx)
        free(source,struct.pack(f'>{len(words)}H',*words))
        sizes.append((ww//8,h//8,addr))
    data=b''.join(tiles)
    descriptor=bytearray(rom[0x27d000:0x27d000+46])
    # Separate the live allocation descriptor from the existing tower bank.
    struct.pack_into('>I',descriptor,6,0xff188a)
    struct.pack_into('>HHII',descriptor,34,len(data),2,len(data),raw_address)
    free(0x293a00,descriptor)
    free(raw_address,data)
    put(0x210100+4*bank_slot,'I',0x293a00)
    prior=0x210500
    groups=[]
    for s in range(70):
        entry=u(prior+4*s)
        groups.append(list(struct.unpack_from(f'>{w(entry)}I',rom,entry+2)) if entry else [])
    first=w(0x210228)
    infos=[]
    for i,ident in enumerate(sum(ICE,())):
        row=records[ident]
        x,y,z=row['x'],row['y'],row['z']
        shape=struct.unpack_from('<6h',things,row["type"]+15)
        frame=(row['type']-0xc6fc)//27
        assert frame in range(3)
        width,height,gfx=sizes[frame]
        top,left=struct.unpack_from('<HH',layout,row['offset']+4)
        rec=0x292000+i*96
        slot=first+i
        collision=rec+48
        # Native collision descriptor: allow damage, leave no permanent ruin,
        # and retain the DOS box and height relative to the object's anchor.
        native=bytearray(rom[0x11a3e6:0x11a3e6+34])
        native[8]=3
        struct.pack_into('>H',native,10,200)
        struct.pack_into('>7h',native,20,0,*shape)
        free(collision,native)
        template=bytearray(rom[0x279410:0x279410+34])
        struct.pack_into('>I4H',template,0,gfx,top,left,top+height,left+width)
        struct.pack_into('>HHhBBBBII',template,16,y,x,z,0x4b if i%2==0 else 0x43,slot,0,0,collision,0xff391e+30*slot)
        script=bytes([0x16,4,10,6,1,slot+1,0,0]) if i%2==0 else b'\0\0'
        free(rec,template+script)
        sx,sy=x//512,y//512
        groups[sy*10+sx].append(rec)
        for ny in range(max(0,sy-1),min(7,sy+2)):
            for nx in range(max(0,sx-1),min(10,sx+2)):
                flag=0x21400c+16*(ny*10+nx)
                put(flag,'I',u(flag)|bank_mask)
        infos.append({'id':ident,'slot':slot,'position':[x,y,z],'box':list(shape),'frame':frame})
    put(0x210228,'H',first+len(infos))
    cursor=0x292500
    for i,entries in enumerate(groups):
        if entries:
            block=struct.pack(f'>H{len(entries)}I',len(entries),*entries)
            free(cursor,block)
            put(prior+4*i,'I',cursor)
            cursor+=len(block)
    return {'tiles':len(tiles),'objects':infos}


if __name__=='__main__':
    build()
