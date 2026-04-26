# Gym Leader Boss AI Verification - 2026-04-26

Purpose: record the current verification state for all 16 gym leaders without
blurring source/audit proof into live emulator proof.

## Bottom Line

All 16 gym leaders are now covered by the roster-level Boss AI audits:

- tier mapping coverage
- map-script-to-trainer-data wiring
- boss held-item coverage
- complete four-move coverage
- Boss AI gating/no-cheat/source invariants
- memory budget

Morty and Jasmine currently have completed live chosen-move trace captures. The
other gym leaders need real PyBoy-compatible decision-point save-states before
they can be called live-proven.

## Audit Tightening Done In This Pass

The audits used to verify Johto leaders, rivals, Elite Four, Champion, and Red,
while the Kanto leaders were present in source but not required by two roster
checks. This pass tightened the audit target sets so "all gym leaders" means
all 16 leaders.

Updated files:

```text
tools/audit/check_ai_tiers.py
tools/audit/check_boss_items_present.py
tools/audit/check_boss_moves_complete.py
```

The Kanto leaders are now required by the tier/items/moves audits:

```text
Brock, Misty, Lt. Surge, Erika, Janine, Sabrina, Blaine, Blue
```

Follow-up tightening added a source-truth cross-check against
`data/trainers/leaders.asm`, so `check_ai_tiers.py` now verifies that the
engine's own `GymLeaders` / `KantoGymLeaders` tables agree with the Boss AI
coverage set.

The live-capture ledger and manifest were also expanded from a small priority
set to explicit rows for every gym leader. Most rows are still `UNTOUCHED`;
this is intentional evidence hygiene, not a claim that live testing happened.

Follow-up verification added and then tightened
`tools/audit/check_gym_leader_wiring.py`. This checks all 16 gym leader map
scripts against the trainer data they are supposed to launch: object event ->
leader script -> `loadtrainer` class/id -> `startbattle` ->
`reloadmapafterbattle` -> beat-event set. It also cross-checks the same leader
against `data/trainers/leaders.asm`, `data/trainers/ai_tiers.asm`,
`constants/trainer_constants.asm`, and `data/trainers/parties.asm`.

The same audit now validates each gym leader party row down to crash-relevant
tokens: one party entry, `TRAINERTYPE_ITEM_MOVES`, 1-6 mons, levels in 1-100,
real species constants, real non-`NO_ITEM` held item constants, and real
non-`NO_MOVE` move constants.

The audit also verifies `data/trainers/party_pointers.asm`: each leader class
must map through `TrainerGroups` to the expected party group. That matters
because `loadtrainer FALKNER, FALKNER1` reaches `FalknerGroup` by class-indexed
pointer lookup, not by label name in the map script.

The latest tightening verifies the other class-indexed trainer support tables
too: class names, trainer attributes, DVs, pic pointers, palette paths, and
encounter music. For every gym leader, the audit checks that the class name is
`LEADER`, the attributes include a positive base reward plus `AI_BASIC`,
`AI_SMART`, `CONTEXT_USE`, and `SWITCH_SOMETIMES`, DVs are in nybble range,
the expected trainer pic and palette are wired, and encounter music has a real
music constant.

Continuation tightening now verifies badge/reward aftermath too. For 15
leaders, the leader script must set the expected badge flag after battle. Clair
is intentionally special: `BlackthornGymClairScript` must branch on
`ENGINE_RISINGBADGE`, and `DragonsDenB1FDragonFangScript` must award the
RisingBadge after the Dragon Fang route. The same check also verifies gym
statue badge-state wiring where the map has a statue, plus one-time reward
gates for Johto `TM_VOUCHER` rewards and the Kanto Erika/Janine TM rewards.

Further tightening now checks battle-resource rows behind the tokens. Gym
leader species must resolve to real `BaseData` rows and `PokemonNames` rows;
gym leader moves must resolve to `Moves`, `MoveNames`, and `MoveDescriptions`
rows; held items and leader reward items must resolve to item attribute, name,
and description rows. This is still static source proof, but it covers the
data tables the battle and reward code actually read.

The newest tightening checks map-resource registration. Each gym leader map
must be included by `data/maps/scripts.asm`, have a matching `map_const`,
`map_attributes` row, `MapGroup` row, and block resource, use `MUSIC_GYM` with
the no-phone gym flag, expose map script/event labels, and place exactly one
leader object event inside the declared map dimensions. Visibility events on
leader objects must resolve to real event constants.

Continuation tightening now checks gym-trainer sweep events. When a leader
script sets subordinate `EVENT_BEAT_*` flags after victory, each swept event
must resolve to a real trainer object/script somewhere in `maps/`, and the
trainer class/id used by that object must be declared. This handles normal
`trainer` macro objects, Janine's custom disguised-trainer scripts, and Clair's
cross-floor Blackthorn Gym sweep.

A scratch battery-save probe also tested whether existing `.sav` files could
unblock live captures. Only `pokegold.sav` loaded as a real game save when
copied to PyBoy's expected `.gbc.ram` name, and it resumed on Route 29 with one
level-11 party mon. That is useful as a possible early-game bootstrap, but it
is not a gym-leader decision state.

## Commands Run

```powershell
python tools\audit\check_ai_tiers.py
python tools\audit\check_boss_items_present.py
python tools\audit\check_boss_moves_complete.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_cheap_difficulty.py
python -m py_compile tools\audit\check_gym_leader_wiring.py
python tools\audit\check_gym_leader_wiring.py
python tools\audit\check_release_smoke.py
python tools\audit\check_battle_math_safety.py
python tools\trace\boss_ai_trace_batch.py
python tools\trace\boss_ai_trace_batch.py --execute --only morty
python tools\audit\check_boss_ai_live_capture_ledger.py
python scripts\generate_dev_index.py --rom pokegold
python tools\audit\check_docs_navigation.py
git diff --check
bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'
```

## Results

```text
check_ai_tiers.py:
  PASS
  Required boss entries covered: 43
  Tier counts: AI_TIER_EARLY=9, AI_TIER_MID=9, AI_TIER_LATE=25
  Adaptive lead entries covered: 17

check_boss_items_present.py:
  PASS
  entries=43
  mons=206
  items_present=true

check_boss_moves_complete.py:
  PASS
  entries=43
  mons=206
  no_no_move_tokens=true

check_boss_ai_memory_budget.py:
  PASS
  Enemy Trainers: normal=0e:4000-7dd1, trace=0e:4000-7ec0
  Boss AI WRAM: normal_used=75, normal_free=65, trace_used=94, trace_free=46

normal Gold/Silver build:
  PASS
  pokegold.gbc and pokesilver.gbc relinked cleanly with the documented WSL RGBDS route

check_cheap_difficulty.py:
  PASS
  Target entries checked: 43
  Target mons checked: 206
  Johto gym peak levels: 11, 17, 21, 26, 32, 34, 33, 39

check_gym_leader_wiring.py:
  PASS
  gym_leaders=16
  map_scripts=true
  object_events=true
  trainer_group_pointers=true
  leader_tables=true
  ai_tiers=true
  party_groups=true
  party_tokens=true
  class_support_tables=true
  badge_reward_aftermath=true
  battle_resources=true
  map_resources=true
  gym_trainer_sweep=true

scratch save probe:
  pokegold.sav loaded when copied to PyBoy's `.gbc.ram` name
  location: map 18:03 / Route 29
  party: one level-11 mon
  result: not usable as a current gym-leader live-capture state

trace batch dry-run:
  Morty: READY
  Jasmine: READY
  Other 14 gym-leader live rows: MISSING_STATE until real decision states exist
  Koga: MISSING_STATE
  Champion Lance: MISSING_STATE
  Shared switch-loop: MISSING_STATE
  summary: ran=0 skipped=19 missing_state=17 invalid_state=0

trace batch execution:
  Morty: RUN
  wrote audit/boss_ai_trace/morty_live.txt
  Jasmine: RUN
  wrote audit/boss_ai_trace/jasmine_live.txt

live capture ledger:
  PASS
  Morty: FINISHED
  Jasmine: FINISHED
  Other 14 gym leaders: UNTOUCHED
  Koga: UNTOUCHED
  Champion Lance: UNTOUCHED
  Shared switch-loop: UNTOUCHED

check_docs_navigation.py:
  PASS
  Trace capture docs match pinned manifest basis

git diff --check:
  PASS
  CRLF warnings only for pre-existing/generated text surfaces
```

## Gym Leader Status

| Leader | Tier | Adaptive lead | Source/audit status | Live status |
| --- | --- | --- | --- | --- |
| Falkner | `AI_TIER_EARLY` | no | `PASS` | `MISSING_STATE`; `audit/boss_ai_trace/falkner_live.txt` |
| Bugsy | `AI_TIER_EARLY` | no | `PASS` | `MISSING_STATE`; `audit/boss_ai_trace/bugsy_live.txt` |
| Whitney | `AI_TIER_EARLY` | no | `PASS` | `MISSING_STATE`; `audit/boss_ai_trace/whitney_live.txt` |
| Morty | `AI_TIER_MID` | no | `PASS` | `FINISHED`; `audit/boss_ai_trace/morty_live.txt` |
| Chuck | `AI_TIER_MID` | yes | `PASS` | `MISSING_STATE`; `audit/boss_ai_trace/chuck_live.txt` |
| Jasmine | `AI_TIER_MID` | yes | `PASS` | `FINISHED`; `audit/boss_ai_trace/jasmine_live.txt`; state `.local/tmp/boss_state_factory/jasmine_chosen_frame_5060.state` |
| Pryce | `AI_TIER_LATE` | yes | `PASS` | `MISSING_STATE`; `audit/boss_ai_trace/pryce_live.txt` |
| Clair | `AI_TIER_LATE` | yes | `PASS` | `MISSING_STATE`; `audit/boss_ai_trace/clair_live.txt` |
| Brock | `AI_TIER_LATE` | yes | `PASS` | `MISSING_STATE`; `audit/boss_ai_trace/brock_live.txt` |
| Misty | `AI_TIER_LATE` | yes | `PASS` | `MISSING_STATE`; `audit/boss_ai_trace/misty_live.txt` |
| Lt. Surge | `AI_TIER_LATE` | yes | `PASS` | `MISSING_STATE`; `audit/boss_ai_trace/lt_surge_live.txt` |
| Erika | `AI_TIER_LATE` | yes | `PASS` | `MISSING_STATE`; `audit/boss_ai_trace/erika_live.txt` |
| Janine | `AI_TIER_LATE` | yes | `PASS` | `MISSING_STATE`; `audit/boss_ai_trace/janine_live.txt` |
| Sabrina | `AI_TIER_LATE` | yes | `PASS` | `MISSING_STATE`; `audit/boss_ai_trace/sabrina_live.txt` |
| Blaine | `AI_TIER_LATE` | yes | `PASS` | `MISSING_STATE`; `audit/boss_ai_trace/blaine_live.txt` |
| Blue | `AI_TIER_LATE` | yes | `PASS` | `MISSING_STATE`; `audit/boss_ai_trace/blue_live.txt` |

## Do Not Overclaim

`PASS` in the table means the current source and audit suite say the leader is
covered by the Boss AI tiering/party legality/invariant checks. It does not
mean a live emulator capture exists.

The current hard live-proof standard is still:

- real boss-position or defensible debugger-position context
- manifest-matching trace ROM/symbol hashes
- nonzero chosen-move trace fields
- output saved in the matching `*_live.txt`
- ledger/manifest status updated only after the capture exists

## Next Best Work

Get real decision-point save-states in gym order if the goal is complete
all-leader live coverage. The current `pokegold.sav` can bootstrap the
factory-driven Jasmine route through real map setup. If prioritizing risk
instead of route order, Clair is now the most valuable next gym capture because
it covers Spikes, public status fail gates, phazing, and public +2 setup
denial after Jasmine.
