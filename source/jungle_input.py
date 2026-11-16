"""Apply Jungle controls/menu on top of the pickup-autoaim patch."""
from pathlib import Path
import json
def apply(b):
 root=Path(__file__).parent
 code=(root/'jungle_input_code.bin').read_bytes()
 assert b[0x1ff500:0x1ff500+len(code)]==b'\xff'*len(code)
 b[0x1ff500:0x1ff500+len(code)]=code
 for p in json.loads((root/'jungle_input_patches.json').read_text()):
  at=p['offset'];old=bytes.fromhex(p['expected']);new=bytes.fromhex(p['data'])
  assert b[at:at+len(old)]==old,hex(at)
  b[at:at+len(old)]=new
