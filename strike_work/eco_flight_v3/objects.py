"""Builder fragment: native trees and landing platforms at DOS positions."""
rows=json.loads((ROOT/'object_positions.json').read_text())
# Tile graphics variants used by the Snow Fortress versions of these objects.
snowtab=ptr(0x525b6+5*4)
for slot in [15,18]:l(tiletab+slot*4,ptr(snowtab+slot*4))
# Independent count/list/storage for static objects; the one dynamic is player.
# Remap the platform art to the existing vehicle palette instead of letting
# its original palette-1 pixels borrow the new water colours.
import numpy as np
pal0=ptr(ptr(0x19292e+5*4)+0x46)
src=np.array([word(pal0+32+i*2) for i in range(16)])
dst=np.array([int.from_bytes(b[palettes+64+i*2:palettes+66+i*2],'big') for i in range(16)])
def rgb(v):return np.stack([(v>>1)&7,(v>>5)&7,(v>>9)&7],1).astype(int)
lut=((rgb(src)[:,None,:]-rgb(dst)[None,:,:])**2).sum(2).argmin(1).astype(np.uint8);lut[0]=0
raw=np.frombuffer((ROOT/'stock_pad_patterns.bin').read_bytes(),np.uint8)
newraw=((lut[raw>>4]<<4)|lut[raw&15]).tobytes()
plat=bytearray(original[0x71560:0x71560+46]);struct.pack_into('>H',plat,0x24,2);struct.pack_into('>I',plat,0x26,len(newraw));struct.pack_into('>I',plat,0x2a,0x263000)
free(0x260000,plat);free(0x263000,newraw);l(tiletab+18*4,0x260000)
wrapper=bytearray(original[0x10f8f4:0x10f8f4+32]);struct.pack_into('>I',wrapper,0x16,0x260200)
free(0x260100,wrapper);mp=ptr(0x10f8f4+0x16)
mapdata=b''.join(struct.pack('>H',(word(mp+i*2)&~0x6000)|0x4000) for i in range(22*12))
free(0x260200,mapdata)
w(level+0x28,len(rows));groups={};report=[]
for i,row in enumerate(rows):
 donor=row['donor'];a=0x250000+i*40
 record=bytearray(original[donor:donor+34])+b'\0\0'
 if row['name']=='F174':struct.pack_into('>I',record,0,0x260100)
 y0=word(donor+0x10);x0=word(donor+0x12)
 dy=row['y']-y0;dx=row['x']-x0
 for off,delta,maximum in [(4,dy,False),(6,dx,False),(8,dy,True),(10,dx,True)]:
  adjustment=-(-delta//8) if maximum else delta//8
  struct.pack_into('>h',record,off,word(donor+off)+adjustment)
 struct.pack_into('>HHh',record,0x10,row['y'],row['x'],row['z'])
 struct.pack_into('>I',record,0x1e,0xff391e+i*30)
 free(a,record)
 sector=(row['y']//512)*10+row['x']//512
 groups.setdefault(sector,[]).append(a)
 # Keep banks available for objects whose image overlaps a neighbouring sector.
 bit=1<<(word(ptr(donor)+4)//4-1)
 for yy in range(max(0,sector//10-1),min(7,sector//10+2)):
  for xx in range(max(0,sector%10-1),min(10,sector%10+2)):
   at=0x214000+(yy*10+xx)*16+12
   l(at,int.from_bytes(b[at:at+4],'big')|bit)
 report.append({'id':row['id'],'name':row['name'],'position':[row['x'],row['y'],row['z']],'definition':hex(a),'donor':hex(donor)})
at=0x252000
for sector,items in sorted(groups.items()):
 data=struct.pack('>H',len(items))+b''.join(struct.pack('>I',x) for x in items)
 free(at,data);l(empty+sector*4,at);at+=len(data)
(ROOT/'objects_report.json').write_text(json.dumps(report,indent=2)+'\n')
# Native colour cycling, relocated to the water-only colours in palette line 1.
free(0x211100,bytes.fromhex('0c79000900ff139e660ed1fc00000032243c0000c0324e75d1fc00000006243c0000c0064e75'))
assert original[0x3ddd2:0x3ddde]==bytes.fromhex('d1fc00000006243c0000c006')
b[0x3ddd2:0x3ddde]=bytes.fromhex('4eb9002111004e714e714e71')
