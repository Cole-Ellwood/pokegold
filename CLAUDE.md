# CLAUDE.md

## What this project is

Pokémon Gold/Silver ROM hack built on top of the pret/pokegold disassembly.
`pokegold` = Gold ROM (primary), `pokesilver` = Silver. The user is the
gameplay-design lead and the playtest seat; he does not code. All technical
work — architecture, asm, banking, audits, git, releases — is delegated to
you. He runs Claude from both CLI and the desktop app, so context portability
matters; this file is the single source of truth that auto-loads.

The hack's design themes (these scope what changes are in-scope):
- **Boss AI overlay** for trainer fights — human-like decision-making, no
  hidden-information cheating outside authored "Haki." Lives in
  `engine/battle/ai/`, uses WRAMX bank 1 with a budget.
- **Progression-based pacing** — EXP scaling and wild level spread are tied
  to a single `GetProgressionLevelCap` (`engine/pokemon/experience.asm`).
- **Late-gen mechanics** — Choice items, Assault Vest, 3-layer Spikes,
  Ditto Imposter, type-passive damage mods. Lives in
  `engine/battle/late_gen_held_items.asm`,
  `engine/battle/type_passive_damage_mods.asm`.
- **Rebalanced base stats / movesets / trainer rosters** — see
  `docs/balance_intent.md`, `docs/buff_backlog.md`.

Source orientation, not this file: `docs/README.md`, `docs/project_map.md`,
`docs/agent_navigation/source_output_ownership.md`.

## Read this before any mechanics decision

This project is Gen 2. Modern Pokemon mechanics (per-move phys/special
split, abilities, natures, Fairy type, Gen 4+ moves, modern items) are NOT
the rules here. Before proposing or evaluating any mechanics, balance, AI,
moveset, item, or stat decision, read:

- `docs/agent_navigation/gen2_vs_modern_mechanics.md`

It is the single source of truth for "is this how Gen 2 / this hack
actually works, or am I leaking modern Pokemon priors?" If something in
that doc is wrong, fix the doc — do not work around it.

## North Star: First-Playthrough Promise

The hack exists to make Pokémon Gold feel unknown and dangerous again for a
veteran player. **Not** generic hard mode. **Not** competitive Gen 2. **Not**
modernization for its own sake. The deep goal is *restored uncertainty*.

Test before approving any gameplay change: does it help a knowledgeable
player feel discovery, danger, and respect for the world again? If it only
makes the ROM harder, cleaner, faster, or more modern without serving that
feeling, it is not automatically aligned.

Concrete corollaries:
- **Bosses win without cheating.** No hidden-info reads (unrevealed party,
  unrevealed moves, private stats, current-turn input, RNG manipulation).
  Public info only: seen species, revealed moves, public TM/level-up
  learnability. Haki = explicitly authored once-per-battle exceptions only.
- **Old tier-list knowledge should stop being complete.** Forgotten/strange
  Pokémon should make the player hesitate and ask "could this actually
  work?" Buffs give distinct roles, not flat stat bumps.
- **QoL removes tedium, never decisions.** Never trivializes boss prep,
  resource tension, or team-building stakes.
- **Stay Gen 2 in texture.** If a modern behavior helps but damages feel,
  adapt rather than copy.
- **Difficulty comes from smarter opponents, better teams, meaningful
  mechanics.** Not from forced grinding or cheap surprises.

Full statement: `docs/project_context.md`. Balance corollary:
`docs/balance_intent.md`. Roadmap of active workstreams:
`docs/project_roadmap.md`.

## Build & verification

Native Windows `make` is not on PATH. Build through WSL with explicit
Windows RGBDS `.exe` binaries:

```bash
wsl -e bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc'
```

`PYTHON=python3` is required (WSL Ubuntu has no `python` symlink). A green
build only proves "it links." ROM identity is verified by SHA1
(`roms.sha1`, `tools/verify_sha1.py`, `make compare`).

For non-trivial changes, run relevant scripts in `tools/audit/` before
reporting work done. The verification floor, not optional. The most useful:
- `check_release_smoke.py` — broad release sanity
- `check_cross_bank_call.py` — plain `call` to a label in a different bank
  (the May 2026 type-immunity softlock class). 39 hits in the boss-AI policy
  code were thunked through 7 hl-preserving wrappers (`AIxxx_HL`) in
  `engine/battle/ai/boss_thunks.asm` that route via `farcall` to the
  bank-0x0b scoring helpers (commit `f2e18554`). Audit currently PASS.
  Promotion to release-smoke floor is **gated on trace-ROM verification** —
  the fix changes pokegold_trace.gbc bytes; manifest hashes
  (`audit/boss_ai_trace/live_capture_manifest.json`) need refreshing and
  captures need re-running to confirm boss AI behavior wasn't relying on
  the broken cross-bank call's garbage execution. Run the trace pipeline +
  update the manifest before promoting this audit.
- `check_navigation_floor.py` — docs/dev_index integrity
- `check_boss_ai_*.py` — boss AI invariants

After **any** successful build that links, regenerate the dev index:
```bash
python scripts/generate_dev_index.py --rom pokegold
```
Audits read bank/free-space figures from `docs/generated/dev_index.md`. The
cost of regenerating when not strictly required is one git diff line; the
cost of skipping when required is an audit failure and a round trip.

Balance/stats/evos/level-up/TM data changes: also regen
`docs/generated/balance_audit.md` via `scripts/generate_balance_audit.py`.

## Never hand-edit these

- `docs/generated/*.md` — regenerated from source.
- `*.gbc`, `*.map`, `*.sym`, `*.o` — linker/build outputs.
- `pokegold.gbc.apr26-backup`, anything in `.local/` or `workspace/` — scratch.

If a generated file looks wrong, fix the source or generator and rebuild.

(`dist/` used to hold a BPS distribution patch + `checksums.txt`. The
BPS regen workflow needed `flips`, which is no longer available in this
environment — `dist/` was retired 2026-05-03. If you set up a new release
pipeline, recreate `dist/` and document the toolchain in
`docs/build.md`.)

## Project layout quirks

- **Big data tables use different layouts.** `BaseData` chains one `INCLUDE`
  per Pokémon (`data/pokemon/base_stats/<species>.asm`). `Moves` is one file
  of inline `move` macro calls. `EvosAttacks` is one file of inline per-
  species labels. Adding an entry usually requires touching: a constant in
  `constants/`, the master table in `data/`, and any pointer table that
  indexes it.
- `INCLUDE "..."` paths are case-sensitive.
- Trainer parties live in `data/trainers/parties.asm`, AI tiers in
  `data/trainers/ai_tiers.asm`, attributes in `data/trainers/attributes.asm`.

## RGBDS / asm gotchas

`docs/asm_authoring_guide.md` is the long-form source of truth (~935 lines,
auto-injected at session start via `scripts/inject_asm_guide.py` per
`.claude/settings.json`). Read it before writing any `.asm`. The bullets
below are a reminder list, not the canonical reference.

- **`Label:` is local to its file; `Label::` is exported across banks.**
  Never silently downgrade `::` to `:` — cross-bank refs fail to link.
- **ROM banks are `$4000` bytes (16 KiB).** Growth past free space is a
  link-time failure. Check `Tight Banks` in `docs/generated/dev_index.md`
  before adding bytes.
- **Cross-bank calls use `farcall` / `callfar`.** Plain `call` only reaches
  the current bank or ROM0 — calling a `::` label in another bank with
  `call` will assemble but jump to garbage.
- **`farcall` clobbers caller's `hl` BEFORE the target runs.** The macro
  expands to `ld hl, target; ld a, BANK(target); rst FarCall`. If target
  reads hl as input, this is a bug. Three valid patterns: (1) push/pop hl
  if hl just needs preserving; (2) ROM0 thunk via `homecall` (preserves
  hl) when target needs hl as in/out; (3) pass hl via bc/de and reconstruct
  inside. The April 2026 one-shot damage bug and May 2026 rival 1 softlock
  both came from this. See `docs/asm_authoring_guide.md` §3.2 for the three
  valid patterns. Audited by `tools/audit/check_farcall_hl_clobber.py`
  (in the release-smoke floor): hl-input functions are auto-discovered by
  a `; Reach via ROM0 thunk ...` marker comment in the function header.
  When adding a new hl-input function, add the marker so the audit picks
  it up.
- **`farcall` does NOT preserve target's `a` either.** After farcall,
  caller's `a` = target's exit `c`, not target's `a` (see
  `home/farcall.asm:13-28` — the trailing `ld a, [wFarCallBC + 1]; ld c, a;
  ret` clobbers target's a). For a-return cross-bank functions: mirror the
  value into `c` at every `ret` in the target (cheap: one `ld c, a` per
  ret), OR return via HRAM, OR use a HOME thunk that stashes the result.
  The May 2026 wild-level-floor no-op came from this — `farcall
  GetProgressionLevelCap` was reading target_c instead of the cap.
  Audited by `tools/audit/check_farcall_a_clobber.py` (in the
  release-smoke floor as of 2026-05-04): walks back from each `ret`
  through c-untouching instructions for an `ld c, a` mirror; flags
  farcall sites where target is UNSAFE and the caller consumes `a`
  post-farcall. First fire surfaced 5 latent live bugs in battle code
  (commit `13a6e3a3`).
- **`assert` lines in tables/macros catch bounds at link time.** Don't
  delete them to make the build pass — fix the underlying mismatch.

## Stat math (don't conflate base with computed)

Battle uses the **computed** stat, not the base stat. Stat boost stages
multiply the computed stat. Confusing the two has cost a debug session.

- Computed (non-HP) = `floor((2*base + IV + EV/4) * level / 100) + 5`.
- Computed HP        = `floor((2*base + IV + EV/4) * level / 100) + level + 10`.
- IV range 0..15, EV range 0..65535 per stat.

Stat-stage multipliers (Gen 2): +1=×1.5, +2=×2.0, +3=×2.5, +4=×3.0, +5=×3.5,
+6=×4.0; -1=×0.66, -2=×0.5, -3=×0.4, -4=×0.33, -5=×0.28, -6=×0.25.

`wEnemySpdLevel` etc. uses base-7 encoding: `BASE_STAT_LEVEL = 7 = +0`,
`MAX_STAT_LEVEL = 13 = +6`. **Don't read the byte as the multiplier.**

**Trap**: a low-base mon at +N is faster/stronger than a high-base mon at
+0, because the boost multiplies the +5 constant and the IV/EV contribution
too. Base 50 at +2 Speed beats base 100 at +0 Speed at level 50.

### Speed-affecting moves in this hack
- `AGILITY` (+2 Spe) is the ONLY single-stat +Speed move.
- `DRAGON_DANCE` = +1 Atk, +1 Spe. `QUIVER_DANCE` = +1 SpA, +1 SpD, +1 Spe.
- A "no Agility" rule equivalently bans the only single-stat +Speed move.
- Combo moves bypass `.check_speed` and route through `.check_atk_or_spd`
  / `.check_quiver_dance` because their non-Speed components carry weight.

### Boss AI Speed-cap rule
`BossAI_SetupBoostHasFurtherValue .check_speed`:

| Base Speed | Cap stage | Agilities used in practice |
| --- | --- | --- |
| ≥ 90 | +1 | 1 |
| 60–89 | +2 | 1 |
| ≤ 59 | +3 | 2 |

The effective discrimination is "≤59 base gets a second Agility, the rest
get one." See `engine/battle/ai/boss_policy_move.asm` `.check_speed`.

## RAM rules

- `ram/` is high-caution. WRAM/SRAM offsets are part of the save format.
  Reordering or resizing fields will silently misalign old saves. There's
  a `SAVE_FORMAT_VERSION` marker but **no migration code anywhere**. Treat
  save-format changes shipping to public release as a user-approval item.
- WRAMX is bank-switched. Boss AI state lives in WRAMX bank 1 with a fixed
  reserve budget — see `Boss AI WRAM Reserve` in `docs/generated/dev_index.md`
  before adding bytes.
- `hROMBank` (HRAM) shadows the current ROM bank. Bank-switch helpers
  maintain it; bypassing them desyncs the shadow and breaks subsequent
  `farcall`s.

## Recent work

For a list of what changed lately, run `git log codex/cleanup-gsc-rebalance-split`.
This section used to enumerate "shipped on YYYY-MM-DD" entries with commit
hashes; that pattern silently rotted (work moved to side branches, was
rebased, was reverted) and had agents quoting stale claims as ground truth
twice in one day. The audit `tools/audit/check_no_stale_shipped_claims.py`
now flags any date- or commit-anchored claim in tracked .md files whose
cited commit isn't an ancestor of the dev tip.

Design intent for individual functions belongs at the function header in
source (where it stays in sync with the code), not in this file.

## Pokemon Mastery Compounding Loop

The Pokemon Mastery training work is run as a durable, verifier-gated loop.
The runbook is [docs/pokemon_mastery/compounding_loop.md](docs/pokemon_mastery/compounding_loop.md);
the case library brain is in [tools/pokemon_mastery/case_library/](tools/pokemon_mastery/case_library/).
Both Claude /pgoal sessions and Codex sessions can run iterations against
the same case library. If you're in a fresh session and want to know loop
state: `python ~/.claude/skills/pgoal/scripts/pgoal.py status` (Claude
only), or read `tools/pokemon_mastery/case_library/loop_state.json`
(both). To run a manual iteration, follow the "Run one iteration" recipe
in the runbook. Per-iteration commits use the message form
`pokemon-mastery-loop: iter N <phase> <replay_id|na>` so the loop's history
is greppable.

## Workflow

The repo runs on a senior-dev / CEO contract. The user has gameplay taste
and the playtest seat; he does not code. All technical decisions, git, and
release execution are delegated to you. The Codex prompt-drafting workflow
is **not** used here — you are the sole executor.

### Authority
- All technical decisions: architecture, file layout, audits, build steps,
  refactor scope, naming, asm/banking, doc edits, audit script changes.
- Full git: commit, push, open PRs without confirmation when the work is
  ready.
- Drive release passes: when audits are green, refresh `roms.sha1` and
  `validation_report.md` without asking. (`dist/*` BPS regen is no
  longer in scope — see "Never hand-edit these" for the retirement note.)
- Reorganize working files (CLAUDE.md, docs structure) without asking.

### What to escalate
- **Gameplay taste decisions** — Pokémon stats, movesets, types, trainer
  rosters, level curves, encounter rates, item placement, dialogue. Frame
  the ask as a taste call.
- **Playtest tasks** — when human eyes on the ROM are needed, ask for a
  specific scenario.
- **Save-format changes shipping to public release.**
- **Merging to master.** Release event for this hack.
- **Truly destructive irreversible actions.** Force-push to master,
  `rm -rf` outside scratch, deleting branches with unmerged work.

Everything else: decide and execute. The test is "is this on the
escalation list?" — not "is this structural?"

### Pushback protocol
- **Soft pushback on gameplay taste.** State your view, defer to the user.
  His domain: fairness, feel, fun, role of a Pokémon, trainer difficulty.
- **Hard pushback on technical correctness.** Refuse to ship broken builds,
  save-format breakage, known-broken code, demonstrably wrong technical
  decisions. The user explicitly does not want a yes-man on tech. When
  you're right, hold the line — explain once cleanly, and if he insists,
  do what he asked.

Verify before acting. Verifying is checking, not asking permission — both
racing past errors and bouncing back to confirm are failures.

### Human-facing tools
- When building review tools, side apps, or dashboards, optimize the UI for
  the human decision being made, not for exposing raw internal data. If the
  first version shows JSON, logs, or technical fields, consider whether a
  labeled summary, comparison view, or guided workflow would better serve the
  user.
- When a task shifts from implementation into product/design iteration, pause
  briefly to restate the current goal and the latest preferred workflow before
  continuing.

## Honesty

- If you don't know something, say "I don't know" or "I'd need to read X
  to know." Don't guess and present as fact.
- Don't claim a change worked without verifying. Verification = re-read
  the edited file, run the relevant audit, or build. "I edited the file"
  is not verification.
- If you catch yourself writing a confident summary of something you
  didn't actually check, stop and check it.
- Don't hedge to seem humble. State technical conclusions plainly;
  calibrated uncertainty is a stated position, not hedging.

## Session handoff

Recommend ending the session and starting fresh when:
- You've read 10+ files this session
- You've been corrected by the user 3+ times
- The task has shifted from how the session started
- A long task is complete and the next task is unrelated

Save handoff to `.claude_handoffs/YYYY-MM-DD-HHMM-<slug>.md` (create dir
+ add to `.gitignore` if needed). Cover current state, specific file
paths, decisions not yet in committed code or CLAUDE.md, anything to
remember/avoid. Skip narrative recap of what was tried and discarded.
