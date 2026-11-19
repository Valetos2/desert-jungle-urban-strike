from pathlib import Path
from collections import defaultdict,Counter
import json,struct
P=Path('strike_work/dos/unpacked/jungle');T=(P/'THINGS').read_bytes();G=Path('strikehd/rom/jungle_strike.bin').read_bytes()
w=lambda b,p:int.from_bytes(b[p:p+2],'little');gw=lambda p:int.from_bytes(G[p:p+2],'big');gu=lambda p:int.from_bytes(G[p:p+4],'big')
def dos(n):
 b=(P/f'LEVEL{n}').read_bytes();start=b.index(b'map'+('10' if n=='A' else n).encode())-4;names={}
 while w(b,start)!=65535:
  h=w(b,start+2);end=b.index(0,start+4);names[h]=b[start+4:end].decode();start=end+1
 e=(P/'EXECUTABLE').read_bytes();im=e[16*w(e,8):];ds=im[16*w(im,4):];desc=w(ds,0xda80+2*(9 if n=='A' else int(n)-1));count=w(ds,desc)
 offsets=sorted({w(b,w(b,i*2)+2+j*2) for i in range(count) if w(b,i*2) for j in range(w(b,w(b,i*2)))})
 out=[]
 for num,p in enumerate(offsets,1):
  typ=w(b,p);name=names.get(w(T,typ),'?');y,x,z=struct.unpack_from('<HHh',b,p+16);out.append(dict(id=num,type=typ,name=name,x=x,y=y,z=z,offset=p))
 return out
lev=gu(0x19292e+5*4);tab=gu(lev+0x3e);statics=[]
for sector in range(gw(lev)):
 p=gu(tab+sector*4)
 if p:
  for j in range(gw(p)):
   rec=gu(p+2+j*4);y,x,z=struct.unpack_from('>HHh',G,rec+16);statics.append(dict(pointer=rec,type=gu(rec),x=x,y=y,z=z))
results=defaultdict(Counter)
for r in dos('6'):
 match=min(statics,key=lambda g:(g['x']-r['x'])**2+(g['y']-r['y'])**2)
 if abs(match['x']-r['x'])+abs(match['y']-r['y'])<=12:results[r['name']][hex(match['type'])]+=1
print({k:dict(v) for k,v in results.items()})
Path('strike_work/eco_flight_v3/object_mapping.json').write_text(json.dumps({k:dict(v) for k,v in results.items()},indent=2)+'\n')
Path('strike_work/eco_flight_v3/dos_static.json').write_text(json.dumps(dos('A'),indent=2)+'\n')
# First integration batch: scenery with already established native equivalents.
allowed={'F165':0x10f4d6,'F166':0x10f508,'F167':0x10f530,'F168':0x10f5a2,'F174':0x10f8f4}
lev=gu(0x19292e+5*4);tab=gu(lev+0x3e);donors=[]
for sector in range(gw(lev)):
 p=gu(tab+sector*4)
 if p:
  donors.extend(gu(p+2+i*4) for i in range(gw(p)))
positions=[]
for row in dos('A'):
 if row['name'] not in allowed:continue
 candidates=[p for p in donors if gu(p)==allowed[row['name']]]
 # Choose a close donor to minimize sub-tile translation differences.
 p=min(candidates,key=lambda p:abs(gw(p+0x10)-row['y'])+abs(gw(p+0x12)-row['x']))
 row['donor']=p;positions.append(row)
Path('strike_work/eco_flight_v3/object_positions.json').write_text(json.dumps(positions,indent=2)+'\n')
print('Exported',len(positions),'objects')
