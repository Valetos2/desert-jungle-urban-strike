"""Jungle Sound/Movie menu. Applied after jungle_input, before ROM checksums."""
from pathlib import Path

def apply(b):
 root=Path(__file__).parent
 b.extend(b'\xff'*(0x400000-len(b)))
 b[0x1a4:0x1a8]=(len(b)-1).to_bytes(4,'big')
 def put(at,data):b[at:at+len(data)]=data
 def jump(at,to):put(at,b'\x4e\xf9'+to.to_bytes(4,'big'))
 put(0x200000,(root/'jungle_tests_code.bin').read_bytes())
 put(0x202000,(root/'jungle_options.bin').read_bytes())
 put(0x203000,(root/'jungle_sound_ids.bin').read_bytes())
 put(0x203100,(root/'jungle_movie_entries.bin').read_bytes())
 put(0x203300,bytes.fromhex("000c0dba00000000000c0e2a00000000"))
 # Small title and a single footer keep original row spacing.
 put(0x202800,b'\x00\x10\x02OPTIONS\0\x03\x03\x1bB:PLAY C:STOP START:EXIT\0\xff')
 # Reuse the original help text, with the existing mode-aware X hint.
 ptrs=[];pos=0x202940
 for i in range(7):
  at=int.from_bytes(b[0x1ff780+i*4:0x1ff784+i*4],'big');end=b.index(255,at)+1
  row=bytearray(b[at:end]);row[2]=8;z=row.index(0);row[z+3]=9
  ptrs.append(pos);put(pos,row);pos+=len(row)
 put(0x202900,b''.join(x.to_bytes(4,'big') for x in ptrs))
 assert b[0x39070:0x39074]==bytes.fromhex('48e73030')
 jump(0x39070,0x200000)
 # Background builder can also return to Movie Test without drawing the main menu.
 jump(0x39312,0x200800);put(0x39318,b'\x4e\x71'*2)
 # Original BSR.W renderer plus BRA.W continuation displaced together.
 jump(0x39ff6,0x200840);put(0x39ffc,b'\x4e\x71')

 jump(0x3a04a,0x200900)
