import sys
from pathlib import Path
sys.path.insert(0,'strike_work/tools')
from retro import Core
R=Path(__file__).resolve().parent;c=Core(R/'Jungle_Strike_Eco_Threat_Flight_TEST_v2.bin');seen=False;shot=False
for f in range(2600):
 level=(c.rw(0x283c)<<16)|c.rw(0x283e)
 if level==0x210200 and not seen:seen=True;start=f;print('scene begins',f,flush=True)
 c.run(1,'S' if not seen and f%150<8 else '')
 if seen and (f-start)%30==0:c.shot(R/f'departure_{f-start:03d}.png')
 if seen and c.lib.retro_debug_reg(16) in [0x3d770,0x3d778]:print('natural departure ended',f-start,flush=True);break
