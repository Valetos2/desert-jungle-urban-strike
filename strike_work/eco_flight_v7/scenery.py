"""Use existing Genesis scenery and collision definitions at three Eco Threat sites."""
import json
import struct

def install(rom, v3, source):
    rows = {row['id']:row for row in json.loads((v3/'dos_static.json').read_text())}
    def w(p): return struct.unpack_from('>H',rom,p)[0]
    def u(p): return struct.unpack_from('>I',rom,p)[0]
    def putw(p,v): struct.pack_into('>H',rom,p,v)
    def putl(p,v): struct.pack_into('>I',rom,p,v)
    table = 0x210500
    sector_lists = []
    for sector in range(70):
        address=u(table+4*sector)
        sector_lists.append([u(address+2+4*i) for i in range(w(address))] if address else [])
    # Index 60 remains reserved for the debug Z latch.
    donors = [(1,0x1ab9ae,True),(73,0x1ad0a0,False),(82,0x1ad332,True)]
    for i,(ident,donor,destructible) in enumerate(donors):
        row=rows[ident]
        slot=61+i
        rec=0x279410+64*i
        gfx=u(donor)
        top,left=struct.unpack_from('<HH',source,row['offset']+4)
        rom[rec:rec+34]=rom[donor:donor+34]
        struct.pack_into('>4H',rom,rec+4,top,left,top+w(gfx+2),left+w(gfx))
        struct.pack_into('>HHh',rom,rec+16,row['y'],row['x'],row['z'])
        rom[rec+22]=0x4f if destructible else 0x49
        rom[rec+23]=slot
        putl(rec+30,0xff391e+30*slot)
        rom[rec+34:rec+36]=b'\0\0'
        if destructible:
            ruin=u(donor-16)
            rom[rec-16:rec]=rom[donor-16:donor]
            struct.pack_into('>4H',rom,rec-12,top,left,top+w(ruin+2),left+w(ruin))
        col,row_index=row['x']//512,row['y']//512
        sector_lists[10*row_index+col].append(rec)
        bank_offset=w(gfx+4)
        putl(0x210100+bank_offset,u(u(0x525b6+20)+bank_offset))
        for sy in range(max(0,row_index-1),min(7,row_index+2)):
            for sx in range(max(0,col-1),min(10,col+2)):
                mask=0x21400c+16*(10*sy+sx)
                putl(mask,u(mask)|(1<<(bank_offset//4-1)))
    address=0x279600
    for sector,entries in enumerate(sector_lists):
        if entries:
            data=struct.pack('>H'+'I'*len(entries),len(entries),*entries)
            rom[address:address+len(data)]=data
            putl(table+sector*4,address)
            address+=len(data)
    putw(0x210228,64)
    return [item[0] for item in donors]
