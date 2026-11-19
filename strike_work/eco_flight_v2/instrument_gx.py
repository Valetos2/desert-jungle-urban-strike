"""Add small local inspection exports to GX; not part of the game ROM."""
from pathlib import Path
p=Path('gx/libretro/libretro.c');s=p.read_text()
for name,code in [
 ('retro_debug_reg','RETRO_API unsigned retro_debug_reg(unsigned reg) {return m68k_get_reg(reg); }'),
 ('retro_debug_set','RETRO_API void retro_debug_set(unsigned reg,unsigned value) {m68k_set_reg(reg,value); }'),
 ('retro_debug_vram','RETRO_API void *retro_debug_vram(void) {return vram; }')]:
 if name not in s:s+='\n'+code+'\n'
p.write_text(s)
p=Path('gx/core/m68k/m68kcpu.c');s=p.read_text()
if 'retro_debug_step' not in s:s+='\n__attribute__((visibility("default"))) void retro_debug_step(void) {m68k_run(m68k.cycles+1);}\n'
p.write_text(s)
print('Now build: make -C gx -f Makefile.libretro -j4 platform=unix')
