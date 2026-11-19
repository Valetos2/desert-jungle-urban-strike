"""Replay the user's captured scroll window, RAM display list and VRAM on GX."""
from pathlib import Path
import sys,ctypes,struct
sys.path.insert(0,'strike_work/tools')
from retro import Core
r=Path(__file__).resolve().parent
c=Core(next(r.glob('*v5.bin')));c.run(1);c.load(r.parent/'eco_flight_v3/game.state')
g=Path(sys.argv[1]).read_bytes()
assert g[:3]==b'GST'
for i,v in enumerate(g[0x2478:0x12478]):c.wb(i,v)
c.lib.retro_debug_vram.restype=ctypes.c_void_p
addr=c.lib.retro_debug_vram()
mem=(ctypes.c_uint8*65536).from_address(addr)
for i,x in enumerate(g[0x12478:0x22478]):mem[i^1]=x
b=next(r.glob('*v5.bin')).read_bytes()
def matches():
 return [sum((mem[k^1]*256+mem[(k+1)^1])==struct.unpack_from('>H',b,0x260200+2*(22*y+x))[0]+c.rw(0x1a4c) for x in range(22) for k in [0xc000+128*((312+y)%64)+2*((55+x)%64)]) for y in range(12)]
print('before',matches())
# Enter the actual scrolling hook; stop on return before resuming game CPU.
sp=0xfffb00;c.wl(sp,0x3d770)
for reg,v in [(15,sp),(10,0xff12e4),(16,0x274100)]:c.lib.retro_debug_set(reg,v)
for _ in range(200000):
 if c.lib.retro_debug_reg(16)==0x3d770:break
 c.lib.retro_debug_step()
print('after',matches());assert matches()[5:]==[22]*7
