# Project workflow

- User: Valentin “Valet2” Kozin. Communicate in Russian unless asked otherwise.
- `main` contains user-accepted fixes. `wip` contains research and experimental changes.
- Commit and push each coherent change to `wip` during active work. Record known failures and unfinished work honestly. Do not silently leave local-only changes.
- Promote tested fixes to `main` when authorized; preserve experimental work on `wip`.
- Never commit original or patched game ROMs, CD images, DOS executables/DAT archives, extracted game graphics/audio, save states, or archives containing them. Deliver ROMs privately in chat only. Publish IPS against hash-verified original ROMs.
- Small existing `source/*.bin` files are patch payloads/menu fragments, not ROMs; allowed for reproducibility. Review any new binary explicitly before staging.
- Keep findings, source, build scripts, patch hashes and validation results. Preserve uncertainty in reverse-engineering notes.
- Do not commit full disassemblies of original games or external tool repositories.
- Prefer explicit file staging. Check the staged paths and binary sizes before every push. Never force-push over user changes.
- Original hashes and output hashes: tests/release_manifest.json. Stable baseline: Checkpoint12 (Desert v04, Jungle v05, Urban v09).
- DOS research is on wip. No bonus mission import is complete yet.
