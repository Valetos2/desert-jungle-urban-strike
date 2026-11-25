"""Install Eco Threat's second objective from the DOS event records."""
from pathlib import Path
import struct,csv,runpy,hashlib,json
import numpy as np
from PIL import Image
root=Path(__file__).resolve().parent
work=root.parent
rom=bytearray(next((work/'eco_flight_v12').glob('*.bin')).read_bytes())
def w(a):return struct.unpack_from('>H',rom,a)[0]
def u(a):return struct.unpack_from('>I',rom,a)[0]
def put(a,fmt,*v):struct.pack_into('>'+fmt,rom,a,*v)
dos=work/'dos/unpacked/jungle'
d=(dos/'LEVELA').read_bytes()
rows={int(r['index']):r for r in csv.DictReader(open(work/'dos/eco_dynamic.csv'))}
ids=[18,*range(25,37)]
types={0xa9ec:0x18ded8,0xa848:0x18dc5a,0xb2a6:0x18de14,0xb332:0x18d77e,0xa4e6:0x18d9c2,0x9fe2:0x18e594}
n=w(0x210226);table=u(0x21024c);old=list(struct.unpack_from('>'+str(n)+'h',rom,table))
offsets=old.copy()
longs=[i for i in ids if int(rows[i]['flags_14_15_16'][2:4],16)&128]
shift=42*len(longs)
for i,v in enumerate(old):
 if v<=-252:offsets[i]-=shift
used=u(0x210250)+shift
groups=[];gt=u(0x210242)
for j in range(70):
 a=u(gt+4*j);grp=[u(a+2+k*4) for k in range(w(a))] if a else []
 for rec in grp:
  slot=old.index(u(rec+8)-0xfffba6)
  put(rec+8,'I',0xfffba6+offsets[slot])
 groups.append(grp)
exe=(dos/'EXECUTABLE').read_bytes();le=lambda b,a:struct.unpack_from('<H',b,a)[0]
mz=exe[le(exe,8)*16:]
for j,i in enumerate(ids):
 r=rows[i];a=int(r['level_offset'],16);rec=0x2a0000+128*j
 delta=-(252+42*longs.index(i)) if i in longs else -used
 if i not in longs:used+=14
 offsets.append(delta)
 typ=int(r['type_ds'],16);native=types.get(typ,0x18e65a)
 route=0
 if le(d,a+4):
  off=(le(d,a+6)-0x1a7e+le(mz,4))*16+le(d,a+4)
  end=off+24
  while mz[end:end+2]!=bytes(2):end+=2
  route=0x2a0800+j*96
  seq=mz[off:end+2];assert len(seq)<=96;rom[route:route+len(seq)]=seq
 sector=int(r['sector']);groups[sector].append(rec)
 put(rec,'IIIHHh',native,route,0xfffba6+delta,*struct.unpack_from('<HHh',d,a+12))
 rom[rec+18:rec+26]=d[a+18:a+23]+bytes(3)
 at=a+26;out=bytearray()
 while d[at]:
  evt,length,op,sub=d[at:at+4];p=d[at+4:at+6]
  if op==6:p=bytes([1,n+ids.index(p[1])])
  else:assert (op,sub)==(2,26)
  out.extend(bytes([evt,4,op,sub])+p);at+=6
 rom[rec+26:rec+28+len(out)]=out+b'\0\0'
put(0x210226,'H',len(offsets));put(0x210250,'I',used);put(0x21024c,'I',0x2a1000);put(0x2a1000,str(len(offsets))+'h',*offsets)
at=0x2a1100
for j,g in enumerate(groups):
 if g:put(gt+4*j,'I',at);put(at,'H'+'I'*len(g),len(g),*g);at+=2+len(g)*4
# Card image from the DOS ICONSA sheet, rendered as four native hardware sprites.
icons=(dos/'ICONSA').read_bytes();off=32+struct.unpack_from('<I',icons,48+2*16+12)[0]
im=Image.fromarray(np.frombuffer(icons[off:off+6336],np.uint8).reshape(72,88)).resize((64,48),Image.Resampling.NEAREST)
pal=runpy.run_path(str(work/'dos/color_experiment/preview.py'))['palette'](icons).astype(int)
# Pause palette zero, sampled in GX after opening the task card.
cram=[0x48,8,0x91,0xd9,0x99,0,0x1ff,0x124,0x49,0xdb,0x1b7,0x16d,0x124,0xd2,0x3a,0x20]
colors=np.array([[(v>>k&7)*255/7 for k in (0,3,6)] for v in cram[1:]])
px=(1+((pal[:,None]-colors)**2).sum(2).argmin(1))[np.array(im)]
tiles=[]
for y in (0,24):
 for x in (0,32):
  for xx in range(x,x+32,8):
   for yy in range(y,y+24,8):
    t=px[yy:yy+8,xx:xx+8].ravel();tiles.append((16*t[::2]+t[1::2]).astype(np.uint8).tobytes())
obj=0x2a2000;gfx=obj+128;frame=gfx+32;art=frame+96
rom[obj:obj+78]=rom[0x18cde6:0x18cde6+78];put(obj,'H',0);put(obj+54,'I',gfx);put(obj+62,'HH',0,0x4000)
put(gfx,'7HI',4,1536,8,8,0,0,0,frame)
rom[frame:frame+40]=rom[0x1420ae:0x1420ae+40]
put(frame,'4h',-24,-32,24,32);put(frame+12,'HH',1536,48);put(frame+18,'H',3);put(frame+28,'HHII',1536,2,1536,art)
for i in range(4):put(frame+40+8*i,'4H',128-34+24*(i//2),0x0e00,12*i,128-40+32*(i%2))
rom[art:art+1536]=b''.join(tiles)
put(u(u(0x212480+36)+14)+6,'I',obj)
# Use one pattern buffer for the large boat hull and helicopter sprite in Eco.
import tempfile,subprocess
with tempfile.TemporaryDirectory() as tmp:
 binary=Path(tmp)/'buffers.bin'
 subprocess.run(['vasm/vasmm68k_mot','-quiet','-Fbin','-o',str(binary),str(root/'buffers.asm')],check=True)
 blob=binary.read_bytes();rom[0x2a3000:0x2a3000+len(blob)]=blob
for site in (0x43396,0x43276):
 assert rom[site:site+4]==bytes.fromhex('302a0002')
 rom[site:site+8]=bytes.fromhex('4e714eb9002a3000')
runpy.run_path(str(work/'eco_flight_v4/build.py'))['checksum'](rom)
(root/'Jungle_Strike_Eco_Threat_Flight_TEST_v13.bin').write_bytes(rom)
(root/'build_report.json').write_text(json.dumps({'sha256':hashlib.sha256(rom).hexdigest(),'actors':ids}))
