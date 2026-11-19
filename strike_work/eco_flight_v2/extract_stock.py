"""Read stock terrain patterns through the game's own loader in a local GX build."""
import sys,ctypes as C,struct
from pathlib import Path
sys.path.insert(0,'strike_work/tools')
from retro import Core
out=Path(__file__).resolve().parent
rom=Path('strikehd/rom/jungle_strike.bin').read_bytes();u=lambda a:int.from_bytes(rom[a:a+4],'big');w=lambda a:int.from_bytes(rom[a:a+2],'big')
c=Core('strike_work/eco_flight/Jungle_Strike_Eco_Threat_Flight_TEST_v1.bin');c.run(1);c.load('strike_work/eco_flight/game.state')
c.lib.retro_debug_vram.restype=C.c_void_p
for n in [1,5]:
 c.load('strike_work/eco_flight/game.state');ts=u(u(0x525b6+n*4)+0x28)
 sp=c.lib.retro_debug_reg(15)-4;c.wl(sp,c.lib.retro_debug_reg(16));c.lib.retro_debug_set(15,sp);c.lib.retro_debug_set(8,ts);c.lib.retro_debug_set(9,0);c.lib.retro_debug_set(16,0x3f45c);c.run(1)
 base=c.rw(u(ts+6));raw=C.string_at(c.lib.retro_debug_vram(),65536);raw=bytes(raw[i^1] for i in range(65536));data=raw[base*32:base*32+w(ts+0x22)]
 (out/f'stock{n+1}_patterns.bin').write_bytes(data)
 lev=u(0x19292e+n*4);pal=rom[u(lev+0x46)+32:u(lev+0x46)+64];(out/f'stock{n+1}_palette.bin').write_bytes(pal)
 print(n+1,hex(base),len(data),data[:16].hex(),flush=True)
