from pathlib import Path
import runpy,struct,json,ctypes
import numpy as np
from PIL import Image
root=Path(__file__).resolve().parent;work=root.parent
m=runpy.run_path(str(work/'eco_flight_v11/check.py'));spawn=m['spawn'];lng=m['ram_long'];press=m['press']
path=next(root.glob('*.bin'));spawn.__globals__['ROM']=path
report={}
for version in (15,16):
    rom=next((work/f'eco_flight_v{version}').glob('*.bin'))
    b=rom.read_bytes()
    slot=int.from_bytes(b[0x2b0000+128*json.loads((work/'eco_flight_v14/build_report.json').read_text())['actors'].index(181)+8:][:4],'big')
    c=m['V10']['Core'](rom);m['V10']['boot'](c)
    history=[];seen=0
    for f in range(900):
        c.run(1,'U')
        actor=lng(c,slot+4)
        if actor:
            p=lng(c,actor+34);x,y=c.rw(p),c.rw(p+4)
            if f%40==0:history.append([f,x,y])
            if 10<x-c.rw(0x1386)<308 and 10<y-c.rw(0x1384)<207:
                seen+=1
                if seen==5:c.shot(f'/tmp/boat16_{version}.png')
    m['closed'](c)
    report[f'boat_{version}']=[seen,history]
c,_=spawn(2200,1025);press(c,'S');before=m['markers'](c);press(c,'S');press(c,'Z');press(c,'S');after=m['markers'](c);report['map']=[before,after]
press(c,'B')
for i in range(12):
    if i in (8,9,10,11):
        c.shot(f'/tmp/stockcard16_{i}.png')
        c.lib.retro_debug_vram.restype=ctypes.c_void_p
        Path('/tmp/stock16_vram'+str(i)).write_bytes(ctypes.string_at(c.lib.retro_debug_vram(),65536))
    press(c,'R',30)
m['closed'](c)
c,_=spawn(646,3011)
m['native_destroy'](c, next(path.read_bytes()[0x276000+64*j+23] for j,r in enumerate([r for r in json.loads((work/'eco_flight_v3/dos_static.json').read_text()) if r['name'] in ('F164','F163','F177')]) if r['id']==67))
ids=json.loads((work/'eco_flight_v14/build_report.json').read_text())['actors'];b=path.read_bytes();slot=int.from_bytes(b[0x2b0008+128*ids.index(47):][:4],'big')
report['scientist_live']=bool(lng(c,slot+4));c.shot('/tmp/scientist16.png');m['closed'](c)
(root/'validation.json').write_text(json.dumps(report,indent=2))
