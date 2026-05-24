# Damage Oracle and Boss AI Integration Plan - 2026-05-18

Purpose: make the damage oracle and Boss AI scoring debugger easy to use together. A fresh Codex session should be able to implement this plan without reading the chat that produced it.

This is an ergonomics/debugger task, not a gameplay policy change. Do not fix the Noctowl/Peck scoring bug as part of this task unless the user explicitly asks. The goal here is to build the tools that would have made that bug obvious immediately.

Review-grounded constraints:

- Keep the first implementation narrow. Ship the two concrete workflows below before adding general flags.
- Reuse existing Boss AI trace infrastructure instead of building a parallel tracer.
- Treat inner `BossAI_ApplyMoveModel.*` labels as hook targets during real execution, not standalone callable helpers.
- Prefer relational assertions for AI behavior so normal tuning does not break tests just because score bytes moved.

## Context

Current mature tools:

- `tools/damage_debugger/oracle.py` models this hack's actual damage chain, including local type chart changes, integer-flooring order, crit, STAB, weather, badge modifiers, late-gen held items, and type-passive modifiers.
- `tools/damage_debugger/matchup.py` is a quick one-move CLI over the oracle. It already parses source tables for species, moves, types, items, grind presets, and friendly move/item names.
- `tools/boss_ai_debugger` handles Boss AI policy, trace replay, ROM contribution traces, scenario materialization, and selector checks.
- `tools/debugger` is a unified front door/router. Its README explicitly says it does not replace focused subsystem debuggers.

Observed pain:

- A user can ask "what does every Noctowl move do into this exact Drowzee?" but the current easy command is one move at a time.
- Exact save/trainer state requires ad hoc scripting: current HP, exact computed stats, active party slot, trainer DVs, trainer item, move list, type pair, sleep clause state, and score bytes are spread across source tables, WRAM, and the save.
- Damage truth and AI scoring truth are separate. The damage oracle can say `Peck = 8-10` and `Confusion = 4-5`, but the Boss AI score path can still block Peck. The user needs one report that shows both.
- The unified debugger can route to damage and Boss AI tools, but it does not provide a single "damage plus AI score" workflow.

Concrete motivating bug:

- Falkner Noctowl versus a level 13 Drowzee from `pokegold.sav`.
- Damage oracle result with exact stats:
  - Tackle: `3-4`
  - Peck: `8-10`
  - Confusion: `4-5`
  - Hypnosis: `0`
- ROM score path observed:
  - Tackle score `80`
  - Peck score `80`
  - Confusion score `22`
  - Hypnosis score around `21` when sleep is legal, or blocked when sleep clause is active depending on state.
- Treat those score bytes as observed context for the current ROM, not as long-term test contracts.
- Root-cause evidence found separately: `BossAI_ApplyMoveModel.CurrentEnemyMoveDamageRank` can return the move effect byte instead of the computed rank for non-multi-hit moves, making `EFFECT_CONFUSE_HIT` look like a huge damage rank while plain `EFFECT_NORMAL_HIT` moves look like rank 0.

The new tooling should surface this class of mismatch as data, not require manual tracing.

## Target User Experience

Implement these commands or equivalent names. Prefer these names unless local CLI conventions strongly argue otherwise.

### Exact all-move damage

```powershell
python -m tools.damage_debugger.battle_calc `
  --attacker-trainer FALKNER1:NOCTOWL `
  --defender-save pokegold.sav --defender-slot 1 `
  --all-moves
```

Expected plain-text shape:

```text
Falkner Noctowl L14 (Mint Berry) into party slot 1 Drowzee L13

Move       Type      Cat       Damage   Current HP   Notes
Tackle     Normal    Physical  3-4      6-8%         resisted
Peck       Flying    Physical  8-10     16-20%       STAB
Confusion  Psychic   Special   4-5      8-10%        resisted, 10% confuse
Hypnosis   Psychic   Status    0        0%           60% accuracy
```

JSON output should include raw exact inputs to `oracle.BattleInputs`, not only formatted text.

### Exact Boss AI score probe

```powershell
python -m tools.boss_ai_debugger move-score-probe `
  --trainer FALKNER1 `
  --enemy NOCTOWL `
  --player-save pokegold.sav --player-slot 1 `
  --sleep-clause both `
  --json
```

Expected report fields:

- scenario metadata: ROM/sym hashes, trainer, enemy mon, player mon, sleep clause variant.
- move ids/names.
- pre-model scores.
- post-model scores.
- selected move distribution or selector explanation when deterministic sampling is requested.
- score-changing rules from contribution tracing when available.
- evidence mode: `live-route`, `hook-snapshot`, `direct-public-helper`, or `unavailable`.
- helper metrics per move:
  - oracle damage range.
  - AI scored power.
  - AI pressure score.
  - AI damage rank.
  - final score.
  - `wont_pick` boolean.

Phase 1 supports only this trainer-versus-save workflow plus `--json` and `--trace`. Unsupported flags should fail with a clear `NotImplementedError` or user-facing equivalent, not silently do an approximate thing.

### Combined damage plus AI report

```powershell
python -m tools.debugger damage-ai-report `
  --trainer FALKNER1 `
  --enemy NOCTOWL `
  --player-save pokegold.sav --player-slot 1 `
  --sleep-clause both
```

Expected combined table:

```text
Sleep clause: inactive

Move       Damage   AI power   AI rank   Final score   Status
Tackle     3-4      30         0         80            won't pick (Confusion looks stronger to AI)
Peck       8-10     38         0         80            won't pick (Confusion looks stronger to AI)
Confusion  4-5      61         76        22            selectable
Hypnosis   0        0          0         21            selectable

Selector: Hypnosis about 60%, Confusion about 40%
Warning: AI rank disagrees with oracle damage order. Peck does more damage than Confusion but is marked won't pick.
```

This command can internally call the two subsystem modules. It should not duplicate damage math.

## Implementation Strategy

### 1. Refactor shared damage-table parsing out of `matchup.py`

Create `tools/damage_debugger/tables.py`.

Move or wrap these current `matchup.py` concepts:

- `BaseStatsRow`
- `MoveRow`
- species lookup
- move lookup
- type constants
- item lookup
- move display names
- `compute_stat`
- `compute_hp`
- `is_physical_type`
- `_is_physical_move`, including the Outrage category-flip rule
- name normalization helpers

Keep `matchup.py` working exactly as before. Its tests and sample commands must still pass.

Reason: the new all-move calculator should reuse the existing parser, not fork it.

### 2. Add exact Pokemon state readers

Create `tools/damage_debugger/state.py`.

Support these input sources:

- Direct source-table Pokemon: species, level, role/grind, item override.
- Battery save (`.sav`) plus party slot.
- PyBoy save-state (`.state`) plus active side or party slot.
- Trainer party row: trainer id plus species or party index.

Explicitly reject VBA-M `.sgm` files in Phase 1 with a clear error such as `VBA-M .sgm save-states are not supported yet; use .sav or PyBoy .state`. Do not try to read `.sgm` as a battery save.

Avoid hardcoding raw SRAM offsets if possible. Preferred approach for `.sav`:

1. Copy the battery save to a temporary ROM `.ram` file, following existing patterns in `tools/trace/boss_ai_state_factory.py`.
2. Boot/continue with PyBoy using existing trace runtime helpers where practical.
3. Read party WRAM symbols such as `wPartyMon1Species`, `wPartyMon1Level`, `wPartyMon1HP`, `wPartyMon1MaxHP`, `wPartyMon1Attack`, `wPartyMon1Defense`, `wPartyMon1SpclAtk`, `wPartyMon1SpclDef`, `wPartyMon1Moves`, `wPartyMon1Item`.

For save-states, load the state directly and read WRAM symbols.

For `.sav` reads, cache the post-continue PyBoy state under `.local/tmp/damage_debugger/<sav-sha>.state` or equivalent local temp path. Invalidate on battery-save hash and ROM hash. The user may run several all-move and AI probes against the same save; do not pay the full continue boot every time when a safe cache can avoid it.

For trainer party rows, parse:

- `data/trainers/parties.asm`
- `data/trainers/dvs.asm`
- item/move list from the trainer row
- computed stats using the trainer DVs/stat experience rules already used by existing tooling
- existing trainer-party readers where possible: `tools/audit/trainer_parties.py` and `tools/boss_ai_preference/boss_team.py`

Data model suggestion: keep per-Pokemon facts separate from battle-wide context. `oracle.BattleInputs` needs both.

```python
@dataclass(frozen=True)
class ExactPokemonState:
    species: str
    species_id: int
    level: int
    item_id: int
    item_name: str
    moves: tuple[int, int, int, int]
    move_names: tuple[str, str, str, str]
    current_hp: int
    max_hp: int
    atk: int
    defense: int
    speed: int
    sp_atk: int
    sp_def: int
    type1: int
    type2: int
    status: int = 0


@dataclass(frozen=True)
class BattleContext:
    weather: int = WEATHER_NONE
    battle_turn: int = 1  # enemy turn for boss move damage
    johto_badges: int = 0
    kanto_badges: int = 0
    link_mode: int = 0
    sleep_clause_active: bool = False
    attacker_stat_stages: Mapping[str, int] = field(default_factory=dict)
    defender_stat_stages: Mapping[str, int] = field(default_factory=dict)
    player_screens: int = 0
    enemy_screens: int = 0
    attacker_substatus: int = 0
    defender_substatus: int = 0
    revealed_moves: tuple[int, ...] = ()
    metronome_count: int = 0
```

This module should expose stable pure helpers wherever possible, and PyBoy-backed helpers where exact save state is required. The conversion from `(ExactPokemonState, MoveRow, BattleContext)` to `oracle.BattleInputs` must fill every field deliberately: move BP/type/effect, physical/special category, items, evolution flags, crit flag, weather, badges, link mode, battle turn, HP/status-derived type-passive flags, selfdestruct flag, initial damage, and Metronome count.

### 3. Implement `tools.damage_debugger.battle_calc`

The new CLI is a higher-level wrapper over `oracle.predict_damage`.

Rules:

- Never reimplement damage formula outside `oracle.py`.
- For each damaging move, build `BattleInputs` from `ExactPokemonState`.
- For status moves, return zero damage plus accuracy/effect metadata from `MoveRow`.
- Provide `--all-moves`, `--json`, and `--trace`.
- Preserve exact stats in JSON.

Phase 1 accepted invocations:

```text
--attacker-trainer TRAINER_ID[:SPECIES_OR_INDEX]
--defender-save PATH --defender-slot N
--all-moves
--json
--trace

--attacker SPECIES:LEVEL[:role]
--defender SPECIES:LEVEL[:role]
--move MOVE
--json
--trace
```

The source-table single-move path may delegate to the current `matchup.py` implementation so existing behavior stays intact. Defer broad flags such as save-state attacker/defender, trainer defender, manual item overrides, weather overrides, and crit override until there is a second real use case. If those flags are parsed early, make them raise `NotImplementedError` instead of returning partial or guessed data.

### 4. Extend Boss AI ROM contribution tracing with a score probe

Add a `move-score-probe` subcommand to `tools/boss_ai_debugger/__main__.py` and implement it by extending `tools/boss_ai_debugger/rom_contribution_trace.py`. Do not create a parallel tracer unless reuse proves impossible.

Goal: materialize a battle state in PyBoy, run the actual ROM Boss AI scoring path, and return final score bytes plus diagnostics.

Use existing code first:

- symbol parsing from `tools.trace.runtime`
- move names from `tools.trace.boss_ai_trace_capture`
- hook registration, candidate boundaries, score helper events, predicate branch events, and public input snapshots from `tools.boss_ai_debugger.rom_contribution_trace`
- trainer-party parsing from `tools/audit/trainer_parties.py` and `tools/boss_ai_preference/boss_team.py`
- DVs/stat computation plumbing added only where the existing trainer-party readers do not already provide it

Critical implementation constraint: direct-call mode is unavailable for the inner labels under `BossAI_ApplyMoveModel`.

These labels are children of the parent routine, depend on parent-frame setup, and should be treated as hook targets only:

- `BossAI_ApplyMoveModel.CurrentEnemyMoveDamageRank`
- `BossAI_ApplyMoveModel.CurrentMoveCanBeDamageDominated`
- `BossAI_ApplyMoveModel.HasDominatingDamagingMove`
- `BossAI_ApplyMoveModel.HasMeaningfullyBetterDamagingMove`

Capture their register and relevant WRAM state at entry/exit while the real `ScoreMove` loop is running. The parent prelude sets up caches and context such as `ResetTurnCaches`, `SelectPlanIfNeeded`, `ComputePlayerPlausibleTypeMask`, `wEnemyMoveStruct`, `wTypeMatchup`, and score pointers. A synthetic direct call to the inner labels will not be trusted.

The two public helpers may be called directly only if the probe first loads `wEnemyMoveStruct` for the target move with the same path the AI uses, such as `AIGetEnemyMove`, and validates that the direct helper value matches hook-captured execution on the fixture:

- `BossAI_CurrentEnemyMoveScoredPower`
- `BossAI_CurrentEnemyMovePressureScore`

Do not rely on `call_function_safe` for inner labels or for helpers that perform internal `farcall`s unless a focused validation proves bank state survives. Prefer hook-snapshot evidence for the score probe.

Important implementation notes:

- Use the non-trace ROM for final behavior if trace hooks affect execution.
- Use the trace ROM for contribution events only after validating final scores match the non-hook score path.
- Define the trace-vs-final equivalence check precisely: same four post-model score bytes, same chosen move byte when selector sampling is deterministic, same sleep-clause legality state, same enemy move ids, and same active-player/enemy species/level/current HP.
- Explicitly set WRAM bank 1 before banked WRAM reads/writes, and document why.
- Seed all relevant public battle fields, not only the active mons:
  - `wBossAITier`
  - `wBossAITurnsElapsed`
  - `wOtherTrainerClass`
  - `wOtherTrainerID`
  - `wTrainerClass`
  - `wCurOTMon`
  - `wCurBattleMon`
  - `wBattleMode`
  - `wEnemyAIMoveScores`
  - `wBattleMon*`
  - `wEnemyMon*`
  - `wEnemyMonBaseStats`
  - stat stages
  - screens/weather/substatus/status
  - sleep clause bytes
  - minimal party liveness fields
  - revealed moves as zero unless supplied
- Report whether each metric is `live-route`, `hook-snapshot`, `direct-public-helper`, or `unavailable`.

Unavailable helper JSON contract:

```json
{
  "ai_damage_rank": {
    "value": null,
    "evidence": "unavailable",
    "reason": "inner BossAI_ApplyMoveModel label is not callable standalone; no hook snapshot was captured"
  }
}
```

For hook-captured helpers, include the entry registers, exit registers, current move slot, current move id, and the score pointer/slot when available. Keep the JSON stable enough for downstream reports, but do not promise byte-exact score values as API contracts.

### 5. Add combined report command

Add a `damage-ai-report` subcommand to `tools/debugger/__main__.py`, or create a small module used by that subcommand.

It should:

1. Resolve exact attacker/defender states using `tools.damage_debugger.state`.
2. Run `tools.damage_debugger.battle_calc` logic for every move.
3. Run the `move-score-probe` logic for the same state.
4. Join rows by move slot.
5. Emit plain text and JSON.

The combined report should include warnings when:

- A higher-damage move is marked `won't pick` while a lower-damage move is selectable.
- AI damage rank ordering disagrees with oracle damage ordering.
- A move is `won't pick` because its score is `80+`.
- Sleep clause/status legality changes the chosen move.
- Contribution tracing and final behavior disagree.

Keep warning language factual. Example:

```text
Warning: Peck does 8-10 damage and Confusion does 4-5, but the AI marks Peck as won't pick while Confusion is selectable.
```

### 6. Tests and verification

Add focused tests. Do not rely on the user's live `pokegold.sav` for unit tests.

Suggested tests:

- `tools.damage_debugger.tables` parses:
  - Noctowl base stats and Normal/Flying typing.
  - Drowzee base stats and Psychic/Psychic typing.
  - Tackle, Peck, Confusion, Hypnosis rows.
  - Mint Berry item lookup.
- `battle_calc` with explicit exact stats returns:
  - Tackle `3-4`
  - Peck `8-10`
  - Confusion `4-5`
  - Hypnosis `0`
- `move-score-probe --self-test` seeds a synthetic Noctowl/Drowzee state and reports relational facts, not byte-pinned tuning:
  - Peck is marked `won't pick` while Confusion is selectable, or the test is updated after the rank bug is explicitly fixed.
  - Oracle damage for Peck is greater than oracle damage for Confusion.
  - Hook diagnostics expose that the AI rank/order used by the ROM disagrees with oracle damage order on the current buggy ROM.
- `matchup.py` existing sample command still works.
- JSON output is stable enough for downstream tooling.
- `.sgm` input fails clearly instead of being silently misread.
- Unsupported Phase 1 flags fail clearly instead of returning guessed data.

Add audit wrappers and wire them into `tools/audit/check_release_smoke.py`, following the small `tools/audit/check_matchup_cli.py` pattern:

- `tools/audit/check_battle_calc.py`
- `tools/audit/check_move_score_probe.py`
- `tools/audit/check_damage_ai_report.py`

Minimum verification commands:

```powershell
python -m tools.damage_debugger.oracle
python -m tools.damage_debugger.matchup NOCTOWL:14:trainer DROWZEE:13:player PECK --attacker-stat 21 --defender-stat 26 --attacker-types NORMAL,FLYING --defender-types PSYCHIC_TYPE,PSYCHIC_TYPE --defender-current-hp 50 --json
python -m tools.damage_debugger.battle_calc --self-test
python -m tools.boss_ai_debugger move-score-probe --self-test
python -m tools.debugger damage-ai-report --self-test
python tools\audit\check_battle_calc.py
python tools\audit\check_move_score_probe.py
python tools\audit\check_damage_ai_report.py
python tools\audit\check_release_smoke.py
python -m unittest discover tools\damage_debugger
python -m unittest discover tools\boss_ai_debugger\tests
python -m unittest discover tools\debugger\tests
```

If a new test directory is added under `tools/damage_debugger/tests`, ensure it is importable and not too slow.

### 7. Documentation updates

Update:

- `tools/damage_debugger/README.md`
- `tools/boss_ai_debugger/README.md`
- `tools/debugger/README.md`
- `docs/generated/dev_index.md` if generated docs are expected after tool changes

Docs should explain:

- Use damage oracle for damage truth.
- Use Boss AI score probe for what the ROM AI thinks.
- Use combined report when investigating "why did the boss pick this move?"

## Acceptance Criteria

The task is complete when a fresh user can run one command and get a table that answers:

1. What damage does every enemy move actually do?
2. What score did Boss AI give every move?
3. Which moves are eligible and which are `won't pick`.
4. Which rule made a move not pickable or changed its score when trace evidence is available?
5. Does AI scoring disagree with actual damage ordering?

For the motivating Noctowl/Drowzee case, the completed tool must make this obvious:

- Peck does more damage than Confusion.
- Peck is marked `won't pick` by the AI score path on the current buggy ROM.
- The mismatch is visible in the same report without hand-written PyBoy scripts.

## Non-Goals

- Do not rewrite the damage oracle.
- Do not replace `tools.damage_debugger.matchup.py`; preserve it.
- Do not replace `tools.boss_ai_debugger` route/materialization tooling.
- Do not create a second Boss AI trace stack when `rom-contribution-trace` can be extended.
- Do not direct-call inner `BossAI_ApplyMoveModel.*` labels and treat the result as evidence.
- Do not change Boss AI policy or fix `CurrentEnemyMoveDamageRank` as part of this ergonomics task.
- Do not hardcode Falkner/Noctowl/Drowzee beyond tests/fixtures.

## Notes for the Implementing Session

Start by reading:

- `tools/damage_debugger/README.md`
- `tools/damage_debugger/matchup.py`
- `tools/damage_debugger/oracle.py`
- `tools/boss_ai_debugger/README.md`
- `tools/boss_ai_debugger/rom_contribution_trace.py`
- `tools/debugger/README.md`
- `tools/trace/boss_ai_state_factory.py`
- `tools/trace/runtime.py`

Then implement in this order:

1. Extract reusable damage table parsing.
2. Add exact state model/readers.
3. Add `battle_calc`.
4. Extend `rom-contribution-trace` and add the `move-score-probe` subcommand.
5. Add combined unified debugger command.
6. Add tests and docs.

Keep each step shippable. The first useful milestone is all-move exact damage from trainer versus save-party slot. The second useful milestone is Boss AI final score bytes. The combined report comes last.
