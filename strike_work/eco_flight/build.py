"""Build the private Eco Threat ground-flight prototype on Jungle v05."""
from pathlib import Path
import struct, hashlib, json, argparse
ROOT=Path(__file__).resolve().parent
args=argparse.ArgumentParser(description=__doc__)
args.add_argument('--base',type=Path,default=Path('strike_work/v12/Jungle_Strike_v05_Menu_Polish.bin'))
args.add_argument('--original',type=Path,default=Path('strikehd/rom/jungle_strike.bin'))
args.add_argument('--assets',type=Path,default=Path('strike_work/dos/color_experiment/output/ground_checker'))
args=args.parse_args()
ROM=args.base
assert hashlib.sha256(ROM.read_bytes()).hexdigest()=='ab521b5c88aa58020781cedff19a4929f1af8a048bd479a7128be45952bd9ea5', 'Expected accepted Jungle v05 base'
b=bytearray(ROM.read_bytes())
original=args.original.read_bytes()
assert hashlib.sha1(original).hexdigest()=='7a7568e39341b1bb218280ee05c2b37c273317b5', 'Wrong original ROM'
def word(a):return int.from_bytes(original[a:a+2],'big')
def ptr(a):return int.from_bytes(original[a:a+4],'big')&0xffffff
def w(a,v):struct.pack_into('>H',b,a,v)
def l(a,v):struct.pack_into('>I',b,a,v)
def free(a,data):
 assert 0x200000<=a and a+len(data)<=0x400000
 assert b[a:a+len(data)]==bytes([255])*len(data),(hex(a),len(data))
 b[a:a+len(data)]=data
assets=args.assets
level=0x210200; ts=0x210000; tiletab=0x210100; palettes=0x210400
empty=0x210500; dynamic=0x210700; player=0x210900; listing=0x210940
baselevel=ptr(0x192932);basetab=ptr(0x525ba);basets=ptr(basetab+0x28)
header=bytearray(original[baselevel:baselevel+0x60+70*4])
struct.pack_into('>I',header,0x5c,0x300000)
struct.pack_into('>I',header,0x46,palettes)
struct.pack_into('>I',header,0x3e,empty)
struct.pack_into('>I',header,0x42,dynamic)
free(level,header);l(0x192932,level)
tab=bytearray(original[basetab:basetab+33*4]);struct.pack_into('>I',tab,0x28,ts);free(tiletab,tab);l(0x525ba,tiletab)
patterns=(assets/'patterns.bin').read_bytes();free(0x220000,patterns)
desc=bytearray(original[basets:basets+46]);struct.pack_into('>H',desc,0x22,len(patterns));struct.pack_into('>H',desc,0x24,2);struct.pack_into('>I',desc,0x26,len(patterns));struct.pack_into('>I',desc,0x2a,0x220000);free(ts,desc)
pal=bytearray(original[ptr(baselevel+0x46):ptr(baselevel+0x46)+128]);pal[32:64]=(assets/'palette.bin').read_bytes();free(palettes,pal)
free(empty,bytes(70*4));dy=bytearray(70*4);sector=5*10+1;struct.pack_into('>I',dy,sector*4,listing);free(dynamic,dy)
actor=bytearray(original[0x19abc0:0x19abc0+28]);assert ptr(0x19abc0+8)==0xfff56a
struct.pack_into('>HH',actor,12,2600,800);free(player,actor);free(listing,struct.pack('>HI',1,player))
# Same world dimensions as Jungle level 2. New map descriptors use palette 1.
blob=bytearray((assets/'native_ground.bin').read_bytes())
for address in set(struct.unpack_from('>560I',blob)):
 struct.pack_into('>H',blob,address-0x300000+0x1e,0x2000)
free(0x300000,blob)
# Front-end initializes the campaign index to 1. Campaign start reaches this map.
assert original[0x38c90:0x38c9a]==bytes.fromhex('23fc0000000000ff10b0')
l(0x38c92,1)
# Assembled start.asm; kept here to avoid an assembler dependency.
setup=bytes.fromhex('33fc006300ff10ce33fc270f00ff10c633fc270f00ff10d4227c00ff16504e75')
free(0x211000,setup);assert original[0x3db78:0x3db7e]==bytes.fromhex('227c00ff1650');b[0x3db78:0x3db7e]=bytes.fromhex('4eb900211000')
# Keep the game's own intro and options flow intact.
checkend=2093788;checkat=2093816
l(checkat,sum(int.from_bytes(b[i:i+4],'big') for i in range(0,checkend,4) if i!=0x18c)&0xffffffff)
w(0x18e,sum(int.from_bytes(b[i:i+2],'big') for i in range(0x200,len(b),2))&0xffff)
path=ROOT/'Jungle_Strike_Eco_Threat_Flight_TEST_v1.bin';path.write_bytes(b)
(ROOT/'build_report.json').write_text(json.dumps({'base_sha256':hashlib.sha256(ROM.read_bytes()).hexdigest(),'sha256':hashlib.sha256(b).hexdigest(),'size':len(b),'level_pointer':hex(level),'tileset_pointer':hex(ts),'spawn':[800,2600],'original_sha1':hashlib.sha1(original).hexdigest(),'standard_checksum':hex(int.from_bytes(b[0x18e:0x190],'big'))},indent=2)+'\n')
print(path)
