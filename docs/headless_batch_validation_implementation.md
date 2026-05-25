# Headless batch validation — implementation handoff

For a fresh session picking up this work cold. Read this end-to-end
before touching anything.

---

## 1. The real goal

Build a workflow that lets us **test tons of board simulations quickly
against real boss-AI teams** to check the AI's logic reacts how we
expect.

The headless simulator is *infrastructure*. The actual deliverable is:
"give me a trainer + N boards + my expectations → tell me which
expectations hold and which don't, in milliseconds per scenario,
without booting PyBoy."

The chain is:

1. Batch validation against real boss AI teams
2. → smarter, well-tested Boss AI
3. → trainers that feel like real opponents (not cheat AI)
4. → veteran players actually have to think (the CLAUDE.md North
   Star: "restored uncertainty")

If anything you build can't be traced back to step 1, reconsider the
scope.

---

## 2. Where we are right now

Substantial infrastructure for a SINGLE trainer (Jasmine/
`shared_switch_loop`) and single-scenario use shipped this session
(2026-05-25). Eight commits on `master`, all with strict mutual-
verified handoff coverage:

| Commit | What it shipped |
|---|---|
| `0e0f8f51` | Ranged switch-roll `report_only` mode + `solo_claude_approved_by_cole` exception + path-scoped no-solo audit |
| `b46130c1` | Full Restore status cure ROM-component proof (closes a labelled boundary; tangential to batch workflow) |
| `0d28b079` | Scoping doc that surfaced "scenario JSON doesn't carry arbitrary board state — fixture is hardcoded" |
| `ccc107fb` | Slice A: fixture-match-or-reject headless→`family=switch_sack` exporter |
| `a0693131` | Slice B: parameterized `switch_materialization_patches` — species/types/HP/max_hp overrides |
| `9ea91d88` | Slice C-status: status byte overrides (burn / poison / paralyze) |
| `9ab0ac19` | Slice C-environment: weather + items + safeguard + nav-floor PDF whitespace fix |
| `848836fd` | Slice C-toxic-sleep: sleep_turns into status byte, SUBSTATUS_TOXIC bit on sub5 |

What works today:
- `headless_to_switch_sack_scenario(state, accept_overrides=True)`
  takes an arbitrary headless `BattleState` and produces a runnable
  `family=switch_sack` scenario dict — modulo stat stages / substitute /
  spikes / un-modelled sub-status bits (those still reject).
- `switch_materialization_patches(scenario)` reads the scenario's
  `overrides` dict to set ~20 WRAM fields beyond the legacy fixture
  defaults.
- The `boss_ai_switch_roll` headless action consumes the materialized
  switch_roll output (`materialized_exact_bridge`) or summarizes a
  ranged output (`ranged_report_only`).

What does NOT work yet:
- **Multiple trainers**: the materialization base state is locked to
  Jasmine via `BASE_ROUTE_TRAINER_CLASS = {"shared_switch_loop":
  "JASMINE"}` and a single save state in
  `audit/boss_ai_trace/live_capture_manifest.json`.
- **Batch runner**: today you call `rom_switch_materialize` per
  scenario and read the verdict by hand. No tool turns "trainer +
  N scenarios + expectations" into a pass/fail report.
- **Expectation schema**: nothing labels "Morty's Haunter should NOT
  switch to Gengar against neutral Shadow Ball pressure" in a
  machine-checkable way.
- **Board sweep generators**: `tools/boss_ai_debugger/generators.py`
  emits synthetic-tagged scenarios, not "iterate over Morty's actual
  roster".
- **Remaining slice C-* fields**: stat stages, substitute, spike
  layers, other sub-status bits (NIGHTMARE / CONFUSED / ENCORED / etc).

Goal of this handoff: ship Phase 1 (batch runner) first, then
expectation framework, then board generators, then multi-trainer.

---

## 3. File map (read these in this order)

### Read first

- [`docs/headless_to_rom_switch_materialize_scoping.md`](headless_to_rom_switch_materialize_scoping.md) — the scoping pass that surfaced the
  fixture-hardcoding constraint and laid out slices A → B → C.
  Critical for understanding why slice A is fixture-match-or-reject.
- [`tools/headless_battle/README.md`](../tools/headless_battle/README.md) — the user-facing surface of the
  headless simulator. Tells you what's source-mirrored, what's
  ROM-differential-proven, what's out of scope.

### Core code (touch only with care)

- [`tools/headless_battle/simulator.py`](../tools/headless_battle/simulator.py) — the headless simulator
  (~5000 lines). `BattleState` / `PokemonState` dataclasses around
  line 200. `boss_ai_switch_roll_results` (line ~3225),
  `boss_ai_switch_roll_source` (line ~3318) — these consume the
  materialized switch_roll output.
- [`tools/headless_battle/rom_switch_scenario_export.py`](../tools/headless_battle/rom_switch_scenario_export.py) — the exporter you
  just shipped. `headless_to_switch_sack_scenario(state, *,
  accept_overrides, ...)` is the entry point. Stays strict — any
  field outside fixture domain raises `SimulationInputError` with a
  named reason.
- [`tools/boss_ai_debugger/rom_switch_materialize.py`](../tools/boss_ai_debugger/rom_switch_materialize.py) — the
  PyBoy-backed materializer. `switch_materialization_patches`
  (line ~257) builds the memory-patch list from a scenario.
  `run_rom_switch_materialization` (line ~166) is the batch
  entry point. `RomSwitchReplaySession` (line ~69) drives PyBoy.
  Pay attention to `BASE_ROUTE_TRAINER_CLASS` and
  `SUPPORTED_FAMILIES` — both need extension for multi-trainer.
- [`audit/boss_ai_trace/live_capture_manifest.json`](../audit/boss_ai_trace/live_capture_manifest.json) — the source of
  base save states. Each capture has `save_state`,
  `pre_choice_state`, and optionally `switch_materialization_state`
  pointers. Multi-trainer support needs new entries here.
- [`tools/boss_ai_debugger/generators.py`](../tools/boss_ai_debugger/generators.py) — current scenario
  generator. `generate_scenarios(family="switch_sack", count, seed)`
  emits synthetic-tagged scenarios. Look here when wiring board
  sweep generators.

### Tests + audits (always extend these for new behavior)

- [`tools/headless_battle/tests/test_rom_switch_scenario_export.py`](../tools/headless_battle/tests/test_rom_switch_scenario_export.py) —
  20 unit tests covering exporter behavior. Mirror the pattern when
  adding tests for new fields.
- [`tools/boss_ai_debugger/tests/test_rom_switch_materialize.py`](../tools/boss_ai_debugger/tests/test_rom_switch_materialize.py) —
  19 tests covering materializer. Has the backward-compat byte-equality
  tests; extend them when adding new override fields.
- [`tools/audit/check_headless_battle_simulator.py`](../tools/audit/check_headless_battle_simulator.py) — the headless
  audit. Add new round-trip smokes here when you ship a new override
  field; pattern shown in the existing `rom_switch_scenario_export`
  + `rom_switch_scenario_export_overrides` sections.
- [`audit/omni_debugger_2026-05-24_handoff_log.jsonl`](../audit/omni_debugger_2026-05-24_handoff_log.jsonl) — the handoff
  log. Append-only. Strict event vocabulary (see §6 below).

### Audit infrastructure (you may need to touch)

- [`tools/audit/check_no_solo_commits_omni_debugger.py`](../tools/audit/check_no_solo_commits_omni_debugger.py) — enforces
  paired Claude/Codex review on omni-debugger commits. Scoped via
  `OMNI_DEBUGGER_PATHS` (line ~46). Accepts
  `solo_claude_approved_by_cole: true` on `slice_review` rows as
  an explicit Cole-granted solo bypass; same flag pattern as the
  existing `solo_codex_approved_by_cole`.
- [`tools/debugger/handoff_log.py`](../tools/debugger/handoff_log.py) — `is_mutual_verified` is the
  function the strict handoff audit uses. Has the same
  `SOLO_CLAUDE_APPROVAL_KEY` / `SOLO_CODEX_APPROVAL_KEY` logic.

### Existing reports / context

- [`docs/debugger_roadmap.md`](debugger_roadmap.md) — broader debugger roadmap (P0–P12).
- [`docs/llm_pairing_rules.md`](llm_pairing_rules.md) — Claude+Codex pairing protocol.
- [`tools/debugger/next_steps.py`](../tools/debugger/next_steps.py) — long `proof_limit` string at line
  ~332 enumerates what the headless slice currently covers. Update
  when you ship new mechanics.

### What to NOT touch

- `engine/`, `data/`, `ram/`, `constants/`, `home/`, `maps/`, `gfx/`,
  `audio/`, any `*.asm` — ROM source is read-only.
- `pokegold.gbc`, `pokegold_debug.gbc`, `pokegold.sym`, etc — build
  outputs.
- `audit/boss_ai_trace/*_live.txt` byte sequences — trace
  invariants. Refresh only via `tools/trace/` capture pipeline.

---

## 4. Git / worktree state

- **Branch**: `master`
- **Tip commit**: `848836fd debugger: toxic + sleep materializer overrides (slice C-toxic-sleep)`
- **Status**: clean (modulo expected dirty files from auto-generated
  trainer dossier PDF + auto-regen balance docs — these are noise).
- **Origin tracking**: `master...origin/master [ahead ~558]`. Do NOT
  push to origin without Cole's explicit ask — this branch
  intentionally diverges from `codex/cleanup-gsc-rebalance-split`.
- **Worktree**: no current worktree is needed. If you want to
  parallelize with Codex, use `git worktree add` for them.

### Recent commits to scan with `git log`

```
848836fd debugger: toxic + sleep materializer overrides (slice C-toxic-sleep)
9ab0ac19 debugger: env materializer overrides (slice C-environment) + pdf whitespace fix
9ea91d88 debugger: status-byte materializer overrides (slice C-status)
a0693131 debugger: parameterized switch_materialization_patches overrides (slice B)
ccc107fb debugger: fixture-match-or-reject headless->switch_sack scenario exporter
0d28b079 docs: scope headless-to-rom-switch-materialize exporter
b46130c1 debugger: Full Restore status cure ROM-component proof
0e0f8f51 debugger: ranged switch-roll report path + scope no-solo audit
```

### Git rules (per CLAUDE.md authority grant)

You have **full git authority** for this workstream: commit, log,
branch, tag without asking. Push to origin only on explicit ask.
Never force-push master. Never skip hooks. Always re-run the
verification floor before commit.

---

## 5. The roadmap to finish

Phases ordered by load-bearingness for the actual goal ("batch
validation against real boss AI teams"). Each phase is one or more
slice commits.

### Phase 1 — Single-trainer batch runner (do this first)

Build `python -m tools.headless_battle batch_switch_materialize`
(or extend the existing `tools.boss_ai_debugger`
`rom-switch-materialize` CLI). It should:

1. Take a `.jsonl` of scenarios (each already in
   `family=switch_sack` shape, produced by
   `headless_to_switch_sack_scenario` or hand-written).
2. Run them through `run_rom_switch_materialization` in one PyBoy
   session (the materializer already caches base-state bytes; reuse
   `RomSwitchReplaySession.run_in_one_session`).
3. Emit a table per scenario: `scenario_id`,
   `switch_confidence`, `switch_roll.switch_probability`,
   `switch_roll.probability_exact`, `proof_status`,
   `observation_status`.
4. Print a summary: `N scenarios, M observed switches, K
   probability_exact, errors=E`.
5. JSON-out path for downstream consumption.

Deliverables:
- `tools/headless_battle/batch_switch.py` (new module) OR extend
  `tools/boss_ai_debugger/rom_switch_materialize.py:main`
- Unit tests with mock PyBoy (skip if not feasible; integration test
  via the existing `RomSwitchReplaySession`)
- Audit smoke: 3-5 scenario batch end-to-end, asserting result shape
- README + `next_steps.py` updates
- Handoff log phase: `headless_battle_batch_switch_runner`

Smallest useful version: 5 scenarios in 30 seconds, table output. No
expectations yet — just "here's what the AI did for each board."

### Phase 2 — Expectation schema + comparator

Define a JSON schema for expectations per scenario:

```json
{
  "scenario_id": "morty_haunter_neutral_shadow_ball",
  "expected": {
    "action": "stay",              // or "switch"
    "switch_probability_max": 0.10  // optional bound
  },
  "rationale": "Neutral Shadow Ball isn't a converter; switching loses tempo"
}
```

Comparator wraps Phase 1:
- Reads `(scenarios.jsonl, expectations.json)`
- Runs batch
- For each scenario, marks the result `pass` / `fail` / `error`
- Prints a violation report

Deliverables:
- `tools/headless_battle/switch_expectations.py`
- Schema doc with examples
- Tests + audit smoke
- Handoff phase: `headless_battle_switch_expectations`

### Phase 3 — Board sweep generators

Take a real trainer roster from `data/trainers/parties.asm`
(parser already lives in `tools/boss_ai_debugger/role_packages.py`
or similar; check `parse_species_order` for the pattern) and emit a
sweep of boards. Variations to parameterize:

- Player species (caller-supplied list)
- Player HP (e.g., [100%, 60%, 30%])
- Player status (none / burn / poison / paralyze)
- Trainer active mon HP (same)
- Weather (none / rain / sun)
- Held items on either side

Each combination → one scenario via
`headless_to_switch_sack_scenario(accept_overrides=True)`.

Deliverables:
- `tools/headless_battle/scenario_sweep.py` with
  `sweep_against_trainer(trainer_name, player_options, ...)`
- Tests + audit
- Handoff phase: `headless_battle_scenario_sweep`

### Phase 4 — Multi-trainer support

Required for "tons of sims against boss AI teamS" (plural).

Steps:
1. Capture new base save states for other gym leaders / E4 via the
   `tools/trace/` pipeline. Each capture is a manual operation that
   feeds `audit/boss_ai_trace/live_capture_manifest.json`. **This
   step needs Cole's playtest seat** — escalate before starting.
2. Extend `BASE_ROUTE_TRAINER_CLASS` in
   `tools/boss_ai_debugger/rom_switch_materialize.py` to map each
   new base_route to its trainer class.
3. The Phase 3 sweep generator takes a `base_route` parameter and
   picks the right manifest entry per trainer.
4. Update Phase 1 batch runner to dispatch per base_route in one
   PyBoy session.

Handoff phase per trainer: `headless_battle_base_route_<trainer>_capture`.

### Phase 5 — Fill remaining slice C-* fields

These widen the board domain the exporter can represent. Each is
its own slice (commit pattern from today: ack_start → impl → tests
→ audit → slice_update → slice_review → phase_done).

- **Slice C-stages**: 5 stat stages per side (Atk / Def / Spe / SpA /
  SpD), base-7 encoded. WRAM fields like `wPlayerStatLevels`
  (offsets +0..+4). Headless exposes them as integers -6..+6 in
  `PokemonState.attack_stage` etc.
- **Slice C-substitute**: `wPlayerSubStatus4` SUBSTITUTE bit + a
  separate substitute-HP storage. Defer until callers actually need
  to debug Sub-related switch decisions.
- **Slice C-spikes**: spike layers encoded in
  `wPlayerScreens` / `wEnemyScreens` alongside SAFEGUARD. Needs the
  spike-layer encoding worked out from the source (see the
  `selected_spikes_entry_damage` source-mirroring in the simulator).
- **Other sub-status bits**: NIGHTMARE (sub1), CONFUSED (sub3),
  ENCORED / LOCK_ON / DESTINY_BOND / CANT_RUN / TRANSFORMED (sub5).
  Same pattern as the toxic bit shipped in `848836fd`.

Each slice mirrors the toxic-sleep template. Don't bundle more than
two related fields per commit.

### Out of scope for this handoff (Cole-call only)

- Live Boss-AI score generation (reimplement the Boss-AI scorer in
  Python). Multi-iteration project. Brief flagged it explicitly:
  "do not claim live Boss AI is solved."
- Full headless battle simulation that runs an entire turn through
  Boss-AI move + switch + item decisions without caller-supplied
  score bytes.
- Anything in `engine/` / `data/` / `ram/` / `*.asm`. ROM source is
  read-only.

---

## 6. Per-slice handoff discipline

Every commit on this workstream needs a handoff-log phase. **The
audit will reject your commit if you skip this.**

For each slice:

```jsonl
# 1. ack_start (before any code)
{
  "schema_version": 1,
  "phase": "<unique_phase_id>",
  "event": "ack_start",
  "status": "in_progress",
  "model": "claude",          // or "codex"
  "primary": "claude",         // matches model
  "reviewer": "claude",
  "confidence": "memory-derived",
  "signed_at": "<ISO 8601 UTC>",
  "claim": "<one paragraph: scope, what you'll touch, what's out of scope>",
  "write_set": ["tools/...", "audit/omni_debugger_2026-05-24_handoff_log.jsonl"],
  "safe_write_set_for_other": [],
  "collision_risk_files": []
}

# 2. slice_update (when code is done, before review)
{
  "schema_version": 1,
  "phase": "<same phase id>",
  "event": "slice_update",
  "status": "ready_for_review",
  "model": "claude",
  "primary": "claude",
  "reviewer": "claude",
  "confidence": "repo-proven",
  "signed_at": "<ISO 8601 UTC>",
  "claim": "<one paragraph: what shipped, what was verified, file-by-file summary>",
  "files_read": [...],
  "verification_replayed": [
    "python -m unittest ... -> N tests OK",
    "python tools/audit/check_headless_battle_simulator.py -> PASS",
    ...
  ]
}

# 3. slice_review (mutual sign-off, OR solo)
{
  "schema_version": 1,
  "phase": "<same phase id>",
  "event": "slice_review",
  "status": "slice_accepted",
  "model": "claude",           // when soloing AS Claude
  "primary": "claude",
  "reviewer": "claude",
  "confidence": "repo-proven",
  "signed_at": "<ISO 8601 UTC>",
  "claim": "<one paragraph: source anchors re-read, what's intentionally bounded, why it's safe>",
  "files_read": [...],
  "verification_replayed": [...],
  "solo_claude_approved_by_cole": true   // <-- only when Cole has explicitly approved solo work
}

# 4. phase_done
{
  "schema_version": 1,
  "phase": "<same phase id>",
  "event": "phase_done",
  "status": "phase_complete",
  "model": "claude",
  "primary": "claude",
  "reviewer": "claude",
  "confidence": "repo-proven",
  "signed_at": "<ISO 8601 UTC>",
  "claim": "<one paragraph: what's now possible, what's still future work>",
  "solo_claude_approved_by_cole": true
}
```

### Solo-Claude vs Codex-paired

Cole granted `solo_claude_approved_by_cole: true` for the current
session's slice work. **If you're not in that session, ask Cole
before setting the flag.** Without mutual Claude+Codex review OR
explicit Cole solo-approval, the no-solo audit rejects your commit.

For Codex-paired work: Codex writes the `slice_review` row, model is
"codex", primary stays "claude". See the existing PASS phases for
shape.

---

## 7. Verification floor (run after EVERY commit)

All 9 of these must pass. The brief codified them and the existing
session has held to it.

```bash
# 1. Scoped unit tests
python -m unittest \
  tools.boss_ai_debugger.tests.test_rom_switch_materialize \
  tools.debugger.tests.test_catalog \
  tools.headless_battle.tests.test_simulator \
  tools.headless_battle.tests.test_rom_switch_scenario_export

# 2. Debugger meta-audit
python -m tools.debugger audit

# 3. Godmode benchmark
python tools/audit/check_debugger_godmode_benchmark.py

# 4. Next-step coverage
python tools/audit/check_debugger_next_coverage.py

# 5. Release smoke (broad sanity)
python tools/audit/check_release_smoke.py

# 6. Navigation floor
python tools/audit/check_navigation_floor.py

# 7. Strict handoff log
python tools/audit/check_two_llm_handoff_log.py --strict \
  --store audit/omni_debugger_2026-05-24_handoff_log.jsonl

# 8. No solo commits (scoped to OMNI_DEBUGGER_PATHS)
python tools/audit/check_no_solo_commits_omni_debugger.py

# 9. Headless battle simulator (workflow + round-trips)
python tools/audit/check_headless_battle_simulator.py
```

A green floor proves wiring. For new behavior, also extend the
relevant test + audit before you'd consider the slice done.

---

## 8. Anti-patterns / gotchas

**Don't silently lossy-map boards.** The exporter raises on any
field outside its current slice scope with a named reason — keep
that discipline. If a board has stat stages and you don't have
slice C-stages yet, the right answer is "reject with `slice
C-stages is future work`", not "drop the stages and pretend the
scenario is faithful."

**Don't add unconditional patches to the materializer.** New
override fields must be emit-only-when-explicitly-present.
Unconditional patches overwrite whatever the base save state has
and can silently change previously-passing scenario behavior.
Pattern: `if "field_name" in overrides_raw:
optional_overrides.append((...))`. See slice C-environment for the
shape and `test_switch_materialization_skips_environment_patches_when_absent`
for the guard.

**Don't trust SPECIES / TYPES dicts as canonical.**
`tools/boss_ai_debugger/rom_score_materialize.py` exposes a tiny
hand-curated dict. For arbitrary species use
`parse_species_order()` from
`tools/boss_ai_debugger/role_packages.py` (251 species). The
exporter already does this via `species_id_for`.

**Don't cite commit hashes in committed docs.** The
`check_no_stale_shipped_claims.py` audit fails when a cited commit
isn't an ancestor of `codex/cleanup-gsc-rebalance-split`. Our work
is on `master`, which diverges. Drop the hash; use file-link
references instead.

**Don't run the verification floor only at the end.** Run it
between commits. The handoff-log audit's strict mode rejects
pending phases, and the no-solo audit rejects new commits without a
matching handoff phase. Catching these mid-stream is one minute;
catching them at commit is a rebase.

**Don't bundle more than two related fields per slice.** The
session's 8-commit cadence kept slices small and reviewable. Bigger
commits hide regressions.

**Don't claim live Boss AI is solved.** Everything you ship sits on
top of `boss_ai_switch_roll` which still requires either (a) the
caller supplied confidence + threshold or (b) `rom-switch-materialize`
produced an observation. The headless side does NOT compute switch
confidence from raw board state — that would be a full Boss-AI
reimplementation and is out of scope.

---

## 9. First action when picking this up cold

1. `git log -10 --oneline` to see the 8 recent commits.
2. Read this doc (you're here).
3. Read [`docs/headless_to_rom_switch_materialize_scoping.md`](headless_to_rom_switch_materialize_scoping.md).
4. Read [`tools/headless_battle/README.md`](../tools/headless_battle/README.md).
5. Run the verification floor (§7). Confirm everything is green
   before changing anything.
6. Pick Phase 1 (batch runner). Smallest concrete deliverable.
7. Write the `ack_start` row for your slice. Confirm Cole's
   solo-approval status if you'll commit solo.
8. Implement, verify, write `slice_update` + `slice_review` +
   `phase_done`, commit.
9. Run floor again. If green, move to next slice.
10. Ping Cole at natural pause points (phase complete, ~3 commits
    deep, or any taste-call boundary).

---

## 10. Build / environment notes

Per CLAUDE.md:
- **Build**: WSL via the Windows `.exe` binaries (see CLAUDE.md
  "Build & verification" for the exact incantation). You don't need
  to build for Phase 1-3; ROM behavior comes from `pokegold_debug`
  which is already built.
- **Python**: `python` on Windows resolves correctly. PyBoy is a
  required dep for materialization (`tools.trace.runtime.load_pyboy`).
- **Working dir**: `C:\Users\lolno\Downloads\pokemon gold hack`.
- **OS**: Windows 11 + WSL Ubuntu. Bash tool and PowerShell tool are
  both available; prefer Bash for portability of grep/find pipelines.

If `python -m tools.headless_battle.rom_differential` won't run,
PyBoy isn't importable in your environment — re-check the
`pysdl2-dll` warning and the PyBoy install.
