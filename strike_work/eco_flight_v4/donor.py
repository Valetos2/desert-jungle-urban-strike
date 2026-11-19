"""Extract the original level-six tree tile bank with the native loader."""
from build import ROOT
from pathlib import Path
import sys, ctypes as C,struct
sys.path.insert(0,'strike_work/tools')
from retro import Core
v2=ROOT.parent/'eco_flight_v2'
b=Path('strikehd/rom/jungle_strike.bin').read_bytes()
u=lambda a:struct.unpack_from('>I',b,a)[0]
w=lambda a:struct.unpack_from('>H',b,a)[0]
bank=u(u(0x525b6+5*4)+15*4)
c=Core(next(v2.glob('*v2.bin')));c.run(1);c.load(v2/'game.state')
sp=c.lib.retro_debug_reg(15)-4;c.wl(sp,c.lib.retro_debug_reg(16))
for reg,value in [(15,sp),(8,bank),(9,0),(16,0x3f45c)]:c.lib.retro_debug_set(reg,value)
c.run(1)
c.lib.retro_debug_vram.restype=C.c_void_p
raw=C.string_at(c.lib.retro_debug_vram(),65536)
start=c.rw(u(bank+6))*32
(ROOT/'stock_trees.bin').write_bytes(bytes(raw[i^1] for i in range(start,start+w(bank+34))))
