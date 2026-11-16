"""Lossless IPS literal-record compression. python tools/repack_ips.py INPUT OUTPUT"""
from pathlib import Path
import sys

def repack(p):
 assert p[:5]==b'PATCH';out=bytearray(b'PATCH');pos=5
 while p[pos:pos+3]!=b'EOF':
  at=int.from_bytes(p[pos:pos+3],'big');n=int.from_bytes(p[pos+3:pos+5],'big');pos+=5
  if not n:
   out+=at.to_bytes(3,'big')+b'\0\0'+p[pos:pos+3];pos+=3;continue
  data=p[pos:pos+n];assert len(data)==n;pos+=n;i=0;start=0
  def literal(a,b):
   if a<b:out.extend((at+a).to_bytes(3,'big')+(b-a).to_bytes(2,'big')+data[a:b])
  while i<n:
   j=i+1
   while j<n and data[j]==data[i]:j+=1
   if j-i>=8 and at+i!=0x454f46:
    literal(start,i);out.extend((at+i).to_bytes(3,'big')+b'\0\0'+(j-i).to_bytes(2,'big')+data[i:i+1]);start=j
   i=j
  literal(start,n)
 return bytes(out+b'EOF'+p[pos+3:])
def apply(a,p):
 assert p[:5]==b'PATCH';b=bytearray(a);i=5
 while p[i:i+3]!=b'EOF':
  at=int.from_bytes(p[i:i+3],'big');n=int.from_bytes(p[i+3:i+5],'big');i+=5
  if n:data=p[i:i+n];i+=n
  else:n=int.from_bytes(p[i:i+2],'big');data=p[i+2:i+3]*n;i+=3
  if len(b)<at+len(data):b.extend(b'\0'*(at+len(data)-len(b)))
  b[at:at+len(data)]=data
 if len(p)==i+6:del b[int.from_bytes(p[i+3:i+6],'big'):]
 else:assert len(p)==i+3
 return bytes(b)
if __name__=='__main__':Path(sys.argv[2]).write_bytes(repack(Path(sys.argv[1]).read_bytes()))
