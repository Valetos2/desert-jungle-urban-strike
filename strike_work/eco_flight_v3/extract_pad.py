"""Extract the native Snow Fortress platform with the stock graphics loader."""
import sys,ctypes as C
from pathlib import Path
sys.path.insert(0,'strike_work/tools')
from retro import Core
R=Path(__file__).resolve().parent;b=Path('strikehd/rom/jungle_strike.bin').read_bytes();u=lambda a:int.from_bytes(b[a:a+4],'big');w=lambda a:int.from_bytes(b[a:a+2],'big');ts=0x71560
c=Core('strike_work/eco_flight_v2/Jungle_Strike_Eco_Threat_Flight_TEST_v2.bin');c.run(1);c.load('strike_work/eco_flight_v2/game.state')
sp=c.lib.retro_debug_reg(15)-4;c.wl(sp,c.lib.retro_debug_reg(16));c.lib.retro_debug_set(15,sp);c.lib.retro_debug_set(8,ts);c.lib.retro_debug_set(9,0);c.lib.retro_debug_set(16,0x3f45c);c.run(1)
c.lib.retro_debug_vram.restype=C.c_void_p;raw=C.string_at(c.lib.retro_debug_vram(),65536);raw=bytes(raw[i^1] for i in range(65536));base=c.rw(u(ts+6));(R/'stock_pad_patterns.bin').write_bytes(raw[base*32:base*32+w(ts+34)]);print(w(ts+34),hex(base))
