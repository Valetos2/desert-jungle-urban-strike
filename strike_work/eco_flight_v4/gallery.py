"""Pair the game-rendered scenes, cropping both versions identically."""
from build import ROOT
from PIL import Image, ImageDraw
names=['F165','F166','F167','F168','F174']
im=Image.new('RGB',(504,5*120+24),'#171d24')
d=ImageDraw.Draw(im)
for column,version in enumerate([3,4]):
    x=44+column*230
    d.text((x+4,4),f'Flight TEST v{version}',fill='white')
    for row,name in enumerate(names):
        y=24+row*120
        shot=Image.open(ROOT/f'{name}_v{version}.png').crop((54,54,282,172))
        im.paste(shot,(x,y))
        d.text((5,y+50),name,fill='white')
im.save(ROOT/'Eco_Threat_objects_v3_v4.png')
