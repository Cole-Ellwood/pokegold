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
> **This began as a plan.** Cole has now approved starting implementation, so
> status notes below distinguish built slices from remaining roadmap work.
> Several phases still carry North-Star decisions that are Cole's to make (see
> [§12](#12-north-star-decisions-cole-owns)).

**Status:** implemented through the current deity benchmark gate. `python
tools/audit/check_debugger_deity_mode.py --timeout 90` now reports
`deity_ready=True`, 15/15 questions, pass_rate 1.000, and 7/7 deity components
built. Phase 6 remains optional cleanup gated by the North-Star decisions in
[§12](#12-north-star-decisions-cole-owns).
**Predecessor:** [`docs/debugger_godmode_spec.md`](debugger_godmode_spec.md)
(DEBUGGER-001, `COMPLETE`).
**Source of current truth:** `python -m tools.debugger session-start`,
[`docs/debugger_unification_plan.md`](debugger_unification_plan.md).
**Focused Boss AI slice:**
[`docs/boss_ai_debugger_deity_mode_roadmap.md`](boss_ai_debugger_deity_mode_roadmap.md)
defines the Boss-AI-only path to self-driving "why did the boss do that?"
proofs without pulling in audio, graphics, script VM, live-view, or generic
taint work.

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

### Per-phase detail standard

Every remaining phase must be detailed at the same level as the focused Boss AI
roadmap. A phase is not implementation-ready unless this document names:

1. The exact user question shape the phase answers.
2. The target schema accepted by the command or benchmark row.
3. The resolver order from user target to runtime input.
4. The artifact manifest fields the phase writes.
5. The proof-status vocabulary for complete, partial, unsupported, stale, and
   hash/backend-blocked states.
6. The benchmark rows that turn from FAIL to PASS.
7. The selftest component and its non-emulator or headless fixture.
8. The fail-closed diagnostics and next-action commands.
9. The strongest focused verification command for the phase.

If a later section only names a feature, treat it as underspecified and expand
this roadmap before coding.

---

## 5) Phase 0 — Deity measurement harness — ✅ DONE

**Goal:** build the numeric target before building capabilities, exactly as
the godmode build opened by building its benchmark. No deity capability is
"done" until a harness can score it.

### Tasks

1. **Author the deity benchmark.** ✅ `audit/debugger_deity_benchmark/questions.jsonl`
   — 8 runtime questions across the frontier (Phase 1 nav ×2, Phase 2 taint ×2,
   Phase 3 replay ×3, Phase 5 live view ×1). Every record:
   `{id, archetype, symptom, proof_mode: runtime, driver: auto, proof_command,
   evidence_marker, expected_answer: {source_anchors[], evidence_standard,
   disproof_standard}, phase, severity}`. `driver: auto` + `evidence_marker`
   are the deity discriminators — the proof must **run** to exit 0 and emit its
   marker, with **no hand-supplied state/trace/scenario**. (More questions get
   added as phases land; 8 is the seed, not the cap.)
2. **Build the scorer.** ✅ `tools/audit/check_debugger_deity_mode.py`: runs each
   `proof_command` as a subprocess; PASS only when `driver==auto` **and** exit 0
   **and** the `evidence_marker` is in stdout. Emits per-question pass/fail +
   the top line `deity_ready=<bool> deity_gap_actions=<n>`. `--baseline` records
   without failing; `--self-test` verifies the scorer's own logic with synthetic
   proofs (no ROM/emulator).
3. **Track the seven component slots — in the scorer, not `selftest.py`.** ✅ A
   deity component counts as **built** when a selftest component of the same
   name is registered (the selftest all-green gate guarantees a registered
   component works end-to-end). This is the key correction to the original plan:
   adding `not-built` placeholders to `selftest.py` would break the **28/28
   frozen floor** (`run_selftest` requires *all* components green). So the
   scorer reads `selftest.NAMED_CHECKS` and reports `components_built=N/7`;
   selftest gains each deity component only when its phase turns it green.
4. **Record the baseline.** ✅ `audit/debugger_deity_benchmark/baseline_2026-05-29.md`.

### Acceptance criterion — ✅ MET

`python tools/audit/check_debugger_deity_mode.py --self-test` PASSES (scorer
logic verified). The historical baseline printed
`deity_ready=False deity_gap_actions=15` (8 failed runtime proofs + 7 unbuilt
components, `pass_rate=0.000`) — the honest start line. The current closeout
run prints `deity_ready=True deity_gap_actions=0` with 15/15 questions and 7/7
components. The God-tool floor remains green: selftest is **35/35**, the
godmode benchmark is **29/29**, and `check_release_smoke.py` passes.

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

1. **Define a target-state predicate language.** ✅ **Done** —
   `tools/debugger/state_predicate.py` (`parse` / `evaluate`, 23 tests in
   `tests/test_state_predicate.py`). One query dialect for navigate/taint/
   replay/watch. Targets look like
   `battle(boss=MORTY) and turn==3 and enemy_active=GENGAR`, or
   `map=ECRUTEAK_GYM and facing=UP`, or `party_has(species=TYPHLOSION,
   level>=30)`. Unknown field/function/flag, bad operator, type mismatch, and
   stray `and` all fail **at parse** with a human-facing message — not at frame
   100000. (Vocabulary tables are curated + extensible; widen them as the
   navigator learns to observe more state.) `evaluate` treats an unobserved
   field as *not satisfied*, so it never claims a state it could not see.
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

**Status -- current deity benchmark slice complete.** The replay-to-checkpoint
half is built and proven for multiple reachable states; input-space search now
exists as a short-horizon, checkpoint-anchored PyBoy BFS that emits replayable
input logs. Long-horizon arbitrary-state synthesis remains out of scope unless
a future benchmark row names it and the compute budget is approved.

- Task 2 (checkpoint library): seeded with `audit/debugger_checkpoints/new_game`
  (`.input.log` + manifest) power-on → `PLAYERS_HOUSE_2F` (map `24:7`), and
  `audit/debugger_checkpoints/route29_first_wild` (chained input logs +
  manifest) power-on → Cyndaquil → Route 29 first wild battle (map `24:3`,
  `wBattleMode=1`), `audit/debugger_checkpoints/route46_south` (chained input
  logs + manifest) power-on → Route 29 first wild → deterministic RUN macro →
  Route 29/46 gate → Route 46 south entrance (map `5:9`, `x=7`, `y=33`), and
  `audit/debugger_checkpoints/route30_south` (chained input logs + manifest)
  power-on → Route 46 south → bounded-search route walk to Route 30 south
  (map `26:1`, `x=6`, `y=53`), `audit/debugger_checkpoints/mr_pokemon_after_oak`
  power-on → Mr. Pokemon's house → bounded script A-mash through Mr. Pokemon
  and Oak (map `26:10`, `x=3`, `y=6`, `script_mode=0`), and
  `audit/debugger_checkpoints/cherrygrove_rival_battle` power-on → post-Oak
  checkpoint → Cherrygrove rival scene → RIVAL1 trainer battle (map `26:3`,
  `x=33`, `y=7`, `wBattleMode=2`), and
  `audit/debugger_checkpoints/cherrygrove_post_rival` power-on → RIVAL1 battle
  → target-aware bounded A-button battle clear → idle Cherrygrove overworld
  (map `26:3`, `x=33`, `y=8`, `script_mode=0`), and
  `audit/debugger_checkpoints/elms_lab_post_officer` power-on → post-rival
  Cherrygrove → Route 29/New Bark → Elm's Lab → officer/name-rival scene
  cleared to idle lab control (map `24:5`, `x=4`, `y=3`, `script_mode=0`,
  `EVENT_GOT_MYSTERY_EGG_FROM_MR_POKEMON=true`,
  `EVENT_RIVAL_CHERRYGROVE_CITY=true`),
  and `audit/debugger_checkpoints/elms_lab_after_aide` power-on → post-officer
  lab → bounded facing-aware A-button interaction with Elm → Mystery Egg
  handoff plus aide Poke Ball handoff cleared to idle lab control (map `24:5`,
  `x=4`, `y=8`, `script_mode=0`, `EVENT_GAVE_MYSTERY_EGG_TO_ELM=true`).
  All pin input-log bytes; Route 29/46/30, post-Oak, rival-battle,
  post-rival, post-officer, and after-aide waypoints also pin frame count,
  PyBoy backend, zeroed in-memory SRAM plus locked zeroed RTC seed, party count,
  and RNG bytes.
- Task 3 (`navigate.py`): built as **auto-select nearest checkpoint + replay
  fixed inputs + evaluate the predicate each frame**, plus
  `navigate --search-to "<predicate>"` for bounded PyBoy BFS from a checkpoint.
  The searcher uses temporary PyBoy save-states only as queue nodes, currently
  expands overworld direction macros, can normalize wild battles with a
  deterministic RUN macro, can clear bounded map/text scripts with recorded
  A-button pulses, can clear simple trainer battles with target-aware bounded
  A-button pulses when the target is the post-battle state, and writes a plain
  text input-log extension. When a predicate names an event flag, the searcher
  also expands bounded A-button interaction actions and observes event bits
  from RAM; the state key includes facing and event bits so it cannot collapse a
  "same tile, wrong facing/event" false positive. That extension must be
  replayed from power-on and `navigate --verify` must match the RAM signature
  before it counts as proof.
  It reaches
  `map=PLAYERS_HOUSE_2F`, `wild_battle and map=ROUTE_29`, `map=ROUTE_46`, and
  `map=ROUTE_30`, plus
  `trainer_battle and trainer_class=RIVAL1`, and the post-rival idle
  Cherrygrove predicate (`map=CHERRYGROVE_CITY`, `x=33`, `y=8`,
  `script_mode=0`, `script_running=0`), plus the post-officer Elm's Lab idle
  predicate (`event=EVENT_GOT_MYSTERY_EGG_FROM_MR_POKEMON`,
  `event=EVENT_RIVAL_CHERRYGROVE_CITY`, `map=ELMS_LAB`, `x=4`, `y=3`,
  `script_mode=0`, `script_running=0`) and the after-aide event predicate
  (`event=EVENT_GAVE_MYSTERY_EGG_TO_ELM`, `map=ELMS_LAB`, `x=4`, `y=8`,
  `script_mode=0`, `script_running=0`), and
  `battle(boss=MORTY) and turn==3` via the manifest-pinned Morty boss AI seed
  plus replayed A-button pulses. The RAM observer now decodes map x/y,
  trainer-vs-wild battle mode, public `trainer_class`/`trainer_id` predicates,
  script mode/running state, boss class, player/enemy active species, player
  and enemy turn counters (predicate `turn` is the battle-turn max), facing,
  and named event flags. On current source, Morty's proof state is Haunter on
  enemy turn 3; the older "Gengar Hypnosis" wording is historical benchmark
  text, not the current party data.
- Task 4 (honest synthesis): `navigate --verify <run-manifest>` re-drives and
  re-asserts predicate + map + checkpoint-log sha + frame + RAM signature.
  Run manifests record checkpoint logs, total frames, reached frame, PyBoy
  backend, RNG bytes, and save-state path. Synthesized states are labeled as
  navigator runs. Local PyBoy navigation runs are serialized with a backend
  lock so overlapping CLI invocations cannot perturb replay validation.
- Task 5 (`save-state-lab synth`): built as a lab-surface wrapper over the
  same checkpoint-backed navigator:
  `python -m tools.debugger save-state-lab synth --to "<predicate>"`. It writes
  the navigator save-state + manifest, replay-verifies the manifest by default,
  labels the output as synthesized/PyBoy-backed, and fails closed when the
  predicate is outside the checkpoint library. Direct PyBoy `.state` decoding
  remains unsupported by `inspect`; predicate truth is confirmed by live RAM
  observation plus manifest replay.
- `auto_navigation` selftest component is **green** (pure-logic gate, no
  emulator); the end-to-end self-drive proofs are now
  `deity_nav_new_game_bedroom`, `deity_nav_first_wild_route29`,
  `deity_nav_route46_search_waypoint`, and
  `deity_nav_route30_search_waypoint`, plus
  `deity_nav_cherrygrove_rival_trainer_battle` and
  `deity_nav_cherrygrove_post_rival_battle` and
  `deity_nav_elms_lab_post_officer` and `deity_nav_elms_lab_after_aide` (all
  PASS). Task 6 (crossemu cross-check),
  deeper trainer/boss waypointing, and full input-space search remain. Latest
  score: `.local/tmp/debugger_deity_benchmark/results.json` from the current
  gate run (15/15 questions, 7/7 components, `deity_ready=True`).

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

### Phase 2 contract

User question shape:

- "Why did byte `$D141` become this value here?"
- "What instruction last wrote this RAM address at this reachable state?"
- "Which source rule/table/input does this output byte depend on?"
- "After this edit, did the write provenance for this byte change?"

Target schema:

- `byte`: absolute address, symbol name, or `bank:addr` pair.
- `at`: state predicate parsed by the Phase 1 predicate language.
- `stop`: `first_write`, `value_equals`, `value_changes`, or
  `after_instruction`.
- `window_policy`: `auto`, `fixed_frames`, or `until_boundary`.
- `max_frames`: hard budget before fail-closed.
- `backend`: `pyboy`, `vbam_check`, or `auto`.
- `expected_value`: optional, used only to verify the observed byte.
- `source_filter`: optional source path, symbol, or label filter for narrowed
  provenance.

Resolver order:

1. Parse the target and reject unknown byte/symbol/predicate fields up front.
2. Ask Phase 1 `navigate` for a verified manifest satisfying `at`.
3. Install a byte watch before advancing frames.
4. Stop at the configured write/value condition.
5. Capture the minimum trace window that reaches a recognized provenance
   boundary.
6. Run the shared taint query over the captured window.
7. Attach source anchors, byte value history, backend metadata, and the
   navigation manifest.

Artifact manifest fields:

- `kind`: `debugger_deity_auto_taint`.
- `target_byte`, `target_symbol`, `target_predicate`, and parsed target AST.
- `navigation_manifest`, checkpoint id, input-log hash, frame count, RNG seed,
  backend, and replay verification result.
- `watch_start_frame`, `write_frame`, `write_pc`, `write_bank`,
  `write_instruction`, and observed before/after values.
- `trace_window_start`, `trace_window_end`, trace hash, and window sizing
  reason.
- `taint_roots`, register lineage, memory-read lineage, source anchors, and
  disproof standard.
- `backend_cross_check`: not required, passed, failed, or unsupported, with
  reason.

Proof statuses:

- `explained`: reached predicate, observed write, taint chain rooted, source
  anchors emitted.
- `partial_window`: write observed, but the auto-sized window stopped before a
  stable root.
- `no_write_observed`: predicate reached but the byte was not written within
  `max_frames`.
- `blocked_by_navigation`: Phase 1 could not reach or verify the target state.
- `blocked_by_backend`: PyBoy/VBA-M setup or divergence prevents authoritative
  proof.
- `unsupported_byte`: target is outside mapped ROM/RAM/symbol ranges.
- `stale_trace_basis`: ROM/symbol hash does not match the manifest basis.

Seed deity rows to close:

- `deity_taint_known_damage_byte`: one-shot taint of a known damage/result byte
  from a checkpointed battle state.
- `deity_taint_textbox_control_byte`: provenance for a text/window control byte
  during an early-game script.
- `deity_taint_navigation_fail_closed`: unsupported deep predicate reports
  `blocked_by_navigation` with the exact next checkpoint/search action.
- `deity_taint_changed_source_delta`: compare a current taint packet with a
  previous run and report whether writer/source anchors changed.

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

Focused verification:

- `python -m tools.debugger taint --byte <known_symbol_or_addr> --at "<reachable_predicate>" --json-out <artifact>`
- `python tools/audit/check_debugger_deity_mode.py --baseline` with the Phase 2
  rows expected to pass and unrelated future rows allowed to remain red.
- `python -m tools.debugger.selftest --component auto_taint` once component
  filtering exists, otherwise the full selftest.

**Status -- current deity benchmark slice complete.** The one-shot taint
surface now self-navigates before capturing the write/provenance packet.
`python -m tools.debugger taint --byte wCurDamage --at
"battle(boss=FALKNER) and turn==1"` and the raw-address form for `$D141` at
`battle and turn==1` pass the deity gate without a hand-supplied report. The
answer includes the navigation manifest, observed byte target, source anchors,
taint root, and model source. Automatic instruction-window expansion beyond the
current benchmark write packet remains deeper work, not a blocker for the
15/15 deity gate.

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

### Phase 3 contract

User question shape:

- "What actually played on the audio channels when this event fired?"
- "What did the player see on this exact frame, and did PyBoy and VBA-M agree?"
- "Which script commands executed from this live event context?"
- "Did runtime behavior diverge from the static mirror even though ROM bytes
  still match?"

Common replay target schema:

- `surface`: `audio`, `graphics`, `script`, or `all`.
- `at`: Phase 1 state predicate.
- `trigger`: event, script label, map interaction, frame count, sound id, text
  id, menu action, or input macro.
- `duration`: frames, until idle, until script return, or until sound/channel
  silence.
- `backend`: `pyboy`, `vbam`, `crosscheck`, or `auto`.
- `mirror_expectation`: static mirror id or auto-discovered mirror record.
- `diff_mode`: `strict`, `semantic`, or `diagnostic`.

Common artifact manifest fields:

- `kind`: `debugger_deity_runtime_replay`.
- `surface`, target predicate, trigger, duration, backend, and replay command.
- `navigation_manifest`, input-log hash, frame count, RNG seed, and replay
  verification.
- `static_mirror_id`, mirror source anchor, mirror payload hash, and mirror
  prediction summary.
- `observed_timeline_hash`, structured timeline path, diff summary, and first
  divergent frame/command/channel when present.
- `cross_backend`: PyBoy result, VBA-M result, equivalence status, and
  divergence notes.
- `proof_status` and exact next-action command.

Surface-specific evidence:

- Audio: NR10-NR52 register timeline, channel enable/disable events, note/freq
  events where decodable, envelope/sweep changes, silence boundary, and the
  static audio mirror row.
- Graphics/UI: framebuffer hash, VRAM/OAM snapshots, tilemap/window/sprite
  decode, palette state, PyBoy/VBA-M image diff, and the first pixel/tile/OAM
  divergence.
- Script VM: script PC timeline, decoded command stream, branch decisions,
  memory effects, called script labels, return/idle boundary, and static script
  mirror decode.

Proof statuses:

- `replayed`: runtime behavior observed and matched the mirror or reported an
  intended diagnostic diff.
- `runtime_mirror_mismatch`: runtime behavior disagrees with static prediction.
- `backend_divergence`: PyBoy and VBA-M disagree on timing/graphics-sensitive
  evidence.
- `blocked_by_navigation`: target event context could not be reached.
- `blocked_by_trigger`: context reached, but requested sound/frame/script did
  not fire.
- `mirror_unmapped`: runtime event observed but no static mirror record maps to
  it.
- `unsupported_surface`: requested surface is not implemented by Phase 3 yet.

Seed deity rows to close:

- `deity_replay_audio_known_cry`: auto-reach a context that plays a known cry
  or sound effect and prove channel-register playback against the mirror.
- `deity_replay_graphics_first_menu_frame`: auto-reach a deterministic UI
  frame, capture framebuffer/VRAM/OAM, and cross-check PyBoy/VBA-M.
- `deity_replay_script_mr_pokemon_handoff`: auto-reach an early script event
  and prove observed script commands/branches against the static decode.
- `deity_replay_static_mirror_regression_fixture`: synthetic test where static
  bytes match but runtime behavior diverges and replay reports the mismatch.

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

Focused verification:

- `python -m tools.debugger replay --surface audio --at "<reachable_predicate>" --json-out <artifact>`
- `python -m tools.debugger replay --surface graphics --at "<reachable_predicate>" --json-out <artifact>`
- `python -m tools.debugger replay --surface script --at "<reachable_predicate>" --json-out <artifact>`
- `python tools/audit/check_debugger_deity_mode.py --baseline` with the Phase 3
  rows expected to pass.
- `python -m tools.debugger.selftest` with `audio_replay`, `graphics_replay`,
  and `script_vm_replay` registered only after they are green.

**Status -- current deity benchmark slice complete.** `replay --surface audio`
for `cry(species=TYPHLOSION)` auto-reaches a clean PyBoy context, enters the ROM
`PlayCry` routine, decodes the matching cry channel block from
`audio/cries.asm`, and captures an APU register timeline. `replay --surface
graphics --at "map=ECRUTEAK_GYM"` auto-selects the Morty/Ecruteak checkpoint
and writes framebuffer, VRAM, OAM, LCD-register, and digest evidence.
`replay --surface script --at "map=ELMS_LAB and script=ProfElmScript"` reaches
Elm's Lab, decodes `ProfElmScript`, initializes the script runner fields, and
captures the script VM pointer stream. These are PyBoy runtime proofs against
static mirror/source anchors; PyBoy/VBA-M pixel parity and richer
branch-by-branch attribution remain North-Star extensions.

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

### Phase 4 contract

User question shape:

- "Do taint and effect-trace agree on this instruction's register/memory
  effects?"
- "Did an instruction model change alter debugger provenance?"
- "Which SM83 opcode semantic difference explains this taint/trace mismatch?"

Model inventory schema:

- `opcode`: byte value and prefixed/unprefixed namespace.
- `mnemonic`: normalized SM83 mnemonic.
- `operands`: normalized operand kinds.
- `reads`: registers, flags, memory, immediate bytes, and implicit reads.
- `writes`: registers, flags, memory, stack, PC, SP, and interrupt state.
- `cycles`: cycle alternatives and branch conditions where modeled.
- `taint_semantics`: source-to-destination propagation rules.
- `trace_semantics`: effect-trace event emission rules.
- `coverage`: unit, fixture, live trace, and parity evidence ids.

Shared model API requirements:

- One instruction decoder used by both consumers.
- One side-effect description object for register, flag, memory, PC/SP, stack,
  and cycle effects.
- Separate adapters for taint propagation and effect-trace event emission, so
  model sharing does not force both tools to emit the same output shape.
- A compatibility shim only where old output formatting requires it; no forked
  semantic copy.

Artifact manifest fields:

- `kind`: `debugger_deity_sm83_parity`.
- model version, opcode table hash, source file anchors, and test fixture id.
- dynamic-taint output digest and effect-trace output digest.
- per-instruction parity result and first semantic mismatch.
- regression fixture result for the historical 1-finding case.
- list of opcodes with only static coverage and no live trace exercise.

Proof statuses:

- `parity_proven`: both consumers share the model and agree on the fixture.
- `model_mismatch`: consumers diverge for an opcode or side effect.
- `coverage_partial`: shared model exists but one or more opcodes lack live or
  fixture evidence.
- `regression_detected`: the historical taint finding count regressed.
- `adapter_only`: outputs differ only in formatting; semantic digest matches.

Seed deity rows to close:

- `deity_sm83_known_taint_trace_parity`: a trace/taint fixture that exercises
  load, arithmetic, branch, and memory-write effects.
- `deity_sm83_historical_regression_guard`: the specific old 1-finding case
  remains one finding after unification.
- `deity_sm83_opcode_coverage_report`: benchmark row proving no unsupported
  opcode is used by current deity proof traces.

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

Focused verification:

- `python -m unittest tools.debugger.tests.test_sm83_model`
- `python -m unittest tools.debugger.tests.test_dynamic_taint`
- `python -m unittest tools.debugger.tests.test_effect_trace`
- `python -m tools.debugger.selftest`
- `python tools/audit/check_debugger_deity_mode.py --baseline` with Phase 4
  rows expected to pass.

**Status -- current deity benchmark slice complete.** `dynamic_taint` and
`effect_trace` both report the shared `tools.debugger.sm83_model` model source,
and the selftest/godmode/deity gates confirm the old dropped-component taint
regression did not return. The current proof traces agree on one model boundary;
exhaustive SM83 opcode/f flag coverage is still future parity work rather than
a current deity-gate blocker.

---

## 10) Phase 5 — Live emulator-coupled visualization

Today `visualization.py` emits **static** markdown/HTML reports. Deity mode's
visible face is a **live** view coupled to a running emulator: step the ROM
and watch registers, RAM, VRAM, and the heatmap update per frame.

**Closes (audit):** `visualization_reports` ("emulator-coupled TUI/canvas
inspectors remain subsystem-specific").

**Builds on:** `visualization.py`, `heatmap.py` (the existing static heatmap),
`crossemu.py`, `runtime_state.py`, `vram_snapshot.py`/`vram_decode.py`.

### Phase 5 contract

User question shape:

- "Show me this bug as it runs."
- "Step this reachable state and show registers/RAM/source side by side."
- "Show the live VRAM/framebuffer and hot code path during this event."
- "Capture a reproducible static packet from the live investigation."

Target schema:

- `at`: Phase 1 state predicate or manifest path.
- `watch`: symbols, addresses, source labels, VRAM ranges, OAM ranges, or
  register groups.
- `breakpoint`: PC, source label, write/read address, predicate, or frame.
- `view`: `tui`, `canvas`, `json_stream`, or `snapshot`.
- `backend`: `pyboy`, `crosscheck`, or `auto`.
- `step_mode`: frame, instruction, until breakpoint, until idle, or until
  predicate.
- `snapshot`: optional path for a static report artifact.

Runtime stream fields:

- frame number, backend, PC/bank, source anchor, registers, flags, SP, selected
  RAM watches, and predicate truth.
- heatmap deltas for executed source ranges.
- VRAM/OAM/framebuffer hashes and decoded UI state where requested.
- input events and breakpoint hits.
- provenance links back to the navigation manifest and any taint/replay packet
  launched from the live view.

Proof statuses:

- `live_stream_started`: target reached and state stream is updating.
- `snapshot_written`: static reproducible artifact emitted from the live run.
- `blocked_by_headless_backend`: interactive view unavailable, but
  `json_stream`/headless mode may still run.
- `blocked_by_navigation`: target state could not be reached.
- `watch_unmapped`: requested symbol/address/source anchor is not mapped.
- `backend_divergence`: cross-backend stream diverges on a checked surface.

Seed deity rows to close:

- `deity_live_view_headless_stream`: headless live stream from a reachable
  checkpoint produces N frames matching `runtime_state`.
- `deity_live_view_breakpoint_snapshot`: live run hits a source or memory
  breakpoint and writes a static snapshot artifact.
- `deity_live_view_vram_frame_digest`: graphics-enabled stream emits VRAM/OAM
  and framebuffer digests tied to source/frame metadata.

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

Focused verification:

- `python -m tools.debugger watch --live --headless --at "<reachable_predicate>" --frames 60 --json-out <artifact>`
- `python -m tools.debugger watch --live --headless --at "<reachable_predicate>" --breakpoint <symbol_or_addr> --snapshot <artifact>`
- `python -m tools.debugger.selftest`
- `python tools/audit/check_debugger_deity_mode.py --baseline` with Phase 5
  rows expected to pass.

**Status -- current deity benchmark slice complete.** `watch --live --headless
--frames 4 --at "battle(boss=FALKNER) and turn==1"` auto-navigates to the
battle state and emits a per-frame runtime state stream for the benchmark and
selftest. The interactive TUI/canvas, breakpoint snapshot UX, and live heatmap
overlay remain presentation work; the headless stream is the verified proof
surface for the current deity gate.

---

## 11) Phase 6 — Deferred-unification cleanup

Three items were deferred in the unification ([plan doc §Deferred](debugger_unification_plan.md));
they are folded in here because deity mode is the natural home to finish them.
Every module is **re-harvestable from `codex/cleanup-gsc-rebalance-split`**
(verified present there: `tools/debugger/causal_graph.py`,
`tools/debugger/hardware_event_stream.py`, `tools/debugger/rom_edit.py` +
`tools/debugger/tests/test_rom_edit.py`).

### Phase 6 contract

This phase is cleanup, but it still needs a deity-grade contract because it can
otherwise blur into vague "nice to have" work.

Shared requirements:

- Every restored verb must be reachable through the unified debugger front
  door.
- Every restored verb must emit machine-readable JSON plus a deterministic text
  form or explicitly document why JSON-only is the first landing step.
- Every restored verb must have a selftest component or be excluded with a
  named reason.
- No restored verb may weaken the read-only North Star. `rom_edit` is dry-run
  only unless Cole explicitly approves guarded source writes.
- The God-tool benchmark remains 29/29 after cosmetic ID changes.

Shared artifact fields:

- `kind`, verb name, source branch/commit harvested from, formatter version,
  input target, output digest, source anchors, and verification command.
- for proposer-style outputs, `working_tree_mutated=false` unless explicit
  guarded apply mode is approved and used.
- for renamed benchmark ids, old id, new id, compatibility alias if any, and
  benchmark result before/after rename.

### 6a — `causal-graph` + `hardware-event-stream` verbs (low risk)

Harvested as libs during unification but **unexposed** — they render via a
`kind→formatter` dispatch with no self-contained `format_text`, so a clean
verb needs their text formatters ported into `formatters.py` (the modules were
removed from the tree to avoid orphans).

Detailed contract:

- `causal-graph` answers "what runtime observations caused this state/output?"
  by rendering nodes for source anchors, instructions, memory reads/writes,
  inputs, and derived values.
- `hardware-event-stream` answers "what hardware-facing events occurred over
  this runtime window?" by rendering ordered events for memory-mapped IO,
  interrupts, DMA/OAM/VRAM-relevant events, timers, and frame boundaries where
  supported.
- Both verbs accept either an auto-captured manifest from Phases 1/2/3/5 or an
  existing replay/trace artifact.
- Both fail closed when the artifact lacks enough timing or source metadata,
  returning `needs_trace_window`, `needs_backend_metadata`, or
  `unsupported_event_kind`.

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

Detailed contract:

- Default mode is `rom-edit propose`: output a unified diff, rationale, source
  anchors, expected audits, and disproof standard.
- `propose` must assert the working tree is unchanged before and after the run.
- If guarded writes are ever approved, `--apply` must require a clean explicit
  confirmation flag, run the configured audit floor first, write only the
  requested source files, and record the exact diff hash and verification
  result.
- Proof statuses are `proposal_written`, `blocked_by_read_only_policy`,
  `blocked_by_dirty_scope`, `blocked_by_audit_floor`, `applied_with_guard`, and
  `unsupported_patch`.
- No deity benchmark row may require source mutation to pass.

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

Detailed contract:

- Maintain an id migration table with old id, new id, archetype, phase, and
  reason.
- Update every harness reference in the same patch as the data rename.
- Keep historical provenance in a note field if useful; do not leave command or
  filename references stale.
- Run the godmode benchmark before and after the rename and store the before
  score in the handoff artifact.
- If any compatibility alias is needed, make it explicit and temporary.

1. Rename IDs + filename + note text in one commit.
2. Update the harness's ID references in lockstep.
3. **Acceptance:** the God-tool benchmark still scores **29/29** after the
   rename (this is the only guard that matters — the change is purely
   cosmetic). If parity can't be preserved cheaply, leave it as documented
   residual; it is not load-bearing.

Focused verification for Phase 6:

- `python -m tools.debugger causal-graph --help`
- `python -m tools.debugger hardware-event-stream --help`
- `python -m tools.debugger rom-edit --dry-run ...` or the final approved
  proposer command shape.
- `python tools/audit/check_debugger_godmode_benchmark.py`
- `python -m tools.debugger.selftest`
- `python tools/audit/check_debugger_deity_mode.py --baseline`

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
  (`COMPLETE` for the current deity benchmark gate). DEBUGGER-001 stays
  `COMPLETE` — deity mode is the *next tier*, not a reopening.
- Start a build session with `python -m tools.debugger session-start`, read
  this doc, then read the predecessor docs in the header.
- Per-phase commit message form (greppable): `debugger-deity: phase N
  <subject>`.
- The God-tool triad (`audit ready=True` 11/11, godmode benchmark 29/29,
  selftest current-count) is a **frozen floor** — never regress it to land a
  deity capability. Deity mode is strictly additive.

---

## 14) Effort, payoff, and where to stop (judgment — Cole's call)

Not all six phases are equally worth building. Listing them is not endorsing
them. This is the honest effort-vs-payoff read so the scope is a *decision*,
not a default. (Effort/payoff/risk are judgment, not measured; the ceiling per
phase is the most that phase can truthfully deliver given [§1's limits](#1-the-tier-line-what-deity-mode-means).)

| Phase | Effort | Payoff to the daily job | Risk of under-delivering | Honest ceiling |
|---|---|---|---|---|
| 0 Harness | S | enabling (can't measure progress without it) | low | a scorecard, not a capability |
| 1 Auto-nav | **L** | **high — keystone, unblocks 2/3/5** | **med–high** (input search is exponential) | short-horizon, checkpoint-anchored nav; *not* arbitrary deep states |
| 2 Auto-taint | M | **high — "why did this byte get this value" is the daily question** | low–med (engine exists; risk is window auto-sizing) | one byte, one reachable state, per run |
| 3 Runtime replay | L (×3 surfaces) | med — audio/graphics/script-VM bugs are rarer here than damage/AI | med (script-VM stepping + PyBoy↔VBA divergence) | behavioral diff vs the static mirror, on an emulation |
| 4 SM83 unify | M | low–med — internal coherence, no new user capability | med (could re-trigger the dropped-component regression) | one model behind both taint consumers |
| 5 Live viz | M–L | med — QoL; the static reports already work | low | a live TUI/canvas; not a new proof |
| 6 Cleanup | S | low — cosmetic + the `rom_edit` decision | low | provenance tidy + a gated proposer |

**Recommended cut line:**

- **Must-build for the "self-driving proof" promise — Phase 0 + 1 + 2.** Measure,
  navigate, one-shot taint. If only these land, the debugger genuinely drives
  its own runtime proofs for the surfaces that already matter most (damage,
  Boss AI, any byte) — which is the bulk of the "95%."
- **Build only if that surface actually bites — Phase 3.** And then only the
  *one* sub-surface (audio / graphics / script-VM) that is producing real bugs;
  don't build all three on spec.
- **Optional polish — Phases 4, 5, 6.** Coherence, a nicer view, and tidy-up.
  Real, but none of them removes a manual step from a typical investigation.
- **If you do nothing else: Phase 0 + Phase 1.** Auto-navigation alone deletes
  the single biggest manual step — hand-building a save state — from *every*
  runtime investigation. Everything past it is leverage on that one win.

The diminishing returns are real and intentional to surface: the curve is steep
through Phase 2 and flattens after. The current benchmark chose narrow,
proof-backed slices of Phases 3–5 as well; deeper Phase 3–6 ambitions should
still wait for a concrete question, budget, or North-Star decision rather than
expanding by checklist.

---

**End of roadmap.** The current deity benchmark gate is implemented and green:
15/15 questions, 7/7 components, `deity_ready=True`, selftest 35/35, godmode
benchmark 29/29, and release smoke passing. This is a self-driving proof
debugger for the implemented benchmark surfaces, not a claim of literal
arbitrary-state omniscience; Phase 6 cleanup and the North-Star extensions in
§12 remain decision-gated future work.
Continue milestone by milestone; do not claim arbitrary-state synthesis until
the navigator can search beyond committed replay checkpoints.
