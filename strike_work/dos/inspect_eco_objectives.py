"""Extract Eco Threat's counters and script references from an unpacked DOS copy."""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def word(data, offset):
    return struct.unpack_from('<H', data, offset)[0]


def parse_commands(data, start):
    pos = start
    while data[pos:pos+2] != b'\0\0':
        opcode, size = data[pos:pos+2]
        if not size or pos + 2 + size > len(data):
            raise ValueError(f'Invalid command at {pos:#x}')
        yield opcode, data[pos+2:pos+2+size]
        pos += 2 + size


def build(root):
    exe = (root / 'EXECUTABLE').read_bytes()
    expected = 'fc477a04215ec3192334953cc1a05a7ec2a03285eebda7fef683a26797dc7e93'
    if hashlib.sha256(exe).hexdigest() != expected:
        raise ValueError('Unexpected Jungle Strike DOS executable')
    image = exe[16 * word(exe, 8):]
    ds = image[16 * word(image, 4):]
    level = (root / 'LEVELA').read_bytes()
    things = (root / 'THINGS').read_bytes()
    flic = (root / 'FLICDATA').read_bytes()
    level_index = 9

    descriptor = word(ds, 0xda80 + 2 * level_index)
    sectors = word(ds, descriptor)
    counters = list(struct.unpack_from('<8H', ds, word(ds, descriptor+0x28)))
    offsets = set()
    for i in range(sectors):
        start = word(level, i*2)
        if start:
            offsets.update(word(level, start + 2*j + 2) for j in range(word(level, start)))
    offsets = sorted(offsets)
    by_slot = {}
    for i, offset in enumerate(offsets, 1):
        address = word(level, offset + 30)
        assert (address-0xcb80) % 20 == 0
        by_slot[(address-0xcb80)//20] = i

    def references(payload):
        namespace, operation = payload[:2]
        if namespace == 0x02 and operation == 0x1a:
            objective, delta = struct.unpack('<Bb', payload[2:])
            return {'objective': objective, 'delta': delta}
        if namespace not in {0x06, 0x0a}:
            return None
        # These operations consume an extra immediate before their reference count.
        immediate = operation in {0x0e, 0x32, 0x36}
        count_at = 3 if immediate else 2
        count = payload[count_at]
        indices = list(payload[count_at+1:count_at+1+count])
        if namespace == 0x0a:
            return {'static_slots': indices, 'map_ids': [by_slot.get(i) for i in indices]}
        return {'dynamic_indices': indices}

    script_table = word(ds, descriptor + 0x2e)
    objective_links = {}
    for i in range(8):
        script = word(things, script_table + 2*i)
        links = []
        if script:
            # Objective streams end on a zero-length record. Unlike object
            # streams, opcode zero can precede a nonzero length.
            pos = script
            while things[pos+1]:
                gate, size = things[pos:pos+2]
                payload = things[pos+2:pos+2+size]
                ref = references(payload)
                if ref:
                    links.append({'threshold': gate, 'operation': f'{payload[:2].hex()}', **ref})
                pos += size+2
        objective_links[i+1] = links

    object_links = {}
    for map_id, offset in enumerate(offsets, 1):
        links = []
        for opcode, payload in parse_commands(level, offset+34):
            ref = references(payload)
            if ref:
                links.append({'event': opcode, 'operation': payload[:2].hex(), **ref})
        if links:
            object_links[map_id] = links

    event_table = word(ds, 0x35ca + 2 * level_index)
    message_table = word(ds, 0x27ff + 2 * level_index)
    events = []
    for i in range(word(ds, event_table) + 1):
        ptr = word(ds, event_table+2+2*i)
        group, flag, slot, kind, threshold, status, outcome = struct.unpack_from('<HBBBBHH', ds, ptr)
        msg = status or outcome
        assert 1 <= msg <= word(ds, message_table)
        route = word(ds, message_table + 2*msg)
        flic_id = word(ds, route+2) // 2
        label_id = word(ds, 0x39be+2*group)//2
        label = flic[word(flic, 2*label_id):].split(b'\0', 1)[0].decode()
        events.append({'event_record': ptr, 'group': group, 'label': label, 'event_kind': kind,
                       'threshold': threshold, 'status': status, 'outcome': outcome,
                       'counter_slot': slot, 'flag': flag, 'flicdata_index': flic_id})
    return {'objective_thresholds': counters, 'objective_links': objective_links,
            'object_links': object_links, 'message_events': events}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('resources', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.resources), indent=2))
