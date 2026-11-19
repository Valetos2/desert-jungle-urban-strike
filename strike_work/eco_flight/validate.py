import sys,json
from pathlib import Path
sys.path.insert(0,'strike_work/tools')
from retro import Core
ROOT=Path('strike_work/eco_flight')
c=Core(ROOT/'Jungle_Strike_Eco_Threat_Flight_TEST_v1.bin');c.run(1);c.load(ROOT/'game.state')
def rl(a):return c.rw(a)*65536+c.rw(a+2)
def ww(a,v):c.wb(a,(v>>8)&255);c.wb(a+1,v&255)
def position():
 p=rl(rl(0x29e8)+0x22)
 return [c.rw(p),c.rw(p+4),c.rw(p+8)]
print('start',position(),'lives',c.rw(0x10ce),'fuel',c.rw(0x10c6),flush=True)
a=position();c.run(300,'U');b=position();assert a!=b
c.shot(ROOT/'flight.png');c.save(ROOT/'flying.state');print('moved',a,b,flush=True)
res=[]
for i,(x,y) in enumerate([(200,200),(2560,200),(4900,200),(200,1800),(2560,1800),(4900,1800),(200,3300),(2560,3300),(4900,3300)]):
 c.load(ROOT/'flying.state');p=rl(rl(0x29e8)+0x22)
 c.wl(p,x<<16);c.wl(p+4,y<<16)
 c.run(180)
 pc=c.lib.retro_debug_reg(16)&0xffffff
 assert pc in (0x3d770,0x3d778),(i,hex(pc))
 c.shot(ROOT/('region_%02d.png'%i));res.append(dict(requested=[x,y],actual=position(),pc=hex(pc),fuel=c.rw(0x10c6)))
 print(res[-1],flush=True)
c.load(ROOT/'flying.state');c.run(2,'S');c.run(30);c.shot(ROOT/'pause.png');c.run(2,'S');c.run(60);print('resume',hex(c.lib.retro_debug_reg(16)&0xffffff),position(),flush=True)
(ROOT/'validation.json').write_text(json.dumps({'movement':[a,b],'regions':res,'pause_resume_pc':hex(c.lib.retro_debug_reg(16)&0xffffff)},indent=2)+'\n')
