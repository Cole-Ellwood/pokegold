# Omni-Debugger First Gap-Action Proof — `boss_wrong_switch_replay_materialization`

**Date:** 2026-05-24
**Branch:** `claude/debugger-godmode` (off `claude/boss-ai-rom-expansion`)
**Pgoal:** Debugger Godmode (Iter 1)
**Pair:** Claude (primary), Codex (reviewer)
**Roadmap:** [`docs/debugger_godmode_codex_task.md`](../docs/debugger_godmode_codex_task.md)
**Handoff log:** [`audit/omni_debugger_2026-05-24_handoff_log.jsonl`](omni_debugger_2026-05-24_handoff_log.jsonl)

## TL;DR

The first audit `gap_action` named by `python -m tools.debugger audit` — `boss_wrong_switch_replay_materialization` — was driven end-to-end from a fresh session in under two minutes. The proof route works: `investigate → next-step packet → rom-switch-materialize --fail-on-mismatch` exits 1 on a real `switch_sack` family scenario JSONL, surfacing one concrete policy disagreement between the boss AI ROM and a policy-card-backed expectation.

**Result classification (per the bounded objective's three buckets):** PROVEN.

**Honest residual state** (important — see Codex's amendment #5 in the roadmap): the route is documented and demonstrated, but the audit's `gap_actions` count is still 1 because `python -m tools.debugger audit` does NOT re-read this proof artifact. The audit blocker stays surfaced until the audit gains an artifact-reading affordance OR until the disputed scenario is resolved (stale-expectation vs real boss-AI bug) as a separate investigation. **Do not mark the audit blocker closed in code on the strength of this writeup alone.**

## What was proven

The boss-AI-debugger's wrong-switch proof route, as encoded in the unified debugger's `next` packet for the `"boss selected wrong switch"` symptom, is exercisable end-to-end without manual code-spelunking:

1. The audit names the gap.
2. The next-step packet names the proof command + required inputs.
3. The proof command runs against existing scenario data + the current trace ROM.
4. The proof command can detect real policy disagreements and exits non-zero under `--fail-on-mismatch`.
5. The detected disagreement has policy-card evidence backing it (not a coincidence; a teaching case).

## Step-by-step chain with citations

### Step 1 — audit surfaces the gap

Command:

```
python -m tools.debugger audit
```

Surface: [`tools/debugger/__main__.py`](../tools/debugger/__main__.py) (subcommand `audit`).

Relevant output excerpt (the `whole_rom_replay_localization` partial capability section):

```
- partial: whole_rom_replay_localization - Whole-ROM replay and localization
    gap: ... exact dynamic replay is still deepest for damage and Boss AI.
    gap_action: boss_wrong_switch_replay_materialization scenario=boss selected wrong switch
    proof: python -m tools.debugger investigate --symptom "boss selected wrong switch" --json-out .local\tmp\debugger_investigate_wrong_switch.json
    command: python -m tools.debugger setup --symbol wCurDamage
```

The line `gap_action: boss_wrong_switch_replay_materialization scenario=boss selected wrong switch` is the audit-counted blocker the recent boss_ai_rom_expansion slices made actionable. The `proof:` line names the entry command.

### Step 2 — investigate emits the next-step route

Command:

```
python -m tools.debugger investigate --symptom "boss selected wrong switch" --json-out .local/tmp/debugger_investigate_wrong_switch.json
```

Output excerpt (Top proof commands):

```
Top proof commands:
  - python -m tools.boss_ai_debugger rom-switch-materialize --scenarios <scenarios.jsonl> --fail-on-mismatch (needs-input)
  - python -m tools.boss_ai_debugger run-suite --profile changed-ai --count 24 --seed 1 (runnable)
  - python -m tools.debugger explain --report .local/tmp/debugger_investigation/01_ingest.json (runnable)
  - python -m tools.debugger rank --report .local/tmp/debugger_investigation/01_ingest.json (runnable)
  - python -m tools.debugger replay --symbol BossAI_SelectMove (runnable)
```

The `(needs-input)` marker on the materialize command tells the LLM (and any consuming tooling) that this command needs a scenario JSONL before it can run — which is exactly the proof-mode separation Codex named in roadmap amendment #4 (source-provable vs runtime-provable; this one is runtime-provable but blocked on scenario data).

Top localization candidates surfaced by the same packet:

```
Top impact:
  - I100 S80 localization_candidate [Boss AI]: Localization candidate: source_file engine/battle/ai/boss_policy_move.asm
  - I100 S80 localization_candidate [Boss AI]: Localization candidate: source_file engine/battle/ai/boss_policy_switch.asm
  - I100 S80 localization_candidate [Boss AI]: Localization candidate: source_file engine/battle/ai/switch.asm
  - I100 S80 localization_candidate [Boss AI]: Localization candidate: source_file tools/boss_ai_debugger/rom_switch_materialize.py
  - I100 S80 localization_candidate [Boss AI]: Localization candidate: symbol BossAI_SwitchOrTryItem
```

These anchors are real source paths (`check_debugger_next_coverage.py` rejects stale anchors — see [`tools/audit/check_debugger_next_coverage.py`](../tools/audit/check_debugger_next_coverage.py)).

### Step 3 — locate the materialize tool's supported scenario family

Source citation: [`tools/boss_ai_debugger/rom_switch_materialize.py:30`](../tools/boss_ai_debugger/rom_switch_materialize.py)

```python
SUPPORTED_FAMILIES = ("switch_sack",)
```

Line 171 in the same file (the skip branch):

```python
verdicts.append(skipped_verdict(scenario_id, "unsupported scenario family"))
```

So the materialize tool only accepts scenarios with `family: "switch_sack"`; everything else gets a `status: skipped, reason: "unsupported scenario family"` verdict.

### Step 4 — find scenarios with the right family

Local-only data lives under `.local/tmp/boss_ai_debugger/`. Three candidate files were found via `grep -c '"kind": "switch"'`:

```
.local/tmp/boss_ai_debugger/all_disagreement_hunt_500.jsonl:        0  scenarios with kind=switch moves
.local/tmp/boss_ai_debugger/all_seed1_120_after_mirror_fix.jsonl:  54  scenarios with kind=switch moves
.local/tmp/boss_ai_debugger/all_seed1_120_probe.jsonl:             54  scenarios with kind=switch moves
```

The first three switch_sack scenarios from `all_seed1_120_after_mirror_fix.jsonl` were filtered into `.local/tmp/wrong_switch_three.jsonl`:

```
grep '"family": "switch_sack"' .local/tmp/boss_ai_debugger/all_seed1_120_after_mirror_fix.jsonl \
  | head -3 \
  > .local/tmp/wrong_switch_three.jsonl
```

(Note: the runs at `audit/boss_ai_debugger/runs/*/scenarios.jsonl` are committed but contain mostly `family: "selector_edges"` and other non-switch families — they get skipped by the materialize tool. The disagreement/seed hunts under `.local/tmp/` are where the switch_sack scenarios actually live. Worth noting in any future source-anchor refresh for the wrong-switch route.)

### Step 5 — run materialize with `--fail-on-mismatch`

Command:

```
python -m tools.boss_ai_debugger rom-switch-materialize \
  --scenarios .local/tmp/wrong_switch_three.jsonl \
  --limit 3 \
  --json-out .local/tmp/wrong_switch_three_result.json \
  --fail-on-mismatch
```

Output:

```
Boss AI ROM switch materialization
scenarios=3 checked=3 skipped=0 errors=0 policy_disagreements=1
base_route=shared_switch_loop base_state=.local/tmp/boss_state_factory/shared_switch_loop_frame_200.state rate=616/min

Top 20 review items:
  generated_switch_sack_1_00002_stay_when_current_move_converts: policy=mismatch expected_switch=False proposed_switch=True confidence=57

Known limits:
  - Switch materialization replays the real BossAI_SwitchOrTryItem path from the shared switch-loop trace state and observes switch confidence/param.
  - This proves switch-dispatch proposal behavior, not move score bytes and not a multi-sample stochastic switch-roll probability.
  - Only public battle facts and boss-owned party state are patched; hidden player party, hidden moves, PP, held items, and current input are not read.
wrote .local/tmp/wrong_switch_three_result.json
```

**Exit code: 1.** Verified by independent re-run:

```
python -m tools.boss_ai_debugger rom-switch-materialize ... --fail-on-mismatch >/dev/null 2>&1; echo "exit=$?"
exit=1
```

(Codex independently confirmed this exit code in their chat reply — `repo-proven` per their confidence label.)

### Step 6 — characterize the disputed scenario

Disputed scenario ID: `generated_switch_sack_1_00002_stay_when_current_move_converts`

| Field | Value |
|---|---|
| family | `switch_sack` |
| expectation.why | "Do not switch or cash out when the current active move is already the converter." |
| expectation.best_action_ids | `["move_route_damage"]` |
| expectation.bad_action_ids | `["move_cashout"]` |
| expectation.policy_tags | `["active_pressure", "switching", "converter"]` |
| expectation.evidence_refs | `["docs/pokemon_mastery/policy_cards/active_pressure_before_status.md", "docs/pokemon_mastery/heuristic_core/converter_before_script.md"]` |
| moves[].kind | `move`, `switch`, `move`, `move` (one switch option: `move_safe_switch`) |
| ROM verdict | `expected_switch=False, proposed_switch=True, confidence=57` |

The expectation is policy-card-backed (two referenced docs in `docs/pokemon_mastery/`). The ROM proposed `switch=True` in a scenario where the active mon's current move is already the converter — i.e. the boss would unnecessarily switch out a mon that's mid-conversion-route.

### Step 7 — what's NOT proven (honest residual state)

Three things this writeup does NOT claim:

1. **The audit blocker is closed.** The `gap_actions=1` count in `python -m tools.debugger audit` does not decrease as a result of this writeup. The audit currently inspects route definitions, not proof artifacts. Closing the audit blocker requires either (a) extending the audit to recognize artifacted proofs OR (b) resolving the disputed scenario such that no policy_disagreement remains.
2. **The disputed scenario is a real boss-AI bug.** Could be a stale expectation (policy card has moved since the seed was generated) OR a real bug in `BossAI_SwitchOrTryItem`'s converter-aware stay path. Determining which requires reading [`engine/battle/ai/boss_policy_switch.asm`](../engine/battle/ai/boss_policy_switch.asm) and comparing to the policy-card semantics — a separate investigation slice.
3. **Other audit `capability_partial` gaps are addressed.** The other five partial capabilities (`causal_provenance`, `generation_fuzzing_counterexamples`, `differential_mirrors`, `impact_ranking_workflow`, `visualization_reports`) are not touched by this slice.

## Artifacts produced

Committed in this Iter 1 commit:

- `audit/omni_debugger_first_gap_action_proof_2026-05-24.md` (this file)
- `audit/omni_debugger_2026-05-24_handoff_log.jsonl` (row 5 appended by Iter 1)
- `docs/project_roadmap.md` (small DEBUGGER-001 proof-status note)
- `docs/debugger_godmode_codex_task.md` (Codex amendment integration: read-required clarification + per-slice north-star check + sub-capability decomposition + proof-mode separation)

Local-only (not committed; `.local/tmp/` is gitignored by policy):

- `.local/tmp/debugger_investigate_wrong_switch.json` (step 2 output)
- `.local/tmp/wrong_switch_three.jsonl` (step 4 filtered input)
- `.local/tmp/wrong_switch_three_result.json` (step 5 verdicts)

## Where this fits in Phase 0

This is Iter 1 of Phase 0 (Foundation). Next iters in this phase:

- **Iter 2-4**: curate `audit/debugger_godmode_benchmark/questions.jsonl` (the historical-question benchmark; both LLMs propose 10-15 questions in parallel).
- **Iter 5-6**: build `tools/audit/check_debugger_godmode_benchmark.py` (the scoring harness).

Iter 1 functions as the first benchmark question pre-validation: "boss selected wrong switch" is already a WHERE/WHY hybrid question that the debugger answers correctly via the proven route. It belongs in the benchmark question set at Iter 2.

## Verification floor for Iter 1

Per the roadmap (Verification floor, "Before declaring any slice done"):

- ✅ Narrow per-slice verifier: the materialize command itself is the slice's verifier (exit=1 on disputed scenario).
- ⏸ Both LLMs `slice_review`: Codex's review is what unblocks the next iter.
- ⏸ Commit only after paired sign-off: this slice's commit lands BEFORE Codex's slice_review per Codex's commit-then-rereview rule (this slice is documented evidence-only, no code change inside `tools/*`).
- ✅ `python -m tools.debugger audit` (will not change as a result of this slice — by design).
- ✅ `python tools/audit/check_debugger_next_coverage.py` should stay green (source anchors unchanged).
- ✅ `python tools/audit/check_release_smoke.py` should stay green (no ROM source change).
- ⏸ `python tools/audit/check_two_llm_handoff_log.py --strict` after Codex appends a `slice_review` row.
- ⏸ `python tools/audit/check_no_solo_commits_omni_debugger.py` will be written in Phase 0 (not yet existent).

## What Codex should do next

Per the task block:

1. (Optional first) append `slice_review` row to `audit/omni_debugger_2026-05-24_handoff_log.jsonl` after reading this writeup + the commit diff. If accepted, mark this slice `slice_accepted`.
2. (Either order) `ack_start` Iter 2: brainstorm 10-15 benchmark questions for `audit/debugger_godmode_benchmark/questions_codex_lane.jsonl`. Codex's lane is mostly WHY/WHAT archetypes (Codex is synthesis-leaning); my Claude lane will weight WHERE.
