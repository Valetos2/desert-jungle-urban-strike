"""python build_autoaim.py desert|jungle|urban ORIGINAL.bin OUTPUT_DIRECTORY
Python3 only. For Urban, includes all previous Urban changes automatically.
"""
from pathlib import Path
import sys,json,hashlib,tempfile
from build_release import build as build_urban, checksum,ips_apply

def build(game,source,out):
 root=Path(__file__).parent;c=json.loads((root/'autoaim_config.json').read_text())[game]
 a=Path(source).read_bytes();assert hashlib.sha256(a).hexdigest()==c['original_sha256'],'Wrong source ROM'
 if game=='urban':
  with tempfile.TemporaryDirectory() as td:
   build_urban(source,td);b=bytearray((Path(td)/'Urban_Strike_Menu_Base.bin').read_bytes())
 else:b=bytearray(a)
 if game=='desert':
  b.extend(b'\xff'*(0x200000-len(b)));b[0x1a4:0x1a8]=(len(b)-1).to_bytes(4,'big')
 code=(root/(game+'_autoaim_code.bin')).read_bytes();at=c['base']
 assert b[at:at+len(code)]==b'\xff'*len(code);b[at:at+len(code)]=code
 for n,at in enumerate(c['hooks']):
  assert b[at:at+8]==bytes.fromhex(c['expected'][n])
  b[at:at+8]=b'\x4e\xf9'+(c['base']+n*0x40).to_bytes(4,'big')+b'\x4e\x71'
 if game=='desert':
  from desert_input import apply as apply_desert_input
  apply_desert_input(b)
  from desert_tests import apply as apply_desert_tests
  apply_desert_tests(b)
 if game=='urban':
  from urban_controls import apply as apply_urban_controls
  apply_urban_controls(b)
 if game=='jungle':
  from jungle_input import apply
  apply(b)
  from jungle_tests import apply as apply_tests
  apply_tests(b)
 if game in ('jungle','desert'):
  from ea_input import apply as apply_ea
  apply_ea(game,b)
 check=sum(int.from_bytes(b[i:i+4],'big') for i in range(0,c['checkend'],4) if i!=0x18c)&0xffffffff
 b[c['checkat']:c['checkat']+4]=check.to_bytes(4,'big');b[0x18e:0x190]=checksum(b).to_bytes(2,'big')
 patch=bytearray(b'PATCH');i=0
 while i<len(b):
  if i<len(a) and a[i]==b[i]:i+=1;continue
  start=i
  while i<len(b) and (i>=len(a) or a[i]!=b[i]) and i-start<65535:i+=1
  patch+=start.to_bytes(3,'big')+(i-start).to_bytes(2,'big')+b[start:i]
 patch+=b'EOF';assert ips_apply(a,patch)==b
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 (out/(c['name']+'.bin')).write_bytes(b);(out/(c['name']+'.ips')).write_bytes(patch)
 print(c['name'],hashlib.sha256(b).hexdigest())
if __name__=='__main__':build(*sys.argv[1:4])
