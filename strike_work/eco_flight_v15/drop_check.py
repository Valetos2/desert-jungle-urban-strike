"""Exercise destruction and inspect the floating drop using the native events."""
import json,runpy,struct
from pathlib import Path
root=Path(__file__).resolve().parent
m=runpy.run_path(str(root.parent/'eco_flight_v11/check.py'))
spawn=m['spawn'];spawn.__globals__['ROM']=next(root.glob('*.bin'))
c,b=spawn(2200,1025);lng=m['ram_long']
u=lambda p:struct.unpack_from('>I',b,p)[0]
w=lambda p:struct.unpack_from('>H',b,p)[0]
rows=json.loads((root.parent/'eco_flight_v11/build_report.json').read_text())['mission1']
def slot(i):
    n=next(r['slot'] for r in rows if r['id']==i)
    return 0xfffba6+struct.unpack_from('>h',b,u(0x21024c)+2*n)[0]
c.run(75)
actor=lng(c,slot(12)+4);assert actor
pos=lng(c,actor+34)
xy=(c.rw(pos),c.rw(pos+4))
m['damage_actor'](c,actor,1000)
crate=slot(21)
p=lng(c,crate+4)
assert p
pos=lng(c,p+34)
drop=(c.rw(pos),c.rw(pos+4))
r=lng(c,crate)
assert u(u(r)+54)==u(0x18e5d6+54)
assert max(abs(a-b) for a,b in zip(xy,drop))<8,(xy,drop)
player=lng(c,lng(c,0x29e8)+34)
for _ in range(150):
    c.wl(player,(drop[0]-70)<<16)
    c.wl(player+4,drop[1]<<16)
    c.run(1)
c.shot('/tmp/eco15_drop.png')
m['closed'](c)
(root/'drop_validation.json').write_text(json.dumps(dict(boat=xy,drop=drop,native_art=hex(u(0x18e5d6+54))),indent=2)+'\n')
