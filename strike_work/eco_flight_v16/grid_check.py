"""Compare streamed plane A cells along the approach from the pad and across the grid."""
import ctypes,json,struct,runpy,sys
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parent
m=runpy.run_path(str(root.parent/'eco_flight_v11/check.py'));spawn=m['spawn']
spawn.__globals__['ROM']=next((root.parent/('eco_flight_v'+(sys.argv[1] if len(sys.argv)>1 else '16'))).glob('*.bin'))
c,b=spawn(605,2489)
w=lambda p:struct.unpack_from('>H',b,p)[0]
u=lambda p:struct.unpack_from('>I',b,p)[0]
cache={}
def match(r):
    g=u(r);data=u(g+22);bank=u(0x210100+w(g+4));base=c.rw(u(bank+6)) if b[bank]&2 else 0x34
    if bank not in cache:
        if w(bank+36)==2:cache[bank]=b[u(bank+42):u(bank+42)+w(bank+34)]
        else:cache[bank]=runpy.run_path(str(root.parent/'eco_flight_v9/water.py'))['unpack_tiles'](b,u(bank+42),w(bank+34))
    top,left=w(r+4),w(r+6);x0,y0=c.rw(0x1386),c.rw(0x1384)
    correct=0;tested=0
    for j in range(w(g)*w(g+2)):
        if w(g+16)==2:
            tile=w(data+2*j)
            if not tile&2047:continue
        else:
            v=b[data+2+j]
            if not v:continue
            tile=(v&63)+((v&192)<<5)+w(data)
        idx=(tile+w(g+30))&2047
        if not any(cache[bank][idx*32:idx*32+32]):continue
        dy,dx=divmod(j,w(g));x,y=left+dx,top+dy
        if 16<=8*x-x0<296 and 16<=8*y-y0<200:
            tested+=1;correct+=((int(vram[0x6000+(y%64)*64+x%64])^(tile+w(g+30)+base))&8191)==0
    return correct,tested
pos=m['ram_long'](c,m['ram_long'](c,0x29e8)+34)
c.lib.retro_debug_vram.restype=ctypes.c_void_p
stats={};inactive={};coords=[(459,3294),(1020,2980),(900,3040),(850,3090),(1250,3200),(590,3228)]
for dest in coords:
    x,y=c.rw(pos),c.rw(pos+4)
    steps=max(abs(dest[0]-x),abs(dest[1]-y))//8+1
    for i in range(1,steps+1):
        c.wl(pos,(x+(dest[0]-x)*i//steps)<<16);c.wl(pos+4,(y+(dest[1]-y)*i//steps)<<16);c.run(4)
        vram=np.frombuffer(ctypes.string_at(c.lib.retro_debug_vram(),65536),dtype='<u2')
        for n in range(7):
            r=u(0x27f100+4*n);a,total=match(r)
            bucket=stats if c.rb(0xff391e+30*b[r+23]+25)&8 else inactive
            s=bucket.setdefault(n,[0,0]);s[0]+=a;s[1]+=total
m['closed'](c)
(root/('grid_validation_'+(sys.argv[1] if len(sys.argv)>1 else '16')+'.json')).write_text(json.dumps(dict(active=stats,destroyed=inactive),indent=2))
