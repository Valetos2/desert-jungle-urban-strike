from pathlib import Path

def apply(game,b):
 base,poll,skip={'jungle':(0x203400,0x3ea,0x3b8),'desert':(0x100100,0xfe392,0xfe360)}[game]
 code=(Path(__file__).parent/(game+'_ea_code.bin')).read_bytes()
 assert b[base:base+len(code)]==b'\xff'*len(code)
 assert b[poll:poll+8]==bytes.fromhex('13fc004000a10009')
 assert b[skip:skip+6]==bytes.fromhex('024000ff6614')
 b[base:base+len(code)]=code
 b[poll:poll+8]=b'\x4e\xf9'+base.to_bytes(4,'big')+b'\x4e\x71'
 b[skip:skip+6]=b'\x4e\xf9'+(base+0x80).to_bytes(4,'big')
