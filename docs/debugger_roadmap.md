# Pokemon Gold Hack — Bespoke Debugger Roadmap

Status: planning document, created 2026-05-16. This is the project-wide
implementation plan for a state-of-the-art debugger tailored to *this*
ROM hack — the Boss AI overlay, late-gen held items, type-passive
mods, custom save format, banked battle engine, all of it.

This roadmap is intentionally maximalist. The user's request was
"literally any feature that would help debug the code." Every plausible
capability is captured here, then phased so we can actually ship.

> "A debugger is just a tool for asking the right question to the
> running system. The job is to make as many questions answerable, and
> as many answers trustworthy, as we can." — north star for this work.

## 0. TL;DR

We already have two mature debug subsystems in this repo:

- [`tools/damage_debugger/`](../tools/damage_debugger/) — battle-engine
  step tracer, oracle, Hypothesis fuzz, byte-level taint, snapshot
  replay, coverage, Tenet writer, ddmin minimizer.
- [`tools/boss_ai_debugger/`](../tools/boss_ai_debugger/) — fixture
  inspection, ROM contribution traces, rule maps, generators,
  metamorphic relations, mutation testing, invariant mining,
  counterfactuals, materialization, review queue.

Plus [`tools/trace/`](../tools/trace/), [`tools/audit/`](../tools/audit/),
[`tools/boss_ai_preference/`](../tools/boss_ai_preference/),
[`tools/pokemon_mastery/`](../tools/pokemon_mastery/).

The plan: unify these under one consistent **debugger kernel**
(emulator pool + symbol/source service + event bus + state store),
adopt a single **event schema** (OpenTelemetry-shaped span tree), add a
**source-level debugger frontend** (DAP-compatible so it lives inside
VS Code), and round out coverage with the genuinely new capabilities
this hack still lacks:

1. **Cross-emulator differential** (PyBoy ↔ SameBoy ↔ BGB ↔ gambatte),
2. **Time-travel / omniscient queries** (interval-tree-backed byte
   history),
3. **Source-level debug with `farcall` cross-bank stack reconstruction**,
4. **Whole-ROM static analyzer** (register-clobber inference, save-format
   drift, free-space bank tracking, cross-bank-call audit, stack-depth
   bounds),
5. **Symbolic / abstract execution** for tiny functions (path-bounded
   model checking),
6. **Live battle visualizer + AI decision explorer** (web UI),
7. **Graphics/Overworld/Audio scopes** (VRAM/OAM/script/music tracers),
8. **Save-state lab** (VBA `.sgm` ↔ PyBoy interop, save diff, format
   migration scaffolding),
9. **LLM-assisted hypothesis tracker** (Claude in the loop, with
   citations and verification),
10. **Differential against vanilla pokegold** for parity-preserving
    changes.

Implementation phases are P0–P12 spread over an estimated 6–10 weeks of
focused work, gated by user approval at each phase boundary. The plan
absorbs and extends the [Boss AI Debugger SOTA
plan](boss_ai_debugger_state_of_art_implementation_plan_2026-05-15.md);
that plan stays the canonical reference for Boss-AI-specific phases.

## 1. Vision & First-Playthrough Promise Alignment

The hack's [North Star](project_context.md) is **restored uncertainty
for a veteran player** — bosses that win without cheating, weak
Pokemon that surprise, QoL that removes tedium and not decisions.

A debugger is not just a programmer's tool. For *this* hack it must
also be a **design-correctness instrument**:

- Boss AI must reason from public information only (except authored
  Haki). Hidden-info leak detection is a *design* requirement, not a
  bug class.
- "Difficulty from smarter opponents" requires us to *prove*
  the opponent is smart: decision traces must be explainable to a
  human, not just verifiable against a Python mirror.
- Stat changes propagate into damage chains, AI scoring, and
  trainer-roster pressure. The debugger must let us follow that
  propagation end-to-end without losing trust.
- Save format breakage = silent corruption for every existing player
  save. Every change to `ram/` needs a debugger-visible diff.

**Therefore**: every debugger capability in this plan must, somewhere,
answer the question *"is this change still serving the
first-playthrough promise?"* — and the user (gameplay-design lead) must
be able to read its output without learning asm.

That guides the UX: terse player-facing reports, not raw memory dumps.
Engineering panels exist but are not the default. Decision waterfalls
explain Boss AI in English. Damage chain diagrams show the player view
("Crobat's Wing Attack does 38–46 (24–28%) — Sharp Beak +Stab boosts
the multiplier from x1.0 → x1.2") before they show the asm.

## 2. Current State (May 2026)

This section is a snapshot of what's *built*, so the rest of the doc
can be honest about what's *new* vs *evolved*.

### 2.1 `tools/damage_debugger/`

Battle-engine focused. Documented at
[damage_debugger/README.md](../tools/damage_debugger/README.md).
Highlights:

- **Step tracer** (`tracer.py`) — PC trace over a single function, with
  HRAM-sentinel return trap (`safe_call.py`), no PyBoy modifications.
- **Symbol service** (`symbols.py`) — forward/reverse `.sym` parser,
  renders `Label+0xNN`.
- **Oracle** (`oracle.py`) — Python damage formula reference. Models
  DamageStats, DamageCalc, Stab, TypeMatchup, TypePassive,
  DamageVariation, after-hit effects, weather, badge boosts, type-boost
  items, late-gen item multipliers, Metronome counter, SolarBeam-in-rain.
- **Clobber smoke** (`clobber_smoke.py`) — multi-scenario regression
  harness against `wCurDamage` ranges + HP post-checks. The §6
  verification floor entry point.
- **Hypothesis fuzz** (`fuzz.py`) — generative ROM-vs-oracle, with
  multiprocessing (`--workers N`), per-worker PyBoy boot cache,
  deterministic seeds.
- **Find** (`find.py`) — bucket-locates ROM-vs-oracle divergence across
  DamageStats / DamageCalc / Stab / TypeMatchup / TypePassive, plus
  reusable hook instrumentation (`--instrument-hook <symbol>`).
- **Cap-add probe** (`cap_add_probe.py`) — DamageCalc nonzero-`wCurDamage`
  accumulation classifier; the M1 endian bug repro.
- **Taint** (`taint.py`) — SM83 byte-level taint tracker over tracer
  frames. Register + memory + stack + ALU propagation, sink reporting.
- **Coverage** (`coverage.py`) — per-PC smoke-scenario coverage report.
- **Tenet writer** (`tenet_writer.py`) — adapts tracer frames into
  [Markus Gaasedelen's Tenet](https://github.com/gaasedelen/tenet)
  delta-line syntax (JSONL + raw `.tenet`).
- **Snapshot replay** (`replay.py`) — bounded save-state ring,
  watch-symbol change detection, rewind + reverify.
- **Boot cache** (`boot_cache.py`) — fast PyBoy startup, used by every
  scenario.
- **Pre-commit hook** (`precommit_check.py`) — wired into
  `.claude/settings.json` `PreToolUse` for `git commit` of damage-chain
  ABI files.
- **Balance heatmap** (`tools/audit/balance_diff.py`) — oracle-backed
  damage delta heatmap across learned moves and modifier variants.

### 2.2 `tools/boss_ai_debugger/`

Boss-AI focused. Documented at
[boss_ai_debugger/README.md](../tools/boss_ai_debugger/README.md) and
the [SOTA implementation
plan](boss_ai_debugger_state_of_art_implementation_plan_2026-05-15.md).
Highlights:

- **Fixture inspect** — load BOSSAI-004 fixtures, render full state.
- **Pairwise preference regression** — strict labels vs Python scorer.
- **ROM contribution trace** — PyBoy execution hooks on trace-ROM AI
  source labels, captures rule deltas and selector entry scores.
- **Score & selector materialization** — patch generated scenarios into
  WRAM before scoring, then drive the ROM selector. Fast-score mode
  shards across workers.
- **Rule map** — semantic IDs for asm labels (stable across line
  shifts).
- **Generators** — `boundary_matrix`, `coverage_guided`,
  `stateful_public_info`, `mastery_replay`, `live_trace_mutator`,
  `leader_personality`.
- **Coverage** — rule-id, branch predicate, source label, public-info,
  leader/tier, mastery card, generator, mutation-kill.
- **Metamorphic** — hidden-info leak detection, public-only invariants.
- **Mutation** — Python scorer mutants, kill-rate report.
- **Invariant mining** — Daikon-style candidate invariants from passing
  traces.
- **Counterfactuals + minimize + localize** — smallest answer-flipping
  change, ddmin, statistical localization.
- **Review queue** — top-N reviewable mismatches with mastery digest.
- **Route eval** — 2–5 turn route classification.
- **Run store** — `audit/boss_ai_debugger/runs/`, JSON metadata,
  artifact hashes, run-vs-run diff.

### 2.3 Supporting

- [`tools/trace/`](../tools/trace/) — PyBoy state factory (all 16
  leaders + Koga + Lance), trace batch capture, state probe, replay
  plumbing.
- [`tools/audit/`](../tools/audit/) — 40+ static audit scripts.
  Release-smoke floor: `check_release_smoke.py`,
  `check_navigation_floor.py`, `check_farcall_a_clobber.py`,
  `check_farcall_hl_clobber.py`, `check_cross_bank_call.py`,
  `check_typepassive_c_mirror.py`, `check_save_format_version.py`, etc.
- [`tools/boss_ai_preference/`](../tools/boss_ai_preference/) —
  preference labels, threat availability report, web UI for human
  judgment.
- [`tools/pokemon_mastery/`](../tools/pokemon_mastery/) — case library,
  compounding-loop infrastructure, replay corpus.

### 2.4 What's already pretty good

- Deterministic scenario harness via WRAM seed + PC injection.
- Cross-process Hypothesis fuzz with worker-isolated boot caches.
- ROM-vs-Python differential with run-store + diff.
- Selector replay at >99.99% on real-script trace captures.
- Per-PC coverage with markdown report.
- Static audit floor that catches several specific bug classes
  (farcall clobbers, cross-bank calls, save format drift, c-mirror
  invariant).
- Pre-commit gate wired through Claude's `PreToolUse`.

### 2.5 What's still missing

(This is the heart of the roadmap — see §4 for full feature catalog.)

- No source-level debugger. We trace and dump, we don't *step*.
- No time-travel / reverse execution at the byte level. The snapshot
  ring is per-call, not omniscient.
- No cross-emulator differential. Single PyBoy. Emulator-specific
  bugs (May 2026 VBA tile jumble class) are debugged ad-hoc.
- No first-class graphics / overworld / audio scope. Battle-only.
- No live battle visualizer. We dump `wCurDamage`, the user reads
  hex.
- No formal static analyzer for register-clobber inference,
  bank-pressure bounds, or stack-depth bounds. We have point audits;
  there's no project-wide static model.
- No symbolic / abstract execution. SM83 has small functions and is a
  perfect fit; nobody's pointed angr or KLEE-style search at it.
- No save-state diff lab. We can't ask "what changed in WRAM between
  these two `.sgm` files."
- No DAP/VS Code integration. Debugging happens in PowerShell.
- No LLM-assisted hypothesis tracker. We already debug *with* Claude,
  but informally — no persisted hypothesis tree.
- No differential against vanilla pokegold for parity-preserving
  changes. We trust SHA1 match; we don't prove "unchanged subsystem
  still behaves like vanilla."
- No first-class link-cable / trade-flow debug (less critical for
  single-player hack but cheap to add when the rest is unified).

The rest of this doc plans those gaps.

## 3. Survey: State of the Art

This section consolidates external research on debugger design,
gathered with web search and primary-source inspection. Each
subsection notes what we'll **adopt** vs **adapt** vs **skip**.

### 3.1 Game Boy / Game Boy Color emulators with debug surfaces

(Full agent research deferred to §10 Bibliography; summary below.)

- **[BGB](https://bgb.bircd.org/)** — long-time gold standard for GB
  debugging. Memory viewer, VRAM viewer, breakpoints (PC, IO, read,
  write), conditional breakpoints, expression evaluator, scriptable
  via integrated trace logger. Windows-only, closed source, but the
  feature list is the spec for "GB debugger UX." **Adopt** its
  breakpoint taxonomy (PC / IO / read / write / VBlank / interrupt,
  with conditions).
- **[SameBoy](https://sameboy.github.io/)** — modern, cycle-accurate,
  scriptable via a Lisp-like REPL. Macros & user-defined commands.
  Open source (MIT). Headless mode + libretro core. **Adopt** SameBoy
  as a *second* emulator backend behind PyBoy for cross-emu diff
  (§4.3.2) and for cycle-accurate verification.
- **[Emulicious](https://emulicious.net/)** — Java, ships a
  [Debug Adapter Protocol](https://microsoft.github.io/debug-adapter-protocol/)
  server so VS Code can attach. Full source-level stepping with
  RGBDS `.sym`. **Adopt** Emulicious-style DAP as our IDE story
  (§4.6.1).
- **[mGBA](https://mgba.io/)** — primarily GBA but has GB/GBC support;
  ships Lua scripting and a feature-rich GUI debugger. **Skip** as
  backend (we don't need GBA), but **adopt** Lua scripting hook idiom
  for our UI plugin layer if we go that direction.
- **[Mesen2](https://www.mesen.ca/)** — multi-system; GB support
  recently added; Lua scripting, event viewer (pixel-by-pixel
  rendering trace), tile/sprite/PPU viewers. **Adopt** the
  event-viewer concept (frame-level pixel-by-pixel tile decode) for
  the May 2026 VBA tile jumble class.
- **[PyBoy](https://github.com/Baekalfen/PyBoy)** — Python emulator.
  Our existing backend. Strengths: scriptable, headless, fast enough
  for fuzz. Weaknesses: not cycle-accurate, missing some quirks. **Keep
  as primary** + harden the cross-emu diff so PyBoy-only quirks don't
  bite us.
- **[gambatte](https://github.com/sinamas/gambatte)** — accuracy
  reference. **Adopt** as cross-emu diff backend for cycle-accuracy
  questions.
- **[NO$GMB / no$gba](http://problemkaputt.de/gmb.htm)** — original
  GB debugger. Largely superseded. **Skip**.
- **[Visual Boy Advance / VBA-M](https://vba-m.com/)** — what
  players use; what produces the `.sgm` save states we already see
  in bug reports. **Adopt** `.sgm` interop as a first-class input to
  the save-state lab (§4.8.3).

### 3.2 Time-travel & record-replay debuggers

- **[rr](https://rr-project.org/)** (Mozilla) — record once, replay
  deterministically, with reverse-continue. Chaos mode for rare bugs.
  Pernosco built on rr. **Adopt** the *recording* concept: every
  /pgoal session can record a PyBoy trace once, then everyone (CLI,
  TUI, LLM agent) replays the same trace and the answers agree.
- **[Pernosco](https://pernos.co/)** — *omniscient* debug UI. The
  trace is a queryable database — "when did this address change?",
  "what called this function?", "show me every event in the last
  500ms tagged with X." **Adopt** the **omniscient query model**:
  every byte/PC change is indexed, every query returns in <1s
  (§4.4.3).
- **[WinDbg TTD](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/time-travel-debugging-overview)**
  — Microsoft's time-travel for x86/x64 Windows. Reverse step, query
  history. **Adopt** the *step-back-N* UX in the source-level
  frontend (§4.6.2).
- **[Replay.io](https://www.replay.io/)** — JS time-travel debugger.
  UI patterns worth stealing: timeline scrubber, "comment on a point
  in time," shared replay URLs. **Adopt** for the web UI.
- **[gdb process-record](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Process-Record-and-Replay.html)**
  — built-in reverse execution. Limited. **Skip** as backend, but
  the user-facing commands (`reverse-step`, `reverse-continue`,
  `reverse-finish`) are the canonical names.
- **[Mesen2 rewind](https://www.mesen.ca/)** — emulator-level rewind
  buffer. **Adopt** the idea: keep an automatic rolling rewind buffer
  during interactive sessions for instant scrubbing.

### 3.3 Property-based & fuzz testing for emulators

- **[Hypothesis](https://hypothesis.readthedocs.io/)** — already in
  use for the damage debugger. **Extend** to other subsystems (boss
  AI generators already use it conceptually; formalize the contract).
- **[Hypothesis state machines](https://hypothesis.readthedocs.io/en/latest/stateful.html)**
  — stateful PBT. **Adopt** for multi-turn battle scenarios, multi-map
  overworld scripts, multi-trainer roster fuzz.
- **[libFuzzer](https://llvm.org/docs/LibFuzzer.html)** /
  **[AFL++](https://aflplus.plus/)** — coverage-guided fuzzers.
  **Adopt** the coverage-feedback loop on top of our existing per-PC
  coverage tracker.
- **[Csmith](https://embed.cs.utah.edu/csmith/)** — random valid-C
  program generation for differential compiler testing. **Adopt** the
  *generator-+-differential* pattern for Pokemon scenarios: generate
  random valid battles, run on ROM + oracle, flag divergence.
- **[Blargg test ROMs](https://github.com/c-sp/gameboy-test-roms)**,
  **[Mooneye](https://github.com/Gekkio/mooneye-test-suite)**,
  **[Same Suite](https://github.com/LIJI32/SameSuite)** — emulator
  conformance suites. **Adopt** as part of the cross-emu diff
  harness: any emulator we use must pass an agreed subset before we
  trust it.
- **[ddmin](https://www.st.cs.uni-saarland.de/zeller/projects/ddmin/index.html)**
  / **[hypothesis shrinking](https://hypothesis.readthedocs.io/en/latest/changes.html)**
  — minimization. Already in use; extend to multi-axis scenarios
  (§4.5.3).
- **[Metamorphic testing](https://en.wikipedia.org/wiki/Metamorphic_testing)**
  — relations instead of exact oracles. Already implemented for
  Boss AI; **extend** to overworld scripts and item economy
  (§4.5.4).

### 3.4 Static analysis on SM83

- **[mgbdis](https://github.com/mattcurrie/mgbdis)** — RGBDS-style
  disassembler. **Skip**, we already have the disassembly.
- **[Ghidra](https://ghidra-sre.org/) +
  [GhidraBoy](https://github.com/Gekkio/GhidraBoy)** — Ghidra plugin
  for SM83. **Adopt** for symbolic execution / decompilation of small
  functions where reading asm is too slow.
- **[Binary Ninja SM83](https://github.com/LIJI32/SameBoy)** — there's
  a BNIL lifter floating around. **Investigate** but **skip** unless
  needed.
- **[rgbds](https://rgbds.gbdev.io/)** — our build. `.sym` + `.map` +
  linker output are our primary sources of truth. **Build a
  comprehensive symbol service on top** (§4.6.3).
- **Cross-bank call analysis**: we already have
  [`check_cross_bank_call.py`](../tools/audit/check_cross_bank_call.py).
  **Extend** to *whole-program* — every plain `call` audited against
  bank assignment, with whitelist for ROM0 thunks.
- **Register-clobber inference**: this is the AG-NN bug class.
  **Build** an abstract-interpretation-style "clobber set" inference
  for every function, with caller-side compatibility check on every
  edit.
- **[KLEE](https://klee-se.org/)** / **[angr](https://angr.io/)** —
  symbolic execution. **Adapt**: write a tiny SM83 path-bounded model
  checker in Python over our existing disassembly walker (§4.7.2).
  Full angr port is out of scope.

### 3.5 Modern debug UX

- **[Debug Adapter Protocol (DAP)](https://microsoft.github.io/debug-adapter-protocol/)**
  — the protocol VS Code uses. **Adopt**: ship a DAP server that
  understands our trace ROM + symbol service so the user can step
  through asm in VS Code with HP / wCurDamage / register watch
  expressions.
- **[Tracy](https://github.com/wolfpld/tracy)** /
  **[Perfetto](https://perfetto.dev/)** — interactive flame graphs.
  **Adopt** for cross-function trace visualization once we have
  enough events.
- **[OpenTelemetry](https://opentelemetry.io/)** — trace/span event
  model. **Adopt** as our event schema (§5.4).
- **[MLflow](https://mlflow.org/)** — experiment tracking. **Adopt**
  patterns (already partly done in boss_ai_debugger run store).
- **[Arrow](https://arrow.apache.org/)** /
  **[DuckDB](https://duckdb.org/)** — columnar analytics. **Adopt**
  for the omniscient byte-history store (§4.4.3) and the per-run
  batch result store.

### 3.6 LLM-assisted debugging

- Anthropic [computer use / browser
  use](https://docs.claude.com/en/docs/build-with-claude/computer-use)
  — applied here as "Claude can drive the debugger UI." **Adopt**:
  the debugger MUST expose a clean CLI/JSON surface for Claude to
  query, not just human-facing TUI.
- Academic work on LLM-as-debugger (DebugBench, RepairLLaMA,
  Reflexion-on-debug) — **adopt** the *hypothesis tree* pattern:
  every debug session is a tree of hypotheses, each with experiments
  + verifications, persisted across sessions.
- Specifically for asm: nobody's done this well at scale yet. **Build
  the first one ourselves**: an LLM agent that can ask the symbol
  service, run scenarios, inspect traces, and propose patches with
  citations to the asm authoring guide.

(Full research bibliography in §10. Agent reports cite specific URLs
where each pattern was sourced.)

## 4. Feature Catalog — Exhaustive

This is the long list. Every plausibly useful feature, organized by
debugger layer. Each entry is tagged with **status** (`have` / `extend` /
`new`) and target **phase** (P0–P12, see §7).

### 4.1 Debugger kernel

| Feature | Status | Phase | Notes |
| --- | --- | --- | --- |
| Headless PyBoy session w/ deterministic boot | have | — | `tools/damage_debugger/emulator.py` |
| Boot-state cache (240-frame warm start) | have | — | `boot_cache.py` |
| HRAM-sentinel function-under-test runner | have | — | `safe_call.py` |
| Cross-process emulator pool | partial | P1 | Used in fuzz workers; needs a kernel-level pool for batch runs across all tools |
| Persistent emulator process w/ RPC | new | P3 | One PyBoy spawned per worker, kept alive across hundreds of scenarios |
| Hot-swap WRAM/SRAM mid-scenario | partial | P2 | We patch WRAM at scenario seed; extend to mid-run mutation |
| Hot-swap ROM bytes mid-scenario | new | P5 | For "what if this instruction were `xor a` instead?" probes |
| Cycle-accurate alternate backend (SameBoy) | new | P4 | Spawn SameBoy as a subprocess, drive via libretro / SameBoy SDK; same scenario must produce same `wCurDamage` |
| Cycle-accurate alternate backend (gambatte) | new | P4 | Same idea; gambatte is the accuracy reference |
| **VBA-M parity backend** | new | P4 | Lower-automation backend: savestate load + frame tick + memdump only, no breakpoint integration. User plays in VBA — divergence between accuracy reference and VBA is the May 2026 tile-jumble bug class |
| Cycle-accurate alternate backend (BGB) | new | P9 | Windows only; deferred |
| Emulator divergence flagger | new | P4 | Run scenario on N emulators, fail if `wCurDamage` / `wEnemyMonHP` / etc differ |
| ROM reload on rebuild | partial | P1 | Currently re-spawn; should be in-process reload |
| Save-state load (PyBoy `.state`) | have | — | Used by trace state factory |
| Save-state load (VBA `.sgm`) | partial | P6 | Legacy decoder in `tools/damage_debugger/legacy/sgm_decoder.py`; promote to active |
| Save-state load (BGB `.sn1`/`.sn2`) | new | P9 | Format docs scarce; lower priority |

### 4.2 Symbol & source service

| Feature | Status | Phase | Notes |
| --- | --- | --- | --- |
| `.sym` parser (forward + reverse) | have | — | `symbols.py` |
| `.map` parser (free-space tracker) | partial | P1 | `scripts/generate_dev_index.py` reads it; need programmatic access |
| Source-line ↔ PC map | new | P1 | Build from rgbds object files; needed for source-level step |
| Macro-expansion debugger | new | P2 | `farcall`, `homecall`, `JumpTable`, `rst Bankswitch` all expand inline; debugger must unwind to surface the macro-level call |
| Cross-reference DB (xrefs) | new | P2 | "Who calls `BattleCommand_DamageCalc`?" answered in O(1) without grep |
| Comment / docstring extractor | new | P3 | Function-header `; In: hl=...` blocks are our register ABI; parse and surface in tooltips |
| Bank ownership map | partial | P1 | `dev_index.md` has it; programmatic access via a typed DataFrame |
| Save format schema export | partial | P1 | `ram/` parsed into a structured schema (Pydantic) |
| Constant resolution (`MOVE_FLAMETHROWER` → 53) | new | P2 | Resolve constants in `.sym` and `constants/` so the user types names |

### 4.3 Tracing

| Feature | Status | Phase | Notes |
| --- | --- | --- | --- |
| PC trace over a single function | have | — | `tracer.py` |
| PC trace project-wide (PC + bank + cycle) | partial | P2 | Currently only inside a `safe_call`; extend to free-run interactive sessions |
| Memory access trace (per-byte read/write) | new | P2 | Backed by interval-tree for time-travel queries |
| Register trace (per-instruction) | partial | P2 | Tracer has it within scope; promote to free-run |
| Stack trace reconstruction (cross-bank) | new | P3 | `farcall` does not put a normal return — reconstruct call chain from `rst FarCall` returns and bank stack |
| OAM / VRAM access trace | new | P6 | For graphics debug |
| LCD timing trace | new | P6 | Mode 0/1/2/3 transitions, VBlank misses |
| Interrupt trace | new | P6 | When was each interrupt taken, how long did it run |
| Audio register trace | new | P9 | When was each sound channel touched |
| Tracer subscription bus | new | P2 | Subscribers register interest in PC ranges / mem regions / events; only matching frames flow to them. Avoids the cost of dumping everything always |
| Tracer sampling | new | P2 | For long sessions, sample 1 in N frames or only frames near events |
| Tracer compression | new | P3 | Delta-encode register snapshots; reach Pernosco-scale storage |
| Tenet export | have | — | `tenet_writer.py` |
| OpenTelemetry export | new | P3 | Same data, OTel format → DuckDB / Grafana / Jaeger if anyone wants the eye candy |

### 4.4 Time-travel & omniscient queries

| Feature | Status | Phase | Notes |
| --- | --- | --- | --- |
| Bounded snapshot ring around function calls | have | — | `replay.py` |
| Free-run rolling rewind buffer | new | P3 | Like Mesen2 rewind, every N frames a snapshot, ring of last ~30s |
| Step backwards (instruction) | new | P3 | Backed by trace + snapshot ring |
| Step backwards (source line) | new | P6 | Maps to source-line map (§4.2) |
| Reverse-continue to PC | new | P3 | Like `gdb reverse-continue` |
| Reverse-continue to mem-write of address | new | P3 | Like `gdb reverse-step` until `*addr` changed |
| Byte history database | new | P3 | Interval tree: for each address, list of (cycle, old, new). Queries: "when did `wCurDamage` last change?" in O(log n) |
| Call history database | new | P3 | Sequence of (cycle, bank, target, return). Queries: "who called `BattleCommand_DamageCalc` between cycles X and Y?" |
| Branch history database | new | P3 | Sequence of (cycle, PC, taken). Queries: "did this `jr nz` ever fall through during the scenario?" |
| Omniscient query DSL | new | P4 | Pernosco-style mini-language: `bytes.changes_in(wCurDamage, cycle_range=...)`. Backed by DuckDB over Parquet |
| Diff two traces | new | P4 | "How did this trace differ from the regression baseline?" |
| Time-travel-aware comparison | new | P4 | When two emulators diverge (§4.1), the diff says *at which cycle and why* |

### 4.5 Property / fuzz / differential testing

| Feature | Status | Phase | Notes |
| --- | --- | --- | --- |
| Hypothesis fuzz over `BattleInputs` | have | — | `fuzz.py` |
| Hypothesis state-machine multi-turn battle | new | P5 | Sequences of move + switch + item until divergence |
| Hypothesis state-machine overworld | new | P9 | Sequences of player actions in a map until event corruption |
| Coverage-guided generator | new | P5 | Use per-PC coverage as guidance; favor inputs that hit new PCs |
| Differential vs Python oracle | have | — | `oracle.py` |
| Differential vs vanilla pokegold | new | P8 | Run same input on hack + vanilla pokegold; flag *unexpected* changes in unchanged subsystems |
| Differential across emulators | new | P4 | §4.1.1 |
| Differential across git revisions | new | P8 | Bisect: which commit changed this scenario's output? |
| ddmin scenario minimizer | have | — | `minimize.py` |
| Multi-axis minimizer (mons + moves + items + state) | extend | P5 | Use Hypothesis structured shrinking |
| Metamorphic relations (boss AI) | have | — | `metamorphic.py` |
| Metamorphic relations (damage) | new | P5 | E.g. "doubling base power doubles damage modulo crit/var" |
| Metamorphic relations (overworld) | new | P9 | E.g. "reordering disjoint script lines produces same map state" |
| Mutation testing (Python scorer) | have | — | `mutation.py` |
| Mutation testing (Python oracle) | new | P5 | Mutants of `oracle.py`; smoke must catch each |
| Mutation testing (asm in sandbox build) | new | P10 | Specific instruction-level mutants on a sandbox build; rebuild + run smoke + flag survivors |
| Oracle invariant mining (Daikon-style) | partial | P5 | `boss_ai_debugger/invariants.py` for boss; extend to damage |

### 4.6 Source-level debugger frontend

| Feature | Status | Phase | Notes |
| --- | --- | --- | --- |
| DAP server | new | P6 | Speak Debug Adapter Protocol so VS Code can attach |
| Breakpoint on label | new | P6 | Source name → bank+PC |
| Breakpoint on source line | new | P6 | Needs source-line map |
| Conditional breakpoint | new | P6 | Expression evaluated in symbol context |
| Watchpoint on WRAM byte | new | P6 | Memory write trap |
| Watchpoint on register set | new | P6 | E.g. `a == 5 && c & 0x80` |
| Step over (call) | new | P6 | Treats `call`/`farcall`/`rst` as one step |
| Step into | new | P6 | Follows call |
| Step out | new | P6 | Run until matching ret |
| Step back (instruction) | new | P6 | Reverse-step |
| Step back (line) | new | P6 | Reverse-step to previous source line |
| Watch expressions | new | P6 | `wBattleMonHP`, `[hl+1]`, etc |
| Symbol-aware register view | new | P6 | E.g. `hl=wBattleMon+8 (Atk)` |
| Stat-stage view | new | P6 | Decode base-7 → multiplier |
| Memory map view | new | P6 | ROM / WRAM / SRAM / HRAM / IO / VRAM, click to inspect |
| RGBDS source open at PC | new | P6 | Click address, jump to `.asm` line |
| Inline disassembly w/ macro reconstruction | new | P6 | `farcall` shown as one logical call |

### 4.7 Static analysis

| Feature | Status | Phase | Notes |
| --- | --- | --- | --- |
| Cross-bank call audit | have | — | `check_cross_bank_call.py` |
| `farcall hl` clobber audit | have | — | `check_farcall_hl_clobber.py` |
| `farcall a` clobber audit | have | — | `check_farcall_a_clobber.py` |
| `ld a,0` / `cp 0` lint | have | — | `check_ld_a_zero.py`, `check_cp_zero.py` |
| Free-space bank-pressure | partial | P1 | `check_pic_bank_pressure.py`; promote to whole-ROM model |
| Stack-depth bounds | new | P7 | Recursive call-graph; flag any function whose max depth could overflow $C000-$DFFF stack |
| Register-clobber inference (AG-NN) | new | P7 | Per-function abstract interpretation; emit a clobber-set summary; flag callers that depend on a clobbered reg |
| Save-format drift audit | new | P7 | Snapshot `ram/` struct hashes; flag offset shifts without `SAVE_FORMAT_VERSION` bump |
| Dead-code / unreachable label | new | P7 | Static call-graph; flag exported labels with no callers |
| `ldh` vs `ld [$FFxx]` consistency | new | P7 | Style + size |
| VRAM access timing | new | P9 | Find writes to `$8000-$9FFF` outside vblank windows |
| Macro consistency (`farcall` not silently downgraded to `call`) | new | P7 | The April 2026 / May 2026 / AG-08 class |
| Constant-vs-magic-number audit | new | P9 | `ld a, 53` vs `ld a, MOVE_FLAMETHROWER` |
| Bank assignment validator | new | P7 | Cross-check `SECTION` declarations against `_BankMap` outputs |

### 4.8 Save-state lab

| Feature | Status | Phase | Notes |
| --- | --- | --- | --- |
| Load VBA `.sgm` into PyBoy-shaped state | partial | P6 | Legacy decoder; promote |
| Load PyBoy `.state` | have | — | Used by trace state factory |
| Diff two save states (field by field) | new | P6 | Decode WRAM + SRAM into named fields; show only the changed ones |
| Save-state ↔ scenario converter | new | P6 | Load a real player's save → extract `BattleInputs` for the harness |
| Save-format version detector | partial | P6 | Read `SAVE_FORMAT_VERSION`; warn on mismatch |
| Save-format migration scaffolding | new | P10 | When `ram/` reorders, generate a migration script for shipped saves |
| WRAM heatmap | new | P6 | Render WRAM as a 256x... grid colored by recent write density |
| SRAM page diff | new | P6 | Compare two saves' SRAM pages |

### 4.9 Battle-engine instrumentation

| Feature | Status | Phase | Notes |
| --- | --- | --- | --- |
| Damage chain step tracer | have | — | `full_chain_v2.py`, `trace_chain.py` |
| Per-PC hook instrumentation | have | — | `find.py --instrument-hook` |
| Live battle state inspector | new | P5 | Render party + active + stages + status + weather as one table |
| Damage chain diagram (player-facing) | new | P5 | "Wing Attack base 60 → STAB 90 → SE 180 → Variation 158…203 → 38–46 actual" — readable, not hex |
| Stat-stage view (decoded) | new | P5 | Base-7 → multiplier |
| Type chart view (live) | new | P5 | Show defender's types + current attack's effectiveness; warns "this is a re-typed mon (data/pokemon/base_stats/<name>.asm)" |
| Turn-by-turn replay | new | P5 | Replay every turn with state diff between turns |
| Move script tracer | new | P5 | Step every `BattleCommand_*` in a move's script |
| Crit-chance probe | new | P5 | Sample crits, show observed vs expected rate |
| Variation distribution probe | new | P5 | Sample DamageVariation; show histogram |
| Speed-tie observability | new | P5 | When speed-tie occurs, show which mon won and the RNG byte |

### 4.10 Boss AI / decision intelligence

(Most of this is the [boss_ai_debugger SOTA
plan](boss_ai_debugger_state_of_art_implementation_plan_2026-05-15.md);
unified here.)

| Feature | Status | Phase | Notes |
| --- | --- | --- | --- |
| Decision waterfall (rule-by-rule score deltas) | partial | P5 | Boss SOTA plan §3 |
| Selector replay (final score → chosen move) | have | — | `check_boss_ai_selector_replay.py` |
| Pre-choice replay (state → chosen move) | have | — | `check_boss_ai_pre_choice_replay.py` |
| Counterfactual explainer | have | — | `counterfactuals.py` |
| Localize (statistical) | have | — | `localize.py` |
| Multi-turn route projection | have | — | `route_eval.py` |
| Mastery integration | have | — | `mastery_index.py` |
| Active review queue | have | — | `review_queue.py` |
| Hidden-info leak audit | have | — | `metamorphic.py`, `check_boss_ai_no_cheat.py` |
| Live Haki tracker | new | P11 | When Haki fires (once-per-battle authored exceptions), log it and verify it was authored, not implicit |
| "Why did the boss do X" — natural-language explanation | new | P11 | LLM-driven, grounded in rule map + decision waterfall |

### 4.11 Graphics / overworld / audio scope

| Feature | Status | Phase | Notes |
| --- | --- | --- | --- |
| VRAM tile viewer | new | P9 | Live or post-trace; render $8000-$97FF as tile grid |
| OAM sprite viewer | new | P9 | Live or post-trace; show all 40 sprite slots |
| BG map viewer | new | P9 | The May 2026 VBA tile jumble class — would catch it earlier |
| Tilemap diff (frame N vs N+1) | new | P9 | Spot rogue writes |
| Palette viewer | new | P9 | Per-frame palette state |
| Map script tracer | new | P9 | Step `engine/overworld/scripting.asm` commands as a turn-based VM |
| Event flag explorer | new | P9 | Decode `wEventFlags` with named flags |
| Trainer flag diff | new | P9 | When did `JR_YOUNGSTER_JOEY` get set? |
| Map transition tracer | new | P9 | When was the map switched, by which script |
| Audio register snapshot | new | P9 | $FF10-$FF26, decoded |
| Music position tracker | new | P9 | Current channel position |
| Sound effect tracer | new | P9 | Which SFX, when, by what code |

### 4.12 Stress / soak / coverage

| Feature | Status | Phase | Notes |
| --- | --- | --- | --- |
| Trainer tournament simulator | new | P8 | Boss AI vs Boss AI across all trainers; coverage + crash detection |
| Wild encounter fuzz | new | P8 | Walk a route, encounter ~1000 wild mons, no crash, expected level spread |
| Random-input soak | new | P8 | Mash random input for N hours; expect no crashes, expected save state |
| Save-load loop soak | new | P8 | Save → reload → save → ... 1000 times; SRAM/save format stability |
| Per-PC coverage report | have | — | `coverage.py` |
| Per-rule coverage (boss AI) | have | — | `boss_ai_debugger/coverage_report.py` |
| Per-branch coverage | new | P8 | jr / jp conditional fall-through coverage |
| Per-function coverage | new | P8 | Aggregate |
| Source-line coverage | new | P8 | Maps to source-line map |
| Coverage badge in PR | new | P10 | Coverage % per touched file in CI summary |

### 4.13 LLM-assisted debug

| Feature | Status | Phase | Notes |
| --- | --- | --- | --- |
| Clean CLI/JSON surface for every tool | partial | P1 | Already mostly true; tighten contract |
| Hypothesis tracker (persistent tree) | new | P11 | `audit/hypothesis_tree.jsonl` — every "I think X is broken, let me check Y" with verifications |
| Auto-localize from failure description | new | P11 | LLM reads `find` output + `taint` output, proposes localized fix candidates with confidence |
| Auto-citation grounding | new | P11 | Every LLM claim cites a file:line or audit output |
| Symbol-aware autocomplete | new | P11 | The LLM can autocomplete `wBattleMon...` from the symbol service |
| LLM-driven scenario synthesis | new | P11 | "Generate a Hypothesis strategy for crit-physical-vs-Eviolite" |
| Memory-format reverse-engineering | new | P11 | "Here's a hex dump, tell me what struct this is" using the schema service |
| Patch proposer with citation to authoring guide | new | P11 | LLM patches must cite `asm_authoring_guide.md` § for any new asm |

### 4.14 UI

| Feature | Status | Phase | Notes |
| --- | --- | --- | --- |
| CLI (PowerShell + bash) | have | — | Every tool is CLI-first |
| Markdown report output | have | — | `coverage.md`, `damage_heatmap.md`, etc |
| JSON output for every tool | have | — | Audit + json out widespread |
| TUI (Textual / Rich) | new | P6 | Single-developer interactive view |
| Web app (FastAPI + Svelte) | new | P10 | Battle visualizer + decision explorer + time-travel scrubber |
| VS Code extension (DAP) | new | P6 | Source-level step + watch + breakpoints |
| Static HTML reports | partial | P5 | Some markdown; render as HTML w/ tooltips for full version |
| Diagram / DOT graph output | new | P9 | Call graph, control-flow graph |

### 4.16 MCP server — the LLM contract

**The single most important new surface.** Research consensus across
the UI/LLM agent and the GB-debugger agent: the right contract between
Claude (the collaborator) and our debugger is an
[MCP](https://modelcontextprotocol.io/) server, not a CLI to be invoked
from the outside. [Gearboy 3.8.4](https://github.com/drhelius/Gearboy)
already ships `--mcp-stdio` / `--mcp-http`; the
[PyBoy MCP server](https://mcpmarket.com/server/pyboy) demonstrates the
pattern for our exact emulator;
[ida-pro-mcp](https://github.com/mrexodia/ida-pro-mcp) is the canonical
RE example.

Why this matters here: the user runs Claude from CLI *and* the desktop
app. The same agent in both contexts must be able to inspect a trace,
step a scenario, evaluate a damage chain, or look up a symbol —
without re-discovering the tool surface every session. MCP solves
that.

Tools the MCP server exposes (Phase P11 + interleaved earlier as
each capability ships):

| Tool | Returns | Use case |
| --- | --- | --- |
| `step(n)` | new PC, regs, cycle | step N instructions in current scenario |
| `step_until(pc)` | regs at break, cycle | run until PC reaches symbol |
| `read_mem(addr, len)` | bytes | inspect WRAM/SRAM/HRAM/IO |
| `read_symbol(name)` | bytes + decoded value | symbol-aware memory read |
| `set_breakpoint(spec)` | breakpoint id | exec / read / write / cond |
| `clear_breakpoint(id)` | ok/err | remove |
| `run_scenario(spec)` | scenario result | one-shot deterministic run |
| `compute_damage(spec)` | (low,high) + chain | oracle-backed prediction |
| `query_symbol(prefix)` | matches | autocomplete |
| `lookup_label(pc)` | label, source_file, line | reverse symbol lookup |
| `query_history(query_dsl)` | rows | omniscient byte/call/branch query |
| `boss_decide(state)` | candidates + scores | run Python boss scorer |
| `boss_waterfall(state)` | rule-by-rule deltas | decision explanation |
| `run_audit(name)` | structured findings | exec a specific tools/audit script |
| `run_smoke()` | clobber_smoke summary | shortcut to the §6 floor |
| `crossemu_diff(spec)` | per-emu agreement | P4 cross-emulator check |
| `save_diff(a, b)` | named field deltas | P6 save lab diff |
| `static_clobber(fn)` | (uses, defs, preserves) | P7 register summary |
| `static_save_drift(against=branch)` | findings | P7 save-format lock check |

Findings come back as structured records compatible with Codex's
review format (File / Line / Issue / Why / Fix / Confidence — already
in user memory).

**Implementation.** Pure-Python MCP server in
`tools/debugger/llm/mcp_server.py`. The tools above are thin wrappers
around the kernel + analysis layers; no business logic lives in the
MCP file. Launch via `python -m tools.debugger mcp --stdio` for
Claude Code, or `--http --port 7777` for the desktop app.

**Why this lands early in P3, not later in P11.** The MCP tools are
the *natural* CLI for the kernel + bus. Building them up-front means
every later phase ships a Claude-usable surface for free, instead of
bolting one on at the end.

### 4.17 Dataflow panel — Pernosco's signature UX, applied to SM83

A user-facing "click any byte / register, walk backward through every
write that produced it" view, in the web UI (P10) and queryable via
MCP/CLI in P3.

Implementation backbone — building on the time-travel agent's
research:

```
For any (cycle, address, byte):
  1. Query byte_history for the most recent write ≤ cycle.
  2. That write has (pc, bank, source_label, source_file, line).
  3. Disassemble the instruction at pc.
  4. For each input register/memory cell of that instruction:
     - recurse, with the new "address" being the register/cell
       and the new "cycle" being just before pc executed.
  5. Stop on:
     - input event (button press, interrupt)
     - ROM constant (immediate or load from $0000-$7FFF)
     - user-pinned "trusted" boundary
```

SM83 makes this tractable in a way x86 doesn't: 8 GP registers, no
SIMD, no out-of-order execution, no speculative loads. The
[Pernosco dataflow page](https://pernos.co/about/dataflow/) describes
the same algorithm for x86 with all the complexity; ours is the easy
case. We're the first GB-tooling project to ship it, per the GB
debugger survey ("No SM83 taint tracking… No semantic-diff trace
viewer").

This subsumes `tools/damage_debugger/taint.py` — that's the
register-and-memory taint forward-propagator already; the dataflow
panel is the backward-walker that uses the same SM83 disassembly
model. Both live under `tools/debugger/analysis/dataflow/`.

### 4.18 Source breakpoint opcodes (`ld b,b`, `ld d,d`)

BGB and SameBoy honor `ld b,b` (`0x40`) as a soft breakpoint and
`ld d,d` (`0x52`) as a debug-message marker — opcodes whose effect on
register state is a no-op, hijacked by the debugger as in-source
assertions. We **adopt** the same convention so debug markers stay in
asm and survive emulator changes:

```asm
BattleCommand_DamageCalc:
    ld d, d                  ; debug: hit damage calc
    ; ...
    cp $ff
    jr nz, .ok
    ld b, b                  ; breakpoint: damage saturated
.ok:
```

Cost: 1 byte per marker. Benefit: persistent, source-controlled,
emulator-portable. The debugger sees the opcode and reacts; without
a debugger attached, the marker is invisible. Audit: a
`tools/audit/check_debug_opcodes.py` warns if any `ld b,b` /
`ld d,d` ships in a release build; the debugger build leaves them in.

### 4.19 Expression language for conditional breakpoints

BGB's expression language is the de facto standard: CPU regs,
`TOTALCLKS`, `SCANLINE`, `ROMBANK`, `VALUE`, `TARGET`, `old`/`new`,
`..5` hit counts, mem dereference. SameBoy's expression evaluator is
similar with `[addr]`/`{addr}` deref. We **adopt** a small DSL with
these primitives — implementable in <300 LOC of Python with `ast`,
parsed once at breakpoint registration.

Example uses:

```
break BattleCommand_DamageCalc if [wCurDamage] > $00C8
break * if hl == wBattleMon
watch wCurDamage if new > 2 * old
break BossAI_ApplyMoveModel.score if ROMBANK == $0b && (cycle - last_hit) > 1000
```

This goes into P6 alongside the DAP server.

### 4.15 Observability & experiment store

| Feature | Status | Phase | Notes |
| --- | --- | --- | --- |
| Run metadata store | have | — | `audit/boss_ai_debugger/runs/`; generalize |
| Run-vs-run diff | partial | P3 | Boss AI has it; extend to damage + cross-domain |
| Artifact hashes | partial | P3 | Trace ROM hash, symbol hash already recorded |
| OpenTelemetry-style event stream | new | P3 | All trace events → OTel-shaped JSONL → DuckDB |
| Decision timeline render | new | P5 | Render any decision as a timeline UI (Pernosco-shaped) |
| Trace bisect | new | P8 | git bisect, but the criterion is "does this trace match the expected output" |

## 5. Architecture

### 5.1 Layered architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  Presentation                                                        │
│  CLI · TUI (Textual) · Web (FastAPI+Svelte) · VS Code (DAP) · LLM   │
├──────────────────────────────────────────────────────────────────────┤
│  Analysis                                                            │
│  Counterfactuals · Localize · Invariants · Coverage · Diff · Bisect │
│  Hypothesis fuzz · Metamorphic · Mutation · Stress · Static audits  │
├──────────────────────────────────────────────────────────────────────┤
│  Event Bus + Store                                                   │
│  OTel-shaped span tree → JSONL (stream) → Parquet (batch) → DuckDB  │
│  Byte-history interval-tree · Call-history sequence · Run store     │
├──────────────────────────────────────────────────────────────────────┤
│  Instrumentation                                                     │
│  PC trace · Mem trace · Reg trace · OAM/VRAM trace · Audio trace    │
│  Cross-bank stack reconstruction · Macro-aware step                 │
├──────────────────────────────────────────────────────────────────────┤
│  Kernel                                                              │
│  Emulator pool (PyBoy · SameBoy · gambatte) · Symbol service        │
│  Source-line map · State schema · Save-state I/O · ROM hot-swap     │
└──────────────────────────────────────────────────────────────────────┘
```

Each layer publishes a stable interface. Tools at one layer only depend
on lower layers. Existing tools (`damage_debugger`, `boss_ai_debugger`)
move into the Analysis layer as packaged modules — they don't get
rewritten, they get **plugged into** the kernel + bus + store.

### 5.2 Module structure

```
tools/debugger/                       (new umbrella package; existing tools are siblings until migrated)
  kernel/
    emulator_pool.py
    backends/
      pyboy.py                        (wraps current emulator.py)
      sameboy.py                      (new; subprocess + RPC)
      gambatte.py                     (new; subprocess + RPC)
    symbol_service.py                 (wraps current symbols.py + .map + source-line map)
    state_schema.py                   (Pydantic; project-wide WRAM/SRAM/HRAM schema)
    save_io.py                        (PyBoy .state + VBA .sgm + BGB .sn?)
  bus/
    events.py                         (OTel-shaped span tree)
    store_jsonl.py
    store_parquet.py
    store_duckdb.py
    byte_history.py                   (interval tree)
    call_history.py
    branch_history.py
  instrumentation/
    pc_tracer.py                      (extends current tracer.py)
    mem_tracer.py
    reg_tracer.py
    vram_tracer.py
    audio_tracer.py
    stack_reconstructor.py            (cross-bank)
    macro_resolver.py                 (farcall / homecall / rst Bankswitch / JumpTable)
  analysis/
    coverage.py                       (extends current coverage.py)
    counterfactuals.py                (extends boss_ai)
    localize.py
    invariants.py
    fuzz.py                           (extends damage_debugger.fuzz)
    metamorphic.py
    mutation.py
    diff.py                           (cross-run, cross-emu, cross-rev)
    bisect.py
    static/
      bank_pressure.py
      stack_depth.py
      clobber_inference.py
      save_drift.py
      cross_bank.py                   (current audit, promoted)
      macro_safety.py                 (farcall hl/a, c-mirror)
  presentation/
    cli.py                            (umbrella `python -m tools.debugger ...`)
    tui/                              (Textual app)
    web/                              (FastAPI + Svelte)
    dap/                              (Debug Adapter Protocol server)
    reports/
      markdown.py
      html.py
      diagram.py
  llm/
    hypothesis_tracker.py             (audit/hypothesis_tree.jsonl)
    citation_grounder.py
    scenario_synth.py
```

This is aspirational. We don't bulk-rename existing code on day one;
we add the umbrella and migrate progressively.

### 5.3 State schema

The state schema is the canonical model of *everything* the debugger
knows about a moment in time. It absorbs:

- The boss_ai_debugger
  [state_schema](boss_ai_debugger_state_schema.md).
- The damage_debugger `BattleInputs` dataclass.
- A new project-wide schema for WRAM / SRAM / HRAM / IO derived from
  `ram/` + `constants/` + macros.

Implementation: Pydantic v2 models, one per top-level region, composed
into a `WorldState`. Round-trips to/from JSON, JSONL, Parquet, PyBoy
`.state`, and (read-only) VBA `.sgm`.

Public-vs-private boundary is a first-class field, not prose: every
attribute carries `visibility: public | semi-public | hidden | haki`.
The boss-AI no-cheat audits use this directly.

### 5.4 Event schema (OpenTelemetry-shaped)

Every observable event in the debugger is a **span** in a tree:

```jsonc
{
  "trace_id": "run_2026-05-16_morty_001",
  "span_id": "decision_42",
  "parent_span_id": "battle_turn_7",
  "name": "score_rule",
  "start_cycle": 1234567,
  "end_cycle": 1234589,
  "attributes": {
    "rule_id": "move.spikes.public_rapid_spin_risk",
    "candidate_slot": 2,
    "score_before": 12,
    "score_after": 22,
    "delta_signed": 10,
    "predicate_outcome": "true",
    "public_reads": ["wPlayerUsedMoves", "wPlayerMonSpecies"],
    "source_label": "BossAI_ApplyMoveModel.spikes_revealed_spin",
    "source_file": "engine/battle/ai/boss_policy_move.asm"
  }
}
```

Spans nest: a `battle_turn` contains `score_rule`s, which contain
`memory_read`s; a `damage_chain` contains `BattleCommand_*` calls; a
`map_script` contains `script_command`s.

Storage strategy:

- **In-memory** during a single scenario: list of dataclasses, ~100KB.
- **JSONL** for streaming runs: append-only.
- **Parquet** for batch analytics: snappy-compressed columnar.
- **DuckDB** for queries: views over Parquet files, scanned in <100ms
  for any reasonable corpus size.

### 5.5 Persistent store layout

```
audit/debugger/
  runs/
    YYYY-MM-DD_HHMM_<slug>/
      meta.json                # commit, ROM hash, symbol hash, seed, command
      events.jsonl             # streaming
      events.parquet           # built post-run
      byte_history.parquet     # interval tree dump
      call_history.parquet
      summary.md
      artifacts/
        decision_waterfall_*.html
        damage_chain_*.svg
        coverage_diff.md
        review_queue.json
  hypothesis_tree.jsonl        # LLM-driven debug session log
  trace_archive/               # gzipped tar of long traces for cold storage
  baseline/
    smoke/                     # known-good outputs for regression
    vanilla/                   # vanilla pokegold reference traces
```

DuckDB views over `audit/debugger/runs/*/events.parquet` give us
project-wide queries: "every selector mismatch this week," "every
trace where `wCurDamage > 200`," "every commit that changed
`BattleCommand_Stab` coverage."

### 5.6 Plugin interface

Existing tools register as **plugins** with the kernel:

```python
# tools/damage_debugger/plugin.py
from tools.debugger.kernel.plugin import DebuggerPlugin

class DamageDebuggerPlugin(DebuggerPlugin):
    name = "damage"
    commands = {
        "smoke": clobber_smoke.main,
        "fuzz":  fuzz.main,
        "find":  find.main,
        # ...
    }

    def register_event_subscribers(self, bus):
        bus.subscribe("memory_write", self._on_mem_write)
        bus.subscribe("score_rule", self._on_score_rule)
```

`python -m tools.debugger damage smoke` dispatches to the plugin
without losing the existing `python -m tools.damage_debugger.clobber_smoke`
entry. Migration is non-breaking.

## 6. Tech Stack

### 6.1 Adopted (already in use)

- **Python 3.13+** — primary language. We have it everywhere. No reason
  to switch.
- **[PyBoy](https://github.com/Baekalfen/PyBoy) 2.7+** — primary
  emulator. Mature, scriptable, fast enough.
- **[Hypothesis](https://hypothesis.readthedocs.io/) 6+** — property
  testing. Already integrated in fuzz.
- **[Pydantic](https://docs.pydantic.dev/) 2** — schema models.
  Already in use in `tools/boss_ai_preference`.
- **PowerShell + WSL** — the existing dev surface; the user prefers
  PowerShell from CLI. WSL is needed for `make`. We won't change this.
- **RGBDS 1.0.1** — build toolchain. Hands-off.

### 6.2 New core

- **[SameBoy](https://sameboy.github.io/) (subprocess)** — second
  emulator backend for cross-emu diff. Cycle-accurate. Driven via its
  scripting REPL or a small thin RPC wrapper we write.
- **[gambatte](https://github.com/sinamas/gambatte)** — accuracy
  reference. Same RPC pattern.
- **[VBA-M](https://vba-m.com/)** — fourth cross-emu backend, parity
  with the user's play emulator. Lower-automation: savestate load +
  frame tick + memdump. Driven via subprocess + savestate file IO; the
  legacy `.sgm` decoder under
  [`tools/damage_debugger/legacy/sgm_decoder.py`](../tools/damage_debugger/legacy/)
  is the starting point and gets promoted in P6.
- **[Apache Arrow](https://arrow.apache.org/) + Parquet** — columnar
  event store. Read via PyArrow.
- **[DuckDB](https://duckdb.org/)** — embedded SQL over Parquet/JSONL.
  Single-process, no daemon. The user can query our event store with
  plain SQL.
- **[Textual](https://textual.textualize.io/)** — TUI framework. Same
  authors as Rich. Best-in-class Python TUI.
- **[FastAPI](https://fastapi.tiangolo.com/) + [Svelte
  5](https://svelte.dev/)** — web UI. FastAPI for the backend
  (Python-native), Svelte for the frontend (less framework overhead
  than React). Static build, can run from `localhost:8765`.
- **[debugpy](https://github.com/microsoft/debugpy) + the
  [DAP](https://microsoft.github.io/debug-adapter-protocol/)
  reference** — for the VS Code source-level frontend. We write our own
  DAP server in Python (no debugpy lift; debugpy is the reference
  implementation we'll learn from).
- **[networkx](https://networkx.org/)** — call graph + control-flow
  graph analysis.
- **[graphviz](https://graphviz.org/) (subprocess)** — diagram
  rendering.

### 6.3 Considered + rejected (with reasons)

- **Rust / Go rewrite** — no. Python is fast enough for batch
  workloads given the emulator is the bottleneck. Rewriting in Rust
  buys ~5x batch speed at ~5x complexity; the user is the only
  developer and reads Python.
- **Tauri / Electron desktop** — no. Web UI on localhost is
  zero-install and lets the user iterate on the frontend without
  rebuilding. Tauri's value is offline / packaged distribution,
  which we don't need.
- **VS Code extension (TypeScript)** — the DAP server is enough.
  Writing a custom extension adds language-server complexity. If
  needed later, the DAP server can be wrapped in a thin TS extension.
- **Jupyter notebooks** — no. We already have CLI + Markdown; the
  notebook surface adds another file format and another
  reproducibility problem. If we want notebook-style analysis, DuckDB
  + Markdown is enough.
- **Ghidra / IDA / Binary Ninja embedded** — overkill. We have source.
  Static analysis is custom Python on top of `.sym` + `.map` + source.
  We may export to Ghidra projects for *manual* exploration, but
  Ghidra isn't a runtime dependency.
- **angr / KLEE port** — too ambitious for the value. Our SM83
  functions are small; a path-bounded model checker in pure Python is
  more tractable and tailored to our needs.
- **gRPC / Thrift between layers** — no. We're single-process Python.
  In-process function calls + Pydantic models are simpler.

### 6.4 Optional (when needed)

- **[Grafana](https://grafana.com/) / [Jaeger](https://www.jaegertracing.io/)**
  — if the OTel-shaped event store grows large enough to want
  off-the-shelf UI, both speak the protocol. Until then, DuckDB +
  Markdown is enough.
- **[Polars](https://pola.rs/)** — faster DataFrame than pandas. If
  any batch analytics become slow, swap in.
- **[Rich](https://github.com/Textualize/rich)** — already pulled in
  by Textual. Use for inline tables / colored output in CLI.

## 7. Implementation Phases

Each phase has: deliverables, exit criteria, estimated effort (in
"focused Claude days" — about 4 hours of dedicated work), risk, and
user-approval points.

### P0 — Plan + baseline gates (this doc + ~1 day)

**Deliverables.**

- This roadmap document, reviewed by the user.
- A single `tools/debugger/__init__.py` umbrella with `python -m
  tools.debugger status` that lists every existing tool entry-point and
  its README.
- A `tools/audit/check_debugger_roadmap_freshness.py` audit that fails
  if `docs/debugger_roadmap.md` claims a phase is complete but the
  phase's exit-criterion audit isn't passing.

**Exit.**

- User accepts roadmap scope or asks for trimming.
- All existing tools still work (no regression).

**Risk.** None — pure doc + index.

**Approval point.** **YES — before starting P1.**

### P1 — Symbol/source service + state schema (3–4 days)

**Deliverables.**

- `tools/debugger/kernel/symbol_service.py` consolidating `.sym` +
  `.map` + bank ownership + source-line map. Builds an index at startup
  in <500ms.
- `tools/debugger/kernel/state_schema.py` — Pydantic models for
  WRAM/SRAM/HRAM/IO. Derived from `ram/` + `constants/`. Round-trips to
  JSON + Parquet + PyBoy `.state`.
- A canonical `WorldState` Pydantic model that current tools (damage,
  boss AI) consume via thin adapters.
- A migration shim so existing `tools/damage_debugger/symbols.py` and
  `tools/boss_ai_debugger/state_schema.py` re-export from the new
  service.

**Exit.**

- `python -m tools.debugger schema validate` passes for every fixture
  + every live trace state.
- `python -m tools.debugger symbol resolve wBattleMonHP` returns
  `(bank=0, addr=0xCB95)` (or whatever) without parsing `.sym`
  per-call.
- Existing damage/boss tools still pass their self-checks.

**Risk.** Low — refactor with adapter shim, not bulk rename.

**Approval point.** No.

### P2 — Tracing & macro-aware step (4–5 days)

**Deliverables.**

- `tools/debugger/instrumentation/macro_resolver.py` — given a PC,
  return the logical macro call (`farcall TargetFn`, `homecall ...`,
  `rst Bankswitch`, `JumpTable dispatch`).
- Extended PC tracer that records bank + cycle + macro context.
- `mem_tracer.py` and `reg_tracer.py` running per-instruction, with
  configurable subscription (only addresses I care about → only those
  events).
- Cross-bank stack reconstructor — given a `ret`, figure out which
  bank we're returning to by replaying the `rst FarCall` stack.

**Exit.**

- A single scenario can be traced with PC + bank + register + memory
  events in one streaming pass.
- `python -m tools.debugger trace --scenario physical_no_items
  --emit-events events.jsonl` produces a valid event stream that loads
  into DuckDB.
- Sample query: `SELECT * FROM events WHERE name = 'memory_write' AND
  attributes.address = (SELECT addr FROM symbols WHERE name =
  'wCurDamage')` returns the right rows.

**Risk.** Medium — instrumenting per-instruction may slow scenarios
significantly. Mitigation: subscription-based filtering at the source.

**Approval point.** No.

### P3 — Event store + omniscient byte history + MCP server (5–7 days)

**Deliverables.**

- `tools/debugger/bus/store_jsonl.py`,
  `tools/debugger/bus/store_parquet.py`,
  `tools/debugger/bus/store_duckdb.py`.
- `byte_history.py` — **hybrid snapshot + per-byte delta log**, per
  the time-travel research:
  - Full PyBoy state snapshot every 60 frames (1 / sec), zstd
    compressed to ~5–10 KB each.
  - Between snapshots, log every CPU-driven write as `(frame, sub_cycle,
    pc, bank, addr, old_byte, new_byte)`.
  - **Per-address write index** in either an in-memory dict-of-lists
    (fast, fits ROM-hack scale) or RocksDB with key
    `(addr, frame, sub_cycle)` (persistent, ranged scans).
  - Expected size: 20–100 MB per 5-minute battle scenario.
  - DMA / OAM DMA / HDMA writes get tagged `pc=None, source=OAM_DMA` —
    the time-travel agent flagged this as the SM83 analog of rr having
    to special-case shared memory.
- `call_history.py` — sequence store with bank + return-PC,
  cross-bank stack reconstructed from `rst FarCall`.
- `branch_history.py` — sequence of (cycle, PC, taken).
- A free-run rolling rewind buffer: forked-emulator query pool
  (Replay.io trick) — pool of N PyBoys parked at evenly-spaced
  snapshots. Incoming query for time T: pick nearest parked emulator,
  fork (PyBoy state pickle is microseconds), fast-forward. Sub-second
  latency for any time-travel query.
- **MCP server** (`tools/debugger/llm/mcp_server.py`) — initial tool
  set: `step`, `read_mem`, `read_symbol`, `set_breakpoint`,
  `run_scenario`, `query_symbol`, `lookup_label`, `query_history`,
  `run_audit`, `run_smoke`. Speaks stdio (Claude Code) + HTTP (desktop
  app).
- `python -m tools.debugger query 'bytes.changes_in(wCurDamage)'`.
- Run metadata + artifact-hash recording lifted from
  `boss_ai_debugger/run_store.py`.

**Exit.**

- A 5-minute interactive scenario produces ≤200MB of events.
- `python -m tools.debugger query` answers any byte/call history
  question in <1s.
- Run-vs-run diff works for damage + boss + (toy) overworld scenarios.
- Claude (via MCP) can drive a scenario, set a breakpoint, and read
  memory without a CLI round-trip.

**Risk.** Medium-high. Storage churn is the main worry. Mitigation:
delta-encoding, zstd compression, configurable event subscription;
time-windowed recording (don't record boot/title screen by default).
Determinism gotchas: PyBoy audio mixer floats, dict iteration order —
the divergence detector becomes a *test* of the recorder itself.

**Approval point.** **YES — this is the foundation for time-travel +
LLM contract. Sanity-check effort vs value before continuing.**

### P4 — Cross-emulator differential + time-travel queries (5–6 days)

The fuzz/differential research called this **the single highest-ROI
addition**: "any time a property fails on PyBoy, you can immediately
answer 'is this our bug or a PyBoy emulation bug?' without human
work." [SameBoy](https://sameboy.github.io/) is the de-facto
reference (passes Mooneye, Wilbert Pol, blargg; >99.9% on ~2800
games). Per §11.3, **VBA-M is the fourth backend** — the user's
play emulator — so cross-emu reports four columns.

**Deliverables.**

- SameBoy + gambatte + **VBA-M** subprocess backends in
  `tools/debugger/kernel/backends/`. VBA-M is parity-only:
  savestate load + frame tick + memdump; no breakpoints (its CLI
  surface doesn't expose them reliably).
- Cross-emu diff harness: same scenario, N emulators, diff
  `(WRAM, regs)` hash every frame; first divergence → byte-diff to
  show *exactly which addresses* started to differ. This is
  Replay.io's "earliest divergence" pattern.
- **Conformance trust gate**: run [Blargg + Mooneye + SameSuite +
  Mealybug + dmg-acid2 + cgb-acid2](https://github.com/c-sp/gameboy-test-roms)
  on every backend before we trust it. Mooneye uses the Fibonacci
  success convention (B=3,C=5,D=8,E=13,H=21,L=34 after `ld b,b`) —
  trivially scriptable. The conformance gate runs as part of CI for
  every backend update.
- Omniscient query DSL implementation over byte_history /
  call_history. Mini-language modeled on
  [Tralfamadore](https://www.dcs.gla.ac.uk/conferences/resolve12/papers/session4_paper1.pdf):
  composable operators (filter, project, join), backed by DuckDB over
  Parquet.
- Trace diff (run-vs-run) at byte-history precision.

**Exit.**

- `python -m tools.debugger crossemu --scenario physical_no_items` runs
  on PyBoy + SameBoy + gambatte, reports `wCurDamage` agreement.
- DSL query `bytes.first_writer(wCurDamage, after=BattleCommand_DamageCalc)`
  returns the (cycle, PC, source_label).
- Smoke runs ≤2 minutes for all backends.
- Mooneye + Blargg + SameSuite trust gate passes for each backend
  before any cross-emu result is trusted as authoritative.

**Risk.** SameBoy / gambatte integration may be painful (no Python
binding for either; subprocess + RPC has overhead). Mitigation: only
spawn alternate backends for explicit cross-emu runs, not every
scenario. PyBoy + audio-mixer floats / dict iteration order are known
determinism gotchas; the conformance gate is the floor.

**Approval point.** **YES — confirm cross-emu is worth the integration
cost. The user might say "PyBoy-only is fine."**

### P5 — Battle visualizer + damage chain diagram + multi-axis fuzz (4–5 days)

**Deliverables.**

- Player-facing damage chain diagram (markdown + HTML + SVG).
- Live battle state inspector — render mons + stages + status + weather.
- Multi-turn Hypothesis
  [`RuleBasedStateMachine`](https://hypothesis.readthedocs.io/en/latest/stateful.html)
  for battle scenarios: `@rule` decorators tag SwitchOut, UseMove,
  ApplyItem, EndTurn; `@invariant` decorators assert "HP within [0,
  MaxHP]", "no double Choice lock", "wEnemySpdLevel ∈ [7, 13]";
  `Bundle` carries active mons + learned moves across rules.
- [`hypothesis.target()`](https://hypothesis.readthedocs.io/) for
  guided search: emit `target(damage / oracle_damage - 1.0,
  label="damage_ratio_drift")` per test; Hypothesis runs simulated
  annealing toward worst-case drift, far better at finding
  overflow/clobber than random sampling.
- Mutation testing extended to Python oracle (DDMIN* + ProbDD).
- [Hierarchical Delta Debugging
  (HDD)](https://users.cs.northwestern.edu/~robby/courses/395-495-2009-fall/hdd.pdf)
  over scenario JSON tree (turns → moves → side effects): drop a
  whole turn first, then a move, then byte-level. Much faster
  convergence than vanilla ddmin.
- Metamorphic relations for damage:
  - **Symmetry**: `damage(A→B at +0/+0) == damage(B→A at +0/+0)`
    when species/moves/levels swap (ignoring asymmetric typing).
  - **Level monotonicity**: `damage(level=L) ≤ damage(level=L+1)`
    ceteris paribus.
  - **STAB monotonicity**: switching attacker type so the move becomes
    STAB never lowers damage.
  - **Stat-stage monotonicity**: more +Atk stages never produce less
    physical damage (modulo overflow — the bug we want to catch).
  - **Item invariants**: Choice Band locks move choice but never
    changes damage on the locked turn.
  - **Determinism**: same RNG seed + scenario → byte-identical WRAM at
    every checkpoint.
- **Third independent oracle** — wrap
  [`@smogon/calc` Gen 2](https://github.com/smogon/damage-calc) as a
  subprocess oracle. When all three (ROM, our Python oracle, Showdown
  calc) agree, ship; when two disagree, that's the bug-finding signal.
  Read Showdown's
  [gen2 mod README](https://github.com/smogon/pokemon-showdown/blob/master/data/mods/gen2/README.md)
  for known GSC differences before trusting parity.
- **Hidden-info leak as a metamorphic relation** (the North Star
  rule): replay a turn with two WRAMs — one with true enemy party,
  one with public-knowledge-only party. Boss AI decision must be
  identical. Any divergence = AI peeked. Pure metamorphic, no oracle
  needed.

**Exit.**

- `python -m tools.debugger battle inspect --state morty_chosen_frame_5467.state`
  prints a one-page summary that a non-coder can read.
- `python -m tools.debugger battle damage CROBAT:44 ALAKAZAM:44 WING_ATTACK --explain`
  produces the player-facing diagram.
- New multi-turn fuzz finds at least one previously unknown edge case
  (verifiable retro: re-run an old commit and confirm fuzz catches a
  known historical bug).
- Showdown-calc oracle wired up; all three oracles agree on the
  fuzz corpus.

**Risk.** Low. Layered on existing matchup CLI + clobber smoke.

**Approval point.** No.

### P6 — Source-level frontend (VS Code DAP) + save-state lab (5–7 days)

**Deliverables.**

- DAP server in `tools/debugger/presentation/dap/`.
- VS Code launch.json snippet documented in `docs/build.md`.
- Source-line map from RGBDS object files.
- Breakpoint / watchpoint / step / step-back / watch-expression
  support.
- Save-state lab: VBA `.sgm` decoder promoted from legacy, two-way
  conversion to PyBoy `.state`, field-by-field diff.

**Exit.**

- User can open `engine/battle/effect_commands.asm` in VS Code, set a
  breakpoint on `BattleCommand_DamageCalc`, hit F5, and step. The
  watch panel shows `wBattleMonHP`, `wCurDamage`, decoded stat stages.
- User can drag a player-submitted `.sgm` onto the debugger CLI and
  get a "what's in this save" report in <2s.

**Risk.** Medium. DAP is well-documented but writing one is a
weekend's work. Worth it for the rest of the UX.

**Approval point.** **YES — DAP is significant investment. Check user
preference between DAP/VS Code and a standalone TUI first.**

### P7 — Whole-ROM static analyzer (5–7 days)

**The keystone analysis is `infer_register_summary.py`** — per the
static-analysis research, this single piece of infrastructure
(~600–800 LOC, backwards abstract interpretation over an 8-register
lattice + memory effects) unlocks 4 of the 8 highest-value audits
without any IR framework, Capstone, angr, or Ghidra dependency. Build
this first; the rest of the static analyzer falls out of it.

Calling convention summary per function: `(uses, defs, preserves)`
over `{A, B, C, D, E, H, L, F}` plus memory effects. Fixed-point over
the call graph. Literature: Balakrishnan & Reps's CodeSurfer/x86 +
VSA is the canonical reference; for stack and clobber summaries
specifically, [Regehr et al.'s microcontroller stack-bounds
paper](http://web.cs.ucla.edu/~palsberg/course/cs239/S04/papers/RegehrReidWebb03.pdf)
is the closest precedent on tiny architectures.

**Deliverables.**

- Project-wide static model in `tools/debugger/analysis/static/`.
- **`infer_register_summary.py`** — backwards abstract interpretation,
  per-function summaries to `.cache/regsummaries.json`. The keystone
  dependency for items below.
- `check_farcall_register_clobber.py` — merges
  `check_farcall_hl_clobber.py` + `check_farcall_a_clobber.py` once
  summaries exist; drops the marker-comment hack.
- `check_abi_drift.py` — diffs regsummaries vs `regsummaries.lock`;
  requires explicit unlock to update. Catches the **transitive
  AG-NN clobber class** statically — same bug class the
  damage_debugger catches dynamically.
- **`check_save_format_lock.py`** — hash (label, offset, size) tuples
  for every symbol in `SRAM*`/`WRAM*` sections from `.sym`+`.map`,
  compare against `save_format.lock` committed to git. CI fail on
  mismatch unless `SAVE_FORMAT_VERSION` bumped in same commit.
  Highest-ROI-per-LoC analysis on the entire list.
- `check_stack_bounds.py` — whole-program reachable call graph from
  `Main` + each interrupt handler; per-function local stack usage
  (counts `push`, `call`, `rst`, `dec sp`); worst-path Bellman-Ford
  to flag any path that could overflow the stack region. Interrupts
  add a frame on every cycle, so worst-path adds their depth.
- `check_bank_freespace_gate.py` — promote dev_index thresholds to
  hard CI; read post-link `.map`, fail PR if any tight bank's free
  bytes dropped below threshold without justification.
- `lint_hram_ldh.py` — token lint, regex over symbol table.
- `lint_bank_balance.py` — structural lint for `push af` /
  `pop af` pairing around `ld [hROMBank], a` / `ld [$2000], a`.
- `check_debug_opcodes.py` — warn if `ld b,b` / `ld d,d` ships in
  release build (per §4.18).
- Dead-code / unreferenced-label scanner.

**Exit.**

- `python -m tools.debugger static analyze` produces a single report
  with every static finding, severity-ranked.
- `python -m tools.debugger static clobber-summary
  BattleCommand_DamageCalc` returns its inferred clobber set, matching
  hand-validated ground truth for ~10 reference functions.
- The merged `check_farcall_register_clobber.py` replaces both
  existing farcall audits in the release-smoke floor.
- `save_format.lock` is committed; any `ram/` field reorder fails CI
  without a `SAVE_FORMAT_VERSION` bump.

**Risk.** Medium. Abstract interpretation on SM83 is approachable but
non-trivial. Mitigation: validate with hand-checked clobber sets for
~10 known functions; AG-NN audits and the damage_debugger remain the
dynamic regression backstop.

**Won't build.** Custom SLEIGH spec (GhidraBoy exists), angr SM83
lifter (multi-month investment, bug density doesn't justify it),
Capstone backend (we have source, not bytes). All explicit
**rejected-with-reason** in the research bibliography.

**Approval point.** No.

### P8 — Stress / soak + bisect + differential against vanilla (4–6 days)

**Deliverables.**

- Trainer tournament simulator.
- Wild encounter fuzz across all Johto/Kanto routes.
- Save-load loop soak.
- `python -m tools.debugger bisect --scenario X --good <commit>
  --bad HEAD` — git bisect with the criterion "scenario output
  matches `good`."
- Vanilla pokegold ROM in `audit/debugger/baseline/vanilla/` (built
  from upstream pret).
- Differential against vanilla: parity-preserving scenarios must match
  byte-for-byte where applicable.

**Exit.**

- Bisect a synthetic regression in <60s by finding the offending
  commit.
- Vanilla diff for an "unchanged subsystem" (e.g., overworld map
  scripts) produces zero diffs.
- Trainer tournament runs all canonical trainers, reports coverage +
  zero crashes.

**Risk.** Vanilla baseline ROM needs to be tracked; we don't want to
keep checking in built ROMs. Mitigation: a tiny `scripts/build_vanilla.py`
that pulls upstream and builds it on-demand, with hash check.

**Approval point.** No.

### P9 — Graphics / overworld / audio scopes (5–7 days)

**Deliverables.**

- VRAM tile viewer, OAM viewer, BG map viewer.
- Tilemap diff per frame.
- Palette viewer.
- Map script tracer (steps `engine/overworld/scripting.asm` commands).
- Event flag explorer (named-flag decode).
- Map transition tracer.
- Audio register snapshot + music position tracker.

**Exit.**

- Reproduces the May 2026 VBA tile jumble class symptom in PyBoy +
  VRAM viewer.
- `python -m tools.debugger map flags --diff <state1> <state2>`
  shows the named flag delta.

**Risk.** Low. PyBoy already exposes VRAM/OAM/IO; this is mostly
presentation.

**Approval point.** No.

### P10 — Web UI + experiment store + coverage in PR (5–7 days)

**Deliverables.**

- FastAPI backend + Svelte 5 frontend.
- Decision waterfall view.
- Time-travel scrubber.
- Battle visualizer.
- Run-vs-run comparison.
- DuckDB queries from the web UI.
- Coverage badges + summaries for PR review.

**Exit.**

- `python -m tools.debugger web --port 8765` starts the UI.
- A scenario run produces a shareable URL (local).
- PR comment posts a "coverage delta" table.

**Risk.** Medium. Frontend work is its own discipline; the user has
asked for Svelte 5 elsewhere; we mirror that.

**Approval point.** **YES — web UI is a big surface. The user might
say "TUI is enough, defer web."**

### P11 — LLM-assisted hypothesis tracker (3–5 days)

**Deliverables.**

- `audit/hypothesis_tree.jsonl` — every debug session's hypotheses,
  with verifications + outcomes.
- `tools/debugger/llm/hypothesis_tracker.py` — CLI for adding /
  refining hypotheses; auto-prompts the LLM with the symbol service.
- Citation grounder — LLM claims must cite file:line.
- Symbol-aware autocomplete (a small JSON service Claude can query).
- Scenario synthesis — LLM proposes Hypothesis strategies for ad-hoc
  bug classes; user reviews and accepts.

**Exit.**

- Three real bug hunts use the tree, each with at least one verified
  hypothesis and one rejected hypothesis recorded.
- Citation grounder rejects any LLM output without a verifiable
  source cite.

**Risk.** Low — the LLM is collaborative, not authoritative. We're
just persisting state.

**Approval point.** No.

### P12 — Polish, performance, definition-of-done (3–5 days)

**Deliverables.**

- Performance pass: hot-loop profiling, persistent emulator pool, byte
  history snappy + delta + dictionary encoded.
- Documentation: `docs/debugger_user_guide.md` with task-recipe
  examples.
- Self-test: every component has a self-test entry, all in one
  `python -m tools.debugger selftest`.
- Final integration with §6 verification floor: the debugger is the
  floor.

**Exit.**

- Definition-of-done in §9 satisfied.
- Verification floor is the debugger floor.

**Approval point.** **YES — declare done.**

### Phase summary

| Phase | Days | Risk | Approval |
| --- | --- | --- | --- |
| P0 — Plan + baseline (approved 2026-05-16) | 1 | None | ✅ DONE |
| P1 — Symbol + state | 3–4 | Low | No |
| P2 — Tracing & macros | 4–5 | Medium | No |
| P3 — Event store + omniscient + MCP | 5–7 | Medium-high | **YES** |
| P4 — Cross-emu (4 backends) + time-travel | 5–6 | Medium | **YES** |
| P5 — Battle viz + multi-axis fuzz | 4–5 | Low | No |
| P6 — DAP / VS Code + save lab (incl. VBA `.sgm` promotion) | 5–7 | Medium | **YES** |
| P7 — Static analyzer (register-summary keystone) | 5–7 | Medium | No |
| P8 — Stress + bisect + vanilla diff | 4–6 | Low | No |
| P9 — Graphics / overworld / audio | 5–7 | Low | No |
| P10 — Web UI + experiment store | 5–7 | Medium | **YES** |
| P11 — LLM hypothesis tracker (persistence + citation only) | 3–5 | Low | No |
| P12 — Polish | 3–5 | Low | **YES (done)** |
| **Total** | **51–75** | | |

That's ~10–15 weeks at "one focused Claude day per calendar day."
Realistically with batching and overlap, **8–12 weeks** of wall time.

User confirmed full P0–P12 commit on 2026-05-16. P0 closed
(approval-by-AskUserQuestion). P1 unblocked for next session.

## 8. Risk Register

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| PyBoy is the only Python-native GB emulator; if its accuracy diverges from real hardware on a feature we ship, we won't notice | Medium | High | P4 cross-emu diff; SameBoy + gambatte as accuracy references; Blargg/Mooneye conformance check on every backend before trust |
| Event store grows unbounded for long traces | High | Medium | Subscription-based capture; configurable filters; snappy + delta + dictionary encoding; cold-storage rotation under `audit/debugger/trace_archive/` |
| DAP server work is significant for a single-developer tool | Medium | Medium | Optional phase (P6 has approval gate); TUI fallback covers same workflow with less polish |
| Static-analysis abstract interpretation is wrong (false positives / negatives) | Medium | High | Hand-validate against ~10 known clobber sets; AG-NN audits are the regression test |
| Save-format migration scaffolding lulls us into shipping format changes without user approval | Low | Critical | Explicit `SAVE_FORMAT_VERSION` gate; user-approval label on save-format changes is still required; migration scaffolding only helps once approved |
| Web UI / Svelte frontend becomes its own maintenance burden | Medium | Medium | Keep frontend small + zero-build (Vite dev server during dev, single static bundle for "ship"); CLI must stay first-class |
| LLM hypothesis tracker becomes a noise generator with low-signal hypotheses | Medium | Low | Tree entries require a verification step; unverified hypotheses are pruned automatically |
| Tooling sprawl: too many entry points to remember | Medium | Medium | Single `python -m tools.debugger ...` umbrella; every existing tool remains accessible at its old entry point too (backwards-compat) |
| User's pacing differs from this 8–12-week estimate | High | Low | Phases are independent enough to pause between any pair; P0–P3 are the foundation, the rest is opt-in |
| Boss AI SOTA plan ([2026-05-15](boss_ai_debugger_state_of_art_implementation_plan_2026-05-15.md)) overlaps with this roadmap | High | Low | This roadmap absorbs the boss plan as P5/P7/P10/P11 components; the boss SOTA plan stays canonical for boss-specific details |
| Cross-emu integration overhead (SameBoy/gambatte are not Python-native) | High | Medium | RPC over subprocess stdin/stdout; emulators only spawned on demand for explicit cross-emu runs |
| Boundary between "debugger" and "audit" blurs | Medium | Low | Audits are point-in-time pass/fail; debugger is interactive + investigative. Audits call into the static analyzer for shared logic |
| Damage debugger's existing CLI gets renamed / breaks user muscle memory | Low | Medium | All existing entry points stay; umbrella is additive |
| Performance regression in batch scenarios when adding instrumentation | High | Medium | Subscription-based filters; default to "no events emitted" except for active subscribers; profiling pass in P12 |

## 9. Success Metrics

### 9.1 Behavioral

- **Selector replay**: 100% on every recorded live trace.
- **Pre-choice replay**: ≥99.99%, target 100%.
- **Damage chain ROM-vs-oracle**: ≥99.99% on every fuzz pass.
- **Cross-emu agreement (PyBoy ↔ SameBoy ↔ gambatte)**: 100% on
  every smoke scenario; ≥99% on every fuzz pass (discrepancies
  flagged + investigated).
- **Coverage**: 100% of reachable rule IDs covered by at least one
  scenario; 100% of damage-chain PCs covered.

### 9.2 Diagnostic

- **From symptom to localized fix candidate in ≤5 minutes** for the
  AG-NN class of bug (register clobber). The current debugger does
  this for the May 2026 5x bug; we should preserve that.
- **From symptom to localized fix candidate in ≤30 minutes** for a
  novel bug class (one we haven't tooled for). LLM hypothesis tracker
  + omniscient query + static analyzer is the toolchain.

### 9.3 Review

- **Top-N review queue has <10% lesson-spam duplication** (already
  hit by boss_ai_debugger; preserve).
- **Every high-severity mismatch has**: minimized repro,
  counterfactual answer-changing change, mastery citation.

### 9.4 Performance

- **Non-ROM scenario triage**: ≥1,000,000/minute.
- **Pure selector replay**: ≥1,000,000/minute.
- **Python scoring**: ≥5,000,000/minute.
- **ROM-backed replay**: ≥10,000/minute (stretch 100,000).
- **Single scenario w/ full event store**: ≤2s end-to-end.
- **Project-wide static audit**: ≤30s.
- **Source-level breakpoint hit**: <100ms latency on F5/F10/F11.
- **Omniscient byte-history query**: <100ms for any address over a
  5-minute scenario.

### 9.5 Trust

- **Every behavior-changing commit can produce a before/after
  behavior diff** (run-vs-run via the experiment store).
- **Every trace artifact records**: ROM hash, symbols hash, source
  commit, seed, scenario id.
- **No silent emulator divergence**: if an emulator's output deviates,
  it surfaces as a failed conformance check, not as a hidden
  inconsistency.
- **No silent save-format drift**: every `ram/` change is checked
  against `SAVE_FORMAT_VERSION`; the debugger flags it.

### 9.6 First-Playthrough Promise

- **Hidden-info leak rate in Boss AI: zero**. The metamorphic suite
  proves it.
- **Haki uses are authored, traced, and explainable in plain
  English**. The live Haki tracker surfaces them.
- **Decision waterfalls render in player-facing language** ("Morty
  wants to stop your Rapid Spin because he saw it last turn"), not
  asm.

### 9.7 The "Single Command" definition-of-done

After any non-trivial AI / battle-engine / save-format / overworld
change, one command should produce:

```
python -m tools.debugger run-suite --since-last-good
```

…and the output answers, in order:

1. Did the build link? (`make`)
2. Does the trace ROM still match the manifest? (existing audit)
3. Do all release-smoke audits pass? (existing audit)
4. Does the damage chain still match the oracle? (`clobber_smoke`)
5. Does the boss AI still match its selector / pre-choice replays?
6. Does the static analyzer flag any new findings? (clobber inference,
   save drift, bank pressure, dead code, macro safety)
7. Does any cross-emu scenario disagree? (P4)
8. Does vanilla pokegold diff still match for unchanged subsystems?
9. What does the run-vs-run diff say changed? Decoded in named
   fields, not hex.
10. If anything is red, what's the top-ranked review item?

If steps 1–8 are green and step 9 says nothing surprising changed,
the change is **safe to commit by the user's senior-dev contract**.
Otherwise, present the failures with localized fix candidates.

That's the bar.

### 6.5 Order of integration

Research consensus on integration order (UI/LLM agent):

1. **MCP server first** — unlocks Claude as power user immediately.
2. **CLI + Markdown reports** — every investigation becomes a
   committed artifact.
3. **Web UI** — only the views CLI can't serve (timeline scrubber,
   VRAM/OAM viewers, dataflow follow-the-byte).
4. **DAP / VS Code** — last; depends on the kernel + state + symbol
   service being stable.

This is the inverse of "build the UI first and bolt automation on
later." For a single-developer tool with Claude as collaborator, the
LLM contract is the primary surface.

## 10. Bibliography

The agents I asked to research each topic returned URLs as part of
their reports. Authoritative pointers below; full agent reports under
[`audit/debugger/research/`](../audit/debugger/) once the corresponding
phase ships.

### 10.1 Game Boy / GBC debuggers

- BGB — <https://bgb.bircd.org/>
  - BGB manual — <https://bgb.bircd.org/manual.html>
  - BGB on gametechwiki — <https://emulation.gametechwiki.com/index.php/BGB>
- SameBoy — <https://sameboy.github.io/>
  - SameBoy debugger reference — <https://sameboy.github.io/debugger/>
  - SameBoy downloads — <https://sameboy.github.io/downloads/>
  - SameBoy source — <https://github.com/LIJI32/SameBoy>
- Emulicious — <https://emulicious.net/>
  - Emulicious debugger docs —
    <https://emulicious.net/documentation/debugger/>
  - VS Code extension —
    <https://marketplace.visualstudio.com/items?itemName=emulicious.emulicious-debugger>
  - emulicious-debugger source (Calindro) —
    <https://github.com/Calindro/emulicious-debugger>
- mGBA — <https://mgba.io/>
  - mGBA scripting docs — <https://mgba.io/docs/scripting.html>
  - mGBA Lua scripting blog (2022) —
    <https://mgba.io/2022/05/29/scripting/>
  - mGBA source — <https://github.com/mgba-emu/mgba>
- Mesen2 — <https://github.com/SourMesen/Mesen2>
  - Mesen2 Lua API —
    <https://github.com/SourMesen/Mesen2/blob/master/UI/Debugger/Documentation/LuaDocumentation.json>
  - Mesen2 debug docs — <https://www.mesen.ca/docs/debugging.html>
- no$gba / NO$GMB — <http://problemkaputt.de/gba-dev.htm>
  - NO$GMB breakpoints & debug messages —
    <https://retroscience.net/gameboy-breakpoints-and-debug-messages-in-no$gmb.html>
- Gambatte — <https://github.com/sinamas/gambatte>
- Gearboy (MCP-enabled) —
  <https://github.com/drhelius/Gearboy>
- gameroy (Rust) — <https://github.com/Rodrigodd/gameroy>
- binjgb (WASM cycle-accurate) — <https://github.com/binji/binjgb>
  - binjgb rewind post — <https://binji.github.io/posts/binjgb-rewind/>
- PyBoy — <https://github.com/Baekalfen/PyBoy>
  - PyBoy docs — <https://docs.pyboy.dk/>
  - PyBoy MCP server — <https://mcpmarket.com/server/pyboy>
- VBA-M — <https://vba-m.com/>
  - VBA-M source — <https://github.com/visualboyadvance-m/visualboyadvance-m>
  - VBA `.sgm` savestate format (referenced from `memory/reference_vba_sgm_format.md`)
- rgbds-vscode (DonaldHays) —
  <https://github.com/DonaldHays/rgbds-vscode>
- hgb-vscode (Hawkbat) — <https://github.com/Hawkbat/hgb-vscode>
- pret/pokegold disassembly — <https://github.com/pret/pokegold>
- RGBDS — <https://rgbds.gbdev.io/>
  - RGBDS `.sym` format — <https://rgbds.gbdev.io/sym>
  - rgblink — <https://rgbds.gbdev.io/docs/v0.4.2/rgblink.1>
- gbdev wiki — <https://gbdev.io/>
- awesome-gbdev emulator list —
  <https://github.com/gbdev/awesome-gbdev/blob/master/EMULATORS.md>
- Pan Docs — <https://gbdev.io/pandocs/>
- Game Boy CPU (SM83) instruction set —
  <https://gbdev.io/gb-opcodes/optables/classic>
- Gekkio Game Boy Complete Technical Reference —
  <https://gekkio.fi/files/gb-docs/gbctr.pdf>

### 10.2 Time-travel / record-replay

- rr — <https://rr-project.org/>
  - rr chaos mode (O'Callahan) —
    <https://robert.ocallahan.org/2016/02/introducing-rr-chaos-mode.html>
  - rr ACM Queue article — <https://queue.acm.org/detail.cfm?id=3391621>
  - "Engineering Record And Replay For Deployability" —
    <https://www.usenix.org/conference/atc17/technical-sessions/presentation/o-callahan>
- Pernosco — <https://pernos.co/>
  - Pernosco basics — <https://pernos.co/about/basics/>
  - Pernosco vision — <https://pernos.co/about/vision/>
  - Pernosco dataflow — <https://pernos.co/about/dataflow/>
  - Pernosco related work — <https://pernos.co/about/related-work/>
  - Pernosco vs gdb — <https://pernos.co/about/gdb/>
  - Visualizing Program State (SCAM 2025) —
    <https://conf.researchr.org/details/scam-2025/scam-2025-plenary-events/2/Visualizing-Program-State-in-the-Pernosco-Debugger>
- WinDbg TTD —
  <https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/time-travel-debugging-overview>
  - TTD ecosystem deep-dive (Elastic) —
    <https://www.elastic.co/security-labs/deep-dive-into-the-ttd-ecosystem>
- UndoDB LiveRecorder —
  <https://undo.io/solutions/products/live-recorder/>
- Replay.io — <https://www.replay.io/>
  - Replay time-travel internals —
    <https://docs.replay.io/basics/time-travel/how-does-time-travel-work>
  - Replay timeline annotations —
    <https://docs.replay.io/basics/replay-devtools/time-travel-devtools/timeline-annotation>
- gdb process-record —
  <https://sourceware.org/gdb/current/onlinedocs/gdb.html/Process-Record-and-Replay.html>
- Mesen2 rewind discussion —
  <https://forums.nesdev.org/viewtopic.php?t=13844>
- TARDIS paper (time-travel for managed runtimes) —
  <https://earlbarr.com/publications/tardis.pdf>
- ReVirt (OSDI '02) —
  <https://www.usenix.org/conference/osdi-02/revirt-enabling-intrusion-analysis-through-virtual-machine-logging-and-replay>
- Tralfamadore (queryable execution traces) —
  <https://www.dcs.gla.ac.uk/conferences/resolve12/papers/session4_paper1.pdf>
- Xen-TT (VEE '16) —
  <https://users.cs.utah.edu/~regehr/papers/vee16-xentt.pdf>
- Snapshot compression (Gaffer on Games) —
  <https://gafferongames.com/post/snapshot_compression/>
- LSM-tree primer — <https://en.wikipedia.org/wiki/Log-structured_merge-tree>

### 10.3 Property / fuzz / differential testing

- Hypothesis — <https://hypothesis.readthedocs.io/>
  - Hypothesis state machines —
    <https://hypothesis.readthedocs.io/en/latest/stateful.html>
  - Rule-based stateful testing (hypothesis.works) —
    <https://hypothesis.works/articles/rule-based-stateful-testing/>
  - Targeted PBT (Hypothesis #1779) —
    <https://github.com/HypothesisWorks/hypothesis/issues/1779>
- Agentic property-based testing (Anthropic Red, 2026) —
  <https://red.anthropic.com/2026/property-based-testing/>
  - Agentic PBT paper (arXiv) — <https://arxiv.org/abs/2510.09907>
- FuzzChick (coverage-guided PBT, POPL '20) —
  <https://lemonidas.github.io/pdf/FuzzChick.pdf>
- Notes on Hypothesis stateful testing (MacIver) —
  <https://www.drmaciver.com/2015/05/notes-on-the-implementation-of-hypothesis-stateful-testing/>
- fast-check model-based testing —
  <https://fast-check.dev/docs/advanced/model-based-testing/>
- quickcheck-state-machine —
  <https://hackage.haskell.org/package/quickcheck-state-machine>
- libFuzzer — <https://llvm.org/docs/LibFuzzer.html>
- AFL++ — <https://aflplus.plus/>
  - AFL++ binary-only fuzzing docs —
    <https://aflplus.plus/docs/fuzzing_binary-only_targets/>
  - AFLplusplus/unicornafl — <https://github.com/AFLplusplus/unicornafl>
  - Battelle/afl-unicorn — <https://github.com/Battelle/afl-unicorn>
- Fuzzing VBA-M with AFL++ (Bananamafia) —
  <https://bananamafia.dev/post/gb-fuzz/>
- DIFUZZRTL (S&P '21) —
  <https://lifeasageek.github.io/papers/jaewon-difuzzrtl.pdf>
- ProcessorFuzz (arXiv 2209.01789) — <https://arxiv.org/pdf/2209.01789>
- Csmith — <https://embed.cs.utah.edu/csmith/>
  - Csmith paper —
    <https://users.cs.utah.edu/~regehr/papers/pldi11-preprint.pdf>
- Game Boy test ROM aggregator (c-sp) —
  <https://github.com/c-sp/game-boy-test-roms>
- Mooneye test suite (Gekkio) —
  <https://github.com/Gekkio/mooneye-test-suite>
- SameSuite (LIJI32) — <https://github.com/LIJI32/SameSuite>
- Mealybug Tearoom (mattcurrie) —
  <https://github.com/mattcurrie/mealybug-tearoom-tests>
- dmg-acid2 — <https://github.com/mattcurrie/dmg-acid2>
- cgb-acid2 — <https://github.com/mattcurrie/cgb-acid2>
- ddmin —
  <https://www.st.cs.uni-saarland.de/zeller/projects/ddmin/index.html>
- DDMIN* (arXiv 2408.04735) — <https://arxiv.org/abs/2408.04735>
- DDMIN* fixed-point iteration evaluation (Wiley) —
  <https://onlinelibrary.wiley.com/doi/10.1002/smr.2702>
- Hierarchical Delta Debugging (HDD, Misherghi & Su) —
  <https://users.cs.northwestern.edu/~robby/courses/395-495-2009-fall/hdd.pdf>
- Reducing Failure-Inducing Inputs (Zeller, Debugging Book) —
  <https://www.debuggingbook.org/html/DeltaDebugger.html>
- Metamorphic testing —
  <https://en.wikipedia.org/wiki/Metamorphic_testing>
- Metamorphic testing of chess engines (ScienceDirect 2023) —
  <https://www.sciencedirect.com/science/article/pii/S0950584923001179>
- Daikon (dynamic invariant mining) —
  <https://plse.cs.washington.edu/daikon/pubs/invariants-tse2001-abstract.html>
- Test-oracle problem (Barr et al) —
  <https://discovery.ucl.ac.uk/id/eprint/1471263/>
- Pokemon Showdown damage-calc (third independent oracle) —
  <https://github.com/smogon/damage-calc>
- Pokemon Showdown gen2 mod README —
  <https://github.com/smogon/pokemon-showdown/blob/master/data/mods/gen2/README.md>
- Snapshot / golden testing overview (Widgetbook) —
  <https://docs.widgetbook.io/glossary/golden-tests>
- Soak testing definition (TechTarget) —
  <https://www.techtarget.com/searchsoftwarequality/definition/Soak-testing>

### 10.4 Static analysis & SM83 tooling

- Ghidra — <https://ghidra-sre.org/>
  - Ghidra P-Code reference —
    <https://ghidra.re/ghidra_docs/languages/html/pcoderef.html>
  - Working with Ghidra P-Code (River Loop) —
    <https://riverloopsecurity.com/blog/2019/05/pcode/>
  - Introduction to P-Code and SLEIGH (eShard) —
    <https://eshard.com/escoaching/Introduction-P-Code-and-GHIDRA-SLEIGH>
  - Creating a Ghidra processor module in SLEIGH (PT SWARM) —
    <https://swarm.ptsecurity.com/creating-a-ghidra-processor-module-in-sleigh-using-v8-bytecode-as-an-example/>
- GhidraBoy — <https://github.com/Gekkio/GhidraBoy>
- CTurt/GameBoy_GhidraSleigh —
  <https://github.com/CTurt/GameBoy_GhidraSleigh>
- bnGB Binary Ninja architecture plugin —
  <https://github.com/icecr4ck/bnGB>
- BNIL overview (Binary Ninja docs) —
  <https://docs.binary.ninja/dev/bnil-overview.html>
- BNIL MLIL — <https://dev-docs.binary.ninja/dev/bnil-mlil.html>
- Binary Ninja architecture plugins guide —
  <https://binary.ninja/2021/12/09/guide-to-architecture-plugins-part2.html>
- mgbdis (mattcurrie) — <https://github.com/mattcurrie/mgbdis>
- angr — <https://angr.io/>
  - angr docs (symbolic execution) —
    <https://docs.angr.io/en/latest/core-concepts/symbolic.html>
  - angr CFG recovery —
    <https://docs.angr.io/built-in-analyses/cfg>
  - angr-platforms custom lifter tutorial —
    <https://github.com/angr/angr-platforms/blob/master/tutorial/4_lifter.md>
- KLEE — <https://klee-se.org/>
- BAP — <https://users.ece.cmu.edu/~aavgerin/papers/bap-cav-11.pdf>
- Stack bounds analysis for microcontrollers
  (Regehr/Reid/Webb) —
  <http://web.cs.ucla.edu/~palsberg/course/cs239/S04/papers/RegehrReidWebb03.pdf>
- CodeSurfer/x86 (Balakrishnan & Reps) —
  <https://research.cs.wisc.edu/wpis/papers/cc04.pdf>
- Abstract Interpretation-Based Certification of Assembly Code
  (Springer) —
  <https://link.springer.com/chapter/10.1007/3-540-36384-X_7>
- Interactive Abstract Interpretation with Demanded Summarization
  (ACM TOPLAS) —
  <https://dl.acm.org/doi/full/10.1145/3648441>
- Interprocedural Control Flow Reconstruction (Springer) —
  <https://link.springer.com/chapter/10.1007/978-3-642-17164-2_14>
- pret/pokecrystal `home/farcall.asm` (reference for the macro
  semantics) —
  <https://github.com/pret/pokecrystal/blob/master/home/farcall.asm>
- pret/gb-asm-tools — <https://github.com/pret/gb-asm-tools>
- Pan Docs — <https://gbdev.io/pandocs/>
- Abstract interpretation — <https://en.wikipedia.org/wiki/Abstract_interpretation>

### 10.5 Modern debug UX & event models

- Debug Adapter Protocol —
  <https://microsoft.github.io/debug-adapter-protocol/>
- VS Code Debugger Extension guide —
  <https://code.visualstudio.com/api/extension-guides/debugger-extension>
- OpenTelemetry — <https://opentelemetry.io/>
- Apache Arrow — <https://arrow.apache.org/>
- DuckDB — <https://duckdb.org/>
- Tracy (frame profiler) — <https://github.com/wolfpld/tracy>
- Perfetto — <https://perfetto.dev/>
  - Perfetto UI docs — <https://perfetto.dev/docs/visualization/perfetto-ui>
  - Perfetto Swiss Army Knife (Lalit Maganti) —
    <https://lalitm.com/perfetto-swiss-army-knife/>
- rr 5.9 news — <https://github.com/rr-debugger/rr/wiki/News>
- GDB TUI multi-window layouts (Undo) —
  <https://undo.io/resources/enhance-gdb-with-tui/>
- GDB TUI Python custom windows (Red Hat) —
  <https://developers.redhat.com/articles/2022/08/03/add-custom-windows-gdb-programming-tui-python>
- Textual — <https://textual.textualize.io/>
- FastAPI — <https://fastapi.tiangolo.com/>
- FastAPI + Svelte real-time dashboard (TestDriven.io) —
  <https://testdriven.io/blog/fastapi-svelte/>
- Svelte — <https://svelte.dev/>
- MLflow — <https://www.mlflow.org/>
- Tauri vs Electron 2025 (DoltHub) —
  <https://www.dolthub.com/blog/2025-11-13-electron-vs-tauri/>
- Honeycomb frontend observability —
  <https://www.honeycomb.io/blog/introducing-honeycomb-for-frontend-observability>
- Sentry distributed tracing —
  <https://docs.sentry.io/concepts/key-terms/tracing/distributed-tracing/>
- Debugging in Jupyter (ML Journey) —
  <https://mljourney.com/debugging-code-like-a-pro-inside-jupyter-notebook/>

### 10.6 LLM-assisted debugging

- Model Context Protocol (MCP) — <https://modelcontextprotocol.io/>
- Anthropic computer use —
  <https://docs.claude.com/en/docs/build-with-claude/computer-use>
- DebugBench (Tian et al, 2024) —
  <https://arxiv.org/abs/2401.04621>
- Reflexion —
  <https://arxiv.org/abs/2303.11366>
  - Reflexion prompting guide —
    <https://www.promptingguide.ai/techniques/reflexion>
- Self-Debug (Chen et al) —
  <https://arxiv.org/abs/2304.05128>
  - Self-Debug ICLR paper —
    <https://proceedings.iclr.cc/paper_files/paper/2024/file/2460396f2d0d421885997dd1612ac56b-Paper-Conference.pdf>
- AutoCodeRover —
  <https://arxiv.org/abs/2404.05427>
  - AutoCodeRover repo —
    <https://github.com/AutoCodeRoverSG/auto-code-rover>
- LDB (Debug like a Human) review —
  <https://rileylearning.medium.com/paper-review-debug-like-a-human-a-large-language-model-debugger-via-verifying-runtime-execution-3872e931cf40>
- LLMDebugger / LDB repo —
  <https://github.com/FloridSleeves/LLMDebugger>
- TraceCoder (2026) — <https://arxiv.org/abs/2602.06875>
- LADYBUG: LLM Agent DeBUGger (EDBT 2025) —
  <https://openproceedings.org/2025/conf/edbt/paper-313.pdf>
- LLM4Decompile — <https://github.com/albertan017/LLM4Decompile>
- REx86 (local LLM for x86 RE) — <https://arxiv.org/html/2510.20975v1>
- ida-pro-mcp (canonical RE example) —
  <https://github.com/mrexodia/ida-pro-mcp>
- LLMs as RE sidekick (Cisco Talos) —
  <https://blog.talosintelligence.com/using-llm-as-a-reverse-engineering-sidekick/>
- AgenTracer (counterfactual replay) —
  <https://huggingface.co/papers/2509.03312>
- Deterministic replay for AI agents (Tian Pan, 2026) —
  <https://tianpan.co/blog/2026-04-12-deterministic-replay-debugging-non-deterministic-ai-agents>
- LLM-based agents for automated bug fixing (arXiv 2024) —
  <https://arxiv.org/html/2411.10213v2>

### 10.7 Internal references

- [docs/asm_authoring_guide.md](asm_authoring_guide.md) — the asm-authoring
  long-form source of truth; debugger output should cite sections of
  this guide (§3.2 farcall hl, §3.3 farcall a, §3.14 c-mirror).
- [docs/boss_ai_debugger_state_of_art_implementation_plan_2026-05-15.md](boss_ai_debugger_state_of_art_implementation_plan_2026-05-15.md)
  — Boss AI debugger SOTA plan; this roadmap absorbs it.
- [docs/project_context.md](project_context.md) — First-Playthrough
  Promise.
- [docs/project_roadmap.md](project_roadmap.md) — current workstream
  board.
- [docs/balance_intent.md](balance_intent.md) — what changed from
  vanilla; informs the differential vs vanilla pokegold (P8).
- [docs/mechanics_changes_from_base.md](mechanics_changes_from_base.md)
  — Gen-2-vs-modern reference; informs the metamorphic-relation
  oracle.
- [tools/damage_debugger/README.md](../tools/damage_debugger/README.md)
- [tools/boss_ai_debugger/README.md](../tools/boss_ai_debugger/README.md)
- [tools/trace/](../tools/trace/) — PyBoy state factory + trace
  pipeline.
- [tools/audit/](../tools/audit/) — static audit floor.

## 10.8 My recommended first cut (if the user says "go")

Per the act-then-report contract, here is the proposal I'd execute by
default unless told otherwise:

**Ship P0 → P3 as one phase block, then reassess.** Approximate
calendar: 2 weeks of focused work. Deliverables at the end of P3:

1. This roadmap doc (already shipped).
2. `tools/debugger/__init__.py` umbrella + index audit.
3. Unified symbol/state service consolidating
   `tools/damage_debugger/symbols.py` and
   `tools/boss_ai_debugger/state_schema.py` (no breakage —
   re-exports).
4. Macro-aware PC + register + memory tracer that publishes events to a
   bus.
5. Event store (JSONL → Parquet → DuckDB) + omniscient byte history
   over the (cycle, address) interval tree.
6. Free-run rolling rewind buffer with the forked-emulator query pool.
7. **MCP server with the initial 10-tool surface** (step, read_mem,
   set_breakpoint, run_scenario, query_history, run_audit, …).

That's the foundation every other phase depends on. After it ships,
the user can decide whether to invest in:

- P4 cross-emulator (high-ROI, ~5 days);
- P5 multi-axis fuzz + battle visualizer (low-risk, ~5 days);
- P6 DAP + VS Code (high effort, optional);
- P7 static analyzer (the AG-NN class catcher, high-leverage);
- P8 stress / soak / bisect / vanilla diff;
- P9 graphics / overworld / audio scopes;
- P10 web UI;
- P11 LLM hypothesis tracker.

The order then becomes a taste call informed by what proved most
useful in the P0–P3 block.

**Why this default and not "do everything serially":** P0–P3 is the
*kernel*. The rest are *layers*. Layers can be cherry-picked; the
kernel cannot. Ship the kernel first; bind to layers as the user's
appetite reveals itself.

**Why this default and not "P0–P1 only":** P0–P1 alone doesn't change
what we can ask the system. P3 is where the user (and Claude) can
start asking "what wrote `wCurDamage`?" and get a sub-second answer.
That's the threshold past which the debugger becomes worth using
versus the current toolset.

## 10.9 Interaction with the Pokemon Mastery Compounding Loop

The Pokemon Mastery
[Compounding Loop](pokemon_mastery/compounding_loop.md) runs as a
durable verifier-gated loop in parallel to engineering work. The
debugger and the mastery loop share infrastructure:

- The boss_ai_debugger
  [decision-trace](boss_ai_debugger_decision_trace.md) feeds mastery
  reviews; the unified decision waterfall (P5 + P10) replaces ad-hoc
  trace inspection in mastery review queues.
- Mastery scenarios are generated by
  [`tools/boss_ai_debugger generators`](../tools/boss_ai_debugger/generators.py);
  the run store under `audit/boss_ai_debugger/runs/` becomes a
  per-mastery-iteration artifact source.
- The hypothesis tracker (P11) is a natural home for mastery-loop
  hypotheses: each iteration's investigation becomes a tree entry,
  with verifications + outcomes persisted.

Compatible. The debugger roadmap does not block the mastery loop, and
the mastery loop does not block the debugger.

## 11. Resolved Decisions (2026-05-16, user-confirmed)

The original §11 listed open questions for P0 approval. The user
answered the consequential ones in-session; the answers are persisted
under `~/.claude/goal-state/.../decisions.jsonl` and summarized here.

### 11.1 Scope: full P0–P12 commitment

**Decision.** Bind to the full P0–P12 plan, not the P0–P3 first-cut
default in §10.8.

**Consequences.** Each phase's named approval gates remain in force —
P3, P4, P6, P10, P12 still pause for explicit user nod before
proceeding to the next phase. "Full commitment" means we won't
re-litigate the scope of the roadmap; it doesn't mean every phase
runs unsupervised.

### 11.2 UI primacy: Claude-centric

**Decision.** Primary surfaces are **MCP server + CLI + Markdown**.
TUI / Web UI / DAP remain in the plan as Phase deliverables but are
framed as Claude-centric: each renders rich artifacts that the user
*reviews* even if Claude doesn't interactively use them.

**Why.** The user delegated UI choice with "it's just for you (Claude)
to use, you decide." For Claude, the canonical surfaces are
programmatic (MCP), committed (Markdown), and one-shot (CLI). The
visual surfaces (TUI, Web, DAP) are still useful — they produce
shareable artifacts and the Web UI in particular is the natural home
for the dataflow panel and time-travel scrubber when the user wants to
inspect a long investigation.

**Effect on phases.** No phase removed. P6 (DAP + save lab) and P10
(Web UI + experiment store) keep their slots and approval gates;
they're flagged "(Claude-renders; user-reviews)" so the framing is
honest.

### 11.3 Cross-emulator: PyBoy + SameBoy + gambatte + **VBA-M**

**Decision.** Add VBA-M as a fourth cross-emulator backend.

**Why VBA matters.** The user plays the ROM in VBA. The accuracy
references (SameBoy, gambatte) tell us *"is the ROM right";* VBA-M
tells us *"does the ROM behave right for the player."* Both questions
are real. The May 2026 VBA tile jumble class proved divergence
between PyBoy and VBA is itself a bug class worth catching, not just
an emulator-quirk to dismiss.

**Effect on P4.** Four backends instead of three. VBA-M support is
intentionally lower-automation: savestate load (the `.sgm` decoder
already in
[tools/damage_debugger/legacy/](../tools/damage_debugger/legacy/)
promoted, in P6), frame tick via subprocess, memory dump on pause.
**No breakpoint integration** for VBA-M; it's a parity-check backend,
not an instrumentation backend.

**Effect on scenarios.** When `crossemu` runs in P4, it reports four
columns: PyBoy / SameBoy / gambatte / VBA-M. Disagreement between
SameBoy and gambatte = accuracy reference disagrees with itself (rare
but possible; investigate the test ROM conformance gate). Disagreement
between (SameBoy ∪ gambatte) and VBA-M = "the user sees something
different than the reference says they should" — that's the May 2026
class. Disagreement between PyBoy and the references = "PyBoy quirk;
do not trust this for that subsystem until corrected."

### 11.4 LLM hypothesis tracker: persistence + citation grounding only

**Decision.** P11 ships persistence + citation grounding only. No
autonomous hypothesis generation in V1.

**Why.** Conservative path. Citation grounding is the floor that
prevents the LLM from drifting into ungrounded claims; persistence
makes investigations survive session changes. Autonomous generation
can be added later (as V2 in a separate plan) if the persisted tree
shows the manual workflow is the bottleneck.

### 11.5 Vanilla pokegold differential

**Decision.** Keep in P8 as planned. Not directly asked but per the
"full commit" answer, defer trimming until P8's named approval gate.

### 11.6 Pacing

**Decision.** Bind to the 50–73-day estimate (8–12 weeks wall time
with batching). Re-evaluate at each phase approval gate.

---

The remaining lines of §11.1–§11.6 are the authoritative scope of
work. §10.8 is preserved as a historical record of the recommended
first-cut; it's no longer the active plan.

## 12. Appendix A — Recipe-style task examples

Concrete tasks and which capabilities they exercise. These are the UX
acceptance tests.

### A.1 "Damage is 5x what I expect"

(The May 2026 AG-NN class.)

```powershell
# Already works today:
python -m tools.damage_debugger.clobber_smoke

# After P3:
python -m tools.debugger trace --scenario physical_no_items --emit-events events.jsonl
python -m tools.debugger query 'bytes.first_writer(wCurDamage, since=BattleCommand_DamageCalc)'
# Returns: (cycle=1234567, PC=$70AB, source=BattleCommand_DamageCalc.do_add_high_byte)

# After P7:
python -m tools.debugger static clobber-summary ApplyLateGenDamageStatsItemMods_Far
# Returns: clobbers={a,c,h,l}; preserves={b,d,e}; warning="bc was preserved historically but recent edit clobbered c"

# After P11:
python -m tools.debugger llm hypothesize --symptom "physical damage 5x too high"
# Tree:
#   H1: AG-NN c-mirror bug recurrence
#     experiment: check_typepassive_c_mirror.py
#     result: FAIL
#     citation: docs/asm_authoring_guide.md §3.14
#     fix: add `push bc / pop bc` around `farcall TypePassive_GetEffectiveMoveCategory_Far` in ApplyLateGenDamageStatsItemMods_Far
#     confidence: 0.92
```

### A.2 "Boss AI picked an obviously bad move"

```powershell
# Already works today:
python -m tools.boss_ai_debugger inspect --fixture-id morty_chosen_frame_5467
python -m tools.boss_ai_debugger rom-contribution-trace --boss-route morty --json-out trace.json

# After P5:
python -m tools.debugger boss waterfall --state morty_chosen_frame_5467.state --candidate DREAM_EATER
# Renders the rule-by-rule score waterfall:
#   base_score:                  50
#   move.spikes.public_rapid_spin_risk:   +0  (no Spikes set)
#   move.ghost.dream_eater_floor:        -20  (player asleep prob: 0)
#   move.lookahead:                       -8  (deals 32% to active)
#   ...
#   final_score:                  22

# After P10 (web UI):
# Click "morty_chosen_frame_5467", scroll to "decision waterfall", hover over each rule for source citation.
```

### A.3 "I changed `ram/` and want to know if old saves break"

```powershell
# After P7:
python -m tools.debugger static save-drift --against codex/cleanup-gsc-rebalance-split
# Output:
#   wPartyMon1Stats offset shifted: was 0x36, now 0x38 (+2 bytes)
#   SAVE_FORMAT_VERSION: unchanged
#   ⚠ ESCALATE: save format change without version bump

# After P6:
python -m tools.debugger save load .local/player_provided.sav --format-version detect
# Output:
#   detected SAVE_FORMAT_VERSION: 0x07
#   current SAVE_FORMAT_VERSION: 0x07
#   ✓ compatible
#   --or--
#   ⚠ format version mismatch — save will be reformatted on load
```

### A.4 "I see a tile jumble in VBA"

```powershell
# Today: ad-hoc, see docs/graphics_emulator_debugging.md

# After P9:
python -m tools.debugger gfx replay --state vba_during_jumble.state --frames-around 30
# Output: per-frame BG map diff, OAM diff, VRAM tile diff.
# Highlights the rogue write: frame 5, $9800-$981F got "letter glyphs"
# from the text routine before WaitSFX completed.

# After P4:
python -m tools.debugger crossemu --state vba_during_jumble.state --frames 30
# Output: PyBoy + SameBoy + gambatte agree; the bug is real, not emu-specific.
```

### A.5 "Did this commit break anything I care about?"

```powershell
# After P3 + P8:
python -m tools.debugger run-suite --since HEAD~1
# Output:
#   - Build: ✓
#   - Audits (43): ✓
#   - Damage smoke: ✓
#   - Boss selector replay: ✓ (100%)
#   - Static analyzer: ✓ (no new findings)
#   - Cross-emu (smoke): ✓
#   - Vanilla diff (unchanged subsystems): ✓
#   - Run-vs-run diff (last commit on this branch):
#     - 0 selector mismatches
#     - 2 damage rolls changed within tolerance (acceptable)
#     - 0 unexpected changes in unchanged subsystems
#   - Top review queue: empty
#   ✓ SAFE TO COMMIT
```

That's the bar.

## 13. Appendix B — Migration guide (existing tools → unified debugger)

Concrete steps for moving existing tools into the umbrella *without
breaking them*.

### B.1 damage_debugger

**Before P1.** Standalone. Imports `pyboy`, `symbols`, `BootStateCache`
directly.

**After P1.** Imports `tools.debugger.kernel.symbol_service` via a
re-export shim in `tools/damage_debugger/symbols.py`:

```python
# tools/damage_debugger/symbols.py
from tools.debugger.kernel.symbol_service import SymbolTable, parse_sym
__all__ = ["SymbolTable", "parse_sym"]
```

**After P2.** Tracer publishes events to the bus instead of returning
frames. `clobber_smoke` subscribes to the same scenario's events; no
behavior change. New flag `--emit-events <path>` for streaming.

**After P3.** `damage_debugger.replay` becomes a thin wrapper around
the project-wide rolling rewind buffer.

**No-rename guarantee.** `python -m tools.damage_debugger.clobber_smoke`
keeps working forever. `python -m tools.debugger damage smoke` is the
new way; both dispatch to the same code.

### B.2 boss_ai_debugger

Same pattern. `python -m tools.boss_ai_debugger ...` keeps working;
`python -m tools.debugger boss ...` is the new alias.

The Boss AI SOTA plan's phases map to *this* plan's phases:

| Boss SOTA plan phase | This roadmap |
| --- | --- |
| 1 — Canonical state | P1 |
| 2 — Full scoring trace | already shipped (`rom_contribution_trace`) |
| 3 — Differential runner | already shipped (`diff`) |
| 4 — Generators & coverage | already shipped (`generate`, `coverage_report`) |
| 5 — Metamorphic & mutation | already shipped (`metamorphic`, `mutation`) |
| 6 — Counterfactuals, minimize, localize | already shipped |
| 7 — Mastery & active review queue | already shipped |
| 8 — Route evaluation | already shipped (`route_eval`) |
| 9 — Experiment store | extends into P3 (project-wide) |
| 10 — Change-adaptation suite | already shipped (`run-suite --profile changed-ai`) |

So most of the boss plan is in the bag. The remaining boss-specific
work folds into P5 (decision waterfall presentation) and P11 (LLM
hypothesis tracker over the existing artifacts).

### B.3 tools/audit/

Audits remain point-in-time pass/fail. They migrate over time to *call
into* the static analyzer (P7) for shared logic, but keep their own
entry points + pre-commit + release-smoke gates.

### B.4 tools/trace/

State factory + trace batch are kernel-layer functionality. They move
into `tools/debugger/kernel/save_io.py` and
`tools/debugger/kernel/trace_orchestration.py` in P1–P3, with
re-export shims at `tools/trace/`.

## 14. Appendix C — What's *out* of scope

To stop scope creep, this is the explicit "we are not building this":

- **Full Pokemon Crystal / Silver-only support.** Silver builds today;
  Crystal would need separate tracing infrastructure and is a
  different codebase. Out of scope.
- **Multi-player / link cable.** This is a single-player hack. Link
  battles are a small subset of the codebase; if/when needed, we add
  a P13.
- **Full Game Boy Advance support.** Different CPU (ARM7TDMI), different
  emulator. Out of scope.
- **Real-hardware deploy + debug.** USB → real cartridge instrumentation.
  Cool but out of scope.
- **Audio synthesizer / music editor.** GB music is its own discipline;
  we'll trace and inspect, not edit.
- **Sprite editor / tile editor.** Use existing tools (gbtdg, Online
  Game Boy Tile Editor).
- **Replacement for `make` / RGBDS.** We integrate; we don't replace.
- **A new emulator from scratch.** No. PyBoy / SameBoy / gambatte cover
  every accuracy point.
- **Multi-user / collaborative debugging.** Single-developer tool.
- **Hosted SaaS.** No. Localhost only. The user's data is private.
- **Mobile / iPad support.** No.
- **Distribution / packaging beyond `pip install -e .`.** No
  PyPI publication, no Tauri bundles, no Homebrew formulas.

## 15. Appendix D — One-page "I just want to debug X" cheat sheet

| Symptom | First command | If P-phase shipped |
| --- | --- | --- |
| Damage looks wrong | `python -m tools.damage_debugger.clobber_smoke` | + `python -m tools.debugger trace --scenario X` (P2) + `python -m tools.debugger query 'bytes.changes_in(wCurDamage)'` (P3) |
| Boss made a weird move | `python -m tools.boss_ai_debugger inspect --fixture-id X` | + `python -m tools.debugger boss waterfall` (P5) + web UI (P10) |
| Build fails / link error | Read the linker output; check `dev_index.md` bank pressure | + `python -m tools.debugger static bank-pressure` (P7) |
| Save load corrupts | `python -m tools.debugger static save-drift` (P7) | + `python -m tools.debugger save diff a.sav b.sav` (P6) |
| Cross-bank call hit garbage | `python tools/audit/check_cross_bank_call.py` | + `python -m tools.debugger static cross-bank` (P7) |
| Register clobber regression | `python -m tools.damage_debugger.clobber_smoke` | + `python -m tools.debugger static clobber-summary <fn>` (P7) |
| Graphics glitch | Read `docs/graphics_emulator_debugging.md` | + `python -m tools.debugger gfx replay` (P9) + cross-emu (P4) |
| Map script doesn't fire | grep `engine/overworld/scripting.asm` | + `python -m tools.debugger map trace` (P9) |
| "When did this byte change?" | grep + tracer manually | + `python -m tools.debugger query 'bytes.changes_in(<addr>)'` (P3) |
| "Did my last commit break anything?" | `make compare && python tools/audit/check_release_smoke.py` | + `python -m tools.debugger run-suite --since HEAD~1` (P8) |
| "Show me the AI's reasoning in English" | manually trace + read | + `python -m tools.debugger boss explain` (P11) |
| "Find me a Hypothesis strategy for this bug class" | hand-write | + `python -m tools.debugger llm synthesize` (P11) |

## 16. Conclusion

We have an unusually strong starting point: two mature debug
subsystems (damage + boss AI), a 40-script audit floor, deterministic
PyBoy harness, ROM contribution traces, mutation testing, metamorphic
relations, run stores, and ~14 months of asm-authoring lessons
encoded as audits.

What we don't have is a **unified** debugger that thinks of the whole
ROM hack as one system. This roadmap closes that gap in 8–12 weeks of
phased work, with explicit user-approval points at every major
investment.

The bar is the **single command** in §9.7: after any non-trivial
change, one command answers "is this safe?" with cited evidence in
language the user understands. Everything in this plan is in service
of that bar.

P0 was approved on 2026-05-16 (user committed to full P0–P12 plan via
AskUserQuestion; decisions logged in §11 and `decisions.jsonl`). P1
is unblocked for the next session — start with the unified symbol +
state service.
