"""Exercise the stock damage, map and iceberg handlers in Genesis Plus GX."""
from pathlib import Path
import json
import runpy

ROOT = Path(__file__).resolve().parent
older = runpy.run_path(str(ROOT.parent/'eco_flight_v11/check.py'))
spawn = older['spawn']
spawn.__globals__['ROM'] = next(ROOT.glob('*.bin'))
offsets = json.loads((ROOT/'build_report.json').read_text())['offsets']
actors = {a['id']:a for a in older['REPORT']['mission1']}
for actor in actors.values():
    actor['offset'] = offsets[str(actor['slot'])]

def slot(ident):
    return 0xfffba6+actors[ident]['offset']

result = {}
for ident,crate in ((12,21),(13,20)):
    x,y,_ = actors[ident]['position']
    core,_ = spawn(x-60,y)
    read = lambda address: older['ram_long'](core,address)
    boat = read(slot(ident)+4)
    pos = read(boat+34)
    dish = read(boat+0x4e)
    phases = []
    for frame in range(110):
        phase = core.rw(dish+4)
        if not phases or phase != phases[-1]:
            phases.append(phase)
        core.run(1)
    dest = (core.rw(pos),core.rw(pos+4))
    older['damage_actor'](core,boat,500)
    dropped = read(slot(crate)+4)
    assert dropped
    item = read(dropped+34)
    assert dest == (core.rw(item),core.rw(item+4)) and dest != (x,y)
    result[ident] = dict(impact=dest,crate=crate,dish_frames=phases)
    older['closed'](core)
result['mission'] = older['mission']()
result['icebergs'] = older['icebergs']()
(ROOT/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
