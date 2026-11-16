"""Compare the variable-length commands attached to DOS and Genesis objects."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OPCODES = {0x02, 0x0E, 0x12, 0x16}
DOS_SLOT_BASE = 0xCB80
MD_SLOT_BASE = 0xFF391E


def read_commands(data, offset, limit):
    commands = []
    pos = offset + 34
    while pos + 2 <= limit:
        opcode, size = data[pos:pos + 2]
        if (opcode, size) == (0, 0):
            return commands
        end = pos + 2 + size
        if opcode not in OPCODES or not size or end > limit:
            break
        commands.append((opcode, data[pos + 2:end]))
        pos = end
    raise ValueError(f"Invalid command sequence at {offset:#x}, command at {pos:#x}")


def padded(commands):
    return [(opcode, data + b"\0" * (len(data) % 2))
            for opcode, data in commands]


def compare(resources, original):
    rom = original.read_bytes()
    expected = 'ea4eb94f7b3ecc1815ab2ac5adbd901b0e3a97a69ee2a31ead27600f12b1483a'
    if hashlib.sha256(rom).hexdigest() != expected:
        raise ValueError("Unexpected Genesis ROM")
    positions = json.loads((ROOT / 'object_correspondence.json').read_text())
    tails = json.loads((ROOT / 'level_resources.json').read_text())['levels']
    names = json.loads((ROOT / 'object_resources.json').read_text())['A']['objects']
    name_by_offset = {row['object_offset']: row['resource'] for row in names}
    report = {}
    for level, info in positions.items():
        data = (resources / ('LEVEL' + level)).read_bytes()
        counts = Counter()
        opcodes = Counter()
        command_objects = []
        rows = info['objects'] if level == 'A' else info['matches']
        limit = tails[level]['tail_offset']
        for row in rows:
            offset = row['offset'] if level == 'A' else row['dos_offset']
            commands = read_commands(data, offset, limit)
            slot_address = int.from_bytes(data[offset + 30:offset + 34], 'little')
            if slot_address >> 16 != 0x1A7E:
                raise ValueError(f'Unexpected DOS segment in LEVEL{level}+{offset:#x}')
            relative_slot = (slot_address & 0xFFFF) - DOS_SLOT_BASE
            if relative_slot < 0 or relative_slot % 20:
                raise ValueError(f'Unexpected DOS slot in LEVEL{level}+{offset:#x}')
            slot = relative_slot // 20
            opcodes.update(f'{opcode:02X}' for opcode, _ in commands)
            counts['parsed'] += 1
            counts['with_commands'] += bool(commands)
            if level == 'A' and commands:
                command_objects.append({
                    'offset': offset, 'resource': name_by_offset[offset], 'slot': slot,
                    'commands': [{'opcode': f'{op:02X}', 'payload_size': len(payload),
                                  'prefix': payload[:2].hex()}
                                 for op, payload in commands],
                })
            candidates = row.get('genesis_candidates', [])
            if len(candidates) != 1:
                continue
            md = candidates[0]
            counts['genesis_pairs'] += 1
            counts['matching_slot'] += (
                int.from_bytes(rom[md + 30:md + 34], 'big') == MD_SLOT_BASE + 30 * slot)
            counts['matching_flags'] += (
                data[offset + 12:offset + 16] == rom[md + 12:md + 16][::-1])
            try:
                md_commands = read_commands(rom, md, min(md + 1024, len(rom)))
            except ValueError:
                counts['genesis_unparsed'] += 1
                continue
            counts['identical_commands'] += md_commands == commands
            counts['matching_with_padding'] += md_commands == padded(commands)
        report[level] = {'counts': dict(counts), 'opcodes': dict(opcodes)}
        if level == 'A':
            report[level]['objects_with_commands'] = command_objects
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=ROOT / 'unpacked/jungle')
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / 'object_commands.json')
    args = parser.parse_args()
    report = compare(args.input, args.rom)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    for level, entry in report.items():
        print(level, entry['counts'], entry['opcodes'])
