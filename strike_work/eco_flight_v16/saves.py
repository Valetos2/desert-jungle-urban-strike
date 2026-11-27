"""Compare the visible wire map cells and their actual pattern bytes in the Fusion save."""
from pathlib import Path
import json,struct,runpy
root=Path(__file__).resolve().parent
old=next((root.parent/'eco_flight_v15').glob('*.bin')).read_bytes()
s=next(Path('upload').glob('*v15.gs2')).read_bytes()
ram=s[0x2478:0x12478];video=s[0x12478:0x22478]
def read(buf,p,n):return int.from_bytes(buf[p:p+n],'big')
w=lambda p:read(old,p,2)
u=lambda p:read(old,p,4)
rw=lambda p:read(ram,p&65535,2)
x,y=rw(0x1386),rw(0x1384)
res={}
for j in range(7):
    r=u(0x27f100+4*j);g=u(r);data=u(g+22);bank=u(0x210100+w(g+4));base=rw(u(bank+6))
    raw=old[u(bank+42):u(bank+42)+w(bank+34)] if w(bank+36)==2 else runpy.run_path(str(root.parent/'eco_flight_v9/water.py'))['unpack_tiles'](old,u(bank+42),w(bank+34))
    matches=[0,0,0]
    for i in range(w(g)*w(g+2)):
        if w(g+16)==2:t=w(data+2*i)
        else:
            n=old[data+2+i]
            if not n:continue
            t=w(data)+(n&63)+((n&192)<<5)
        t+=w(g+30);idx=t&2047;pattern=bytes(raw[idx*32:idx*32+32])
        if not any(pattern):continue
        dy,dx=divmod(i,w(g));cx=w(r+6)+dx;cy=w(r+4)+dy
        if not (x<=8*cx<x+320 and y<=8*cy<y+224):continue
        a=read(video,0xc000+2*(cx%64+64*(cy%64)),2);at=(a&2047)*32
        matches[0]+=1;matches[1]+=((a^(t+base))&8191)==0
        matches[2]+=video[at:at+32]==pattern
    res[j]=dict(counts=matches,active=bool(ram[0x391e+30*old[r+23]+25]&8),base=base)
out=dict(gs2_camera=[x,y],requested_banks=hex(read(ram,0x2976,4)),wires=res)
gs1=next(Path('upload').glob('*v15.gs1')).read_bytes()
out['gs1_camera']=[read(gs1,0x2478+0x1386,2),read(gs1,0x2478+0x1384,2)]
# Inspect the SAT at the coordinates of the stationary gun in the original
# save and in GX. Its turret and base have separate runtime sprite records.
import ctypes
for ver in (15,16):
    m=runpy.run_path(str(root.parent/'eco_flight_v11/check.py'));spawn=m['spawn']
    spawn.__globals__['ROM']=next((root.parent/f'eco_flight_v{ver}').glob('*.bin'))
    for j,(cx,cy) in enumerate([(354,3391),(535,3172)]):
        c,b=spawn(cx,cy);c.run(30);c.shot(f'/tmp/save16_{ver}_{j}.png')
        if j==0:
            slot=read(b,0x2b0588,4);actor=m['ram_long'](c,slot+4)
            if actor:
                sprite=m['ram_long'](c,actor+78);tile=c.rw(sprite+66)
                c.lib.retro_debug_vram.restype=ctypes.c_void_p
                vram=ctypes.string_at(c.lib.retro_debug_vram(),65536)
                def vw(p):return int.from_bytes(vram[p:p+2],'little')
                indices=[];idx=0
                for n in range(80):
                    at=0x400+8*idx;attr=vw(at+4)
                    if tile<=(attr&2047)<tile+12:indices.append(hex(attr))
                    idx=vw(at+2)&127
                    if not idx:break
                out[f'gun_{ver}']=indices
        m['closed'](c)
(root/'saves_validation.json').write_text(json.dumps(out,indent=2))
