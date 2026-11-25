"""Run first-mission, iceberg, and supplied pad-save probes in GX."""
import json
from pathlib import Path
import runpy
import struct


ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
ROM=ROOT/'Jungle_Strike_Eco_Threat_Flight_TEST_v11.bin'
REPORT=json.loads((ROOT/'build_report.json').read_text())
V10=runpy.run_path(str(WORK/'eco_flight_v10/check.py'))
spawn,closed,press,pc,ram_long,native_destroy=(V10[k] for k in
    ('spawn','close','press','pc','ram_long','native_destroy'))


def markers(core):
    found=[]
    actor=ram_long(core,0x414)
    while actor:
        sprite=ram_long(core,actor+0x4e)
        if mission:=core.rw(actor+44):
            found.append((mission,core.rw(sprite+0x1c),core.rw(sprite+0x1e)))
        actor=ram_long(core,actor)
    return found


def damage_actor(core, actor, damage):
    sp=core.lib.retro_debug_reg(15)-4
    core.wl(sp,pc(core))
    for reg,value in ((15,sp),(16,0x4192e),(13,actor),(0,damage)):
        core.lib.retro_debug_set(reg,value)
    core.run(180)


def mission():
    core,_=spawn(2200,1025)
    actor_data={row['id']:row for row in REPORT['mission1']}
    mobile=0xfffba6+actor_data[12]['offset']
    actor=ram_long(core,mobile+4)
    position=ram_long(core,actor+34)
    start=(core.rw(position),core.rw(position+4))
    core.run(100)
    assert (core.rw(position),core.rw(position+4))!=start
    press(core,'S')
    initial=markers(core)
    assert len(initial)==5 and all(i[0]==1 for i in initial), initial
    press(core,'B',60)
    assert core.rw(0x104e)==6
    press(core,'S')
    player=ram_long(core,ram_long(core,0x29e8)+34)
    counters=[]
    for j,index in enumerate((12,13,23,9,5),1):
        row=actor_data[index]
        x,y,_=row['position']
        x0,y0=core.rw(player),core.rw(player+4)
        steps=max(abs(x-x0),abs(y-y0))//16+1
        for i in range(1,steps+1):
            core.wl(player,(x0+(x-x0)*i//steps)<<16)
            core.wl(player+4,(y0+(y-y0)*i//steps)<<16)
            core.run(2)
        slot=0xfffba6+row['offset']
        core.run(30)
        actor=ram_long(core,slot+4)
        assert actor,index
        damage_actor(core,actor,500)
        counter=core.rw(0x10da)
        assert counter==((j-5)&65535)
        counters.append(counter-65536 if counter else 0)
    press(core,'S')
    if core.rw(0x104e)!=2:
        press(core,'A')
    assert core.rw(0x104e)==2
    final=markers(core)
    assert final==[(2,70,127)],final
    closed(core)
    return {'initial_markers':initial,'counter_after_each_destroy':counters,
            'markers_after_completion':final,'mission_card':True}


def icebergs():
    passed=[]
    objects=REPORT['icebergs']['objects']
    for i in range(0,len(objects),2):
        big,small=objects[i:i+2]
        x,y,_=big['position']
        core,_=spawn(x-60,y)
        a=0xff391e+30*big['slot']
        b=0xff391e+30*small['slot']
        assert core.rb(a+25)&8 and not core.rb(b+25)&8
        native_destroy(core,big['slot'])
        assert not core.rb(a+25)&8 and core.rb(b+25)&8
        native_destroy(core,small['slot'])
        assert not core.rb(b+25)&8
        closed(core)
        passed.append([big['id'],small['id']])
    return passed


def pad(save):
    if not save.is_file():
        return None
    data=save.read_bytes()[0x2478:]
    def get(a):
        return struct.unpack_from('>I',data,a&65535)[0]
    state=get(get(0x29e8)+34)
    a,b=get(state)>>16,get(state+4)>>16
    trajectory=[]
    for image in (V10['ROM'],ROM):
        spawn.__globals__['ROM']=image
        core,_=spawn(a,b)
        pos=ram_long(core,ram_long(core,0x29e8)+34)
        for offset in range(0,0x28,4):
            core.wl(pos+offset,get(state+offset))
        core.wb(0x12b7,0x12)
        series=[]
        for i in range(90):
            core.run(1,'U')
            series.append(core.rw(pos))
        trajectory.append(min(series))
        closed(core)
    spawn.__globals__['ROM']=ROM
    assert trajectory[1]<trajectory[0]-15,trajectory
    return trajectory


if __name__=='__main__':
    spawn.__globals__['ROM']=ROM
    output={'mission':mission(),'iceberg_pairs':icebergs()}
    save=Path('upload/Jungle_Strike_Eco_Threat_Flight_TEST_v10(1).gs0')
    if (trajectory:=pad(save)) is not None:
        output['pad_gs0_minimum_x_v10_v11']=trajectory
    (ROOT/'validation.json').write_text(json.dumps(output,indent=2)+'\n')
    print(output)
