"""Composite the stock map-screen supplies over a 1:1 sample of Eco terrain."""
from tempfile import TemporaryDirectory
from scipy.ndimage import binary_fill_holes, label

def snow_sample():
    pal=np.array([[(w(0x210400+2*i)>>k&7)*255/7 for k in (1,5,9)] for i in range(64)])
    best=(-1,None)
    for g in dict.fromkeys(u(0x300000+4*j) for j in range(560)):
        pixels=img(g)
        for y in (0,48):
            for x in (0,80,160):
                patch=pal[pixels[y:y+72,x:x+88]]
                if patch.min()<110:continue
                score=patch.std(axis=(0,1)).sum()
                if score>best[0]:best=(score,patch.copy())
    assert best[1] is not None
    return best[1]

def native_photos():
    import sys
    tools=runpy.run_path(str(work/'eco_flight_v11/check.py'))
    with TemporaryDirectory() as folder:
        p=Path(folder)/'reference.bin'
        donor=bytearray(rom)
        runpy.run_path(str(work/'eco_flight_v4/build.py'))['checksum'](donor)
        p.write_bytes(donor)
        start=tools['spawn'];start.__globals__['ROM']=p
        c,_=start(2200,1025);press=tools['press']
        press(c,'S');press(c,'B')
        result=[]
        for j in range(12):
            if j>=8:
                filename=Path(folder)/'frame.png';c.shot(str(filename))
                result.append(np.array(Image.open(filename).convert('RGB').crop((56,40,144,112))))
            press(c,'R',30)
        tools['closed'](c)
        return result

snowpic=snow_sample()
for j,photo in enumerate(native_photos()):
    yy,xx=np.indices(photo.shape[:2])
    # The stock ground uses tan highlights and brown shadow flecks. Restrict
    # the flood fill to the item, retaining enclosed cut-outs in its drawing.
    r,g,b=photo.transpose(2,0,1).astype(int)
    center=(xx>=18)&(xx<=71)&(yy>=15)&(yy<=57)
    earthy=(r>g+8)&(g>b+8)
    vegetation=(g>125)&(r<70)&(b<12)
    regions,count=label(center&~earthy&~vegetation)
    sizes=np.bincount(regions.ravel());sizes[0]=0
    mask=binary_fill_holes(regions==sizes.argmax())
    original=photo.astype(float)*255/238
    target=np.where(mask[:,:,None],original,snowpic)
    base=0x2f4000+0x1800*j
    native=u(menu+2+12*(8+j))
    clone=0x2dc000+j*512
    copy(clone,native,512);put(menu+2+12*(8+j),'I',clone)
    obj=base;gfx=base+128;frame=base+160;art=base+512
    copy(obj,0x2e3000,200)
    rom[clone+1]=2;put(clone+6,'I',obj);put(obj,'H',0)
    put(obj+54,'I',gfx);put(obj+62,'HH',0,0x4000)
    # Static picture with smaller sprites so the original object and nearby
    # snow can choose a palette row independently in each 16x16 region.
    copy(gfx,0x2e0080,32);copy(frame,0x2e00a0,40)
    put(gfx+14,'I',frame);put(frame+18,'H',29)
    put(frame+36,'I',art)
    data=bytearray()
    for n in range(30):
        yy,xx=divmod(n,6);y=16*yy;x=16*xx
        ys=slice(y,y+16);xs=slice(x,x+16)
        part=target[ys,xs];weights=1+mask[ys,xs]*500
        best=None
        for row in range(4):
            d=((part[:,:,None]-colors[row,1:])**2).sum(3)
            d[~mask[ys,xs]]+=(np.ptp(colors[row,1:],axis=1)>1)*200000
            cost=(weights*d.min(2)).sum()
            if best is None or cost<best[0]:best=(cost,row,1+d.argmin(2))
        _,row,px=best;h,wd=px.shape
        put(frame+40+8*n,'4H',79+y,((wd//8-1)*4+h//8-1)<<8,
            (row<<13)+len(data)//32,84+x)
        for sx in range(0,wd,8):
            for sy in range(0,h,8):
                pix=px[sy:sy+8,sx:sx+8].astype(np.uint8).ravel()
                data.extend((pix[::2]*16+pix[1::2]).tobytes())
    assert len(data)==3168
    rom[art:art+len(data)]=data
