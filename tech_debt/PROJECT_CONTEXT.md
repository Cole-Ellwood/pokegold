# Project context — for tech debt work

This file is a tech-debt-focused supplement. The project's full source of
truth is the repo's top-level `CLAUDE.md` (auto-loaded in Claude Code
sessions). Read this file if you need a portable summary or you're acting
outside that context.

## What the hack is

A Pokémon Gold/Silver ROM hack built on the pret/pokegold disassembly.
`pokegold` = Gold (primary build target), `pokesilver` = Silver.

Design themes (these scope what changes are in-scope):
- **Boss AI overlay** — human-like trainer decision-making, no
  hidden-information cheating outside authored "Haki" exceptions. Lives in
  `engine/battle/ai/`. State in WRAMX bank 1 with a fixed reserve budget.
- **Progression-based pacing** — EXP scaling and wild encounter levels are
  tied to a single `GetProgressionLevelCap` source of truth.
- **Late-gen mechanics** — Choice items, Assault Vest, 3-layer Spikes,
  Imposter, type-passive damage modifiers.
- **Rebalanced base stats / movesets / trainer rosters.**

The deep design goal is **restored uncertainty** for veteran players — not
generic difficulty, not modernization, not competitive Gen 2. Tech debt
fixes that hurt feel are not net wins. See `docs/project_context.md` and
`docs/balance_intent.md` for the full statement.

## Where the code lives

| Subsystem | Path |
|-----------|------|
| Boss AI | `engine/battle/ai/boss.asm` (largest single file in the project) |
| Late-gen held items | `engine/battle/late_gen_held_items.asm` |
| Type passive damage mods | `engine/battle/type_passive_damage_mods.asm` |
| EXP scaling / progression cap | `engine/pokemon/experience.asm` |
| Wild encounter levels | `engine/overworld/wildmons.asm` |
| Save / SRAM | `engine/menus/save.asm`, `ram/sram.asm` |
| WRAM / WRAMX | `ram/wram.asm` (bank-switched bank 1 holds boss AI) |
| HRAM | `ram/hram.asm` |
| Pokémon base stats | `data/pokemon/base_stats/<species>.asm` (one file per species) |
| Moves | `data/moves/moves.asm` (single file with inline `move` macros) |
| Evolutions / level-up | `data/pokemon/evos_attacks.asm` (inline labels) |
| Trainer parties | `data/trainers/parties.asm` |
| Trainer AI tiers | `data/trainers/ai_tiers.asm` |
| Trainer attributes | `data/trainers/attributes.asm` |
| Constants | `constants/` |
| ROM bank layout | `layout.link` |
| Generated docs | `docs/generated/dev_index.md`, `docs/generated/balance_audit.md` |
| Audit scripts | `tools/audit/` |
| Build scripts | `scripts/` |
| Doc-driven nav | `docs/agent_navigation/`, `docs/project_map.md` |

Quirks:
- **`BaseData` chains one `INCLUDE` per species.** Adding a Pokémon usually
  touches a constant, the master table, and any pointer table that indexes
  it.
- **`INCLUDE "..."` paths are case-sensitive** even on Windows hosts.

## Build

Native Windows `make` is not on PATH. Use WSL with explicit RGBDS .exe paths:

```bash
wsl -e bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc'
```

`PYTHON=python3` required (no `python` symlink in this WSL Ubuntu).

A green build only proves "it links." ROM **identity** is verified by SHA1
(`make compare`, against `roms.sha1`).

## Verification floor (the audit suite)

Run from `tools/audit/` before reporting any non-trivial work as done. These
are the gates a finding must pass before being marked `done:` in
`AGENT_LOG.md`.

| Audit | Purpose | When required |
|-------|---------|---------------|
| `check_release_smoke.py` | Broad release sanity; stale labels, structure | Always |
| `check_farcall_hl_clobber.py` | farcall hl-input bug class | Any farcall edit |
| `check_navigation_floor.py` | docs/dev_index integrity | Any doc/structure change |
| `check_boss_ai_no_cheat.py` | Boss AI doesn't read hidden info | Any boss AI edit |
| `check_boss_ai_trace_invariants.py` | Boss AI trace contract | Any boss AI edit |
| `check_boss_ai_memory_budget.py` | WRAMX bank 1 reserve | Any WRAMX bank 1 edit |
| `check_battle_math_safety.py` | Numerical safety | Battle math edits |
| `check_save_format_version.py` | Save state compat | SRAM/save edits |
| `check_workspace_hygiene.py` | File organization | Always |

After **any** successful build that links, regenerate the dev index:

```bash
python scripts/generate_dev_index.py --rom pokegold
```

Audits read bank/free-space figures from `docs/generated/dev_index.md`.
Skipping the regen produces phantom audit failures.

For balance/stat/evolution/level-up/TM data changes also regenerate:

```bash
python scripts/generate_balance_audit.py
```

## Critical gotchas (the ones that have cost real time)

These have cost real debugging sessions. Read before touching the relevant
area.

### `farcall` hl-clobber (April 2026 one-shot damage bug, May 2026 Rival 1 softlock)
`farcall TARGET` expands to `ld hl, TARGET; ld a, BANK(TARGET); rst FarCall`.
Caller's `hl` is destroyed **before** the target runs. Three patterns:
- Push/pop `hl` if `hl` just needs preserving across the call.
- ROM0 thunk via `homecall` if target needs `hl` as input/output.
- Pass via `bc`/`de` and reconstruct inside.

Audit: `tools/audit/check_farcall_hl_clobber.py`.

### `farcall` does NOT preserve target's `a` (May 2026 wild-level no-op bug)
After `farcall`, caller's `a` = target's exit `c`, **not** target's `a`
(see `home/farcall.asm:13-28` — the trailing `ld a, [wFarCallBC + 1]; ld c, a; ret`
clobbers `a`). For a-return cross-bank functions, mirror to `c` at every
`ret` in the target (`ld c, a; ret`), or return via HRAM, or use a HOME
thunk. Spot-check by reading the target's exit `c`. Not currently audited.

### `Label:` vs `Label::`
Single colon = file-local. Double colon = exported across banks. Don't
silently downgrade `::` to `:` — cross-bank refs fail to link with
confusing errors.

### Plain `call` cannot cross banks
`call` only reaches the current bank or ROM0. Calling a `::` label in
another bank with `call` will assemble but jump to garbage at runtime.
Use `farcall` (or `callfar`).

### ROM banks are $4000 bytes (16 KiB)
Growth past free space is a link-time failure with often-unhelpful errors.
Check the `Tight Banks` table in `docs/generated/dev_index.md` before
adding bytes. Several banks are at 0-6 bytes free as of 2026-05-02 — see
TD-001 in the report.

### `assert` lines in tables/macros
Catch bounds at link time. **Don't delete them to make the build pass.**
Fix the underlying mismatch.

### Stat math: computed vs base
Battle uses the **computed** stat. Stat-stage multipliers act on the
computed value, not base.
- Computed (non-HP): `floor((2*base + IV + EV/4) * level / 100) + 5`
- Computed HP: same `+ level + 10`
- IV 0..15, EV 0..65535 per stat.
- `wEnemySpdLevel` etc. uses base-7 encoding: `BASE_STAT_LEVEL = 7 = +0`,
  `MAX_STAT_LEVEL = 13 = +6`. **Don't read the byte as the multiplier.**
- A low-base mon at +N can be faster/stronger than a high-base mon at +0.

### RAM and save format
- `ram/` is high-caution. WRAM/SRAM offsets are part of the save format.
  Reordering or resizing fields silently misaligns existing saves.
- There is a `SAVE_FORMAT_VERSION` marker but **no migration code**.
- Save-format changes shipping to public release are an escalation item.

### Bank switching
- WRAMX is bank-switched. Boss AI state lives in WRAMX bank 1 with a
  fixed reserve budget — `Boss AI WRAM Reserve` in
  `docs/generated/dev_index.md`.
- `hROMBank` (HRAM) shadows the current ROM bank. Use the bank-switch
  helpers; bypassing them desyncs the shadow and breaks subsequent
  `farcall`s.

## Don't hand-edit these

Generated by build/scripts — fix the source or generator and rebuild:
- `docs/generated/*.md`
- `dist/` (`*.bps`, `checksums.txt`)
- `*.gbc`, `*.map`, `*.sym`, `*.o`
- `pokegold.gbc.apr26-backup`, anything in `.local/` or `workspace/`

## Authority for tech-debt agents

Per `CLAUDE.md`, technical decisions are delegated. You can drive audits,
git, doc edits, and asm refactors without asking. Escalate only:
- Gameplay taste decisions (stats, movesets, types, rosters, encounter
  rates, dialogue).
- Save-format changes shipping to public release.
- Merging to master.
- Truly destructive irreversible actions (force-push to master,
  `rm -rf` outside scratch, deleting branches with unmerged work).

The user is the gameplay-design lead and playtest seat. He does **not**
code. State technical conclusions plainly; don't hedge.
