"""Emulator regressions for EA input, mission map, scenery and water."""
import ctypes
import json
from pathlib import Path
import struct
import sys
from tempfile import TemporaryDirectory

import numpy as np

from build import CHECKSUM, NAME, ROOT, V8

sys.path.insert(0, 'strike_work/tools')
from retro import Core

ROM = ROOT / (NAME+'.bin')
BASE = V8 / (NAME.replace('v9', 'v8')+'.bin')
ORIGINAL = Path('strikehd/rom/jungle_strike.bin')


def pc(core):
    return core.lib.retro_debug_reg(16) & 0xffffff


def ram_long(core, address):
    return core.rw(address)*65536 + core.rw(address+2)


def until(core, condition, limit=4800, buttons=''):
    for frame in range(limit):
        core.run(1, buttons)
        if condition():
            return frame
    raise AssertionError(hex(pc(core)))


def close(core):
    core.lib.retro_unload_game()
    core.lib.retro_deinit()


def boot(core):
    for frame in range(4800):
        core.run(1, 'S' if frame % 150 < 8 else '')
        if pc(core) in (0x3d770,0x3d778):
            assert core.rw(0x139e) == 9
            core.run(160)
            return
    raise AssertionError(hex(pc(core)))


def check_ea():
    report = {}
    for label, image in [('original', ORIGINAL), ('v8', BASE), ('v9', ROM)]:
        for pad in (3, 6):
            core = Core(image, pad)
            try:
                until(core, lambda: 0x388 <= pc(core) < 0x3d2, limit=1400)
                core.run(45)
                assert 0x388 <= pc(core) < 0x3d2
                with TemporaryDirectory() as directory:
                    state = Path(directory) / 'ea.state'
                    core.save(state)
                    durations = {}
                    for key in ('', 'A', 'B', 'C', 'S'):
                        core.load(state)
                        durations[key or 'idle'] = until(core, lambda: pc(core) >= 0x1000, buttons=key)
                    assert durations['idle'] > 60
                    assert all(durations[key] <= 4 for key in ('A', 'B', 'C', 'S')), durations
                    report[f'{label}_{pad}'] = durations
            finally:
                close(core)
    for pad in (3,6):
        assert abs(report[f'v9_{pad}']['idle'] - report[f'v8_{pad}']['idle']) <= 3, report
    return report


def press(core, button, wait=120):
    core.run(8, button)
    core.run(wait)


def native_destroy(core, slot):
    live = 0xff391e+slot*30
    sp = core.lib.retro_debug_reg(15)-4
    core.wl(sp, pc(core))
    for reg, val in [(15,sp),(13,live),(0,0),(16,0x40a4c)]:
        core.lib.retro_debug_set(reg,val)
    core.run(40)
    assert core.rb(live+25) & 32


def check_markers(core):
    for mission, expected in enumerate(([], [2], [3], [])):
        if mission:
            press(core,'Z',90)
        press(core,'S')
        assert pc(core) in (0x3ac58,0x3ac60)
        found = []
        marker = ram_long(core,0x414)
        while marker:
            if (mission_number := core.rw(marker+44)):
                found.append(mission_number)
            else:
                sprite = ram_long(core, marker+0x4e)
                assert core.rw(sprite+0x1c) == core.rw(sprite+0x1e) == 0
            assert len(found) < 20
            marker = ram_long(core, marker)
        assert found == expected, (mission, found)
        press(core,'S')
    for slot in (74,75,76):
        assert core.rb(0xff391e+30*slot+25)&2 == 0
    for _ in range(3):
        press(core,'Z',90)
    for slot in (74,75,76):
        live = 0xff391e+30*slot
        assert core.rb(live+25)&2 and core.rw(live+20)==400, (slot,hex(core.rb(live+25)),core.rw(live+20))


def check_water_and_map():
    captures = []
    for image in (BASE, ROM):
        core = Core(image)
        try:
            boot(core)
            core.lib.retro_debug_cram.restype = ctypes.c_void_p
            states = {}
            for _ in range(48):
                core.run(1)
                cram = np.frombuffer(ctypes.string_at(core.lib.retro_debug_cram(),128),np.uint16)
                states[int(cram[31])] = core.frame[101:209,12:140].copy()
            assert set(states) == {208,216,281}
            captures.append(np.stack([states[i] for i in (208,216,281)]))
            if image == ROM:
                assert cram[30] == 208
                check_markers(core)
        finally:
            close(core)
    before, after = captures
    changed = np.any(before != after,axis=3)
    assert np.array_equal(changed[0],changed[1]) and np.array_equal(changed[0],changed[2])
    assert changed[0].sum() == 2099, changed[0].sum()
    assert np.all(after[changed] == (0,68,98)) and np.all(before[changed] == (0,68,65))
    return int(changed[0].sum())


def check_ruins(directory):
    def match(core, rom, record):
        def w(at):
            return struct.unpack_from('>H',rom,at)[0]
        def u(at):
            return struct.unpack_from('>I',rom,at)[0]
        gfx = u(record)
        width, height, bank_offset = w(gfx), w(gfx+2), w(gfx+4)
        top,left = w(record+4), w(record+6)
        bank = u(0x210100+bank_offset)
        tilebase = core.rw(u(bank+6)) if rom[bank]&2 else 0x34
        data, attrs = u(gfx+22), w(gfx+30)
        expected = []
        for j in range(width*height):
            if w(gfx+16)==2:
                expected.append((w(data+2*j)+attrs+tilebase)&65535)
            else:
                code=rom[data+2+j]
                expected.append(((code&63)+((code&192)<<5)+w(data)+attrs+tilebase)&65535 if code else 1)
        expected=np.array(expected).reshape(height,width)
        core.lib.retro_debug_vram.restype = ctypes.c_void_p
        vram=np.frombuffer(ctypes.string_at(core.lib.retro_debug_vram(),65536),dtype='<u2').reshape(-1,64)
        target=vram[384:448][np.ix_((np.arange(height)+top)%64,(np.arange(width)+left)%64)]
        # Transparent cells expose the terrain. Require the native opaque tiles
        # at the corrected position, tolerating overlays by adjacent scenery.
        opaque=(expected&2047)>tilebase
        eq=((expected^target)&0x1fff)==0
        matches=int((eq&opaque).sum())
        return matches,int(opaque.sum())

    report={}
    for slot, record in [(61,0x279410),(63,0x279490),(65,0x27a570),(74,0x27b210)]:
        rom=bytearray(ROM.read_bytes())
        y,x=struct.unpack_from('>HH',rom,record+16)
        x,y=min(x+65,5050),min(y+58,3500)
        struct.pack_into('>HH',rom,0x21090c,y,x)
        rom[0x210700:0x210818]=bytes(280)
        struct.pack_into('>I',rom,0x210700+(10*(y//512)+x//512)*4,0x210940)
        CHECKSUM(rom)
        path=directory/f'spawn_{slot}.bin'
        path.write_bytes(rom)
        core=Core(path)
        try:
            boot(core)
            original=match(core,rom,record)
            native_destroy(core,slot)
            remains=match(core,rom,record-16)
            print(slot,original,remains,flush=True)
            assert original[0] >= 8 and remains[0] >= 8
            report[slot]={'intact_opaque_matches': original,'ruin_opaque_matches': remains}
        finally:
            close(core)
    return report


if __name__=='__main__':
    report = {'ea_frames_after_sample': check_ea()}
    print(report,flush=True)
    report['static_water_pixels'] = check_water_and_map()
    with TemporaryDirectory() as directory:
        report['vdp'] = check_ruins(Path(directory))
    (ROOT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
