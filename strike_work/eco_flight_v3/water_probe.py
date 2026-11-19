import sys,ctypes as C,json,struct
from pathlib import Path
sys.path.insert(0,'strike_work/tools')
from retro import Core
R=Path('strike_work/eco_flight_v3')
idx=int(sys.argv[1]);b=bytearray(Path('strike_work/eco_flight_v3/Jungle_Strike_Eco_Threat_Flight_TEST_v3.bin').read_bytes());struct.pack_into('>I',b,0x38c92,idx);struct.pack_into('>I',b,2093816,sum(int.from_bytes(b[i:i+4],'big') for i in range(0,2093788,4) if i!=0x18c)&0xffffffff);struct.pack_into('>H',b,0x18e,sum(int.from_bytes(b[i:i+2],'big') for i in range(0x200,len(b),2))&65535);tmp=R/'local_water.bin';tmp.write_bytes(b);c=Core(tmp)
for f in range(2600):
 c.run(1,'S' if f%150<8 else '')
 if c.rw(0x139e)==idx and c.lib.retro_debug_reg(16) in [0x3d770,0x3d778]:break
c.lib.retro_debug_cram.restype=C.c_void_p
seen=[set() for _ in range(64)]
for f in range(360):
 c.run(1);data=C.string_at(c.lib.retro_debug_cram(),128)
 for i in range(64):seen[i].add(data[2*i:2*i+2].hex())
result={'campaign_index':idx,'frames':360,'changing_palette_indices':{i:sorted(v) for i,v in enumerate(seen) if len(v)>1}}
assert set(result['changing_palette_indices'])==({25,26,27} if idx==9 else {3,4,5}),result
(R/f'water_validation_{idx}.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));tmp.unlink()
