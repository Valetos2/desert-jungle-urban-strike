from pathlib import Path
import argparse,json,struct,sys,hashlib
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R.parent/'eco_flight_v4'))
from build import checksum
b=bytearray(next((R.parent/'eco_flight_v4').glob('*v4.bin')).read_bytes())
assert hashlib.sha256(b).hexdigest()=='1fb4914323df0924bcf00a9590fe619e23fa6c85f013f5f5ea220c4aff02fbf0'
def put(p,data): b[p:p+len(data)]=data
def u(p):return struct.unpack_from('>I',b,p)[0]
def w(p):return struct.unpack_from('>H',b,p)[0]
def long(p,v):struct.pack_into('>I',b,p,v)
def word(p,v):struct.pack_into('>H',b,p,v)
args=argparse.ArgumentParser()
args.add_argument('--without-debug-z',action='store_true')
debug=not args.parse_args().without_debug_z
put(0x213f00,bytes.fromhex('001c08')+b'10\0\x02\x09\x0aECO THREAT\0\xff')
put(0x273000,b[0xe1e00:0xe1e2a]);word(0x27300a,w(0xe0036+10))
put(0x213a80,struct.pack('>4I',0x273000,0xe20d0,0xe210e,0))
for n in [0xba8,0xbb4]:
 p=b.index(n.to_bytes(4,'big'),0x200900,0x200990);long(p,n-0x100)
# The donor mission scripts are invalid for the new object table. Use an
# independent table for native completion events. Event 4 enables mound 6.
long(0x210236,0x273100)
put(0x273100,bytes(32))
source=R.parent/'eco_flight_v3'
defs=json.loads((source/'dos_static.json').read_text())
existing=json.loads((source/'object_positions.json').read_text())
groups={}
for i,r in enumerate(existing):groups.setdefault(r['y']//512*10+r['x']//512,[]).append(0x250000+i*40)
donors={'F164':0x1ac88a,'F163':0x1abaf2,'F177':0x1abed0}
dos=(R.parent/'dos/unpacked/jungle/LEVELA').read_bytes()
new=[]
for row in defs:
 if row['name'] not in donors:continue
 i=47+len(new);rec=0x276000+64*len(new);donor=donors[row['name']];gfx=u(donor)
 put(rec,b[donor:donor+34]+bytes(4))
 top,left=struct.unpack_from('<HH',dos,row['offset']+4)
 put(rec+4,struct.pack('>4H',top,left,top+w(gfx+2),left+w(gfx)))
 put(rec+16,struct.pack('>HHh',row['y'],row['x'],row['z']))
 # Scenery stage: retain silhouette and physical dimensions, disable combat scripts.
 b[rec+22]=0x40 if row['id']==6 else 0x48
 long(rec+30,0xff391e+i*30)
 if row['id']==6:
  long(0x27310c,0x273150)
  put(0x273150,bytes([0,4,10,6,1,i,0,0]))
 slot=w(gfx+4)//4
 long(0x210100+4*slot,u(u(0x525b6+20)+slot*4))
 y,x=row['y']//512,row['x']//512
 groups.setdefault(y*10+x,[]).append(rec)
 for yy in range(max(0,y-1),min(7,y+2)):
  for xx in range(max(0,x-1),min(10,x+2)):
   p=0x21400c+16*(10*yy+xx);long(p,u(p)|1<<(slot-1))
 new.append(row['id'])
word(0x210228,47+len(new)+1) # one unused 30-byte slot reserves the debug latch
p=0x277000
for sector,entries in groups.items():
 long(0x210500+4*sector,p);data=struct.pack('>H',len(entries))+struct.pack('>'+str(len(entries))+'I',*entries);put(p,data);p+=len(data)
latch=0xff391e+30*(47+len(new))
import subprocess
subprocess.run(['vasm/vasmm68k_mot','-quiet','-Fbin','-o',str(R/'hooks.bin'),str(R/'hooks.asm')],check=True)
hook=(R/'hooks.bin').read_bytes().replace(bytes.fromhex('00ff4080'),latch.to_bytes(4,'big'))
put(0x274000,hook)
if debug:put(0x3cf4c,bytes.fromhex('4eb9002740004e714e71'))
put(0x40592,bytes.fromhex('4eb900274100'))
put(0x3db02,bytes.fromhex("4eb9002741804e71"))
checksum(b)
name='Jungle_Strike_Eco_Threat_Flight_TEST_v5'
(R/(name+'.bin')).write_bytes(b)
(R/'build_report.json').write_text(json.dumps(dict(sha256=hashlib.sha256(b).hexdigest(),new_ids=new,debug_z=debug),indent=2))
