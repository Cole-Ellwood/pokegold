# Boss AI Trace Capture Refresh — Codex Task Spec

> Four boss-AI behavior changes have shipped since the last trace refresh
> (commits `8089199f` MercyRefusal removal, `0351b8f7` ShellBell +
> GrassRegrowth removal + Choice 40→60 tighten, plus the `f40da374`
> repartition merge — repartition was byte-identical so the trace ROM
> SHA only changed for the bias-removal commits). The manifest at
> [`audit/boss_ai_trace/live_capture_manifest.json`](../audit/boss_ai_trace/live_capture_manifest.json)
> still pins the pre-removal `pokegold_trace.gbc` SHA256, and all 19
> entries in [`audit/boss_ai_trace/live_capture_ledger.md`](../audit/boss_ai_trace/live_capture_ledger.md)
> are FINISHED against that pre-removal ROM.
>
> This task rebuilds `pokegold_trace.gbc` with current source, updates
> the manifest's pinned hashes, re-runs every capture in the batch, and
> updates ledger rows whose `chosen_id` / `top_moves` / `plan_id`
> changed. Pure verification work — no source edits expected.
>
> Read the canonical write-up at
> [`docs/boss_ai_post_patch_notes.md`](boss_ai_post_patch_notes.md) §
> "Manual Build Fallback" for the trace-ROM build incantation; the
> capture pipeline is documented inline in the ledger.

## Execution shape

This task runs as 4 ordered steps (A → B → C → D). Codex executes all
four in one pass without stopping between them.

### STEP A — Worktree setup (BEFORE any file edit)

Run these commands first, exactly as written:

```bash
git fetch origin
git worktree add .claude/worktrees/codex-boss-ai-trace-refresh origin/codex/cleanup-gsc-rebalance-split
cd .claude/worktrees/codex-boss-ai-trace-refresh
cp -r ../../../rgbds-1.0.1 .
git rev-parse HEAD
git rev-parse origin/codex/cleanup-gsc-rebalance-split
```

The two `git rev-parse` outputs MUST match. If they do not, the
worktree is on a stale base and Codex must rerun.

THEN, before any file edit, print this **four-check report** so the
user can spot a misplacement before any commit:

```bash
pwd
git branch --show-current
git rev-parse HEAD
ls audit/boss_ai_trace/live_capture_manifest.json
```

Required state:
- `pwd` ends in `.claude/worktrees/codex-boss-ai-trace-refresh`
- branch is the auto-named codex worktree branch (NOT
  `codex/cleanup-gsc-rebalance-split` directly, NOT any pre-existing
  codex branch)
- `git rev-parse HEAD` matches
  `git rev-parse origin/codex/cleanup-gsc-rebalance-split`
- `audit/boss_ai_trace/live_capture_manifest.json` lists

ALL subsequent work happens inside this worktree.

### STEP B — Reading

Before doing anything else, read:

- [`docs/codex_playbook.md`](codex_playbook.md) §1, §2, §2.3.
- [`docs/boss_ai_post_patch_notes.md`](boss_ai_post_patch_notes.md)
  "Verification Already Performed" + "Manual Build Fallback" sections
  (the trace-ROM build incantation lives here).
- [`audit/boss_ai_trace/live_capture_ledger.md`](../audit/boss_ai_trace/live_capture_ledger.md)
  in full — both the tooling status table and the per-boss table at
  the bottom name the moves and `plan_id`s the audit will check.
- [`audit/boss_ai_trace/live_capture_manifest.json`](../audit/boss_ai_trace/live_capture_manifest.json)
  to confirm capture IDs and save-state paths.
- `tools/trace/boss_ai_trace_batch.py` `main()` to see the
  `--execute` flag semantics and the manifest hash validation.
- `tools/audit/check_boss_ai_live_capture_ledger.py` to see what the
  audit will fail on (manifest hash mismatch, ledger/manifest desync,
  missing per-row fields in `*_live.txt`).

### STEP C — Execution

Run the 6 sub-steps in [Steps](#steps) below, in order.

### STEP D — Ship

Merge to dev tip via the playbook §2.3 commit-tree pattern. Final
merge commit body has the bug-check Findings report (§1.1 format),
including the rebuilt trace ROM's SHA256, the diff between old and
new ledger rows (if any), and explicit confirmation that
`check_boss_ai_live_capture_ledger.py` passes.

---

## Background

The trace ROM is the boss-AI debug build: same source as
`pokegold.gbc` but compiled with `-D BOSS_AI_TRACE`, which adds WRAM
fields that mirror the boss AI's per-decision scoring state to a
known location for tools to read. The 19 captures in the ledger are
PyBoy emulator runs that step the ROM forward from a hand-prepared
save-state and snapshot the boss AI's `chosen_id`, `top_moves`,
`plan_id`, `switch_confidence`, `risk_flags`, `plausible_mask`, and
`revealed_masks` at the first decision frame.

**Why the refresh is needed.** Each of the 4 behavior changes
modifies the boss-AI source bank. The repartition merge `f40da374`
was byte-identical to its parent (verified via `make compare`), but
the bias removals were not — they changed scoring constants and
bias weights. The trace ROM's SHA256 is therefore stale, the
manifest's `trace_rom_sha256` will fail validation in
`boss_ai_trace_batch.py:validate_manifest_hash`, and the captured
top_moves / chosen_id rows could shift if any of the removed/tightened
biases would have fired in the captured scenario.

**Expected diff in captures.** Most captures should be unchanged. The
removed biases were narrowly gated:
- MercyRefusal applied only at very low boss HP. None of the 19
  capture save-states are HP-stressed enough to trigger it.
- ShellBell sustain only fires when the boss holds Shell Bell. Audit
  the manifest's bosses against `data/trainers/parties.asm` to confirm
  no Shell Bell holders.
- GrassRegrowth fires for Grass-type bosses post-damage. Erika's team
  is the only candidate; her capture is at first-decision (no prior
  damage), so no fire.
- Choice 40→60 tighten changes the first-lock regret threshold for
  Choice-item holders. Sabrina has a Choice-band lead in late-tier
  builds; verify against current `data/trainers/parties.asm`.

If any capture's `chosen_id` / `top_moves` / `plan_id` actually shifts,
that is **expected and correct** — the bias removal was the point.
The deliverable updates the ledger row to match.

**Critical constraint.** No source edits in this task. The only files
that should change are:
- `audit/boss_ai_trace/live_capture_manifest.json` (hash pins +
  optionally `notes` if a capture's behavior changed)
- `audit/boss_ai_trace/*_live.txt` (regenerated by the batch)
- `audit/boss_ai_trace/live_capture_ledger.md` (updated rows for any
  capture whose tracked fields shifted)

If any source change is needed (e.g., a capture's save-state needs
regenerating), surface for user judgment in Findings — do not edit
boss-AI source in this pass.

---

## Files to investigate

- `audit/boss_ai_trace/live_capture_manifest.json` — pinned trace
  ROM/symbol SHA256 hashes; per-capture save_state + out paths.
- `audit/boss_ai_trace/live_capture_ledger.md` — per-boss expected
  fields; the audit reads `chosen_id`, `top_moves`, and `plan_id`
  from the live `*_live.txt` files and matches against this table's
  free-text rationale columns.
- `audit/boss_ai_trace/*_live.txt` — 19 capture excerpts that the
  batch script overwrites.
- `tools/trace/boss_ai_trace_batch.py` — the entry point; respects
  `--execute` (default is dry-run / READY status).
- `tools/audit/check_boss_ai_live_capture_ledger.py` — validates
  ledger ↔ manifest ↔ live-capture file consistency.
- `docs/boss_ai_post_patch_notes.md` — has the trace-ROM build
  incantation in "Manual Build Fallback".

Other (do not edit):
- `engine/battle/ai/boss_*.asm` — out of scope.
- `data/trainers/parties.asm` — read-only, for the Shell Bell / Choice
  audit in Step 4.
- `pokegold.gbc`, `pokegold.sym`, `pokegold.map` — release ROM. This
  task touches `pokegold_trace.gbc` only.

---

## Steps

### Step 0 — Snapshot pre-refresh state

```bash
git rev-parse HEAD > .local/trace_refresh_head.txt
sha256sum pokegold_trace.gbc 2>/dev/null > .local/trace_refresh_old_sha.txt || true
cp audit/boss_ai_trace/live_capture_manifest.json .local/trace_refresh_old_manifest.json
```

Record the manifest's currently pinned SHAs so the Findings diff has
a clean before/after.

### Step 1 — Build the trace ROM

Run from the worktree root via WSL (Windows make is not on PATH; see
CLAUDE.md "Build & verification"):

```bash
wsl -e bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack/.claude/worktrees/codex-boss-ai-trace-refresh" && make -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc DEFINES="-D BOSS_AI_TRACE"'
```

Note that the Makefile produces `pokegold.gbc` regardless of
DEFINES — there is no separate `pokegold_trace.gbc` target. After
building with `-D BOSS_AI_TRACE`, rename the output:

```bash
mv pokegold.gbc pokegold_trace.gbc
mv pokegold.sym pokegold_trace.sym
```

Verify the output file lists and the SHAs differ from the manifest's
pinned values:

```bash
ls -la pokegold_trace.gbc pokegold_trace.sym
sha256sum pokegold_trace.gbc pokegold_trace.sym
```

If `make compare` is later needed, rebuild the normal release ROMs
afterward (the trace build replaces `pokegold.gbc`'s on-disk artifact
even though `roms.sha1` won't match while the trace ROM is the latest
build).

### Step 2 — Update manifest hash pins

Edit `audit/boss_ai_trace/live_capture_manifest.json`:

- `trace_rom_sha256` ← uppercase SHA256 of new `pokegold_trace.gbc`
- `trace_symbols_sha256` ← uppercase SHA256 of new `pokegold_trace.sym`

Use Python to compute (matches the audit's hashing exactly — the
audit uppercases hex digests):

```bash
python -c "import hashlib; print(hashlib.sha256(open('pokegold_trace.gbc','rb').read()).hexdigest().upper())"
python -c "import hashlib; print(hashlib.sha256(open('pokegold_trace.sym','rb').read()).hexdigest().upper())"
```

### Step 3 — Re-run all 19 captures

```bash
python tools/trace/boss_ai_trace_batch.py --execute --strict
```

`--execute` actually runs each capture (default is dry-run / READY).
`--strict` fails on missing save-states. The script reads pinned
trace ROM/symbol paths from the manifest, validates SHAs, and runs
`tools/trace/boss_ai_trace_capture.py` per entry to overwrite each
`*_live.txt`.

If a save-state preflight fails (Morty has a strict preflight), the
batch will surface MISSING_STATE / INVALID_STATE per row. STOP and
report — do not regenerate save-states without user approval.

### Step 4 — Audit and reconcile ledger

```bash
python tools/audit/check_boss_ai_live_capture_ledger.py
```

The audit fails if:
- Manifest SHA pins don't match the on-disk ROM/sym files
  (Step 2 fixed this; verify it actually fixed it).
- A `*_live.txt` is missing required fields (`chosen`, `top_moves`,
  `plan_id`, `switch_confidence`, `risk_flags`, `plausible_mask`,
  `revealed_masks`).
- A `*_live.txt`'s embedded `trace_rom`/`trace_rom_sha256`/
  `trace_symbols`/`trace_symbols_sha256` headers don't match the
  manifest. (The capture script writes these on every run.)
- Manifest status / path don't match the ledger row.

Note that the audit does **not** verify the per-boss "expected
chosen_id and top_moves" rationale text in
`live_capture_ledger.md` against the new `*_live.txt` outputs —
it only checks that the file has *some* nonzero decision-trace
evidence. Compare manually:

```bash
git diff audit/boss_ai_trace/
```

For each capture whose `chosen_id`, `top_moves`, or `plan_id` shifted,
update the matching row in `live_capture_ledger.md` to reflect the
new values and (if relevant) note in the row why the bias removal
caused the shift. If no behavioral diff fired (the expected outcome
for most captures), only the trace ROM/symbol headers in `*_live.txt`
will differ; the ledger does not need editing.

### Step 5 — Build sanity

The release-smoke audit reads bank/free-space figures from
`docs/generated/dev_index.md`. Since this task didn't touch source,
the dev-index doesn't strictly need regenerating, but a clean release
build verifies the trace-build path didn't regress:

```bash
wsl -e bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack/.claude/worktrees/codex-boss-ai-trace-refresh" && make -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc'
python tools/verify_sha1.py roms.sha1
```

`make compare` should still pass — `roms.sha1` is unchanged because
no source moved.

### Step 6 — Final audit floor

- `python tools/audit/check_release_smoke.py` PASS.
- `python tools/audit/check_boss_ai_live_capture_ledger.py` PASS.
- `git diff --check` PASS.

`clobber_smoke` and the boss-AI invariants audits don't need re-running
unless the manifest update somehow changed the trace-build code path
(it doesn't).

---

## Acceptance criteria

- [ ] `pokegold_trace.gbc` rebuilt from current `codex/cleanup-gsc-rebalance-split` HEAD with `-D BOSS_AI_TRACE`.
- [ ] `audit/boss_ai_trace/live_capture_manifest.json` `trace_rom_sha256` and `trace_symbols_sha256` updated to match the new ROM/sym files.
- [ ] All 19 `audit/boss_ai_trace/*_live.txt` files regenerated by `tools/trace/boss_ai_trace_batch.py --execute --strict`. The script's exit code MUST be 0.
- [ ] `python tools/audit/check_boss_ai_live_capture_ledger.py` PASS.
- [ ] `python tools/audit/check_release_smoke.py` PASS.
- [ ] `roms.sha1` unchanged (no row diff vs dev tip).
- [ ] For any capture whose `chosen_id` / `top_moves` / `plan_id` shifted, `live_capture_ledger.md`'s matching row reflects the new values; surface the per-boss before/after in Findings.
- [ ] Final merge commit body has §1.1 Findings report covering: rebuilt trace ROM SHA256 (old vs new), per-capture diff summary (likely "no behavioral diff observed in N/19; M captures shifted with explanation"), and audit results.

---

## Scope boundaries / Do NOT

- Do NOT edit `engine/battle/ai/boss_*.asm` or any other source file.
- Do NOT regenerate save-states. If a state goes stale (preflight
  fails, capture script reports INVALID_STATE), STOP and surface for
  user approval — state regeneration is its own task with creative
  judgment about which battle frame to anchor on.
- Do NOT bump `SAVE_FORMAT_VERSION`. This task touches no save-format
  surface.
- Do NOT touch `pokegold.gbc` or `pokegold.sym` artifacts that are
  the release ROM (rename intermediate output, don't commit it). Only
  the trace ROM's hash goes in the manifest; the trace ROM artifact
  itself is git-ignored.
- Do NOT modify CLAUDE.md, the codex playbook, or any handoff docs.
- If the trace ROM build fails (link error, missing INCLUDE), STOP
  and report — the source is supposed to build clean with the
  `-D BOSS_AI_TRACE` flag.
- If `check_boss_ai_live_capture_ledger.py` fails after Step 4 with a
  reason other than expected ledger desync (e.g., a `*_live.txt`'s
  required field is missing), STOP and report — the capture pipeline
  itself may have regressed.
