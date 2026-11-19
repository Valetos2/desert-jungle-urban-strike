from pathlib import Path
import sys,json
sys.path.insert(0,'strike_work/tools')
from retro import Core
R=Path(__file__).resolve().parent;c=Core(R/'Jungle_Strike_Eco_Threat_Flight_TEST_v3.bin')
for f in range(2000):
 c.run(1,'S' if f%150<8 else '')
 if c.lib.retro_debug_reg(16) in [0x39380,0x39388]:break
else:raise AssertionError('main menu')
c.run(20);c.save(R/'main.state');results=[]
for index in range(5):
 c.load(R/'main.state');c.run(2,'B');c.run(150)
 for _ in range(index):c.run(2,'R');c.run(20)
 selected=c.rb(0x1098);c.shot(R/f'copilot_{index}.png');c.run(2,'S');c.run(120)
 pc=c.lib.retro_debug_reg(16)&0xffffff
 results.append({'requested':index,'selected':selected,'after_accept_pc':hex(pc),'lock_mask':c.rb(0x1099)})
 assert selected==index,results[-1]
 assert pc in [0x39380,0x39388],results[-1]
(R/'copilot_validation.json').write_text(json.dumps(results,indent=2)+'\n');print(results)
