from pathlib import Path

def apply(b):
 code=Path(__file__).with_name('urban_controls_code.bin').read_bytes()
 assert b[0x1ff600:0x1ff600+len(code)]==b'\xff'*len(code)
 b[0x1ff600:0x1ff600+len(code)]=code
 for at,old,to in [(0x9cb2,'4ab900ff10b466000016',0x1ff600),(0x65b8,'343900ff1024',0x1ff640)]:
  expected=bytes.fromhex(old);assert b[at:at+len(expected)]==expected,(hex(at),b[at:at+len(expected)].hex())
  b[at:at+len(expected)]=b'\x4e\xf9'+to.to_bytes(4,'big')+b'\x4e\x71'*((len(expected)-6)//2)

 b[0x1ff368:0x1ff372]=bytes.fromhex('4ef9001ff6c04e714e71')
 for at in [0x1d1a,0x1ece]:b[at:at+6]=bytes.fromhex('4eb9001ff700')
 ptrs=[];pos=0x1ff120
 for i in range(7):
  idx=i if i<3 else (i-4 if i>=4 else 0)
  at=int.from_bytes(b[0x7ce66+idx*4:0x7ce6a+idx*4],'big')
  if i<4:ptrs.append(at);continue
  end=b.index(255,at)+1;row=b[at:end].replace(b'and Jink',b'X: Jink ').replace(b'AND JINK',b'X: JINK ')
  ptrs.append(pos);b[pos:pos+len(row)]=row;pos+=len(row)
 assert pos<=0x1ff200,hex(pos)
 b[0x1ff100:0x1ff11c]=b''.join(x.to_bytes(4,'big') for x in ptrs)
 for at in [0x1d16,0x1ef2]:b[at:at+4]=(0x1ff100).to_bytes(4,'big')
