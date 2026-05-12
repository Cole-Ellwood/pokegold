# Boss AI Multi-Turn Coach UI Implementation Plan

> **STATUS: IMPLEMENTED 2026-05-11.** This is the implementation plan and
> acceptance checklist for the BOSSAI-004 multi-turn Coach Mode. The current
> tool now supports generated plan cards, trajectory preferences, missing-plan
> demonstrations, public-belief rollout summaries, Coach UI save endpoints, and
> trajectory-aware reports/proposals.

## Decision

Build a **Coach Mode** around trajectory preferences and option-like plans.

The user should not write JSON, manually construct rollouts, or label dozens of
near-duplicate single-move states. The tool should generate a small set of
reasonable plan cards, show the boss's full private knowledge and the player's
public knowledge, and ask one focused question:

```text
What should this boss be trying to do from here?
```

The answer should usually be one click:

- `Attack now`
- `Set up, then attack`
- `Status/control`
- `Switch/preserve`
- `Scout/probe`
- `Sacrifice/trade`
- `Neither, bad question`

Only after that choice should the UI reveal condition chips, branch/stop rules,
and optional notes.

## Research Grounding

This plan borrows the parts of modern human-feedback learning that fit this ROM
project and rejects the parts that would make the Game Boy policy opaque.

- Christiano et al. train from human preferences between **trajectory segments**,
  not just isolated actions. Translation here: compare short Pokemon battle
  lines such as "Swords Dance then Wing Attack" against "Wing Attack now".
  <https://arxiv.org/abs/1706.03741>
- Sutton, Precup, and Singh's options framework treats a multi-step behavior as
  a temporally extended action with an initiation condition, internal policy,
  and termination condition. Translation here: a boss plan is an option like
  "Sand Attack once, then Gust until the target switches."
  <https://www.cs.utexas.edu/~shivaram/readings/b2hd-SuttonPS1999.html>
- DAgger exists because sequential decisions create the future states that must
  later be judged. Translation here: generate labels from states reached by the
  current boss AI and its proposed plans, not only from hand-authored snapshots.
  <https://proceedings.mlr.press/v15/ross11a.html>
- ISMCTS is useful for hidden-information games because search should reason
  over information sets, not pretend it knows the hidden state. Translation
  here: the boss planner can use sampled public-belief worlds for player moves,
  but the UI must label what is public, plausible, or impossible.
  <https://edpowley.com/academic/papers/tciaig_ismcts.pdf>
- B-Pref highlights informative query selection and noisy teacher robustness.
  Translation here: ask the user for boundary cases and store confidence,
  holdouts, conflicts, and lesson status.
  <https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/d82c8d1619ad8176d665453cfb2e55f0-Abstract-round1.html>
- InstructGPT uses both demonstrations and rankings. Translation here: the user
  should be able to demonstrate a correct plan, then rank generated alternatives
  against it.
  <https://arxiv.org/abs/2203.02155>
- TAMER shows that quick evaluative feedback can shape sequential behavior.
  Translation here: allow fast thumbs/up-down style feedback on a played-out
  plan segment, but keep it secondary to explicit plan comparisons.
  <https://www.cs.utexas.edu/~pstone/Papers/bib2html/b2hd-ICDL08-knox.html>
- Microsoft's human-AI interaction guidelines emphasize showing contextual
  information, explaining why the system acted, and supporting efficient
  correction. Translation here: the UI should show why a question is queued,
  what the AI currently thinks, and make correction one click.
  <https://www.microsoft.com/en-us/research/wp-content/uploads/2019/01/Guidelines-for-Human-AI-Interaction-camera-ready.pdf>

## Product Goal

Coach Mode should make the user feel like a battle coach, not a data labeler.

Target session:

1. Double-click `START Boss AI Preference Lab.bat`.
2. Open the `Coach` tab.
3. Review 10 high-value questions.
4. For each question, pick a plan card or press `Best plan missing`.
5. Add only 0-3 condition chips.
6. Leave notes only when the chips are insufficient.
7. Run `lesson-report`, `fit-model`, and `propose`.

The tool should optimize for high signal per minute.

## Information Model

### Boss Knowledge

Yes, the user should see the boss side fully. This is not cheating. The boss AI
knows its own active Pokemon, full team, moves, items, HP, status, boosts, role,
plan memory, and legal switches.

Show this as a compact table:

```text
Boss Team
Active  Scyther 81%  item Silverpowder  role ace
        Quick Attack | Wing Attack | Swords Dance | ...
Bench   Ariados 100% | Ledian 100%
```

For each boss mon, include:

- species, level, HP, status, item
- known moves, including unrevealed boss-owned moves
- role: lead, wall, ace, sack, cleaner, status opener
- speed relation if known or inferable from public battle events
- current boosts, volatile states, locks, recharge, Encore/Disable state
- preserve value: expendable, useful later, ace, last mon
- safe switch-in estimate against public player threats

### Player Public Knowledge

The player side must remain public-info only, but it should be much richer than
the current fixture display.

Show:

- active species, level if known, HP band, status, visible item
- revealed moves
- seen party members
- observed speed order
- observed damage ranges
- last 3-5 turns
- public field state: weather, screens, hazards, Sleep Clause, locks
- plausible moves with source buckets
- impossible moves ruled out by four revealed moves
- public switch risk for seen bench members

The UI must clearly separate:

- `revealed`: confirmed by battle events
- `plausible`: legal and public by learnset/TM/checkpoint
- `impossible`: ruled out by public evidence
- `unknown`: not inferable

Never label a player hidden move as fact unless it has been revealed.

## Core Data Model

### Plan Action

Add plan actions beside move/switch actions. A plan is a candidate option, not a
ROM script.

```json
{
  "id": "plan_sand_attack_once_then_gust",
  "kind": "plan",
  "label": "Sand Attack once, then Gust",
  "horizon": 4,
  "initiation_conditions": [
    "direct_damage_under_15_percent",
    "player_has_public_rock_pressure"
  ],
  "steps": [
    {"turn": 1, "action_id": "move_sand_attack"},
    {
      "turn": 2,
      "action_id": "move_gust",
      "repeat_until": ["boss_faints", "target_switches", "target_in_ko_range"]
    }
  ],
  "branch_rules": [
    {"if": "target_switches", "then": "re_score"},
    {"if": "accuracy_drop_already_landed", "then": "do_not_repeat_debuff"}
  ],
  "stop_conditions": [
    "target_switches",
    "boss_hp_below_30",
    "plan_goal_reached"
  ],
  "rationale": "One debuff is useful when chip is worthless; repeating it is bad."
}
```

### Trajectory Preference

Add `tools/boss_ai_preference/labels/boss_ai_trajectory_preferences.jsonl`.

```json
{
  "schema_version": 1,
  "fixture_id": "bugsy_scyther_vs_quilava_fire_pressure",
  "trajectory_a_id": "plan_swords_dance_then_wing_attack",
  "trajectory_b_id": "plan_wing_attack_then_quick_attack",
  "choice": "a_better",
  "preferred_trajectory_id": "plan_swords_dance_then_wing_attack",
  "horizon": 3,
  "confidence": "medium",
  "public_info_scope": "public_only",
  "lesson_type": "sequence_policy",
  "condition_tags": [
    "boss_faster",
    "survives_one_hit",
    "setup_changes_ko_math"
  ],
  "branch_tags": [
    "if_player_switches_rescore",
    "if_setup_no_longer_changes_ko_math_attack_now"
  ],
  "holdout": false,
  "note": "If Scyther is faster, Swords Dance still wins in two boss turns and leaves +2.",
  "created_at": "2026-05-11T00:00:00+00:00",
  "tool_version": "boss-ai-preference-v1"
}
```

Allowed trajectory choices:

- `a_better`
- `b_better`
- `both_good`
- `both_bad`
- `depends`
- `neither_best_plan_missing`
- `upstream_state_issue`
- `needs_context`

### Plan Demonstration

When generated plans are wrong, the user can demonstrate a better plan by
editing chips, not JSON.

```json
{
  "schema_version": 1,
  "fixture_id": "brock_golem_vs_vaporeon_explosion_question",
  "demonstration_id": "demo_sack_or_explode_for_clean_omastar",
  "horizon": 4,
  "steps": [
    {"turn": 1, "action_id": "move_explosion"},
    {"turn": 2, "action_id": "switch_omastar", "actor": "boss_next_mon"}
  ],
  "near_tie_with": ["plan_hard_switch_omastar"],
  "condition_tags": ["boss_outsped", "clean_switch_value", "mixed_strategy"],
  "human_summary": "Explosion and switching are close; vary them instead of always Earthquake."
}
```

### Episode Snapshot

Add an optional episode context object for mid/late game states.

```json
{
  "episode_id": "lance_champion_turn_12_ice_probe",
  "phase": "late",
  "turn_number": 12,
  "last_turns": [
    {
      "turn": 9,
      "boss_action": "switch_gyarados",
      "player_action": "surf",
      "public_result": "Gyarados took about 28%"
    }
  ],
  "observed_speed": [
    {"faster": "Suicune", "slower": "Aerodactyl", "basis": "turn_8"}
  ],
  "observed_damage": [
    {"move": "Surf", "target": "Gyarados", "range": "26-31%"}
  ]
}
```

## UI Design

### Layout

Use four tabs, with `Coach` as the default.

```text
Coach | Queue | Reports | Data
```

The `Coach` tab uses three dense panes:

```text
+------------------+-------------------------------+----------------------+
| Question Queue   | Battle Snapshot               | Answer               |
| ranked cards     | boss full info + player public| plan cards + chips   |
+------------------+-------------------------------+----------------------+
```

### Question Queue

Each card should explain why it is worth asking.

```text
1. Bugsy: Scyther vs Quilava
Priority 15
Teaches: setup timing, damage race
Why: scorer disagrees with your old label; speed boundary unresolved
```

Clicking a queue item loads the battle snapshot and generated plan cards.

Filters:

- `All`
- `Early`
- `Mid`
- `Late`
- `Needs my judgment`
- `Regression gap`
- `Counterfactual family`
- `Holdout`

### Battle Snapshot

The snapshot must answer the user's real question: "What do I know as the boss?"

Sections:

1. Boss active and team table.
2. Player active public card.
3. Seen player party.
4. Last turns.
5. Public threat panel.
6. Current AI explanation.

The boss side should show all boss moves and team members. The player side
should show revealed and plausible information with badges:

```text
Revealed   Ember, Quick Attack
Plausible  Flame Wheel 75%, Dig 50%
Blocked    Fire Blast 0% - unavailable before Goldenrod TM
Unknown    fourth moveslot
```

### Answer Panel

The default answer panel shows generated plan cards.

```text
What should Bugsy try?

[Plan A] Swords Dance -> Wing Attack
Goal: turn 2 KO or force switch
Stops if: Quilava is faster, Scyther below 35%

[Plan B] Wing Attack -> Quick Attack
Goal: cash damage immediately
Stops if: Quilava leaves KO range

[Plan C] Switch Ledian
Goal: preserve Scyther
Risk: still eats Fire pressure
```

Primary buttons:

- `Plan A`
- `Plan B`
- `Plan C`
- `Both fine`
- `Depends`
- `Best plan missing`

Secondary chips appear after the primary choice:

- `boss faster`
- `player faster`
- `survives one hit`
- `KO confirmed`
- `2HKO only`
- `target can punish`
- `target can switch`
- `hidden coverage plausible`
- `sleep clause free`
- `sleep clause occupied`
- `preserve ace`
- `sack for clean switch`
- `do once only`
- `repeat until KO`
- `rescore after switch`

The user can save without a note. Notes are optional.

### Plan Builder

Only open this when `Best plan missing` is clicked.

Do not show a blank editor first. Start with templates:

- `Do X once, then Y`
- `Repeat X until stop condition`
- `Set up, then cash damage`
- `Scout/probe, then preserve or commit`
- `Switch, then threaten`
- `Sack/trade for clean switch`
- `Status, then attack`
- `Stall/recover until safe`

The builder should be chip-based:

```text
Turn 1: [move_sand_attack v]
Turn 2: [move_gust v] [repeat until: target switches v]
Stop if: [accuracy debuff landed once] [boss below 30%]
Branch if: [player switches] -> [re-score]
```

### Quick Feedback Mode

For live trace review, add a fast "replay strip":

```text
AI chose: Earthquake
Alternative: Explosion
Outcome projection: Vaporeon likely KOs next turn

[Good] [Bad] [Good but only as mixup] [Needs plan]
```

This is TAMER-like evaluative feedback. It should not replace plan
preferences, but it is useful for rapidly triaging live traces.

## Early, Mid, And Late Game Teaching

### Early Game: Opening Policy

Early-game questions are about identity and first commitment.

Examples:

- Should the boss lead with status, setup, direct damage, or scout?
- Is one early utility move acceptable before attacking?
- Does the boss reveal ace pressure immediately or preserve it?
- Should the boss respect common public coverage from turn 1?

Generated plan templates:

- `status_opener_then_attack`
- `setup_once_then_attack`
- `probe_then_commit`
- `direct_damage_until_switch`
- `preserve_ace_if_bad_lead`

Features:

- known starter route checkpoint
- public move priors
- direct damage estimate
- boss identity/personality
- early cheapness tolerance
- first-turn setup safety

UI default:

- hide complex last-turn history because there is none
- emphasize public priors and opening identity
- ask "What plan should this boss start with?"

### Mid Game: Conditional Plans

Mid-game questions are about branching.

Examples:

- Setup only if it changes KO math.
- Switch only if it preserves a useful mon and the switch-in fits.
- Status only if the target is not already neutralized.
- Probe hidden coverage before committing an ace.

Generated plan templates:

- `setup_if_survives_then_cash`
- `switch_preserve_then_counterpressure`
- `status_then_attack_until_range`
- `probe_then_switch_if_threat_revealed`
- `recover_only_if_not_outdamaged`

Features:

- last 3-5 turns
- revealed moves
- observed speed order
- observed damage ranges
- HP race
- expected switch-fit
- Sleep Clause state
- current locks and volatile states

UI default:

- show last-turn strip
- show plan branch rules
- ask "Which line stays good after the next response?"

### Late Game: Win Condition And Resource Use

Late-game questions are about closing the fight.

Examples:

- Take guaranteed KO over slow chip.
- Sack for clean switch.
- Preserve ace if it still wins later.
- Explosion trade can be correct if the mon is otherwise dead weight.
- Avoid deterministic near-tie behavior.

Generated plan templates:

- `force_ko_now`
- `sack_for_clean_switch`
- `preserve_ace_and_pivot`
- `trade_explosion`
- `mixed_strategy_near_tie`

Features:

- remaining team counts
- last mon status
- boss preserve value
- player remaining revealed threats
- guaranteed KO / revenge KO
- clean-switch value
- deterministic-repeat penalty

UI default:

- show remaining teams prominently
- show win-condition summary
- ask "Which line wins or preserves the win condition?"

## Plan Generation Engine

Add `tools/boss_ai_preference/plans.py`.

Responsibilities:

1. Generate candidate plan cards for a fixture.
2. Keep plans public-info legal.
3. Explain each plan in plain English.
4. Include stop/branch rules.
5. Score plan diversity so the UI shows meaningfully different lines.

Candidate pools:

- current top scorer action
- second-best scorer action
- highest-damage action
- best switch-fit action
- best preserve action
- setup-then-attack template
- status-then-attack template
- scout/probe template
- sacrifice/trade template
- user demonstration templates from prior labels

Plan generation should be conservative:

- horizon defaults to 3 turns
- max horizon 5
- no hidden player facts
- no branching explosion in UI
- at most 4 plan cards shown
- every plan has a goal and stop condition

Priority formula for showing plan questions:

```text
priority =
  5 * single_turn_label_conflict
+ 4 * top_move_changes_after_one_turn_rollout
+ 4 * old_note_mentions_sequence
+ 3 * setup_or_status_or_switch_action_in_top_3
+ 3 * hidden_coverage_or_speed_boundary
+ 2 * late_game_resource_trade
+ 2 * current_scorer_margin_small
+ 2 * active_queue_stale_team_hash
- 3 * already_has_high_confidence_trajectory_label
- 2 * repeated_same_plan_shape
```

## Belief And Rollout Engine

Add `tools/boss_ai_preference/rollouts.py`.

This does not need a full battle simulator at first. It needs a small public
belief rollout that is good enough to generate reviewable plan cards.

### Belief State

For player hidden moves:

- revealed moves are fixed at 99%
- four revealed moves block all unrevealed alternatives
- level-up STAB/core moves get high prior
- direct TM/HM access gets medium prior
- optional or route-dependent moves get low prior
- impossible moves get 0%

For player action selection:

- if player has a revealed KO, assume it may click it
- if player is hard-walled, assume switch is plausible
- if player is faster and can 2HKO, assume pressure
- if player is statused/locked, discount pressure

This is closer to information-set planning than perfect-information search.
Keep the language in reports as "public belief" rather than "known".

### Rollout Modes

1. `deterministic_public_worst_case`
   Assume the player uses the strongest public plausible punish.

2. `public_belief_samples`
   Sample a few plausible player move sets and actions by public source bucket.

3. `human_trace_replay`
   Use actual live trace turns already captured.

Reports must show which mode generated a plan card.

## Learning Loop

The learning loop should combine demonstrations, preferences, and proposals:

1. `active-queue` finds states worth asking.
2. `plan-queue` generates trajectory questions.
3. Coach UI collects trajectory preferences and demonstrations.
4. `lesson-report` derives plan lessons.
5. `fit-model` fits both action and plan features.
6. `propose` suggests ROM-safe rule changes or asks for more labels.
7. Approved changes become fixtures/audits/scoring edits.

Do not ship learned weights into ROM automatically.

## Files To Add Or Change

### New Files

- `tools/boss_ai_preference/plans.py`
- `tools/boss_ai_preference/rollouts.py`
- `tools/boss_ai_preference/trajectory_data.py`
- `tools/boss_ai_preference/plan_queue.py`
- `tools/boss_ai_preference/labels/boss_ai_trajectory_preferences.jsonl`
- `tools/boss_ai_preference/labels/boss_ai_plan_demonstrations.jsonl`
- `audit/boss_ai_preference/plan_queue.md`
- `audit/boss_ai_preference/plan_queue.json`
- `audit/boss_ai_preference/trajectory_report.md`
- `audit/boss_ai_preference/trajectory_report.json`

### Existing Files

- `tools/boss_ai_preference/app.py`
  Add Coach tab, plan cards, plan builder, trajectory save endpoints.

- `tools/boss_ai_preference/__main__.py`
  Add `plan-queue`, `trajectory-report`, and `coach-report`.

- `tools/boss_ai_preference/SCHEMA.md`
  Document plan actions, trajectory preferences, demonstrations, episode
  snapshots, branch tags, stop conditions.

- `tools/boss_ai_preference/features.py`
  Add plan-level features and state-transition features.

- `tools/boss_ai_preference/active_queue.py`
  Feed high-priority items into plan queue.

- `tools/boss_ai_preference/lessons.py`
  Derive sequence/switch/scout lessons from trajectory rows.

- `tools/boss_ai_preference/reward_model.py`
  Add Bradley-Terry model over plan feature differences.

- `tools/boss_ai_preference/proposals.py`
  Add proposal types for plan policies and branch/stop rules.

- `tools/audit/check_boss_ai_preference.py`
  Add trajectory schema, plan generation, and report smoke tests.

## Commands

```powershell
python -m tools.boss_ai_preference plan-queue
python -m tools.boss_ai_preference trajectory-report
python -m tools.boss_ai_preference coach-report
python -m tools.boss_ai_preference fit-model --include-trajectories
python -m tools.boss_ai_preference propose --include-trajectories
```

## Report Outputs

- `audit/boss_ai_preference/plan_queue.md`
- `audit/boss_ai_preference/plan_queue.json`
- `audit/boss_ai_preference/trajectory_report.md`
- `audit/boss_ai_preference/trajectory_report.json`
- `audit/boss_ai_preference/coach_report.md`
- `audit/boss_ai_preference/coach_report.json`

## Phased Implementation

### Phase C1 - Trajectory Schema

Work:

- Add `trajectory_data.py`.
- Add loaders/writers for trajectory preferences and plan demonstrations.
- Validate plan ids, choices, horizon, condition tags, branch tags, holdout.
- Preserve old pairwise data unchanged.

Verification:

```powershell
python -m tools.boss_ai_preference validate
python tools\audit\check_boss_ai_preference.py
python -m compileall -q tools\boss_ai_preference
```

### Phase C2 - Plan Generator

Work:

- Add plan actions generated from current fixture actions.
- Generate at most 4 plan cards per state.
- Include goal, stop conditions, branch rules, and public-info rationale.
- Support early/mid/late phase templates.

Verification:

```powershell
python -m tools.boss_ai_preference plan-queue
python tools\audit\check_boss_ai_preference.py
```

### Phase C3 - Coach UI

Work:

- Add `Coach` tab.
- Show question queue, battle snapshot, and answer panel.
- Add plan-card comparison.
- Add chip-based plan builder for `Best plan missing`.
- Add full boss team/moves display.
- Add richer player public/revealed/plausible/impossible display.

Verification:

```powershell
python -m tools.boss_ai_preference serve --host 127.0.0.1 --port 8765
```

Manual browser checks:

- Coach tab loads.
- Plan cards fit at desktop and narrow widths.
- Saving a trajectory row updates reports.
- Existing pairwise UI still works.
- Trace/queue cards explain why they are being asked.

### Phase C4 - Rollout And Public Belief

Work:

- Add lightweight public-belief rollout.
- Generate plan projections for 3-5 turns.
- Support deterministic public worst-case and sampled public-belief modes.
- Clearly label all sampled/plausible assumptions in UI and reports.

Verification:

```powershell
python -m tools.boss_ai_preference plan-queue --rollout-mode public-belief-samples
python tools\audit\check_boss_ai_preference.py
```

### Phase C5 - Trajectory Lessons And Model

Work:

- Extend lesson extraction from trajectory preferences.
- Add plan-level Bradley-Terry features.
- Report action-only vs trajectory accuracy.
- Report where single-turn scoring and trajectory labels disagree.

Verification:

```powershell
python -m tools.boss_ai_preference trajectory-report
python -m tools.boss_ai_preference fit-model --include-trajectories
```

### Phase C6 - Proposal Integration

Work:

- Propose `sequence_policy`, `switch_policy`, `scout_policy`, and
  `mixed_strategy` changes from trajectory evidence.
- Default to `needs_more_labels` unless trajectory evidence covers the relevant
  early/mid/late boundary.
- Generate audit fixture suggestions for every accepted plan lesson.

Verification:

```powershell
python -m tools.boss_ai_preference propose --include-trajectories
python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json
python tools\audit\check_boss_ai_trace_invariants.py
```

## UI Acceptance Criteria

- The user can answer a generated plan question in one click.
- The user can add common conditions without typing.
- The user can demonstrate a missing plan without editing JSON.
- The boss side shows full boss team, moves, items, HP, status, and role.
- The player side separates revealed, plausible, impossible, and unknown info.
- Early, mid, and late game filters are available.
- A saved trajectory appears in `trajectory-report`.
- Existing pairwise labels remain valid.
- The reports name whether a lesson is single-turn or multi-turn.
- No ROM behavior changes are made automatically.

## Engineering Acceptance Criteria

- New schema loaders reject invalid trajectory rows.
- Generated plan cards contain at least one stop condition.
- Generated plan cards never use hidden player moves as facts.
- Rollout assumptions are included in JSON and Markdown reports.
- Active queue de-duplicates repeated plan shapes.
- Plan lessons can be held out for evaluation.
- All generated reports are deterministic for a fixed corpus.
- `check_boss_ai_preference.py` covers trajectory save/load, plan generation,
  rollout public-info constraints, and report generation.
- `git diff --check` passes.

## First Labels To Collect After Implementation

Collect these before changing scoring:

1. Falkner: `Sand Attack once then Gust` vs repeated debuff vs direct Gust.
2. Bugsy: Scyther faster vs Quilava faster setup boundary.
3. Whitney: Body Slam until paralysis, then Rollout boundary.
4. Morty: Hypnosis when Sleep Clause free vs occupied.
5. Chuck/Pryce: switch-preserve lines where the best action is not in the pair.
6. Clair/Lance: scout/probe before ace commitment.
7. Brock: Explosion vs switch as near-tie mixed strategy.
8. Misty/Koga: immediate KO over recovery/status/chip.

## Risks

- **Too much UI complexity.** Mitigation: default to plan cards and hide the
  builder behind `Best plan missing`.
- **Fake precision in rollouts.** Mitigation: label projections as rough public
  belief, not exact battle simulation.
- **Hidden-info leakage.** Mitigation: report every player-side assumption as
  revealed/plausible/impossible/unknown.
- **Overfitting from few labels.** Mitigation: holdouts, active queue, proposal
  defaults to `needs_more_labels`.
- **Plan labels not mappable to ROM.** Mitigation: convert plans to small
  branch/stop rules and audits, never opaque learned policies.

## Implementation Notes

Implemented files:

- `tools/boss_ai_preference/trajectory_data.py`
- `tools/boss_ai_preference/plans.py`
- `tools/boss_ai_preference/rollouts.py`
- `tools/boss_ai_preference/plan_queue.py`
- `tools/boss_ai_preference/app.py`
- `tools/boss_ai_preference/__main__.py`
- `tools/boss_ai_preference/features.py`
- `tools/boss_ai_preference/lessons.py`
- `tools/boss_ai_preference/reward_model.py`
- `tools/boss_ai_preference/proposals.py`
- `tools/audit/check_boss_ai_preference.py`

The Coach UI remains intentionally conservative: generated plans and learned
reports are review tools only, and no ROM behavior changes are made
automatically.
