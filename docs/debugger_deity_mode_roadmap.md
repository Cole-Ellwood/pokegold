# Debugger Deity-Mode Roadmap — from "God tool" to "God deity"

> **Forward-looking spec (authored 2026-05-29).** The debugger reached the
> **God-tool** bar — an omniscient repo Q&A oracle, unified onto canonical
> `master` (tip `04170ddf`; the nine `debugger-unify:` commits
> `31996f61`→`04170ddf`). That bar and its rationale are recorded in
> [`docs/debugger_unification_plan.md`](debugger_unification_plan.md) and the
> archived [`docs/debugger_godmode_spec.md`](debugger_godmode_spec.md). This
> doc defines the **next tier above it — deity mode** — and the ranked,
> step-by-step path to get there.
>
> **This is a plan, not an implementation.** Nothing here is built. Per the
> handoff: do **not** start implementing deity-mode features until Cole has
> reviewed this roadmap. Several phases carry North-Star decisions that are
> Cole's to make (see [§12](#12-north-star-decisions-cole-owns)).

**Status:** authored, awaiting review.
**Predecessor:** [`docs/debugger_godmode_spec.md`](debugger_godmode_spec.md)
(DEBUGGER-001, `COMPLETE`).
**Source of current truth:** `python -m tools.debugger session-start`,
[`docs/debugger_unification_plan.md`](debugger_unification_plan.md).

---

## 1) The tier line: what "deity mode" means

The God-tool bar (met) is an **oracle that prescribes proofs**. Ask it any
WHERE/WHY/WHAT question and it returns cited source anchors, a causal
explanation, the *exact proof command*, the inputs that command needs, the
disproof standard, and the regression gate. For runtime questions, that
"input you must supply" is the catch: a **hand-built save state**, a
**pre-captured trace window**, or a **hand-authored scenario**. The human is
still in the proof loop, feeding the oracle the state it reasons over. And
three whole surfaces — audio, graphics/UI, and the script VM under arbitrary
event context — are proven only by **static byte mirrors** (the ROM bytes
match the disassembly's prediction), never by *replaying the surface in an
emulator* and watching it behave.

Deity mode closes that loop. The debugger **supplies its own inputs and runs
its own proofs, end to end, across every surface.**

| | **God tool (done)** | **God deity (this roadmap)** |
|---|---|---|
| Runtime state | You hand it a save state | It **navigates a fresh game** to the state you name |
| Instruction taint | You capture the trace window first | It **auto-captures** the window around any byte, one shot |
| Audio / graphics / script VM | Proven by static byte mirror | Proven by **live emulator replay** under arbitrary context |
| Causal substrate | Two taint engines, separate SM83 models | **One unified SM83 model** behind both |
| Output | Static markdown / HTML report | **Live emulator-coupled** TUI / canvas |
| Human's role in a runtime proof | Ask + supply inputs + run the command + read | **Ask + read.** The debugger drives the rest |

The one-sentence definition:

> **Deity mode** = for *any reachable game state* and *any ROM surface*, the
> debugger can reach the state, capture the evidence, run the proof, and
> render the result **without a human supplying a save state, a trace, or a
> scenario** — only the question and the verdict cross the human boundary.

"Reachable" is load-bearing: deity mode does **not** mean omniscience over
unreachable or hidden-info states (that would violate the First-Playthrough
Promise's no-cheating rule). It means the debugger can autonomously reach and
prove anything a *player or the engine could legitimately produce* — within
the hard limits named next.

### What deity mode does NOT do — the ceiling

"Deity" is a **codename for self-driving proofs**, not a literal claim of
omniscience. The honest bar is Cole's original "**95% automates the debugging
job**," not 100%. Even fully built, the debugger cannot:

1. **Reach every state — only *tractably* reachable ones.** The input-space
   search is exponential; deep, long-horizon, or RNG-gated states can be
   infeasible to navigate to under any practical budget. "Reachable" means
   "the engine can produce it *and* the navigator can find a path within the
   compute budget" — not "any RAM configuration you can name."
2. **Answer hidden-information or taste questions.** No private reads; no "is
   this fair / fun / well-balanced," no "does this Pokémon now have a distinct
   role." Those are the First-Playthrough Promise and gameplay-taste calls —
   Cole's seat, escalated by design. The debugger *informs* them; it does not
   make them.
3. **Prove universal absence.** It finds counterexamples and proves *specific*
   scenarios. "This bug can never happen in any state" is not provable by
   trace/fuzz/replay — only "not in the states I checked." Universal
   correctness over all inputs is undecidable in general; the tool samples, it
   does not exhaust.
4. **Guarantee behavior on the real platform.** Proofs run on PyBoy
   (cross-checked on VBA-M). That is evidence about *an emulation*, not a proof
   about real MBC3 hardware or every flashcart/emulator config. Divergence is a
   known bug class (North-Star #5), not an edge case.
5. **Design features or make architectural calls.** It locates where a change
   goes, proposes a proof + regression gate, and at most drafts a diff. It does
   not decide *what* to build or *whether* the design is right.
6. **Exceed its own ground truth.** It reasons from the disassembly, the symbol
   table, and the static mirrors. A mislabeled symbol or a wrong mirror is an
   error the debugger inherits — it is only as correct as its inputs.

Deity mode shrinks the human's role in *mechanically-decidable, well-posed,
tractably-reachable* runtime questions to **ask-and-read**. The remaining ~5% —
taste, design, universal guarantees, real-hardware certainty — stays human **by
construction**, not for lack of effort. A phase that claims to cross one of
these limits is mis-scoped, not ambitious.

---

## 2) North-Star constraints that survive into deity mode

These are non-negotiable and unchanged from the God-tool bar
([`debugger_godmode_spec.md` §North Star](debugger_godmode_spec.md)). Every
phase below is designed to respect them; where a phase puts pressure on one,
it is flagged.

1. **Read-only on the ROM.** The debugger lives in `tools/`. It reads,
   indexes, navigates, and replays `engine/`, `data/`, `ram/`, `home/`,
   `gfx/`, `audio/`, `maps/`, `*.asm` — it never writes them. Deity-mode
   self-driving makes the debugger *act on* the ROM (drive inputs, page
   banks, read RAM); it still never *mutates* ROM source. (`rom_edit` is the
   one module in tension with this — see
   [§11](#11-phase-6--deferred-unification-cleanup) and
   [§12](#12-north-star-decisions-cole-owns).)
2. **No hidden-information cheating.** Auto-navigation drives the game through
   *legitimate inputs and engine transitions only*. It may seed RNG and read
   any RAM for *proof* purposes, but a synthesized "proof state" must be one
   the engine could actually reach; it must never fabricate an impossible
   board to make a claim true.
3. **ROM-byte-neutral tooling.** Pure `tools/*` work; zero `engine/data/ram`
   edits; `make compare` must still match `roms.sha1`. If any deity-mode
   change touches the trace ROM's bytes, that requires `make compare` review
   exactly as today.
4. **Honest synthesis.** Every state the debugger reaches on its own carries
   a **manifest** (checkpoint id + input script + frame count + RNG seed) and
   is **re-validated** (replaying the manifest reproduces the same RAM
   signature). Synthesized states are *labeled as synthesized*, never passed
   off as captured. Fail-closed: if the debugger cannot reach the named
   predicate, it says so — it does not approximate and pretend.
5. **Emulator-divergence honesty.** PyBoy is the local automation backend, but
   Cole plays in **VBA-M**, and PyBoy↔VBA-M divergence is a real bug class
   (the May 2026 tile jumble;
   [`docs/graphics_emulator_debugging.md`](graphics_emulator_debugging.md)).
   Deity-mode runtime proofs on timing/graphics-sensitive surfaces must be
   **cross-checked on VBA-M** via `crossemu` before they are declared
   authoritative, and a proof's answer must name which backend produced it.

---

## 3) How deity mode is measured

The God-tool bar is measured by a triad: `python -m tools.debugger audit`
(`ready=True`, 11/11 complete), `check_debugger_godmode_benchmark.py` (29/29),
and `python -m tools.debugger.selftest` (28/28 components). That triad already
reports green at the *God-tool* bar — so deity mode needs its **own,
higher** gate, built parallel to it rather than by moving the existing
goalposts (the whole repo's audit floor depends on the current `ready=True`).

**Phase 0 of this roadmap builds that gate** (it mirrors how the godmode
build started by building its benchmark harness). The deity gate is a triad:

1. **Deity benchmark** — `audit/debugger_deity_benchmark/questions.jsonl`, a
   new question set where every record carries `proof_mode: runtime` **and**
   `driver: auto`. A question scores PASS only when the debugger drove the
   proof end-to-end: **no hand-supplied save state, trace, or scenario.** Run
   by a new `tools/audit/check_debugger_deity_mode.py`. The God-tool benchmark
   (`debugger_godmode_benchmark`, 29/29) is **frozen and never regressed** —
   deity is additive.
2. **New selftest components** — one health-check slot per deity capability,
   added to `tools/debugger/selftest.py`. The count climbs **28 → 35** as the
   five capability phases (Phases 1–5) each land their component:
   `auto_navigation`, `auto_taint`, `audio_replay`, `graphics_replay`,
   `script_vm_replay`, `sm83_model_parity` (re-added — see
   [§9](#9-phase-4--full-sm83-model-unification)), `live_view` — plus 2 more
   (→ 37) if Phase 6a's `causal-graph`/`hardware-event-stream` verbs land.
3. **Deity audit tier** — `check_debugger_deity_mode.py` asserts (a) every
   deity-benchmark question's proof ran with `driver: auto` and passed, and
   (b) the new selftest components are green. Its top line —
   `deity_ready=True deity_gap_actions=0` — is the deity analogue of the
   God-tool `ready=True`. Optionally, annotate each capability in `catalog.py`
   with a `deity_gap` field so `audit --tier deity` surfaces the remaining
   frontier per-capability without perturbing the God-tool `ready=True`.

**Whole-roadmap done = `deity_ready=True`, deity benchmark pass_rate 1.000
(driver:auto), selftest at its new full count, God-tool triad still green,
`check_release_smoke.py` PASS.**

---

## 4) Phase ordering and the dependency spine

The frontier was already identified; this roadmap ranks it by **what unblocks
the most downstream work**, not by listed order. The keystone
(auto-navigation) is the substrate every other runtime phase stands on.

```
Phase 0  Deity measurement harness ............ (the numeric target)
   │
Phase 1  Auto-navigation / state synthesis ..... KEYSTONE — unblocks 2 & 3
   │           │
   ▼           ▼
Phase 2     Phase 3
auto-taint  runtime replay of static surfaces
(one-shot)  (audio · graphics/UI · script VM)
   │           │
   └────┬──────┘
        ▼
Phase 4  SM83-model unification ................ (substrate coherence)
        ▼
Phase 5  Live emulator-coupled visualization ... (the deity "face")
        ▼
Phase 6  Deferred-unification cleanup .......... (rom_edit · causal-graph ·
                                                  hw-event-stream · codex_* IDs)
```

Phases 2 and 3 both depend on Phase 1 but are independent of each other and
could run in parallel. Phase 4 wants both taint (Phase 2) and the trace engine
exercised first. Phase 5 is the visible payoff and is best last among the
capability phases. Phase 6 is independent cleanup that can slot in any time
after its North-Star decisions land.

Each capability phase ships in the same shape: **a new verb/subcommand + a new
selftest component + ≥1 deity-benchmark question lifted FAIL→PASS + the audit
`deity_gap` note for its capability cleared.** That per-phase contract is the
deity-mode analogue of the godmode per-slice north-star gate.

---

## 5) Phase 0 — Deity measurement harness

**Goal:** build the numeric target before building capabilities, exactly as
the godmode build opened by building its benchmark. No deity capability is
"done" until a harness can score it.

### Tasks

1. **Author the deity benchmark.** `audit/debugger_deity_benchmark/questions.jsonl`,
   ~15–25 runtime questions seeded from real Cole asks + the five frontier
   areas. Every record: `{id, archetype: WHERE|WHY|WHAT, symptom,
   proof_mode: runtime, driver: auto, expected_answer: {source_anchors[],
   proof_command, evidence_standard, disproof_standard}, phase, severity}`.
   `driver: auto` is the deity discriminator — the proof must run with **no
   hand-supplied state/trace/scenario**.
2. **Build the scorer.** `tools/audit/check_debugger_deity_mode.py`: run each
   question through its `proof_command`, assert it ran `driver: auto` and
   matched the expected anchors/standard, emit per-question pass/fail +
   aggregate + the top line `deity_ready=<bool> deity_gap_actions=<n>`.
3. **Wire the selftest slots.** Add the seven component names from
   [§3](#3-how-deity-mode-is-measured) to `selftest.py` as `skipped/not-built`
   placeholders so the count target is explicit; each phase flips its slot to
   green.
4. **Record the baseline.** `audit/debugger_deity_benchmark/baseline_2026-05-29.md`
   — expected near-0% (almost everything FAIL; that is the start line).

### Acceptance criterion

`python tools/audit/check_debugger_deity_mode.py` runs, scores every deity
question (baseline ~0% PASS), and prints `deity_ready=False` with a non-zero
gap count; baseline committed. The God-tool triad is untouched and still
green.

---

## 6) Phase 1 — Auto-navigation / arbitrary-state synthesis (KEYSTONE)

**The single highest-value gap.** Today every runtime proof needs a
hand-supplied save state; `save-state-lab` only `inspect`s and `diff`s states
that already exist. Nothing in the tool can drive a fresh game to, e.g.,
"battle vs Morty, turn 3, enemy Gengar active." Until this exists, deity mode
is impossible — Phases 2, 3, and 5 all need to *reach a state on demand*.

**Closes (audit):** `causal_provenance` deepest gap ("automatic save-state
synthesis across every ROM surface") + `generation_fuzzing_counterexamples`
("arbitrary event-engine states still need dedicated dynamic ROM generators").

**Builds on (already on master):** `crossemu.py` (PyBoy backend), `replay.py`
(deterministic replay), `input_log.py` (input scripts), `runtime_state.py`
(read RAM at a frame), `state_space.py` (state targets), `runtime_watch.py`,
`save_state_lab.py` (the inspect/diff surface to extend).

### Tasks

1. **Define a target-state predicate language.** Reuse `tdb`'s predicate
   style so there is one query dialect across the tool. Targets look like
   `battle(boss=MORTY) and turn==3 and enemy_active=GENGAR`, or
   `map=ECRUTEAK_GYM and facing=UP`, or `party_has(species=TYPHLOSION,
   level>=30)`. Validate predicates against symbol/`content_mirror` knowledge
   so a typo'd species or unreachable clause fails at parse, not at frame
   100000.
2. **Build a committed checkpoint/waypoint library.** Named, reachable
   anchors stored as input-scripts (preferred — replayable, tiny, save-format
   neutral) or seed states: `new_game`, `post_elm`, each gym door, in-battle
   vs each boss, key event gates. Synthesis = "nearest checkpoint + short
   input script to the exact predicate," not "drive from boot every time."
   Store under `audit/debugger_checkpoints/` with a manifest per anchor.
3. **Write the navigator.** New `navigate.py` exposing
   `python -m tools.debugger navigate --to "<predicate>"`: pick the nearest
   checkpoint, search input space (scripted macros for menu/overworld/battle
   transitions, bounded BFS/greedy with `runtime_state` predicate checks each
   frame) to reach the predicate, emit a save state + manifest.
4. **Make synthesis honest (North-Star #4).** The manifest records checkpoint
   id + input script + frame count + RNG seed. `navigate --verify` replays the
   manifest from the checkpoint and asserts the same RAM signature. Fail
   closed with a precise "could not reach `<clause>`; nearest was `<state>`"
   when unreachable.
5. **Extend `save-state-lab` with a `synth` subcommand** so the keystone is
   reachable from the lab surface too: `save-state-lab synth --to "<predicate>"`
   → state + manifest, then `inspect` confirms the predicate holds.
6. **Cross-backend honesty (North-Star #5).** For any synthesized state that a
   later proof will treat as authoritative on a timing/graphics surface, run
   `crossemu` to confirm PyBoy and VBA-M agree on the reached RAM signature;
   record the backend in the manifest.

### Acceptance criterion

`python -m tools.debugger navigate --to "battle(boss=MORTY) and turn==3"`
emits a save state whose `save-state-lab inspect` confirms the predicate, with
a manifest that `navigate --verify` reproduces deterministically. A
deity-benchmark question previously blocked on a hand-supplied state (e.g.
"why does Morty's Gengar switch on turn 3?") now scores PASS with
`driver: auto`. New selftest component `auto_navigation` green (synth a small
known target from a checkpoint, verify the manifest round-trips, assert
fail-closed on a deliberately unreachable predicate).

---

## 7) Phase 2 — One-shot automatic instruction-level taint for any byte

The taint engine exists, but `tdb` requires a **pre-captured** effect-trace
report (`tdb "<query>" --report <report.json>`). The human still has to set up
the run, capture the window, and feed it in. Deity mode: name a byte and a
state, and the debugger does the rest.

**Closes (audit):** `causal_provenance` ("arbitrary-output taint needs
automatic save-state synthesis").

**Builds on:** Phase 1 (`navigate` to reach the state), `dynamic_taint.py`,
`taint.py`, `effect_trace.py`, `tdb.py`.

### Tasks

1. **Add a one-shot taint verb.** `python -m tools.debugger taint --byte
   $D141 --at "<predicate>"`: auto-`navigate` (Phase 1) to the state, install
   a watch on the byte, run forward until the write fires, auto-capture the
   trace window around it, run the taint engine, and return the
   instruction-level provenance (writer PC, bank, register lineage, source
   `path:line`).
2. **Auto-size the trace window.** Capture enough frames before the write to
   root the taint chain at a stable origin (a memory read, a table lookup, an
   input) without recording the whole battle. Start from the write and walk
   back until the chain hits a boundary `effect_trace`/`tdb` already
   recognizes.
3. **Reuse `tdb`'s predicate engine for the output side** so
   `taint --byte` and `tdb "writes(addr=$D141)"` share one query surface —
   the difference is only whether the report is auto-captured or supplied.
4. **Honesty + cross-backend.** The taint answer names the synthesized state's
   manifest and the backend; if the byte's write is timing-sensitive,
   cross-check the window on VBA-M (North-Star #5).

### Acceptance criterion

`python -m tools.debugger taint --byte <addr> --at "<predicate>"` returns a
complete instruction-level provenance chain for an *arbitrary* byte at an
*arbitrary* reachable state with **no hand-supplied `--report`**. A
deity-benchmark "why did byte X get value Y" question scores PASS with
`driver: auto`. New selftest component `auto_taint` green (one-shot taint of a
known damage byte reproduces the chain `tdb` produces from a hand-captured
report).

---

## 8) Phase 3 — Runtime behavioral replay for the static-only surfaces

Audio, graphics/UI, and the script VM are proven today by **static byte
mirrors** — `content_mirror/audio.py`, `visual_snapshot.py`,
`content_mirror/scripts.py` assert the ROM bytes match the disassembly's
prediction. That proves the *data is laid out as intended*; it does **not**
prove the surface *behaves* correctly when the engine runs it under arbitrary
event context. Deity mode replays the surface in the emulator and diffs
observed behavior against the mirror's prediction.

**Closes (audit):** `differential_mirrors` ("full script VM behavior under
arbitrary surrounding event-engine state, graphics/UI behavior, full audio
playback still need emulator-backed behavioral ROM mirrors") +
`generation_fuzzing_counterexamples` ("graphics/audio/UI semantic playback,
full script VM behavior under arbitrary event-engine context") + the replay
half of `whole_rom_replay_localization`.

**Builds on:** Phase 1 (`navigate` to the event context), `crossemu.py`,
`runtime_state.py`, and each surface's existing static mirror.

### Tasks (one replay harness per surface — independent, can parallelize)

1. **Audio replay** (`audio_replay`). Navigate to a context that triggers a
   sound/cry/track, step the emulator, capture the APU channel-register
   timeline (NR10–NR52), and diff the observed playback against
   `content_mirror/audio.py`'s prediction. Flag drift the static mirror can't
   see (wrong channel, wrong tempo, cut-off envelope).
2. **Graphics/UI replay** (`graphics_replay`). Navigate to a frame, render it
   in PyBoy *and* VBA-M (the divergence class lives here — North-Star #5),
   capture the framebuffer + VRAM/OAM, and diff against `visual_snapshot.py`.
   Reuse `vram-snapshot`/`vram-diff` for the structured VRAM comparison.
3. **Script-VM replay** (`script_vm_replay`). Navigate to an arbitrary
   event-engine state, step the script VM through a target script under that
   live context, and diff the observed command stream / branch decisions /
   memory effects against `content_mirror/scripts.py`'s static decode. This is
   the deepest of the three — the static mirror decodes the script bytes; the
   replay proves the VM *executes* them as decoded under real surrounding
   state.
4. **Unify under one verb family.** `python -m tools.debugger replay --surface
   {audio,graphics,script} --at "<predicate>"` so all three share the
   navigate→step→diff→render skeleton; the per-surface code is just the
   capture+diff adapter.

### Acceptance criterion

For each of the three surfaces, `replay --surface <s> --at "<predicate>"`
produces a runtime behavioral proof that **catches a synthetic regression the
static byte mirror alone misses** (the canonical test: perturb behavior
without changing the mirrored bytes — e.g. a timing/branch divergence — and
confirm replay flags it while the static mirror stays green). Three
deity-benchmark questions (one per surface) score PASS with `driver: auto`.
Selftest components `audio_replay`, `graphics_replay`, `script_vm_replay` all
green.

---

## 9) Phase 4 — Full SM83-model unification

The unification deliberately **dropped** the `sm83_model_parity` selftest
component (28/28, not 29/29) because a wholesale swap of the God branch's
`dynamic_taint` regressed master's taint findings (0 where master finds 1), so
master's taint engine was kept intact and the frame model grafted additively.
The two taint consumers (`dynamic_taint` and `effect_trace`) now work
independently on **separate SM83 models**. Deity-grade causal reasoning wants
**one** model behind both, so a taint claim and a trace claim are provably the
same machine — without re-introducing the regression that caused the drop.

**Closes (audit):** `causal_provenance` ("Boss AI provenance is branch/
probe-based; damage is trace/taint-based — they don't share a unified causal
substrate yet").

**Builds on:** `sm83_model.py`, `dynamic_taint.py`, `effect_trace.py`; the
parity assertion that was removed (re-add it as the gate).

### Tasks

1. **Characterize the regression first.** Before touching either engine,
   write a characterization test that pins master's *current* taint findings
   (the "1 finding" case the swap regressed to 0). This is the guardrail the
   whole phase is judged against — it must stay green throughout.
2. **Extract a single SM83 instruction model** that both `dynamic_taint` and
   `effect_trace` consume, by reconciling the two divergent models rather than
   replacing one with the other. Where they disagree on an instruction's
   register/flag effects, the disassembly + `docs/asm_authoring_guide.md` §1–2
   is the tiebreaker (SM83, *not* Z80 — no `IX/IY`, no shadow regs, etc.).
3. **Re-add the `sm83_model_parity` selftest component** asserting both
   consumers share the model and produce consistent per-instruction effects.
4. **Regression-gate the merge.** The Phase 0 characterization test and the
   full `dynamic_taint` test suite must stay green; if unification reintroduces
   the 0-findings regression, stop and reconcile per-instruction — do not ship
   a model that loses a finding to gain parity.

### Acceptance criterion

`python -m tools.debugger.selftest` reports the new full count **including
`sm83_model_parity` green**, AND master's taint findings are unchanged from
today (the characterization test from Task 1 still passes — the original
drop-reason regression does not recur). A deity-benchmark question that needs
a taint claim and a trace claim to agree on the same instruction semantics
scores PASS.

---

## 10) Phase 5 — Live emulator-coupled visualization

Today `visualization.py` emits **static** markdown/HTML reports. Deity mode's
visible face is a **live** view coupled to a running emulator: step the ROM
and watch registers, RAM, VRAM, and the heatmap update per frame.

**Closes (audit):** `visualization_reports` ("emulator-coupled TUI/canvas
inspectors remain subsystem-specific").

**Builds on:** `visualization.py`, `heatmap.py` (the existing static heatmap),
`crossemu.py`, `runtime_state.py`, `vram_snapshot.py`/`vram_decode.py`.

### Tasks

1. **Live TUI.** `python -m tools.debugger watch --live --at "<predicate>"`:
   navigate (Phase 1) to a start state, then a stepping TUI (curses) showing
   registers, watched RAM, current PC/bank with source `path:line`, and
   step/continue/breakpoint controls. This is `tdb`/`probe` made interactive.
2. **Live heatmap overlay.** Drive `heatmap.py`'s execution-frequency cells
   from a live run instead of a recorded trace, overlaid on the stepping view
   so hot code is visible as it runs.
3. **Live VRAM/framebuffer canvas.** Render the decoded VRAM/framebuffer
   (`vram-snapshot`/`vram-decode`) as a per-frame canvas next to the TUI, with
   the PyBoy↔VBA-M divergence shown side-by-side for graphics work (North-Star
   #5).
4. **Keep static reports as the artifact.** The live view is for
   investigation; a `--snapshot` flag still emits the committed static
   md/html so proofs remain reproducible and reviewable offline.

### Acceptance criterion

`python -m tools.debugger watch --live --at "<predicate>"` launches a stepping
TUI that advances the ROM frame-by-frame and renders live register/RAM/VRAM
state with source anchoring, plus the live heatmap overlay. A deity-benchmark
"show me X as it runs" question scores PASS. New selftest component
`live_view` green (headless: drive N frames, assert the per-frame state stream
matches `runtime_state` ground truth).

---

## 11) Phase 6 — Deferred-unification cleanup

Three items were deferred in the unification ([plan doc §Deferred](debugger_unification_plan.md));
they are folded in here because deity mode is the natural home to finish them.
Every module is **re-harvestable from `codex/cleanup-gsc-rebalance-split`**
(verified present there: `tools/debugger/causal_graph.py`,
`tools/debugger/hardware_event_stream.py`, `tools/debugger/rom_edit.py` +
`tools/debugger/tests/test_rom_edit.py`).

### 6a — `causal-graph` + `hardware-event-stream` verbs (low risk)

Harvested as libs during unification but **unexposed** — they render via a
`kind→formatter` dispatch with no self-contained `format_text`, so a clean
verb needs their text formatters ported into `formatters.py` (the modules were
removed from the tree to avoid orphans).

1. Re-harvest `causal_graph.py` + `hardware_event_stream.py` from the old
   branch.
2. Port their `kind→formatter` text rendering into `formatters.py` (or ship a
   JSON-only wrapper first if the text formatter is large).
3. Register `causal-graph` and `hardware-event-stream` verbs in
   `v2_passthrough.py`; port their tests.
4. **Acceptance:** both verbs run from the front door, emit text + JSON, pass
   their ported tests; selftest gains a component for each.

### 6b — `rom_edit` gate redesign (BLOCKED on a Cole decision — see §12)

Its original gate was "ROM edit requires a *mutual-verified* (two-LLM) handoff
phase." Single-owner needs a new gate, **and** `rom_edit` writes ROM source —
in direct tension with the read-only North Star.

1. **Get the North-Star decision** ([§12](#12-north-star-decisions-cole-owns))
   on whether the debugger may ever write ROM source.
2. If **read-only stays absolute** (recommended default): keep `rom_edit` as a
   **dry-run proposer only** — it emits a unified diff + the audit floor that
   diff must pass, but never applies it. The "gate" becomes "audits pass on
   the proposed diff," and application stays a human action.
3. If Cole sanctions guarded writes: redesign the gate as "full ASM
   verification floor green (`clobber_smoke`, farcall audits,
   `save_format_version`) + `make compare` review," re-harvest, and sandbox
   writes behind an explicit `--apply` that runs the floor first.
4. **Acceptance:** `rom_edit` runs under the chosen gate; in proposer mode it
   never mutates ROM source (a test asserts the working tree is unchanged
   after a dry run).

### 6c — `codex_*` benchmark question IDs (cosmetic, lowest priority)

16 of the 29 `codex_*` question IDs in `questions.jsonl`, the
`questions_codex_lane.jsonl` filename, and "Codex pair-review" note text remain
as historical provenance. The harness keys per-question scoring on the IDs, so
mass-renaming risks the 29/29.

1. Rename IDs + filename + note text in one commit.
2. Update the harness's ID references in lockstep.
3. **Acceptance:** the God-tool benchmark still scores **29/29** after the
   rename (this is the only guard that matters — the change is purely
   cosmetic). If parity can't be preserved cheaply, leave it as documented
   residual; it is not load-bearing.

---

## 12) North-Star decisions Cole owns

These are escalations per CLAUDE.md — decide before the dependent phase
starts, not mid-implementation.

1. **Does the debugger ever write ROM source? (Phase 6b)** Default and
   recommendation: **no — read-only stays absolute**, `rom_edit` ships as a
   dry-run proposer. Sanctioning guarded writes is a real expansion of the
   tool's authority and a taste/risk call only Cole makes.
2. **Are synthesized save states allowed as committed fixtures?** Phase 1
   produces states from input-script manifests (save-format neutral, the
   recommended form). If any phase wants to commit a *binary* synthesized save
   state, that touches the save format — an explicit Cole-escalation per
   CLAUDE.md's RAM rules.
3. **Is PyBoy-driven automation an acceptable proof backend, given Cole plays
   VBA-M?** This roadmap assumes **yes for navigation/capture, with VBA-M
   cross-check mandatory for timing/graphics-sensitive proofs** (North-Star
   #5). If Cole wants VBA-M as the *primary* driver, Phase 1's substrate
   choice changes (VBA-M scripting is heavier than PyBoy's) — confirm before
   building.
4. **Compute/time budget.** Auto-navigation + per-surface replay is heavy
   (BFS over input space, multi-backend runs). If a per-question proof must
   stay under a wall-clock budget, say so — it shapes the checkpoint-library
   density (Phase 1 Task 2) and whether replay caches are committed.

---

## 13) How to work from this doc

- This file is the **canonical contract** for the deity-mode workstream, the
  way [`debugger_unification_plan.md`](debugger_unification_plan.md) was for
  the unification. If scope shifts during the build, **update this file
  first, then act.**
- Tracked in [`docs/project_roadmap.md`](project_roadmap.md) as `DEBUGGER-002`
  (`PLANNED`). DEBUGGER-001 stays `COMPLETE` — deity mode is the *next tier*,
  not a reopening.
- Start a build session with `python -m tools.debugger session-start`, read
  this doc, then read the predecessor docs in the header.
- Per-phase commit message form (greppable): `debugger-deity: phase N
  <subject>`.
- The God-tool triad (`audit ready=True` 11/11, godmode benchmark 29/29,
  selftest current-count) is a **frozen floor** — never regress it to land a
  deity capability. Deity mode is strictly additive.

---

**End of roadmap.** Built but unbuilt: every phase here is a plan awaiting
Cole's review. Do not begin Phase 1 until that review lands.
