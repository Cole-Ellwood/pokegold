# Voucher Removal + TM Swap Implementation Plan

Created 2026-05-08. Branch: `codex/damage-debugger-roadmap-20260506`.

## Goal

Revert the TM Voucher / TM Tutor system. It is the only meta-system in this
hack with no precedent in any Pokémon game and clashes with the "feels like
base Gold but with different mechanics" design intent (`docs/project_context.md`).
Replace voucher rewards with actual TMs as gym leader rewards. Swap five
niche existing TMs for five strong moves so the gym reward themes work.

## Non-goals

- Late-gen items, type passives, Imperial Scales, Dragon's Majesty, the
  Outrage physical-when-Atk>SpA recategorization — all stay.
- Boss AI engine logic — no changes.
- Save format version — **no bump required** (see § Save format).

## Decisions locked (user-approved 2026-05-08)

### Gym rewards

| Leader | Reward TM | Note |
| --- | --- | --- |
| Falkner | `TM_WING_ATTACK` | new TM (the hack's first Flying TM) |
| Bugsy | `TM_LEECH_LIFE` | new TM |
| Whitney | `TM_DOUBLE_EDGE` | new TM |
| Morty | `TM_SHADOW_BALL` | already TM30 |
| Chuck | `TM_DYNAMICPUNCH` **and** `TM_FOCUS_PUNCH` | DP is TM01; FP is new. Chuck gives two TMs. |
| Jasmine | `TM_IRON_TAIL` | already TM23 |
| Pryce | `TM_BLIZZARD` | already TM14 |
| Clair | `TM_OUTRAGE` | new TM |

### TM swap mapping

Five existing TMs are repurposed. TM number and item ID stay; only the
move taught changes.

| Slot | Item ID | Old move | New move |
| --- | --- | --- | --- |
| TM09 | `0xc8` | `PSYCH_UP` | `WING_ATTACK` |
| TM13 | `0xcc` | `SNORE` | `LEECH_LIFE` |
| TM39 | `0xe7` | `SWIFT` | `DOUBLE_EDGE` |
| TM43 | `0xeb` | `DETECT` | `FOCUS_PUNCH` |
| TM50 | `0xf2` | `NIGHTMARE` | `OUTRAGE` |

## Save format

No bump.

- `TM_VOUCHER` constant slot at item ID `0x73` stays reserved (rename to
  `RESERVED_VOUCHER_SLOT` or match the existing `ITEM_73` convention).
  Old saves with the item still load; the item just does nothing.
- `wTMTutorCredits` byte (`ram/wram.asm:2466`) becomes
  `RESERVED_UNUSED`. WRAM layout preserved.
- `EVENT_TM_TUTOR_UNLOCKED` (`constants/event_flags.asm:1163-1164`)
  stays in place as `RESERVED_*` or just unused. Event flag layout
  preserved.
- TM swap (TM09 = `WING_ATTACK`, etc.) keeps the same bit positions.
  An old saved Pokémon with "knows TM09" set will, after the swap, mean
  it knows `WING_ATTACK` instead of `PSYCH_UP`. That is a content
  change, not a corruption. Player's bag with TM09 in it now teaches
  `WING_ATTACK`. No version bump needed.

## Phase 1 — TM swap

This phase comes first. Gym scripts in Phase 3 reference the new TM
constants, which only exist after Phase 1.

### 1.1 Update TM constants

File: `constants/item_constants.asm` (lines 220-271)

Edit five `add_tm` lines in place:

```diff
-	add_tm PSYCH_UP    ; c8
+	add_tm WING_ATTACK ; c8
-	add_tm SNORE       ; cc
+	add_tm LEECH_LIFE  ; cc
-	add_tm SWIFT       ; e7
+	add_tm DOUBLE_EDGE ; e7
-	add_tm DETECT      ; eb
+	add_tm FOCUS_PUNCH ; eb
-	add_tm NIGHTMARE   ; f2
+	add_tm OUTRAGE     ; f2
```

This redefines `TM09_MOVE` … `TM50_MOVE` to point at the new moves.
The corresponding `_TMNUM` constants for `WING_ATTACK`, `LEECH_LIFE`,
`DOUBLE_EDGE`, `FOCUS_PUNCH`, `OUTRAGE` get assigned. The OLD-move
`_TMNUM` constants (e.g. `PSYCH_UP_TMNUM`) disappear, which is what
forces the `tmhm` line edits in Phase 1.3.

### 1.2 Update item descriptions

File: `data/items/descriptions.asm`

For each retired TM, the description needs to be replaced with the new
TM's description. Search for the existing `TMxx_*Desc:` blocks for
`PSYCH_UP`, `SNORE`, `SWIFT`, `DETECT`, `NIGHTMARE` and replace with
descriptions for `WING_ATTACK`, `LEECH_LIFE`, `DOUBLE_EDGE`,
`FOCUS_PUNCH`, `OUTRAGE`. Match the format used by neighboring TM
descriptions.

### 1.3 Migrate base_stats `tmhm` learnsets

This is the bulk of the work. Every Pokémon's `tmhm` line that contains
a retired move name will fail to assemble (the move's `_TMNUM` no
longer exists). For each retired move:

1. Find every `data/pokemon/base_stats/*.asm` whose `tmhm` line lists
   the old move (`grep -l "tmhm.*PSYCH_UP" data/pokemon/base_stats/*.asm`,
   etc.).
2. For each Pokémon that should learn the **new** move at this slot,
   replace the old name with the new name in their `tmhm` list.
3. For each Pokémon that should NOT learn the new move, just remove
   the old name from their `tmhm` list.
4. For each Pokémon that should learn the new move but did not learn
   the old one, ADD the new move to their `tmhm` list.

**First-pass heuristic:** mirror canonical post-Gen-2 learnsets as the
starting point. Specifically:

- `WING_ATTACK` — Flying-types and "winged" Pokémon: Pidgey/Pidgeotto/
  Pidgeot, Spearow/Fearow, Hoothoot/Noctowl, Murkrow, Skarmory,
  Aerodactyl, Crobat, Charizard, Dragonite, Gyarados, Articuno,
  Zapdos, Moltres, Lugia, Ho-Oh. Plus anything that learns it via
  level-up in `data/pokemon/evos_attacks.asm`.
- `LEECH_LIFE` — Bug-types broadly (Caterpie/Metapod/Butterfree only
  if reasonable; Beedrill, Heracross definitely; Venomoth, Crobat,
  Gengar). Cross-reference current evos_attacks LEECH_LIFE learners.
- `DOUBLE_EDGE` — heavy Normal-types and strong physical attackers:
  Snorlax, Tauros, Donphan, Rhydon/Rhyhorn, Aerodactyl, Tyranitar,
  Ursaring, Stantler, etc. Wide distribution (most physical attackers
  learned this in canon).
- `FOCUS_PUNCH` — Fighting-types and strong physical attackers:
  Hitmonchan, Hitmonlee, Hitmontop, Machamp, Heracross, Snorlax,
  Tyranitar, Granbull (Chuck's roster uses it on Hitmontop, Hitmonlee,
  Poliwrath — those should learn it).
- `OUTRAGE` — Dragon-types and select strong physical attackers:
  Dragonair/Dragonite, Charizard, Gyarados, Kingdra, **Steelix** (now
  STEEL/DRAGON; learns via level-up at L38 already, can also be a TM
  learner), Tyranitar, Aerodactyl, Charmeleon line, Salamence-style
  if any.

The user will review Codex's first-pass mapping per move and adjust
for hack balance intent (see § Open items).

### 1.4 Mart wiring

File: `data/items/marts.asm`

Search for the retired TMs in mart inventories. If present, replace
with the new TM (or remove the line if the new TM should not be
purchasable in that mart's tier).

### 1.5 Item ball / hidden item placements

`grep -rn "TM_PSYCH_UP\|TM_SNORE\|TM_SWIFT\|TM_DETECT\|TM_NIGHTMARE" maps/`
and update each to the corresponding new TM constant (or to a
different existing TM if the location-themed fit no longer makes
sense).

### 1.6 Trainer parties

`grep -n "PSYCH_UP\|SNORE\|SWIFT\|DETECT\|NIGHTMARE" data/trainers/parties.asm`
and review. NPC parties are not affected by `tmhm` learnset changes
(they specify moves directly), so each NPC retains the old move IF
the move is still legal via level-up. If the move is now unobtainable
(e.g., a retired TM and not a level-up move), pick a thematic
substitute or leave with two moves and pad with `NO_MOVE` only if the
audit exception covers it (Falkner Spearow precedent).

## Phase 2 — Voucher / Tutor removal

### 2.1 Item constant — keep slot reserved

File: `constants/item_constants.asm:123`

```diff
-	const TM_VOUCHER       ; 73
+	const RESERVED_VOUCHER_SLOT ; 73
```

(Or rename to `ITEM_73` to mirror the existing `ITEM_C3` / `ITEM_DC`
convention. Either is fine.)

### 2.2 Item display name

File: `data/items/names.asm:117`

```diff
-	li "TM VOUCHER"
+	li "?"
```

The slot is unobtainable after this work; the placeholder name only
matters for old saves that already have one in their bag.

### 2.3 Item attributes

File: `data/items/attributes.asm:239`

Replace the `TM_VOUCHER` attribute row with a placeholder no-effect
row. Match the format of any neighboring reserved-slot rows.

### 2.4 Item effect

File: `engine/items/item_effects.asm:131`

Update the comment; the entry stays at `NoEffect`:

```diff
-	dw NoEffect ; TM_VOUCHER
+	dw NoEffect ; RESERVED_VOUCHER_SLOT (was TM_VOUCHER)
```

### 2.5 Item description

File: `data/items/descriptions.asm:707-709`

Delete the `TMVoucherDesc:` block entirely. If the description table
expects one entry per item ID, replace with a placeholder pointer
matching how the other reserved slots are handled.

### 2.6 Day Care Tutor NPC removal

File: `maps/DayCare.asm`

Delete the following:

- Line 4: `const DAYCARE_TM_TUTOR`
- Line 7: `DEF DAYCARE_TM_TUTOR_UNLOCK_FEE EQU 1000`
- Lines 51-161: full `DayCareTMTutorScript` and all `.` child labels
  (FaceCheck, FightDone, AfterVoucherReward, etc.).
- Lines 178-274: all `DayCareTMTutor*Text` blocks (16 entries).
  `DayCareServicePamphletText` (the bookshelf entry advertising the
  voucher exchange) — replace with vanilla daycare flavor or remove
  the bookshelf script entry from the map.
- Line 294: the `object_event 8, 4, SPRITE_SUPER_NERD, ... ,
  DayCareTMTutorScript, -1` line.

After deletion, the Day Care building has only the breeding couple,
matching base Gold/Silver behavior.

### 2.7 Engine file removal

Delete `engine/events/tm_tutor.asm` entirely.

### 2.8 Special pointer registration

File: `data/events/special_pointers.asm:131`

Remove the `add_special TMTutorTeachAnyTM` line.

### 2.9 main.asm INCLUDE

File: `main.asm:153`

Remove `INCLUDE "engine/events/tm_tutor.asm"`.

### 2.10 WRAM reservation

File: `ram/wram.asm:2466`

```diff
-wTMTutorCredits:: db
+	ds 1 ; RESERVED_UNUSED (was wTMTutorCredits)
```

Line 2465 (`wTMTutorBadgesCounted::`) is already a reserved
placeholder — leave or rename for clarity.

### 2.11 Event flags

File: `constants/event_flags.asm:1163-1164`

`EVENT_TM_TUTOR_UNLIMITED` is already RESERVED — leave. For
`EVENT_TM_TUTOR_UNLOCKED`, either rename to a `RESERVED_EVENT_*`
placeholder or just leave the constant defined but unused. Both
preserve flag bit layout.

## Phase 3 — Gym rewards

For each gym leader, replace the `verbosegiveitem TM_VOUCHER` with the
correct TM. Maps and lines:

| Map | Lines | New giveitem |
| --- | --- | --- |
| `maps/VioletGym.asm` | 41 | `verbosegiveitem TM_WING_ATTACK` |
| `maps/AzaleaGym.asm` | 44 | `verbosegiveitem TM_LEECH_LIFE` |
| `maps/GoldenrodGym.asm` | 67 | `verbosegiveitem TM_DOUBLE_EDGE` |
| `maps/EcruteakGym.asm` | 44 | `verbosegiveitem TM_SHADOW_BALL` |
| `maps/CianwoodGym.asm` | 61 | `verbosegiveitem TM_DYNAMICPUNCH` |
| `maps/CianwoodGym.asm` | (after 61) | add `verbosegiveitem TM_FOCUS_PUNCH` (Chuck's second reward — sequenced after the first, with its own bag-full check if the existing macro requires one) |
| `maps/OlivineGym.asm` | 35 | `verbosegiveitem TM_IRON_TAIL` |
| `maps/MahoganyGym.asm` | 45 | `verbosegiveitem TM_BLIZZARD` |
| `maps/BlackthornGym1F.asm` | 57, 73, 98 | all three: `verbosegiveitem TM_OUTRAGE` |

### Notes

- **Chuck's two TMs:** the script flow needs a second `verbosegiveitem`
  call after the first succeeds. If the first hits a bag-full branch,
  decide whether the second still attempts. Simplest: gate the second
  on the first having succeeded. Add a new event flag (e.g.
  `EVENT_GOT_TM_FROM_CHUCK_DYNAMICPUNCH`) if the existing event flag
  pattern requires one per TM. Or reuse one flag for "got both" — your
  call.
- **Clair's three branches:** all three currently gate on
  `EVENT_GOT_TM24_DRAGONBREATH`. After the swap that flag's name is
  misleading (Clair gives Outrage, not DragonBreath). Optional cosmetic
  rename: `EVENT_GOT_TM24_DRAGONBREATH` → `EVENT_GOT_CLAIR_REWARD_TM`
  in `constants/event_flags.asm` and every reference. Not required for
  correctness.

## Phase 4 — Cleanup

### 4.1 Audits

#### `tools/audit/check_gym_leader_wiring.py` (lines 352-363)

Replace the `LEADER_REWARDS` dict's `TM_VOUCHER` entries:

```python
LEADER_REWARDS = {
    "Falkner": "TM_WING_ATTACK",
    "Bugsy": "TM_LEECH_LIFE",
    "Whitney": "TM_DOUBLE_EDGE",
    "Morty": "TM_SHADOW_BALL",
    "Chuck": ("TM_DYNAMICPUNCH", "TM_FOCUS_PUNCH"),  # Chuck gives two
    "Jasmine": "TM_IRON_TAIL",
    "Pryce": "TM_BLIZZARD",
    "Clair": "TM_OUTRAGE",
    # Kanto entries unchanged
    "Erika": "TM_GIGA_DRAIN",
    "Janine": "TM_TOXIC",
}
```

Update the audit logic to handle the two-tuple case for Chuck (every
listed TM must appear in the gym script).

#### `tools/audit/bug_hunt_triage.py`

- Line 24: remove `TM_TUTOR = ROOT / "engine" / "events" / "tm_tutor.asm"`.
- Lines 542-571: remove the `audit_tm_tutor_cur_item_restore` function
  and any reference to it in the audit dispatcher.

#### `tools/audit/check_release_smoke.py`

- Line 959: remove the `require_text(ROOT / "main.asm",
  'INCLUDE "engine/events/tm_tutor.asm"')` line.
- Line 1052: remove `engine/events/tm_tutor.asm` from the required
  files list.

#### `tools/boss_ai_preference/threat_availability.py`

- Lines 30-36: remove `voucher_limited` from `STAB_FLOOR_BY_SOURCE`.
- Lines 39-53 (`Checkpoint` dataclass): remove the `vouchers_before`
  and `tm_tutor_available` fields.
- Remove the `daycare_tutor_is_any_tm()` function and any caller. The
  `legal_moves_for_species` call site at line 562-569 must be updated:
  drop the `voucher_limited` source attribution branch entirely.
- Lines 605-606 (`likelihood_for_move`): remove the `voucher_limited`
  branch.
- Every `Checkpoint(...)` constructor call (lines 176 onwards) must
  drop the `vouchers_before` and `tm_tutor_available` arguments.

#### `tools/audit/check_boss_ai_preference.py`

- Lines 95-101 reference `voucher_limited` and `tm_available`. Adjust
  to expect only `tm_available` (TMs are now solely the via direct-TM
  source).
- Any test that asserts voucher-pathway behavior should be deleted.

### 4.2 Documentation

#### `docs/mechanics_changes_from_base.md`

- Delete §3.1 "TM Tutor Credit Economy" (lines 339-356).
- Delete §3.3 "Gym Reward Economy Shift" (lines 372-381).
- Add a brief replacement note under §3 that gym TM rewards follow the
  vanilla pattern with the leader → TM table from this plan's Phase 3.

#### `docs/agent_navigation/custom_terms.md`

- Lines 41 and 57: remove the TM Tutor / TM Voucher entries.

#### `docs/manual_qa_backlog.md`

- Lines 55 and 78: remove voucher-economy QA tests. If a "verify gym
  TM rewards" test is desired, replace with a generic version covering
  the new gym TM map.

#### `docs/qol_handoff.md`

- Lines 16, 41, 133, 144, 160, 235: leave references in place. This
  doc is a "what was tried" archive; it should reflect history.

#### `docs/RELEASE_NOTES.md`

- Line 10: remove the TM Tutor / voucher mention from the progression
  list. Replace with the gym TM reward summary from this plan.

#### `docs/project_roadmap.md`

- Line 59 (QOL-001 reference): leave — historical changelog. Optionally
  add a new row noting the voucher removal + TM swap as a 2026-05-08
  workstream.

#### `docs/balance_intent.md`

- Add a section under "Boss Roster Intent Notes" documenting the TM
  swap: which 5 moves were retired, which 5 moves added, and the
  rationale (gym leader rewards now reflect each leader's type via
  actual type-relevant TMs; no meta-system).

### 4.3 Generated artifacts

After all of the above, regenerate (in this order):

```bash
python scripts/generate_balance_audit.py
python scripts/generate_dev_index.py --rom pokegold
python -m tools.boss_ai_preference threat-report
python -m tools.boss_ai_preference report
```

Files updated:
- `docs/generated/balance_audit.md`
- `docs/generated/dev_index.md`
- `audit/boss_ai_preference/threat_availability_report.md`
- `audit/boss_ai_preference/threat_availability_report.json`
- `audit/boss_ai_preference/latest_report.md`
- `audit/boss_ai_preference/latest_report.json`

## Verification

### Build

```bash
wsl -e bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && \
  make -j4 PYTHON=python3 \
    RGBASM=rgbds-1.0.1/rgbasm.exe \
    RGBLINK=rgbds-1.0.1/rgblink.exe \
    RGBFIX=rgbds-1.0.1/rgbfix.exe \
    RGBGFX=rgbds-1.0.1/rgbgfx.exe \
    pokegold.gbc'
```

### Audits (must pass)

```bash
python tools/audit/check_boss_moves_complete.py
python tools/audit/check_gym_leader_wiring.py
python tools/audit/check_docs_navigation.py
python tools/audit/check_boss_ai_preference.py
python tools/audit/check_boss_ai_trace_invariants.py
python -m tools.boss_ai_preference validate
```

`check_release_smoke.py` is expected to still fail on the pre-existing
stale shipped-claims issue in handoff/docs files. Not caused by this
work.

### ROM SHA1

After build success, do NOT update `roms.sha1` until manual playtest
confirms each gym sequence behaves correctly. The SHA1 will change.

### Manual playtest checklist

- [ ] Falkner defeated → receives `TM_WING_ATTACK`.
- [ ] Bugsy defeated → receives `TM_LEECH_LIFE`.
- [ ] Whitney defeated → receives `TM_DOUBLE_EDGE`.
- [ ] Morty defeated → receives `TM_SHADOW_BALL`.
- [ ] Chuck defeated → receives `TM_DYNAMICPUNCH` first, then
      `TM_FOCUS_PUNCH` (or both in a single dialog flow — verify the
      script's bag-full handling for both).
- [ ] Jasmine defeated → receives `TM_IRON_TAIL`.
- [ ] Pryce defeated → receives `TM_BLIZZARD`.
- [ ] Clair defeated (full Dragon's Den arc) → receives `TM_OUTRAGE`.
- [ ] Day Care building functional (breeding works); no NPC where the
      tutor used to stand.
- [ ] An old saved game from before this work loads cleanly. If the
      bag had a TM_VOUCHER, it shows as "?" or the placeholder name
      and does nothing when used.

## Open user-curation items

After Phase 1.3, the user reviews Codex's first-pass `tmhm` learnset
mapping for each new TM:

- `WING_ATTACK` — which Pokémon learn it via TM
- `LEECH_LIFE` — which Pokémon learn it via TM
- `DOUBLE_EDGE` — which Pokémon learn it via TM
- `FOCUS_PUNCH` — which Pokémon learn it via TM
- `OUTRAGE` — which Pokémon learn it via TM

Codex's first pass should mirror canonical Gen 4 learnsets. The user
will adjust for hack-specific balance.

## Execution order summary

1. Phase 1.1 (TM constants) — unlocks the new TM names for everything else
2. Phase 1.2 (descriptions)
3. Phase 1.3 (base_stats migration) — gated by Phase 1.1
4. Phase 1.4-1.6 (marts / item balls / parties cleanup)
5. Phase 2 (voucher / tutor removal) — independent of Phase 1, can run in parallel
6. Phase 3 (gym rewards) — gated by Phase 1.1 and Phase 2
7. Phase 4.1-4.2 (audit + doc cleanup)
8. Phase 4.3 (regen generated artifacts) — must come after everything else
9. Verification
10. User playtest pass + roms.sha1 refresh
