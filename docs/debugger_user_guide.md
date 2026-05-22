# Debugger User Guide

Pick your symptom. Each recipe lists the first debugger command, what
success looks like, what the proof actually reaches, and how to record
the investigation so the next session inherits it.

Status: v2 surface — co-authored by Claude and Codex 2026-05-21. Stays
in sync with `docs/omni_debugger_v2.md`.

For the full CLI command surface, see
[`tools/debugger/README.md`](../tools/debugger/README.md). This guide
maps **symptoms → first command**; the README maps **commands → options**.

## Before you start

Fresh session? Run the orientation snapshot first — it composes the
selftest health check, open hypothesis history, recent commits,
working-tree summary, and recommended next commands in one read-only
call. Exits nonzero only if the selftest health gate fails.

```powershell
python -m tools.debugger session-start
```

Expected shape (real output uses real branch + commits):

```
Pokemon Gold romhack debugger — session orientation

branch: <current branch>

selftest PASS (13/13 components healthy)

open hypotheses: 0 (stale citations: 0)

recent commits (3):
  <sha> <commit message>
  ...

working tree: modified=0, added=0, deleted=0, untracked=<n>

first recommended commands:
  python -m tools.debugger.selftest
  python -m tools.debugger triage --symptom "<plain English>"
  python -m tools.debugger hypothesis list --refresh-citations
```

If session-start passes but you want a deeper component-level health
check, drop straight to selftest:

```powershell
python -m tools.debugger.selftest
```

Expected (~5s on this branch):

```
Selftest PASS  (13/13 components healthy)
  [ok]   capability_audit  — capability audit ready=True, complete=11
  [ok]   inventory  — inventory ok (5 subsystems)
  ...
  [ok]   save_state_lab  — save_state_lab raw WRAM + .sgm fail-closed round-trip ok
  [ok]   bisect  — bisect synthetic regression localized in 2 steps
```

If selftest fails, **fix the named component first** — the output names
the next command to run. The debugger's own health is the floor for
trusting anything below.

The v1 readiness gate is separate:

```powershell
python -m tools.debugger audit
```

`audit` checks that capabilities are registered with their evidence
paths. `selftest` actually exercises them end-to-end. Both should be
green; if they disagree, audit is the load-bearing v1 gate and
selftest is a deeper v2 health surface.

## When you don't know where to start

```powershell
python -m tools.debugger triage --symptom "plain English description"
python -m tools.debugger triage --changed-file path/to/touched/file.asm
```

Triage routes to one of the focused subsystem debuggers. Both flags
combine. Always safe; never edits anything.

For a more thorough first-cut once triage points at a subsystem:

```powershell
python -m tools.debugger investigate --symptom "..." --symbol wCurDamage
```

Investigate is the one-command packet — it ingests inputs, plans
replays, runs localization + coverage + causal explanation + mirror
routing, and writes a directory of evidence under
`.local/tmp/debugger_investigation/`. Use it when triage has narrowed
the subsystem but the next move is still unclear.

## Recipes

### "Player reported a bug"

**Inputs needed**

- A save state (`.state` or `.sgm`) from the player.
- An input log if reproducing the symptom requires button sequences.
- A screenshot if the symptom is visual.
- A one-sentence player-facing symptom description.

**First command**

```powershell
python -m tools.debugger capture-playtest `
  --rom pokegold.gbc `
  --symbols pokegold.sym `
  --save-state .local/tmp/bug.state `
  --input-log .local/tmp/bug.inputs `
  --screenshot .local/tmp/bug.png `
  --symptom "NPC freezes after sign text"
```

Then feed the packet to `investigate`:

```powershell
python -m tools.debugger investigate `
  --playtest-packet .local/tmp/playtest_packet.json
```

**Success looks like**

A directory of evidence under `.local/tmp/debugger_investigation/` —
trace index, localization plan, coverage gaps, candidate watch
symbols, and the suggested next commands. `investigate` writes a
`packet_summary.json` you can hand to the next session.

**Proof limit**

`capture-playtest` packages evidence and plans the next debugger step;
it is `planned_only` proof. Runtime proof comes from the subsequent
`investigate --execute-*` runs (`--execute-watch`,
`--execute-snapshots`, `--execute-attribution`,
`--execute-runtime-evidence`).

**Hypothesis tracker hook**

```powershell
python -m tools.debugger.hypothesis_tracker add `
  --symptom "NPC freezes after sign text" `
  --claim "<your first guess>" `
  --confidence judgment `
  --session-id playtest-<date>
```

Then refine as evidence comes in.

### "Input log is too long to inspect"

Use this after `capture-playtest`, `replay`, or a manual repro gives
you a long `.inputs` file but the bug only needs a few button events.

**First command**

```powershell
python -m tools.debugger minimize `
  --domain input_log `
  --input-log .local/tmp/bug.inputs `
  --expect event=played_input,button=A `
  --expect event=played_input,button=START `
  --out-input-log .local/tmp/bug.min.inputs `
  --json-out .local/tmp/bug.minimize.json
```

Then feed the minimized artifact back into replay or investigate:

```powershell
python -m tools.debugger replay `
  --report .local/tmp/bug.minimize.json `
  --input-log .local/tmp/bug.min.inputs
```

**Success looks like**

The minimization report has `input_log_minimization.preserved=true`,
a smaller `minimized_event_count`, and a non-empty `reduction_trace`.
The output log keeps the retained events' original timing, so a long
repro can collapse to the shortest button sequence that still satisfies
the explicit input predicate.

**Proof limit**

`--domain input_log` proves only that the reduced text input log still
contains the declared input evidence. It does not prove the ROM symptom
still reproduces until a replay/watch/investigation route executes the
minimized log against the ROM.

### "Bug only reproduces sometimes"

Use chaos mode when the report smells like a timing-sensitive flake:
input windows, frame-boundary races, or a bug that disappears under the
normal deterministic replay schedule.

**Known-stable control**

```powershell
python -m tools.debugger fuzz `
  --chaos `
  --runs 100 `
  --seed 1 `
  --chaos-scenario stable `
  --json-out .local/tmp/chaos.stable.json
```

**Synthetic flake smoke**

```powershell
python -m tools.debugger fuzz `
  --chaos `
  --runs 100 `
  --seed 1 `
  --chaos-scenario synthetic_flake `
  --json-out .local/tmp/chaos.flake.json
```

**Success looks like**

For the stable control, `diverged=false` and `stable_count` should stay
at 99 or higher out of 100. For the synthetic flake smoke,
`diverged=true`, `minimal_seed` is an integer, and
`candidate_input_log` contains the replay inputs that triggered the
flake. Feed that input log into `minimize --domain input_log` when it
is too long to inspect.

**Proof limit**

Current chaos mode has two layers. The schedule/campaign layer records
deterministic hardware-envelope requests and catches synthetic flake
divergence. The PyBoy adapter layer can drive public `tick` and
`button` APIs, but PyBoy does not expose public cycle-level controls for
vblank/hblank timing, joypad-latch cycles, or DMA-vs-CPU interleaving.
Those requests are preserved as `planned_not_applied` evidence rather
than reported as applied perturbations.

### "Generated scenario is too noisy"

Use this when `generate`, `content-scenarios`, or a subsystem tool gives
you a battle or map-script scenario with the right bug signal buried in
extra party members, moves, events, or script steps.

**Battle scenario**

```powershell
python -m tools.debugger minimize `
  --domain battle `
  --scenario .local/tmp/battle_cases.jsonl `
  --scenario-id <case_id> `
  --expect contains=MILTANK `
  --expect contains=ROLLOUT `
  --expect contains=critical_window `
  --out-shrunk-scenario-dir .local/tmp/shrunk `
  --json-out .local/tmp/battle.minimize.json
```

**Map-script scenario**

```powershell
python -m tools.debugger minimize `
  --domain map_script `
  --scenario .local/tmp/script_cases.jsonl `
  --scenario-id <case_id> `
  --expect contains=jump_script `
  --expect contains=UnitNpcScript `
  --expect contains=unit_signpost `
  --out-shrunk-scenario-dir .local/tmp/shrunk `
  --json-out .local/tmp/script.minimize.json
```

**Success looks like**

The report has `battle_minimization.preserved=true` or
`map_script_minimization.preserved=true`. The `best.out_scenario.path`
points at the minimized JSON artifact, `best.removed_counts` says what
was removed, and `best.reduction_trace` records each accepted/rejected
candidate.

**Proof limit**

Battle and map-script domain minimization uses explicit text predicates
over scenario JSON (`contains=` / `not-contains=`). It proves the reduced
scenario still contains the named facts. It does not prove the minimized
scenario still reproduces the ROM symptom until a materialization or
replay route executes that artifact.

### "Damage is wrong"

The most common bug class in this hack. Bind to the existing damage
debugger before reaching for anything else.

**First command**

```powershell
python -m tools.damage_debugger.clobber_smoke
```

Runs the hand-curated regression scenarios. Any FAIL points at a
damage-chain divergence between ROM and the Python oracle.

**Then localize**

```powershell
python -m tools.debugger investigate `
  --symbol BattleCommand_DamageCalc `
  --address D141 `
  --watch-size 2 `
  --symptom "physical damage 5x too high"
```

**Or ask the omniscient question directly (P2 when-wrote)**

```powershell
python -m tools.debugger when-wrote `
  --address 01:D141 `
  --report <effect-trace.json> `
  --since-symbol BattleCommand_DamageCalc
```

`when-wrote` is the Pernosco-style "who last wrote this byte" query.
Returns the writer's PC, symbol, bank, frame, and the proof vector
(proof_status, match_precision). Refuses to fall back to a
bus-address match when the target is bank-qualified — the P0 proof
boundary holds. Use this when you have a recorded effect trace and
the question is "which write clobbered the damage byte?" The full
`investigate` pipeline runs more analyses but is heavier; `when-wrote`
is one second when you already know the address.

**Count whether the suspected code path ran (P8 probes)**

When the symptom says "damage was wrong" but the next question is
whether a specific routine ran at all, declare a named probe once and
count it against the trace:

```powershell
python -m tools.debugger probe declare `
  --name damage_calc_entry `
  --pc BattleCommand_DamageCalc

python -m tools.debugger probe stats `
  --trace <instruction-or-effect-trace.jsonl>
```

`probe stats` reports per-probe fire count, first/last frame, average
inter-fire interval, and sample PCs. Use it to separate "this path did
not run" from "this path ran but wrote the wrong value"; then use
`when-wrote` for the byte-level writer.

**Success looks like**

`clobber_smoke` reports all scenarios PASS. If not, the named scenario
narrows the failure class (physical-no-items, type-passive, late-gen,
etc.); cross-reference with
[`tools/damage_debugger/README.md`](../tools/damage_debugger/README.md)
for which file each scenario stresses.

**Proof limit**

`clobber_smoke` proves the curated scenarios match. It does NOT prove
every wild encounter and every move combination. For broader coverage:

```powershell
python -m tools.damage_debugger.fuzz --self-check-workers=2
python -m tools.damage_debugger.oracle
```

**Hypothesis tracker hook**

For AG-NN-class bugs (transitive register clobbers from ABI changes —
the May 2026 5x physical damage class, where a downstream ABI change
clobbers a register a caller relied on past the dispatch boundary; see
also [`docs/asm_authoring_guide.md`](asm_authoring_guide.md) §3.13–§3.14):

```powershell
python -m tools.debugger.hypothesis_tracker add `
  --symptom "<damage symptom>" `
  --claim "AG-NN transitive register clobber suspected" `
  --confidence memory-derived `
  --session-id damage-<date>

# Once localized to a specific function in source:
python -m tools.debugger.hypothesis_tracker refine <id> `
  --claim "<specific function and the clobbered register>" `
  --confidence repo-proven `
  --citation "engine/battle/<file>.asm:<line>"

# Once clobber_smoke confirms the fix:
python -m tools.debugger.hypothesis_tracker verify <id> `
  --command "python -m tools.damage_debugger.clobber_smoke" `
  --expected "all scenarios pass" `
  --verdict pass
```

The May 2026 AG-08 c-mirror investigation is the named lived smoke
for this recipe (`Ag08LivedSmokeTests` in
[`test_hypothesis_tracker.py`](../tools/debugger/tests/test_hypothesis_tracker.py)).

### "Boss AI picked an obviously bad move"

**First command**

```powershell
python -m tools.boss_ai_debugger inspect `
  --fixture-id <fixture or trace-id>
```

Renders the boss state, candidate moves, and rule-by-rule score
contributions.

**Then for source-level attribution**

```powershell
python -m tools.boss_ai_debugger rom-contribution-trace `
  --boss-route morty `
  --json-out .local/tmp/morty_trace.json
```

This runs against the trace ROM with hooks on AI source labels and
captures rule deltas + selector entry scores.

**Success looks like**

A rule waterfall that explains the chosen move in plain language —
e.g. `move.ghost.dream_eater_floor: -20 (player asleep prob: 0)`.

**Proof limit**

Boss AI traces against the trace ROM, which has marker NOPs at known
PCs. The trace doesn't guarantee the release ROM behaves identically
unless `check_boss_ai_trace_invariants.py` is green. Always re-run
that audit after AI changes.

**Hypothesis tracker hook**

Boss AI bugs often surface as policy contradictions ("rule says X
biases against Y, but the bias didn't fire"). Record the bias gate
condition you THINK fires, refine with the actual scoring evidence,
and verify by re-running with patches:

```powershell
python -m tools.debugger.hypothesis_tracker add `
  --symptom "Morty chose Dream Eater into awake target" `
  --claim "move.ghost.dream_eater_floor bias should be active here" `
  --confidence memory-derived
```

### "Save loaded weird / save format broke"

**Static check first**

```powershell
python tools/audit/check_save_format_version.py
```

This proves that `SAVE_FORMAT_VERSION` was bumped if any `ram/`
field's offset shifted.

**Runtime inspection**

```powershell
python -m tools.debugger.save_state_lab inspect <state>
python -m tools.debugger.save_state_lab diff <a> <b>
```

V0 trusts two surfaces: raw 64 KiB address-space dumps and raw 8 KiB
WRAM images with named-symbol deltas via the existing `.sym` service.
`.sgm` files (VBA / VBA-M) are classified by suffix + magic bytes and
returned as `vba_sgm_candidate` with `decode_supported=false` — the V0
deliberately fails closed rather than guessing a WRAM offset map.
VBA `.sgm` files use a non-contiguous WRAM bank layout; a bank-contiguous
assumption silently mis-decodes them, which is why the V0 contract
requires an explicit format proof before trusting a decode.

If the inspect reports `decode_supported=false`, the workflow falls
back to manual reading via
[`tools/damage_debugger/legacy/sgm_decoder.py`](../tools/damage_debugger/legacy/sgm_decoder.py)
until a trusted offset decoder lands. Diff between unsupported formats
reports invalid instead of guessing.

**Proof limit**

`check_save_format_version.py` catches OFFSET drift but not SEMANTIC
drift (e.g., re-purposing a byte without moving it). If you change the
meaning of an existing field, you still need a version bump.

**Hypothesis tracker hook**

Save bugs are often caused by reordering the schema accidentally
during refactor. Record the suspected schema diff:

```powershell
python -m tools.debugger.hypothesis_tracker add `
  --symptom "save loads with wrong party" `
  --claim "wPartyMon1 offset shifted in <commit>" `
  --confidence repo-proven `
  --citation "ram/wram.asm:<line>"
```

### "Graphics or audio glitch in VBA"

The user plays in VBA-M, not PyBoy. PyBoy and VBA-M can disagree
(May 2026 tile jumble class). Lived play behavior is VBA-M's call,
not PyBoy's; treat PyBoy agreement as a signal, not a proof, for any
user-reported graphics/audio symptom.

**For visible-region snapshots**

```powershell
python -m tools.debugger visual-snapshot `
  --save-state <state> `
  --frames 30 `
  --json-out .local/tmp/visual.json
```

**For audio register state**

```powershell
python -m tools.debugger audio-snapshot `
  --save-state <state> `
  --frames 30 `
  --json-out .local/tmp/audio.json
```

**For raw VRAM/OAM state diffs (P6)**

Use this only when you have trusted raw 64 KiB address-space dumps
from before and after the visible glitch. It decodes VRAM tile maps,
CGB attrs, OAM sprites, LCDC, and palettes, then reports structured
tilemap/OAM/palette/LCDC deltas instead of a byte blob.

```powershell
python -m tools.debugger vram-snapshot `
  --decode before.raw64k `
  --json-out .local/tmp/vram_before.json

python -m tools.debugger vram-diff `
  before.raw64k after.raw64k `
  --json-out .local/tmp/vram_diff.json
```

If the available artifact is an opaque VBA/VBA-M `.sgm` or generic
`.state`, `vram-snapshot` and `vram-diff` refuse to decode it. That is
intentional: guessing emulator-specific offsets would create false
graphics evidence. Convert or export a trusted raw 64 KiB dump first,
or keep the claim at `planned_only` and use the visual/audio snapshots
as PyBoy-only signals.

**Cross-emulator (v2, deferred)**

`python -m tools.debugger crossemu --backends pyboy,sameboy,gambatte,vba-m`
will land when SameBoy / gambatte / VBA-M binaries have a documented
install path on this machine. Until then, manual cross-check via the
user playing in VBA-M is the workflow.

**Proof limit**

Visual + audio snapshots come from PyBoy. They prove "PyBoy renders X"
not "VBA renders X." If the user reports a VBA-only symptom, treat
PyBoy snapshot agreement as a signal but not as proof.

**Hypothesis tracker hook**

```powershell
python -m tools.debugger.hypothesis_tracker add `
  --symptom "tile jumble during transition (VBA-M)" `
  --claim "VBA-M-specific OAM DMA timing edge" `
  --confidence judgment
```

### "Did this commit break X?"

**Diff-based first**

```powershell
python -m tools.debugger compare --symbol wCurDamage
python -m tools.debugger compare --changed-file engine/battle/effect_commands.asm
```

Mirror-based comparisons against known-good evidence.

**Release smoke floor**

```powershell
python tools/audit/check_release_smoke.py
```

Always run when in doubt. This is the project-wide audit floor.

**Bisect**

```powershell
python -m tools.debugger.bisect --good <known-good-commit> --bad HEAD `
  -- python tools/audit/check_release_smoke.py
```

The scenario after `--` is exec'd at each midpoint; exit 0 means
good, nonzero means bad. The harness drives `git bisect` end-to-end
and prints the first bad commit on success.

Pre-flight refuses on a dirty tracked tree, unresolvable refs, or if
the repo is already in a bisect state. `git bisect reset` is
attempted in `finally` (best-effort) on every error path; if reset
itself fails — corrupted refs, missing HEAD, etc. — the harness
prints a warning to stderr with the manual recovery command rather
than raising and masking the bisect verdict.

**Exit code 125 fails closed.** `git bisect run` reserves 125 for
"cannot test this commit (skip)" — the harness refuses rather than
marking the commit bad, on the principle that a false first-bad is
worse than an explicit refusal. Make sure your scenario returns
deterministically (0 for good, any nonzero except 125 for bad) before
running the harness on a long bisect range.

Skip-as-verdict (real `git bisect skip` semantics), shell-string
scenarios, and `--allow-dirty` are deferred to V1.

**Proof limit**

`compare` shows a difference between current evidence and a recorded
baseline. It does NOT prove the difference is wrong — only that it
exists. The release smoke floor is broader but slower.

**Hypothesis tracker hook**

```powershell
python -m tools.debugger.hypothesis_tracker add `
  --symptom "audit X started failing at <commit>" `
  --claim "regression in <suspected subsystem>" `
  --confidence judgment

# Once the bisect or compare points at a specific file:line:
python -m tools.debugger.hypothesis_tracker refine <id> `
  --confidence repo-proven `
  --citation "engine/<file>.asm:<line>"
```

## Hypothesis Tracker — workflow recipe

For multi-step investigations, persist the tree at every step so a
later session (Claude OR Codex) can pick up exactly where you left
off without re-deriving conclusions.

**Store**: `audit/hypothesis_tree.jsonl` (append-only, committed).

**Confidence labels** (mirror
[`docs/llm_pairing_rules.md`](llm_pairing_rules.md) rule #4):

- `repo-proven` — verified against the actual source or a runnable
  test. Requires at least one `path:line` citation.
- `memory-derived` — recalled from memory files / prior sessions.
  Citations allowed; never satisfies a verification gate alone.
- `judgment` — opinion or extrapolation. Same gate semantics as
  memory-derived.

**Gate semantics**: a `pass` verdict promotes status to `verified`
only when current confidence is in `GATE_VALID_LABELS`
(`{repo-proven}` in V0). A `pass` against a non-grounded claim leaves
status `open` and increments `blocked_pass_count`. A later refinement
to `repo-proven` does NOT retroactively legitimize an earlier blocked
pass.

A `fail` verdict refutes regardless of confidence.

**List open investigations**

```powershell
python -m tools.debugger.hypothesis_tracker list --status open `
  --refresh-citations
```

`--refresh-citations` flags any hypothesis whose source citation no
longer resolves (file moved, line drifted, function renamed).

**Render a hypothesis with its history**

```powershell
python -m tools.debugger.hypothesis_tracker show <id>
```

Prints folded current state, stale-citation report, and an ASCII tree
of all events (claim, refinements, verifications, rejections).

## Selftest — workflow recipe

Run before any debugger-heavy work in a fresh session.

```powershell
python -m tools.debugger.selftest
python -m tools.debugger.selftest --json   # machine-readable
python -m tools.debugger.selftest --component hypothesis_tracker
```

`--component` accepts any of: `capability_audit`, `inventory`,
`ingest`, `triage`, `coverage`, `provenance`, `mirrors_compare`,
`fuzz`, `trace_index`, `visualization`, `hypothesis_tracker`,
`save_state_lab`, `bisect`.

A passing selftest does NOT replace `python -m tools.debugger audit` —
audit is the v1 readiness gate. Selftest is the v2 health check on
top.

## Proof limit reminders

These reach as far as their evidence reaches — no further.

- A green build proves "it links." Not "it works."
- A green `python -m tools.debugger audit` proves "the catalog says the
  capability set is wired." Not "every component works end-to-end."
- A green `python -m tools.debugger.selftest` proves "each component
  accepts synthetic input without crashing." Not "every realistic
  scenario works."
- A green `clobber_smoke` proves the curated regression scenarios pass.
  Not every wild encounter / move combination.
- A green `check_release_smoke.py` proves "no known invariant
  regressed." Not "no NEW bug class was introduced."
- ROM-verified ≠ player-verified. The user plays in VBA-M; PyBoy
  agreement is a signal, not a proof.
- A memory entry is a snapshot in time. Cite the source file before
  acting on a recommendation.

When in doubt, escalate to a runnable command. The hypothesis tracker
records WHAT you ran, WHAT you expected, and WHAT actually happened —
the next session inherits that as ground truth.

## Where this guide is canonical

- Symptoms → first command: this doc.
- Commands → options: [`tools/debugger/README.md`](../tools/debugger/README.md).
- v1 vs v2 scope and acceptance: [`docs/omni_debugger_v2.md`](omni_debugger_v2.md).
- Pairing protocol (Claude+Codex): [`docs/llm_pairing_rules.md`](llm_pairing_rules.md).
- ASM authoring rules: [`docs/asm_authoring_guide.md`](asm_authoring_guide.md).

If a recipe in this guide no longer matches the underlying tool, the
underlying tool is canonical — open a PR to update the recipe.
