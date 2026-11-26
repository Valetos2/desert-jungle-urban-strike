"""Compare both builds along the world coordinates stored in the three Fusion saves."""
from pathlib import Path
import json, runpy, struct
from PIL import Image
root=Path(__file__).resolve().parent
m=runpy.run_path(str(root.parent/'eco_flight_v11/check.py'))
spawn=m['spawn']; lng=m['ram_long']
points=[]
for j in range(3):
    raw=next(Path('upload').glob('*v14.gs'+str(j))).read_bytes()
    ram=raw[0x2478:0x12478]
    ptr=lambda p:struct.unpack_from('>I',ram,p&65535)[0]
    word=lambda p:struct.unpack_from('>H',ram,p&65535)[0]
    pos=ptr(ptr(0x29e8)+34)
    points.append([word(pos),word(pos+4)])
def travel(c,x,y):
    pos=lng(c,lng(c,0x29e8)+34)
    a,b=c.rw(pos),c.rw(pos+4)
    steps=max(abs(x-a),abs(y-b))//10+1
    for i in range(1,steps+1):
        c.wl(pos,(a+(x-a)*i//steps)<<16)
        c.wl(pos+4,(b+(y-b)*i//steps)<<16)
        c.run(2)
    c.run(45)
def state(c):
    return dict(free=lng(c,0x161c),camera=[c.rw(0x1386),c.rw(0x1384)],sectors=hex(lng(c,0x297a)),bank_mask=hex(lng(c,0x2976)),failure=c.rb(0x1621),pc=hex(m['pc'](c)))
results={}
for version in (14,15):
    rom=next((root.parent/f'eco_flight_v{version}').glob('*.bin'))
    spawn.__globals__['ROM']=rom
    result=[]
    c,b=spawn(*points[1])
    for point in [points[1],points[2]]:
        travel(c,*point)
        result.append(state(c))
        Image.fromarray(c.frame).save(f'/tmp/eco15_{version}_{len(result)}.png')
    m['closed'](c)
    results[str(version)]=result
    print(version,result,flush=True)
c,b=spawn(2200,1025)
m['press'](c,'S',90)
print('map',hex(m['pc'](c)),m['markers'](c),flush=True)
m['press'](c,'B',90)
print('card',hex(m['pc'](c)),c.rw(0x104e),flush=True)
Image.fromarray(c.frame).save('/tmp/eco15_card.png')
import ctypes
c.lib.retro_debug_cram.restype=ctypes.c_void_p
print("cram", list((ctypes.c_uint16*64).from_address(c.lib.retro_debug_cram())),flush=True)
m['closed'](c)
(root/'validation.json').write_text(json.dumps(dict(positions=points,route=results),indent=2)+'\n')
