import sys
from pathlib import Path
sys.path.insert(0,'strike_work/tools')
from retro import Core
c=Core('strike_work/eco_flight_v2/Jungle_Strike_Eco_Threat_Flight_TEST_v2.bin')
def pc():return c.lib.retro_debug_reg(16)&0xffffff
def long(a):return c.rw(a)*65536+c.rw(a+2)
for f in range(4800):
 c.run(1,'S' if f%150<8 else '')
 if f%300==0:print(f,hex(pc()),'campaign',long(0x10b0),'level',hex(long(0x283c)),'player',hex(long(0x29e8)),flush=True)
 if long(0x283c)==0x210200 and pc()==0x3d778:
  print('GAME',f,hex(long(0x29e8)),hex(long(0x121e)),c.rw(0x1232),c.rw(0x1234),flush=True)
  c.run(180);c.save('strike_work/eco_flight_v2/game.state');c.shot('strike_work/eco_flight_v2/first.png');break
else:c.shot('strike_work/eco_flight_v2/blocked.png')
