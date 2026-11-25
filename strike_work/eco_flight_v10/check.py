"""Run v10 regressions in the instrumented Genesis Plus GX core."""
import ctypes
import json
from pathlib import Path
import struct
import sys
from tempfile import TemporaryDirectory

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'eco_flight_v9'))
from check import CHECKSUM, Core, boot, close, native_destroy, pc, press, ram_long

ROM = ROOT / 'Jungle_Strike_Eco_Threat_Flight_TEST_v10.bin'
ACTORS = {a['dos_index']: a for a in json.loads((ROOT/'build_report.json').read_text())['actors']}


def slot(index):
    return 0xfffba6 + ACTORS[index]['offset']


def spawn(x, y):
    rom = bytearray(ROM.read_bytes())
    struct.pack_into('>HHH', rom, 0x21090c, y, x, 0)
    rom[0x210912:0x210914] = b'\0\0'
    table = struct.unpack_from('>I', rom, 0x210242)[0]
    groups = []
    for index in range(70):
        ptr = struct.unpack_from('>I', rom, table+4*index)[0]
        count = struct.unpack_from('>H', rom, ptr)[0] if ptr else 0
        entries = struct.unpack_from(f'>{count}I', rom, ptr+2)
        groups.append([entry for entry in entries if entry != 0x210900])
    groups[y//512*10+x//512].append(0x210900)
    ptr = 0x29e000
    for sector, entries in enumerate(groups):
        struct.pack_into('>I', rom, table+4*sector, ptr if entries else 0)
        if entries:
            struct.pack_into(f'>H{len(entries)}I', rom, ptr, len(entries), *entries)
            ptr += 2+4*len(entries)
    CHECKSUM(rom)
    with TemporaryDirectory() as directory:
        path = Path(directory)/'flight.bin'
        path.write_bytes(rom)
        core = Core(path)
        boot(core)
    core.wb(0x12b7,14)  # Enter the standard flight controller at the diagnostic start.
    return core, rom


def check_map():
    core = Core(ROM)
    boot(core)
    result = {}
    for completed, expected in enumerate(([], [2], [3], [])):
        if completed:
            press(core,'Z',90)
        press(core,'S')
        assert pc(core) in (0x3ac58,0x3ac60)
        points = []
        icon = ram_long(core,0x414)
        player = None
        while icon:
            sprite = ram_long(core,icon+0x4e)
            x,y = core.rw(sprite+0x1c),core.rw(sprite+0x1e)
            if core.rw(icon+44):
                points.append(core.rw(icon+44))
            elif x or y:
                assert player is None
                player = x,y
            icon = ram_long(core,icon)
        assert points == expected and player is not None, (points,player)
        if not completed:
            assert player == (176,49)
            x,y = player
            samples = set()
            for _ in range(110):
                core.run(1)
                samples.add(core.frame[y-3:y+6,x-4:x+6].tobytes())
            assert len(samples)>1
            result['player_animation_frames'] = len(samples)
        result[str(completed)] = points
        press(core,'S')
    close(core)
    return result


def check_enemies():
    result = {}
    for index in (0,77,130):
        x,y = ACTORS[index]['xy']
        core,_ = spawn(x-64,y)
        address = slot(index)
        actor = ram_long(core,address+4)
        assert actor and core.rb(address+8)&8
        position = ram_long(core,actor+0x22)
        assert (core.rw(position),core.rw(position+4),core.rw(position+8)) == (x,y,ACTORS[index]['height'])
        armor = core.rw(address+12)
        weapon = ram_long(core,actor+0x34)
        before = core.rw(weapon+18)
        core.run(180)
        fired = (before-core.rw(weapon+18))&0xffff
        assert 0<fired<100
        for _ in range(8):
            core.run(3,'C')
            core.run(20)
        if index == 77:
            # Ground-level fire passes underneath. Falling tower kills gunner.
            assert core.rw(address+12)==armor and ram_long(core,address+4)
            native_destroy(core,61)
        assert not ram_long(core,address+4) and core.rb(address+8)&32
        result[index] = {'armor':armor, 'shots_before_attack':fired, 'height':ACTORS[index]['height']}
        close(core)
        if index != 77:
            core,_ = spawn(x-64,y+55)
            core.run(180,'C')
            assert core.rw(address+12)==armor and ram_long(core,address+4)
            result[index]['off_axis_gunfire_missed'] = True
            close(core)
    return result


def check_mounds():
    for mound, indices in ((47,(99,100)),(49,(107,))):
        x,y = ACTORS[indices[0]]['xy']
        core,_ = spawn(x-64,y)
        assert all(not core.rb(slot(i)+8)&8 and not ram_long(core,slot(i)+4) for i in indices)
        native_destroy(core,mound)
        assert all(core.rb(slot(i)+8)&8 and ram_long(core,slot(i)+4) for i in indices)
        close(core)


def check_wires():
    core,rom = spawn(750,3210)
    core.lib.retro_debug_vram.restype = ctypes.c_void_p

    def word(p):
        return struct.unpack_from('>H',rom,p)[0]

    def long(p):
        return struct.unpack_from('>I',rom,p)[0]

    bank = long(0x210100+36)
    wires = []
    for i in range(6):
        p = 0x27a690+i*96
        gfx = long(p)
        assert word(gfx+4)==36
        data,attrs = long(gfx+22),word(gfx+30)
        top,left = struct.unpack_from('>HH',rom,p+4)
        width,height = struct.unpack_from('>HH',rom,gfx)
        tiles = []
        for j in range(width*height):
            if word(gfx+16)==2:
                tile=word(data+2*j)
                if tile&2047<=1:
                    continue
            else:
                code=rom[data+2+j]
                if not code:
                    continue
                tile=(code&63)+((code&192)<<5)+word(data)
            yy,xx=divmod(j,width)
            tiles.append((left+xx,top+yy,tile+attrs))
        wires.append(tiles)

    seen = set()
    sectors = set()
    samples = [0]*6
    player_position = ram_long(core,ram_long(core,0x29e8)+0x22)
    for wx,wy in ([(x,3180) for x in range(750,1330,8)]
                  +[(1322,y) for y in range(3180,2910,-8)]
                  +[(x,2916) for x in range(1322,370,-8)]
                  +[(378,y) for y in range(2916,3480,8)]
                  +[(x,3476) for x in range(378,1330,8)]
                  +[(1322,y) for y in range(3476,3225,-8)]
                  +[(x,3228) for x in range(1322,590,-8)]
                  +[(590,3228)]*40):
        core.wl(player_position,wx<<16)
        core.wl(player_position+4,wy<<16)
        for _ in range(3):
            core.run(1)
            x,y=core.rw(0x1386),core.rw(0x1384)
            if (x,y) in seen:
                continue
            seen.add((x,y))
            sectors.add(ram_long(core,0x297a))
            vram=np.frombuffer(ctypes.string_at(core.lib.retro_debug_vram(),65536),dtype='<u2')
            base=core.rw(long(bank+6))
            for j,tiles in enumerate(wires):
                for tx,ty,val in tiles:
                    if x+16<=tx*8<x+296 and y+16<=ty*8<y+200:
                        actual = int(vram[0x6000+64*(ty%64)+tx%64])
                        assert (actual^(val+base))&0x1fff==0, (j,tx,ty,x,y,hex(actual),hex(val+base))
                        samples[j] += 1
    assert all(samples), samples
    press(core,'S')
    press(core,'S')
    assert all(core.rb(0xff391e+30*i+25)&8 for i in range(68,74))
    native_destroy(core,65)
    for i in range(68,74):
        assert bool(core.rb(0xff391e+30*i+25)&8)==(i not in (68,69,73))
    close(core)
    return {'camera_positions': len(seen), 'sector_sets':len(sectors), 'visible_tile_samples':samples}


if __name__ == '__main__':
    report = {'map':check_map(),'enemies':check_enemies()}
    check_mounds()
    report['mound_pickups'] = [99,100,107]
    report['wires'] = check_wires()
    (ROOT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
