from pathlib import Path
from collections import Counter,defaultdict
import struct,json
R=Path('strikehd/rom/jungle_strike.bin').read_bytes()
w=lambda p:int.from_bytes(R[p:p+2],'big')
l=lambda p:int.from_bytes(R[p:p+4],'big')&0xffffff
results=[]
for level in range(1,10):
 p=l(0x19292e+(level-1)*4);height,width=w(p+20)//16,w(p+22)//16;grid=w(p+6);tab=l(p+0x5c)
 def cell(x,y):
  tm=l(tab+((y//16)*grid+x//32)*4);mp=l(tm+0x16);idx=(y%16)*32+x%32
  if w(tm+0x10)==0x1a:
   v=R[mp+2+idx];value=(v&63)|((v&128)<<5)|((v&64)<<5);value+=w(mp)
  else:value=w(mp+idx*2)
  return (w(tm+4),w(tm+0x1e),value)
 raw=Path(f'strike_work/dos/unpacked/jungle/MAP{level}X').read_bytes();ids=struct.unpack('<'+'H'*(len(raw)//2),raw)
 if len(ids)!=width*height:results.append({'level':level,'error':'dimension mismatch'});continue
 pairs=defaultdict(Counter)
 for i,v in enumerate(ids):
  x=(i%width)*2;y=(i//width)*2
  g=tuple(cell(x+dx,y+dy) for dy in range(2) for dx in range(2))
  pairs[v][g]+=1
 matches=sum(c.most_common(1)[0][1] for c in pairs.values())
 results.append({'level':level,'width_pixels':width*16,'height_pixels':height*16,'cells':len(ids),'best_per_DOS_tile_matches':matches,'fraction':matches/len(ids),'unique_DOS_tiles':len(pairs),'unique_Genesis_quads':len(set(g for c in pairs.values() for g in c))})
print(json.dumps(results,indent=2));Path('strike_work/dos/map_correspondence.json').write_text(json.dumps(results,indent=2))
