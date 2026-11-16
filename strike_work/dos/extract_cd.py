from pathlib import Path
import json,hashlib
src=Path('upload/Desert Strike and Jungle Strike.bin');out=Path('strike_work/dos/files');f=src.open('rb')
def read(lba,n):
 data=bytearray()
 while len(data)<n:
  f.seek(lba*2352+16);data+=f.read(2048);lba+=1
 return bytes(data[:n])
pvd=read(16,2048);assert pvd[1:6]==b'CD001';print('Volume:',pvd[40:72].decode().strip())
rows=[]
def walk(rec,parent):
 lba=int.from_bytes(rec[2:6],'little');size=int.from_bytes(rec[10:14],'little');data=read(lba,size);pos=0
 while pos<len(data):
  n=data[pos]
  if not n:pos=((pos//2048)+1)*2048;continue
  r=data[pos:pos+n];pos+=n;name=r[33:33+r[32]]
  if name in [b'\0',b'\1']:continue
  name=name.decode('ascii').split(';')[0].rstrip('.');assert '/' not in name and name not in ['..','.']
  rel=parent/name
  if r[25]&2:walk(r,rel)
  else:
   at=int.from_bytes(r[2:6],'little');sz=int.from_bytes(r[10:14],'little');blob=read(at,sz);dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(blob)
   rows.append({'path':str(rel),'bytes':sz,'lba':at,'sha256':hashlib.sha256(blob).hexdigest()})
walk(pvd[156:190],Path())
Path('strike_work/dos/cd_files.json').write_text(json.dumps(rows,indent=2));print('Files',len(rows),'bytes',sum(r['bytes'] for r in rows));print('\n'.join(str(x) for x in rows[:65]))
