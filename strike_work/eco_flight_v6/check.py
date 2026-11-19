"""Revisit the coordinates from the seven v5 saves with fresh v6 video RAM."""
from pathlib import Path
import ctypes as C
import struct
import sys
import tempfile
from build import ROOT, NAME, v4
sys.path.insert(0, 'strike_work/tools')
from retro import Core

def boot(rom):
    core = Core(rom)
    for f in range(4500):
        core.run(1, 'S' if f % 150 < 8 else '')
        if core.lib.retro_debug_reg(16) in (0x3d770, 0x3d778):
            return core
    raise AssertionError('Game did not start')

def replay(save):
    g = save.read_bytes()
    ram = g[0x2478:0x12478]
    def u(a): return struct.unpack_from('>I',ram,a&65535)[0]
    def w(a): return struct.unpack_from('>H',ram,a&65535)[0]
    pos = u(u(0x29e8)+34)
    x, y = w(pos), w(pos+4)
    b = bytearray((ROOT/(NAME+'.bin')).read_bytes())
    struct.pack_into('>HH',b,0x21090c,y,x)
    b[0x210700:0x210818]=bytes(280)
    struct.pack_into('>I',b,0x210700+(y//512*10+x//512)*4,0x210940)
    v4.checksum(b)
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/'probe.bin'
        p.write_bytes(b)
        core=boot(p)
    core.run(180)
    core.lib.retro_debug_vram.restype=C.c_void_p
    mem=(C.c_uint8*65536).from_address(core.lib.retro_debug_vram())
    def vw(k): return mem[k^1]*256+mem[(k+1)^1]
    rows=[(92,324),(172,196),(236,328),(312,55),(266,165),(360,326)]
    def frame():
        x,y=core.rw(0x1386),core.rw(0x1384)
        base=core.rw(0x1a4c)
        actual=set()
        visible=set()
        for yy in range(y//8,(y+223)//8+1):
            for xx in range(x//8,(x+319)//8+1):
                v=vw(0xc000+128*(yy%64)+2*(xx%64))
                if base and v&0x6000==0x4000 and 0<=((v&2047)-base)<100:
                    actual.add((xx,yy))
                if any(l<=xx<l+22 and t<=yy<t+12 for t,l in rows):
                    visible.add((xx,yy))
        # Check absence of repeats and track incomplete visible pads separately.
        assert actual<=visible, (x,y,len(actual-visible))
        return len(visible),len(actual)
    initial=frame()
    target = {'.gs0': 67, '.gs1': 43, '.gs6': 12}.get(save.suffix)
    if target:
        from json import loads
        ids=loads((ROOT.parent/'eco_flight_v5/build_report.json').read_text())['new_ids']
        live=0xff391e+(47+ids.index(target))*30
        flags=core.rb(live+25)
        assert (flags & 0x4b)==0x4b,(target,hex(flags))
        hp=core.rw(live+20)
        assert hp>0
        sp=core.lib.retro_debug_reg(15)-4
        core.wl(sp,core.lib.retro_debug_reg(16))
        for reg,val in [(15,sp),(13,live),(0,hp),(16,0x40b5a)]:
            core.lib.retro_debug_set(reg,val)
        core.run(160)
        print('Damage',target,'armor',hp,'->',core.rw(live+20),'flags',hex(core.rb(live+25)),flush=True)
        assert core.rb(live+25)&0x20,(target,hex(core.rb(live+25)))

    missing=0
    for key in ('DX','DX','UX','RX','RX','RX','RX','LX','LX','LX','UX','DX'):
        for i in range(90):
            core.run(1,key)
            if i%3==0:
                expected,actual=frame()
                missing=max(missing,expected-actual)
    print(save.suffix, (x,y), 'initial expected/actual', initial, 'maximum missing', missing,flush=True)

if __name__=='__main__':
    replay(Path(sys.argv[1]))
