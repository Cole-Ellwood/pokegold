# Debugger Godmode Spec — Omniscient Repo Q&A Oracle

> **Historical spec (archived 2026-05-29).** This documents the bar the godmode
> Q&A oracle was built to — and met (`audit ready=True`,
> `check_debugger_godmode_benchmark.py` 29/29). The two-LLM pairing protocol
> below is **retired**: this is single-owner (Claude) work now, so the
> handoff-log / no-solo-commit / mutual-approval scaffolding no longer applies.
> The live forward-looking doc is
> [`docs/debugger_unification_plan.md`](debugger_unification_plan.md). The body
> is preserved as the record of what the capability bar was and why.

**Status:** spec met; capability bar documented for the record.
**Project roadmap anchor:** [`docs/project_roadmap.md`](project_roadmap.md) row `DEBUGGER-001`.

## Goal

Cole's exact ask (2026-05-24 via `/codex-pgoal`):

> *"i want you two to make the romhack debugger into having godlike power. theres essentially nothing it cannot do. it 95% automates yalls jobs when it comes to debugging."*

Cole's operational definition (clarified in the same session):

> *"it can help yall with literally any request i have in the repo. add a feature, ask why something does something, explain something weird happening. the debugger is omniscient. no more yall digging through code, just ask the debugger where it is."*

**Bounded interpretation: the debugger becomes a WHERE/WHY/WHAT repo Q&A oracle.** Given any natural-language Cole question or symptom about the repo, `python -m tools.debugger investigate --symptom "<question>"` (or a direct subcommand) must independently return:

- (a) cited source files / lines / symbols anchoring the answer (no hallucinated paths — `check_debugger_next_coverage.py` rejects stale anchors),
- (b) a reproducible or disprovable proof command on the current ROM / repo state,
- (c) the regression gate that catches breakage, and
- (d) the evidence-strong-enough and disproof-strong-enough conditions for the answer.

When the pair (Claude + Codex) can confidently *not* dig through the code anymore — the debugger's answer is good enough to act on — the bar is hit.

## North Star constraint (load-bearing — non-negotiable)

From [CLAUDE.md](../CLAUDE.md): the debugger lives in `tools/`, it does NOT edit the targets it investigates. ROM behavior, balance, AI, save-format, hardware idioms are read-only from the debugger's perspective. The debugger gets smarter; the ROM doesn't change because of debugger work.

From this hack's First-Playthrough Promise: a smarter debugger MUST NOT change gameplay feel by accident. Any debugger change that produces a different `pokegold.gbc` byte (e.g. trace ROM bytes were impacted) requires `make compare` review.

From [`docs/asm_authoring_guide.md`](asm_authoring_guide.md): if any debugger work induces asm edits (typically through audit additions), the full ASM verification floor (clobber_smoke, farcall audits, save_format_version) applies.

## Locked decisions (from `/codex-pgoal` Step 0)

| Question | Answer | Implication |
|---|---|---|
| Acceptance bar | "omniscient repo Q&A — debugger answers WHERE / WHY / WHAT questions on the repo, no more digging" | Benchmark harness + audit ready=True gate combined; pair-defined operational test of "good enough" per held-out question. |
| Edit scope | All of `tools/*` | `tools/debugger/*`, `tools/boss_ai_debugger/*`, `tools/damage_debugger/*`, `tools/audit/*`, `tools/boss_ai_preference/*`, `tools/pokemon_mastery/*`, `tools/trace/*`, `scripts/*`, `tools/scratch_*` all editable. `engine/*`, `data/*`, `ram/*`, `constants/*`, `home/*`, `maps/*`, `gfx/*` remain READ-ONLY targets. |
| Branch | New off current | `claude/debugger-godmode` off `claude/boss-ai-rom-expansion`. PR back when phase 2 ships. |
| Codex chat | Continue "Advance omni-debugger" | Preserves the ~145k tokens of debugger context Codex already has loaded. |
| Pacing | Single big pgoal | One armed goal with aggressive budget: 1800 wall-clock minutes (30 hours), 300 iterations, 3000 tool calls, max-no-progress 5, max-compactions 5. |

## Per-slice north-star check (Codex amendment 2026-05-24)

For every slice, the implementer must be able to answer YES to this gate before declaring slice-complete:

> *A user asks a repo question in ordinary language; the debugger returns source/data locations, causal explanation, first proof command, disproof standard, and regression gate without Codex/Claude manually spelunking first.*

If the slice doesn't move at least one benchmark question closer to YES, it's the wrong slice. Slices that only restructure debugger internals without making any benchmark question more answerable don't count toward the goal.

## Decomposition into measurable sub-capabilities (Codex amendment 2026-05-24)

"Godlike" is the ambition; the measurable slices are these six sub-capabilities that together compose a Q&A oracle. They map roughly onto the six audit `capability_partial` gaps but with explicit user-facing language:

| Sub-capability | What the user sees | Closes which audit gap (roughly) |
|---|---|---|
| Source locator | "Where do I add X / where is Y handled?" → list of source paths + line ranges + symbol names | `whole_rom_replay_localization` (the localization half) |
| Behavior explainer | "Why does X happen in-game?" → causal chain (input → function → data → ROM state → visible behavior) | `causal_provenance` |
| Repro planner | "Reproduce this for me" → a save-state setup + key-press script or scenario JSONL the LLM can run cold | `generation_fuzzing_counterexamples` |
| Proof runner | "Did my fix actually fix it?" → executable proof gate (e.g. `rom-switch-materialize --fail-on-mismatch`) | `differential_mirrors` + replay half of `whole_rom_replay_localization` |
| Regression suggester | "What test should I add so this never regresses?" → concrete `tools/audit/check_*.py` skeleton + invariant statement | `impact_ranking_workflow` |
| Report renderer | "Show me what you found" → rendered markdown / JSON with all five above stitched together | `visualization_reports` |

Each benchmark question's `expected_answer` schema names which sub-capabilities are required to score it PASS. A slice that improves one sub-capability without changing the score on any question fails the per-slice north-star gate.

## Separation: Q&A oracle vs live runtime proof (Codex amendment 2026-05-24)

Two distinct proof modes; the roadmap distinguishes them so we don't over-promise:

- **Source-provable answers** (locator, regression suggester, partial behavior explainer): can be answered from static source + grep + symbol table + git history. Cheap, deterministic, no ROM execution.
- **Runtime-provable answers** (repro planner, proof runner, full behavior explainer): require save-state synthesis + ROM execution. Slower, sometimes flaky, must be marked as such in the answer.

Every benchmark question record carries a `proof_mode: source|runtime|hybrid` field. The scoring rubric expects the answer to declare which mode it used and whether the proof actually ran.

## Phase structure (internal to the single pgoal)

### Phase 0 — Foundation (target: Iter 1-6)

**Goal**: lock the bar and build the benchmark harness so Phase 1 has a numeric target.

- **Iter 1 (already-agreed sub-slice)**: land `audit/omni_debugger_first_gap_action_proof_2026-05-24.md` documenting the proven `boss_wrong_switch_replay_materialization` route end-to-end (the slice Codex agreed on as (a) before scope expansion). Append to handoff log. Small DEBUGGER-001 proof-status note in `docs/project_roadmap.md`. **Do NOT touch `tools/debugger/*` in this iter** (Codex's collision rule from the prior audit-action slice); **do NOT mark the audit blocker closed in code** — the audit doesn't re-read proof artifacts; the honest state is "route proven, blocker still present, disputed scenario available for separate investigation."
- **Iter 2-4**: curate the **historical-question benchmark** — `audit/debugger_godmode_benchmark/questions.jsonl` (the "held-out" test set; pair-curated from past Cole asks pulled from `git log --grep`, the boss_ai_rom_expansion 2026-05-23 handoff log, memory references, and bug-fix commit subjects). Aim for ~20-30 questions split roughly: 10 WHERE, 10 WHY, 5-10 WHAT. Each question is a record: `{id, archetype: WHERE|WHY|WHAT, symptom, expected_answer: {source_anchors[], proof_command, evidence_standard, disproof_standard}, severity: low|medium|high, notes}`. Both LLMs author + cross-review; commit per row.
- **Iter 5-6**: build `tools/audit/check_debugger_godmode_benchmark.py` — runs each benchmark question through `python -m tools.debugger investigate --symptom "<question>"` and `next --symptom`, scores the answer against the expected source_anchors / proof_command / evidence_standard fields, emits per-question pass/fail + aggregate. Initial baseline expected ~20-40% (lots of failures; that's the starting target).

**Phase 0 exit criterion**: harness runs, baseline recorded in `audit/debugger_godmode_benchmark/baseline_<date>.md`. Both LLMs `slice_review` the benchmark and harness shape.

### Phase 1 — Capability buildout (target: Iter 7-50, biggest phase)

**Goal**: close the 6 `capability_partial` gaps from `python -m tools.debugger audit` + raise benchmark score each iteration.

The 6 audit-reported partial capabilities (as of 2026-05-24, `python -m tools.debugger audit`):

| ID | Subject | Top gap |
|---|---|---|
| 1 | `whole_rom_replay_localization` | Semantic replay/watch reducers need automatic reruns after each candidate state removal. Exact dynamic replay is still deepest for damage and Boss AI only. |
| 2 | `causal_provenance` | Arbitrary-output taint needs automatic save-state synthesis across every ROM surface. Boss AI provenance is branch/probe-based; damage is trace/taint-based — they don't share a unified causal substrate yet. |
| 3 | `generation_fuzzing_counterexamples` | Graphics/audio/UI semantic playback, banking, full script VM behavior under arbitrary event-engine context, and arbitrary event-engine states still need dedicated dynamic ROM generators. |
| 4 | `differential_mirrors` | Full script VM behavior under arbitrary surrounding event-engine state, graphics/UI behavior, full audio playback, and arbitrary map interactions still need dedicated emulator-backed behavioral ROM mirrors. |
| 5 | `impact_ranking_workflow` | Per-subsystem semantic severity models need deeper ROM behavior calibration outside damage and Boss AI. Learned semantic impact needs expansion. |
| 6 | `visualization_reports` | Emulator-coupled TUI/canvas inspectors remain subsystem-specific. |

Each iteration in Phase 1:
1. Pick the lowest-scoring benchmark question OR the gap that most blocks an unanswered question.
2. Implement the smallest capability change that lifts at least one benchmark question from FAIL to PASS.
3. Re-run the benchmark + audit; verify no regressions; commit.
4. Pair `slice_review` before commit (per defense #2).

**No solo implementation commits.** Verified by `tools/audit/check_no_solo_commits_omni_debugger.py` (to be written in Phase 0 if not already extant from boss-ai-rom-expansion's audit lineage — `check_no_solo_commits_boss_ai_rom_expansion.py` is the template).

### Phase 2 — Verifier gate + ship (target: Iter 51+ until all green)

**Goal**: all acceptance criteria pass via `pgoal verify --run --record`.

- All 6 audit `capability_partial` gaps closed → `python -m tools.debugger audit` reports `ready=True` with `gap_actions=0`.
- `python tools/audit/check_debugger_godmode_benchmark.py` exits 0 with ≥85% pass across the curated benchmark (acceptance threshold; pair may revise this number up or down with mutual approval and a commit to this file before the final verifier run).
- All other acceptance criteria green (release-smoke, debugger-next-coverage, two-llm-handoff-log, no-solo-commits).
- Final write-up: `audit/debugger_godmode_completion_<date>.md` documenting the journey + the final benchmark score + the questions that still fail.

## In scope (v1)

1. All of `tools/*` (any Python or helper script).
2. `docs/debugger_godmode_codex_task.md` (this file; update when scope changes).
3. `docs/project_roadmap.md` DEBUGGER-001 row (status notes only; no other row).
4. `audit/omni_debugger_2026-05-24_handoff_log.jsonl` (full slice history).
5. `audit/debugger_godmode_benchmark/` (the curated question set + baselines + per-iter scores).
6. New audits under `tools/audit/check_*.py` covering benchmark + gap-closing invariants.
7. Build remains green (`make pokegold.gbc` exits 0); release-smoke green throughout.

## Out of scope (edit-forbidden, read-required)

**Important distinction (Codex amendment 2026-05-24):** the directories below are EDIT-forbidden but READ-required. The debugger must read, index, parse, and trace provenance through them to do its job. Out-of-scope means the LLM pair MUST NOT modify these files; it does NOT mean the debugger can't inspect them.

- `engine/*`, `data/*`, `ram/*`, `constants/*`, `home/*`, `maps/*`, `gfx/*`, `audio/*`, `*.asm` — investigation targets. Read freely; never write. If a benchmark question genuinely needs an ROM-side change (e.g. a new symbol export), surface that as a separate workstream; don't sneak it in.
- Save-format changes — explicit Cole-escalation per CLAUDE.md.
- Trainer roster / Pokemon stat / moveset edits — separate workstreams (`docs/balance_intent.md`, `docs/buff_backlog.md`).
- Modernization features that change gameplay feel — First-Playthrough Promise.
- Anything in `engine/battle/ai/` (boss AI is a debugger TARGET in this work, not a debugger surface).

## Acceptance criteria

Mirrored into `pgoal acceptance init` JSON. All must pass for `pgoal verify --run --record`:

1. **`roadmap_committed`** — `git log --oneline -- docs/debugger_godmode_codex_task.md` returns ≥1 commit on this branch.
2. **`audit_ready_true`** — `python -m tools.debugger audit` exits 0 AND its JSON output shows `ready: true` AND `gap_actions: 0` (no actionable gaps remain).
3. **`benchmark_threshold`** — `python tools/audit/check_debugger_godmode_benchmark.py` exits 0; the audit emits `pass_rate >= 0.85` across the curated benchmark questions; baseline + final scores committed under `audit/debugger_godmode_benchmark/`.
4. **`debugger_next_coverage`** — `python tools/audit/check_debugger_next_coverage.py` exits 0 (route/source-anchor staleness gate stays green).
5. **`release_smoke`** — `python tools/audit/check_release_smoke.py` exits 0.
6. **`two_llm_handoff_log`** — `python tools/audit/check_two_llm_handoff_log.py --strict --store audit/omni_debugger_2026-05-24_handoff_log.jsonl` exits 0.
7. **`no_solo_commits`** — `python tools/audit/check_no_solo_commits_omni_debugger.py` exits 0 (every commit on `claude/debugger-godmode` after this roadmap commit has a paired `slice_review` row from the *other* LLM in the handoff log).
8. **`navigation_floor`** — `python tools/audit/check_navigation_floor.py` exits 0 (docs/dev_index integrity).

## Structural defenses (acceptance, not advisory)

Per `feedback_codex_pgoal_structural_defenses.md` (Cole's 2026-05-23 directive). These are PROMOTED INTO ACCEPTANCE (#6, #7), not just behavioral hints:

1. **v7 strict in acceptance** — handoff log timestamp-order drift is an error; any phase without mutual sign-off fails.
2. **No solo implementation commits** — verified by audit #7.
3. **Screenshot Codex first on every pgoal continuation** — Idle-waiting-on-me → review/send work; observably-coding → poll/note only.
4. **Brainstorm split up front** — Phase 0 benchmark curation: both LLMs propose questions independently, cross-review for taxonomy + coverage gaps.
5. **Co-authored roadmap** — this file is updated by both LLMs as scope refines (e.g. the 85% threshold may shift up or down by mutual approval committed here).

## Approach preference

Per `docs/llm_pairing_rules.md`:

- **Files-first split.** Declare write-set, safe-set, collision-risk in every `ack_start`. Most slices touch 1-3 Python files; cross-LLM collision happens when both touch `tools/debugger/*` simultaneously.
- **Confidence labels.** `repo-proven` (≥1 `path:line` citation), `memory-derived`, or `judgment`. Stated on every load-bearing claim.
- **Adversarial review.** Default review stance: assume the slice has a bug or a regression. Run the relevant audit before signing off.
- **2-commits-or-1-hour cadence.** Surface direction at that cadence regardless of momentum.
- **Mutual approval before mutual_done.** Both LLMs must sign off.
- **Talk like a human in chat, JSON in the handoff log.** Cole reads conversational English; the protocol details live in the audit log.

## Edge cases

- **Benchmark question covers an ROM-side bug, not a tooling gap.** Mark the question with `severity: low` and `expected_status: documented_as_open_bug` instead of demanding the debugger fix the ROM. Keep the question; it's still a valid "the debugger can EXPLAIN this" test even if it can't fix it.
- **Benchmark question is unanswerable in principle (e.g. requires hidden info).** Drop it from the benchmark with a `dropped_reason` note in the questions.jsonl. Don't bend the debugger to leak hidden info.
- **Closing one audit gap regresses another.** Stop, run the full benchmark, identify the trade. If genuine trade-off: surface to Cole. If accidental: fix.
- **`make pokegold.gbc` breaks because a tooling change emits different ROM bytes.** Trace ROM (`pokegold_trace.gbc`) is allowed to change; release ROM is not without explicit approval.
- **Codex grinds past 50 iters without 85%.** If at Iter 50 we're at <70%, surface; the bar or the benchmark may need recalibration. Don't burn the rest of the budget on a wrong target.
- **Audit tool itself becomes the bottleneck** (e.g. `python -m tools.debugger audit` takes >5 minutes per run). Cache or stage the audit; don't gut its rigor.

## Verification floor (per slice + per phase)

Before declaring any slice done:

1. The narrow per-slice verifier (pytest target / focused audit) passes.
2. Both LLMs `slice_review`.
3. Commit only after paired sign-off (defense #2).

Before declaring any phase done:

1. `python -m tools.debugger audit --json-out .local/tmp/debugger_audit_<phase>.json` — record the gap_actions count.
2. `python tools/audit/check_debugger_godmode_benchmark.py` — record per-archetype pass rate.
3. `python tools/audit/check_release_smoke.py` and `check_debugger_next_coverage.py` and `check_navigation_floor.py` all PASS.
4. If anything in `tools/audit/` changed: re-run the touched audit + at least one neighbor to verify the harness still runs.

Before declaring the **whole pgoal** done:

1. All 8 acceptance criteria pass via `pgoal verify --run --record`.
2. `audit/debugger_godmode_completion_<date>.md` committed with final benchmark scores + journey notes + remaining-open questions.
3. The pair (both LLMs) agree the debugger is good enough that they would NOT dig through code first on a typical Cole question — Cole's operational bar from his clarification.

## Branching / commits

- Work on `claude/debugger-godmode` (off `claude/boss-ai-rom-expansion`).
- **No commit without a paired slice_review row** — defense #2.
- Push to `claude/debugger-godmode` allowed. Push to `claude/boss-ai-rom-expansion` (parent) only on Cole's ask. Push to `codex/cleanup-gsc-rebalance-split` (main) **forbidden** without Cole-escalation.
- No PR creation without Cole's explicit ask. Merging to master is a release event (CLAUDE.md escalation).
- Per-iter commit message: `debugger-godmode: iter N <slice_subject>` (greppable for the loop's history).

## Stop conditions

Pause and surface (or escalate to Cole), do not push through, if:

- `pgoal verify --run` fails 3 times in a row with the same root cause.
- Two consecutive Claude-authored commits land with no Codex `slice_review` row.
- The spec needs a load-bearing change Cole hasn't approved (especially the 85% threshold, scope expansion to ROM-side, or save-format change).
- The benchmark questions need to be REGENERATED (not refined) — that's a Phase-0 redo signal.
- Build red on `make pokegold.gbc` and the fix isn't obvious within one slice.
- `clobber_smoke` regression: any damage debugger FAIL while iterating on `tools/damage_debugger/*`.
- Audit gap_actions count INCREASES (regression).
- Any benchmark question that previously passed now fails (no-regression rule on the bar).

## Disagreement resolution

**Primary rule (Cole 2026-05-23):** Claude + Codex agreement IS Cole's decision. Do not pause for his feedback when the pair can decide. See `feedback_claude_codex_agreement_is_cole_decision.md`.

- **Tiebreak**: Claude + Codex deliberate. Settle with adversarial-review passes (default: 2 passes minimum before declaring deadlock).
- **Codex-defaults-win**: code style inside Codex's write set, idiomatic Python patterns inside debugger surfaces.
- **Claude-defaults-win**: roadmap interpretation, benchmark question wording, structural-defense enforcement, when to surface to Cole.

**Escalate to Cole** only on:
1. Mutual deadlock after ≥2 adversarial-review passes.
2. CLAUDE.md escalation-list items (gameplay taste, playtest, save-format, master merge, destructive).
3. Directive conflicts (two Cole-stated directives in opposition).

**Escalation channel:**
- Chat default. Async via ntfy topic `The-CCC-Boys` matching the same bar.

## Time / scope budget

- Standard pgoal duration: 1800 wall-clock minutes (30 hours), 300 iterations, 3000 tool calls.
- Phase 0 budget cap: ~6 iters. If Phase 0 is still open at iter 10, surface to Cole.
- Phase 1 per-slice: aim for ≤3 iters per gap closure.
- Phase 2: ~5-10 iters of cleanup + final write-up.
- If at iter 100 we've closed <2 audit gaps OR are at <50% benchmark, surface to Cole rather than burn the rest of the budget.

## Async channel

- Cole reachable via chat (he's at work but the chat does survive). Interrupt only on the 3 escalate-to-Cole conditions above.
- Cole reachable via ntfy (`The-CCC-Boys`): yes — same bar.

## Pgoal arming plan

```bash
python "$HOME/.claude/skills/pgoal/scripts/pgoal.py" set \
  --objective "Make the omni-debugger (tools/debugger/*, tools/boss_ai_debugger/*, tools/damage_debugger/*, tools/audit/*) into an omniscient repo Q&A oracle: given any Cole question about the repo (WHERE/WHY/WHAT archetype), python -m tools.debugger investigate --symptom returns cited source anchors + reproducible/disprovable proof command + regression gate without the LLM pair needing to dig through code." \
  --phase implementation \
  --criteria "<see Acceptance criteria above>" \
  --constraints "<see Structural defenses + Stop conditions above>" \
  --verify "<see Verification floor above>" \
  --max-iterations 300 \
  --max-wall-minutes 1800 \
  --max-tool-calls 3000 \
  --max-no-progress 5 \
  --max-compactions 5 \
  --no-auto-discover --assume-defaults --replace --clarified
```

## Provenance policy

- `docs/debugger_godmode_codex_task.md` (this file): **committed**.
- `audit/omni_debugger_2026-05-24_handoff_log.jsonl`: **committed** (already seeded; appended in every turn).
- `audit/debugger_godmode_benchmark/questions.jsonl` + baselines + per-iter scores: **committed**.
- `audit/debugger_godmode_completion_<date>.md`: **committed** at the final iter.
- `tools/audit/check_debugger_godmode_benchmark.py`, `tools/audit/check_no_solo_commits_omni_debugger.py`: **committed**.
- Implementation deliverables (Python under `tools/*`): **committed** under the paired slice rule.
- `.local/` and `.local/tmp/` artifacts: NOT committed (the benchmark harness writes its detailed traces here; only the summary JSON is committed).

## Background memory to read before pairing

Both LLMs read before the first slice (Codex: `git pull` + read directly):

- [docs/llm_pairing_rules.md](llm_pairing_rules.md) — committed pairing rules.
- [CLAUDE.md](../CLAUDE.md) — project config, North Star, no-hidden-info rule, ASM gotchas.
- [docs/asm_authoring_guide.md](asm_authoring_guide.md) §0 + §6 — load-bearing rules + verification floor (only if asm work is induced).
- [docs/project_roadmap.md](project_roadmap.md) — DEBUGGER-001 row + its historical lineage.
- `docs/boss_ai_debugger_*.md` (14 docs) — subsystem-specific context for the boss_ai_debugger surface.
- Memory: `reference_damage_debugger.md`, `feedback_codex_pgoal_structural_defenses.md`, `feedback_claude_codex_agreement_is_cole_decision.md`, `reference_omni_debugger_v2_surface.md`, `project_debugger_roadmap.md`.

## Codex task block

```
---CODEX-TASK---
**Goal:** Make the omni-debugger (`tools/debugger/*`, `tools/boss_ai_debugger/*`, `tools/damage_debugger/*`, `tools/audit/*`, all of `tools/*`) into an omniscient repo Q&A oracle: given any Cole question about the repo, `python -m tools.debugger investigate --symptom "<question>"` returns cited source anchors + reproducible/disprovable proof command + regression gate without the LLM pair needing to dig through code.

**Roadmap (canonical contract — read first, work from it):**
`@docs/debugger_godmode_codex_task.md`

The roadmap covers Phase 0 (foundation: land the (a) writeup + curate the historical-question benchmark + build the scoring harness), Phase 1 (capability buildout: close the 6 audit capability_partial gaps + raise benchmark score), Phase 2 (verifier gate + ship), scope, 8 acceptance criteria, structural defenses (5 promoted to acceptance), edge cases, verification floor, branch/commit policy, stop conditions, disagreement resolution, and the pgoal arming plan.

**Branch:** `claude/debugger-godmode` (off `claude/boss-ai-rom-expansion`). Already created.
**Handoff log:** `audit/omni_debugger_2026-05-24_handoff_log.jsonl` (seeded; ready for your `ack_start`).

**Pairing protocol:** today's debrief rules verbatim. Files-first split. Confidence labels (`repo-proven` with path:line / `memory-derived` / `judgment`). Mutual approval before any commit. Silence=unknown not approval. Hard-stop reflex on collision risk. 2-commits-or-1-hour cadence. **No solo implementation commits** — defense #2 is acceptance criterion #7.

**Phase 0 Iter 1 (immediate next slice, already agreed pre-scope-expansion):** land `audit/omni_debugger_first_gap_action_proof_2026-05-24.md` documenting the proven `boss_wrong_switch_replay_materialization` route end-to-end. Append handoff log. Small DEBUGGER-001 proof-status note in `docs/project_roadmap.md`. **Do NOT touch `tools/debugger/*` in this iter** (collision rule from your prior audit-action slice); **do NOT mark the audit blocker closed in code** — the audit doesn't re-read proof artifacts; the honest state is "route proven, blocker still present, disputed scenario available for separate investigation." Author: Claude (the slice I already agreed to take). You: slice_review after my commit. Acceptable to commit-then-rereview per your own rule since this is a small documented slice.

**Phase 0 Iter 2-4 (after Iter 1):** historical-question benchmark curation. Both LLMs propose 10-15 questions each (WHERE/WHY/WHAT mix) drawn from real Cole asks (git log `--grep`, boss_ai_rom_expansion handoff log, memory, bug-fix commit subjects). Cross-review; converge on ~20-30 question final set; commit `audit/debugger_godmode_benchmark/questions.jsonl`.

**Phase 0 Iter 5-6:** scoring harness `tools/audit/check_debugger_godmode_benchmark.py`. Codex primary on harness; Claude primary on question taxonomy / scoring rubric.

**Phase 1+ slices:** pick the lowest-scoring benchmark question OR the audit gap most blocking unanswered questions; close it; raise benchmark; commit; paired slice_review.

**Expected first move:** read the roadmap, check repo status, declare write set / collision-risk files / tests running / files to read / intended commit message, then append your `ack_start` handoff row. We agreed I take Iter 1 (the (a) writeup); your first ack_start should be for Iter 2 brainstorming (benchmark questions) OR for slice_review of my Iter 1 commit — your call which order.
---END-TASK---
```

---

**End of roadmap.** Both Claude and Codex work from this file. If something changes during the build, update this file first, then act.
