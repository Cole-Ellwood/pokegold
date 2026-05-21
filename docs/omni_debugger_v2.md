# Omni Debugger V2 Roadmap

Status: branch-canonical v2 planning surface.
Last reconciled: 2026-05-21.

## Source Truth

Unified debugger v1 is complete by the current branch gate:

```powershell
python -m tools.debugger audit
```

Expected current result:

```text
ready=True status_counts={'complete': 11, 'partial': 0, 'missing': 0}
blocking_gaps=0
```

The v1 done model lives in `tools/debugger/catalog.py`,
`tools/audit/check_unified_debugger_ready.py`, and the audit command above.
Do not treat v2 items in this file as blockers for v1 readiness.

The earlier P0-P12 debugger roadmap from the Claude worktree is source
material only. Do not import it wholesale as `docs/debugger_roadmap.md` or use
it to contradict the current catalog gate. When useful, promote individual
ideas into this v2 roadmap with a fresh priority, acceptance check, and
verification command.

## V2 Objective

Turn the v1 proof substrate into an omni-debugger that makes future sessions
faster and less drift-prone:

- persist hypotheses and cite claims to repo evidence;
- expose one-command health checks;
- give future agents task recipes instead of tool archaeology;
- inspect and diff player-provided save states;
- bisect regressions from scenario evidence;
- defer heavier IDE, cross-emulator, and web surfaces until their local ROI is
  clear.

## Acceptance Rules

Every v2 increment needs:

- one command, document, or workflow a future session will actually use;
- one named scenario or recipe from the failure class it addresses;
- proof-status language that separates planned routes from executed evidence;
- narrow tests or audits, plus `git diff --check`;
- no promotion of optional v2 work into v1 readiness.

## Ranked Backlog

### S-Tier

#### Hypothesis Tracker V0

Purpose: make debugging state persistent, cited, and reviewable across Codex and
Claude handoffs.

Scope:

- `audit/hypothesis_tree.jsonl` or equivalent append-only store.
- CLI under `python -m tools.debugger hypothesis ...`.
- Add, refine, reject, and verify hypotheses.
- Citation checker for file:line evidence.
- No autonomous hypothesis generation in V0.

Acceptance:

- A sample investigation can record at least one active hypothesis, one rejected
  hypothesis, and one verification result.
- Claims that require source support must carry file:line citations.
- Citation validation fails on missing or stale file references.

#### Selftest Infrastructure

Purpose: give future sessions a one-bit health command before deeper debugging.

Scope:

- `python -m tools.debugger selftest`.
- Per-component results for catalog/audit, ingest, replay/watch planning,
  compare/mirror, visualization/reporting, and any new v2 modules.
- Text output for humans plus optional JSON for automation.

Acceptance:

- Selftest returns nonzero on any component failure.
- The output names the failing component and the next command to run.
- Existing `python -m tools.debugger audit` remains the v1 readiness gate.

#### Debugger User Guide

Purpose: turn the current CLI surface into decision-useful recipes.

Scope:

- `docs/debugger_user_guide.md`.
- Task recipes for player bug packets, damage anomalies, Boss AI choices,
  save-load risk, graphics/audio symptoms, and commit regression checks.
- Each recipe names required inputs, command sequence, expected output shape,
  and proof limit.

Acceptance:

- A fresh session can choose the right first debugger command for each listed
  symptom without reading `tools/debugger/__main__.py`.
- Recipes do not imply live proof when only static planning exists.

### A-Tier

#### Save-State Lab V0

Purpose: make player-submitted state files inspectable before patching or
guessing.

Scope:

- Inspect PyBoy state and VBA/VBA-M `.sgm` inputs when format confidence is
  sufficient.
- Diff WRAM/SRAM/HRAM/IO-relevant bytes between two states.
- Decode known high-value symbols through the existing symbol service.
- Report save-format marker and checksum/version signals where available.
- Treat two-way conversion as later work unless a format proof exists.

Acceptance:

- `python -m tools.debugger save inspect <state>` prints a concise state report
  in under 2 seconds for supported formats.
- `python -m tools.debugger save diff <a> <b>` shows named-symbol deltas where
  symbols are known, raw address deltas otherwise.
- Unsupported or ambiguous state formats fail with an honest format report, not
  a guessed decode.

#### Bisect Harness

Purpose: turn known scenario regressions into the offending commit quickly.

Scope:

- `python -m tools.debugger bisect --scenario <id-or-file> --good <commit>
  --bad <commit>`.
- Scenario criterion can be exact output match, expectation pass/fail, or
  command exit status.
- Keep git operations non-interactive and preserve dirty-tree safety.

Acceptance:

- A synthetic regression can be localized to the injected bad commit.
- The command refuses to run on a dirty tracked worktree unless explicitly told
  how to preserve or ignore the changes.

### B-Tier Deferred

#### Cross-Emulator Differential

Reason deferred: SameBoy, gambatte, and VBA-M are not currently installed
locally, so immediate work would mostly be scaffold and install notes.

Next useful step:

- Add an install/discovery preflight before backend harness work.
- Trust results only after backend conformance checks using established Game Boy
  test ROM suites.

#### DAP / VS Code Frontend

Reason deferred: current collaboration is CLI/MCP/Claude-centric. A DAP server
is useful only if the user actually wants VS Code as the primary debugger UI.

Next useful step:

- Revisit after selftest, hypothesis tracking, user guide, and save-state lab
  are working.

#### Web UI

Reason deferred: local HTML/Markdown reports already cover the near-term review
need. A web app is a larger surface that should wait until the data contracts
stabilize.

Next useful step:

- If user review artifacts become the bottleneck, prototype a static report
  browser before a server-backed app.

## Current Parallel Plan

After this reconciliation commit:

- Codex lane: Save-State Lab V0.
- Claude lane: Hypothesis Tracker V0 plus Selftest Infrastructure.

Shared collision-risk files:

- `tools/debugger/__main__.py`
- `tools/debugger/catalog.py`
- `tools/debugger/README.md`
- `tools/debugger/tests/test_catalog.py`

Before either side touches those files, restate the write set and current test
plan. New modules under separate directories are safe to work in parallel if
the CLI wiring waits for a sync point.

## Verification Floor

For this roadmap doc:

```powershell
python tools\audit\check_navigation_floor.py
git diff --check
```

For v2 implementation lanes:

```powershell
python -m tools.debugger audit
python -B -m unittest discover tools\debugger\tests
git diff --check
```

Use narrower focused tests first when the write set allows it. Broaden to the
full debugger tests when changing shared CLI, catalog, report schema, or proof
status behavior.
