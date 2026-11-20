"""Recolor the existing Eco Threat terrain, using the native Snow Fortress texture."""
import struct
from collections import defaultdict
import numpy as np

def recolor(rom, v3, static_water_index=13):
    def w(p): return struct.unpack_from('>H',rom,p)[0]
    def u(p): return struct.unpack_from('>I',rom,p)[0]
    def pixels(data):
        raw=np.frombuffer(data,np.uint8)
        return np.stack((raw>>4, raw&15),axis=-1).reshape(-1,8,8)
    oldmap=(v3/'assets/native_ground.bin').read_bytes()
    oldtiles=pixels((v3/'assets/patterns.bin').read_bytes())
    snowtiles=pixels((v3/'stock6_patterns.bin').read_bytes())
    snowmap=u(0x102e30+22)+2
    snowcodes=np.frombuffer(rom[snowmap:snowmap+512],np.uint8).reshape(16,32)
    # Palette 0 is the untouched Snow Fortress terrain line. Palette 1 also
    # preserves the native building/pad colors; only 13 and 15 are free.
    coast=np.array([13,static_water_index,13,13,2,2,3,3,5,15,15,15,12,3,5,13],np.uint8)
    tiles=[]
    aliases={}
    blocks={}
    terrain=bytearray(560*4)
    for block in range(560):
        desc=struct.unpack_from('>I',oldmap,block*4)[0]-0x300000
        source=struct.unpack_from('>I',oldmap,desc+22)[0]-0x300000
        names=[]
        for i,v in enumerate(struct.unpack_from('>512H',oldmap,source)):
            pat=oldtiles[v&2047]
            if v&0x1000: pat=pat[::-1]
            if v&0x0800: pat=pat[:,::-1]
            if np.all((pat>=4)&(pat<=8)):
                code=int(snowcodes[i//32,i%32])
                pat=snowtiles[code&63]
                if code&128: pat=pat[::-1]
                if code&64: pat=pat[:,::-1]
                palette=0
            else:
                pat=coast[pat]
                palette=0x2000
            key=pat.tobytes()
            if key not in aliases:
                index=len(tiles)
                tiles.append(pat.copy())
                for flip in range(4):
                    t=pat[::-1] if flip&2 else pat
                    if flip&1: t=t[:,::-1]
                    aliases.setdefault(t.tobytes(),index|(flip<<11))
            names.append(aliases[key]|palette)
        data=struct.pack('>512H',*names)
        if data not in blocks:
            address=0x300000+len(terrain)
            blocks[data]=address
            header=bytearray(oldmap[desc:desc+32])
            struct.pack_into('>I',header,22,address+32)
            terrain.extend(header+data)
        struct.pack_into('>I',terrain,block*4,blocks[data])
    packed=np.asarray(tiles,np.uint8).reshape(-1,64)
    pattern=(packed[:,::2]*16+packed[:,1::2]).tobytes()
    assert len(tiles)<=342, len(tiles)
    return pattern,terrain
