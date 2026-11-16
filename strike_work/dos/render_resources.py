from pathlib import Path
import struct
from PIL import Image
ROOT=Path(__file__).resolve().parent
P=ROOT/'unpacked/jungle'
O=ROOT/'previews';O.mkdir(exist_ok=True)
def graphic(name):
 b=(P/name).read_bytes(); pal=b.find(b'PALETTE '); colors=b[pal+32:]; palette=[min(255,round(v*255/63)) for v in colors];palette=(palette+[0]*768)[:768]
 return b,palette
for n in ['DASHMAP1','DASHMAP2','DASHMAP6','DASHMAPA','BRIEFMA','BRIEFSA']:
 b,pal=graphic(n);w,h=struct.unpack_from('<HH',b,44)
 if w and h and w*h<=len(b)-48:
  im=Image.frombytes('P',(w,h),b[48:48+w*h]);im.putpalette(pal);im.resize((w*3,h*3),Image.Resampling.NEAREST).save(O/(n+'.png'))
for n in ['BLOCKS10','BLOCKS6X','BLOCKS2X']:
 b,pal=graphic(n);count=struct.unpack_from('<H',b,40)[0];im=Image.new('P',(16*16,16*((count+15)//16)));im.putpalette(pal)
 for i in range(count):im.paste(Image.frombytes('P',(16,16),b[48+i*256:48+(i+1)*256]),((i%16)*16,(i//16)*16))
 im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST).save(O/(n+'.png'))
# Dimensions for known levels follow verified Genesis bounds; MAP10 shape remains a hypothesis.
for name,blocks,w,h in [('MAP1X','BLOCKS1X',256,256),('MAP2X','BLOCKS2X',320,224),('MAP6X','BLOCKS6X',256,192),('MAP10','BLOCKS10',320,224)]:
 b,pal=graphic(blocks);raw=(P/name).read_bytes();ids=struct.unpack('<'+'H'*(len(raw)//2),raw);im=Image.new('P',(w*16,h*16));im.putpalette(pal)
 for i,v in enumerate(ids):
  t=Image.frombytes('P',(16,16),b[48+(v&255)*256:48+((v&255)+1)*256])
  if v&256:t=t.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  if v&512:t=t.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
  im.paste(t,((i%w)*16,(i//w)*16))
 im.resize((w*3,h*3),Image.Resampling.NEAREST).save(O/(name+'_candidate.png'))
