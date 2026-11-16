"""Read the contiguous named-resource tails of Jungle DOS LEVEL1..LEVELA.
Run from repository root after unpack_dat.py. No original bytes are exported.
The meaning of kind/address words is not yet established by loader tracing.
"""
from pathlib import Path
import json,re,struct
ROOT=Path(__file__).resolve().parent
DEFAULT=ROOT/'unpacked/jungle'
ENTRY=re.compile(rb'([\x00\x01\x02\x42])\x00(..)([A-Za-z0-9_-]{2,12})\x00',re.S)
def parse_tail(data):
 # Anchor on the map name, then require every remaining byte to parse.
 candidates=[m.start() for m in ENTRY.finditer(data) if m[3].lower().startswith(b'map')]
 valid=[]
 for start in candidates:
  pos=start;rows=[]
  while data[pos:pos+2]!=b'\xff\xff':
   m=ENTRY.match(data,pos)
   if m is None:break
   rows.append({'offset':pos,'kind':m[1][0],'address_word':int.from_bytes(m[2],'little'),'resource':m[3].decode()});pos=m.end()
  if pos+2==len(data) and rows:valid.append({'tail_offset':start,'entries':rows})
 if len(valid)!=1:raise ValueError(f'Expected one complete resource tail, found {len(valid)}')
 return valid[0]
def inspect(root=DEFAULT):
 levels={n:parse_tail((root/('LEVEL'+n)).read_bytes()) for n in '123456789A'}
 names={n:{r['resource'].lower() for r in v['entries']} for n,v in levels.items()}
 overlap={name:[n for n in '123456789' if name in names[n]] for name in sorted(names['A'])}
 return {'levels':levels,'mission10_resources_in_other_level_tails':overlap,
         'caution':'These are resource dependencies, not object instances. Absence from another LEVEL tail does not prove an asset is new or unused by global loading.'}
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,default=DEFAULT);ap.add_argument('--output',type=Path,default=ROOT/'level_resources.json');a=ap.parse_args()
 result=inspect(a.input);a.output.write_text(json.dumps(result,indent=2)+'\n')
 for n,v in result['levels'].items():print(n,hex(v['tail_offset']),len(v['entries']))
