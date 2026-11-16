from pathlib import Path

def apply(b):
 root=Path(__file__).parent
 def put(at,data):b[at:at+len(data)]=data
 code=(root/'desert_input_code.bin').read_bytes();assert b[0x100300:0x100300+len(code)]==b'\xff'*len(code);put(0x100300,code)
 for at,n,to,jsr in [(0x8e66,8,0x100300,False),(0x2eee,10,0x100340,True),(0x8ee8,6,0x100480,False),(0x6f18,6,0x1004c0,False)]:
  put(at,bytes.fromhex('4eb9' if jsr else '4ef9')+to.to_bytes(4,'big')+b'\x4e\x71'*((n-6)//2))
 # Temporary stock-layout options, extended with controller mode.
 end=b.index(b'\x00\x03\x12MUSIC:',0x52c)
 tab=bytearray(b[0x52c:end]);tab[1]=2
 tab+=b'\x00\x03\x13JOYSTICK:\0\0\x02\x62\0' + b'3 BUTTON\0\x02\x62\0' + b'6 BUTTON\0\xff'
 put(0x100600,tab)
 for at in [0x33e8,0x4894]:assert b[at:at+4]==bytes.fromhex('0000052c');put(at,(0x100600).to_bytes(4,'big'))
