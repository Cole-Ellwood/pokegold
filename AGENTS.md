# Project Instructions

These instructions apply to the whole repository. Start here, then follow the
more detailed routing in `docs/README.md` before broad source search.

## Project Shape

This project is a custom Pokemon Gold/Silver ROM hack built on the
pret/pokegold disassembly, with Gold as the primary ROM; the design goal is for
a veteran player to feel like they are playing Pokemon for the first time again.

## Non-Negotiable Constraints

- Preserve the First-Playthrough Promise: a veteran player should feel like
  they are playing Pokemon for the first time again, not generic hard mode,
  competitive Gen 2, or modernization for its own sake.
- Bosses must win by legal, public-information reasoning; hidden-information
  cheating is forbidden except for explicitly authored once-per-battle Haki
  branches.
- Treat current source, linker outputs, and generated audits as source truth;
  hand-authored docs explain intent and workflow, not current byte reality.
- Do not hand-edit generated/build artifacts: `docs/generated/*.md`, `*.gbc`,
  `*.map`, `*.sym`, `*.o`, patches, saves, states, or scratch outputs.
- Respect save-format risk. Changes in `ram/` or SRAM/WRAM layout need explicit
  care because this repo has a `SAVE_FORMAT_VERSION` marker but no migration
  system.

## Commands

- Install/setup: read `INSTALL.md`; this Windows checkout usually builds
  through WSL with repo-local `rgbds-1.0.1/*.exe`. Check tools with
  `bash -lc 'command -v make && command -v python3'`.
- Run app: no app server. Build `pokegold.gbc`, then open it in a Game Boy
  Color emulator.
- Targeted tests: use the relevant audit from `tools/audit/`; for docs-only
  routing changes run `python tools\audit\check_navigation_floor.py`.
- Full tests: `python -m pytest tools` for Python tool tests when pytest is
  available; the project release floor is `python tools\audit\check_release_smoke.py`.
- Lint/typecheck/build: `git diff --check`, then
  `bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'`.

## Architecture Notes

- Main entry point: `main.asm`, with top-level includes flowing through
  `includes.asm`, `home.asm`, `audio.asm`, and `ram.asm`.
- Core modules: battle logic in `engine/battle/`, Boss AI in
  `engine/battle/ai/`, trainer data in `data/trainers/`, Pokemon stats and
  learnsets in `data/pokemon/`, maps/scripts in `maps/`, WRAM/SRAM definitions
  in `ram/`, helper tooling in `tools/`, and durable project docs in `docs/`.
- Data/storage/contracts: `*.map` and `*.sym` are linker truth after a build;
  `docs/generated/dev_index.md` mirrors source/linker state and must be
  regenerated, not edited; save/WRAM changes must preserve old-save alignment
  unless the user explicitly approves a migration/release plan.

## Local Rules

- Read order for ambiguous or gameplay-facing work starts at `docs/README.md`;
  for mechanics, balance, AI, moves, items, or stats, read
  `docs/agent_navigation/hack_mechanics_reference.md` and
  `docs/agent_navigation/gen2_vs_modern_mechanics.md` before making claims.
- Match local assembly style and banking patterns. Before writing `.asm`, read
  `docs/asm_authoring_guide.md`; farcall/register/bank mistakes are a known
  bug class in this project.
- Check `git status --short` before editing and leave unrelated dirty files
  alone. This repo often has many active work products in flight.
- Source changes need the narrowest relevant audit first, then broader release
  checks when risk warrants it. A build proves linking only, not gameplay feel.
- After any successful build whose linker outputs are kept, regenerate
  `docs/generated/dev_index.md` with `python scripts\generate_dev_index.py --rom pokegold`.
- Do not change ROM behavior, generated docs, build outputs, save/state files,
  or release artifacts during docs/navigation work unless the user explicitly
  asks for that scope.

## Definition of Done

- The requested behavior works, or the requested documentation exists where
  future sessions will naturally find it.
- Relevant tests/checks pass, or any inability to run them is explained with
  the exact command and blocker.
- The diff is narrow and does not alter unrelated behavior.
- Generated files are refreshed only when their source truth changed; otherwise
  they are deliberately left alone.
- Remaining gameplay, emulator, live-proof, or manual-playtest gaps are stated
  plainly instead of implied solved.
