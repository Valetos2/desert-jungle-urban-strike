from pathlib import Path
import sys
sys.path.insert(0,'strike_work/tools')
from retro import Core
R=Path(__file__).resolve().parent
c=Core(next(R.glob('*v5.bin')))
for f in range(6000):
 c.run(1,'S' if f%150<8 else '')
 if c.lib.retro_debug_reg(16) in (0x3d770,0x3d778):break
else:raise AssertionError(hex(c.lib.retro_debug_reg(16)))
c.run(180)
slot=0x391e+48*30
assert not c.rb(slot+25)&8
print('boot',f,flush=True)
def values():return [c.rw(0x10da+2*i) for i in range(8)]
for j in range(8):
 c.run(20,'Z');c.run(80)
 print(j+1,values(),hex(c.lib.retro_debug_reg(16)),flush=True)
 assert bool(c.rb(slot+25)&8)==(j>=3)
 assert values()[:j+1]==[0]*(j+1) and (j==7 or values()[j+1]>32767)
