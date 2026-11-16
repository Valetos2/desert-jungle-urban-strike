from pathlib import Path
import json,struct,hashlib

def unpack(data):
 pos=0;out=bytearray();pending=[];table=None;escape=None
 def byte():
  nonlocal pos
  v=data[pos];pos+=1;return v
 def dictionary():
  nonlocal table,escape
  n=byte();table=[None for i in range(256)];marker=byte();escape=marker if n else None
  if n:
   for _ in range(n):
    key,left,right=byte(),byte(),byte();table[key]=((left,table[left] is not None),(right,table[right] is not None))
 def expanded():
  nonlocal pending
  if pending:return pending.pop()
  v=byte()
  if v==escape:return byte()
  stack=[(v,table[v] is not None)];value=[]
  while stack:
   symbol,ref=stack.pop()
   if ref:
    left,right=table[symbol];stack.extend([right,left])
   else:value.append(symbol)
   assert len(value)<16000000 and len(stack)<10000
  pending=list(reversed(value[1:]));return value[0]
 dictionary()
 while True:
  code=expanded()
  if code==0:return bytes(out),pos
  if code==128:
   assert not pending
   dictionary();continue
  if code&64:n=((code&63)<<8)|expanded()
  else:n=code&63
  if code&128:out.extend(bytes([expanded()])*n)
  else:out.extend(expanded() for _ in range(n))
  assert len(out)<16000000

def extract(name):
 b=Path('strike_work/dos/files',name+'.DAT').read_bytes();n=int.from_bytes(b[:4],'little');rows=[];dest=Path('strike_work/dos/unpacked',name.lower());dest.mkdir(parents=True,exist_ok=True)
 for i in range(n):
  p=16+i*16;label=b[p:p+8].decode().strip();off,packed,raw=struct.unpack_from('<IHH',b,p+8);end=int.from_bytes(b[p+24:p+28],'little') if i+1<n else len(b)
  try:value,used=unpack(b[off:end])
  except (IndexError,AssertionError) as e:
   rows.append({'name':label,'offset':off,'packed_bytes':end-off,'decode_error':str(e)});continue
  assert used<=end-off,(label,used,end-off)
  (dest/('EXECUTABLE' if label=='!' else label)).write_bytes(value)
  rows.append({'name':label,'offset':off,'packed_bytes':end-off,'consumed':used,'unpacked_bytes':len(value),'declared_paragraphs':raw,'size_matches':(len(value)+15)//16==raw,'trailing_bytes':end-off-used,'sha256':hashlib.sha256(value).hexdigest()})
 Path('strike_work/dos/'+name.lower()+'_resources.json').write_text(json.dumps(rows,indent=2));print(name,len(rows),'directory entries',sum(x.get('unpacked_bytes',0) for x in rows),'bytes')
if __name__=='__main__':extract('JUNGLE')
