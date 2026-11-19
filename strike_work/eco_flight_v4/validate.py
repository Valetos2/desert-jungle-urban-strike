"""Cold-boot the private ROM. Compare VDP plane words to the ROM's tile maps."""
from build import ROOT, V3, NAME, checksum
import struct, sys, ctypes, json
import numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
sys.path.insert(0,'strike_work/tools')
from retro import Core

def boot(c):
    for f in range(2600):
        c.run(1,'S' if f%150<8 else '')
        if c.lib.retro_debug_reg(16) in (0x39380,0x39388) and not (ROOT/'menu.png').exists():
            c.shot(ROOT/'menu.png')
        if c.lib.retro_debug_reg(16) in (0x3d770,0x3d778):break
    else: raise AssertionError('boot')
    c.run(180)

def press(c,k):
    c.run(2,k)
    c.run(28)

def menus():
    c=Core(ROOT/(NAME+'.bin'));boot(c)
    for completed in range(9):
        if completed:
            # Stand in for the as-yet unported objective scripts.
            c.wb(0x10da+2*(completed-1),0)
            c.wb(0x10db+2*(completed-1),0)
        press(c,'S');c.run(100)
        mask=c.rw(0x1086)
        assert mask==(1<<min(8,completed+1))-1,(completed,mask)
        assert c.rw(0x103c)==7
        # The native info tab uses Genesis B (bit 4).
        for key in ("B","C","A"):
            if c.rw(0x104e)==6:break
            press(c,key)
        assert c.rw(0x104e)==6,(c.rw(0x104e),hex(c.lib.retro_debug_reg(16)))
        for _ in range(8):
            idx=c.rw(0x104c)
            assert bool(c.rw(0x041e))==(idx>completed),(idx,completed)
            if completed==0 and idx<2:c.shot(ROOT/f'info_{idx}.png')
            press(c,'R')
        press(c,'S');c.run(120)
        assert c.lib.retro_debug_reg(16) in (0x3d770,0x3d778)
    print('Verified visibility of eight entries at nine stages')

def object_case(name,version):
    rows=json.loads((V3/'object_positions.json').read_text())
    tag=name
    if tag.isdigit():
        i,row=next((i,v) for i,v in enumerate(rows) if v['id']==int(tag))
        name=row['name']
    else:
        i,row=next((i,v) for i,v in enumerate(rows) if v['name']==name and v['x']>320 and 300<v['y']<3000)
    b=bytearray((ROOT/(NAME+'.bin') if version==4 else next(V3.glob('*v3.bin'))).read_bytes())
    u=lambda p:struct.unpack_from('>I',b,p)[0]
    w=lambda p:struct.unpack_from('>H',b,p)[0]
    rec=0x250000+40*i
    gfx=u(rec)
    width,height=w(gfx),w(gfx+2)
    top,left=w(rec+4),w(rec+6)
    # Native level on a blank ground with the original objects; change only the
    # diagnostic player's spawn, ground pixels, and his sector-list entry.
    b[0x220000:0x220000+342*32]=bytes([0x11])*(342*32)
    x=min(5050,left*8+width*4+65)
    y=min(3500,top*8+height*4+52)
    struct.pack_into('>HH',b,0x21090c,y,x)
    b[0x210700:0x210818]=bytes(280)
    struct.pack_into('>I',b,0x210700+(y//512*10+x//512)*4,0x210940)
    checksum(b)
    tmp=ROOT/f'probe_{tag}_{version}.bin';tmp.write_bytes(b);c=Core(tmp);boot(c);tmp.unlink()
    if not tag.isdigit():c.shot(ROOT/f'{tag}_v{version}.png')
    if version==3:return
    bank=u(0x210100+w(gfx+4))
    tilebase=c.rw(u(bank+6))
    data=u(gfx+22);attrs=w(gfx+30)
    expected=[]
    for j in range(width*height):
        if w(gfx+16)==2: val=w(data+j*2)+attrs+tilebase
        else:
            code=b[data+2+j]
            val=(code&63)+((code&192)<<5)+w(data)+attrs+tilebase if code else 1
        expected.append(val&65535)
    c.lib.retro_debug_vram.restype=ctypes.c_void_p
    v=np.frombuffer(ctypes.string_at(c.lib.retro_debug_vram(),65536),dtype='<u2')
    # Compare actual resident tile bytes with the donor bank decoded independently
    # by the stock Snow Fortress loader (or the v3 raw platform conversion).
    reference = (ROOT/'stock_trees.bin').read_bytes() if name!='F174' else bytes(b[u(bank+42):u(bank+42)+w(bank+34)])
    payload = v.astype('>u2').tobytes()
    assert payload[tilebase*32:tilebase*32+len(reference)]==reference
    expected=np.array(expected).reshape(height,width)
    loc=[]
    for base in (0,8192,16384,24576):
        plane=v[base:base+4096].reshape(64,64)
        for off in (0,0x8000):
            if np.array_equal(plane[np.ix_((np.arange(height)+top)%64,(np.arange(width)+left)%64)],expected^off):
                loc.append(hex(2*base))
    print(tag, name, 'expected world tile',left,top,'bank',hex(tilebase),'matching planes',loc,flush=True)
    if not loc:
        plane=v[24576:28672].reshape(64,64);got=plane[np.ix_((np.arange(height)+top)%64,(np.arange(width)+left)%64)]
        print("Mismatch by row", [np.nonzero(a!=z)[0].tolist() for a,z in zip(got,expected)])
        c.shot(ROOT/f"inspect_{tag}.png")
    assert loc,(name,expected[0].tolist(),[hex(int(v[k+64*(top%64)+left%64])) for k in (0,8192,16384,24576)])
if __name__=='__main__':
    if len(sys.argv)==1:menus()
    else:object_case(sys.argv[1],int(sys.argv[2]))
