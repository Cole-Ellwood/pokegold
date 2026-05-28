# Romhack Boss AI Implementation Roadmap

Status: 2026-05-17 historical roadmap — substantial boss AI work has shipped
on this branch since (see `git log codex/cleanup-gsc-rebalance-split` and the
`claude/boss-ai-rom-expansion` branch tip). Read the "Goal For The Next
Session" framing below as a snapshot of where the planning was at the time,
not as current next-up work. For current state, see `git log` and the
boss-AI docs under `docs/agent_navigation/subsystems/boss_ai_logic.md` and
`docs/boss_ai_spec.md`.

Created: 2026-05-17.
Workspace: `C:\Users\lolno\Downloads\pokemon gold hack`.

## Goal For The Next Session (as of 2026-05-17 — see Status above)

Implement romhack-aware tiered trainer AI safely:

- Ordinary trainers keep base-game planning strength.
- All AI paths, including ordinary trainers, must understand the romhack's
  mechanics well enough to avoid basic legality/type/item/passive mistakes.
- Only selected bosses get upgraded strategic AI.
- Boss tiers must differ by concrete capabilities, not by vague "harder"
  labels.
- Claims of improvement must come from local source, fixtures, debugger output,
  ROM materialization, or live traces. Vanilla GSC replay scores are not
  validation for romhack Boss AI.

Suggested active goal text:

```text
Implement and validate romhack-aware tiered Boss AI. Keep ordinary trainers on
base-level planning while making shared AI mechanics-correct. Enforce the
intended boss whitelist and exact tier map, make tier differences observable in
policy gates/scoring/tests, fix confirmed Boss AI policy bugs with debugger
evidence, and validate through builds, audits, generated scenarios, ROM
materialization, and trace/live proof. Do not claim improvement from vanilla GSC
replay results.
```

## First Read Order

Read these before changing code:

1. The repo instructions supplied in the thread. If an `AGENTS.md` file exists
   in the fresh session, read it too.
2. `docs/pokemon_mastery/romhack_boss_ai_implementation_roadmap.md`
3. `docs/pokemon_mastery/policy_cards/romhack_mechanics_firewall.md`
4. `docs/pokemon_mastery/romhack_boss_ai_mastery.md`
5. `docs/agent_navigation/hack_mechanics_reference.md`
6. `docs/mechanics_changes_from_base.md`
7. `docs/pokemon_mastery/romhack_deltas/spikes_and_rapid_spin.md`
8. `docs/agent_navigation/subsystems/boss_ai_logic.md`
9. `docs/agent_navigation/subsystems/boss_ai_trace.md`
10. `docs/boss_ai_debugger_changed_ai_suite.md`
11. `docs/boss_ai_debugger_decision_trace.md`
12. `docs/pokemon_mastery/runs/2026-05-17_battle_debugger_bug_hunt.md`

Do not open old vanilla GSC reviews or quick tests as validation material for
romhack Boss AI. They may provide strategy vocabulary only after the local
mechanics are checked.

## Non-Negotiable Design Split

Mechanics correctness is shared by all AI.

Strategic strength is gated behind boss tiers.

This means:

- Base trainers should use the local type chart, local move categories,
  three-layer Spikes cap, Rapid Spin clearing all layers, visible held item
  legality/immunity, and relevant type passive effects when those determine
  whether a move works.
- Base trainers should not become route-aware planners, preservation experts,
  or branch-punish engines.
- Boss trainers get the strategic overlay: route conversion, resource
  preservation, controlled sacks, scouting, branch punishment, hazard loops,
  setup/recovery timing, and wincon play.

If a rule prevents a mechanically impossible or obviously failed move, it
belongs in shared/base-safe mechanics. If a rule chooses a better multi-turn
line among legal moves, it belongs behind boss tiers.

## Intended Tier Map

Use static trainer class/id mappings, not live badge checks, unless a future
requirement proves badge-based behavior is needed. Static trainer IDs are easier
to audit and match story progression.

### Base

All unmapped trainers:

- ordinary route trainers;
- ordinary Rocket Grunts;
- any trainer not explicitly selected as a boss.

Base means base-level planning, not vanilla-GSC mechanics.

### Early Boss AI

Early bosses should avoid obvious blunders and use local mechanics correctly,
but should not feel like endgame planners.

Expected entries:

- `FALKNER, FALKNER1`
- `BUGSY, BUGSY1`
- `WHITNEY, WHITNEY1`
- `RIVAL1, RIVAL1_1_CHIKORITA`
- `RIVAL1, RIVAL1_1_CYNDAQUIL`
- `RIVAL1, RIVAL1_1_TOTODILE`
- `RIVAL1, RIVAL1_2_CHIKORITA`
- `RIVAL1, RIVAL1_2_CYNDAQUIL`
- `RIVAL1, RIVAL1_2_TOTODILE`

Behavior contract:

- mechanics-correct damaging and status choices;
- obvious utility only;
- no multi-turn lookahead;
- no strong proactive preservation;
- low scouting/prediction;
- still allowed to make early-game strategic mistakes.

### Mid Boss AI

Mid bosses start playing routes. They should look prepared and observant, but
should not use the full late-game wincon engine.

Expected entries:

- `MORTY, MORTY1`
- `CHUCK, CHUCK1`
- `JASMINE, JASMINE1`
- `PRYCE, PRYCE1`
- `EXECUTIVEM, EXECUTIVEM_1`
- `EXECUTIVEM, EXECUTIVEM_2`
- `EXECUTIVEM, EXECUTIVEM_3`
- `EXECUTIVEM, EXECUTIVEM_4`
- `EXECUTIVEF, EXECUTIVEF_1`
- `EXECUTIVEF, EXECUTIVEF_2`
- `RIVAL1, RIVAL1_3_CHIKORITA`
- `RIVAL1, RIVAL1_3_CYNDAQUIL`
- `RIVAL1, RIVAL1_3_TOTODILE`
- `RIVAL1, RIVAL1_4_CHIKORITA`
- `RIVAL1, RIVAL1_4_CYNDAQUIL`
- `RIVAL1, RIVAL1_4_TOTODILE`

Behavior contract:

- short lookahead;
- route candidate inclusion: active converter, preservation/recovery/sack line,
  branch-covering line;
- recognizes revealed/public Rapid Spin, setup, revenge threats, and status
  absorbers;
- proactive switches only when the public route is clear;
- controlled sacks when the current piece has finished its job;
- moderate scout and plausible-risk handling;
- no hidden player team, hidden move, hidden item, hidden PP, or current-turn
  player-input reads outside quarantined Haki.

### Late Boss AI

Late bosses should play win conditions and resources.

Expected entries:

- `CLAIR, CLAIR1`
- `WILL, WILL1`
- `KOGA, KOGA1`
- `BRUNO, BRUNO1`
- `KAREN, KAREN1`
- `CHAMPION, LANCE`
- `BROCK, BROCK1`
- `MISTY, MISTY1`
- `LT_SURGE, LT_SURGE1`
- `ERIKA, ERIKA1`
- `JANINE, JANINE1`
- `SABRINA, SABRINA1`
- `BLAINE, BLAINE1`
- `BLUE, BLUE1`
- `RED, RED1`
- `RIVAL1, RIVAL1_5_CHIKORITA`
- `RIVAL1, RIVAL1_5_CYNDAQUIL`
- `RIVAL1, RIVAL1_5_TOTODILE`
- `RIVAL2, RIVAL2_1_CHIKORITA`
- `RIVAL2, RIVAL2_1_CYNDAQUIL`
- `RIVAL2, RIVAL2_1_TOTODILE`
- `RIVAL2, RIVAL2_2_CHIKORITA`
- `RIVAL2, RIVAL2_2_CYNDAQUIL`
- `RIVAL2, RIVAL2_2_TOTODILE`

Behavior contract:

- deeper lookahead and multi-turn projection;
- strong hazard economy: 3-layer Spikes, phazing pressure, Rapid Spin denial;
- strong resource identity: ace, wallbreaker, spinner, phazer, status absorber,
  sack piece, cleaner;
- branch coverage against the highest-incentive public player line;
- proactive preservation and cash-out timing;
- late scout/prediction tools;
- ace timing and cleanup planning;
- still public-info only, except explicitly quarantined Haki branches.

### Current Source Mismatch To Fix First

As of this roadmap, `data/trainers/ai_tiers.asm` has Rocket Executives mapped
to `AI_TIER_MID`, but `PRYCE, PRYCE1` is still `AI_TIER_LATE`. The intended
policy above says Pryce is mid because leaders 4-7 are mid and Clair is the
first Johto late boss.

First implementation patch:

1. Change `PRYCE, PRYCE1` from `AI_TIER_LATE` to `AI_TIER_MID`.
2. Strengthen `tools/audit/check_ai_tiers.py` so it asserts the exact expected
   tier for every boss pair, not merely nonzero coverage.
3. Keep the unexpected-entry guard so ordinary trainers cannot silently become
   Boss AI.

## Existing Source Anchors

Core activation and tiering:

- `constants/trainer_data_constants.asm`: tier constants.
- `data/trainers/ai_tiers.asm`: `BossAITierMap`, `BossAITierRampMap`,
  `AdaptiveLeadMap`.
- `engine/battle/read_trainer_attributes.asm`: `LoadBossAITier`,
  `ClearBossAIState`.
- `engine/battle/ai/move.asm`: base path vs `BossAI_ApplyMoveModel` and
  `BossAI_SelectMove`.
- `engine/battle/ai/items.asm`: base switch/item path vs
  `BossAI_TrySwitch`.

Boss AI implementation:

- `engine/battle/ai/boss_platform.asm`: public-info memory, type helpers,
  score helpers, caches, revealed move tracking.
- `engine/battle/ai/boss_policy_move.asm`: move scoring overlay, tier weights,
  role bias, lookahead, plausible-risk/scout policy, plan selection.
- `engine/battle/ai/boss_policy_switch.asm`: boss switch logic, switch
  confidence, risk refinement, ace timing.
- `engine/battle/ai/boss_thunks.asm`: HL-preserving thunks into base AI scoring
  helpers. Be careful with register preservation here.
- `engine/battle/ai/scoring.asm`: legacy/base Gen 2 AI scoring. Boss AI runs
  after base scoring; base trainers use this path directly.
- `engine/battle/ai/redundant.asm`: redundancy checks, including Spikes cap.

Mechanics source:

- `data/types/type_matchups.asm`
- `constants/type_constants.asm`
- `data/moves/moves.asm`
- `data/moves/effects.asm`
- `data/moves/effects_priorities.asm`
- `data/moves/contact_flags.asm`
- `engine/battle/effect_commands.asm`
- `engine/battle/type_passive_damage_mods.asm`
- `engine/battle/late_gen_held_items.asm`
- `engine/battle/move_effects/spikes.asm`
- `engine/battle/move_effects/rapid_spin.asm`
- `engine/battle/core.asm`
- `data/trainers/parties.asm`

Generated references:

- `docs/agent_navigation/hack_mechanics_reference.md`
- `docs/generated/dev_index.md`
- `docs/agent_navigation/subsystems/boss_ai_logic.md`
- `docs/agent_navigation/subsystems/boss_ai_trace.md`

Regenerate generated references after relevant source/build changes:

```powershell
python scripts\generate_dev_index.py --rom pokegold --out docs\generated\dev_index.md
python scripts\generate_boss_ai_index.py
```

## Current Known Findings

Already fixed in current local work:

- `AICheckPlayerQuarterHP_HL` and `AICheckPlayerHalfHP_HL` in
  `engine/battle/ai/boss_thunks.asm` now preserve `bc/de`.
- The previous bug was real: player HP fraction checks could corrupt Boss AI
  lookahead accumulators.
- Air Balloon quick oracle/runtime smoke paths were updated before this
  roadmap; quick damage gates passed in the prior session.
- Rocket Executives were added to the boss tier map as `AI_TIER_MID`.

Still open:

- Pryce is currently late in source but should be mid by the intended tier map.
- `tools/audit/check_ai_tiers.py` currently proves required coverage and
  unexpected-entry rejection, but the next session should make it assert exact
  expected tiers.
- Changed-AI run `audit/boss_ai_debugger/runs/20260517_113914_changed_ai`
  still had Boss AI policy/mirror issues:
  - 24 scenarios.
  - 16 pass, 3 acceptable-top, 5 bad-roll.
  - trace replay 19/19.
  - metamorphic 30/30.
  - ROM score materialization checked 3, score byte matches 1, selector top
    matches 2, contribution mismatches 2.
- Remaining policy anchors:
  - `generated_setup_heal_1_00000_setup_once_in_real_window`: acceptable-top,
    but broad lookahead discourages all four candidates.
  - `generated_prediction_mix_1_00000_coverage_into_named_receiver`: Toxic/status
    or obvious active line can be over-preferred instead of branch coverage.
  - `generated_spikes_spin_1_00000`: policy pass; keep as capped-Spikes
    regression anchor.
  - `generated_spikes_spin_1_00001`: policy pass but Python/ROM score bytes can
    differ; keep as mirror-alignment anchor.

Anchor scenario file:

```text
audit/boss_ai_debugger/runs/20260517_113914_changed_ai/scenarios.jsonl
```

## Unified Debugger: What It Is For

`python -m tools.debugger` is the broad triage and investigation front door for
the whole ROM. Use it when a change touches multiple systems or when you are
not sure which audits/traces matter.

Important commands:

```powershell
python -m tools.debugger --help
python -m tools.debugger triage --changed-file engine\battle\ai\boss_policy_move.asm --symptom "boss ai move scoring route budget hazards items" --json
python -m tools.debugger gate --changed-file engine\battle\ai\boss_policy_move.asm --symptom "boss ai move scoring route budget hazards items" --max-commands 10 --json
python -m tools.debugger gate --changed-file engine\battle\ai\boss_policy_move.asm --symptom "boss ai move scoring route budget hazards items" --execute --max-commands 10 --timeout-seconds 120 --json
python -m tools.debugger investigate --changed-file engine\battle\ai\boss_policy_move.asm --symptom "lookahead status overprefer route budget" --json
```

Workflow:

1. Run `triage` with changed files and symptom before broad debugging.
2. Run `gate` without `--execute` to see the proposed command set.
3. Run `gate --execute` when the proposed set is relevant.
4. Use `investigate`, `slice`, `provenance`, `watch`, `expect`, or
   `suggest-tests` only after a concrete symptom or failing case exists.
5. Persist any confirmed lesson in a doc or test, not only in chat.

Do not use the unified debugger as a substitute for the specialized Boss AI
debugger when the question is move/switch decision quality.

## Boss AI Debugger: What It Is For

`python -m tools.boss_ai_debugger` is the decision-quality harness. It generates
source-derived scenarios, scores expectations, creates review queues, compares
Python mirrors to ROM traces, materializes scores in the trace ROM, and stores
reproducible runs.

Start here:

```powershell
python -m tools.boss_ai_debugger --help
python -m tools.boss_ai_debugger run-suite --help
python -m tools.boss_ai_debugger generate --help
python -m tools.boss_ai_debugger decision-trace --help
python -m tools.boss_ai_debugger rom-score-materialize --help
```

Core workflow for AI behavior changes:

1. Generate or reuse a focused scenario packet.
2. Inspect Python decision waterfall if needed.
3. Run a changed-AI suite.
4. ROM-materialize high-value anchors before claiming behavior changed.
5. Compare before/after metrics and mismatches.
6. Add a fixture/audit if the behavior should be permanently protected.

Common commands:

```powershell
python -m tools.boss_ai_debugger run-suite --profile changed-ai --count 24 --seed 1 --json
python -m tools.boss_ai_debugger run-suite --profile changed-ai --count 100 --seed 1 --refresh-rom-score-materialization --json
python -m tools.boss_ai_debugger run-suite --profile changed-ai --count 200 --seed 1 --rebuild-roms --refresh-live-traces --refresh-rom-score-materialization --json

python -m tools.boss_ai_debugger decision-trace --scenario audit\boss_ai_debugger\runs\20260517_113914_changed_ai\scenarios.jsonl --scenario-id generated_prediction_mix_1_00000_coverage_into_named_receiver --json

python -m tools.boss_ai_debugger rom-score-materialize --scenarios audit\boss_ai_debugger\runs\20260517_113914_changed_ai\scenarios.jsonl --limit 24 --compare-fast-score --json-out .local\tmp\boss_ai_debugger\rom_score_after_patch.json --json

python -m tools.boss_ai_debugger diff --scenarios audit\boss_ai_debugger\runs\20260517_113914_changed_ai\scenarios.jsonl --trace-dir audit\boss_ai_trace --json
```

Scenario families available now:

- `selector_edges`
- `spikes_spin`
- `mastery_policy`
- `switch_sack`
- `setup_heal`
- `prediction_mix`
- `support_handoff`
- `cashout_board_delta`
- `all`

Example:

```powershell
python -m tools.boss_ai_debugger generate --family spikes_spin --count 100 --seed 7 --out .local\tmp\boss_ai_debugger\spikes_spin_probe.jsonl
```

## Trace ROM And Live Proof Workflow

Use this when source-level tests are not enough and you need actual ROM
decision proof.

Normal ROM build:

```powershell
wsl make pokegold.gbc pokesilver.gbc
```

Trace ROM rebuild:

```powershell
wsl bash -lc 'rgbasm -Weverything -Wtruncation=1 -Q8 -P includes.asm -D _GOLD -D BOSS_AI_TRACE -o main_gold_trace.o main.asm && rgbasm -Weverything -Wtruncation=1 -Q8 -P includes.asm -D _GOLD -D BOSS_AI_TRACE -o ram_gold_trace.o ram.asm && rgblink -Weverything -Wtruncation=1 -l layout.link -n pokegold_trace.sym -m pokegold_trace.map -o pokegold_trace.gbc audio_gold.o home_gold.o main_gold_trace.o ram_gold_trace.o data/text/common_gold.o data/maps/map_data_gold.o data/pokemon/egg_moves_gold.o data/pokemon/evos_attacks_gold.o engine/movie/credits_gold.o engine/overworld/events_gold.o gfx/misc_gold.o gfx/sprites_gold.o gfx/tilesets_gold.o data/pokemon/dex_entries_gold.o gfx/pics_gold.o && rgbfix -Weverything -cjsv -k 01 -l 0x33 -m MBC3+TIMER+RAM+BATTERY -r 3 -p 0 -t POKEMON_GLD -i AAUE pokegold_trace.gbc && tools/stadium pokegold_trace.gbc'
```

State factory and trace capture:

```powershell
python tools\trace\boss_ai_state_factory.py --all --update-manifest
python tools\trace\boss_ai_trace_batch.py
python tools\trace\boss_ai_trace_batch.py --execute --only clair
python tools\audit\check_boss_ai_live_capture_ledger.py
```

Pre-choice replay:

```powershell
python tools\trace\boss_ai_trace_batch.py --pre-choice-replay
python tools\trace\boss_ai_trace_batch.py --pre-choice-replay --execute
python tools\audit\check_boss_ai_pre_choice_replay.py
```

Current manifest support covers the 16 gym leaders, Koga, Champion Lance, and a
shared switch-loop fixture. The next implementation should add Rocket Executive
trace routes if live proof is needed for executives. Use real map scripts as
source truth:

- `maps/RadioTower4F.asm`
- `maps/RadioTower5F.asm`
- `maps/TeamRocketBaseB2F.asm`
- `maps/TeamRocketBaseB3F.asm`

## Implementation Plan

### Phase 0: Orient And Protect User Work

Run:

```powershell
Get-Location
git status --short
git diff -- data\trainers\ai_tiers.asm tools\audit\check_ai_tiers.py engine\battle\ai\boss_policy_move.asm engine\battle\ai\boss_policy_switch.asm engine\battle\ai\boss_platform.asm engine\battle\ai\boss_thunks.asm engine\battle\ai\scoring.asm
```

Assume the worktree is dirty. Do not revert unrelated changes.

Baseline verification floor:

```powershell
python tools\audit\check_ai_tiers.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_ai_policy_contract.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_boss_ai_index_lines.py
python tools\audit\check_docs_navigation.py
```

If a generated doc is stale after a successful build, regenerate through its
script, do not hand-edit generated rows.

### Phase 1: Make Tier Scope Exact

Edit:

- `data/trainers/ai_tiers.asm`
- `tools/audit/check_ai_tiers.py`
- a durable doc, probably `docs/pokemon_mastery/romhack_boss_ai_tier_contract.md`

Required changes:

1. Move `PRYCE, PRYCE1` to `AI_TIER_MID`.
2. Keep Rocket Executives mid.
3. Keep Clair late.
4. Keep Kanto leaders, E4/Lance, Red late.
5. Keep Silver scaling by trainer ID:
   - `RIVAL1_1_*`, `RIVAL1_2_*`: early.
   - `RIVAL1_3_*`, `RIVAL1_4_*`: mid.
   - `RIVAL1_5_*`, `RIVAL2_1_*`, `RIVAL2_2_*`: late.
6. Update `check_ai_tiers.py` to assert exact expected tier per pair.
7. Keep failing on unexpected `BossAITierMap` entries.

Validation:

```powershell
python tools\audit\check_ai_tiers.py
python tools\audit\check_boss_ai_gating.py
wsl make pokegold.gbc pokesilver.gbc
python scripts\generate_dev_index.py --rom pokegold --out docs\generated\dev_index.md
python scripts\generate_boss_ai_index.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_boss_ai_index_lines.py
python tools\audit\check_docs_navigation.py
```

### Phase 2: Base AI Mechanics Correctness Audit

Purpose: normal trainers should not be smarter, but they should not be wrong
about the romhack.

Existing evidence:

- Legacy `AI_Types` and `AI_Status` call `BattleCheckTypeMatchup`, so basic
  changed type effectiveness flows through local mechanics.
- `engine/battle/ai/redundant.asm` treats Spikes as redundant only at three
  layers.
- `AI_Smart_RapidSpin` notices Spikes layers on the AI side.

Audit these shared/base paths:

- changed type chart cases:
  - Poison into Normal is super-effective;
  - Ghost into Steel is no-effect;
  - Dark into Steel is neutral;
  - Grass into Flying is neutral;
  - Ground into Ghost is no-effect;
  - Psychic into Poison is neutral.
- status and type immunity:
  - status moves using type matchup do not ignore local immunities;
  - Dark status shield is not blindly over/under-scored if visible to AI path.
- three-layer Spikes:
  - fourth Spikes click is blocked/redundant;
  - Rapid Spin clears all layers.
- visible item legality:
  - Assault Vest blocks support moves for the holder;
  - Choice lock does not score illegal alternatives for the locked holder;
  - Air Balloon Ground immunity is respected when visible/relevant;
  - Rocky Helmet/contact and Poison contact retaliation are not treated as free.
- local category:
  - type-based physical/special split;
  - Outrage exception.

Possible output:

- Add or extend `tools/audit/check_base_ai_mechanics_correctness.py`.
- Add fixtures under `tools/damage_debugger/` or `tools/boss_ai_debugger/`
  only where runtime behavior is needed.
- Fix only confirmed mechanics mistakes in base/shared code. Do not add
  boss-style route planning to base trainers.

Validation commands:

```powershell
python -m tools.damage_debugger.oracle
python -m tools.damage_debugger.clobber_smoke
python -m tools.damage_debugger.fuzz --self-check-workers=2
python -m tools.damage_debugger.hazard_smoke
python tools\audit\check_farcall_a_clobber.py
python tools\audit\check_farcall_hl_clobber.py
python tools\audit\check_cross_bank_call.py
```

### Phase 3: Make Tier Differences Observable

Do not implement three copied AIs. Use one shared scorer with tier-weighted
tables and gates.

Existing knobs:

- `BossAITierWeights` in `engine/battle/ai/boss_policy_move.asm`.
- `BossAITierRampMap` in `data/trainers/ai_tiers.asm`.
- `BOSS_AI_LOOKAHEAD_ENABLE_TIER_MIN` in `constants/battle_constants.asm`.
- `BossAI_GetSwitchThreshold` in `engine/battle/ai/boss_policy_switch.asm`.
- `BossAI_GetTierPlausibleRiskWeight`.
- `BossAI_GetScoutRollThreshold`.
- `BossAI_ApplyMultiTurnProjection`.
- late-only plan confidence and ace timing.

Implement tier distinction by capabilities:

- Early:
  - no lookahead;
  - lower route/tempo/status weights;
  - high switch threshold;
  - weak plausible-risk/scout;
  - blocks mechanical blunders.
- Mid:
  - short lookahead;
  - route candidate inclusion;
  - moderate preservation/sack/switch;
  - public branch punish when evidence is clear.
- Late:
  - deeper lookahead;
  - stronger route, denial, preservation, and branch coverage;
  - lower switch threshold when preservation is correct;
  - stronger plausible-risk/scout;
  - ace/wincon timing.

Add fixtures proving this on the same state:

- capped Spikes state: base/early block fourth Spikes; mid/late also choose the
  route-progress alternative.
- 0-layer Spikes with safe spinblock: mid/late value Spikes more than early.
- setup window: early may hit, mid sets up only if route-changing, late also
  prices the future receiver/reset branch.
- preservation switch: early often stays, mid preserves sometimes, late
  preserves the unique future job.
- branch coverage: late is more willing than mid to choose receiver coverage
  when public probability/payoff justifies it.

These should be debugger scenarios, not prose claims.

### Phase 4: Fix Current Policy Anchors One At A Time

Use the anchor scenario file:

```text
audit/boss_ai_debugger/runs/20260517_113914_changed_ai/scenarios.jsonl
```

Start with one failure class only. Recommended order:

1. Broad lookahead penalty in
   `generated_setup_heal_1_00000_setup_once_in_real_window`.
2. Toxic/status or obvious-line over-preference in
   `generated_prediction_mix_1_00000_coverage_into_named_receiver`.
3. Python/ROM score-byte alignment in `generated_spikes_spin_1_00001`.

Before changing a rule, write:

```text
Hypothesis:
Evidence that would confirm it:
Evidence that would reject it:
Scenarios explained:
Source hook:
Expected metric:
```

Then change exactly one thing. After every change:

```powershell
python -m tools.boss_ai_debugger decision-trace --scenario audit\boss_ai_debugger\runs\20260517_113914_changed_ai\scenarios.jsonl --scenario-id <anchor_id> --json
python -m tools.boss_ai_debugger rom-score-materialize --scenarios audit\boss_ai_debugger\runs\20260517_113914_changed_ai\scenarios.jsonl --limit 24 --compare-fast-score --json-out .local\tmp\boss_ai_debugger\anchor_after_patch.json --json
python -m tools.boss_ai_debugger run-suite --profile changed-ai --count 24 --seed 1 --refresh-rom-score-materialization --json
```

Do not claim a fix from the Python mirror alone when ROM materialization
disagrees.

### Phase 5: Boss-Specific Role Data

Bosses should feel different because their teams, moves, items, and roles are
different, not because of arbitrary scripts.

Source first:

- `data/trainers/parties.asm`
- `data/trainers/dvs.asm`
- `data/pokemon/base_stats/*.asm`
- `data/pokemon/evos_attacks.asm`
- `data/moves/moves.asm`
- `engine/battle/late_gen_held_items.asm`

Map each boss to role packages:

- lead pressure;
- hazard setter/remover;
- phazer;
- setup sweeper;
- wallbreaker;
- status spreader;
- status absorber;
- spinner/spinblocker;
- defensive pivot;
- ace/cleaner;
- controlled sack or Explosion cash-out.

Persist the role map in a source-derived doc or table. Do not teach from
vanilla Smogon species roles without checking local stats, type, moves, and
items.

### Phase 6: Rocket Executive And Silver Proof

Rocket Executives:

- They are boss scope.
- The real battles use `EXECUTIVEM_1..4` and `EXECUTIVEF_1..2`.
- Do not map unused `GRUNTM_*` rows named `EXECUTIVE@`.
- Add exact tier audit coverage and, if practical, trace routes for at least
  one hideout executive and one Radio Tower executive.

Silver:

- Use trainer ID scaling, not badge count.
- Add exact audit checks for all starter variants.
- Add at least one generated scenario per Silver tier if the debugger supports
  trainer context.

### Phase 7: Final Verification Floor

For any Boss AI source change, run the narrow floor:

```powershell
python tools\audit\check_ai_tiers.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_ai_policy_contract.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_boss_ai_index_lines.py
python tools\audit\check_docs_navigation.py
python -m tools.boss_ai_debugger run-suite --profile changed-ai --count 24 --seed 1 --refresh-rom-score-materialization --json
wsl make pokegold.gbc pokesilver.gbc
```

For behavior-significant policy changes, expand:

```powershell
python -m tools.boss_ai_debugger run-suite --profile changed-ai --count 200 --seed 1 --rebuild-roms --refresh-live-traces --refresh-rom-score-materialization --json
python tools\audit\check_boss_ai_debugger_done.py --generated-count 200
```

For damage/item/type/passive changes, also run:

```powershell
python -m tools.damage_debugger.oracle
python -m tools.damage_debugger.clobber_smoke
python -m tools.damage_debugger.fuzz --self-check-workers=2
python -m tools.damage_debugger.hazard_smoke
python tools\audit\check_farcall_a_clobber.py
python tools\audit\check_farcall_hl_clobber.py
python tools\audit\check_cross_bank_call.py
```

After successful build or source-line shifts:

```powershell
python scripts\generate_dev_index.py --rom pokegold --out docs\generated\dev_index.md
python scripts\generate_boss_ai_index.py
git diff --check
```

## Metrics To Report

Report metrics separately for these categories:

- base AI mechanics correctness;
- exact boss tier map coverage;
- generated Boss AI scenario quality;
- ROM score materialization agreement;
- selector trace replay;
- live trace proof;
- no-cheat/gating/memory safety.

Do not summarize all of these as one "AI improved" number.

Minimum Boss AI scenario metrics:

- scenario count;
- route classifications: pass, acceptable-top, bad-roll;
- selector top match;
- score byte match;
- contribution mismatch count;
- metamorphic pass count;
- repeated failure tags;
- severe mechanics/state/hidden-info errors.

## Definition Of Done

The implementation goal is not done until:

- ordinary trainers remain unmapped from `BossAITierMap`;
- ordinary trainers are mechanics-correct for the audited local mechanics;
- exact intended tier map is enforced by audit;
- Pryce is mid and Clair is late;
- Rocket Executives are mid and Rocket Grunts remain base;
- Silver scales by static trainer ID;
- tier differences are proven by fixtures or generated scenarios on same-state
  comparisons;
- current known Boss AI anchor failures are fixed or explicitly quarantined with
  evidence;
- no hidden-info/no-cheat audit regression;
- normal Gold/Silver builds pass;
- generated index docs are current;
- Boss AI debugger changed-AI suite is run and summarized;
- any claimed gameplay improvement has ROM materialization or live trace proof.

## What Not To Do

- Do not make all trainers Boss AI.
- Do not make base trainers strategically stronger just to fix mechanics
  correctness.
- Do not duplicate entire AI routines per tier.
- Do not validate romhack Boss AI with vanilla GSC replay cycles.
- Do not hardcode modern Pokemon assumptions.
- Do not teach the AI one-layer Spikes.
- Do not use hidden player party/move/item/PP information.
- Do not expand Haki/oracle behavior while trying to implement ordinary tier
  strength unless the user explicitly asks for that.
- Do not claim a root cause without a concrete missed decision, trace, source
  hook, or materialized scenario.

## Suggested Final Report Template

```text
Implemented:
- ...

Tier map:
- base:
- early:
- mid:
- late:

Base mechanics correctness:
- verified:
- fixed:
- remaining risk:

Boss AI behavior:
- scenarios:
- pass/acceptable/bad:
- ROM score materialization:
- selector trace:

Known anchors:
- setup/heal:
- prediction/status:
- spikes cap:
- spikes spin/mirror:

Verification:
- command: result
- command: result

Files changed:
- ...

Next session:
- ...
```
