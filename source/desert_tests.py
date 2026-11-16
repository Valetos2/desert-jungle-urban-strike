from pathlib import Path

def apply(b):
 root=Path(__file__).parent
 def put(at,data):b[at:at+len(data)]=data
 def jump(at,to):put(at,b'\x4e\xf9'+to.to_bytes(4,'big'))
 put(0x101000,(root/'desert_tests_code.bin').read_bytes())
 put(0x102000,(root/'desert_options.bin').read_bytes())
 put(0x103000,(root/'desert_sound_ids.bin').read_bytes())
 put(0x103100,(root/'desert_movie_entries.bin').read_bytes())
 put(0x102800,b'\x00\x0b\x00OPTIONS\0\x03\x01\x17B:PLAY C:STOP START:EXIT\0\xff')
 ptrs=[];pos=0x102940
 for i in range(7):
  idx=i if i<3 else (i-4 if i>=4 else 0)
  at=int.from_bytes(b[0x6aa+idx*4:0x6ae+idx*4],'big');end=b.index(255,at)+1
  row=bytearray(b[at:end]);row[2]=6;z=row.index(0);row[z+3]=7
  if i>=4:row=row.replace(b'and Jink',b'X: Jink ')
  ptrs.append(pos);put(pos,row);pos+=len(row)
 put(0x102900,b''.join(x.to_bytes(4,'big') for x in ptrs))
 jump(0x33a8,0x101000)
 jump(0x3740,0x101800);put(0x3746,b'\x4e\x71'*2)
 jump(0x4740,0x101840);put(0x4746,b'\x4e\x71')
 jump(0x4794,0x101900)


 jump(0xffa78,0x101b00);put(0xffa7e,b"\x4e\x71"*2)
 put(0x103180,bytes.fromhex("000008e400000000"))
