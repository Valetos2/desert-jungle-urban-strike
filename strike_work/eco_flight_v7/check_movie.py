"""Select the additional movie through Options and observe both new text pages."""
from build import ROOT,NAME
import sys
sys.path.insert(0,'strike_work/tools')
from retro import Core
c=Core(ROOT/(NAME+'.bin'))
pc=lambda:c.lib.retro_debug_reg(16)&0xffffff
for f in range(2200):
    c.run(1,'S' if f%150<8 else '')
    if pc() in (0x39380,0x39388):break
else:raise AssertionError('Menu unavailable')
c.run(2,'C');c.run(45)
c.run(2,'U');c.run(28)
assert c.rb(0x452)==4,c.rb(0x452)
for _ in range(21):
    c.run(2,'R');c.run(16)
a6=c.lib.retro_debug_reg(14)&0xffffff
assert c.rw(a6+18)==21,(hex(a6),c.rw(a6+18))
c.run(2,'B')
seen=set()
for f in range(7000):
    c.run(1)
    p=c.rw(0x408)*65536+c.rw(0x40a)
    if p==0x279100:
        seen.add(p)
    if f>200 and c.rb(0x452)==4 and pc() in (0x200040,0x200044,0x200048):
        break
else:raise AssertionError(('Movie did not return',hex(pc()),len(seen),hex(c.rb(0x452))))
print('Movie Test returned after',f,'frames, briefing scene states:',len(seen))
assert seen
