"""Run the game's real decoder and patched routines in a 16-bit CPU emulator."""
from pathlib import Path
import struct
import sys
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_INTR
from unicorn.x86_const import *
from build_scout_dat import patch_executable
from unpack_dat import unpack

ROOT = Path(__file__).parent
data = (Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT/'scout2/JUNGLE.DAT').read_bytes()
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

# Write and reload the native profile, with DOS file I/O backed by memory.
cfg = {}
def cfg_cpu():
    u = game()
    image = exe[struct.unpack_from('<H', exe, 8)[0]*16:]
    base = struct.unpack_from('<H', image, 4)[0]*16
    u.mem_write(D, image[base:base+65536])
    u.reg_write(UC_X86_REG_ES, D//16)
    w(u, 10, 0x5000)  # loader-provided buffer for the config
    def dos_io(u, interrupt, _):
        assert interrupt == 0x21
        fn = u.reg_read(UC_X86_REG_AH)
        ptr = u.reg_read(UC_X86_REG_DS)*16 + u.reg_read(UC_X86_REG_DX)
        count = u.reg_read(UC_X86_REG_CX)
        carry = False
        if fn in (0x3c,0x3d):
            name = bytes(u.mem_read(ptr,11)).split(b'\0')[0]
            assert name == b'SCOUT2.CFG'
            carry = fn == 0x3d and 'data' not in cfg
            result = 2 if carry else 5
        elif fn == 0x3f:
            chunk = cfg['data'][:count]
            u.mem_write(ptr,chunk)
            result = len(chunk)
        elif fn == 0x40:
            cfg['data'] = bytes(u.mem_read(ptr,count))
            result = count
        else:
            assert fn == 0x3e
            result = 0
        u.reg_write(UC_X86_REG_AX,result)
        u.reg_write(UC_X86_REG_EFLAGS,(u.reg_read(UC_X86_REG_EFLAGS)&~1)|carry)
    u.hook_add(UC_HOOK_INTR,dos_io)
    u.reg_write(UC_X86_REG_SP,0x1800)
    u.emu_start(0x2ae1,0x2b33,count=50000)
    assert u.reg_read(UC_X86_REG_IP)==0x2b33
    return u

def menu(u):
    u.reg_write(UC_X86_REG_SI,0x1d9f)
    u.reg_write(UC_X86_REG_BX,0x1ccc)
    run(u,0x280e)
    result=[]
    for i in range(8):
        label=r(u,D+r(u,D+0x1ccc+2*i))
        result.append(bytes(u.mem_read(D+label,12)).split(b'\0')[0].decode())
    return result

keys=bytes.fromhex('1e 20 11 1f 4b 51 50 4f')
u=cfg_cpu()
labels=menu(u)
assert [s.upper() for s in labels]==['A','D','W','S','* 4','* 3','* 2','* 1'],labels
for scan,mask in zip(keys,[4,8,1,2,128,64,16,32]):
    u.mem_write(D+0x43d+scan,b'\1')
    u.reg_write(UC_X86_REG_AX,0)
    u.reg_write(UC_X86_REG_BX,0)
    run(u,0x2a17)
    assert u.reg_read(UC_X86_REG_AL)==mask
    u.mem_write(D+0x43d+scan,b'\0')
# Confirm later edits via DEFINE KEYS survive a native save and restart.
u.mem_write(D+0x1cec,bytes([0x10])+keys[1:])
u.emu_start(0x27ce,0x27d9,count=100)
run(u,0x2bb4)
fresh=cfg_cpu()
assert menu(fresh)[0].upper()=='Q'
assert bytes(fresh.mem_read(D+0x1d9f,8))==bytes([0x10])+keys[1:]
print('DEFINE KEYS labels:', ', '.join(labels))
print('Eight native input masks and changed binding after native CFG save/reload OK')
