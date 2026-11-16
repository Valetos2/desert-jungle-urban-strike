"""Compare DOS sector-referenced object geometry against original Genesis ROM.
No original data payloads are exported; reports contain counts and correspondence offsets.
"""
from pathlib import Path
import struct,json,argparse,hashlib
from collections import defaultdict,Counter
ROOT=Path(__file__).resolve().parent
COUNTS={'1':64,'2':70,'3':70,'4':48,'5':56,'6':48,'7':96,'8':54,'9':36,'A':70}
def word(b,p):return int.from_bytes(b[p:p+2],'little')
def objects(data,count):
 refs={}
 for sector in range(count):
  at=word(data,sector*2)
  if not at:continue
  assert count*2<=at<len(data)-2,(sector,at)
  n=word(data,at);assert 0<n<1000 and at+2+2*n<=len(data),(sector,at,n)
  for i in range(n):
   obj=word(data,at+2+i*2);assert count*2<=obj<len(data)-36,(sector,obj)
   refs.setdefault(obj,[]).append(sector)
 return refs

def signature_dos(b,p):return tuple(word(b,p+o) for o in (4,6,8,10,16,18,20))
def signature_md(b,p):return tuple(int.from_bytes(b[p+o:p+o+2],'big') for o in (4,6,8,10,16,18,20))
def compare(root,rom):
 r=rom.read_bytes();assert hashlib.sha256(r).hexdigest()=='ea4eb94f7b3ecc1815ab2ac5adbd901b0e3a97a69ee2a31ead27600f12b1483a','Wrong original Jungle ROM';out={}
 for level in '123456789A':
  b=(root/('LEVEL'+level)).read_bytes();refs=objects(b,COUNTS[level]);result={'sector_count':COUNTS[level],'unique_objects':len(refs),'sector_references':sum(map(len,refs.values()))}
  if level!='A':
   num=int(level);start=int.from_bytes(r[0x19292e+(num-1)*4:0x192932+(num-1)*4],'big');end=int.from_bytes(r[0x19292e+num*4:0x192932+num*4],'big') if num<9 else 0x1c0000
   lookup={}
   for p in range(start,end-36,2):lookup.setdefault(signature_md(r,p),[]).append(p)
   rows=[]
   for p,sectors in sorted(refs.items()):
    matches=lookup.get(signature_dos(b,p),[]);rows.append({'dos_offset':p,'genesis_candidates':matches,'sectors':sectors})
   result.update({'unique_matches':sum(len(x['genesis_candidates'])==1 for x in rows),'ambiguous':sum(len(x['genesis_candidates'])>1 for x in rows),'unmatched':sum(not x['genesis_candidates'] for x in rows),'matches':rows})
  else:
   result['objects']=[{'offset':p,'sectors':s,'bounds_yx':list(signature_dos(b,p)[:4]),'position_yx':list(signature_dos(b,p)[4:6]),'parameter20':word(b,p+20),'word22':word(b,p+22)} for p,s in sorted(refs.items())]
   result['caution']='Mission10 sector count70 inferred from map area and header; field semantics beyond geometry remain unverified.'
  out[level]=result
 mapping=defaultdict(Counter)
 for n in '123456789':
  b=(root/('LEVEL'+n)).read_bytes()
  for row in out[n]['matches']:
   if len(row['genesis_candidates'])==1:
    p=row['dos_offset'];q=row['genesis_candidates'][0]
    mapping[int.from_bytes(b[p:p+4],'little')][int.from_bytes(r[q:q+4],'big')]+=1
 b=(root/'LEVELA').read_bytes()
 for row in out['A']['objects']:
  p=row['offset'];key=int.from_bytes(b[p:p+4],'little');row['descriptor_word32']=key
  row['genesis_descriptor_candidates']=[{'address':k,'supporting_matches':v} for k,v in mapping[key].items()]
 out['A']['objects_with_unique_descriptor_candidate']=sum(len(x['genesis_descriptor_candidates'])==1 for x in out['A']['objects'])
 return out
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,default=ROOT/'unpacked/jungle');ap.add_argument('--rom',type=Path,required=True);ap.add_argument('--output',type=Path,default=ROOT/'object_correspondence.json');a=ap.parse_args();r=compare(a.input,a.rom);a.output.write_text(json.dumps(r,indent=2)+'\n')
 for n,v in r.items():print(n,{k:x for k,x in v.items() if k not in ('matches','objects','caution')})
