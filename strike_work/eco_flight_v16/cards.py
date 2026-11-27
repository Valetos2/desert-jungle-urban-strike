icons=(dos/'ICONSA').read_bytes()
palette=np.array(res['palette'](icons),np.uint8).reshape(-1,3)
rows=np.array([[72,8,145,217,153,0,511,292,73,219,439,365,292,210,58,32],
               [72,8,145,217,153,0,31,5,72,12,439,247,365,292,219,3],
               [72,438,229,146,73,0,58,32,8,81,154,227,238,165,83,10],
               [72,511,32,25,16,0,63,30,9,228,237,136,208,290,146,73]])
colors=np.stack([((rows>>k)&7)*255/7 for k in (0,3,6)],axis=2)
for i in (0,3,4,5):
    obj=0x2e0000+i*0x1000;frame=obj+160
    if i==0:
        pic=Image.new('RGB',(88,72),(36,73,73))
        hull=res['sprite']((dos/'BOATPT').read_bytes(),1).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        pic.paste(hull,((88-hull.width)//2,(72-hull.height)//2),hull)
        pixels=np.asarray(pic).astype(float)
    else:
        p=32+struct.unpack_from('<I',icons,60+16*(i+1))[0]
        pixels=palette[np.frombuffer(icons[p:p+6336],np.uint8).reshape(72,88)].astype(float)
    data=bytearray()
    for j in range(9):
        yy,xx=divmod(j,3);x,y=xx*32,yy*24
        part=pixels[y:y+24,x:min(88,x+32)]
        red=(part[:,:,0]>1.6*part[:,:,1])&(part[:,:,0]>1.6*part[:,:,2])&(part[:,:,0]>12)
        fire=(part[:,:,0]>90)&(part[:,:,1]>.45*part[:,:,0])&(part[:,:,2]<part[:,:,1]*.55) if i==4 else np.zeros(red.shape,bool)
        best=None
        for row in range(4):
            dist=((part[:,:,None,:]-colors[row,1:])**2).sum(3)
            # Protect identifying colors even when a grey is slightly closer.
            rr,gg,bb=colors[row,1:].T
            if red.any():dist[red]+=((rr<105)|(gg>.39*rr)|(bb>.39*rr))*250000
            if fire.any():dist[fire]+=((rr<125)|(gg<75)|(bb>gg*.65))*250000
            px=1+dist.argmin(2)
            score=dist.min(2).sum()
            if best is None or score<best[0]:best=(score,row,px.astype(np.uint8))
        _,row,px=best
        entry=frame+44+8*j
        put(entry,'H',(w(entry)&0x1fff)|(row<<13))
        for tx in range(0,px.shape[1],8):
            for ty in range(0,24,8):
                v=px[ty:ty+8,tx:tx+8].ravel()
                data.extend((16*v[::2]+v[1::2]).tobytes())
    rom[obj+320:obj+320+len(data)]=data
# Re-anchor all twelve views of the rotating native dish on the cabin roof.
dish=0x2f2000
copy(dish,0x1420de,62)
for j in range(12):
    old=u(0x1420de+14+4*j);new=dish+64+48*j
    assert w(old+18)==0
    copy(new,old,48);put(dish+14+4*j,'I',new)
    put(new+40,'H',w(old+40)-7);put(new+46,'H',w(old+46)+5)
put(0x2e0036,'I',dish)
