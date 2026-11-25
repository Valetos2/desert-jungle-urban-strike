"""Build Eco Threat flight test 14 from the local v13 image and DOS resources."""
from pathlib import Path
import struct,csv,runpy,hashlib,json
import numpy as np
from PIL import Image
root=Path(__file__).resolve().parent
work=root.parent
rom=bytearray(next((work/'eco_flight_v13').glob('*.bin')).read_bytes())
assert hashlib.sha256(rom).hexdigest()==json.loads((work/'eco_flight_v13/build_report.json').read_text())['sha256']
def w(a):return struct.unpack_from('>H',rom,a)[0]
def u(a):return struct.unpack_from('>I',rom,a)[0]
def put(a,fmt,*v):struct.pack_into('>'+fmt,rom,a,*v)
dos=work/'dos/unpacked/jungle'
d=(dos/'LEVELA').read_bytes()
rows={int(r['index']):r for r in csv.DictReader(open(work/'dos/eco_dynamic.csv'))}
prior=json.loads((work/'eco_flight_v10/build_report.json').read_text())['actors']
known={v['dos_index'] for v in prior}|{v['id'] for v in json.loads((work/'eco_flight_v11/build_report.json').read_text())['mission1']}|{18,*range(25,37)}
ids=sorted(({i for i,r in rows.items() if int(r['group']) in (1,10,25,29,61,64) and int(r['flags_14_15_16'][:2],16)&8}|set(range(37,48)))-known)

types={0xa55e:0x18edb4,0xa6a2:0x18d006,0xaaa2:0x190150,0xb1e8:0x18f2fa,0xa046:0x18e65a,0xa9ec:0x18ded8,0xa848:0x18dc5a,0xb2a6:0x18de14,0xb332:0x18d77e,0xa4e6:0x18d9c2,0x9fe2:0x18e594}
n=w(0x210226);table=u(0x21024c);old=list(struct.unpack_from('>'+str(n)+'h',rom,table))
offsets=old.copy()
longs=[i for i in ids if int(rows[i]['flags_14_15_16'][2:4],16)&128]
# v13 has six original long slots and all extended mission-two slots.
boundary=-42*(6+sum(1 for i in [18,*range(25,37)] if int(rows[i]['flags_14_15_16'][2:4],16)&128))
shift=42*len(longs)
for i,v in enumerate(old):
 if v<=boundary:offsets[i]-=shift
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
 r=rows[i];a=int(r['level_offset'],16);rec=0x2b0000+128*j
 delta=(boundary-42*longs.index(i)) if i in longs else -used
 if i not in longs:used+=14
 offsets.append(delta)
 typ=int(r['type_ds'],16);native=types[typ]
 route=0
 if le(d,a+4):
  off=(le(d,a+6)-0x1a7e+le(mz,4))*16+le(d,a+4)
  end=off+24
  while mz[end:end+2]!=bytes(2):end+=2
  route=0x2b4000+j*256
  seq=mz[off:end+2];assert len(seq)<=256;rom[route:route+len(seq)]=seq
 sector=int(r['sector']);groups[sector].append(rec)
 put(rec,'IIIHHh',native,route,0xfffba6+delta,*struct.unpack_from('<HHh',d,a+12))
 rom[rec+18:rec+26]=d[a+18:a+23]+bytes(3)
 at=a+26;out=bytearray()
 while i in range(37,48) and d[at]:
  evt,length,op,sub=d[at:at+4];p=d[at+4:at+6]
  if op==6:p=bytes([1,n+ids.index(p[1])])
  else:assert (op,sub)==(2,26)
  out.extend(bytes([evt,4,op,sub])+p);at+=6
 rom[rec+26:rec+28+len(out)]=out+b'\0\0'
assert len(offsets)==len(set(offsets)) and len(ids)*256<=0x4000
put(0x210226,'H',len(offsets));put(0x210250,'I',used);put(0x21024c,'I',0x2b8000);put(0x2b8000,str(len(offsets))+'h',*offsets)
at=0x2b8500
for j,g in enumerate(groups):
 if g:put(gt+4*j,'I',at);put(at,'H'+'I'*len(g),len(g),*g);at+=2+len(g)*4
# Card image from the DOS ICONSA sheet, rendered as four native hardware sprites.
icons=(dos/'ICONSA').read_bytes();off=32+struct.unpack_from('<I',icons,48+3*16+12)[0]
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
obj=0x2b9000;gfx=obj+128;frame=gfx+32;art=frame+96
rom[obj:obj+78]=rom[0x18cde6:0x18cde6+78];put(obj,'H',0);put(obj+54,'I',gfx);put(obj+62,'HH',0,0x4000)
put(gfx,'7HI',4,1536,8,8,0,0,0,frame)
rom[frame:frame+40]=rom[0x1420ae:0x1420ae+40]
put(frame,'4h',-24,-32,24,32);put(frame+12,'HH',1536,48);put(frame+18,'H',3);put(frame+28,'HHII',1536,2,1536,art)
for i in range(4):put(frame+40+8*i,'4H',128-34+24*(i//2),0x0e00,12*i,128-40+32*(i%2))
rom[art:art+1536]=b''.join(tiles)
put(u(u(0x212480+36)+26)+6,'I',obj)

# Static shelters activate the local guards or scientist when destroyed.
static=json.loads((work/'eco_flight_v3/dos_static.json').read_text())
extras=[r for r in static if r['name'] in ('F164','F163','F177')]
for house,person in [(67,47),(83,37),(84,38)]:
 rec=0x276000+64*next(j for j,r in enumerate(extras) if r['id']==house)
 assert rom[rec+34:rec+36]==bytes(2)
 rom[rec+34:rec+42]=bytes([22,4,6,6,1,n+ids.index(person),0,0])
# Native debrief dispatcher, preserving original DOS thresholds.
import textwrap
flic=(dos/'FLICDATA').read_bytes()
events=[r for r in json.loads((work/'dos/eco_objectives.json').read_text())['message_events'] if r['outcome'] and r['group'] in (92,60,65)]
put(0x212400+36,'I',0x2ba000);put(0x2ba000,'H',len(events)-1)
for j,r in enumerate(events):
 rec=0x2ba100+32*j;addr=0x2ba300+512*j
 put(0x2ba002+4*j,'I',rec)
 rom[rec:rec+26]=rom[0xe5c38:0xe5c38+26]
 put(rec,'H4B',79 if r['group']==92 else r['group'],1,j,r['event_kind'],r['threshold'])
 put(rec+22,'I',addr)
 msg=flic[le(flic,2*r['flicdata_index']):].split(bytes(1))[0].decode('ascii')
 block=b''.join(bytes([2,2,20+k])+line.lower().encode()+bytes([0,255]) for k,line in enumerate(textwrap.wrap(msg,36)))
 rom[addr:addr+len(block)+1]=block[:-1]+bytes([240,255])
# Two native delayed intelligence reports. The event record has no immediate
# movie pointer. On opening the map, the scene's static text uses the DOS caption.
put(0x2ba000,'H',4)
for j,(group,kind,index) in enumerate(((22,1,175),(65,2,176))):
 rec=0x2ba180+64*j;caption=0x2bc100+512*j
 put(0x2ba00e+j*4,'I',rec)
 rom[rec:rec+32]=rom[0xe6756:0xe6756+26]+bytes(6)
 put(rec,'H4B',group,0,3+j,kind,1);put(rec+32,'H',0xffff)
 put(rec+26,'I',caption)
 msg=flic[le(flic,2*index):].split(bytes(1))[0].decode('ascii')
 lines=textwrap.wrap(msg,21)
 block=b''.join(bytes([3,17,6+(k*14)//max(1,len(lines)-1)])+line.encode()+bytes([0]) for k,line in enumerate(lines))+bytes([255])
 rom[caption:caption+len(block)]=block
assert rom[0x44a90:0x44a98]==bytes.fromhex('4cdf00076100ff06')
rom[0x44a90:0x44a98]=bytes.fromhex('4ef9002be1004e71')

# Register loss of the station buildings under their DOS group.
for j,row in enumerate(extras):
 if 43<=row['id']<=49:
  rec=0x276000+64*j
  col=u(rec+26);rom[0x2bb000:0x2bb050]=rom[col:col+80]
  put(0x2bb00c,'H',79);put(rec+26,'I',0x2bb000)
import subprocess,tempfile
with tempfile.TemporaryDirectory() as tmp:
 binary=Path(tmp)/'retry.bin'
 subprocess.run(['vasm/vasmm68k_mot','-quiet','-Fbin','-o',str(binary),str(root/'retry.asm')],check=True)
 data=binary.read_bytes()
 rom[0x2be000:0x2be000+len(data)]=data
 assert u(0x3cf4e)==0x274000
 put(0x3cf4e,'I',0x2be000)
exec(compile((root/'scenery.py').read_text(),'scenery.py','exec'))
runpy.run_path(str(work/'eco_flight_v4/build.py'))['checksum'](rom)
(root/'Jungle_Strike_Eco_Threat_Flight_TEST_v14.bin').write_bytes(rom)
(root/'build_report.json').write_text(json.dumps({'sha256':hashlib.sha256(rom).hexdigest(),'actors':ids}))
