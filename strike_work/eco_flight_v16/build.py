from pathlib import Path
import csv,struct,runpy,json,hashlib
import numpy as np
from PIL import Image
root=Path(__file__).resolve().parent
work=root.parent
rom=bytearray(next((work/'eco_flight_v15').glob('*.bin')).read_bytes())
assert hashlib.sha256(rom).hexdigest()==json.loads((work/'eco_flight_v15/build_report.json').read_text())['sha256']
dos=work/'dos/unpacked/jungle'
w=lambda p:struct.unpack_from('>H',rom,p)[0]
u=lambda p:struct.unpack_from('>I',rom,p)[0]
def put(p,fmt,*v):struct.pack_into('>'+fmt,rom,p,*v)
def copy(dst,src,n):rom[dst:dst+n]=rom[src:src+n]
def records(table,s):
    a=u(table+4*s)
    return [u(a+2+4*j) for j in range(w(a))] if a else []
def img(g):
    data=u(g+22);bank=u(0x210100+w(g+4));base=u(bank+42)
    raw=rom[base:base+w(bank+34)] if w(bank+36)==2 else runpy.run_path(str(work/'eco_flight_v9/water.py'))['unpack_tiles'](rom,base,w(bank+34))
    out=np.zeros((8*w(g+2),8*w(g)),np.uint8)
    for j in range(w(g)*w(g+2)):
        if w(g+16)==2:v=w(data+2*j)
        else:
            k=rom[data+2+j]
            if not k:continue
            v=(k&63)+((k&192)<<5)+w(data)
        v+=w(g+30);a=np.frombuffer(raw,np.uint8,32,(v&2047)*32)
        t=np.stack([a>>4,a&15],axis=1).reshape(8,8)
        if v&0x800:t=t[:,::-1]
        if v&0x1000:t=t[::-1]
        y,x=divmod(j,w(g));out[y*8:y*8+8,x*8:x*8+8]=np.where(t,t+16*(v>>13&3),0)
    return out
# The null far pointer on the five active gunners has no native route in v15.
# Match the DOS patrol shared by its four other standard attack boats.
layout=(dos/'LEVELA').read_bytes()
exe=(dos/'EXECUTABLE').read_bytes()
le=lambda b,p:struct.unpack_from('<H',b,p)[0]
mz=exe[16*le(exe,8):]
sample=next(r for r in csv.DictReader((work/'dos/eco_dynamic.csv').open()) if r['index']=='78')
at=int(sample['level_offset'],16)
route=(le(layout,at+6)-0x1a7e+le(mz,4))*16+le(layout,at+4)
stop=route+24
while mz[stop:stop+2]!=bytes(2):stop+=2
patrol=mz[route:stop+2]
route_ptr=rom.find(patrol,0x190000,0x193000)
assert route_ptr>0
for s in range(70):
    for r in records(u(0x210242),s):
        if u(r)==0x18dc5a and not u(r+4) and rom[r+21]&128:put(r+4,'I',route_ptr)
# The native mission-list pass already filters locked entries. Leave targets
# on the map until they are gone, even after the test shortcut changes a count.
seq=bytes.fromhex('d0402f0841f900ff10d84a700000205f6b')
off=rom.find(seq,0x27a180,0x27a1d0)
assert off>=0
rom[off:off+2]=bytes([0x60,rom.index(bytes.fromhex('201f48e7'),off,off+60)-off-2])
for p in [0x27a570,0x27a5d0,0x27a630]:
    top=w(p+4)+9
    put(p-12,'H',top)
    put(p-8,'H',top+w(u(p-16)+2))
# Transfer wire graphics to the persistent terrain allocation. Re-index the
# sparse byte maps, preserving transparent cells and priority.
bank=u(0x210100+36)
wire_raw=runpy.run_path(str(work/'eco_flight_v9/water.py'))['unpack_tiles'](rom,u(bank+42),w(bank+34))
base=w(0x210022)//32
terrain=bytearray(rom[0x220000:0x220000+base*32])
tile_lookup={}
wire_maps={}
for rec in [0x279450]+[u(0x27f100+4*j) for j in range(6)]:
    g=u(rec)
    if g not in wire_maps:
        dest=0x2f0000+len(wire_maps)*256
        copy(dest,g,32)
        data=u(g+22)
        assert w(g+16)==0x1a
        put(dest+4,'H',40)
        put(dest+22,'I',dest+32)
        put(dest+32,'H',(w(data)&0xf800)+base-1)
        for i in range(w(g)*w(g+2)):
            byte=rom[data+2+i]
            if byte:
                idx=(w(data)+(byte&63))&2047
                raw=bytes(wire_raw[idx*32:idx*32+32])
                assert len(raw)==32
                if raw not in tile_lookup:
                    tile_lookup[raw]=len(tile_lookup)+1
                    terrain.extend(raw)
                byte=(byte&192)|tile_lookup[raw]
            rom[dest+34+i]=byte
        wire_maps[g]=dest
    put(rec,'I',wire_maps[g])
assert len(tile_lookup)<64
put(0x210022,'HHII',len(terrain),2,len(terrain),0x220000)
rom[0x220000:0x220000+len(terrain)]=terrain
for s in range(70):
    p=0x21400c+16*s
    put(p,'I',u(p)&~0x100)
# Static #24 uses frame one of F169-170 in THINGS.
res=runpy.run_path(str(work/'dos/eco_threat_reference.py'))
r=next(i for i in json.loads((work/'eco_flight_v3/dos_static.json').read_text()) if i['id']==24)
things=(dos/'THINGS').read_bytes()
art=np.asarray(res['sprite']((dos/r['name']).read_bytes(),things[r['type']+2]))
rgb=np.array([[(w(0x210400+2*i)>>k&7)*255/7 for k in (1,5,9)] for i in range(16)])
indices=(1+((art[:,:,:3,None].astype(float)-rgb[1:].T)**2).sum(2).argmin(2)).astype(np.uint8)
indices[art[:,:,3]==0]=0
ih,iw=indices.shape
indices=np.pad(indices,((0,-ih%8),(0,-iw%8)))
tiles=[];attrs=[]
for y in range(0,indices.shape[0],8):
    for x in range(0,indices.shape[1],8):
        pix=indices[y:y+8,x:x+8].ravel()
        data=(pix[::2]*16+pix[1::2]).tobytes()
        if data not in tiles:tiles.append(data)
        attrs.append(tiles.index(data))
g=0x2f1000;bank=0x2f1200;rec=0x2f1600;col=rec+64
copy(g,0x293000,32)
ww,hh=indices.shape[1]//8,indices.shape[0]//8
put(g,'3H',ww,hh,76)
put(g+10,'3H',0,hh,ww*2);put(g+16,'HII',2,len(attrs)*2,g+32)
put(g+30,'H',0x8000);put(g+32,'H'*len(attrs),*attrs)
copy(bank,0x293a00,46)
data=b''.join(tiles)
put(bank+6,'I',0xff1a56);put(bank+34,'HHII',len(data),2,len(data),bank+64)
rom[bank+64:bank+64+len(data)]=data;put(0x210100+76,'I',bank)
top,left=struct.unpack_from('<2H',layout,r['offset']+4)
slot=w(0x210228);put(0x210228,'H',slot+1)
copy(rec,0x250000,34)
put(rec,'I4H',g,top,left,top+hh,left+ww)
put(rec+16,'HHh',r['y'],r['x'],r['z'])
rom[rec+22:rec+26]=bytes([0x49,slot,0,0])
put(rec+26,'IIH',col,0xff391e+slot*30,0)
copy(col,u(0x250000+26),34)
put(col+20,'7h',0,*struct.unpack_from('<6h',things,r['type']+15))
s=r['y']//512*10+r['x']//512
items=records(0x210500,s)+[rec];put(0x210500+4*s,'I',0x2f1680)
put(0x2f1680,'H'+'I'*len(items),len(items),*items)
put(0x21400c+s*16,'I',u(0x21400c+s*16)|(1<<18))
# Use the four original pause-picture definitions as donors.
menu=u(0x212480+36);snow=u(0x212480+20)
for i in range(4):put(menu+98+12*i,'I',u(snow+2+12*(11+i)))
exec(compile((root/'cards.py').read_text(),'cards.py','exec'))
for script in ('tower.py','supplies.py'):
    exec(compile((root/script).read_text(),script,'exec'))
runpy.run_path(str(work/'eco_flight_v4/build.py'))['checksum'](rom)
(root/'Jungle_Strike_Eco_Threat_Flight_TEST_v16.bin').write_bytes(rom)
(root/'build_report.json').write_text(json.dumps(dict(sha256=hashlib.sha256(rom).hexdigest(),boat_route=hex(route_ptr),wire_tiles=len(tile_lookup),igloo_slot=slot),indent=2))
