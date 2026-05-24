# Phase 1 Planning — Capability Buildout vs Benchmark Score

**Status:** revised 2026-05-24 after Codex Iter 4 commit (1a7289fb) landed the harness + baseline_2026-05-24.md. Re-revised post-Iter-5 with actual probe data and revised Iter 6+ plan.

**Author:** Claude. Iter 4 review-only work; Iter 5 + Iter 6 plan revisions paired with Codex.

**Provenance:** ships in the Iter 5 commit (paired Codex slice_review).

## Iter 5 actual result (ROM/audit-replayable)

Iter 5 enriched four strings in `tools/debugger/next_steps.py`:
- `EVIDENCE_STANDARDS["wrong_switch"]` — added BossAI_SwitchOrTryItem, switch WRAM targets, boss_policy_switch source anchors, materialization command (confirmed in `engine/battle/ai/boss_policy_switch.asm` + `items.asm`).
- `DISPROOF_STANDARDS["wrong_switch"]` — added the negative shape (returned route omits rom-switch-materialize / routes to damage/banking fallbacks).
- `EVIDENCE_STANDARDS["haki_taunt_read"]` — added the ai_haki_excluded exclusion table (in `data/trainers/`), boss policy switch surface (BossAI_OracleHakiRead / BossAI_QueueHakiTaunt in `boss_policy_switch.asm:24,142`), and tier-and-class gate logic.
- `DISPROOF_STANDARDS["haki_taunt_read"]` — added the stale-route shape (bespoke Morty path without uniform oracle refactor).

Re-benchmark (run `python tools/audit/check_debugger_godmode_benchmark.py --baseline --markdown-out audit/debugger_godmode_benchmark/iter5_evidence_disproof_2026-05-24.md`):

| Dimension | Pre (baseline_2026-05-24) | Post-Iter-5 | Delta |
|---|---|---|---|
| source_anchor | 5/29 | 5/29 | +0 |
| proof_command | 10/29 | 10/29 | +0 |
| regression_gate | 12/29 | 12/29 | +0 |
| evidence_standard | 3/29 | 6/29 | +3 |
| disproof_standard | 5/29 | 5/29 | +0 |
| pass_rate (5-of-5) | 0.034 (1/29) | 0.034 (1/29) | +0 |

No regressions on any dimension. Pass-rate is unchanged because the +3 evidence lifts hit questions that still fail at least one other dimension (source_anchor or proof_command). That's expected and goal-aligned: dimension lifts are the leading indicator; pass-rate flips need broader coverage.

The +3 evidence lifts:
1. `codex_where_boss_wrong_switch` — correctly routed to wrong_switch. Overlap 2 → 13. Intentional.
2. `claude_where_boss_ai_haki_eligibility_gate` — correctly routed to haki_taunt_read. Overlap 2 → 11. Intentional.
3. `claude_why_audit_says_gap_actions_1_after_iter1` — MIS-ROUTED to wrong_switch. Overlap 2 → 4. **Incidental** — token overlap from the enriched wrong_switch string accidentally covers this question's expected words. The route is still wrong (the question is about pgoal audit gap_actions, not boss AI switching). The Iter 6 routing fix should re-route this question to a new symptom_class; the incidental lift is benign for now but the routing bug remains.

Per Codex amendment #2 ("don't enrich misrouted classes"), the wrong_switch enrichment itself was honest — it describes what wrong_switch route actually evidences. The mis-route is the bug. Disclosed for the record.

## Iter 6 — the bigger lever: routing-gap fix

The probe (`.local/tmp/iter5_route_probe.json`) revealed the real Phase 1 bottleneck: **18 of 29 questions route to `general`** because their domain has no symptom_class entry in `NEXT_STEP_ROWS` and no triage match. Five more **mis-route** to specific-but-wrong classes (keyword leakage).

| Category | Failing question IDs | Route now → should-be |
|---|---|---|
| pgoal/audit internals | claude_why_audit_says_gap_actions_1_after_iter1, claude_what_durable_proof_artifact, claude_what_new_release_smoke_audit | wrong_switch / general → new `pgoal_audit_internals` class |
| asm gotchas | claude_why_farcall_clobbers_hl, claude_why_cross_bank_call_silent_garbage, claude_why_stat_stage_byte_not_multiplier | general → new `asm_gotcha_reference` class |
| repo navigation | claude_where_rom_bank_free_space, codex_where_hm_field_tools, codex_where_farfetchd_stick_role, codex_where_yanma_ariados_showcases | general → new `repo_navigation` class |
| save format | claude_what_save_format_bump_impact | general → new `save_format_change` class |
| trace ROM vs release | claude_why_trace_rom_differs_from_release | general → new `trace_rom_divergence` class |
| script VM internals | codex_how_script_entry_state_space, codex_what_map_script_rom_mirror | general → existing `script_vm_impossible_state` (or new sibling) |
| QoL gates | codex_what_repel_renewal_guard, codex_what_release_gate_for_qol_changes | general → new `qol_gate_design` class |
| wild encounters | codex_what_first_wild_route29_reset_repro (already passes), others | already in `crash_reset` |
| damage/role/typing | codex_why_physical_damage_5x, claude_where_type_chart (mis-routed to ko_band_pressure), claude_where_add_new_move (mis-routed) | needs new classes for damage debugger + type chart navigation + add-a-move |
| boss AI navigation | claude_where_boss_ai_haki_eligibility_gate (now passes ev), claude_where_boss_ai_wramx_reserve (mis-routed to observation_tendency_behavior), codex_why_boss_ai_no_current_turn_input | new `boss_ai_navigation` class for the "where" cases |
| boss AI switch debug | codex_where_boss_wrong_switch (now passes ev), codex_why_switch_sack_converter_disagreement | existing wrong_switch class; rename/refine for the disagreement case |
| wram bank crash | codex_why_wram_bank_ret_crash (mis-routed) | new `wram_bank_ret_crash` class (relates to crash_reset) |
| damage matchup CLI | codex_where_damage_matchup_cli (mis-routed) | new `damage_matchup_cli` class |
| hidden power | codex_why_hidden_power_immunity (already passes) | already in boss_ai_hidden_power_type |
| trainer evolution | codex_why_trainer_evolution_music_frozen (already passes) | already in script_vm_impossible_state |

Iter 6 plan: add ~10 new entries to `NEXT_STEP_ROWS` covering the categories above. Each entry needs `symptom_class`, `keywords` (for `_matching_rows`), `matched_lane`, `title`, `first_command`, `required_inputs`, `proof_limit`, `escalation_command`, plus matching entries in `SOURCE_REFS` / `EVIDENCE_STANDARDS` / `DISPROOF_STANDARDS` / `REGRESSION_GATES`. Expected lift: source_anchor 5/29 → ~20/29 (the new routes' source_refs contain the expected anchors), proof_command and regression_gate similarly. Pass-rate 0.034 → projected ~0.55–0.70 if routing is right.

## Concrete baseline (replaces earlier speculative ranking)

## Concrete baseline (replaces earlier speculative ranking)

From [`audit/debugger_godmode_benchmark/baseline_2026-05-24.md`](debugger_godmode_benchmark/baseline_2026-05-24.md):

- Total: 29 questions
- Passed: 1 (`codex_what_first_wild_route29_reset_repro`)
- Pass rate: 0.034 (3.4%)
- Threshold to ship: 0.85 (85%)

### Dimension-level pass counts (out of 29):

| Dimension | Pass count | % | Notes |
|---|---|---|---|
| evidence_standard | 3 | 10% | **Lowest — broadest fix opportunity.** Adding evidence_standard field to the debugger's investigate/next packet would flip ~20+ FAILs. |
| source_anchor | 5 | 17% | Tied for second-lowest. Localization is partial; closing the `whole_rom_replay_localization` audit gap helps here. |
| disproof_standard | 5 | 17% | Mirror of evidence_standard; same packet-shape fix would lift this. |
| proof_command | 10 | 34% | Mid. |
| regression_gate | 12 | 41% | Highest — debugger already proposes regression gates for most questions. |

### Closest-to-passing list (top 5)

Sorted by "fewest FAILing dimensions" (1 = ready to flip with one slice):

1. **`codex_why_trainer_evolution_music_frozen`** — 4/5 PASS (only proof_command failing). Cheapest possible Phase 1 win. WHY/hybrid archetype.
2. **`codex_where_boss_wrong_switch`** — 3/5 PASS (source 2/5 below threshold, evidence FAIL). 2 dimensions to flip.
3. **`claude_what_new_release_smoke_audit`** — 3/5 PASS (source 2/4 at threshold, evidence FAIL, disproof FAIL). 2-3 dimensions to flip depending on rubric.
4. **`codex_why_trainer_evolution_music_frozen`** is the single 4/5 question.
5. Others at 3/5: codex_what_repel_renewal_guard, codex_where_hm_field_tools, codex_what_release_gate_for_qol_changes, etc.

## Recommended first Phase 1 slice (Iter 5+)

Given the dimension counts, the highest-leverage slice is: **make the debugger's investigate/next packet ALWAYS render evidence_standard + disproof_standard fields when those exist in the route definition**.

Hypothesis: most failures on evidence_standard / disproof_standard aren't "the debugger has no idea" — they're "the debugger has the route data but the field isn't surfaced into the user-facing answer." A small change to the JSON output schema (and the report/visualize renderers) could lift these from 3/29 and 5/29 toward 20+/29.

Verify by:
1. Pick a failing question whose route in `tools/debugger/next_steps.py` HAS evidence_standard/disproof_standard data but isn't rendering.
2. Add the rendering.
3. Re-run baseline; expect dimension count jumps.

If the hypothesis is wrong (the data really isn't there), Phase 1 Iter 5 becomes "author evidence_standard for the missing routes" — a different, larger slice.

### Alternative cheapest slice

**`codex_why_trainer_evolution_music_frozen`** alone-flip: investigate why the harness scores proof_command FAIL for this question. Likely either (a) the route's proof_command differs from the question's expected proof_command in wording, or (b) the harness's token-overlap check is too strict on this specific pairing. Either way, one slice flips the question to PASS (giving 2/29 = 6.9% — a measurable, committable Phase 1 first win).

I'd run BOTH in Iter 5 (alone-flip first as a confidence-builder; broad evidence_standard rendering as the bigger leverage). Both should be doable in one Iter 5 slice with paired review.

## Phase 1 plan summary

- **Iter 5 (next)**: dimension-rendering fix for evidence_standard + disproof_standard. Re-run baseline; expect pass_rate jump.
- **Iter 6-15**: pick the next "closest-to-passing" question each iter; flip one at a time. Aim 50% pass rate at iter 15.
- **Iter 16-30**: tougher slices — source_anchor coverage improvements, audit capability_partial gap closures. Aim 70% pass rate.
- **Iter 31-50**: stretch — runtime-mode questions, harness v2 (run actual proof_commands).
- **Iter 51+**: verifier gate + ship at 85%+ pass rate.

## Open questions deferred to fresh-session pair

1. Should the harness gain a `--rubric strict|lenient` flag so we can compare progress on multiple scoring rubrics simultaneously? (E.g., a strict mode that requires ALL source_anchors hit, and a lenient that only requires top-3.)
2. The runtime-mode questions are mostly FAIL on proof_command — should we promote them to "run the proof_command and check exit code" semantics (Codex's flagged v2)?
3. As Phase 1 ships fixes that mutate tools/debugger/*, when do we re-baseline? Every commit? Once per iter? Once per phase?

---

*This doc was uncommitted at session end 2026-05-24. Fresh session: read this + the roadmap + the baseline file, propose Iter 5 to Codex, get slice_review, commit including this file.*

## What Phase 1 is

Per [`docs/debugger_godmode_codex_task.md`](../docs/debugger_godmode_codex_task.md) §"Phase 1 — Capability buildout (target: Iter 7-50, biggest phase)":

> Each iteration in Phase 1:
> 1. Pick the lowest-scoring benchmark question OR the gap that most blocks an unanswered question.
> 2. Implement the smallest capability change that lifts at least one benchmark question from FAIL to PASS.
> 3. Re-run the benchmark + audit; verify no regressions; commit.
> 4. Pair `slice_review` before commit.

The slice picker is the question with the highest *expected value per byte of code* — i.e., lifts the most failing questions per unit implementation work. Without baseline scores I can't compute this exactly; with baseline scores it becomes mechanical.

## Map: audit capability_partial gap → debugger sub_capability → benchmark questions affected

Per [`docs/debugger_godmode_codex_task.md`](../docs/debugger_godmode_codex_task.md) §"Decomposition into measurable sub-capabilities" + the audit's six `capability_partial` IDs:

| Audit gap | Sub-capability(s) closed | Questions in benchmark whose `sub_capabilities` array contains the sub-capability | Estimated impact (if gap fully closed) |
|---|---|---|---|
| `whole_rom_replay_localization` | source_locator + proof_runner (replay half) | Most WHERE (10) + the runtime/hybrid WHY/WHAT (~8) | High — touches ~18/29 questions |
| `causal_provenance` | behavior_explainer | Most WHY (11) | High — touches ~11/29 questions |
| `generation_fuzzing_counterexamples` | repro_planner | Hybrid WHATs + runtime questions (~5) | Medium — touches ~5/29 |
| `differential_mirrors` | proof_runner (mirror half) | Runtime questions + the disputed-scenario WHY (~5) | Medium — touches ~5/29 |
| `impact_ranking_workflow` | regression_suggester | WHATs naming regression gates (~5) | Medium — touches ~5/29 |
| `visualization_reports` | report_renderer | Indirect; every question's rendered answer (~29) but secondary | Low-direct, high-indirect |

**Note**: a question may have *multiple* required sub_capabilities. Lifting ONE question from FAIL → PASS requires ALL its required sub_capabilities to score above threshold. So gap closures are ANDs, not ORs, for the question scoring.

## Pre-baseline ranking (speculative; replace with real numbers once harness runs)

If the baseline tracks our intuition that source-mode questions score higher than runtime ones (because the existing debugger surfaces are mature on source-locator and weak on proof_runner / repro_planner), then Phase 1 should attack runtime/proof_runner gaps first.

Best-guess slice order (subject to harness output):

1. **`differential_mirrors`** — Codex's `codex_what_map_script_rom_mirror` and `codex_why_switch_sack_converter_disagreement` both name `python -m tools.debugger compare`-shape proof commands. The compare subcommand exists but its semantic mirror is "deep for damage and Boss AI only." Closing this to cover map scripts + the disputed switch_sack scenario would lift ~3-4 questions.
2. **`whole_rom_replay_localization` (replay half)** — many runtime/hybrid questions need a save-state setup + replay-and-observe loop. The existing `setup` and `replay` subcommands work for damage and Boss AI; extending to other surfaces is a moderate slice.
3. **`causal_provenance`** — broadest impact but largest scope (~11 questions). Better as Phase 1 mid-game once smaller wins land.
4. **`impact_ranking_workflow`** — narrow, mostly regression-gate guidance; might be a quick win.
5. **`generation_fuzzing_counterexamples`** — needed for repro_planner but the existing `generate` / `fuzz` subcommands cover damage already; extending takes time.
6. **`visualization_reports`** — last; secondary impact.

## What I'd like from Codex's harness output

Once `tools/audit/check_debugger_godmode_benchmark.py` runs and produces baseline:

1. **Per-question pass/fail** with breakdown (source_anchors_hit / proof_command_hit / regression_gate_hit / evidence_standard_rendered).
2. **Per-archetype pass rate** (WHERE / WHY / WHAT).
3. **Per-proof_mode pass rate** (source / hybrid / runtime).
4. **Per-sub_capability hit rate** (source_locator / behavior_explainer / repro_planner / proof_runner / regression_suggester / report_renderer).
5. **Top failing questions** sorted by "closest to passing" (i.e., questions where 3 of 4 components hit; flipping one component would lift the question).

(5) is the key signal — those are the cheapest wins. A slice that flips ONE component for ONE question is the smallest possible Phase 1 step; the whole-numbers question of which gap-closure to attack falls out of this.

## Open questions for Codex when the harness lands

1. Does the harness's per-question scoring distinguish "source_anchors hit" from "source_anchors COMPLETELY hit"? (i.e., top-N localization vs full set)
2. Does the harness re-run the question's `proof_command` and check exit code, or just look for the command name in the debugger's `Top proof commands` list?
3. Is the harness output reproducible across runs (deterministic)? Or does the debugger's investigate have any RNG (e.g., scenario sampling)?

## Stop conditions I'd apply in Phase 1

- If a slice claims to lift question X but the harness shows X still failing, revert and try a different slice.
- If two consecutive slices land with no benchmark movement, stop and inspect the harness scoring rubric (might be too strict to be moveable).
- Per the roadmap: "If at iter 100 we've closed <2 audit gaps OR are at <50% benchmark, surface the slowdown to Cole." Apply this conservatively.

---

*Update this doc with baseline numbers + revised ranking once `python tools/audit/check_debugger_godmode_benchmark.py --baseline` is committed and runnable.*
