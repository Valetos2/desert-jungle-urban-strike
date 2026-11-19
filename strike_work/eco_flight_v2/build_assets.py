"""Native Genesis water/snow interiors, DOS coast layout, and pause overview."""
from pathlib import Path
import json,struct
from collections import Counter
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'assets';OUT.mkdir(exist_ok=True)
R=Path('strikehd/rom/jungle_strike.bin').read_bytes();w=lambda a:int.from_bytes(R[a:a+2],'big');u=lambda a:int.from_bytes(R[a:a+4],'big')
res=Path('strike_work/dos/unpacked/jungle');blocks=(res/'BLOCKS10').read_bytes()
source=np.frombuffer(blocks[48:48+32768],np.uint8).reshape(128,16,16)
raw=np.frombuffer((res/'MAP10').read_bytes(),dtype='<u2').reshape(224,320)
colors=np.array([(0,0,0),(0,2,3),(0,2,2),(0,3,3),(7,7,7),(6,6,6),(5,5,5),(4,5,5),(3,4,4),(3,4,4),(5,6,6),(1,3,3),(4,3,1),(4,4,5),(2,3,3),(0,0,0)],np.int16)
cram=(colors[:,2]<<9)|(colors[:,1]<<5)|(colors[:,0]<<1)
(OUT/'palette.bin').write_bytes(cram.astype('>u2').tobytes())
stock={n:np.stack([np.frombuffer((ROOT/f'stock{n}_patterns.bin').read_bytes(),np.uint8)>>4,np.frombuffer((ROOT/f'stock{n}_patterns.bin').read_bytes(),np.uint8)&15],1).reshape(-1,8,8) for n in [2,6]}
def map_words(d):
 p=u(d+0x16)
 if w(d+0x10)==0x1a:
  v=np.frombuffer(R[p+2:p+514],np.uint8).astype(np.uint16)
  v=(v&63)|((v&128)<<5)|((v&64)<<5);v+=w(p)
 else:v=np.frombuffer(R[p:p+1024],dtype='>u2')
 return (v.astype(np.uint16)+w(d+0x1e)).reshape(16,32)
# Complete original native map blocks retain adjoining wave/snow pixels.
stock_maps={2:map_words(0xfd132),6:map_words(0x102e30)}
def native(n,x,y):
 result=np.zeros((16,16),np.uint8)
 lev=u(0x19292e+(n-1)*4);p=np.frombuffer(R[u(lev+0x46):u(lev+0x46)+128],dtype='>u2');rgb=np.stack([(p>>1)&7,(p>>5)&7,(p>>9)&7],1)
 for i in range(4):
  v=int(stock_maps[n][(y%8)*2+i//2,(x%16)*2+i%2])
  t=stock[n][v&2047];t=t[::-1] if v&4096 else t;t=t[:,::-1] if v&2048 else t
  if n==2:
   lut=np.array([1,1,2,3,3,11,4,5,6,7,8,9,10,12,13,14],np.uint8)
  else:
   src=rgb[(v>>13&3)*16:((v>>13&3)+1)*16]
   lut=4+((src[:,None,:]-colors[None,4:9,:])**2).sum(2).argmin(1)
  result[i//2*8:i//2*8+8,i%2*8:i%2*8+8]=lut[t]
 return result
world=np.empty((3584,5120),np.uint8);counts=Counter()
for y in range(224):
 for x in range(320):
  v=int(raw[y,x]);t=source[v&255];s=set(t.ravel())
  if s<={0,1,2,3}:
   t=native(2,x,y);counts['water']+=1
  elif s<={4,5,6,7,8,13,14}:
   t=native(6,x,y);counts['snow']+=1
  else:
   t=t[::-1] if v&512 else t;t=t[:,::-1] if v&256 else t;counts['coast']+=1
  world[y*16:y*16+16,x*16:x*16+16]=t
# Pack exact 8x8 patterns and reflected aliases, like the earlier converter.
def pack(im):
 pats=[];lookup={};names=[]
 for y in range(0,im.shape[0],8):
  for x in range(0,im.shape[1],8):
   t=im[y:y+8,x:x+8];key=t.tobytes()
   if key not in lookup:
    i=len(pats);pats.append(t.copy())
    for hf,vf in [(0,0),(1,0),(0,1),(1,1)]:
     v=t[::-1] if vf else t;v=v[:,::-1] if hf else v
     lookup.setdefault(v.tobytes(),i|(hf<<11)|(vf<<12))
   names.append(lookup[key])
 a=np.array(pats,dtype=np.uint8).reshape(-1,64)
 return ((a[:,::2]<<4)|a[:,1::2]).tobytes(),np.array(names,dtype='>u2').reshape(im.shape[0]//8,im.shape[1]//8)
patterns,names=pack(world);assert len(patterns)//32<1024
(OUT/'patterns.bin').write_bytes(patterns)
base=0x300000;template=bytearray(R[u(u(u(0x192932)+0x5c)):u(u(u(0x192932)+0x5c))+32]);unique=[];lookup={};sectors=[]
for y in range(28):
 for x in range(20):
  block=names[y*16:y*16+16,x*32:x*32+32].tobytes()
  if block not in lookup:lookup[block]=len(unique);unique.append(block)
  sectors.append(lookup[block])
size=560*4;blob=bytearray(size)
for i,block in enumerate(unique):
 d=template.copy();struct.pack_into('>H',d,0x10,2);struct.pack_into('>I',d,0x16,base+size+i*1056+32);struct.pack_into('>H',d,0x1e,0)
 blob.extend(d);blob.extend(block)
for i,v in enumerate(sectors):struct.pack_into('>I',blob,i*4,base+size+v*1056)
(OUT/'native_ground.bin').write_bytes(blob)
# Downsample the actual generated level, so the overview has the same shores.
rgb=(colors*255//7).astype(np.uint8);image=Image.fromarray(rgb[world]);image.resize((1280,896),Image.Resampling.NEAREST).save(ROOT/'terrain_preview.png')
mini=np.array(image.resize((192,136),Image.Resampling.BOX));dist=((mini[:,:,None,:].astype(np.int32)-rgb[None,None,:,:])**2).sum(3);mi=dist.argmin(2).astype(np.uint8)
# The pause UI leaves room for 29 map patterns. Preserve that budget so the
# expanded overview cannot overwrite HUD/font tiles at fixed VRAM addresses.
binary=(mini.astype(np.int32).mean(2)>110).astype(np.uint8)
cells=np.array([binary[y:y+8,x:x+8] for y in range(0,136,8) for x in range(0,192,8)])
choices=[np.zeros((8,8),np.uint8),np.ones((8,8),np.uint8)]
for _ in range(27):
 variants=np.array([t[::-1] if vf else t for t in choices for vf in [0,1]])
 variants=np.concatenate([variants,variants[:,:,::-1]])
 distance=(cells[:,None,:,:]!=variants[None,:,:,:]).sum((2,3)).min(1)
 choices.append(cells[distance.argmax()].copy())
words=[];decoded=[]
for cell in cells:
 best=min(((int((cell!=(t[::-1] if vf else t)[:,::-1] if hf else cell!=(t[::-1] if vf else t)).sum()),i,hf,vf) for i,t in enumerate(choices) for hf in [0,1] for vf in [0,1]),key=lambda a:a[0])
 _,i,hf,vf=best;words.append(i|(hf<<11)|(vf<<12));t=choices[i][::-1] if vf else choices[i];decoded.append(t[:,::-1] if hf else t)
a=np.where(np.array(choices).reshape(-1,64),6,13).astype(np.uint8)
pp=((a[:,::2]<<4)|a[:,1::2]).tobytes();pm=np.array(words,dtype='>u2').reshape(17,24)
mi=np.where(np.array(decoded).reshape(17,24,8,8).transpose(0,2,1,3).reshape(136,192),5,1).astype(np.uint8)
(OUT/'pause_patterns.bin').write_bytes(pp);(OUT/'pause_map.bin').write_bytes(pm.tobytes());(OUT/'pause_palette.bin').write_bytes((OUT/'palette.bin').read_bytes());Image.fromarray(rgb[mi]).save(ROOT/'pause_preview.png')
report=dict(counts);report.update(patterns=len(patterns)//32,pause_patterns=len(pp)//32,blocks=len(unique));(ROOT/'assets_report.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
