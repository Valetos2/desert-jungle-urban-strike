# Desert / Jungle / Urban Strike improvements

ROM hacks and quality-of-life improvements for Sega Genesis / Mega Drive.
Project by Valentin “Valet2” Kozin, developed and tested with ChatGPT assistance.

## Stable patches / Проверенные патчи

`main` contains the user-tested Checkpoint 12 builds. Apply **one IPS to the matching original, unmodified ROM**, never over an earlier patch. ROMs and original game data are not distributed here.

| Game | Patch | Original edition |
|---|---|---|
| Desert Strike | [v04 Menu Fixes](patches/Desert_Strike_v04_Menu_Fixes.ips) | Return to the Gulf (U) [!] |
| Jungle Strike | [v05 Menu Polish](patches/Jungle_Strike_v05_Menu_Polish.ips) | (W), Apr 1993 [!] |
| Urban Strike | [v09 Menu Music](patches/Urban_Strike_v09_Menu_Music.ips) | (W) [!] |

Exact input/output SHA-256 hashes: [release manifest](tests/release_manifest.json). Start the patched game from reset; old emulator save states may carry incompatible state.

Изменения включают определение шестикнопочного контроллера, стрейф на X/Mode, запуск Hellfire по нажатию в шестикнопочном режиме, защиту подбираемых объектов от автоприцеливания, Sound/Movie Test, циклическое меню и исправления возврата из заставок. В Urban устранены обнаруженные паузы музыки при переходах. Это не неуязвимость подбираемых объектов: случайный огонь по-прежнему может их уничтожить.

Подробности последней сборки и проверки: [русское описание](docs/CHECKPOINT12_RU.md). Свойства ко-пилотов: [COPILOTS_RU](docs/COPILOTS_RU.md). Таблицы Sound/Movie Test находятся в `docs/`.

## Build

Python 3, no third-party modules needed for the stable build:

```sh
python source/build_autoaim.py jungle /path/to/original.bin /path/to/local-output
```

Replace `jungle` with `desert` or `urban`. The builder verifies the original ROM hash and emits the patched ROM plus IPS. `source/*.bin` are small patch payloads and menu fragments, **not game ROMs**. They are supplied so the build does not require an assembler. ASM sources can be assembled with vasm (`-Fbin -m68000 -no-opt`, working directory `source`).

Published IPS files use standard IPS RLE compression for long fill areas. To reproduce the exact published IPS after building:

```sh
python tools/repack_ips.py /path/to/local-output/Jungle_Strike_v05_Menu_Polish.ips /path/to/compact.ips
```

Compact IPS files produce byte-identical ROMs to Checkpoint 12; only patch packaging changed. The original checkpoint manifest retains the old, uncompressed IPS hashes. `tests/release_manifest.json` identifies the published versions.

## Development

`main`: accepted stable changes. `wip`: ongoing research and experimental modifications, committed and pushed after each coherent change. DOS bonus missions are **not implemented** in these stable patches.

Local ROMs, CD images, extracted game assets, emulator saves and build outputs must stay outside Git history. See [AGENTS.md](AGENTS.md). The game code, graphics and audio belong to their respective rights holders; this unofficial project is not affiliated with Electronic Arts. No license to the original games is granted.
