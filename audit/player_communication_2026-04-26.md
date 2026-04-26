# Player Communication Capsule - 2026-04-26

Lane: player communication.

Purpose: move core fair-hard rules from implicit surprise into an early,
optional, in-world teaching surface.

## Change

Updated `maps/EarlsPokemonAcademy.asm` so the Academy notebook now teaches:

- Johto League trainer battles use Set-style rules.
- Trainer battles do not allow Pack breaks.
- Gym Leaders remember public/revealed moves rather than reading hidden party
  information.
- Type habits are stronger, with examples for Poison contact punishment, Grass
  between-turn healing, and Dragon matchup pressure.
- Held items matter more; some boost stats but lock moves; item text should be
  read before a Gym.

Added a regression guard in `tools/audit/check_release_smoke.py` under the
existing QoL communication text checks.

## Verification Results

- `python tools\audit\check_release_smoke.py` passed immediately after the text
  and audit guard changed.
- WSL normal build passed for both ROMs:
  `bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'`.
- The build relinked map data and wrote fresh `pokegold.map`,
  `pokegold.sym`, `pokesilver.map`, and `pokesilver.sym`.
- `python scripts\generate_dev_index.py --rom pokegold` refreshed
  `docs/generated/dev_index.md` from the new linker outputs.
- Final `python tools\audit\check_release_smoke.py` passed.
- Final `python tools\audit\check_docs_navigation.py` passed, including the
  generated dev index match.
- Final `git diff --check` reported no whitespace errors. It repeated the
  pre-existing CRLF warning for `audit/boss_ai_trace/morty_live.txt`.

## Remaining Verification

- Manual emulator text rendering was not performed during the source edit.
