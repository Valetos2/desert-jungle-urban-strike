"""Encode the original test briefing with the game's existing text commands."""
import struct
from textwrap import wrap

PAGES = (
    "ICE STATION GOLF IS IN ENEMY HANDS. START WITH THE RADAR NET. THEN CLEAR THE APPROACH TO THE BASE.",
    "HOSTILE CREWS HAVE TAKEN OVER THE OIL TERMINAL. KEEP THE LOADED TANKERS SAFE AND RECOVER THE STOLEN EQUIPMENT.",
)

def install(rom):
    text=bytearray()
    for i,page in enumerate(PAGES):
        lines=wrap(page, width=30, break_long_words=False, break_on_hyphens=False)
        assert len(lines)<=5 and all(len(line)<=30 for line in lines)
        for j,line in enumerate(lines):
            text.extend(bytes((2,4,20+j))+line.encode('ascii')+b'\0')
            text.append(0xa6 if j==len(lines)-1 else 0xfc)
        text.append(255 if i==len(PAGES)-1 else 254)
    address=0x279200
    rom[address:address+len(text)]=text
    scene=bytearray(rom[0xe20d0:0xe20d0+34])
    struct.pack_into('>I',scene,26,address)
    rom[0x279100:0x279100+len(scene)]=scene
    struct.pack_into('>3I',rom,0x213a80,0x273000,0x279100,0)
    struct.pack_into('>IHH',rom,0x203100+21*8,0x213a80,9,0)
    assert rom[0x20025e:0x200260]==b'\0\x14'
    struct.pack_into('>H',rom,0x20025e,21)
    p=rom.index(b'ENDING       \0\xff',0x202000,0x202800)+14
    row=b'\x02\xf6\0BRIEF 10     \0\xff'
    rom[p:p+len(row)]=row
