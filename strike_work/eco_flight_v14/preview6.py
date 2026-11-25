"""Capture Snow Fortress in GX using a temporary image for each camera-matched view."""
import struct,runpy,tempfile,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parent
sys.path.insert(0,'strike_work/tools')
from retro import Core
sys.path.insert(0,'strike_work/eco_flight_v9')
from water import unpack_tiles
checksum=runpy.run_path('strike_work/eco_flight_v4/build.py')['checksum']
base=next(root.glob('*.bin')).read_bytes(); shots=[];cameras=[]
for modified in (False,True):
 b=bytearray(base)
 u=lambda a:struct.unpack_from('>I',b,a)[0]
 w=lambda a:struct.unpack_from('>H',b,a)[0]
 def put(a,fmt,*values):struct.pack_into('>'+fmt,b,a,*values)
 lev=u(0x19292e+20);tab=u(lev+0x42)
 x,y=477,2848
 player=0x1adaba
 put(player+12,'2H',y,x)
 newsector=y//512*w(lev+2)+x//512;b[player+22]=newsector
 cursor=0x2e0000
 for k in range(w(lev)):
  src=u(tab+4*k);entries=[u(src+2+4*i) for i in range(w(src))] if src else []
  entries=[ptr for ptr in entries if ptr!=player]
  if k==newsector:entries.append(player)
  put(tab+4*k,'I',cursor if entries else 0)
  put(cursor,'H'+'I'*len(entries),len(entries),*entries);cursor+=2+4*len(entries)
 put(0x38c92,'I',5)
 put(0x40a4c,'H',0x4e75)  # Keep scenery intact during the long diagnostic camera flight.
 if modified:
  # Draw the relocated native station and the two selected wire strands as one tile rectangle.
  bankptr=u(0x525b6+20)+17*4;desc=u(bankptr)
  raw=unpack_tiles(b,u(desc+42),w(desc+34));tiles=[bytes(raw[i:i+32]) for i in range(0,len(raw),32)]
  def pixels(g,raw):
   width,height=struct.unpack_from('>2H',b,g);out=np.zeros((height*8,width*8),np.uint16)
   for j in range(width*height):
    attr=w(u(g+22)+2*j)+w(g+30)
    a=np.frombuffer(raw[(attr&2047)*32:((attr&2047)+1)*32],np.uint8)
    px=np.stack((a>>4,a&15),-1).reshape(8,8)
    if attr&2048:px=px[:,::-1]
    if attr&4096:px=px[::-1]
    yy,xx=divmod(j,width);out[yy*8:yy*8+8,xx*8:xx*8+8]=np.where(px,px+16*((attr>>13)&3),0)
   return out
  g=0x10f754;px=pixels(g,raw)
  out=np.zeros((152,136),np.uint16);out[49:49+px.shape[0],:128]=px
  # Reuse wire silhouette, paint it with the original donor wire ink.
  wires=pixels(0x2c4800,b[u(u(0x210100+68)+42):]);ink=1
  for yy,xx in zip(*np.nonzero(wires)):out[16+yy,80+xx]=ink
  attrs=[]
  for yy in range(0,152,8):
   for xx in range(0,136,8):
    a=out[yy:yy+8,xx:xx+8].ravel();row=int(a.max())//16
    packed=bytes((((a[::2]&15)*16)+(a[1::2]&15)).astype('uint8'))
    if packed not in tiles:tiles.append(packed)
    attrs.append(0x8000+row*8192+tiles.index(packed))
  dst=0x2d0000;b[dst:dst+32]=b[g:g+32];put(dst,'2H',17,19);put(dst+12,'2H',19,34);put(dst+18,'II',len(attrs)*2,dst+64);put(dst+30,'H',0)
  put(dst+64,str(len(attrs))+'H',*attrs)
  put(0x1ad332,'I4H',dst,337,47,356,64)
  data=b''.join(tiles);put(desc+34,'HHII',len(data),2,len(data),0x2d1000);b[0x2d1000:0x2d1000+len(data)]=data
 checksum(b)
 with tempfile.TemporaryDirectory() as tmp:
  f=Path(tmp)/'six.bin';f.write_bytes(b);c=Core(f)
  for i in range(4400):
   c.run(1,'S' if i%150<8 else '')
   if c.rw(0x139e)==5 and c.lib.retro_debug_reg(16) in (0x3d770,0x3d778):break
  else:raise RuntimeError('Snow Fortress boot')
  c.run(150);c.wb(0x12b7,14)
  def long(at):return c.rw(at)*65536+c.rw(at+2)
  pos=long(long(0x29e8)+34);x0,y0=c.rw(pos),c.rw(pos+4)
  steps=max(abs(x-x0),abs(y-y0))//5+1
  for k in range(1,steps+1):
   c.wl(pos,(x0+(x-x0)*k//steps)<<16);c.wl(pos+4,(y0+(y-y0)*k//steps)<<16);c.run(2)
  best=100000;tx,ty=400,2848
  for k in range(700):
   cx,cy=c.rw(0x1386),c.rw(0x1384)
   distance=abs(cx-303)+abs(cy-2656)
   if distance<best:
    best=distance;camera=(cx,cy);frame=Image.fromarray(c.frame)
   if k%12==0:
    tx+=max(-8,min(8,303-cx));ty+=max(-8,min(8,2656-cy))
   c.wl(pos,tx<<16);c.wl(pos+4,ty<<16);c.run(1)
  cameras.append(camera);shots.append(frame);c.lib.retro_unload_game();c.lib.retro_deinit()
left=max(x for x,y in cameras);top=max(y for x,y in cameras)
width=320-(left-min(x for x,y in cameras));height=224-(top-min(y for x,y in cameras))
assert width>=160 and height>=128,(width,height)
canvas=Image.new('RGB',(width*4,height*2+32),'#21232a')
for i,(s,(x,y)) in enumerate(zip(shots,cameras)):
 crop=s.crop((left-x,top-y,left-x+width,top-y+height))
 canvas.paste(crop.resize((width*2,height*2),Image.Resampling.NEAREST),(width*2*i,32))
 ImageDraw.Draw(canvas).text((width*2*i+12,10),('Snow Fortress - original','Snow Fortress - preview (-7 px, 96 x 88)')[i],fill='white')
canvas.save('/mnt/data/Snow_Fortress_station_v14.png')
