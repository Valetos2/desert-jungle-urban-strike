"""Fire via pad input at a static target, without calling damage directly."""
import sys
import tempfile
import struct
from pathlib import Path
from build import ROOT, NAME, v4

sys.path.insert(0,'strike_work/eco_flight_v6')
from check import boot

def fire(i, dy, key):
    b=bytearray((ROOT/(NAME+'.bin')).read_bytes())
    rec=0x276000+64*i
    y,x=struct.unpack_from('>HH',b,rec+16)
    x, y = max(8,x-50), y+dy
    struct.pack_into('>HH',b,0x21090c,y,x)
    b[0x210912]=0
    b[0x210700:0x210818]=bytes(280)
    struct.pack_into('>I',b,0x210700+(y//512*10+x//512)*4,0x210940)
    v4.checksum(b)
    with tempfile.TemporaryDirectory() as temp:
        p=Path(temp)/'probe.bin'
        p.write_bytes(b)
        core=boot(p)
    core.run(650)
    core.wb(0x12b7,14) # diagnostic spawn bypasses the scripted takeoff mode
    target=0xff391e+(47+i)*30
    before=core.rw(target+20)
    def u(a):return core.rw(a)*65536+core.rw(a+2)
    player=u(0x29e8)
    ammo=lambda:tuple(core.rw(u(player+k)+18) for k in (0x34,0x38,0x3c))
    initial=ammo()
    for _ in range(8):
        core.run(3,key)
        core.run(20)
        if core.rw(target+20)==0 or core.rw(target+20)>32767:break
    after=core.rw(target+20)
    print(i,dy,key,'HP',before,after,'ammo',initial,ammo(),flush=True)
    assert ammo()==initial
    return after==0 or after>32767

if __name__=='__main__':
    assert fire(int(sys.argv[1]),int(sys.argv[2]),sys.argv[3])
