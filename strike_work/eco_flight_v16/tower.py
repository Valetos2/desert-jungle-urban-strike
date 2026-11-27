# Campaign 8's separator descends a pixel per row from the inner vertical edge.
# Only change the affected tile instances. The terrain-facing edge is untouched.
g=0x2c0000;bank=u(0x210100+64);raw=u(bank+42)
size=w(bank+34)
tiles={}
for y,x in [(y,65) for y in range(125,130)]+[(y,66+y-130) for y in range(130,139)]:
    entry=u(g+22)+2*((y//8)*w(g)+x//8)
    attr=w(entry)
    if entry not in tiles:
        start=raw+(attr&2047)*32
        idx=size//32
        assert raw+size+32<0x2c4000
        copy(raw+size,start,32);size+=32
        put(entry,'H',(attr&0xf800)|idx);tiles[entry]=idx
    tx=(7-x%8) if attr&2048 else x%8
    ty=(7-y%8) if attr&4096 else y%8
    addr=raw+32*tiles[entry]+4*ty+tx//2
    shift=4*(1-tx%2)
    # These tiles use world palette zero, whose slot 12 is the dark grey.
    assert ((attr>>13)+1)%4==0
    rom[addr]=(rom[addr]&~(15<<shift))|(12<<shift)
put(bank+34,'HHI',size,2,size)
# Save gs1 overlooks shelter 83. Gunner 43 stands just north of its rear
# right roof edge. Set priority only on the roof tiles under that sprite.
house=0x2762c0
roof=0x2f2800
src=u(house)
copy(roof,src,32)
count=w(src)*w(src+2)
copy(roof+32,u(src+22),2*count)
put(roof+22,'I',roof+32)
for y in range(2):
    for x in range(5,9):
        cell=roof+32+2*(y*w(src)+x)
        put(cell,'H',w(cell)|0x8000)
put(house,'I',roof)
# This stationary gun is behind shelter 83. Its two native parts normally
# use a single depth sample each, missing the roof at their southern edges.
# For this instance keep the parts' original low priority in the SAT. The
# terrain base has low priority and the overlapping roof tiles have high.
gun=0x2b0580
assert u(gun)==0x18ded8
kind=0x2f2940
copy(kind,u(gun),90)
for offset in (64,76):
    put(kind+offset,'H',(w(kind+offset)&~0x4000)|0x0400)
put(gun,'I',kind)
