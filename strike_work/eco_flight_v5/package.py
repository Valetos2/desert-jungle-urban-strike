"""Create an IPS against the clean original and verify exact reconstruction."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parent
old=Path('strikehd/rom/jungle_strike.bin').read_bytes()
rom=ROOT/'Jungle_Strike_Eco_Threat_Flight_TEST_v5.bin'
new=rom.read_bytes()
patch=bytearray(b'PATCH');i=0
while i<len(new):
    if i<len(old) and old[i]==new[i]:
        i+=1;continue
    end=i+1
    while end<min(i+65535,len(new)) and (end>=len(old) or old[end]!=new[end]):end+=1
    # Split runs for compact RLE; especially the unused expanded ROM space.
    j=i
    while j<end:
        run=j+1
        while run<end and new[run]==new[j]:run+=1
        if run-j>=8:
            patch.extend(j.to_bytes(3,'big')+b'\0\0'+(run-j).to_bytes(2,'big')+new[j:j+1]);j=run
        else:
            start=j;j=run
            while j<end:
                r=j+1
                while r<end and new[r]==new[j]:r+=1
                if r-j>=8:break
                j=r
            patch.extend(start.to_bytes(3,'big')+(j-start).to_bytes(2,'big')+new[start:j])
    i=end
patch.extend(b'EOF')
out=bytearray(old);p=5
while patch[p:p+3]!=b'EOF':
    at=int.from_bytes(patch[p:p+3],'big');n=int.from_bytes(patch[p+3:p+5],'big');p+=5
    if n:chunk=patch[p:p+n];p+=n
    else:
        n=int.from_bytes(patch[p:p+2],'big');chunk=patch[p+2:p+3]*n;p+=3
    if at+n>len(out):out.extend(b'\0'*(at+n-len(out)))
    out[at:at+n]=chunk
assert bytes(out)==new
assert len(new)==0x400000
assert int.from_bytes(new[0x1a4:0x1a8],'big')==0x3fffff
assert int.from_bytes(new[0x18e:0x190],'big')==sum(int.from_bytes(new[i:i+2],'big') for i in range(0x200,len(new),2))&65535
ips=rom.with_suffix('.ips');ips.write_bytes(patch)
r=json.loads((ROOT/'build_report.json').read_text());r.update(ips_bytes=len(patch),ips_sha256=hashlib.sha256(patch).hexdigest(),ips_roundtrip=True)
(ROOT/'build_report.json').write_text(json.dumps(r,indent=2)+'\n')
with zipfile.ZipFile(rom.with_suffix('.zip'),'w',zipfile.ZIP_DEFLATED) as z:
    for path in [rom,ips,ROOT/'README_RU.md',ROOT/'build_report.json']:
        z.write(path,path.name)
print(json.dumps(r,indent=2))
