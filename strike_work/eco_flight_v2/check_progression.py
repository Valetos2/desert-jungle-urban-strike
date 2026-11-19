"""Exercise the real 68000 continuation branch at both campaign boundaries."""
import sys,json
from pathlib import Path
sys.path.insert(0,'strike_work/tools')
from retro import Core
ROOT=Path(__file__).resolve().parent
c=Core(ROOT/'Jungle_Strike_Eco_Threat_Flight_TEST_v2.bin');c.run(1)
def ww(a,v):c.wb(a,v>>8);c.wb(a+1,v&255)
results=[]
for current in [8,9]:
 ww(0xff139e,current);c.lib.retro_debug_set(1,current*4);c.lib.retro_debug_set(16,0x3dcc8)
 for _ in range(8):
  pc=c.lib.retro_debug_reg(16)&0xffffff
  if pc in [0x3d904,0x3dcdc]:break
  c.lib.retro_debug_step()
 expected=0x3d904 if current==8 else 0x3dcdc
 assert pc==expected,(current,hex(pc));assert c.rw(0x139e)==current+1
 results.append(dict(completed_campaign=current+1,next_index=c.rw(0x139e),branch='load_next' if current==8 else 'ending',pc=hex(pc)))
(ROOT/'progression_validation.json').write_text(json.dumps({'method':'isolated real-CPU branch check, not a full mission playthrough','results':results},indent=2)+'\n');print(results)
