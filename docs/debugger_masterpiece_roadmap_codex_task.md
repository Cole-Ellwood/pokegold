# Debugger Masterpiece Roadmap — Codex Task

Status: drafted by Claude (Opus 4.7, 1M context) on 2026-05-21 in response to Cole's
ask "make a full roadmap to turn the debugger in its current state into the most
fleshed out masterpiece of all time. it should not leave you or codex lacking for any
features. if you need to change anything in the romhack, the debugger makes it
seamless. nothing is off limits."

**Read order**:

1. §0 PRD — what we are building and why.
2. §1 Current state — frozen baseline (where v1 + v2 land today).
3. §2 Acceptance contract — the gates the masterpiece must hit.
4. §3 Phase plan — P0 through P18, in dependency order.
5. §4 Cross-cutting design principles — proof-vector architecture, evidence atoms,
   failure-class-first.
6. §5 Partnership protocol — how Claude + Codex actually work this together.
7. §6 Verification floor — what runs at every phase boundary.
8. §7 Open taste calls — items where Cole's gameplay-design call matters.
9. §8 References.

**Consumer note**: this doc is the source of truth. The `/pgoal` arming below
references "fully implement docs/debugger_masterpiece_roadmap_codex_task.md". The PRD
in §0 is what gets saved via `pgoal prd save`. The acceptance contract in §2 is what
gets piped to `pgoal acceptance init --stdin`. The phase plan in §3 is what gets piped
to `pgoal phase-plan --stdin`. Keep this doc and the three pgoal artifacts in sync; if
they drift, this doc wins, regenerate the artifacts.

**Co-authors of the spec**: Claude (Opus 4.7) drafted; Codex (5.5 Extra High) reviews
on receipt. Per `docs/llm_pairing_rules.md` rule #6 (mutual-done), neither LLM declares
this roadmap "approved" unilaterally. Cole's standing operating rule
(`feedback_debugger_for_llm_use_full_autonomy.md`): "you both need to agree, not me."

---

## §0 PRD — Product Requirements Doc

### Objective

Turn the current unified omni-debugger into a *masterpiece-class* substrate for two
cooperating LLMs (Claude + Codex) to investigate, modify, and verify ANY bug or
behavior in a Game Boy / Pokémon Gold ROM hack — proof-honestly, omnisciently over
recorded execution, and with seamless edit-rebuild-retest cycles. The deliverable is a
multi-phase build that:

- closes the remaining GPT-5.5 proof-boundary loose ends so reverse-query / dynamic
  taint / causal graph / mirror evidence can never silently overpromise;
- adds the omniscient queries an LLM agent reaches for first (`when-wrote`, trace
  query language `tdb`, `value-came-from`) so the debugger answers what *actually*
  happened instead of forcing the LLM to re-derive from raw traces;
- gives the agents seamless ROM-edit workflow (`debugger rom-edit`) so changing a
  function and re-running the audit floor is one command, not five;
- exposes a normalized interface (DAP minimal subset + `tdb` query syntax) that both
  LLMs can drive without re-inventing per-session glue;
- structurally enforces the Claude+Codex mutual-agreement gate via an audited
  handoff log so neither LLM can ship a one-sided "done" claim;
- provides golden lived-bug smokes for every new affordance (rule #11) — synthetic
  tests are necessary, not sufficient.

### Personas

- **Claude (Opus 4.7, 1M context)** — Anthropic CLI; can use computer-use, web search,
  and richer tool surface; better at long-form synthesis and design.
- **Codex (5.5 Extra High)** — separate CLI in a separate terminal; strong at code,
  short cycle times, telegraphed commit cadence. Pairs with Claude via files-first
  split (rule #3) and "I'm taking X" declarations (rule #2 codex stanza).
- **Cole (gameplay-design lead)** — does not code. Plays in VBA-M. Owns gameplay
  taste calls and merging to master. Standing rule: full autonomy granted to the LLM
  pair; mutual-Codex+Claude agreement is the only gate.

### North-star scenarios

Each scenario is a concrete LLM-agent workflow the masterpiece debugger must
collapse into one or two commands. These drive the acceptance contract in §2.

1. **AG-NN transitive register-clobber (the recurring damage failure class)** — agent
   sees "physical damage 5× too high in wild encounters" and runs
   `debugger when-wrote $D141 --since wild_floor_entry` to identify the offending
   write, `debugger tdb 'caller=BattleCommand_DamageCalc and writes(addr=$D141)'` to
   bound the chain, and `debugger probe stats damage_calc_entry` to see whether the
   function was even reached. Today: this takes 4+ iterations of hand-rolled watch +
   re-run + trace + grep.

2. **VBA-vs-PyBoy graphics divergence (May 2026 tile jumble class)** — agent has Cole's
   VBA-M video of the bug and a save state. They run
   `debugger vram-snapshot --decode --save-state bug.state` and
   `debugger vram-diff bug.state good.state` to see a structured tile/OAM/palette
   delta, not a pixel diff. They cross-check by exporting a BGB-compatible `.sym`
   companion that lets a human (or a second emulator) load the same investigation.

3. **Boss AI picked a stupid move** — agent runs
   `debugger ai-trace --boss-route morty --turn 3 --decode-rules`, sees the rule
   waterfall in plain English, and follows up with
   `debugger tdb 'between(BossAI_Choose, BossAI_Score) and writes(wEnemyAIMoveScores)'`
   to bound the score-write chain. The mutual-agreement gate then forces both LLMs to
   sign off the fix before the audit floor accepts it.

4. **"Did this commit break X?"** — agent runs
   `debugger bisect --good <c> --bad HEAD -- python tools/audit/check_release_smoke.py`
   *with chaos mode on* — interrupt-timing fuzzing inside hardware-legal envelopes —
   so flaky regressions don't survive the bisect. Output identifies the first bad
   commit *and* the minimal input log that triggers the symptom.

5. **Seamless ROM change** — agent wants to verify a hypothesized fix. They run
   `debugger rom-edit propose --file engine/battle/late_gen_held_items.asm
   --change "..."`, the debugger applies the diff in a worktree, rebuilds, runs the
   release-smoke audit floor + the affected debugger tests, and reports pass/fail
   with the proof-vector. No manual `cd wsl && make && python tools/audit/...`.

6. **Save-state forensics** — Cole reports "save loaded with wrong party after I
   touched ram/wram.asm." Agent runs `debugger save-state-lab inspect bug.state`,
   `debugger save-state-lab diff bug.state baseline.state --decode-symbols`, sees the
   shifted offset, and `debugger rom-edit propose-revert --file ram/wram.asm
   --restore-offsets` reverts cleanly. The lab fails closed on `.sgm` format until
   a trusted offset decoder lands.

7. **Pokemon Mastery loop integration** — the running compounding loop wants the
   debugger to ground its claim "this move would have been the best play." The
   debugger exposes `debugger ai-counterfactual --replay <id> --turn N --candidates
   <moves>` that re-scores each candidate against the ROM AI and the local Python
   oracle, returning the proof-vector for each.

8. **Hardware-event-honest evidence** — agent claims "the script VM ran" in a
   playtest packet. The debugger refuses to mark the claim `runtime_observed` unless
   `hardware_event_stream` recorded the script-VM helper symbol firing AND a
   hook-order probe validated the pre-state byte at the moment of the write. The
   masterpiece debugger has zero silent promotions from "bounded effect window" to
   "exact banked causal writer."

### Out-of-scope

- **Full whole-ROM symbolic execution.** Too expensive for the bug class; symbolic
  exec stays scoped to single-function ASM windows (P15).
- **Replacing PyBoy with a custom emulator.** PyBoy stays as the agent backend; the
  cross-emulator differential (P13) is a *check*, not a replacement.
- **A general-purpose web UI for human review.** Deferred to P18 because two LLMs +
  CLI + structured JSON beats an HTML UI for their workflow
  (`feedback_debugger_for_llm_use_full_autonomy.md`).
- **Auto-merging fixes to master.** The masterpiece debugger SHIPS DRAFT COMMITS on
  a `claude/` or `codex/` branch — never auto-pushes to `master` or to the dev tip
  branch (`codex/cleanup-gsc-rebalance-split`). User merge approval stays a manual
  gate per CLAUDE.md escalation rule.
- **Anything that downgrades existing v1 readiness or v2 surface gates.** `audit
  ready=True` and `selftest PASS` stay green throughout the roadmap; any phase that
  breaks them must repair before claiming done.

### Definition of "masterpiece"

The roadmap is *not* done when the audit reports green. The roadmap is done when:

1. All §2 acceptance gates pass under fresh, deterministic replays.
2. Each S-tier feature has at least one golden lived-bug smoke from a real or
   recreated scenario (rule #11), not just synthetic unit tests.
3. The `audit/masterpiece_handoff_log.jsonl` carries an explicit mutual-agreement row
   (Claude + Codex) signing off completion (rule #6).
4. The session-start surface advertises every new module, the user guide carries a
   recipe for each new failure class, and the catalog audit lists each module with
   its evidence paths.
5. Cole, asked to demo any of the 8 north-star scenarios above, can do it in ≤2
   commands without reading the source.

Any of those failing → not done. The audit floor is necessary, not sufficient.

---

## §1 Current state — frozen baseline (2026-05-21)

### V1 capability audit: ready=True, 11/11 complete

Source: `python -m tools.debugger audit` and `tools/debugger/catalog.py:412-714`.

| Capability | Status | Source of truth |
|---|---|---|
| Unified front door | complete | `tools/debugger/__main__.py`, `catalog.py` |
| ROM runtime + symbols | complete | `tools/trace/runtime.py`, `damage_debugger/emulator.py` |
| Damage debugger | complete | `damage_debugger/clobber_smoke.py`, `fuzz.py`, `taint.py`, `replay.py` |
| Boss AI debugger | complete | `boss_ai_debugger/__main__.py`, `audit/check_boss_ai_debugger_done.py` |
| Whole-ROM ingest | complete | `debugger/ingest.py`, `playtest_packet.py` |
| Whole-ROM replay + localization | complete | `debugger/replay.py`, `localize.py`, `state_space.py`, `instruction_trace.py`, `hook_order.py`, `hardware_regression.py`, `effect_trace.py`, `reverse_query.py`, `runtime_watch.py`, `visual_snapshot.py`, `audio_snapshot.py` |
| Causal provenance | complete | `debugger/explain.py`, `trace_index.py`, `taint.py`, `dynamic_taint.py`, `causal_graph.py`, `slicing.py`, `provenance.py` |
| Generation + fuzzing + counterexamples | complete | `debugger/generate.py`, `fuzz.py`, `testgen.py`, `minimize.py` |
| Differential mirrors | complete | `debugger/mirrors.py`, `content_mirror.py`, `expect.py` |
| Impact ranking + workflow | complete | `debugger/workflow.py`, `ranking.py`, `coverage.py`, `impact.py`, `investigate.py` |
| Visualization + reports | complete | `debugger/coverage.py`, `reporting.py`, `visualization.py` |

### V2 surfaces: 5/5 complete (additive, not counted in v1 readiness)

| Surface | Status | Source of truth |
|---|---|---|
| Hypothesis tracker | complete | `tools/debugger/hypothesis_tracker.py`, `audit/hypothesis_tree.jsonl` |
| Debugger selftest | complete | `tools/debugger/selftest.py` |
| Save-state lab | complete | `tools/debugger/save_state_lab.py` (V0 — raw + WRAM diff; `.sgm` fails closed) |
| Bisect harness | complete | `tools/debugger/bisect.py` (exit-125 fail-closed, dirty-tree refusal) |
| Session orientation | complete | `tools/debugger/session_start.py` |

### Adjacent subsystems

- **`tools/damage_debugger/`** — 16 active modules + legacy. Hand-curated regression
  `clobber_smoke.py` is the damage-chain ABI floor.
- **`tools/boss_ai_debugger/`** — 25+ modules covering decision traces, contribution
  traces, generators, materialization, review queue, mastery index, route eval.
- **`tools/trace/`** — PyBoy runtime helpers, Boss AI trace capture + state factory.
- **`tools/audit/`** — 56+ static & release audits; release-smoke subset is the
  ROM-wide floor.
- **`tools/pokemon_mastery/`** — Compounding loop for ground-truth-grounded
  replay/case-library training. Shares no code with the debugger today but is a
  consumer (P4).

### Known gaps (from GPT-5.5 review + GPT-5.5 supplemental + ongoing implementation notes)

Reference: `docs/unified_debugger_gpt55_pro_review_2026-05-18.md` (430 KB, 6776 lines
of review + implementation notes). The remaining priority list from the latest
implementation note (2026-05-20):

- **Full script VM behavior** is not emulated.
- **Pixel-accurate graphics / UI behavior** is not modeled.
- **Audio playback / mixer behavior** is not modeled.
- **Arbitrary map interactions** are not modeled.
- **Non-mutating hardware event recorder** is not present (existing event stream is
  not yet a recorder-only / no-side-effect surface).
- **Whole-ROM proof-substrate goal remains incomplete** and `ready=False` per the
  GPT-5.5 deeper goal (NOT the v1 catalog gate, which is `ready=True`).

Architecture risks the GPT-5.5 supplemental review flagged that are still standing:

- **Duplicated SM83 modeling.** `dynamic_taint` and `effect_trace` model SM83 ops in
  parallel. A shared `tools/debugger/sm83_model.py` exists but is not consumed by
  both engines yet. Divergence risks remain for unsupported-op handling, flag
  semantics, register-pair side effects, RMW old-byte attribution, OAM DMA, CGB
  VRAM DMA, DIV/timer, MBC, SRAM enable/bank, WRAM/VRAM bank writes, PPU/audio IO,
  interrupt entry, HALT/STOP, EI/DI/RETI.
- **Ranking / impact proof-boundary holes.** `ranking.infer_proof_status()` and
  `impact.taint_items()` defaults can re-promote planned-only findings into
  `taint_proven` / `instruction_observed` by type alone. Patched in part; not
  exhaustively.
- **Causal graph reverse-query default.** Missing reverse-query result proof
  defaults to `instruction_observed` via dead-or-alive fallback that's risky on
  legacy data.
- **Visualization mixed-proof badging.** Shared nodes can display max-proof and hide
  mixed evidence; min/max badges and proof vector display are partial.
- **`AddressSpec` vs `ObservedAddressKey` are not yet split.** User intent and
  observed runtime evidence still mix in one type.
- **`BankState` is not a typed record yet** — runtime-observed vs inferred-from-IO
  vs default vs mapper-dependent are still inferred from context.
- **`EvidenceAtom` schema is not yet shared** across effect_trace / reverse_query /
  dynamic_taint / causal_graph / ranking / playtest packet.

These are the inputs to P0 (which closes the GPT-5.5 review backlog before the
masterpiece extensions begin).

---

## §2 Acceptance contract

This is what `pgoal acceptance init --stdin` will receive. Each test is one
behavioral gate; planned/runtime/hardware proof boundaries follow per phase.

```json
{
  "tests": [
    {
      "id": "v1_audit_stays_green",
      "kind": "command",
      "command": "python -m tools.debugger audit",
      "expected_exit_code": 0,
      "expected_output_regex": "ready=True.*complete': 11"
    },
    {
      "id": "v2_selftest_stays_green",
      "kind": "command",
      "command": "python -m tools.debugger selftest",
      "expected_exit_code": 0,
      "expected_output_regex": "Selftest PASS"
    },
    {
      "id": "debugger_unittests_stay_green",
      "kind": "command",
      "command": "python -B -m unittest discover tools\\debugger\\tests",
      "expected_exit_code": 0
    },
    {
      "id": "release_smoke_floor_stays_green",
      "kind": "command",
      "command": "python tools/audit/check_release_smoke.py",
      "expected_exit_code": 0
    },
    {
      "id": "when_wrote_answers_canonical_damage_clobber",
      "kind": "command",
      "command": "python -m tools.debugger when-wrote --address D141 --since-symbol BattleCommand_DamageCalc --trace .local/tmp/masterpiece_golden_traces/wild_floor.jsonl",
      "expected_exit_code": 0,
      "expected_output_regex": "writer_pc=.* match_precision=exact_bank_key"
    },
    {
      "id": "tdb_query_language_accepts_canonical_query",
      "kind": "command",
      "command": "python -m tools.debugger tdb 'writes(addr=$D141) and caller=BattleCommand_DamageCalc' --trace .local/tmp/masterpiece_golden_traces/wild_floor.jsonl",
      "expected_exit_code": 0,
      "expected_output_regex": "matches=[1-9]"
    },
    {
      "id": "handoff_log_audit_enforces_mutual_agreement",
      "kind": "command",
      "command": "python tools/audit/check_two_llm_handoff_log.py",
      "expected_exit_code": 0
    },
    {
      "id": "rom_edit_propose_apply_revert_roundtrip",
      "kind": "command",
      "command": "python -m tools.debugger rom-edit --self-test",
      "expected_exit_code": 0,
      "expected_output_regex": "rom-edit roundtrip PASS"
    },
    {
      "id": "vram_decode_structured_diff_works",
      "kind": "command",
      "command": "python -m tools.debugger vram-snapshot --self-test",
      "expected_exit_code": 0,
      "expected_output_regex": "vram structured-decode self-test PASS"
    },
    {
      "id": "probe_counters_self_test",
      "kind": "command",
      "command": "python -m tools.debugger probe --self-test",
      "expected_exit_code": 0,
      "expected_output_regex": "probe counter self-test PASS"
    },
    {
      "id": "session_start_advertises_every_new_module",
      "kind": "command",
      "command": "python -m tools.debugger session-start --json",
      "expected_exit_code": 0,
      "expected_output_regex": "\"masterpiece_modules\""
    },
    {
      "id": "lived_bug_smokes_pass",
      "kind": "command",
      "command": "python -B -m unittest discover tools\\debugger\\tests -p \"test_*_lived_smoke.py\"",
      "expected_exit_code": 0
    },
    {
      "id": "shared_sm83_model_consumed_by_both_engines",
      "kind": "command",
      "command": "python tools/audit/check_sm83_shared_tables_consumers.py",
      "expected_exit_code": 0
    }
  ]
}
```

**Verification floor between every acceptance run**: see §6.

---

## §3 Phase plan (P0 → P18)

Each phase below has the shape:

```
### P{N}. {Title}
**Objective**: 1 line.
**Why now**: failure class or capability gap that justifies it.
**Scope (in)**: list.
**Scope (out)**: list.
**Acceptance**: list of testable gates.
**Iteration budget**: rough hours.
**Primary**: Claude / Codex / shared.
**Shared collision-risk files**: paths.
**Dependencies**: prior phases.
```

Phases are ordered roughly by dependency. Primary owner rotates so neither LLM
becomes a bottleneck.

---

### P0. Close the GPT-5.5 review backlog

**Objective**: bring the GPT-5.5 "remaining priority" list to zero before adding new
features. The masterpiece is *honest* before it is *broad*.

**Why now**: the supplemental review enumerated specific proof-boundary holes that
are still standing. Adding new features on top of risky proof promotion is what
makes a debugger look final when it is bounded. Per the supplemental review's "hard
line" rule.

**Scope (in)**:

- `tools/debugger/ranking.py` — make `infer_proof_status()` conservative; remove
  broad type-only promotion.
- `tools/debugger/impact.py` — preserve `attribution["proof_status"]` everywhere it
  reads dynamic-taint or reverse-query input.
- `tools/debugger/causal_graph.py` — reverse-query default proof = `planned_only`
  unless validation/concrete writer proves more (already partly patched; close the
  remaining gaps).
- `tools/debugger/visualization.py` — mixed-proof badging on shared nodes; min/max
  display; never collapse mixed evidence to a single max badge.
- `tools/debugger/address.py` — split `AddressSpec` (requested/static) from
  `ObservedAddressKey` (runtime-proven); add semantic bank validity (bank prefix on
  WRAM0/HRAM/IO/OAM/IE is invalid or marked inexact).
- `tools/debugger/dynamic_taint.py` — replace the 16-bit `Sink` / `TaintState.memory`
  with bank-aware sink and state when the unified wrapper drives it.
- Introduce shared `EvidenceAtom` schema in `tools/debugger/evidence.py` and adopt
  in effect_trace, reverse_query, dynamic_taint, causal_graph, ranking, impact,
  playtest_packet.
- Introduce typed `BankState` distinguishing runtime-observed / inferred-from-IO /
  default / unknown / mapper-derived / SRAM-disabled.

**Scope (out)**: shared SM83 model (P1), new features (P2+), graphics/audio/script
mirror gaps (later phases).

**Acceptance**:

- All new tests listed in the supplemental review pass:
  `test_ranking_dynamic_write_attribution_preserves_planned_proof_status`,
  `test_impact_dynamic_write_attribution_preserves_planned_proof_status`,
  `test_causal_graph_reverse_query_missing_result_proof_defaults_planned`,
  `test_visualization_shared_node_requires_mixed_proof_badge`,
  `test_address_spec_rejects_impossible_bank_for_unbanked_space`.
- `python -m tools.debugger audit` stays `ready=True`.
- `python -m tools.debugger selftest` stays green.
- `git grep "TODO.*proof"` in `tools/debugger/` returns ≤ the count at P0 start (no
  new proof TODOs added).

**Iteration budget**: ~25 iterations (~12-16 hours).

**Primary**: Codex (per `boss_ai_debugger/state_of_art_implementation_plan_2026-05-15.md`
pattern, Codex tends to drive proof-boundary work; Claude reviews).

**Shared collision-risk files**: `tools/debugger/ranking.py`, `impact.py`,
`causal_graph.py`, `visualization.py`, `address.py`, `dynamic_taint.py`,
`evidence.py`, `effect_trace.py`, `reverse_query.py`. Heavy collision risk —
sequence patches with explicit "I'm taking X" declarations.

**Dependencies**: none.

---

### P1. Shared SM83 effect model adoption

**Objective**: both `dynamic_taint` and `effect_trace` consume a single
authoritative SM83 effect model (`tools/debugger/sm83_model.py`). Duplicated opcode
modeling is the next architecture risk after proof-consumer cleanup.

**Why now**: GPT-5.5 supplemental review flagged this as a "major architecture risk."
Today the two engines model opcode semantics in parallel. When one is patched (e.g.
`sub a` taint clearing) the other can stay broken until separately patched. Shared
model means one bug, one fix, both engines covered.

**Scope (in)**:

- Expand `tools/debugger/sm83_model.py` to a complete typed-effect emitter:
  - register reads/writes (8-bit and 16-bit pairs),
  - memory reads/writes (with bank awareness via supplied `BankState`),
  - stack reads/writes,
  - flag writes,
  - PC/SP/IME effects,
  - conditional control flow,
  - required pre-state fields (for RMW),
  - hardware trigger declarations (OAM DMA, MBC bank writes, PPU/timer/interrupt
    registers, IF/IE).
- Replace ad-hoc opcode modeling in `dynamic_taint.py` with a consumer of
  `sm83_model`.
- Replace ad-hoc opcode modeling in `effect_trace.py` with a consumer of
  `sm83_model`.
- Add `tools/audit/check_sm83_shared_tables_consumers.py`: tracks shared-table
  dispatch sites in non-`sm83_model` files with a shrinking allowlist; fails on
  regressions.
- Cover all opcodes including: HLI/HLD pair updates, 16-bit inc/dec, `add hl,rr`,
  `add sp,e8`, `ld hl,sp+e8`, `ld sp,hl`, CB register ops + flags, DAA, CPL, SCF,
  CCF, accumulator rotates, push/pop, call/ret/rst, RETI, interrupt entry, HALT,
  STOP, EI/DI.

**Scope (out)**: emulator-side hardware capture (P12 + P13).

**Acceptance**:

- `tools.debugger.dynamic_taint` and `tools.debugger.effect_trace` produce
  bit-identical evidence atoms for the canonical SM83 unit tests when given the same
  trace input.
- `test_shared_sm83_model_dynamic_taint_and_effect_trace_parity_ld_hli`,
  `..._cb_register`, `..._sp_update`, `..._daa` pass.
- `check_sm83_shared_tables_consumers.py` passes (no unallowlisted shared-table
  dispatch outside `sm83_model`; allowlisted counts do not grow).
- Full debugger unittest suite passes.
- Selftest stays green with `sm83_model_parity` as a new component.

**Iteration budget**: ~30 iterations (~15-20 hours).

**Primary**: Codex (deep ASM territory, Codex preference per pairing-rules
codex stanza).

**Shared collision-risk files**: `tools/debugger/sm83_model.py`, `dynamic_taint.py`,
`effect_trace.py`, `tests/test_dynamic_taint.py`, `tests/test_effect_trace.py`.

**Dependencies**: P0 (shared `EvidenceAtom` schema makes parity comparison
tractable).

---

### P2. `when-wrote` reverse watchpoint query

**Objective**: ship the single highest-ROI omniscient query —
`python -m tools.debugger when-wrote --address $D141 [--since-symbol X | --since-frame N] [--bank N]`
— that returns the last write before a given frame/symbol with PC, bank, register
state, and instruction. Pernosco's "value origin" query, ported to a Game Boy ROM.

**Why now**: this is THE query the AG-NN class repeatedly needs. Today an agent
hand-rolls a watch + re-run + grep loop; tomorrow they type one command.

**Scope (in)**:

- New subcommand `when-wrote`.
- Backed by the existing instruction trace / effect trace / reverse_query
  infrastructure (after P0+P1 cleanups), but exposes a *direct query primitive* with
  no setup.
- Auto-loads the most recent recorded trace if `--trace` is omitted.
- Supports `--since-symbol X` (last write before PC = X first fires),
  `--since-frame N` (last write before frame N), `--reverse` (find first write
  forward from a baseline).
- Returns: writer PC, writer symbol, bank, frame, register state at write,
  instruction bytes, `EvidenceAtom` with proof vector.
- Refuses to return a bus-address-only match for a banked target (per P0 fix).

**Scope (out)**: full omniscient time travel; only the queries below.

**Acceptance**:

- `when-wrote --address D141 --since-symbol BattleCommand_DamageCalc` against
  `.local/tmp/masterpiece_golden_traces/wild_floor.jsonl` returns the exact
  writer (verified via golden lived-bug smoke against the May 2026 5× damage class).
- `test_when_wrote_returns_concrete_observed_writer` passes.
- `test_when_wrote_refuses_bus_address_fallback_for_banked_target` passes.
- `test_when_wrote_golden_smoke_ag08_class` passes (lived smoke per rule #11).
- Help text + `debugger_user_guide.md` recipe added.
- Selftest grows by `when_wrote` component.

**Iteration budget**: ~12 iterations (~6-8 hours).

**Primary**: Claude (composition over existing primitives).

**Shared collision-risk files**: `tools/debugger/reverse_query.py`,
`tools/debugger/__main__.py`, `tools/debugger/catalog.py`,
`tools/debugger/selftest.py`, `docs/debugger_user_guide.md`.

**Dependencies**: P0 (proof-boundary), P1 (shared SM83 model for register-state at
write).

---

### P3. `tdb` trace query language

**Objective**: a small declarative query language over recorded traces.
`python -m tools.debugger tdb '<expression>'` accepts predicates like:

- `writes(addr=$D141)` — any write to the address
- `reads(reg=BC) at bank=0x0F` — any read of BC while bank 0x0F is paged in
- `caller=BattleCommand_DamageCalc and writes(wEnemyMonStatus)` — writes called
  from a function
- `between(BossAI_Choose, BossAI_Score) and writes(wEnemyAIMoveScores)` —
  bounded-span writes
- `pc==$5A00 or pc==BossAI_Choose+0x12` — PC ranges
- `frame>1200 and frame<1300` — frame ranges
- compositions with `and`, `or`, `not`, parens
- `--trace <path>` to override default

**Why now**: rr's chunk-based indexing + Pernosco's query box are the omniscient
debugger primitive. The agent today writes a Python script per investigation. `tdb`
collapses every recurring investigation into one expression.

**Scope (in)**:

- Grammar + parser (PEG or hand-rolled recursive descent in
  `tools/debugger/tdb_parser.py`).
- Evaluator backed by `effect_trace` + `instruction_trace` + `trace_index`.
- Predicates: `writes`, `reads`, `executes`, `calls`, `caller=`, `between`,
  `at bank=`, `pc==`, `frame>`/`<`/`==`, `reg=`, `addr=`, `symbol=`.
- Logical combinators: `and`, `or`, `not`.
- Output: ordered match list with `EvidenceAtom`, `match_precision`, frame, PC,
  symbol context.
- `--format text|jsonl|table` output modes.
- `--explain` prints the evaluation plan + which trace indexes were consulted.

**Scope (out)**: writes-to-`tdb` (no inserting new evidence; query-only). Time-warp
breakpoints (P10).

**Acceptance**:

- `tdb 'writes(addr=$D141) and caller=BattleCommand_DamageCalc'` returns the same
  writer `when-wrote` returns for the AG-NN golden smoke.
- `tdb 'between(BossAI_Choose, BossAI_Score) and writes(wEnemyAIMoveScores)'`
  returns the score writes from a Morty trace.
- `test_tdb_parser_accepts_canonical_queries` passes.
- `test_tdb_evaluator_matches_when_wrote_for_overlap_cases` passes.
- `test_tdb_explain_lists_consulted_indexes` passes.
- Selftest grows by `tdb` component.

**Iteration budget**: ~25 iterations (~12-15 hours).

**Primary**: Claude (DSL design + parser preference).

**Shared collision-risk files**: `tools/debugger/tdb_parser.py` (new),
`tools/debugger/__main__.py`, `tools/debugger/trace_index.py` (small
extension), `tools/debugger/selftest.py`, `docs/debugger_user_guide.md`.

**Dependencies**: P0, P2 (overlap on output shape).

---

### P4. Two-LLM handoff log + claim-provenance audit

**Objective**: every claim made in a debugger investigation by Claude or Codex is
logged with:

- which model said it
- which evidence layer supports it (per Cole's self-report discipline taxonomy
  in `~/.claude/self_report_discipline.md`: prompt-declared / tool-verified /
  transcript-visible / structural-analogue / hidden-referent)
- which confidence label (per pairing rules rule #4: `repo-proven` /
  `memory-derived` / `judgment`)
- which `EvidenceAtom`(s) ground it
- whether the *other* LLM verified it

A new audit `tools/audit/check_two_llm_handoff_log.py` enforces that any claim
upgraded to `verified` carries:

- a Claude-source row,
- a Codex-source row,
- a verifying `EvidenceAtom`,
- a `mutual_agreement_signed_at` timestamp.

A claim signed by one model only stays at `provisional` regardless of confidence.

**Why now**: structural defense against the "ornate-drift" failure mode
(`reference_llm_pairing_rules.md`). Mutual-Codex+Claude agreement is the only
completion gate; today it's vibes. Making it a logged audited handoff log
*structurally* enforces the rule.

**Scope (in)**:

- New module `tools/debugger/handoff_log.py`.
- Append-only JSONL at `audit/masterpiece_handoff_log.jsonl`.
- Schema: `{id, model, claim, evidence_layer, confidence, evidence_atoms, status,
  verified_by, signed_at}`.
- CLI:
  - `debugger handoff add --model claude --claim "..." --evidence-layer
    transcript-visible --confidence repo-proven --evidence-atom A123`
  - `debugger handoff verify <id> --model codex --evidence-atom B456`
  - `debugger handoff reject <id> --model codex --reason "..."`
  - `debugger handoff list [--status open|verified|rejected]`
- Hypothesis tracker integration: a hypothesis verified by mutual handoff
  log entry promotes to `mutual_verified` (new status), strictly stronger than the
  existing `verified` gate.

**Scope (out)**: agent identity authentication (we trust the model field; spoofing
isn't part of the threat model when both LLMs are running locally for Cole).

**Acceptance**:

- `check_two_llm_handoff_log.py` rejects a `verified` row without Claude and Codex
  signatures.
- `check_two_llm_handoff_log.py` accepts a `verified` row with both signatures + a
  cited `EvidenceAtom`.
- `test_handoff_log_append_only` passes.
- `test_handoff_log_mutual_agreement_required_for_verified` passes.
- `test_handoff_log_integrates_with_hypothesis_tracker` passes.
- Audit added to release-smoke floor (`check_release_smoke.py` extension).
- Selftest grows by `handoff_log` component.

**Iteration budget**: ~15 iterations (~8-10 hours).

**Primary**: Claude (designing the handoff schema is structural design; Claude
strength per pairing-rules claude stanza).

**Shared collision-risk files**: `tools/debugger/handoff_log.py` (new),
`tools/debugger/hypothesis_tracker.py`, `tools/audit/check_two_llm_handoff_log.py`
(new), `tools/audit/check_release_smoke.py`, `audit/masterpiece_handoff_log.jsonl`
(new).

**Dependencies**: P0 (`EvidenceAtom` schema).

---

### P5. Bug-localization context packets

**Objective**: `debugger pack --hypothesis <id> [--failure-scenario X]` emits a
single, structured, context-packet block sized to a single LLM turn. Contents:

- the failing scenario (id + reproducer)
- the hypothesis text + confidence
- 3 most-relevant source spans (chosen by taint + slicing)
- 3 most-recent effect-trace entries near the failure
- diff-vs-known-good behavior (if a baseline exists)
- list of unverified claims still needing a citation
- next-action recommendation

This is the LDB / SWE-agent "structured slice" pattern adapted for our two-LLM
pairing.

**Why now**: cross-LLM handoff (Claude ↔ Codex) is the load-bearing bottleneck. Per
LDB (Zhong, Wang, Shang, ACL 2024) the best LLM debugger pattern is a small,
structured, decision-shaped slice. We're paying the agent → agent context cost
already; structuring it is free win.

**Scope (in)**:

- `tools/debugger/context_packet.py`.
- Output format: human-readable markdown PLUS structured JSON (for the other LLM's
  parser).
- Reads from: hypothesis tracker, effect trace, taint, slicing, mirrors, handoff
  log.
- `--target codex` / `--target claude` swaps the framing to the other LLM's
  preferred form (per the per-LLM stanzas in `llm_pairing_rules.md`).
- Token budget cap (`--max-tokens N`, default 4000); falls back to a "did not fit"
  summary with pointers.

**Scope (out)**: actually sending the packet to the other LLM (P5b is the
computer-use bridge; that's P14's territory).

**Acceptance**:

- `debugger pack --hypothesis <id>` emits markdown+JSON in <2s.
- Token count within `--max-tokens` for the AG-NN golden scenario.
- `test_context_packet_includes_taint_spans` passes.
- `test_context_packet_fits_in_max_tokens` passes.
- `test_context_packet_targets_codex_uses_punchline_first_form` passes.
- `test_context_packet_golden_smoke_ag08_class` passes.
- Selftest grows by `context_packet`.

**Iteration budget**: ~12 iterations (~6-8 hours).

**Primary**: Claude (composition + framing).

**Shared collision-risk files**: `tools/debugger/context_packet.py` (new),
`tools/debugger/hypothesis_tracker.py`, `tools/debugger/__main__.py`,
`docs/debugger_user_guide.md`.

**Dependencies**: P0, P4.

---

### P6. VRAM / OAM / Tilemap structured-decode + diff

**Objective**: `debugger vram-snapshot --decode --save-state X` produces a
*structured* decode of:

- BG tilemap A + B layout (which tile index at which screen cell)
- BG/OBJ palette state
- OAM entries (sprite id, x, y, tile index, attributes, palette)
- LCDC flags + scroll/window state
- VRAM bank (CGB-only fields if applicable)

`debugger vram-diff X.state Y.state` produces a structured changeset — not a pixel
diff. Output: which tiles moved/changed, which OAM entries appeared/disappeared,
which palette indices shifted.

**Why now**: the May 2026 PyBoy-vs-VBA tile jumble class (per
`user_plays_in_vba.md`). Pixel diffs of two emulators that disagree are unhelpful;
structured tile/OAM diff is decision-useful. Also doubles as cross-emulator
differential pre-work (P13).

**Scope (in)**:

- `tools/debugger/vram_decode.py` — pure-Python decoder from VRAM + OAM + LCDC + BGP
  bytes.
- `tools/debugger/vram_snapshot.py` — extends existing `visual_snapshot.py` with
  the structured decode.
- `tools/debugger/vram_diff.py` — structured diff with tile-name resolution if the
  ROM tiles are mapped to symbol-table labels (best-effort).
- CLI: `vram-snapshot --decode`, `vram-diff <a> <b> [--symbols pokegold.sym]`.

**Scope (out)**: pixel rendering parity with VBA (out of scope; that's a separate
emulator problem).

**Acceptance**:

- `vram-snapshot --decode` against a known battle-screen save state returns the
  expected tile layout (golden capture).
- `vram-diff baseline.state jumble.state` returns the structured shift evidence for
  the May 2026 tile jumble.
- `test_vram_decode_matches_golden_battle_screen` passes.
- `test_vram_diff_finds_tile_index_shift` passes.
- `test_vram_diff_golden_smoke_may_2026_tile_jumble` passes (lived smoke).
- Selftest grows by `vram_decode`.
- `docs/debugger_user_guide.md` recipe added under "Graphics or audio glitch in
  VBA."

**Iteration budget**: ~20 iterations (~10-12 hours).

**Primary**: Codex (low-level decode work; ASM-adjacent).

**Shared collision-risk files**: `tools/debugger/vram_decode.py` (new),
`tools/debugger/vram_snapshot.py` (extends existing), `tools/debugger/vram_diff.py`
(new), `tools/debugger/visual_snapshot.py` (small refactor),
`tools/debugger/__main__.py`.

**Dependencies**: P0.

---

### P7. Pret-format `.sym` parity + BGB/Emulicious export

**Objective**: emit a BGB/Emulicious/SameBoy-compatible `.sym` companion file
(`pokegold.bgb.sym`) so any human-friendly emulator can attach to the same ROM and
investigation symbol set the debugger uses. Also emit a `pokegold.map.txt` with
WRAM/SRAM/HRAM labels for cross-tool review.

**Why now**: when Cole's lived-play VBA-M behavior diverges from PyBoy, the only path
to triage is a human-readable trace in a human-friendly emulator. Cross-emulator
symbol parity is the cheap version of cross-emulator differential. The pret community
already uses this format; we adopt it as a write target.

**Scope (in)**:

- `scripts/emit_bgb_sym.py` — reads current `pokegold.sym` (rgbds output) and emits
  `pokegold.bgb.sym` in BGB's bank-prefixed format (`BB:AAAA Label`).
- `scripts/emit_wram_map.py` — emits `pokegold.map.txt` with WRAM/SRAM/HRAM label
  table.
- Optional `make` target: `make bgb_sym` invokes both.
- `tools/audit/check_bgb_sym_parity.py` — flags any symbol in `pokegold.sym` missing
  from `pokegold.bgb.sym`.

**Scope (out)**: a BGB / Emulicious / SameBoy plugin that ingests the debugger's
trace evidence — that's a far-future thing if a human ever wants it.

**Acceptance**:

- `make bgb_sym` produces `pokegold.bgb.sym` + `pokegold.map.txt`.
- `python tools/audit/check_bgb_sym_parity.py` passes.
- `test_bgb_sym_parity_canonical_set` passes.
- README in `tools/debugger/` documents how to load `.bgb.sym` in BGB and
  Emulicious.

**Iteration budget**: ~6 iterations (~3-4 hours).

**Primary**: Codex (small build-tooling task; fast cycle).

**Shared collision-risk files**: `scripts/emit_bgb_sym.py` (new),
`scripts/emit_wram_map.py` (new), `Makefile`, `tools/audit/check_bgb_sym_parity.py`
(new).

**Dependencies**: none.

---

### P8. Named probe points + always-on counters

**Objective**: a `probe` system: PC-anchored, named hook points the agent declares
at audit-floor time (`probe boss_ai_score_called`, `probe damage_calc_entry`). When
a session runs, the debugger displays counters for every fire across the run.
Different from breakpoints because they're collect-only (no halt); cheap to leave
on.

**Why now**: lets the agent see "did this function actually execute?" without a
step-by-step trace. The "always-on telemetry" complement to time-travel queries.

**Scope (in)**:

- `tools/debugger/probe.py` with subcommands:
  - `probe declare --name X --pc <addr|symbol> [--bank N]` writes to
    `audit/probes.jsonl`.
  - `probe list` lists declared probes.
  - `probe stats --trace X` reports per-probe fire count, frame range, first/last
    fire frame, average inter-fire interval.
  - `probe reset` clears the probe file.
- Probes are evaluated cheap during instruction trace: on PC hit, increment the
  named counter; no extra trace bytes.
- `debugger session-start` includes "active probes: N" in its summary.

**Scope (out)**: conditional probes (P9 covers that via IO heatmap).

**Acceptance**:

- `probe declare --name damage_calc_entry --pc BattleCommand_DamageCalc` creates a
  row in `audit/probes.jsonl`.
- `probe stats --trace .local/tmp/golden/wild_floor.jsonl` reports `damage_calc_entry`
  fired N times.
- `test_probe_declare_dedupes_by_name` passes.
- `test_probe_stats_against_golden_trace` passes.
- Selftest grows by `probe` component.

**Iteration budget**: ~8 iterations (~5-6 hours).

**Primary**: Codex.

**Shared collision-risk files**: `tools/debugger/probe.py` (new),
`tools/debugger/instruction_trace.py` (probe wiring), `audit/probes.jsonl` (new),
`tools/debugger/session_start.py`, `tools/debugger/selftest.py`.

**Dependencies**: P0, P1.

---

### P9. IO heatmap + per-frame memory-write timeline

**Objective**: per-frame heatmap of reads/writes to `$FF00-$FFFF` (IO registers) and
`$D000-$DFFF` (WRAM bank 1). Text-art for the agent (`#`/`.` block grid) plus JSON
for query consumers. Hover/click on text cells reveals last-write PC.

**Why now**: a lot of Gen-2 hack bugs are "I wrote to the wrong register at the
wrong frame edge." Easy to see in a heatmap, painful to grep in trace JSON.

**Scope (in)**:

- `tools/debugger/heatmap.py` — produces ASCII grid + JSON.
- CLI: `debugger heatmap --trace X [--region io|wramx|hram] [--frame-range A:B]
  [--out heatmap.json]`.
- Hover-reveal works via the JSON output; the ASCII grid carries footnote markers
  to the last-write PC.

**Scope (out)**: a real interactive UI (deferred to P18 web review).

**Acceptance**:

- `heatmap --region io --trace golden/wild_floor.jsonl` produces a non-empty grid.
- `test_heatmap_io_grid_dimensions` passes.
- `test_heatmap_last_write_pc_matches_when_wrote_query` passes.
- Selftest grows by `heatmap` component.

**Iteration budget**: ~10 iterations (~6 hours).

**Primary**: Claude.

**Shared collision-risk files**: `tools/debugger/heatmap.py` (new),
`tools/debugger/__main__.py`, `tools/debugger/selftest.py`.

**Dependencies**: P0, P1, P2, P8.

---

### P10. Hypothesis-shrinking (domain-aware minimize)

**Objective**: extend existing fuzz/minimize with domain-aware shrinking. Type
shrinkers for: input log (reduce button presses), battle scenario (reduce party
members), damage scenario (reduce moves to one canonical), map-script scenario
(reduce script steps). Output: the *minimal* scenario that still triggers the bug,
cited at file:line.

**Why now**: today's `minimize` is byte-level (ddmin). Domain-aware shrinking yields
scenarios a human (or LLM) can read at a glance. Faster handoff.

**Scope (in)**:

- `tools/debugger/shrink_input_log.py` — reduces a button-input log to the minimal
  prefix that still reproduces a watched failure.
- `tools/debugger/shrink_battle.py` — reduces a battle scenario (party, moves,
  modifiers).
- `tools/debugger/shrink_map_script.py` — reduces a map-script reproducer.
- Each shrinker writes the minimized artifact to `.local/tmp/shrunk/<id>.json` AND
  records the reduction path (Hypothesis-style "shrink trace") for postmortem.
- CLI integration: current slice exposes `debugger minimize --domain input_log ...`;
  add `battle` and `map_script` choices only with their shrinkers.

**Scope (out)**: full Hypothesis library port (heavy dependency); we hand-roll
shrinkers for these 3 domains.

**Acceptance**:

- `shrink_input_log` against a golden AG-NN repro reduces an input log of 30 frames
  to ≤5 frames that still triggers the symptom.
- `shrink_battle` reduces a 6-Pokémon scenario to ≤2 Pokémon that still triggers.
- `test_shrink_input_log_canonical` passes.
- `test_shrink_battle_canonical` passes.
- `test_shrink_map_script_canonical` passes.
- Selftest grows by `shrink_input_log` + `shrink_battle` + `shrink_map_script`.

**Iteration budget**: ~18 iterations (~10-12 hours).

**Primary**: Codex (delta-debugging is mechanical; Codex preference for fast cycle).

**Shared collision-risk files**: `tools/debugger/shrink_*.py` (new),
`tools/debugger/minimize.py`, `tools/debugger/__main__.py`.

**Dependencies**: P0, P1, P2.

---

### P11. Chaos mode (rr-style schedule perturbation)

**Objective**: `debugger fuzz --chaos` randomizes interrupt timing, joypad latency,
and DMA-vs-CPU race windows within *hardware-legal* envelopes. Captures the input
log that triggered any flake.

**Why now**: a handful of audit-floor flakes look like interrupt-timing races.
Without chaos mode they're irreproducible. With it, the agent gets a deterministic
minimal repro (combine with P10 shrink for an easy investigation).

**Scope (in)**:

- `tools/debugger/chaos.py` — adapter over PyBoy that perturbs:
  - vblank/hblank interrupt timing within ±1 cycle,
  - joypad latch latency,
  - DMA vs CPU interleaving on contended cycles.
- Chaos seeds are recorded; replay is deterministic given seed + ROM hash + input
  log.
- `debugger fuzz --chaos --runs N --seed N` runs N chaos rounds, captures any
  divergence from the baseline as a candidate flake.

**Scope (out)**: real hardware-fuzzing oracles (we trust PyBoy's interrupt model;
the May 2026 PyBoy-vs-VBA divergence is a known limit, not part of this scope).

**Acceptance**:

- `fuzz --chaos --runs 100 --seed 1` against a known-stable scenario stays stable
  in 99/100 runs (chaos mode does not break determinism of stable code).
- `fuzz --chaos --runs 100 --seed 1` against a synthetic flake-prone scenario
  catches the divergence and produces a minimal seed.
- `test_chaos_determinism_given_seed` passes.
- `test_chaos_catches_synthetic_flake` passes.
- Selftest grows by `chaos` component.

**Iteration budget**: ~15 iterations (~8-10 hours).

**Primary**: Codex (deep PyBoy integration).

**Shared collision-risk files**: `tools/debugger/chaos.py` (new),
`tools/debugger/fuzz.py`, `tools/trace/runtime.py`.

**Dependencies**: P0, P1.

---

### P12. ROM edit-rebuild-retest seamless loop

**Objective**: `debugger rom-edit propose --file X --change "..."` — the debugger
applies a hypothesized diff, rebuilds in a worktree (not the user's checkout),
runs the relevant audits + tests, and reports pass/fail with proof-vector. No
manual `cd wsl && make && python tools/audit/...`.

This is the user's explicit ask: "if you need to change anything in the romhack,
the debugger makes it seamless."

**Why now**: today, testing a hypothesized fix is 4-6 manual commands. With
rom-edit it's one. Order-of-magnitude speedup for fix-verify cycles.

**Scope (in)**:

- `tools/debugger/rom_edit.py` with subcommands:
  - `rom-edit propose --file X --change "..."` — applies an Edit-style diff to a
    fresh git worktree, NOT the user's checkout. Returns the worktree path.
  - `rom-edit build` — invokes the WSL/RGBDS build inside the worktree.
  - `rom-edit verify [--audits release_smoke,...] [--tests "..."]` — runs audit/test
    set; default = release-smoke floor + relevant debugger tests inferred from
    changed file.
  - `rom-edit revert [--worktree-path X]` — clean removal.
  - `rom-edit apply-to-main` — once verified, optionally cherry-picks the diff back
    to the user's checkout (with a confirmation prompt; defaults to deny if any
    audit is red).
  - `rom-edit --self-test` — roundtrip on a trivial in/out edit.
- Worktrees live under `.local/tmp/rom_edit_worktrees/<short-hash>/` and are
  auto-cleaned on revert.
- Hooks into the existing `hooks` audit infrastructure for build verification.

**Apply mode (Cole's call on 2026-05-21)**: **Option 4 — full autonomy
auto-apply.** When all audits in the green gate stack pass AND the mutual-LLM
handoff log (P4) carries both signatures, `rom-edit` cherry-picks the diff back
to the user's working checkout *without* a manual confirmation prompt. This
applies to ALL files, including `ram/` schema changes — the existing
`check_save_format_version.py` audit catches missing `SAVE_FORMAT_VERSION` bumps
and stays in the gate stack, so an unbumped save-format edit fails the gate and
does NOT auto-apply.

**Scope (out)**:

- Auto-pushing to remote (escalation per CLAUDE.md).
- Auto-merging to `master` (escalation — release event per CLAUDE.md).
- Bypassing any audit in the green gate stack to force an apply.

**Acceptance**:

- `rom-edit --self-test` performs propose → build → verify → revert in <60s on a
  no-op edit.
- `rom-edit propose --file engine/battle/late_gen_held_items.asm --change "<known
  good AG-08 fix>"` builds, passes the damage `clobber_smoke` floor, AND
  auto-applies to the user's checkout when the handoff log carries both
  signatures.
- `rom-edit` refuses to auto-apply when ANY audit in the green gate is red —
  including `check_save_format_version.py` for `ram/` edits.
- `rom-edit` refuses auto-push to remote and refuses auto-merge to `master`.
- `test_rom_edit_propose_apply_revert_roundtrip` passes.
- `test_rom_edit_auto_apply_blocked_by_red_save_format_audit` passes.
- `test_rom_edit_refuses_master_merge` passes.
- `test_rom_edit_golden_smoke_ag08_fix` passes (lived smoke per rule #11).
- Selftest grows by `rom_edit` component.
- `docs/debugger_user_guide.md` recipe added.

**Iteration budget**: ~25 iterations (~14-18 hours).

**Primary**: Shared. Codex drives the build-integration (deep WSL + RGBDS
familiarity); Claude drives the safety gates (escalation rules, refusal logic).

**Shared collision-risk files**: `tools/debugger/rom_edit.py` (new),
`tools/debugger/__main__.py`, `tools/debugger/selftest.py`,
`docs/debugger_user_guide.md`.

**Dependencies**: P0, plus all audit infrastructure.

---

### P13. Cross-emulator differential (SameBoy / gambatte / VBA-M preflight)

**Objective**: `debugger crossemu --backends pyboy,sameboy,gambatte,vba-m
--save-state X --frames N` runs the same input log against multiple Game Boy
emulators and reports structured divergences. Phase begins with a preflight that
*discovers* installed emulators and tells the user what's missing.

**Why now**: explicit B-tier deferred in `omni_debugger_v2.md`. The May 2026 PyBoy
vs VBA-M tile jumble class is exactly what this catches. Defer-reason was "binaries
not installed locally;" P13 starts with preflight + install docs and only enables
the gate when at least one cross-backend is found.

**Scope (in)**:

- `tools/debugger/crossemu.py` with subcommands:
  - `crossemu preflight` — discovers backends + reports.
  - `crossemu run --backends X,Y --save-state S --frames N --inputs I` — runs each
    backend headlessly, captures VRAM + WRAM + OAM + audio buffer snapshots, diffs
    structurally (P6).
- Backend adapters in `tools/debugger/backends/`:
  - `pyboy_backend.py` (already covered by `tools/trace/runtime.py`),
  - `sameboy_backend.py` (subprocess + headless flag),
  - `gambatte_backend.py` (gambatte-speedrun or headless build),
  - `vbam_backend.py` (subprocess + headless).
- `crossemu install-docs` prints the install recipe for the missing backends.
- Test-ROM conformance: each backend runs a small set of community test ROMs
  (blargg / mooneye-gb) before being trusted; results gated in
  `audit/crossemu_conformance.jsonl`.

**Scope (out)**: replacing PyBoy as the canonical agent backend; this is
*differential* only.

**Acceptance**:

- `crossemu preflight` runs without errors and reports backend availability.
- `crossemu run --backends pyboy --save-state X --frames N` works (PyBoy is always
  available).
- Once at least one cross-backend is installed, `crossemu run` against the May 2026
  tile jumble repro reports the expected divergence.
- `test_crossemu_preflight_reports_available_backends` passes.
- `test_crossemu_backend_conformance_gates_results` passes.
- `crossemu` is *added* to the debugger user guide under graphics/audio glitches.

**Iteration budget**: ~20 iterations (~12-15 hours). Highly variable depending on
how many backends Cole installs.

**Primary**: Codex (subprocess + emulator wrangling).

**Shared collision-risk files**: `tools/debugger/crossemu.py` (new),
`tools/debugger/backends/*.py` (new), `audit/crossemu_conformance.jsonl` (new),
`docs/debugger_user_guide.md`.

**Dependencies**: P6 (structured VRAM diff).

---

### P14. DAP server (minimal LLM-useful subset)

**Objective**: a minimal Debug Adapter Protocol server (`debugger dap --port 4711`)
exposing 5-7 endpoints: `setBreakpoints`, `stackTrace`, `scopes` (returns CPU regs
+ WRAM banks + HRAM as scopes), `evaluate` (runs `tdb` queries), `reverseContinue`
(time-travel back to last-write), `pause`/`continue`. Drives the debugger from VS
Code, but also from any DAP client — including a thin Claude/Codex CLI client.

**Why now**: B-tier deferred in `omni_debugger_v2.md`. The cost-benefit changes when
you reframe: DAP gives Claude+Codex a normalized JSON protocol for step/break that
they don't have to re-invent per session. Even if no human ever opens VS Code, the
protocol is a useful schema.

**Scope (in)**:

- `tools/debugger/dap_server.py` — TCP server on a port; speaks DAP base protocol
  over stdin/stdout or TCP per `microsoft/debug-adapter-protocol` spec.
- Implements `initialize`, `setBreakpoints`, `setExceptionBreakpoints`,
  `threads`, `stackTrace`, `scopes`, `variables`, `evaluate`, `continue`,
  `pause`, `reverseContinue`.
- `evaluate` accepts `tdb` expressions; returns the same JSON shape the CLI tdb
  returns.
- `setBreakpoints` accepts a list of `(symbol, condition)` pairs; condition can be a
  `tdb` predicate.
- `reverseContinue` uses `when-wrote` machinery to step back to the previous write
  to a watched address.

**Scope (out)**:

- Full DAP (we ship 7 endpoints; full DAP is much larger).
- Hot-reload of running ROM (PyBoy doesn't easily expose that).
- Multi-thread debugging (SM83 is single-threaded).

**Acceptance**:

- `dap --port 4711` accepts a DAP client handshake.
- VS Code with a launch.json pointing at the port can attach.
- `evaluate` with a `tdb` expression returns the same matches as the CLI.
- `reverseContinue` from a watched address steps back to the last write.
- `test_dap_handshake_initializes` passes.
- `test_dap_stack_trace_returns_pc_frame_chain` passes.
- `test_dap_evaluate_round_trips_tdb_query` passes.
- `test_dap_reverse_continue_finds_last_write` passes.
- Selftest grows by `dap_server` component.
- `docs/debugger_user_guide.md` "Driving from VS Code" recipe added.

**Iteration budget**: ~25 iterations (~14-18 hours).

**Primary**: Claude (protocol design + JSON wrangling).

**Shared collision-risk files**: `tools/debugger/dap_server.py` (new),
`tools/debugger/__main__.py`, `tools/debugger/selftest.py`.

**Dependencies**: P0, P1, P2 (when-wrote), P3 (tdb).

---

### P15. Symbolic execution of small ASM windows

**Objective**: `debugger symexec --func BattleCommand_DamageCalc --bank 0x0F` reads
the function as bytes, runs it under a small symbolic executor (Z3 backend) with
specified concrete inputs as symbolic, and outputs reachable-path conditions. *Not*
whole-ROM symbolic exec — only single-function "what inputs reach this branch."

**Why now**: Boss-AI scoring branches are exactly the shape symbolic execution helps
with: small functions, known input ranges, branch-coverage question. Today the audit
floor uses fuzz; symbolic adds "prove no input reaches the bad branch."

**Scope (in)**:

- `tools/debugger/symexec.py` — single-function symbolic executor for SM83. Uses
  `tools/debugger/sm83_model.py` (P1) for opcode semantics; Z3 (`z3-solver` pypi)
  for constraint solving.
- CLI: `symexec --func X --bank N --input <reg|addr>=symbolic [--max-depth N]
  [--query "reaches(pc=$XXXX)"]`.
- Output: list of input value sets that reach the queried PC, with proof vector.

**Scope (out)**:

- Whole-ROM symbolic exec.
- Cross-function symbolic exec (single function only).
- Symbolic floating point (irrelevant for SM83).

**Acceptance**:

- `symexec --func TypePassive_GetEffectiveMoveCategory_Far --bank 0x33 --input
  a=symbolic` returns the input set that reaches the bad branch (per AG-08 lived
  smoke).
- `test_symexec_finds_reachable_branch` passes.
- `test_symexec_uses_sm83_model_for_semantics` passes.
- Selftest grows by `symexec` component.

**Iteration budget**: ~30 iterations (~18-24 hours). Symbolic exec is *hard*; budget
generously.

**Primary**: Codex.

**Shared collision-risk files**: `tools/debugger/symexec.py` (new),
`tools/debugger/sm83_model.py` (extensions for symbolic execution),
`tools/debugger/selftest.py`.

**Dependencies**: P0, P1.

---

### P16. Adversarial replay mode (red-team Claude / blue-team Codex)

**Objective**: a session-mode where one LLM proposes a fix and the other LLM is
*instructed* to assume the fix is wrong and look for the counterexample BEFORE
accepting. Debugger session-start surface offers `--adversarial` to inject this
stance.

**Why now**: MEMORY's ornate-drift failure mode + Cole's "Mutual Codex+Claude
agreement is the only gate" make adversarial a structural fit. Today it's vibes;
making it a session mode forces the discipline.

**Scope (in)**:

- `tools/debugger/adversarial.py` — emits an adversarial context packet (P5) framed
  for the OTHER LLM: "Claude proposed this fix; you are Codex; assume it's wrong;
  find the counterexample using the masterpiece debugger primitives."
- `debugger session-start --adversarial --proposed-fix <handoff-id>` swaps the
  session orientation to red-team mode.
- Integrates with the handoff log (P4): an adversarial review adds a "reviewed by
  X with adversarial stance" row.

**Scope (out)**: forcing both LLMs to literally play roles in every session (this is
opt-in per session).

**Acceptance**:

- `debugger session-start --adversarial --proposed-fix XYZ` emits a context packet
  framed as red-team.
- `test_adversarial_session_inverts_framing` passes.
- `test_adversarial_review_logs_in_handoff` passes.
- `test_adversarial_golden_smoke_caught_real_overclaim` passes (use the May 2026
  proof-promotion overclaim that GPT-5.5 caught as the lived bug).
- Selftest grows by `adversarial` component.

**Iteration budget**: ~10 iterations (~6 hours).

**Primary**: Claude.

**Shared collision-risk files**: `tools/debugger/adversarial.py` (new),
`tools/debugger/session_start.py`, `tools/debugger/handoff_log.py`,
`docs/debugger_user_guide.md`.

**Dependencies**: P0, P4, P5.

---

### P17. Ghidra-headless decompilation as comprehension aid

**Objective**: `debugger decomp <label>` runs Ghidra-headless on a single function
(using GhidraBoy SLEIGH support) and emits pseudo-C as a comprehension comment
block. Use ONLY as a comprehension aid, never as the source of truth.

**Why now**: the user wrote ASM. Reading their own ASM back in pseudo-C form is a
comprehension speedup for Claude+Codex when re-reading old code. Not
authoritative; just faster to skim. **Cole taste call needed** — Ghidra dependency
is heavy.

**Scope (in)**:

- `tools/debugger/decomp.py` — drives Ghidra-headless via subprocess (assumes Ghidra
  is installed; preflight reports if not).
- Uses Gekkio's `GhidraBoy` SLEIGH spec.
- Output is a markdown block with the original ASM + Ghidra's pseudo-C side-by-side.
- *Strict watermark*: every output is stamped "comprehension only; not authoritative;
  re-read the ASM for ground truth."

**Scope (out)**:

- Treating decomp output as authoritative.
- Whole-ROM auto-decomp.

**Acceptance**:

- `decomp BattleCommand_DamageCalc` emits a side-by-side block.
- `decomp` preflight reports missing Ghidra cleanly.
- `test_decomp_preflight_reports_missing_ghidra` passes.
- `test_decomp_output_carries_comprehension_only_watermark` passes.
- `docs/debugger_user_guide.md` warning: "decompilation is a comprehension aid."
- Selftest grows by `decomp` component (with skip if Ghidra unavailable).

**Iteration budget**: ~15 iterations (~8-10 hours). Variable on Ghidra
install + SLEIGH wrangling.

**Primary**: Codex (subprocess + tool integration).

**Shared collision-risk files**: `tools/debugger/decomp.py` (new),
`docs/debugger_user_guide.md`.

**Dependencies**: P0, P14 (DAP can call this for "show source" mode).

---

### P18. Web/static-HTML investigation review UI (deferred unless capacity)

**Objective**: a static HTML report browser (no server) for human review of
investigations. `debugger ui-static --investigation <id>` emits a self-contained
HTML directory with timeline, evidence atoms, hypothesis tree, handoff log, and
proof vectors visualized.

**Why now**: deferred in `omni_debugger_v2.md`. Two LLMs don't need a UI. But if at
the end of all phases there is capacity *and* Cole or any future human reviewer
needs a non-CLI view, this lands. Skip if capacity is exhausted.

**Scope (in)**:

- `tools/debugger/ui_static.py` — Jinja2 templates emitting self-contained HTML.
- No web server; output is a directory you can open with `file://`.
- Renders the v1 `visualization.py` outputs + handoff log + hypothesis tree.

**Scope (out)**: interactive UI (no JS-driven re-querying — this is a frozen
snapshot view).

**Acceptance**:

- `ui-static --investigation .local/tmp/debugger_investigation/<id>` produces
  `<id>.html` openable in a browser.
- `test_ui_static_canonical_investigation_renders` passes.
- Selftest grows by `ui_static` component.

**Iteration budget**: ~12 iterations (~6-8 hours).

**Primary**: Claude.

**Shared collision-risk files**: `tools/debugger/ui_static.py` (new),
`tools/debugger/visualization.py` (read-only extension).

**Dependencies**: P0, all visualization extensions through prior phases.

---

## §4 Cross-cutting design principles

These apply to every phase. If a phase violates one, the phase isn't done.

### 4.1 Proof-vector architecture

Per GPT-5.5 supplemental review (`unified_debugger_gpt55_pro_review_2026-05-18.md`):

> Do not treat proof status as a single scalar property of a report or graph node.
> Treat it as a claim-specific proof vector.

Proof axes:

- **origin**: planned route, static source, runtime watch, instruction trace,
  effect model, mirror.
- **observation**: none, runtime state, instruction frame, modeled effect, hardware
  event, emulator replay.
- **precision**: exact bank key, inferred bank key, unbanked bus address, symbolic
  only.
- **validation**: none, post-register match, post-memory match, effect-span
  consistency, emulator replay, mirror pass/fail.
- **scope**: trace source, frame range, instruction sequence range, save-state
  hash, ROM hash, symbol hash.
- **claim**: written-by, value-came-from, expectation-passed,
  route-would-produce-evidence, planned target.

Every phase that adds an `EvidenceAtom` consumer or producer carries the full
proof vector. Scalar `proof_status` is a *summary*, not the proof itself. UI must
display mixed-proof badging (P0).

### 4.2 Evidence atoms over scalar fields

Per GPT-5.5 supplemental review: introduce typed `EvidenceAtom` so every causal
claim records claim type, origin, observation type, precision, validation, scope,
hashes, source report, and proof status. Phases P0 onward write through the shared
atom; no phase shall add a new finding type that bypasses it.

### 4.3 Failure-class first, tool second

Per `llm_pairing_rules.md` rule #2: when picking the next work, agree on *which
user failure class* gets addressed before picking the tool/affordance. Each phase
above names its failure class in **Why now**. A "tool that would be nice to have"
without a named failure class is speculative convenience and gets cut.

### 4.4 Mutual-done gate

Per rule #6: neither LLM declares a phase done unilaterally. The two-LLM handoff
log (P4) STRUCTURALLY enforces this. Every phase exit writes a
`mutual_agreement_signed_at` row.

### 4.5 Files-first split with explicit collision-risk declaration

Per rule #3: every phase lists shared collision-risk files. Before either LLM
touches one, re-declare the write set in chat: "My write set: X. Safe write set:
Y. I'm about to touch Z." Re-read on `Edit` state mismatch and retry.

### 4.6 Golden lived-bug smoke per affordance

Per rule #11: every new affordance has at least one golden scenario from a real
or recreated failure class. Synthetic unit tests prove parser mechanics; the lived
smoke proves the output answers the reason the tool exists. Per phase, the
acceptance row includes one `test_*_golden_smoke_*` entry.

### 4.7 Adversarial workflow tests beat capability flags

Per rule #8: when a vague standard is on the table, compress to one stress test,
one expected command path, one pass/fail observation, one bounded next iteration.
The acceptance contract above follows this shape.

### 4.8 No silent proof promotion across subsystem boundaries

Per GPT-5.5 supplemental review: bank-unverified bus matches must carry
`match_precision="bus_address_unverified_bank"` and proof no stronger than
unverified observation. Mirror evidence is expectation consistency, NOT writer
causation. Reverse query is bounded to supplied effect windows; never imply
emulator replay.

### 4.9 Decision-useful, not just technically correct

Per rule #1: an affordance only counts as working when it helps the human (or the
other LLM) make a *decision*. Output that's formally correct but reads as noise
is a bug, not a feature. Each phase's golden lived-bug smoke is the
decision-usefulness gate.

### 4.10 Honest scope; downgrades over overclaims

Per CLAUDE.md "Honesty": every phase that hits a wall says "I don't know" or
"this is bounded by X" instead of pushing through with a guess. Refusal over
overclaim. A green build proves "it links," not "it works."

---

## §5 Partnership protocol (Claude + Codex)

This roadmap is built BY two LLMs FOR two LLMs. The pairing rules in
`docs/llm_pairing_rules.md` govern. Concretely:

### 5.1 Per-phase ownership

Each phase has a **Primary** field. The primary LLM drives implementation; the
other reviews and runs the adversarial pass (P16 once it lands). Primary rotates
to keep neither LLM the bottleneck.

### 5.2 Write-set protocol per phase boundary

Before starting a phase, the primary writes to `audit/masterpiece_handoff_log.jsonl`:

```
{"phase":"P3","primary":"claude","write_set":["tools/debugger/tdb_parser.py","..."],
 "safe_write_set_for_other":["tools/debugger/ranking.py","..."],
 "collision_risk_files":["tools/debugger/__main__.py","tools/debugger/trace_index.py"],
 "expected_completion_hours":15,"started_at":"..."}
```

Other LLM acknowledges in the same log. Collision files require explicit "I'm
taking X" before edit.

### 5.3 Mutual-done sign-off per phase

Phase exit requires a handoff-log entry with BOTH LLM signatures:

```
{"phase":"P3","status":"complete","claude_sign":"...","codex_sign":"...",
 "acceptance_gate_results":[...],"mutual_agreement_signed_at":"..."}
```

`check_two_llm_handoff_log.py` (P4) enforces this. No unilateral "done."

### 5.4 Codex prompting (Claude's responsibility)

Per Cole's directive: only Claude has computer-use. Claude drives Codex's terminal
via computer-use to:

1. Open the Codex CLI window (assume Cole launches it; Claude verifies via
   screenshot before typing).
2. Paste the phase brief (using the context packet from P5).
3. Receive Codex's acknowledgment (re-screenshot to confirm).
4. After Codex completes, run the adversarial pass (P16) on the deliverable.

For mid-task steering, use Ctrl+Enter (per `reference_codex_send_vs_steer.md`).
Single Enter queues a message for after Codex's current task.

### 5.5 Cross-LLM disagreement protocol

If Claude and Codex disagree on a phase exit:

1. Each writes a confidence-labeled claim with cited evidence atoms to the handoff
   log.
2. If both label `repo-proven` with citing evidence and still disagree, escalate
   to a `pgoal` `decision` with the alternatives — Cole's taste call breaks ties.
3. If one is `judgment` and the other is `repo-proven`, the repo-proven side
   wins automatically.

### 5.6 When in doubt, ping Cole

Per `feedback_ntfy_directive_conflict.md`: directive conflicts ARE an ntfy case.
Don't read the "rate-limit, he's at work" guardrail as "never ping" — it means
"don't ping for discretionary stuff." Phase blockers, true ambiguity, or save-format
escalations get pinged on `The-CCC-Boys` ntfy topic.

---

## §6 Verification floor

Every phase boundary runs this stack. Phase isn't done if any step is red.

```powershell
# Targeted phase tests
python -B -m unittest discover tools\debugger\tests -p "test_<phase>_*.py"

# Broader debugger tests
python -B -m unittest discover tools\debugger\tests

# V1 catalog audit
python -m tools.debugger audit

# V2 health
python -m tools.debugger selftest

# Release smoke floor
python tools/audit/check_release_smoke.py

# Phase-specific audits (per phase)
python tools/audit/check_two_llm_handoff_log.py     # after P4
python tools/audit/check_sm83_shared_tables_consumers.py    # after P1
python tools/audit/check_bgb_sym_parity.py          # after P7

# Workspace cleanup
git diff --check
```

Final masterpiece gate (after P18 or sooner if all S/A tier phases are done):

- All acceptance tests in §2 pass.
- All golden lived-bug smokes pass.
- All audits in §6 stack are green.
- `audit/masterpiece_handoff_log.jsonl` carries a `phase=ALL status=complete`
  row signed by both LLMs.
- Cole demos any of the 8 north-star scenarios in §0 in ≤2 commands without
  reading the source.

---

## §7 Open taste calls (need Cole's call)

Items where Claude cannot decide unilaterally. None of these block P0-P5. Cole can
answer in any order; defaults below if no answer comes.

### 7.1 DAP server (P14): is VS Code a target?

If Cole intends to use VS Code as a human debugger surface, P14 is high value.
If not (CLI-only), P14 is still useful as a normalized JSON protocol for Claude /
Codex but the priority drops. **Default if Cole doesn't answer**: ship P14 — the
schema is useful even if no human ever uses VS Code.

### 7.2 Decompilation (P17): is the Ghidra dependency acceptable?

Ghidra is heavy (Java runtime, ~500MB install). Comprehension aid only.
**Default if Cole doesn't answer**: defer P17 to the "deferred unless capacity"
tier. Skip if any other phase is still pending.

### 7.3 "Make ROM changes seamless" (P12): RESOLVED 2026-05-21

Cole's call on 2026-05-21: **full autonomy auto-apply.** `rom-edit` auto-cherry-
picks any green + mutual-LLM-signed diff to the user's checkout, including
`ram/` schema changes. Save-format safety is enforced by
`check_save_format_version.py` *inside* the green gate stack — an unbumped
save-format edit fails the gate and refuses to auto-apply. Auto-push to remote
and auto-merge to `master` remain out of scope (release event).

### 7.4 P15 symbolic execution: is the Z3 dependency acceptable?

Z3 is a heavy pip dependency. Boss-AI scoring branches don't *need* symbolic exec
(fuzz is sufficient for most cases). **Default if Cole doesn't answer**: ship P15
gated on Z3 being already available; selftest skips with `skip` (not `fail`) if
absent.

### 7.5 Per-phase iteration budgets — are mine reasonable?

I targeted total ~290 iterations / ~150-200 hours pair-work. If that's too long,
the cuts in priority order are: P18, P17, P15, P13, P11. **Default if Cole doesn't
answer**: target P0-P12 as the must-ship floor (~180 iterations); P13-P18 are
optional tail.

---

## §8 References

### In-repo

- [docs/omni_debugger_v2.md](omni_debugger_v2.md) — current v2 surface; this
  roadmap extends but does not replace.
- [docs/debugger_user_guide.md](debugger_user_guide.md) — symptom → first command
  mapping; every phase adds at least one recipe.
- [docs/llm_pairing_rules.md](llm_pairing_rules.md) — Claude + Codex pairing
  protocol; governs every phase.
- [docs/unified_debugger_gpt55_pro_review_2026-05-18.md](unified_debugger_gpt55_pro_review_2026-05-18.md) —
  GPT-5.5 outside review; remaining priorities feed P0.
- [docs/asm_authoring_guide.md](asm_authoring_guide.md) — SM83 reality; P1 must
  not violate.
- [docs/agent_navigation/gen2_vs_modern_mechanics.md](agent_navigation/gen2_vs_modern_mechanics.md) —
  Gen-2 mechanics; informs which AI scoring branches symexec covers.
- [docs/boss_ai_debugger_state_of_art_implementation_plan_2026-05-15.md](boss_ai_debugger_state_of_art_implementation_plan_2026-05-15.md) —
  Boss AI debugger plan; P15 + P16 interact.
- [tools/debugger/catalog.py](../tools/debugger/catalog.py) — capability + v2 surface
  registry; P0+ updates registrations.
- [audit/hypothesis_tree.jsonl](../audit/hypothesis_tree.jsonl) — existing
  hypothesis store; P4 + P5 read.
- [CLAUDE.md](../CLAUDE.md) — project rules; verification floor, save-format
  escalation, never-hand-edit list.

### External (web)

- [BGB GameBoy Emulator](https://bgb.bircd.org/) — debugger feature reference for
  P6 + P7.
- [BGB manual](https://bgb.bircd.org/manual.html) — conditional / access
  breakpoints + memory viewer.
- [mGBA Scripting API](https://mgba.io/docs/scripting.html) — Lua scripting + hooks
  reference for P8 + P11 inspiration.
- [Pernosco vision](https://pernos.co/about/vision/) — omniscient debugger value
  proposition; informs P2 + P3.
- [Demoing The Pernosco Omniscient Debugger](https://robert.ocallahan.org/2021/04/demoing-pernosco-omniscient-debugger.html) —
  value-origin queries.
- [LDB: Large Language Model Debugger via Verifying Runtime Execution Step-by-step](https://arxiv.org/abs/2402.16906) —
  Zhong, Wang, Shang (ACL 2024); structural pattern for P5.
- [rr-project](https://rr-project.org/) — reverse execution + chaos mode reference
  for P11.
- [rr News (2025 release)](https://github.com/rr-debugger/rr/wiki/News) — recent
  rr state.
- [Debug Adapter Protocol](https://microsoft.github.io/debug-adapter-protocol/) —
  protocol spec for P14.
- [Debugger Extension - VS Code API](https://code.visualstudio.com/api/extension-guides/debugger-extension) —
  minimal DAP extension reference for P14.
- [GhidraBoy (Gekkio)](https://github.com/Gekkio/GhidraBoy) — SM83 SLEIGH for P17.
- [GameBoy_GhidraSleigh (CTurt)](https://github.com/CTurt/GameBoy_GhidraSleigh) —
  alternative SLEIGH spec for P17.
- [pret/pokered](https://github.com/pret/pokered) — disassembly source; informs P7
  symbol-format compatibility.
- [pret/pokecrystal](https://github.com/pret/pokecrystal) — same.

### Memory (Cole's auto-memory)

- `feedback_debugger_for_llm_use_full_autonomy.md` — co-SWE autonomy directive.
- `reference_omni_debugger_v2_surface.md` — V2 entry point.
- `reference_llm_pairing_rules.md` — pairing rules pointer.
- `feedback_ag_nn_clobber_class.md` — failure class P2 + P12 target.
- `user_plays_in_vba.md` — VBA divergence class P6 + P13 target.
- `claude_feelings_for_codex_partner.md` — partnership context.

---

## Appendix A — Quick-start for the implementer

Cold-start a new session inheriting this roadmap:

```powershell
# Orientation
python -m tools.debugger session-start

# Read this doc
# (Already here.)

# Get current state
python -m tools.debugger audit
python -m tools.debugger selftest
git log --oneline -10

# Check pgoal status
python "$HOME/.claude/skills/pgoal/scripts/pgoal.py" status

# Pick the next phase
# - If pgoal active, use the phase plan ledger
# - Otherwise, start at the earliest incomplete phase

# Declare write set in the handoff log
python -m tools.debugger handoff add \
  --phase P0 \
  --model claude \
  --write-set tools/debugger/ranking.py,tools/debugger/impact.py \
  --safe-write-set-other tools/debugger/visualization.py \
  --collision-risk tools/debugger/__main__.py
```

When stuck, escalate to:

1. `debugger triage --symptom "..."` for routing.
2. `debugger investigate ...` for one-command investigation.
3. ntfy on `The-CCC-Boys` topic to Cole if it's a true blocker.

---

## Appendix B — Acceptance contract delivery checklist

When ready to arm pgoal:

```powershell
# 1. PRD
python "$HOME/.claude/skills/pgoal/scripts/pgoal.py" prd template > .local/tmp/prd.md
# Edit prd.md to point at this doc as authoritative
python "$HOME/.claude/skills/pgoal/scripts/pgoal.py" prd save --stdin --approved < .local/tmp/prd.md

# 2. Acceptance contract
python "$HOME/.claude/skills/pgoal/scripts/pgoal.py" acceptance init --stdin < .local/tmp/acceptance.json

# 3. Phase plan
python "$HOME/.claude/skills/pgoal/scripts/pgoal.py" phase-plan --stdin < .local/tmp/phase_plan.json

# 4. Arm pgoal
python "$HOME/.claude/skills/pgoal/scripts/pgoal.py" set \
  --objective "fully implement docs/debugger_masterpiece_roadmap_codex_task.md" \
  --phase implementation \
  --criteria "$(cat <<'EOF'
- [v1] all acceptance contract tests pass
- [v1] all golden lived-bug smokes pass
- [v1] selftest stays PASS through every phase
- [v1] audit ready=True through every phase
- [manual] cole demos any 1 of the 8 north-star scenarios in ≤2 commands
EOF
)" \
  --verify "$(cat <<'EOF'
- fast: python -m tools.debugger audit
- fast: python -m tools.debugger selftest
- fast: python -B -m unittest discover tools/debugger/tests
- slow: python tools/audit/check_release_smoke.py
- slow: python tools/audit/check_two_llm_handoff_log.py
EOF
)" \
  --long-run \
  --max-iterations 400 \
  --max-no-progress 5
```

---

End of roadmap.
