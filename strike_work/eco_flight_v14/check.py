"""Exercise the native Genesis event paths and a missed sector spawn in GX."""
from pathlib import Path
import struct,json,runpy,tempfile
root=Path(__file__).resolve().parent
m=runpy.run_path(str(root.parent/'eco_flight_v11/check.py'))
spawn=m['spawn'];rom=next(root.glob('*.bin'));spawn.__globals__['ROM']=rom
long=m['ram_long'];close=m['closed'];b=rom.read_bytes()
static=json.loads((root.parent/'eco_flight_v3/dos_static.json').read_text())
extra=[r for r in static if r['name'] in ('F164','F163','F177')]
ids=json.loads((root/'build_report.json').read_text())['actors']
def house(i):
 j=next(j for j,r in enumerate(extra) if r['id']==i)
 return extra[j],b[0x276000+64*j+23]
def live(i):return struct.unpack_from('>I',b,0x2b0000+128*ids.index(i)+8)[0]
def visit(c,x,y):
 pos=long(c,long(c,0x29e8)+34)
 a,d=c.rw(pos),c.rw(pos+4);steps=max(abs(x-a),abs(y-d))//12+1
 for j in range(1,steps+1):
  c.wl(pos,(a+(x-a)*j//steps)<<16);c.wl(pos+4,(d+(y-d)*j//steps)<<16);c.run(2)
 c.run(80)
def call(c,addr,regs):
 sp=c.lib.retro_debug_reg(15)-4;c.wl(sp,m['pc'](c))
 for r,v in [(15,sp),(16,addr),*regs]:c.lib.retro_debug_set(r,v)
 c.run(40)
r,_=house(43);c,_=spawn(r['x']-40,r['y']);counts=[]
for i in (43,44,45):
 m['native_destroy'](c,house(i)[1]);counts.append((c.rb(0x1110),long(c,0x1104)))
assert counts==[(2,0),(1,0),(0,0x2ba700)],counts
close(c)
# Set up the precise missing-radar state from the GS0 without requiring
# cross-version compatibility of the two runtime slot tables.
radar=0x298380
with tempfile.TemporaryDirectory() as tmp:
 diag=bytearray(b);diag[radar+20]&=0xf7
 f=Path(tmp)/'diag.bin';f.write_bytes(diag);spawn.__globals__['ROM']=f
 c,_=spawn(143,1630);s=struct.unpack_from('>I',b,radar+8)[0]
 assert not long(c,s+4)
 c.wb(s+8,c.rb(s+8)|8);sector=long(c,0x297e)
 for wait in range(1,350):
  c.run(1)
  if long(c,s+4):break
 assert long(c,s+4) and sector==long(c,0x297e)
 close(c)
spawn.__globals__['ROM']=rom
r,slot=house(67);c,_=spawn(r['x']-30,r['y']);m['native_destroy'](c,slot)
s=live(47);assert long(c,s+4)
# Exercise event 2A on the rescued person's runtime slot, then actual damage
# on five armed targets. The other objectives need not be debug-completed.
call(c,0x415c2,[(13,s)])
assert long(c,0x1108)==0x2ba1c0,hex(long(c,0x1108))
points=[c.rw(0x10de)]
for i in (39,40,42,43,45):
 rec=0x2b0000+128*ids.index(i);y,x=struct.unpack_from('>HH',b,rec+12)
 visit(c,x-30,y)
 actor=long(c,live(i)+4)
 if actor:m['damage_actor'](c,actor,800)
 else:call(c,0x41a6e,[(13,live(i)),(0,0x16)])
 points.append(c.rw(0x10de))
close(c)
r,slot=house(67);c,_=spawn(r['x']-30,r['y']);m['native_destroy'](c,slot)
call(c,0x415a2,[(13,live(47))])
assert long(c,0x1104)==0x2ba500
close(c)
c,_=spawn(490,3300);m['native_destroy'](c,b[0x279490+23])
assert long(c,0x1104)==0x2ba300
close(c)
c,_=spawn(143,1630)
for _ in range(2):m['press'](c,'Z',25)
assert long(c,0x1108)==0x2ba180
m['press'](c,'S',100)
assert m['pc'](c) in (0x3b904,0x3b90c)
m['press'](c,'B',100)
close(c)
print('mission3',points)
assert points==[65531,65532,65533,65534,65535,0],points
(root/'validation.json').write_text(json.dumps(dict(houses=counts,radar_retry_frames=wait,mission3_signed=[v-65536 if v else 0 for v in points]),indent=2)+'\n')
