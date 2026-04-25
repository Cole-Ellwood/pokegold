# Project Map

This file is a fast index of canonical locations to edit.
Use it before searching broadly.

## Core source of truth

- `main.asm`: top-level assembly entry and includes.
- `engine/`: gameplay logic and systems (battle, events, overworld, menus).
- `data/`: gameplay data tables (pokemon, moves, trainers, maps, text, types).
- `maps/`: per-map scripts and map-specific logic.
- `constants/`: enum/constant definitions used across source.
- `home/`: shared low-level routines.
- `ram/`: memory layout definitions.
- `audio/`: music/sfx engine and data.
- `gfx/`: graphics assets and generated graphic intermediates.
- `macros/`: macro helpers used by asm sources.
- `tools/`: build tools and helper scripts.

## Build and verification

- `Makefile`: ROM build targets and cleanup targets.
- `INSTALL.md`: setup instructions.
- `docs/build.md`: build notes.
- `roms.sha1`: checksum verification targets.
- `scripts/find.ps1`: preset code search helper for common edit areas.

## Working directories (non-canonical for gameplay edits)

These paths contain analysis, copies, or temporary outputs and are excluded from default search:

- `audit/`
- `outbox/`
- `.local/`
- `dist/`
- `workspace/`

Legacy scratch trees are archived under:

- `workspace/scratch/review/`
- `workspace/scratch/type_passives_dropin/`

If you need files from these paths, search them explicitly.
