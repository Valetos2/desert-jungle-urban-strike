"""Exercise the native pause menu and capture evidence of the selected map icons."""
import json,runpy
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parent
m=runpy.run_path(str(root.parent/'eco_flight_v11/check.py'))
spawn=m['spawn'];spawn.__globals__['ROM']=next(root.glob('*.bin'))
c,_=spawn(2200,1025)
p=m['press']
p(c,'S')
p(c,'B');p(c,'A');c.shot('/tmp/eco15_map.png')
print('sel',c.rw(0x1038),c.rb(0x103a),c.rw(0x104e),flush=True)
first=m['markers'](c)
assert len(first)==5 and all(mark[0]==1 for mark in first)
icons=[set() for _ in first]
for _ in range(100):
    c.run(1)
    for i,(_,x,y) in enumerate(first):
        icons[i].add(c.frame[y-9:y+10,x-9:x+10].tobytes())
assert all(len(states)>1 for states in icons)
p(c,'B')
for n in range(12):
    c.shot(f'/tmp/eco15_menu_{n}.png')
    print(n, c.rb(0x1024),c.rw(0x1022),hex(m['pc'](c)),flush=True)
    p(c,'R',35)
m['closed'](c)
(root/'map_validation.json').write_text(json.dumps(dict(initial=first,pixel_states=[len(entries) for entries in icons]),indent=2)+'\n')
