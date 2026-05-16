# Boss AI Debugger Closed-Loop Alignment Plan

Status: planning artifact. Created 2026-05-15.

Purpose: define how to keep using the Boss AI debugger to find AI-vs-expert
disagreements, decide which disagreements are real strategic bugs, patch Boss
AI scoring safely, and repeat until the in-game AI matches the current mastery
policy as closely as ROM constraints allow.

This document is a plan only. It does not authorize implementation by itself.

## Goal Statement

Run Boss AI alignment as a closed-loop engineering campaign: repeatedly search
for ROM-confirmed places where the in-game AI and my current best GSC policy
disagree, classify each disagreement with mastery evidence, patch only the
confirmed strategic bugs that can be represented legally in the ROM scoring
system, and keep rerunning the loop until no high-confidence untriaged strategic
bug remains.

The goal is not to make the debugger, generator, or Python scorer decide what is
"best" by itself. The debugger's job is to keep the evidence, labels, ROM traces,
and review queue organized enough that I can apply the same policy consistently
without forgetting prior lessons.

## Success Criteria

The loop is working when each Boss AI change starts from reproducible
disagreement evidence and ends with a reproducible proof that:

- the target disagreement class is reduced or eliminated in generated and
  ROM-materialized checks,
- no public-info, no-cheat, selector, trace, memory, or live-capture gate
  regresses,
- the changed score rules remain explainable from source labels and public
  facts,
- the remaining disagreements are either accepted close calls, mastery-note
  gaps, generator expectation bugs, or ROM constraint tradeoffs.

The long-run target is not "zero generated mismatches at any cost." The target
is "no known high-confidence strategic bug remains untriaged, unowned, or
uncovered by a regression case."

## Operating Loop

### 1. Freeze The Baseline

Before changing AI code, record the current behavior.

Commands:

```powershell
python -m tools.boss_ai_debugger run-suite --profile changed-ai --count 200 --seed 1 --runs-dir audit\boss_ai_debugger\runs
python tools\audit\check_boss_ai_debugger_done.py --generated-count 24
```

Evidence to keep:

- run-suite metadata and Markdown summary,
- done-gate JSON,
- `git status --short`,
- current `pokegold.gbc`, `pokegold_trace.gbc`, and symbol hashes from the run
  artifacts.

Do not begin a behavior patch if the baseline done gate is already failing,
unless the failure is the explicit target of the patch.

### External Research Gate

Use web search when the question is about current tools, emulator/debugger APIs,
Python testing libraries, property-based testing practice, data-store formats,
or any other implementation detail that may have changed. Prefer primary sources
and official documentation for tool behavior.

Do not use web search to decide GSC strategy. Strategy decisions should come
from mastery notes, replay reviews, simulator knowledge, and explicit current
judgment. External research can improve the debugger, but it should not become
an unreviewed policy source for ROM behavior.

### 2. Generate Disagreement Batches

Run broad search first, then focused search around the largest disagreement
cluster.

Broad pass:

```powershell
python -m tools.boss_ai_debugger generate --family all --count 5000 --seed <seed> --out .local\tmp\boss_ai_debugger\alignment_all_<seed>.jsonl
python -m tools.boss_ai_debugger batch-simulate --scenarios .local\tmp\boss_ai_debugger\alignment_all_<seed>.jsonl --json-out .local\tmp\boss_ai_debugger\alignment_all_<seed>_batch.json --quiet
python -m tools.boss_ai_debugger review-queue --report .local\tmp\boss_ai_debugger\alignment_all_<seed>_batch.json --limit 200 --max-per-lesson 20 --json-out .local\tmp\boss_ai_debugger\alignment_all_<seed>_queue.json
```

Focused pass examples:

```powershell
python -m tools.boss_ai_debugger generate --family spikes_spin --count 5000 --seed <seed> --out .local\tmp\boss_ai_debugger\alignment_spikes_spin_<seed>.jsonl
python -m tools.boss_ai_debugger generate --family mastery_policy --count 2000 --seed <seed> --out .local\tmp\boss_ai_debugger\alignment_mastery_<seed>.jsonl
```

Search expectations:

- use at least three seeds before concluding a class is stable,
- keep the top queue diverse for first-pass review,
- allow duplicates only after the root cause class is clear.

The 2026-05-15 smoke hunt found 167 reviewable cases from 500 mixed scenarios;
the top 100 were all hazard-retention/Rapid Spin/Spikes cases. That is the
current first target class.

### 3. Prove The Disagreement Is In-Game Behavior

For any class that may drive an AI code patch, materialize representative
scenarios into the trace ROM.

Command:

```powershell
python -m tools.boss_ai_debugger rom-score-materialize --scenarios <selected_scenarios.jsonl> --limit <n> --compare-fast-score --json-out .local\tmp\boss_ai_debugger\<class>_rom_score_materialization.json
```

Minimum evidence for a patch candidate:

- at least 20 representative scenarios checked,
- zero skipped/errors,
- ROM selector top agrees with debugger top for every checked scenario,
- hook-equivalence mismatches are zero,
- exact score-byte mismatches are either zero or explained and decision-neutral.

If ROM selector top does not match the debugger top, fix the debugger or
materialization path before touching AI scoring.

### 4. Triage Each Disagreement Class

Group queue items by root cause, not by individual scenario id.

For each class, record:

- policy tag and mastery evidence refs,
- condition tags that define the class,
- ROM top action and probability,
- expected best, acceptable, bad, and catastrophic actions,
- whether the AI is wrong, the expectation is wrong, or the case needs more
  context,
- source scoring rules that made the ROM choose its action,
- smallest public fact that flips the preferred answer.

Useful commands:

```powershell
python -m tools.boss_ai_debugger decision-trace --scenario <scenarios.jsonl> --scenario-id <id> --json-out .local\tmp\boss_ai_debugger\<id>_decision_trace.json
python -m tools.boss_ai_debugger counterfactual --scenario <scenarios.jsonl> --scenario-id <id> --json-out .local\tmp\boss_ai_debugger\<id>_counterfactual.json
python -m tools.boss_ai_debugger minimize --scenario <scenarios.jsonl> --scenario-id <id> --json-out .local\tmp\boss_ai_debugger\<id>_minimized.json
python -m tools.boss_ai_debugger localize --scenarios <scenarios.jsonl> --json-out .local\tmp\boss_ai_debugger\<class>_localization.json
```

Classification rules:

- Strategic bug: mastery note is high-confidence, ROM behavior is confirmed,
  and the chosen action is bad, unreachable, or systematically overvalued.
- Close call: ROM top is acceptable, probability is modest, or answer-changing
  information is genuinely missing.
- Mastery gap: the expected answer depends on a policy not yet written or on a
  newly learned exception.
- Generator bug: the expectation contradicts its own condition tags, or the
  generated state cannot represent the policy it claims.
- ROM constraint: the desired behavior needs hidden info, too much memory, too
  much bank space, or scoring precision the current system cannot afford.

Only strategic bugs proceed to scoring design.

### 5. Design The Smallest Scoring Patch

For each strategic bug class, write a short patch proposal before editing asm.

The proposal must include:

- target source labels,
- public facts read,
- no-cheat boundary statement,
- expected score movement in points or tier weight,
- examples that should flip,
- examples that must not flip,
- memory and bank risk,
- regression scenarios to add,
- expected effect on current live captures.

Patch shape preference:

1. tune an existing weight,
2. add a narrow branch in an existing helper,
3. add a helper only if the branch would otherwise be unreadable,
4. avoid new WRAM unless there is no clear alternative.

For the current hazard-retention cluster, the likely proposal area is not
"make Explosion bad." It is more likely:

- improve when useful Spikes layers outrank cash-out,
- remove residual bad Spikes rolls when Rapid Spin makes the hazard turn fake,
- distinguish capped/failing Spikes from live hazard progress,
- make immediate pressure choose live damage before self-KO unless cash-out has
  a named converter.

### 6. Implement One Class At A Time

Do not patch multiple strategic classes in one iteration unless they share the
same source rule and the same regression set.

Patch cycle:

1. edit asm and debugger mirror for exactly one class,
2. add targeted generated scenarios or fixtures,
3. rebuild ROMs if asm changed,
4. refresh only the trace artifacts needed for the class,
5. run focused gates,
6. run the full changed-AI and done gates before declaring the class closed.

The debugger mirror is not the authority, but it must track the ROM after every
accepted behavior patch.

### 7. Validate The Patch

Focused gates:

```powershell
wsl make pokegold.gbc pokesilver.gbc
wsl make pokegold_trace.gbc
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_boss_ai_memory_budget.py
python -m tools.boss_ai_debugger batch-simulate --scenarios <focused_corpus.jsonl> --json-out .local\tmp\boss_ai_debugger\<class>_post_batch.json --quiet
python -m tools.boss_ai_debugger rom-score-materialize --scenarios <focused_selected.jsonl> --limit <n> --compare-fast-score --json-out .local\tmp\boss_ai_debugger\<class>_post_rom_score.json
```

Full gates:

```powershell
python -m unittest discover tools\boss_ai_debugger\tests
python tools\audit\check_boss_ai_selector_replay.py
python tools\audit\check_boss_ai_live_capture_ledger.py
python tools\audit\check_boss_ai_debugger_roadmap.py --generated-count 40 --check-rom-selector-materialization --check-rom-score-materialization
python tools\audit\check_boss_ai_debugger_done.py --generated-count 24
```

Completion criteria for one class:

- target class reviewable count drops to zero or to documented accepted close
  calls,
- no new high-severity class appears in the same focused generator,
- ROM materialization confirms the changed top action on representative cases,
- selector replay and live capture ledger stay green,
- no-cheat and memory gates stay green,
- coverage report still shows the touched rules as executed.

### 8. Preserve Lessons And Regressions

Every accepted strategic bug should leave behind durable evidence.

Artifacts:

- one minimized scenario or fixture per distinct branch,
- one policy-card or quick-test update if the mastery note was sharpened,
- one debugger regression if the Python mirror changed,
- one trace/materialization artifact if the ROM path was subtle,
- one changed-AI run summary comparing before and after.

If a disagreement is rejected as a generator bug or mastery gap, update the
generator expectation or mastery note before rerunning the hunt.

### 9. Decide When To Stop

Stop an alignment campaign only after all of these are true:

- three fresh seeds across `all`, targeted family, and `mastery_policy` produce
  no untriaged high-confidence strategic bugs,
- the review queue's remaining top items are accepted close calls, generator
  issues, or documented ROM constraints,
- full done gate passes,
- changed-AI previous-run diff shows the intended behavior changed and no
  unrelated severe behavior class appeared,
- the current disagreement ledger names every remaining class and owner.

Do not stop merely because one batch is clean.

## Disagreement Ledger Template

Use this table for each campaign.

| Field | Required content |
| --- | --- |
| class_id | Short name, e.g. `hazard_spin_cashout_overbias` |
| status | `new`, `triaging`, `strategic_bug`, `close_call`, `mastery_gap`, `generator_bug`, `rom_constraint`, `fixed` |
| policy_refs | Mastery cards or quick tests |
| scenario_refs | Representative scenario ids and minimized files |
| rom_evidence | ROM materialization JSON and checked counts |
| source_cause | Rule ids and source labels |
| proposed_patch | Weight/branch/helper sketch |
| regression_plan | Generated fixtures, debugger tests, audit checks |
| outcome | Post-patch metrics and remaining risk |

## Current First Campaign

Class: `hazard_spin_cashout_overbias`.

Evidence:

- `.local\tmp\boss_ai_debugger\top_100_disagreements.md`
- `.local\tmp\boss_ai_debugger\top_100_disagreements_rom_score_materialization.json`

Observed pattern:

- generated mixed search found 167 reviewable cases from 500 scenarios,
- top 100 were all hazard-retention/Rapid Spin/Spikes,
- ROM materialization confirmed the decision surface for all 100,
- the AI is often too eager to pick `Explosion`,
- when Rapid Spin is live, it can still allow bad `Spikes` rolls,
- when Spin is absent or blocked, it often still cashes out instead of making
  hazard progress.

Next planning step before implementation:

1. split the 100 cases into three sub-classes: live-spin attack preference,
   no-spin Spikes preference, capped-Spikes anti-click preference,
2. pick 5 representative ROM-materialized scenarios for each sub-class,
3. trace source contributions for those 15 cases,
4. draft one scoring proposal per sub-class,
5. choose the smallest proposal that improves the most severe class without
   worsening the other two.
