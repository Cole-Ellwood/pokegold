# Boss AI RLHF-ish V2 Implementation Plan

> **STATUS: IMPLEMENTED 2026-05-11.** This records the V2 implementation plan
> for BOSSAI-004 after the Version A preference labeler. V2 makes the user's
> feedback more sample-efficient without shipping an opaque learned policy into
> the ROM.

> **FINAL HARDENING PASS 2026-05-11.** Coach Mode now treats trajectory labels
> as first-class by default, saves every shown plan-card comparison covered by a
> coaching answer, auto-advances through unresolved questions, records
> fixture/team hashes on trajectory rows, and emits a `final-report` readiness
> gate before any ROM scoring review.

## Decision

Build V2 as an **active preference coaching loop**:

1. Capture the current AI's public-info decision and explanation.
2. Ask the user only high-value questions.
3. Convert prose notes into structured, reviewable lessons.
4. Fit an offline, readable preference model against those lessons.
5. Produce candidate scoring/fixture/audit changes for human approval.

Do **not** build black-box deep RL for the ROM. The Game Boy side should remain
readable asm and small tables. The trained pieces live offline as tools that
explain which existing scoring rule, fixture, or policy table should change.

## Research Inputs

V2 should borrow the useful parts of RLHF/preference learning and reject the
parts that do not fit this repo.

- Christiano et al. show the core RLHF shape: humans compare behavior segments,
  a reward model learns the preference, and the policy improves using that
  learned reward. The useful translation here is "compare boss battle snippets
  and plans," not "ship a neural policy."
  <https://arxiv.org/abs/1706.03741>
- OpenAI's 2017 preference-learning writeup emphasizes active queries: as the
  model improves, ask for feedback where the model is uncertain. That is exactly
  the missing piece in Version A's hand-authored fixture flow.
  <https://openai.com/index/learning-from-human-preferences/>
- Settles' active-learning survey frames the label bottleneck: labels are scarce,
  so the learner should choose informative examples instead of random examples.
  V2 should use this for the review queue.
  <https://burrsettles.com/pub/settles.activelearning_20090109.pdf>
- DAgger's lesson is that sequential policies should be trained on states they
  actually induce, because future states depend on previous actions. V2 should
  query states from the current boss AI's real trace/debugger distribution, not
  only curated standalone snapshots.
  <https://proceedings.mlr.press/v15/ross11a.html>
- Microsoft Research's human-AI guidelines are directly relevant to the Coach
  UI: show why the system produced a suggestion, ask for clarification when
  uncertain, and make correction cheap instead of hiding uncertainty behind an
  overconfident answer.
  <https://www.microsoft.com/en-us/research/wp-content/uploads/2019/01/Guidelines-for-Human-AI-Interaction-camera-ready.pdf>
- B-Pref highlights two practical issues for preference-based RL: query
  selection matters, and "teacher" feedback can be noisy or inconsistent. V2
  needs conflict reports, confidence, holdouts, and robustness checks.
  <https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/d82c8d1619ad8176d665453cfb2e55f0-Abstract-round1.html>
- InstructGPT used both demonstrations and rankings. For this project, that
  means a user-written "correct plan" can be more valuable than only choosing
  A over B.
  <https://arxiv.org/abs/2203.02155>

## Current Repo Ground Truth

Version A already exists in `tools/boss_ai_preference/`:

- fixture loader and schema
- pairwise and single-action JSONL labels
- local browser UI
- CLI label/preference commands
- source-derived player threat availability
- rough damage estimates
- Markdown/JSON reports
- `tools/audit/check_boss_ai_preference.py`

BOSSAI-003 also exists and matters to V2:

- `engine/battle/ai/PLATFORM_API.md` defines the public-info platform boundary.
- `engine/battle/ai/POLICY_DESIGN.md` anchors readable policy intent.
- `tools/boss_ai_debugger/` can inspect scored actions and regress pairwise
  labels against the current scorer.
- Static Boss AI audits already guard no-cheat and policy-contract behavior.

The current label file is small but already high-signal. The user's notes are
mostly not simple "move X beats move Y" facts. They are conditional battle
principles:

- Falkner: one accuracy debuff can be correct when direct chip is worthless, but
  repeated debuffs are bad because switching clears them.
- Bugsy: setup depends on speed and survival; `Swords Dance` is good only if
  Scyther is faster or still reaches the same damage race.
- Whitney: ramp-lock moves are worse into bulky resisted targets until the board
  is made safer by paralysis or KO pressure.
- Morty: sleep is a high-value legal pressure tool, but now must respect Sleep
  Clause and immediate fail states.
- Chuck/Pryce/Clair: several `other_better` labels say the comparison was too
  narrow because the best action was a switch/preserve line.
- Lance: some states are the wrong active-mon decision; the correct lesson is
  upstream scouting, information value, and ace preservation.
- Koga/Misty: a guaranteed or near-guaranteed KO should dominate slow chip or
  recovery when the opponent can immediately punish passivity.
- Brock: sacrifice, switch, and Explosion can be near-tie mixed strategies; the
  AI should not become perfectly deterministic in these spots.

These labels remain useful after team changes, but direct action ids can go
stale. V2 must preserve the principle and re-anchor it to the current legal
actions.

## V2 Product Shape

V2 has four user-facing commands:

```powershell
python -m tools.boss_ai_preference active-queue
python -m tools.boss_ai_preference lesson-report
python -m tools.boss_ai_preference fit-model
python -m tools.boss_ai_preference propose
```

And one browser addition:

- a review queue tab that shows "why this question matters" before asking for a
  label.

The preferred workflow:

1. Run `active-queue`.
2. Label 10-20 high-value states in the browser.
3. Run `lesson-report` to review extracted principles.
4. Run `fit-model` to see where a small offline preference model agrees or
   disagrees with the current scorer.
5. Run `propose` to generate candidate fixture/scoring/audit changes.
6. Human approves changes one at a time. Nothing auto-lands into ROM.

## Final-Version Gates

The final version must not let a Coach label look stronger than it is. A click
on Plan C saves Plan C against every other shown plan. `both_good`, `depends`,
`needs_context`, and `best plan missing` are saved across all shown plan pairs.
The queue treats a question as complete only when every shown pair has coverage.

Trajectory rows now carry `fixture_state_hash` and `source_team_hash`, so
reports can flag stale lessons after roster, move, or fixture edits. Source
team display is anchored to the parsed trainer party group/index and reports
whether the anchor is exact.

`lesson-report`, `fit-model`, and `propose` include trajectory data by default.
Use `--no-include-trajectories` only for a legacy action-only sanity check.

Run this before turning labels into scoring work:

```powershell
python -m tools.boss_ai_preference final-report
```

The report gates ROM scoring review on: no trajectory conflicts, no stale
trajectory rows, non-empty holdouts, exact party anchors, full shown-pair
coverage for the top plan queue, and proposal reports not blocked by conflicts.
Generated proposals remain manual review artifacts; they set
`rom_behavior_change: false` and `requires_human_approval: true`.

## Data Model V2

Keep the existing v0/v1 JSONL readable. Add new optional fields rather than
breaking old rows.

### Pairwise Preference Extensions

```json
{
  "fixture_id": "bugsy_scyther_vs_quilava_fire_pressure",
  "state_version": 2,
  "action_a_id": "move_swords_dance",
  "action_b_id": "move_wing_attack",
  "choice": "a_better",
  "preferred_action_id": "move_swords_dance",
  "confidence": "medium",
  "public_info_scope": "public_only",
  "lesson_type": "sequence_policy",
  "condition_tags": [
    "if_user_faster",
    "survives_one_hit",
    "setup_reaches_ko_threshold"
  ],
  "counterfactual_group": "bugsy_scyther_setup_speed_boundary",
  "holdout": false,
  "note": "If Scyther is faster, Swords Dance keeps the same damage race and leaves +2."
}
```

New fields:

- `confidence`: `low`, `medium`, `high`.
- `public_info_scope`: `public_only`, `public_plus_common_meta`,
  `hidden_info_rejected`, `needs_source_check`.
- `lesson_type`: `hard_rule`, `weight_hint`, `sequence_policy`,
  `switch_policy`, `scout_policy`, `personality_style`, `fixture_bug`,
  `stale_direct_action`, `needs_context`.
- `condition_tags`: structured predicates that make the note portable.
- `counterfactual_group`: groups generated boundary variants.
- `holdout`: true means use for evaluation only, not fitting.
- `source_team_hash`: optional hash of relevant trainer party/moveset data.
- `stale_reason`: optional reason a direct action label no longer maps cleanly.

### Structured Lesson Records

Add `tools/boss_ai_preference/labels/boss_ai_lessons.jsonl`.

```json
{
  "lesson_id": "rollout_resisted_non_ko_lockin",
  "source_preference_ids": [
    "whitney_miltank_vs_geodude_rollout_temptation:move_rollout:move_body_slam"
  ],
  "status": "candidate",
  "lesson_type": "hard_rule",
  "applies_to": {
    "move_properties": ["ramp_lock"],
    "target_properties": ["resists_move", "physically_bulky"],
    "excluded_when": ["ko_confirmed", "target_paralyzed", "late_ramp_already_locked"]
  },
  "expected_direction": "discourage",
  "rom_target": "engine/battle/ai/scoring.asm",
  "human_summary": "Do not start a resisted ramp-lock sequence when it does not KO and the target can punish or switch."
}
```

Lesson records are not trusted automatically. They are a review surface between
free-form notes and code changes.

## Feature Extraction

Add `tools/boss_ai_preference/features.py`. It should compute features from a
fixture plus current source-derived threat metadata.

Feature groups:

- **Damage and KO:** damage bucket, KO chance bucket, 2HKO/3HKO threshold,
  recoil/self-KO, Explosion trade value.
- **Tempo:** current HP race, whether setup changes the damage race, whether
  recovery loses to incoming damage, whether chip enables a teammate revenge.
- **Speed:** known faster/slower/tie/unknown, priority threat, speed control
  available, paralysis aftermath.
- **Status:** sleep legal, Sleep Clause occupied, target already statused,
  Safeguard, Substitute, held status cure, Rest self-sleep.
- **Setup:** safe setup window, stop condition, one-use setup, repeated setup
  diminishing value, phaze/Encore risk.
- **Switching:** active mon threatened, bench switch-fit, ace preservation,
  sacrifice value, clean-switch value, repeated-switch penalty.
- **Hidden information:** revealed threat, plausible threat, information-probe
  move, Bayesian flip after a stay-in, hidden-coverage suspicion.
- **Move class:** ramp-lock, recharge, low accuracy, OHKO, phazing, trapping,
  Counter/Mirror Coat, Destiny Bond, recovery, chip status.
- **Personality:** leader risk tolerance, ace style, cruelty/cheapness allowed,
  iconic move bonus only when strategically close.

Feature extraction must never read hidden move slots as facts. It can only use
revealed moves and public learnability buckets already exposed by Version A.

## Active Query Engine

Add `tools/boss_ai_preference/active_queue.py`.

### Candidate Pools

1. Existing hand-authored fixtures.
2. Current Boss AI debugger fixtures.
3. Live trace states from `audit/boss_ai_trace/*_live.txt`.
4. Counterfactual variants generated from labeled fixtures.
5. Stale-team relabel candidates where `source_team_hash` changed.
6. States where the current scorer's top move conflicts with a lesson.
7. States where top legal actions are close, especially move vs switch.

### Priority Score

Use a simple readable score first:

```text
priority =
  4 * scorer_disagreement
+ 3 * top_score_margin_uncertainty
+ 3 * lesson_boundary_value
+ 2 * stale_team_or_moveset
+ 2 * legal_action_set_changed
+ 2 * undercovered_leader
+ 1 * new_feature_combination
- 2 * repeated_question_shape
- 3 * already_confident_lesson
```

The queue report must explain each item:

```text
1. lance_dragonite_vs_suicune_ice_probe_variant_03
   Reason: current scorer prefers Dragon Dance, but existing Lance note says
   hidden Ice coverage makes scout/probe value central. Top actions are close.
   Teaches: scout_policy + information_probe + ace_preservation.
```

This is the biggest human-time win in V2. The tool should ask the user questions
where the answer changes policy, not where the answer only confirms the obvious.

## Counterfactual Fixture Generator

Add `tools/boss_ai_preference/counterfactuals.py`.

Counterfactuals are small, legal mutations of an existing fixture. They should
be grouped and traceable, not random fuzz.

Templates:

- `speed_boundary`: user faster, enemy faster, speed tie.
- `hp_threshold`: target in KO range, 2HKO range, survives comfortably.
- `status_aftermath`: healthy, paralyzed, already asleep, Sleep Clause occupied.
- `hidden_coverage`: threat revealed, plausible only, impossible by public data.
- `setup_stop`: zero boosts, one boost enough, repeated setup greedy.
- `switch_fit`: safe switch-in, risky switch-in, bad switch-in, sacrifice pivot.
- `move_lock`: ramp-lock start, mid-ramp locked, recharge risk, Outrage lock.
- `information_probe`: chip move reveals stay-in coverage vs immediate setup.
- `ace_preservation`: active mon expendable vs leader ace vs last mon.

Rules:

- Generated states must remain plausible for the current source teams.
- Every generated fixture stores `parent_fixture_id`, `mutation_template`,
  `changed_fields`, and `rationale`.
- The UI should show generated variants as a family so the user can label the
  boundary quickly.

## Plan Labels

Single-turn move labels are too weak for Pokemon. Add optional plan actions:

The detailed follow-up plan for a low-friction multi-turn Coach UI is
[`boss_ai_multiturn_coach_ui_plan.md`](boss_ai_multiturn_coach_ui_plan.md).

```json
{
  "id": "plan_sand_attack_once_then_gust",
  "kind": "plan",
  "steps": [
    {"action_id": "move_sand_attack"},
    {"action_id": "move_gust", "repeat_until": "faint_or_target_switches"}
  ],
  "stop_conditions": ["target_switches", "accuracy_drop_landed_once"]
}
```

The browser should allow:

- "A is better now"
- "B is better now"
- "Neither; this plan is better"
- "This is an upstream switch/team-selection issue"

This directly addresses the current `other_better` and `needs_context` notes.

## Offline Preference Model

Add `tools/boss_ai_preference/reward_model.py`.

Do not overbuild this. Start with a small Bradley-Terry/logistic model over
hand-authored features:

```text
P(action_a preferred over action_b) =
  sigmoid(weight * (features(action_a) - features(action_b)))
```

Implementation constraints:

- Pure Python is fine.
- Use deterministic train/holdout split.
- L2 regularization by default; optional L1 report to find sparse rules.
- No model artifact ships to ROM.
- The model must print top positive/negative features in plain English.
- If the model confidently disagrees with the ASM scorer, generate a review
  item, not an automatic code change.

Reports:

- pairwise accuracy on fit rows
- pairwise accuracy on holdout rows
- per-leader accuracy
- confusion by lesson type
- examples fixed by the model but missed by current scorer
- examples current scorer gets right but the model misses
- top feature weights
- unstable weights with low support

## Proposal Generator

Add `tools/boss_ai_preference/proposals.py`.

Proposal types:

- `schema_only`: the label needs better structure, not ROM behavior.
- `fixture_update`: the old fixture is stale after team/moveset changes.
- `scoring_weight`: adjust an existing readable weight.
- `hard_rule`: add or modify a small ASM fail/discourage rule.
- `switch_policy`: adjust move-vs-switch arbitration.
- `sequence_policy`: add a stop condition or plan-selection rule.
- `audit_guard`: add a targeted regression/audit fixture.
- `needs_more_labels`: active queue should ask more boundary questions first.

Proposal report shape:

```markdown
## Candidate: discouraged resisted ramp-lock opener

Evidence:
- Whitney label prefers Body Slam over Rollout into Geodude.
- Existing scorer also failed similar resisted opening ramp cases.

Improves:
- whitney_miltank_vs_geodude_rollout_temptation

Risks / worsens:
- none in current holdout

Suggested implementation:
- hard-rule scoring discourage for ramp-lock opener when resisted, non-KO, and
  target has meaningful damage.

Required verification:
- build
- check_boss_ai_trace_invariants.py
- boss_ai_debugger regress
```

The proposal generator should be conservative. If fewer than two examples
support a general rule, default to `needs_more_labels` unless the rule is a
mechanics hard fail.

## Handling Old Labels After Team Changes

V2 should split every old label into two layers:

1. **Direct judgment:** "In this exact fixture, action X beat action Y."
2. **Portable principle:** "Setup is good only if it preserves or improves the
   damage race."

When teams change:

- mark direct judgments `stale_direct_action` if the action set changed
- keep portable principles active
- generate replacement fixtures from the current teams
- ask the user only where the principle does not re-anchor cleanly

This answers the practical question: old lessons are not useless, but V2 must
stop treating every old `action_id` as timeless.

## Current Label Lessons To Encode First

These should become the first structured lessons.

| Lesson | Type | First implementation target |
| --- | --- | --- |
| One debuff can be correct when direct chip is worthless; repeated debuffs are bad if switching clears them. | `sequence_policy` | Plan labels + counterfactuals |
| Setup is correct when it does not lose the HP race and changes future KO math. | `weight_hint` | Feature extraction + reward model |
| Ramp-lock openers are bad into bulky resisted non-KO targets until status or KO pressure changes the board. | `hard_rule` | Proposal report; ASM only after regression |
| Sleep is strong legal pressure, but hard fail states and Sleep Clause must gate it. | `hard_rule` | Scorer fail-awareness proposal |
| Immediate KO beats slow chip/status/recovery when the target can punish passivity. | `weight_hint` | Reward model + scorer comparison |
| `other_better` often means move comparison is missing switch actions. | `schema_only` | UI/query generation |
| Hidden coverage suspicion can make scouting or probing better than greedy setup. | `scout_policy` | Counterfactuals + active queue |
| Sacrifice vs switch vs attack can be a near-tie mixed-strategy spot. | `personality_style` | Proposal only after more labels |

## Browser UI Changes

Add a V2 review mode with four panes:

1. **Battle state:** current Version A display.
2. **AI explanation:** current scorer top actions and why.
3. **Why this is in the queue:** active-query rationale.
4. **Label panel:** pairwise choice, plan choice, condition tags, confidence,
   public-info scope, and optional note.

Required UI affordances:

- quick buttons for common condition tags
- "this depends on speed"
- "this depends on hidden coverage"
- "best action not shown"
- "this is an upstream switch/scout issue"
- "make a counterfactual family from this"
- "hold this out for evaluation"

Do not make the UI ask the user to write JSON.

## Implementation Phases

### Phase V2.0 - Plan And Source Alignment

Files:

- `docs/boss_ai_rlhf_v2_implementation_plan.md`
- `docs/boss_ai_rl_training_plan.md`
- `docs/project_roadmap.md`

Work:

- Add this plan.
- Link it from the existing BOSSAI-004 roadmap.
- Keep Version A as the current shipped state.

Verification:

```powershell
python tools\audit\check_docs_navigation.py
```

### Phase V2.1 - Schema Extension

Files:

- `tools/boss_ai_preference/SCHEMA.md`
- `tools/boss_ai_preference/data.py`
- `tools/boss_ai_preference/__main__.py`
- `tools/audit/check_boss_ai_preference.py`

Work:

- Accept v2 optional fields while continuing to read v0 rows.
- Add validation for `confidence`, `lesson_type`, `condition_tags`,
  `public_info_scope`, `counterfactual_group`, and `holdout`.
- Add CLI flags to `prefer` for the new fields.
- Preserve replacement behavior for duplicate fixture/action pairs.

Verification:

```powershell
python -m tools.boss_ai_preference validate
python tools\audit\check_boss_ai_preference.py
```

### Phase V2.2 - Feature Extraction

Files:

- `tools/boss_ai_preference/features.py`
- `tools/boss_ai_preference/damage_estimates.py`
- `tools/boss_ai_preference/threat_availability.py`
- `tools/audit/check_boss_ai_preference.py`

Work:

- Compute feature vectors for every fixture/action.
- Keep feature names stable and readable.
- Include source links for features derived from threat availability.
- Write `audit/boss_ai_preference/feature_report.json`.

Verification:

```powershell
python -m tools.boss_ai_preference feature-report
python tools\audit\check_boss_ai_preference.py
```

### Phase V2.3 - Active Queue

Files:

- `tools/boss_ai_preference/active_queue.py`
- `tools/boss_ai_preference/__main__.py`
- `tools/boss_ai_preference/app.py`
- `tools/audit/check_boss_ai_preference.py`

Work:

- Build candidate pools from fixtures, labels, debugger outputs, and trace
  captures.
- Score candidates with the readable priority formula.
- Emit Markdown and JSON queue reports.
- Add a browser queue tab.

Outputs:

- `audit/boss_ai_preference/active_queue.md`
- `audit/boss_ai_preference/active_queue.json`

Verification:

```powershell
python -m tools.boss_ai_preference active-queue
python tools\audit\check_boss_ai_preference.py
```

### Phase V2.4 - Counterfactual Fixture Families

Files:

- `tools/boss_ai_preference/counterfactuals.py`
- `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`
- `tools/boss_ai_preference/SCHEMA.md`
- `tools/audit/check_boss_ai_preference.py`

Work:

- Generate legal boundary variants from labeled fixtures.
- Store generated fixtures separately or mark them with `generated: true`.
- Ensure all generated fixtures still obey public-info constraints.
- Add grouped UI display.

Verification:

```powershell
python -m tools.boss_ai_preference generate-counterfactuals --dry-run
python tools\audit\check_boss_ai_preference.py
```

### Phase V2.5 - Lesson Report

Files:

- `tools/boss_ai_preference/lessons.py`
- `tools/boss_ai_preference/labels/boss_ai_lessons.jsonl`
- `tools/boss_ai_preference/__main__.py`
- `tools/audit/check_boss_ai_preference.py`

Work:

- Convert labels into candidate structured lessons.
- Detect conflicts and stale direct actions.
- Require manual status promotion from `candidate` to `accepted`.
- Emit lesson coverage by leader, lesson type, and feature.

Outputs:

- `audit/boss_ai_preference/lesson_report.md`
- `audit/boss_ai_preference/lesson_report.json`

Verification:

```powershell
python -m tools.boss_ai_preference lesson-report
python tools\audit\check_boss_ai_preference.py
```

### Phase V2.6 - Offline Preference Model

Files:

- `tools/boss_ai_preference/reward_model.py`
- `tools/boss_ai_preference/features.py`
- `tools/boss_ai_preference/__main__.py`

Work:

- Fit a small pairwise model over feature differences.
- Respect `holdout`.
- Print readable feature weights and disagreement examples.
- Compare model predictions to current Boss AI debugger scores where available.

Outputs:

- `audit/boss_ai_preference/reward_model_report.md`
- `audit/boss_ai_preference/reward_model_report.json`

Verification:

```powershell
python -m tools.boss_ai_preference fit-model
python -m tools.boss_ai_debugger regress --json-out audit/boss_ai_preference/regression_report.json
```

### Phase V2.7 - Proposal Generator

Files:

- `tools/boss_ai_preference/proposals.py`
- `tools/boss_ai_preference/__main__.py`
- `tools/audit/check_boss_ai_preference.py`

Work:

- Generate candidate changes with evidence, risks, worsened examples, and
  required verification.
- Separate fixture/schema/report changes from ROM behavior changes.
- Require human approval before any source edit.

Outputs:

- `audit/boss_ai_preference/proposals.md`
- `audit/boss_ai_preference/proposals.json`

Verification:

```powershell
python -m tools.boss_ai_preference propose
python tools\audit\check_boss_ai_preference.py
```

### Phase V2.8 - Optional Simulation Lab

Only start this after Phases V2.1-V2.7 are useful.

Files:

- `tools/boss_ai_preference/sim_lab.py`
- `tools/trace/boss_ai_state_factory.py`
- `tools/damage_debugger/` helpers where appropriate

Work:

- Generate realistic battle states from current trainer teams.
- Run candidate policies/scoring tables offline.
- Use simulation to propose active-query states, not to auto-author ROM policy.
- Include scripted opponent personalities only as stress tests.

Verification:

- deterministic seeds
- reproducible state dumps
- no hidden-info reads in generated fixtures
- reports name all assumptions

## Quality Gates

V2 is not complete until all of these hold:

- Old labels load unchanged.
- New labels validate with structured fields.
- Active queue explains why each question is worth the user's time.
- Counterfactual families preserve public-info legality.
- Lesson report distinguishes direct stale actions from portable principles.
- Offline model has holdout metrics and readable feature weights.
- Proposal report names improved and worsened examples.
- ROM edits remain manual, small, and auditable.
- Boss AI source changes still pass the Boss AI audit floor.

## Non-Goals

- No neural model in the ROM.
- No opaque policy blob.
- No auto-generated asm tables without human review.
- No hidden-info training target.
- No optimizing only for win rate.
- No treating all old labels as timeless after teams/moves change.

## Practical Next Step

Implement Phase V2.1 first. The schema extension unlocks every other phase while
keeping Version A usable. After that, Phase V2.3 active queue gives the largest
immediate value because it reduces wasted human labels.
