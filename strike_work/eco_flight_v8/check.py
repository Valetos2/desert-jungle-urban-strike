"""Check menu Z edges, original marker actors, and flight test supplies."""
from build import ROOT,NAME
import sys
sys.path.insert(0,'strike_work/tools')
from retro import Core

c=Core(ROOT/(NAME+'.bin'))
def u(a): return c.rw(a)*65536+c.rw(a+2)
def pc(): return c.lib.retro_debug_reg(16)&0xffffff
def tap(key, wait=20):
    c.run(8,key)
    c.run(wait)
def wait_for(addresses, frames=3800, buttons=''):
    for _ in range(frames):
        c.run(1,buttons)
        if pc() in addresses:return
    raise AssertionError(hex(pc()))

for f in range(2600):
    c.run(1,'S' if f%150<8 else '')
    if pc() in (0x39380,0x39388):break
else:raise AssertionError('No main menu')
assert u(0x10b0)==9
for campaign in list(range(9))+[9]:
    c.run(55,'Z')
    assert u(0x10b0)==campaign,(campaign,u(0x10b0))
    c.run(6)
    c.shot(ROOT/f'campaign{campaign+1}.png')
print('All ten campaign indices, wrap and Z hold verified',flush=True)
stock = '--stock' in sys.argv
if stock:tap('Z',20)
tap('S',20)
wait_for({0x3d770,0x3d778},14000)
c.run(260)
assert c.rw(0x139e)==(0 if stock else 9)
assert c.rw(0x10ce)==99 and c.rw(0x10c6)==9999
def call(addr, a5, damage):
    sp=c.lib.retro_debug_reg(15)-4
    c.wl(sp,pc())
    for reg,value in [(15,sp),(13,a5),(0,damage),(16,addr)]:
        c.lib.retro_debug_set(reg,value)
    c.run(3)

player=u(0x29e8)
slot=u(player+8)
armor=c.rw(player+44)
slot_armor=c.rw(slot+12)
assert armor and slot_armor
call(0x4192e,player,armor)
call(0x41762,slot,slot_armor)
assert (c.rw(player+44),c.rw(slot+12))==(armor,slot_armor)
print('Full fuel and lives; both armor damage paths protected',flush=True)
if stock:
    # Movement mode 14 enables the regular airborne controller for this probe.
    c.wb(0x12b7,14)
    player=u(0x29e8)
    weapon=u(player+0x34)
    ammo=c.rw(weapon+18)
    cooldown=u(weapon+12)
    tap('C',20)
    assert u(weapon+12)!=cooldown and c.rw(weapon+18)==ammo
    print('Washington probe: pad-triggered gunfire and unchanged ammo')
    sys.exit()

def markers():
    tap('S',120)
    assert pc() in (0x3ac58,0x3ac60),hex(pc())
    p=u(0x414)
    found=[]
    while p:
        mission=c.rw(p+44)
        if mission:found.append(mission)
        assert len(found)<20
        p=u(p)
    tap('S',120)
    return found
for goal,expected in [(0,[]),(1,[2]),(2,[3]),(3,[])]:
    if goal:tap('Z',90)
    actual=markers()
    print('Objectives complete',goal,'native map markers',actual,flush=True)
    assert actual==expected
    if goal==2:
        state=ROOT/'map_check.state'
        c.save(state)
        tower=0xff391e+30*63
        call(0x40a4c,tower,0)
        c.run(130)
        assert c.rb(tower+25)&32
        assert markers()==[]
        c.load(state)
        state.unlink()
        print('Destroying the power station removes its marker',flush=True)

# Confirm the first playable state of the burial site without importing NPCs.
hill=0xff391e+48*30
entrance=0xff391e+64*30
assert not c.rb(hill+25)&8 and not c.rb(entrance+25)&8
tap('Z',90)
assert c.rb(hill+25)&8 and not c.rb(entrance+25)&8
call(0x40a4c,hill,0)
assert c.rb(entrance+25)&8
print('The buried entrance is revealed only after the mound is destroyed',flush=True)

pylon=0xff391e+65*30
wires=[0xff391e+30*i for i in (68,69,73)]
assert all(c.rb(wire+25)&8 for wire in wires)
call(0x40a4c,pylon,0)
print("Pylon flags",hex(c.rb(pylon+25)),"wire flags",[hex(c.rb(wire+25)) for wire in wires])
assert all(not c.rb(wire+25)&8 for wire in wires)
print('Destroying the pylon removes its three associated wire sections',flush=True)
