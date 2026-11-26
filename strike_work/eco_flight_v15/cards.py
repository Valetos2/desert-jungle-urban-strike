icons = (dos/'ICONSA').read_bytes()
resources = runpy.run_path(str(work/'dos/eco_threat_reference.py'))
palette = np.array(resources['palette'](icons),np.uint8).reshape(-1,3)
def icon(n):
    off = 32+struct.unpack_from('<I',icons,60+16*n)[0]
    return Image.fromarray(palette[np.frombuffer(icons[off:off+6336],np.uint8).reshape(72,88)])

def ground():
    # Select an 8x6-tile all-snow patch from the actual expanded terrain.
    pal = np.array([[(w(0x210400+2*i)>>shift&7)*255//7 for shift in (1,5,9)] for i in range(64)],np.uint8)
    for g in dict.fromkeys(u(0x300000+4*j) for j in range(560)):
        values = np.frombuffer(rom,dtype='>u2',count=512,offset=u(g+22)).reshape(16,32)
        for y in (0,6):
            for x in (0,8,16,24):
                rgb = np.empty((48,64,3),np.uint8)
                for j,v in enumerate(values[y:y+6,x:x+8].flat):
                    v = int(v)+w(g+30)
                    raw = np.frombuffer(rom,np.uint8,32,0x220000+32*(v&2047))
                    pix = np.stack([raw>>4,raw&15],axis=1).reshape(8,8)
                    if v&2048: pix=pix[:,::-1]
                    if v&4096: pix=pix[::-1]
                    yy,xx=divmod(j,8)
                    rgb[yy*8:yy*8+8,xx*8:xx*8+8] = pal[pix+16*((v>>13)&3)]
                if rgb.min()>100 and np.unique(rgb.reshape(-1,3),axis=0).shape[0]>=3:
                    return Image.fromarray(rgb)
    raise ValueError('Snow sample not found')

cram = [0x48,8,0x91,0xd9,0x99,0,0x1ff,0x124,0x49,0xdb,0x1b7,0x16d,0x124,0xd2,0x3a,0x20]
colors = np.array([[(v>>k&7)*255/7 for k in (0,3,6)] for v in cram[1:]])
def card(index, photo, overlay=None):
    obj = 0x2e0000+index*0x1000
    gfx,frame,art = obj+128,obj+160,obj+320
    copy(obj,0x2a2000,256)
    put(obj+54,'I',gfx)
    put(gfx+14,'I',frame)
    put(frame+36,'I',art)
    if overlay:
        copy(obj+66,obj+54,12)
        copy(obj+54,overlay,12)
        put(obj,'H',1)
    put(gfx+2,'H',3168)
    put(frame,'4h',-36,-44,36,44)
    put(frame+12,'HH',3168,99)
    put(frame+18,'H',8)
    put(frame+28,'HHII',3168,2,3168,art)
    tile=0
    for j in range(9):
        y,x=divmod(j,3)
        width=(4,4,3)[x]
        put(frame+40+8*j,'4H',128-49+24*y,(4*(width-1)+2)<<8,tile,128-44+32*x)
        tile+=width*3
    pixels=np.asarray(photo.resize((88,72),Image.Resampling.NEAREST),dtype=float)
    # Palette one supplies the red stripe. Resolve the water shades against
    # two close dark colors, retaining the DOS wave pattern.
    target=colors
    if index==0:
        row=[72,8,145,217,153,0,31,5,72,12,439,247,365,292,219,3]
        target=np.array([[(v>>k&7)*255/7 for k in (0,3,6)] for v in row[1:]])
        for j in range(9): put(frame+44+8*j,'H',w(frame+44+8*j)|0x2000)
    px=1+((pixels[:,:,None,:]-target)**2).sum(3).argmin(2)
    if index==0:
        sea_pixels=(pixels[:,:,0]<25)&(pixels[:,:,2]>pixels[:,:,0]+25)
        px[sea_pixels]=np.where(pixels[:,:,1][sea_pixels]>70,2,8)
        stripe=(pixels[:,:,0]>pixels[:,:,1]*1.5)&(pixels[:,:,0]>pixels[:,:,2]*1.5)
        px[stripe]=7
    if index>=8:
        grays=np.array([5,6,7,8,9,11,12])
        px=grays[((pixels[:,:,None,:]-colors[grays-1])**2).sum(3).argmin(2)]
    data=bytearray()
    for y in (0,24,48):
        for x in (0,32,64):
            for xx in range(x,min(88,x+32),8):
                for yy in range(y,y+24,8):
                    vals=px[yy:yy+8,xx:xx+8].ravel()
                    data.extend((16*vals[::2]+vals[1::2]).astype(np.uint8).tobytes())
    assert len(data)==3168
    rom[art:art+3168]=data
    desc=u(menu+2+12*index)
    if index>=8:
        clone=0x2dc000+512*(index-8)
        copy(clone,desc,512)
        put(menu+2+12*index,'I',clone)
        desc=clone
    rom[desc+1]=2
    put(desc+6,'I',obj)

sea=icon(0)
hull=resources['sprite']((dos/'BOATPT').read_bytes(),1).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
sea.paste(hull,((sea.width-hull.width)//2,(sea.height-hull.height)//2),hull)
card(0,sea,0x298000+54)
for index in range(3,8):
    card(index,icon(index+1))
snow_patch=ground()
for index,actor in enumerate([0x18e618,0x18e594,0x18e65a,0x18f6d4],8):
    card(index,snow_patch,actor+54)
