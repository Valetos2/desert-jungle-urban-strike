import sys
sys.path.insert(0,str(work/'eco_flight_v9'))
from water import unpack_tiles
state=Path('upload/Jungle_Strike_Eco_Threat_Flight_TEST_v10.gs2').read_bytes()
pal=np.array([[((w(0x210400+2*i)>>k)&7)*34 for k in (1,5,9)] for i in range(64)],np.uint8);pal[62]=0;pal[63]=238
def asset(g,raw=None,po=0):
 width,height,bank=struct.unpack_from('>3H',rom,g)
 if raw is None:
  desc=u(0x210100+bank)
  if w(desc+36)==0x12:raw=unpack_tiles(rom,u(desc+42),w(desc+34))
  elif bank==0:raw=state[0x12478:0x22478]
  else:raise ValueError(hex(desc))
 idx=np.zeros((height*8,width*8),np.uint8);tab=u(g+22)
 for j in range(width*height):
  if w(g+16)==2:t=w(tab+2*j)
  else:
   v=rom[tab+2+j]
   if not v:continue
   t=(v&63)+((v&192)<<5)+w(tab)
  t+=w(g+30);p=np.frombuffer(raw[(t&2047)*32:((t&2047)+1)*32],np.uint8);p=np.stack((p>>4,p&15),axis=-1).reshape(8,8)
  if t&2048:p=p[:,::-1]
  if t&4096:p=p[::-1]
  y,x=divmod(j,width);idx[y*8:y*8+8,x*8:x*8+8]=np.where(p,p+16*((po+(t>>13))%4),0)
 return idx
t=asset(0x112e8c,rom[0x27d040:],1);y,x=np.indices(t.shape);left=x<40;roof=y<np.where(left,27+(x-2)*.5,46-(x-39)*.5);out=t.copy()
out[t==30]=42;out[t==31]=41
out[(t==19)&left]=20
out[(t==20)&~left&roof]=21
out[(t==21)&~left&~roof]=np.where(y<156-(x-40)*.50,22,21)[(t==21)&~left&~roof]
out[(t==17)&((x==14)|(y<36))]=63
out[(t==22)&(y<np.where(left,46+(x-40)*.5,46-(x-40)*.5)+6)]=62
out[(t==22)&~left&(x<66)&(y>62)&(y<156-(x-40)*.5)]=62
out[(t==22)&left&(y>130)&(x>18)&(x<31)]=62
# Grey checker pixels inside the glass are bounded by green horizontally/diagonally.
from scipy.ndimage import maximum_filter
glass=(t==31)|(t==30)
out[(y<65)&(t==22)&maximum_filter(glass,size=3)]=62

new=out.copy()
# Left abutment projects diagonally, right abutment stands at the front corner.
mask=((y>=124)&(x<=15)&(y+x>=137)&(y+x<=147))|((y>=135)&(x>=36)&(x<=45)&(y>=135+np.maximum(x-41,0))&(y<=158-np.maximum(x-41,0))&(t!=0))
for idx,dst in [(17,63),(18,18),(19,20),(20,21),(21,22),(22,62)]:
 new[mask&(t==idx)]=dst
# Restrict bright faces on the buttress at the far right of the tower.
edge=(x>=62)&(x<81)&(y>=122)&(y<=142)&(t!=0)
for idx,color in [(17,21),(18,21),(19,22),(20,22)]:
 new[edge&(t==idx)]=color
actual=np.array([[((w(0x210400+2*i)>>k)&7)*34 for k in (1,5,9)] for i in range(64)],int)
def encode(indices,bank,addr,source,tiles,palette_base=0,priority=0):
 height,width=indices.shape;attrs=[]
 by_tile={tile:k for k,tile in enumerate(tiles)}
 for yy in range(0,height,8):
  for xx in range(0,width,8):
   pix=indices[yy: yy+8,xx:xx+8].ravel();colors=pal[pix].astype(int)
   options=[]
   for row in range(4):
    diff=((colors[:,None]-actual[16*row+1:16*row+16])**2).sum(2)
    if row==1:diff[:,12:]=999999
    mapping=diff.argmin(1);loss=diff[np.arange(64),mapping]
    options.append((loss[pix!=0].sum(),row,np.where(pix,mapping+1,0)))
   _,row,px=min(options,key=lambda q:q[0])
   raw=(px[::2]*16+px[1::2]).astype(np.uint8).tobytes()
   if raw not in by_tile:by_tile[raw]=len(tiles);tiles.append(raw)
   attrs.append(priority|(((row-palette_base)%4)<<13)|by_tile[raw])
 rom[addr:addr+32]=rom[0x293000:0x293020]
 put(addr,'3H',width//8,height//8,bank*4);put(addr+10,'3H',0,height//8,width//4)
 put(addr+16,'HII',2,len(attrs)*2,source);put(addr+30,'H',0)
 put(source,str(len(attrs))+'H',*attrs)
def bankdata(bank,tiles,addr,raw):
 desc=u(0x210100+bank*4);rom[addr:addr+46]=rom[desc:desc+46]
 data=b''.join(tiles);put(addr+34,'HHII',len(data),2,len(data),raw);rom[raw:raw+len(data)]=data
 put(0x210100+bank*4,'I',addr)
# Rebuild tower and ruin as a compact common bank.
oldruin=asset(u(0x27b210-16),bytes(rom[0x27d040:]),1)
tiles=[bytes(32)]
encode(new,16,0x2c0000,0x2c0100,tiles,1,0x8000)
encode(oldruin,16,0x2c0400,0x2c0500,tiles,1,0x8000)
bankdata(16,tiles,0x2c0800,0x2c1000)
for rec in (0x27b210,0x27b250,0x27b290):put(rec,'I',0x2c0000);put(rec-16,'I',0x2c0400)
rec=0x279490;station=asset(u(rec));ruin=asset(u(rec-16))
# Bank 17 also serves unmodified pylons. Preserve their tile indices.
b=u(0x210100+17*4);raw=unpack_tiles(rom,u(b+42),w(b+34));tiles=[bytes(raw[k:k+32]) for k in range(0,len(raw),32)]
for i,(p,indices) in enumerate(((rec,station),(rec-16,ruin))):
 shifted=np.pad(indices,((1,7),(0,0)))
 encode(shifted,17,0x2c4000+i*0x400,0x2c4040+i*0x400,tiles,0,0x8000 if i==0 else 0)
 put(p,'I',0x2c4000+i*0x400);put(p+4,'H',w(p+4)-1)
put(rec+16,'H',w(rec+16)-7)
wire=asset(0x104718);drawing=np.zeros((48,56),np.uint8)
for sx,sy,end in [(6,34,2),(28,45,34)]:
 gap=50-(sx-6);best=None
 for mode in (0,-1):
  line=np.array([np.flatnonzero(wire[:,i])[mode] for i in range(96)])
  for k in range(96-gap):
   seg=line[k:k+gap+1]
   if np.abs(np.diff(seg)).max()>2:continue
   if sy+seg[-1]-seg[0]==end:best=(k,seg);break
  if best:break
 k,seg=best
 for j,v in enumerate(seg):
  if sx+j==56:continue  # last pixel belongs to the existing pylon terminal
  drawing[sy+v-seg[0],sx+j]=wire[v,k+j]
encode(drawing,17,0x2c4800,0x2c4840,tiles,0,0x8000)
bankdata(17,tiles,0x2c4a00,0x2c5000)
wire_rec=0x2c4b00;rom[wire_rec:wire_rec+36]=rom[0x27a6f0:0x27a6f0+36]
slot=w(0x210228);put(0x210228,'H',slot+1);put(wire_rec,'I4H',0x2c4800,403,57,409,64)
put(wire_rec+16,'2H',3264,480);rom[wire_rec+23]=slot;put(wire_rec+30,'I',0xff391e+30*slot)
ins=rom.index(bytes.fromhex('7e05'),0x27f000,0x27f040);rom[ins+1]=6;put(0x27f118,'I',wire_rec)
for p in (rec,0x27a5d0):
 a=p+34
 while rom[a]:a+=2+rom[a+1]
 rom[a:a+8]=bytes([22,4,10,10,1,slot,0,0])
