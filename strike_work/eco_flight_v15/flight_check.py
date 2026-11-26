"""Follow the GS0 heading with native controls and inspect the grid on a second route."""
import ctypes,json,runpy,struct
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parent
m=runpy.run_path(str(root.parent/'eco_flight_v11/check.py'))
spawn=m['spawn']; lng=m['ram_long']
def readlong(buf,p): return struct.unpack_from('>I',buf,p&65535)[0]
def observe(c,rom,rec,ruin=False):
    pos=rec-16 if ruin else rec
    word=lambda p:struct.unpack_from('>H',rom,p)[0]
    ptr=lambda p:struct.unpack_from('>I',rom,p)[0]
    g=ptr(pos)
    top,left=word(pos+4),word(pos+6)
    data=ptr(g+22)
    c.lib.retro_debug_vram.restype=ctypes.c_void_p
    vram=np.frombuffer(ctypes.string_at(c.lib.retro_debug_vram(),65536),dtype='<u2')
    bank=ptr(0x210100+word(g+4))
    base=c.rw(ptr(bank+6)) if rom[bank]&2 else 0x34
    stats=[0,0]
    for j in range(word(g)*word(g+2)):
        if word(g+16)==2: value=word(data+2*j)
        else:
            v=rom[data+2+j]
            if not v:continue
            value=(v&63)+((v&192)<<5)+word(data)
        if not value&2047:continue
        y,x=divmod(j,word(g));x+=left;y+=top
        if 8<=8*x-c.rw(0x1386)<304 and 8<=8*y-c.rw(0x1384)<210:
            current=int(vram[0x6000+64*(y%64)+x%64])
            stats[0]+=int((current^(value+word(g+30)+base))&0x1fff==0)
            stats[1]+=1
    return stats
out={}
for ver in (14,15):
    spawn.__globals__['ROM']=next((root.parent/f'eco_flight_v{ver}').glob('*.bin'))
    raw=next(Path('upload').glob('*v14.gs0')).read_bytes()[0x2478:0x12478]
    src=readlong(raw,readlong(raw,0x29e8)+34)
    c,b=spawn(readlong(raw,src)>>16,readlong(raw,src+4)>>16)
    pos=lng(c,lng(c,0x29e8)+34)
    for offset in range(0,40,4):c.wl(pos+offset,readlong(raw,src+offset))
    c.wb(0x12b7,0x12)
    ids=json.loads((root.parent/'eco_flight_v14/build_report.json').read_text())['actors']
    live=struct.unpack_from('>I',b,0x2b0000+ids.index(80)*128+8)[0]
    visible=[]; positions=[]
    for frame in range(300):
        c.run(1,'U')
        if frame%40==0:
            actor=lng(c,live+4);st=lng(c,actor+34) if actor else 0
            positions.append([c.rw(pos),c.rw(pos+4),c.rw(0x1386),c.rw(0x1384),c.rw(st) if st else None,c.rw(st+4) if st else None])
        actor=lng(c,live+4)
        if actor:
            st=lng(c,actor+34);x=c.rw(st)-c.rw(0x1386);y=c.rw(st+4)-c.rw(0x1384)-c.rw(st+8)
            if 12<x<308 and 12<y<207:
                spr=lng(c,actor+0x4e)
                visible.append([frame,x,y,c.rw(spr+0x42)])
                if len(visible)==5:c.shot(f'/tmp/eco15_heli{ver}.png')
    m['closed'](c)
    grid={}
    for tag,x,y,rec in [('pad',605,2489,0x2503e8),('station',408,3380,0x279490),('pylon',601,3310,0x27a5d0)]:
        c,b=spawn(x,y)
        c.run(30)
        grid[tag]=observe(c,b,rec)
        if tag!='pad':
            m['native_destroy'](c,b[rec+23])
            grid[tag+'_ruin']=observe(c,b,rec,True)
        m['closed'](c)
    out[str(ver)]=dict(player_track=positions,heli_visible_area_frames=len(visible),heli_first=visible[:1],grid_tiles=grid)
    print(ver,out[str(ver)],flush=True)
(root/'flight_validation.json').write_text(json.dumps(out,indent=2)+'\n')
