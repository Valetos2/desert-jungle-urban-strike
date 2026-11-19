"""Convert the original DOS DASHMAPA overview; retain full 192x136 artwork."""
from pathlib import Path
import numpy as np,json
from PIL import Image
R=Path(__file__).resolve().parent;b=Path('strike_work/dos/unpacked/jungle/DASHMAPA').read_bytes()
p=b.index(b'PALETTE ');source=np.frombuffer(b[p+32:p+32+48],np.uint8).reshape(16,3).astype(np.int32)*255//63
# Existing pause UI palette 0: do not change the HUD's colors.
cram=np.array([0x220,0x20,0x442,0x662,0x462,0,0xeee,0x888,0x222,0x666,0xcce,0xaaa,0x888,0x644,0xe4,0x80])
rgb=np.stack([(cram>>1)&7,(cram>>5)&7,(cram>>9)&7],1)*255//7
mapping=((source[:,None,:]-rgb[None,:,:])**2).sum(2).argmin(1)
# Water uses a cold dark ramp rather than the UI's green-tinted nearest color.
mapping[6:9]=[8,2,13]
a=mapping[np.frombuffer(b[48:48+192*136],np.uint8).reshape(136,192)].astype(np.uint8)
pats=[];lookup={};names=[]
for y in range(0,136,8):
 for x in range(0,192,8):
  t=a[y:y+8,x:x+8]
  if t.tobytes() not in lookup:
   i=len(pats);pats.append(t)
   for h,v in [(0,0),(1,0),(0,1),(1,1)]:
    z=t[::-1] if v else t;z=z[:,::-1] if h else z;lookup.setdefault(z.tobytes(),i|(h<<11)|(v<<12))
  names.append(lookup[t.tobytes()])
pat=np.array(pats,np.uint8).reshape(-1,64);raw=((pat[:,::2]<<4)|pat[:,1::2]).tobytes()
(R/'assets/pause_patterns.bin').write_bytes(raw);(R/'assets/pause_map.bin').write_bytes(np.array(names,dtype='>u2').tobytes())
Image.fromarray(rgb[a].astype('uint8')).resize((576,408),Image.Resampling.NEAREST).save(R/'pause_preview.png')
(R/'pause_report.json').write_text(json.dumps({'source':'DOS DASHMAPA','size':[192,136],'patterns':len(pats),'mapping':mapping.tolist()},indent=2)+'\n');print(len(pats),len(raw))
