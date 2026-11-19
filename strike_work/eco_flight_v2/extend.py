"""Builder fragment: expand campaign tables without replacing original entries."""
# Every listed table has nine entries. Entry 9 is the new campaign, not a
# temporary alias written into one of those nine original slots.
tables={
 0x19292e:level,0x525b6:tiletab,
 0xe40e0:0x213a80,  # Snow Fortress departure scene
 0xe4074:0x240000,          # new pause overview
 0xe4098:ptr(0xe4098+5*4), # temporary mission diagram
 0xe40bc:ptr(0xe40bc+5*4), # temporary objective text
 0xe4104:ptr(0xe4104+5*4), # departure/completion sequence
 0xe4128:ptr(0xe4128+1*4), # player vehicle properties
 0xe6bbc:0,               # no stock intelligence-event table
 0xebf84:0x213c00,
 0x7e122:0,               # no stock fly-by script during play
 0x7e21e:0x213f00,         # campaign name in briefing
 0xe4022:ptr(0xe4022+5*4),
}
for i,(old,extra) in enumerate(tables.items()):
 assert ROM.read_bytes()[old:old+36]==original[old:old+36],hex(old)
 new=0x212000+i*0x80
 free(new,original[old:old+36]+struct.pack('>I',extra))
 needle=struct.pack('>I',old)
 # Relocate references in the executable, retaining all original table entries.
 for at in range(0x38000,0x48000,2):
  if b[at:at+4]==needle:l(at,new)
for i,old in enumerate([0xe4018,0xe406a]):
 new=0x213000+i*0x80;free(new,original[old:old+9]+original[old+5:old+6])
 needle=struct.pack('>I',old)
 for at in range(0x38000,0x48000,2):
  if b[at:at+4]==needle:l(at,new)
free(0x213f00,bytes.fromhex('001c08410002090a')+b'ECO THREAT\0\xff')
# Existing indices are zero-based: 0..8. Move the end sentinel to 10.
w(0x3d8f8,10)
l(0x3dcd4,40) # byte offset after ten pointer entries
w(0x3bb2c,9) # password after campaign 9, ending after campaign 10
w(0x3b00e,9)
w(0x3dc6a,9)
l(0x3a196,9) # campaign selection upper bound
# Per-sector resource masks from the donor map can unload the new ground.
# Give every sector its own copy, always requesting the new terrain tile set.
for sector in range(70):
 rec=bytearray(original[ptr(baselevel+0x60+sector*4):ptr(baselevel+0x60+sector*4)+16])
 struct.pack_into('>I',rec,12,0x200)
 free(0x214000+sector*16,rec)
 l(level+0x60+sector*4,0x214000+sector*16)
# New map resource: wrapper -> tile-set pointer -> raw tile graphics + palette.
# Same geometry and placement as the original map, with native word tile map.
wrapper=bytearray(original[ptr(0xe4074+4):ptr(0xe4074+4)+32])
struct.pack_into('>I',wrapper,6,0x240080)
struct.pack_into('>H',wrapper,0x10,2)
struct.pack_into('>I',wrapper,0x16,0x242000)
free(0x240000,wrapper);free(0x240080,struct.pack('>I',0x240100))
d=bytearray(original[ptr(ptr(ptr(0xe4074+4)+6)):ptr(ptr(ptr(0xe4074+4)+6))+46])
# Map graphics use the original resource allocation record and raw transfer.
# Dynamic allocator and its live record are preserved for release/restore.
d[1]=2
struct.pack_into('>I',d,0x1a,0x241000)
pat=(ROOT/'assets/pause_patterns.bin').read_bytes()
struct.pack_into('>H',d,0x22,len(pat));struct.pack_into('>H',d,0x24,2)
struct.pack_into('>I',d,0x26,len(pat));struct.pack_into('>I',d,0x2a,0x244000)
free(0x240100,d);free(0x241000,(ROOT/'assets/pause_palette.bin').read_bytes())
free(0x242000,(ROOT/'assets/pause_map.bin').read_bytes());free(0x244000,pat)

# One neutral free-flight entry; no donor objectives referencing absent objects.
free(0x213c00,struct.pack('>HII4B',1,0x213c40,0x213c80,0,0,1,0))
free(0x213c40,original[0xe9c6e:0xe9c6e+10])
free(0x213c80,b'\x01ECO THREAT\0')

# Only the Snow Fortress departure shot (aircraft over parked helicopter),
# without that campaign's preceding briefing/dialogue or its old caption.
scene=bytearray(original[0xe1e00:0xe1e00+34])
struct.pack_into('>I',scene,0x1a,0)
struct.pack_into('>H',scene,32,0xffff)
free(0x213a00,scene);free(0x213a80,struct.pack('>II',0x213a00,0))
free(0x213ac0,b'\x01\x07\x18MISSION 10: ECO THREAT\0\xff')
