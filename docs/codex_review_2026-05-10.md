<!-- audit:noqa-file stale-claims -->

# Codex review request — Claude session 2026-05-10

Trainer-roster + species rebalance pass with one tooling extension and one
tooling bugfix. Seven commits, all on `claude/upbeat-williamson-ed7924`.

## Branch state

- **Worktree**: `C:\Users\lolno\Downloads\pokemon gold hack\.claude\worktrees\upbeat-williamson-ed7924`
- **Branch**: `claude/upbeat-williamson-ed7924`
- **Tracks**: `origin/codex/cleanup-gsc-rebalance-split` (not pushed)
- **Position**: 10 commits ahead of base (3 from prior session, 7 from this session)
- **Working tree**: clean

If you operate in a different worktree, all session commits are reachable via
`git log --oneline 9a391843..claude/upbeat-williamson-ed7924`. SHAs below are
abbreviated; full SHAs are stable.

## Session commits (newest first)

| SHA | Title | Files touched |
|---|---|---|
| `159845ac` | balance(red): Venusaur / Charizard / Blastoise moveset polish | `data/trainers/parties.asm`, regen artifacts |
| `c4e3e224` | dossier: render level-up moves for TRAINERTYPE_NORMAL / _ITEM rosters | `scripts/generate_trainer_dossier_pdf.py`, regen pdf |
| `06147f24` | balance: rival 6/7 movesets + fight 5/6/7 starter slot moves | `data/trainers/parties.asm`, `data/pokemon/evos_attacks.asm`, regen artifacts |
| `1c24b204` | balance: rival 5 movesets + fight 4/5 starter levels + Typhlosion/Meganium | `data/trainers/parties.asm`, `data/pokemon/base_stats/{typhlosion,meganium}.asm`, `data/pokemon/evos_attacks.asm`, `tools/audit/check_release_smoke.py`, regen artifacts |
| `1c43631d` | balance: rival 1/3/4 tweaks + zubat/magnemite buffs | `data/trainers/parties.asm`, `data/pokemon/base_stats/{zubat,magnemite}.asm`, regen artifacts |
| `3cdd632d` | tooling(dossier): add Rival / Rocket admins / Red sections | `scripts/generate_trainer_dossier_pdf.py`, regen pdf |
| `770e46bb` | balance: Kanto gym pass + species edits + HP type rendering | (this commit was a pre-session WIP block from prior chat; landed at session start) |

Prior-session commits already on branch (for context, not in scope for review):
- `8c584f82` — balance(lance): five-Dragon-Dance setup squad + doc fix
- `585c7ad8` — balance: Johto/E4/Champion roster + species pass
- `05e28d66` — tooling: add trainer dossier PDF generator (initial)

## What changed in detail

### `3cdd632d` — Dossier extension: Rival / Rocket admins / Red sections

`scripts/generate_trainer_dossier_pdf.py` extended:
- Refactored `_parse_group_block` into `_parse_group_blocks` (returns ALL
  trainer entries in a Group label, bounded by next `*Group:` label) +
  `_parse_trainer_body` helper. Single-member entry point is a thin wrapper
  that takes `member_idx=1` for back-compat.
- New `RivalFight` dataclass models the 3-starter-branch collapse:
  `shared_party` (0-5 mons, identical across branches) + `starter_variants`
  (always exactly 3, in order Bayleef/Quilava/Croconaw line). An assertion
  fires if non-starter slots ever differ between branches.
- New meta tables: `RIVAL_FIGHTS` (7 fights), `ROCKET_ADMINS` (6 fights),
  `RED_FIGHT` (1 fight).
- New `render_rival_fight`: shared mons in 2-col, then a "STARTER SLOT"
  subheader band, then 3 starter variants in 3-col with "If you picked
  TOTODILE / CHIKORITA / CYNDAQUIL" labels above each.
- Added `ExecutiveMGroup` / `ExecutiveFGroup` to `_GROUP_TO_CLASS_OVERRIDE`
  so trainer-class DV lookup resolves correctly (no current admin uses HP
  but the wiring is in place).
- Cover subtitle updated.

**Design call**: Rocket admin name attribution (Petrel / Proton / Ariana /
Archer) follows HGSS canon since vanilla GS doesn't print these names.
Inferred from signature mons (Houndoom→Archer, Vileplume/Murkrow→Ariana)
and the "I'm a Rocket fortress" dialog at RT4F (Petrel). If wrong, edit
`ROCKET_ADMINS` — nothing else relies on it.

PDF: 14 → 31 pages.

### `1c43631d` — Rival 1 intro + species buffs + rival 3/4 move tweaks

Parties (`data/trainers/parties.asm`):
- Fight 1 (Cherrygrove): L8 starters with 4 moves → L5 with 2 base moves
  only (TACKLE/GROWL, TACKLE/LEER, SCRATCH/LEER). Just-got-the-starter
  intro should feel like an easy first scout. Kept TRAINERTYPE_ITEM_MOVES
  with NO_MOVE filler in slots 3-4 (consistent with rest of file).
- Fight 3 (Burned Tower) Haunter L20: CURSE → PSYBEAM
- Fight 4 (Goldenrod Underground) Sneasel L29: SCREECH → ICE_PUNCH
- Fight 4 Haunter L27: CURSE → DREAM_EATER (combos with existing HYPNOSIS)

Species:
- Zubat: Spe 55 → 70 (BST 245 → 260)
- Magnemite: HP 25 → 35 (BST 365 → 375)

### `1c24b204` — Rival 5 + fight 4/5 starter levels + Typhlosion/Meganium

Parties:
- **Fight 4 starter slot: L29 → L32** (matches vanilla GS; the only fight
  where the prior 2026-04-25 progression rebalance went *lower* than vanilla)
- **Fight 5 starter slot: L36 → L38**
- Fight 5 Sneasel L32: FURY_CUTTER → ICE_PUNCH
- Fight 5 Magneton L33: SWIFT / SONICBOOM → HIDDEN_POWER / TRI_ATTACK
  - HP resolves to **BUG** via RIVAL1 class DVs (atk 13 / def 13)
  - Tri Attack chosen because Magneton's 60 base Atk makes Iron Tail / Steel
    Wing weak; Tri Attack is the cleanest non-Electric coverage answer
- Fight 5 Gengar L33: HYPNOSIS / DESTINY_BOND / CONFUSE_RAY →
  SLUDGE_BOMB / PSYCHIC_M / THUNDER. All-special nuke (Shadow Ball +
  Sludge Bomb + Psychic + Thunder).

Species:
- Typhlosion: Atk 84 → 99, SpD 85 → 70 (BST stays 555). Real physical option
  to pair with the existing 130 SpA.
- Meganium: 110/82/100/80/83/100 → 130/75/107/60/83/100 (BST stays 555).
  Tank redistribution.

Learnset (`data/pokemon/evos_attacks.asm`):
- TyphlosionEvosAttacks: added `db 36, DOUBLE_EDGE` between L31 FLAME_WHEEL
  and L37 FIRE_BLAST. L36 is the Quilava→Typhlosion evolution level (was
  empty), so evolved Typhlosion learns Double-Edge on the spot.

Audit fingerprint:
- `tools/audit/check_release_smoke.py` pins Meganium / Typhlosion / Feraligatr
  stats as a regression check on starter final evolutions. Updated Meganium
  and Typhlosion expected values to match the new intentional stats.

### `06147f24` — Rival 6/7 movesets + fight 5/6/7 starter slot moves

Mirrors the rival 5 set into the post-Lance fights (Rival2Group), so Silver's
team identity persists into the late game.

Parties:
- Fight 6 (Mt. Moon, Rival2_1) + Fight 7 (Indigo Plateau, Rival2_2):
  - Sneasel L38 / L43: FURY_CUTTER → ICE_PUNCH
  - Magneton L38 / L43: SWIFT / SONICBOOM → HIDDEN_POWER / EXPLOSION
    - HP resolves to BUG via RIVAL2 class DVs (also 13/13)
    - Explosion is the kamikaze finisher: 250 BP physical, halves target Def,
      85 base Atk → ~425 effective BP
- Fights 5 / 6 / 7 Meganium L38 / L42 / L48: EARTHQUAKE → SYNTHESIS
  - Earthquake is wrong-type on a pure Grass mon; Synthesis already in
    Meganium's level-up at L23. Pairs with the new tankier 130/107 stat line.
- Fights 5 / 6 Typhlosion L38 / L42: QUICK_ATTACK → DOUBLE_EDGE
- Fight 7 Typhlosion L48: ANCIENTPOWER → DOUBLE_EDGE (slot 3, kept Flamethrower
  in slot 4)

Learnset:
- MagnetonEvosAttacks: added `db 42, EXPLOSION` after L38 ZAP_CANNON. Silver's
  L38/L43 Magneton sets Explosion explicitly via TRAINERTYPE_ITEM_MOVES, but
  the level-up entry keeps the species learnset legal at parity.

### `c4e3e224` — Dossier MOVES fix for TRAINERTYPE_NORMAL / _ITEM

**Symptom**: Proton's Mahogany B3F roster (and any other admin using
TRAINERTYPE_NORMAL) had empty MOVES columns in the dossier. Same would
have applied to TRAINERTYPE_ITEM rosters.

**Cause**: parser mapped both NORMAL and ITEM trainer types to four NO_MOVE
placeholders. The actual in-game behavior is that the engine fills moves at
runtime by walking the species' EvosAttacks level-up table — see
`engine/pokemon/evolve.asm:484` `FillMoves`.

**Fix**: replicated `FillMoves` in Python.
- `compute_levelup_moves(species, level)` walks the species' EvosAttacks
  block in source order. Learns each move at lvl ≤ current; if 4 slots full,
  FIFO-evicts oldest (engine's `ShiftMoves`); skips duplicates. Returns 4
  moves padded with NO_MOVE.
- Wired into `_parse_trainer_body` for both NORMAL and ITEM trainer types.

Edge cases handled:
- Evolution markers (`db EVOLVE_*, ..., SPECIES`) skipped — first arg is
  non-numeric, regex doesn't match.
- `db 0` sentinels skipped — no comma, regex doesn't match.
- Special species naming (MR__MIME, HO_OH, FARFETCH_D, NIDORAN_F/M, PORYGON2)
  via lookup table in `_species_to_evos_label`.

Verification: Zubat L22 → TACKLE / SUPERSONIC / BITE / CONFUSE_RAY (matches
ZubatEvosAttacks by hand: L1 TACKLE, L6 SUPERSONIC, L12 BITE, L19 CONFUSE_RAY;
L27 WING_ATTACK not yet learned).

### `159845ac` — Red moveset polish

Parties (Red is the only entry in RedGroup, member 1):
- Venusaur L77: GIGA_DRAIN → SLUDGE_BOMB. Sun-Solarbeam already covers Grass
  damage; Sludge Bomb hits Grass-types neutrally (Solarbeam can't reach them).
- Charizard L77: FIRE_SPIN → SUNNY_DAY, SLASH → SOLARBEAM. Becomes a
  sun-setter; 1-turn Solarbeam under sun punishes Water/Rock/Ground
  switch-ins. Sun also boosts the existing Flamethrower 1.5×.
- Blastoise L77: RAIN_DANCE → EARTHQUAKE, WHIRLPOOL → MIRROR_COAT. EQ
  closes the Electric coverage gap; Mirror Coat punishes "just Thunderbolt
  the turtle" play. Removing Rain Dance also stops Blastoise from
  countering Charizard's Sunny Day setup.

Two of Red's six mons now run sun (Venusaur, Charizard) — first to the field
banks the weather; both benefit.

## What I'd specifically like your eye on

1. **Dossier `compute_levelup_moves` algorithm**
   (`scripts/generate_trainer_dossier_pdf.py`). Mirrors
   `engine/pokemon/evolve.asm:484` `FillMoves`. Things worth verifying:
   - Multiple L1 moves: Typhlosion has 4× L1 moves (TACKLE / LEER /
     SMOKESCREEN / EMBER). At L1 should yield those 4. At L6 the L6
     SMOKESCREEN should be a no-op dedup. Spot-check.
   - Does `wSkipMovesBeforeLevelUp` (used by FillMoves on subsequent
     calls) matter for the first-fill case I'm modeling? I believe no —
     first-fill has it cleared.
   - Evolution markers preceding the move table: my regex distinguishes
     by first-arg-numeric, but some evolution macros could in principle
     start with a numeric (none currently do). Worth a thought.

2. **Rocket admin name attribution** (`ROCKET_ADMINS` table). HGSS-canonical
   mapping based on signature mons + dialog hints:
   - ExecutiveM_4 (Mahogany B3F, Zubat/Raticate/Koffing L22-24) = Proton
   - ExecutiveF_2 (Mahogany B2F, Arbok/Gloom/Murkrow L23-25) = Ariana
   - ExecutiveM_3 (RT5F, 6 Koffing/Weezing L30-32) = Petrel (Director-disguise)
   - ExecutiveM_1 (RT5F, Houndour/Koffing/Houndoom L33-35) = Archer
   - ExecutiveF_1 (RT5F, Arbok/Vileplume/Murkrow L32) = Ariana (second)
   - ExecutiveM_2 (RT4F, single Golbat L36) = Petrel ("I'm a fortress")

   If you have stronger evidence for a different attribution, flag it.

3. **Magneton Tri Attack pick** (commit `1c24b204`). User said "hidden power
   and a coverage attack". I picked Tri Attack because Magneton's 60 base Atk
   makes Iron Tail / Steel Wing weak, and Tri Attack is the cleanest non-
   Electric special-side coverage option. Taste call — could Lock-On + Zap
   Cannon (guaranteed-hit Electric STAB) or Mirror Coat be a better feel for
   a Steel/Electric mid-fight rival mon?

4. **Typhlosion DOUBLE_EDGE at L36** (commit `1c24b204` evos_attacks change).
   I added at L36 because that's the Quilava→Typhlosion evolution level and
   Typhlosion's L36 slot was empty. But Gen 2's "learn-on-evolution" mechanic
   is subtle — does the engine actually trigger move-learning at the post-
   evolution level if a move is mapped to that level? The relevant code is
   `engine/pokemon/evolve.asm` around the `FillMoves` call after evolution
   completes; check whether wPrevPartyLevel is set such that L36 is "newly
   learned" at the moment of evolution.

5. **Cherrygrove fight reduction to L5 / 2 moves** (commit `1c43631d`). The
   pre-existing convention in this hack uses TRAINERTYPE_ITEM_MOVES with
   explicit moves. I kept that and used NO_MOVE for slots 3-4. An alternative
   is TRAINERTYPE_NORMAL (which would yield only L1 moves at L5 via FillMoves).
   Either works; preference is taste.

6. **Audit fingerprint update** (`tools/audit/check_release_smoke.py`). I
   bumped the pinned Meganium / Typhlosion stats. The audit's purpose is
   regression detection — bumping values when a change is intentional is
   correct, but worth confirming I didn't bypass a safety check meant to
   force escalation on starter-stat edits. Read the audit's surrounding
   context to see if there's a separate review hook.

7. **Erika class DV change side effect** (from prior commit `770e46bb`,
   first commit of session). Atk DV 7 → 14 affects ALL Erika's mons'
   computed Atk by ~+4. I noted this is "essentially free" because none of
   her team runs physical attacks except Exeggutor's Explosion (one-shot
   anyway). Worth a second look: does any of her current roster benefit
   from or get destabilized by the +4 Atk?

## Things deliberately NOT changed (so you don't flag them as gaps)

- Late-fight Gengar movesets in Rival 6 (Mt. Moon) and Rival 7 (Indigo
  Plateau): user's Gengar rework was scoped to Rival 5 only. Rival 6/7
  Gengars still have HYPNOSIS / DESTINY_BOND / THUNDERBOLT / SHADOW_BALL
  + PSYCHIC. Matches user's specified scope; not propagated.
- Crobat in any rival fight: not touched.
- Alakazam in any rival fight: not touched.
- All Johto gym leader rosters (handled in prior session commits
  `8c584f82` / `585c7ad8`).
- All E4 / Champion rosters.

## Verification done per commit

- ROM build via WSL with the worktree-local rgbds copy trick:
  `cp -r ../../rgbds-1.0.1 .` then `make`, then `rm -rf rgbds-1.0.1`
- `tools/audit/check_release_smoke.py` — passes
- `python scripts/generate_dev_index.py --rom pokegold` — regenerated
- `python scripts/generate_balance_audit.py` — regenerated
- `python scripts/generate_trainer_dossier_pdf.py` — regenerated
- Dossier visual spot-checks via `pypdfium2` page renders for affected pages

Audits NOT run (none would have applied — would only matter for asm/code
changes I didn't make):
- `check_cross_bank_call.py` (no asm code touched, just data tables)
- `check_navigation_floor.py` (no docs source changes)
- `check_save_format_version.py` (no `ram/` touched)
- `check_typepassive_c_mirror.py` (no `late_gen_held_items.asm` /
  `type_passive_damage_mods.asm` touched)
- Damage debugger (`tools/damage_debugger`) (no battle ABI / register
  clobber changes)

## Findings format I'd like

Per Cole's preference:

- **File**: `<path>`
- **Line**: `<line number>`
- **Issue**: `<one sentence>`
- **Why**: `<reasoning>`
- **Fix**: `<proposed change>`
- **Confidence**: `low / medium / high`
