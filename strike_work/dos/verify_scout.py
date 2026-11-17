"""Run the game's real decoder and patched routines in a 16-bit CPU emulator."""
from pathlib import Path
import struct
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_INTR
from unicorn.x86_const import *
from build_scout_dat import patch_executable
from unpack_dat import unpack

ROOT = Path(__file__).parent
data = (ROOT/'scout/JUNGLE.DAT').read_bytes()
original = (ROOT/'files/JUNGLE.DAT').read_bytes()
start, = struct.unpack_from('<I', data, 24)
end, = struct.unpack_from('<I', data, 40)
old_end, = struct.unpack_from('<I', original, 40)
assert data[end:] == original[old_end:]
exe, consumed = unpack(data[start:end])
assert exe == patch_executable((ROOT/'unpacked/jungle/EXECUTABLE').read_bytes())
assert consumed == end-start

def cpu():
    u = Uc(UC_ARCH_X86, UC_MODE_16)
    u.mem_map(0, 1024 * 1024)
    u.reg_write(UC_X86_REG_SS, 0x8000)
    u.reg_write(UC_X86_REG_SP, 0x1800)
    return u

def w(u, address, value):
    u.mem_write(address, struct.pack('<H', value))

def r(u, address):
    return struct.unpack('<H', u.mem_read(address, 2))[0]

def run(u, start, stop=0xfff0):
    w(u, 0x81800, stop)
    u.reg_write(UC_X86_REG_SP, 0x1800)
    u.emu_start(start, stop, timeout=10_000_000, count=12_000_000)
    assert u.reg_read(UC_X86_REG_IP) == stop

# The unpacker reads file bytes through DOS int 21h, function 3Fh.
loader = cpu()
loader.mem_write(0, (ROOT/'files/JUNGLE.EXE').read_bytes()[0x200:])
w(loader, 0x3f1, 0x1000)
w(loader, 0x3f3, 0x9000)
pos = start
def interrupt(u, interrupt_no, _):
    global pos
    assert interrupt_no == 0x21 and u.reg_read(UC_X86_REG_AX) == 0x3f00, (interrupt_no, hex(u.reg_read(UC_X86_REG_AX)), hex(u.reg_read(UC_X86_REG_IP)), pos)
    count = u.reg_read(UC_X86_REG_CX)
    buffer = u.reg_read(UC_X86_REG_DS) * 16 + u.reg_read(UC_X86_REG_DX)
    chunk = data[pos:pos+count]
    u.mem_write(buffer, chunk)
    pos += len(chunk)
    u.reg_write(UC_X86_REG_AX, len(chunk))
    u.reg_write(UC_X86_REG_EFLAGS, u.reg_read(UC_X86_REG_EFLAGS) & ~1)
loader.hook_add(UC_HOOK_INTR, interrupt)
run(loader, 0x17e)
assert loader.mem_read(0x10000, len(exe)) == exe
print('Native DOS decoder round-trip OK')

D = 0x20000
F = 0x30000
def game():
    u = cpu()
    u.mem_write(0, exe[0x7200:0x17200])
    u.reg_write(UC_X86_REG_DS, D // 16)
    u.reg_write(UC_X86_REG_FS, F // 16)
    return u

for dmg, player in ((0xc9c6, True), (0xc9c6, False), (0xc9f0, True), (0xc9f0, False)):
    u = game()
    active, target = 0x6000, 0x6000 if player else 0x6100
    w(u, D+0x5cfe, active)
    w(u, D+active+4, 0x6200)
    w(u, D+target+4, 0x6200 if player else 0x6300)
    descriptor = r(u, D+target+4)
    w(u, D+target+9, 2)
    w(u, F+descriptor+8, 2)
    w(u, F+descriptor+0xb, 0x80)
    w(u, D+target+0x1c, 100)
    w(u, F+descriptor+0xc, 100)
    w(u, D+0x1fd8, 10)
    w(u, D+0x1fd2, target if dmg == 0xc9c6 else descriptor)
    run(u, dmg)
    assert r(u,F+descriptor+0xc) == (100 if player else 90)
    assert r(u,D+target+0x1c) == (100 if player or dmg == 0xc9f0 else 90)

for active in (True,False):
    u = game()
    w(u,D+0x5cfe,0x6000)
    w(u,D+0x1fc8,0x6000 if active else 0x6100)
    u.reg_write(UC_X86_REG_SI,0x6200)
    w(u,D+0x620c,10)
    run(u,0x7ea1,0x7eb3)
    assert r(u,D+0x620c)==(10 if active else 9)
for available in (0,1,99):
    u=game()
    w(u,D+0x3f10,100)
    w(u,D+0x3e7d,available)
    run(u,0xafc3,0xaff6)
    assert r(u,D+0x3e7d)==100
print('Player armor, other-target damage, fuel restoration and ammo consumption OK')
