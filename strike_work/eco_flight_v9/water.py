"""Give the static water texture its own display color on palette line 1."""
import struct


def unpack_tiles(rom, source, size):
    """Decode $12 tiles, whose 16-bit mask selects changed words per tile."""
    count = struct.unpack_from('>H', rom, source)[0]
    assert 32*count == size
    cursor = source+2
    words = [0]*16
    out = bytearray()
    for _ in range(count):
        flags = struct.unpack_from('>H', rom, cursor)[0]
        cursor += 2
        for i in range(16):
            if flags & (1 << i):
                words[i] = struct.unpack_from('>H', rom, cursor)[0]
                cursor += 2
        out.extend(struct.pack('>16H', *words))
    return out


def restore_static_lines(rom, original_terrain, recolor, sectors, free):
    def word(at):
        return struct.unpack_from('>H', rom, at)[0]

    def long(at):
        return struct.unpack_from('>I', rom, at)[0]

    # Slot E was used by two Snow Fortress graphics. Change those specific
    # opaque tile nibbles to the near-white already at 1/2 ($0ccc vs $0cca).
    slot, white = 14, 2
    bank_offset = 14*4
    bank = long(0x210100+bank_offset)
    assert word(bank+36) == 0x12
    raw = unpack_tiles(rom, long(bank+42), word(bank+34))
    gfx = {long(p) for group in sectors for p in group}
    gfx.update(long(p-16) for group in sectors for p in group if rom[p+22]&4)
    use = {1: set(), 0: set(), 2: set(), 3: set()}
    for obj in gfx:
        if not 0 < obj < len(rom)-32 or word(obj+4) != bank_offset:
            continue
        source, attrs = long(obj+22), word(obj+30)
        for i in range(word(obj)*word(obj+2)):
            if word(obj+16) == 2:
                attr = word(source+2*i) + attrs
            else:
                value = rom[source+2+i]
                if not value:
                    continue
                attr = (value&63) + ((value&192)<<5) + word(source) + attrs
            tile = attr & 2047
            assert tile*32 < len(raw), (hex(obj), tile)
            use[(attr>>13)&3].add(tile)
    affected = set()
    for tile in use[1]:
        pixels = raw[tile*32:tile*32+32]
        if any(slot in (p>>4,p&15) for p in pixels):
            affected.add(tile)
    assert affected and not affected.intersection(use[0] | use[2] | use[3])
    for tile in affected:
        for i in range(tile*32, tile*32+32):
            hi, lo = raw[i]>>4, raw[i]&15
            raw[i] = ((white if hi==slot else hi)<<4) | (white if lo==slot else lo)

    descriptor = bytearray(rom[bank:bank+46])
    struct.pack_into('>HII', descriptor, 36, 2, len(raw), 0x27c040)
    free(0x27c000, descriptor)
    free(0x27c040, raw)
    struct.pack_into('>I', rom, 0x210100+bank_offset, 0x27c000)
    assert word(0x210420+2*slot) == 0x0cca
    struct.pack_into('>H', rom, 0x210420+2*slot, 0x0640)

    patterns, terrain = recolor(rom, original_terrain, static_water_index=slot)
    rom[0x220000:0x220000+len(patterns)] = patterns
    struct.pack_into('>H', rom, 0x210022, len(patterns))
    struct.pack_into('>I', rom, 0x210026, len(patterns))
    rom[0x300000:0x300000+len(terrain)] = terrain
    return len(patterns)//32
