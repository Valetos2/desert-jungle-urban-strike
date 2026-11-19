"""Cold-boot each region (no teleport/camera discontinuity) and donor campaigns."""
from pathlib import Path
import struct,sys,json
sys.path.insert(0,'strike_work/tools')
from retro import Core
ROOT=Path(__file__).resolve().parent
if len(sys.argv)==1:
 import subprocess
 results=[]
 for tag,x,y,idx in [('start',3859,40,9),('northeast',5000,40,9),('northwest',80,40,9),('southeast',5000,3460,9),('southwest',80,3460,9),('center',2560,1800,9),('original2',0,0,1),('original6',0,0,5),('original9',0,0,8)]:
  r=subprocess.run([sys.executable,__file__,tag,str(x),str(y),str(idx)],text=True,capture_output=True,check=True);results.append(json.loads(r.stdout));print(r.stdout.strip(),flush=True)
 (ROOT/'region_validation.json').write_text(json.dumps(results,indent=2)+'\n')
else:
 tag,x,y,idx=sys.argv[1:];x,y,idx=map(int,[x,y,idx]);b=bytearray((ROOT/'Jungle_Strike_Eco_Threat_Flight_TEST_v2.bin').read_bytes())
 struct.pack_into('>I',b,0x38c92,idx)
 if idx==9:
  struct.pack_into('>HH',b,0x21090c,y,x)
  b[0x210700:0x210700+280]=bytes(280);struct.pack_into('>I',b,0x210700+((y//512)*10+x//512)*4,0x210940)
 struct.pack_into('>I',b,2093816,sum(int.from_bytes(b[i:i+4],'big') for i in range(0,2093788,4) if i!=0x18c)&0xffffffff)
 struct.pack_into('>H',b,0x18e,sum(int.from_bytes(b[i:i+2],'big') for i in range(0x200,len(b),2))&65535)
 tmp=ROOT/f'local_{tag}.bin';tmp.write_bytes(b);c=Core(tmp)
 for f in range(2600):
  c.run(1,'S' if f%150<8 else '')
  if c.rw(0x139e)==idx and c.lib.retro_debug_reg(16) in [0x3d770,0x3d778]:break
 else:raise AssertionError((tag,'no game',hex(c.lib.retro_debug_reg(16))))
 c.run(180);c.shot(ROOT/f'check_{tag}.png')
 groundslot=c.rw(0x1876);flags=(c.rw(0x2976)<<16)|c.rw(0x2978)
 c.run(2,'S');c.run(120);assert c.lib.retro_debug_reg(16) in [0x3ac58,0x3ac60],hex(c.lib.retro_debug_reg(16));c.shot(ROOT/f'check_{tag}_pause.png')
 c.run(2,'S');c.run(120);assert c.lib.retro_debug_reg(16) in [0x3d770,0x3d778]
 c.shot(ROOT/f'check_{tag}_resumed.png')
 print(json.dumps(dict(case=tag,index=idx,boot_frame=f,ground_slot=hex(groundslot),resource_flags=hex(flags),pause_resume=True)))
 tmp.unlink()
