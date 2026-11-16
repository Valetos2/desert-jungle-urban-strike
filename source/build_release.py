"""Python 3; usage: python build_release.py ORIGINAL.bin [OUTPUT_DIRECTORY]
No third-party packages needed. IPS targets precisely the attached original ROM.
"""
from pathlib import Path
import hashlib,json,sys
SOURCE_SHA256='ae63ade3413ce1b4816cd335e1fc4673c272b40026222566e8c9e3b7b01ca43d'
def checksum(b):return sum(int.from_bytes(b[i:i+2],'big') for i in range(0x200,len(b),2))&65535
def ips_make(a,b):
 out=bytearray(b'PATCH');i=0
 while i<len(b):
  if a[i]==b[i]:i+=1;continue
  start=i
  while i<len(b) and a[i]!=b[i] and i-start<65535:i+=1
  out+=start.to_bytes(3,'big')+(i-start).to_bytes(2,'big')+b[start:i]
 return bytes(out+b'EOF')
def ips_apply(a,p):
 b=bytearray(a);i=5;assert p[:5]==b'PATCH'
 while p[i:i+3]!=b'EOF':
  at=int.from_bytes(p[i:i+3],'big');n=int.from_bytes(p[i+3:i+5],'big');i+=5;assert n
  b[at:at+n]=p[i:i+n];i+=n
 assert i+3==len(p);return bytes(b)
def build(src,out):
 a=Path(src).read_bytes();assert hashlib.sha256(a).hexdigest()==SOURCE_SHA256,'Wrong original ROM; use Urban Strike (W) [!] supplied in this conversation'
 b=bytearray(a);changes=[]
 def patch(at,expected,data,reason):
  assert b[at:at+len(expected)]==expected,hex(at)
  assert len(expected)==len(data)
  b[at:at+len(data)]=data;changes.append({'offset':hex(at),'before':expected.hex(),'after':data.hex(),'reason':reason})
 code=Path(__file__).with_name('urban_input_code.bin').read_bytes()
 patch(0x1ff200,b'\xff'*len(code),code,'Input helpers in original unused ROM tail')
 patch(0x4c78,bytes.fromhex('61004f660839000100ff05f1'),bytes.fromhex('4eb9001ff2004e714e714e71'),'Preserve D1 timer while polling controller in cutscene loop; replay displaced BTST')
 patch(0x18fa,bytes.fromhex('23fc0000000000ff10b4'),bytes.fromhex('4eb9001ff2184e714e71'),'Detect six-button controller during options initialization')
 music=Path(__file__).with_name('urban_music_code.bin').read_bytes()
 patch(0x1ff260,b'\xff'*len(music),music,'Music-safe setup and cleanup around movie-sequence loader')
 patch(0xbec,bytes.fromhex('48e7fffe23fc00ff55de00ff55d6'),bytes.fromhex('4ef9001ff260'+'4e71'*4),'Save caller interrupt state, enable existing audio-only VBlank during movie resource preparation')
 patch(0xc8c,bytes.fromhex('4cdf7fff4e75'),bytes.fromhex('4ef9001ff28e'),'Restore original interrupt handler, SR and registers after movie sequence')
 sound=Path(__file__).with_name('urban_sound_code.bin').read_bytes()
 patch(0x1ff300,b'\xff'*len(sound),sound,'Sound-test handlers and 53 bank/id pairs after removal of v03 entries14..29')
 for at,old,new,reason in [
  (0x7cb1e,'0002','0004','Reveal SOUND and MOVIE rows'),
  (0x2efc,'48e7e0e048c1','4ef9001ff300','Silent bounded sound-index adjustment; stop previous playback'),
  (0x1e38,'203900ff10b8','4ef9001ff368','Play selected bank/id pair'),
  (0x1c68,'2f03163c0020','4ef9001ff3b8','Stop sound when leaving its row; restore menu sound bank'),
  (0x1f2e,'08b9000000ff10a0','4eb9001ff3d24e71','Stop and restore menu bank on Options exit'),
  (0x1cd8,'0007cae8','001ff800','Point Options footer to new help string'),
  (0x7cbc7,'f4','00','Place sound index to the right of label'),
  (0x1e08,'0004','0006','A stops: previous input bit'),
  (0x1e14,'0004','0006','A stops: current input bit'),
  (0x1e26,'0005','0004','B plays: previous input bit'),
  (0x1e32,'0005','0004','B plays: current input bit')]:
  patch(at,bytes.fromhex(old),bytes.fromhex(new),reason)
 footer=b'\x01\x07\x1aA Stop  B Play  Start Exit\0\xff'
 patch(0x1ff800,b'\xff'*len(footer),footer,'Help text using existing font, below sound row')
 movie=Path(__file__).with_name('urban_movie_code.bin').read_bytes()
 patch(0x1ff900,b'\xff'*len(movie),movie,'Movie player, settings preservation, menu reconstruction and small-font selector')
 row=Path(__file__).with_name('movie_row.bin').read_bytes()
 patch(0x7cbca,a[0x7cbca:0x7cbca+len(row)],row,'17 nonempty movie selections')
 patch(0x1ec2,bytes.fromhex('0c39000000ff045a'),bytes.fromhex('4ef9001ff9004e71'),'Dispatch movie B button while retaining original control-layout handling')
 patch(0x2dda,bytes.fromhex('6100e1f8600000ae'),bytes.fromhex('4ef9001ffc004e71'),'Draw movie title using original small font')
 for at,n,target in [(0x1ffc,10,0x1ffd00),(0x1d38,8,0x1ffd40),(0x1c74,10,0x1ffd80)]:
  patch(at,a[at:at+n],bytes.fromhex('4ef9')+target.to_bytes(4,'big')+bytes.fromhex('4e71')*((n-6)//2),'Movie return to Options / retained MOVIE cursor / cyclic options navigation')
 for at,old,new in [(0x7cb66,14,13),(0x7cb96,18,17),(0x7cbbd,23,21)]:
  patch(at,bytes([old]),bytes([new]),'Compact options rows to make room for MOVIE')
 menu_music=Path(__file__).with_name('urban_menu_music_code.bin').read_bytes()
 patch(0x1ff500,b'\xff'*len(menu_music),menu_music,'Keep audio VBlank active during main-menu resource initialization')
 patch(0x6fb8,bytes.fromhex('33fc000000ff1306'),bytes.fromhex('4ef9001ff5004e71'),'Wrap main-menu resource preparation and restore caller interrupt state afterwards')
 longsum=sum(int.from_bytes(b[i:i+4],'big') for i in range(0,0x1ff0d4,4) if i!=0x18c)&0xffffffff
 patch(0x1ff0f0,a[0x1ff0f0:0x1ff0f4],longsum.to_bytes(4,'big'),'Update original additional integrity check; do not bypass it')
 patch(0x18e,a[0x18e:0x190],checksum(b).to_bytes(2,'big'),'Update standard Sega checksum')
 out=Path(out);out.mkdir(parents=True,exist_ok=True);name='Urban_Strike_Menu_Base'
 ip=ips_make(a,b);assert ips_apply(a,ip)==b
 assert len(a)==len(b)==2097152
 assert longsum==int.from_bytes(b[0x1ff0f0:0x1ff0f4],'big')
 assert checksum(b)==int.from_bytes(b[0x18e:0x190],'big')
 (out/(name+'.bin')).write_bytes(b);(out/(name+'.ips')).write_bytes(ip)
 (out/(name+'_manifest.json')).write_text(json.dumps({'original_sha256':SOURCE_SHA256,'output_sha256':hashlib.sha256(b).hexdigest(),'size':len(b),'changes':changes,'checks':['original SHA256','expected original bytes','same ROM size','standard checksum','IPS round trip']},indent=2))
 print(hashlib.sha256(b).hexdigest())
if __name__=='__main__':build(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else '.')
