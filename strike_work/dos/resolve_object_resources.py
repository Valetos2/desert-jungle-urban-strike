"""Resolve sector object descriptors via THINGS and LEVEL resource names.
This identifies resource references, not gameplay type or mission role.
"""
from pathlib import Path
from collections import Counter
import json,argparse
ROOT=Path(__file__).resolve().parent

def resolve(root,correspondence,tails):
 things=(root/'THINGS').read_bytes();out={}
 for level,info in correspondence.items():
  raw=(root/('LEVEL'+level)).read_bytes()
  names={r['address_word']:r['resource'] for r in tails['levels'][level]['entries']}
  offsets=[x['offset'] for x in info['objects']] if level=='A' else [x['dos_offset'] for x in info['matches']]
  rows=[]
  for offset in offsets:
   ptr=int.from_bytes(raw[offset:offset+4],'little');at=ptr&65535
   assert ptr>>16==0x4b1b,hex(ptr)
   assert at+3<=len(things)
   slot=int.from_bytes(things[at:at+2],'little')
   rows.append({'object_offset':offset,'things_offset':at,'resource_slot':slot,'resource':names.get(slot),'byte2':things[at+2]})
  out[level]={'count':len(rows),'resolved':sum(x['resource'] is not None for x in rows),'resources':dict(Counter(x['resource'] or 'UNRESOLVED' for x in rows)),'objects':rows}
 return out
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--input',type=Path,default=ROOT/'unpacked/jungle');v=a.parse_args()
 r=resolve(v.input,json.loads((ROOT/'object_correspondence.json').read_text()),json.loads((ROOT/'level_resources.json').read_text()))
 (ROOT/'object_resources.json').write_text(json.dumps(r,indent=2)+'\n')
 for n,x in r.items():print(n,x['resolved'],'/',x['count'])
