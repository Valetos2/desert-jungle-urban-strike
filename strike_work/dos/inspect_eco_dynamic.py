"""Export Eco Threat dynamic object definitions from the unpacked DOS resources."""
import argparse
import csv
import hashlib
import struct
import sys
from pathlib import Path

from inspect_eco_objectives import word


def definitions(root):
    exe = (root / "EXECUTABLE").read_bytes()
    level = (root / "LEVELA").read_bytes()
    for name, data, expected in (
        ("EXECUTABLE", exe, "fc477a04215ec3192334953cc1a05a7ec2a03285eebda7fef683a26797dc7e93"),
        ("LEVELA", level, "942ce5a037ceb034ca16af09fb76c665b00579100c8260fbf8e958c157d5740c"),
    ):
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f"Unexpected Jungle Strike DOS {name}")

    image = exe[16 * word(exe, 8):]
    ds = image[16 * word(image, 4):]
    descriptor = word(ds, 0xda80 + 2 * 9)
    slots = word(ds, descriptor + 0x32)
    # Index 194 is the highest initialized slot. C490's sector walk uses
    # LEVELA:1326 (set by C32D), with 70 entries from the descriptor.
    indices = {0xc810 + word(ds, slots + 2*i): i for i in range(195)}
    records = {}
    for sector in range(word(ds, descriptor)):
        sector_list = word(level, 0x1326 + 2*sector)
        if not sector_list:
            continue
        for entry in range(word(level, sector_list)):
            offset = word(level, sector_list + 2 + 2*entry)
            slot = word(level, offset + 8)
            index = indices[slot]
            if index in records:
                raise ValueError(f"Duplicate dynamic slot {slot:#x}")
            type_id = word(level, offset)
            position_c, position_e, height = struct.unpack_from("<HHh", level, offset + 0xc)
            records[index] = {
                "index": index,
                "sector": sector,
                "level_offset": f"0x{offset:04x}",
                "live_slot": f"0x{slot:04x}",
                "type_ds": f"0x{type_id:04x}",
                "group": word(ds, type_id + 6),
                "position_word_c": position_c,
                "position_word_e": position_e,
                "height": height,
                "flags_14_15_16": level[offset+0x14:offset+0x17].hex(),
                "script_offset": f"0x{offset+0x1a:04x}" if level[offset+0x1a] else "",
            }
    if set(indices.values()) - records.keys() != {174}:
        raise ValueError("Unexpected dynamic slot coverage")
    return [records[index] for index in sorted(records)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("resources", type=Path)
    rows = definitions(parser.parse_args().resources)
    writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
