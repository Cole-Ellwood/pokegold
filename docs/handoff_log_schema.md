# Two-LLM Handoff Log Schema

Append-only JSONL at `audit/masterpiece_handoff_log.jsonl`. Every row is one event
in the Claude+Codex partnership: a slice ack, a slice update, a slice review, or
a phase sign-off. The audit at `tools/audit/check_two_llm_handoff_log.py` enforces
the rule-#6 mutual-agreement gate (`docs/llm_pairing_rules.md`) by refusing to
treat a phase as `mutual_verified` until BOTH models have rows that pass the gate.

## Why this exists structurally

`docs/llm_pairing_rules.md` rule #6 says neither LLM declares done unilaterally.
That's a convention until a programmatic gate refuses to flip the verified bit
without both signatures. The handoff log is the gate. P4 in
`docs/debugger_masterpiece_roadmap_codex_task.md` ships this gate so P12
(`rom-edit` full-autonomy auto-apply) has a structural foundation for the
"mutual-LLM signed" condition that lets diffs apply without manual Cole
confirmation.

## Required fields (every row)

| Field | Type | Notes |
|---|---|---|
| `schema_version` | int | Currently `1`. Rows without this field are normalized as legacy on read (see Legacy normalization below). |
| `phase` | string | Phase id from the roadmap (e.g. `P0`, `P4`, `P0_consumer_audit`). |
| `event` | string | One of `ack_start`, `slice_update`, `slice_review`, `phase_done`. |
| `status` | string | Allowed values depend on `event` (see Status by event below). |
| `model` | string | Who wrote this row. One of `claude`, `codex`. Extensible by editing `KNOWN_MODELS` in `tools/debugger/handoff_log.py`. |
| `confidence` | string | One of `repo-proven`, `memory-derived`, `judgment` (mirrors `llm_pairing_rules.md` rule #4). Only `repo-proven` satisfies the gate. |
| `claim` | string | What the row is asserting. Required text. |
| `signed_at` | string | ISO 8601 UTC timestamp. Auto-filled by `HandoffRow.as_dict()` if omitted. |

## Optional fields

| Field | Type | When used |
|---|---|---|
| `primary` | string | Model that owns the slice. Required for `is_mutual_verified` to know who counts as "the other model." |
| `reviewer` | string | Required on `slice_review` rows. Identifies who's signing. |
| `slice_id` | string | Optional sub-slice identifier within a phase. |
| `files_changed` | list[string] | Files touched by this slice. |
| `files_read` | list[string] | Read but not changed; helps the next LLM avoid redundant reads. |
| `write_set` | list[string] | Files the model declares it will modify (per rule #3 files-first split). |
| `safe_write_set_for_other` | list[string] | Files the other model is invited to edit during this slice. |
| `collision_risk_files` | list[string] | Files both might touch; requires "I'm taking X" coordination. |
| `verification` | list[string] | Commands the slice author ran with their results. |
| `verification_replayed` | list[string] | Commands the reviewer replayed with results. |
| `accepted_pushbacks` | list[string] | Reviewer's accepted concerns, queued for the next-slice plan. |
| `next_recommended_slice` | string | Pointer at the next work item. |
| `mutual_done_status` | string | Free-form descriptor of phase status. |
| `citations` | list[string] | `path:line` references grounding the claim. |
| `legacy_status` / `legacy_partial_phase` | str / bool | Set by the legacy normalizer when an old row used a status that means "partial acceptance." Do not set these manually. |

## Event kinds and allowed statuses

| Event | Statuses |
|---|---|
| `ack_start` | `in_progress` |
| `slice_update` | `ready_for_review`, `blocked`, `abandoned` |
| `slice_review` | `slice_accepted`, `slice_rejected`, `slice_revisions_requested` |
| `phase_done` | `phase_complete` |

`slice_review` requires `reviewer`. Other events do not.

## Mutual-verification gate (`is_mutual_verified`)

A phase is `mutual_verified` iff ALL of:

1. The phase has at least one row.
2. All rows that declare a `primary` agree on the value (no conflicting primary).
3. No row has `status=slice_rejected` anywhere in the phase.
4. The primary model has filed an `ack_start` row with `status=in_progress`.
5. The primary model has filed a `slice_update` row with `status=ready_for_review`.
6. At least one `slice_review` row exists where:
   - `model` is NOT the primary,
   - `status` is in `{slice_accepted, phase_complete}`,
   - `confidence` is `repo-proven`,
   - the row is NOT marked `legacy_partial_phase=True`.

Self-review by the primary model is structurally non-binding (rule 6 requires
`model != primary`). Solo sign-off is refused — this is the gate's load-bearing
property and the AG-NN-class golden lived-bug smoke exists to lock it in.

## Legacy normalization

The first three rows of `audit/masterpiece_handoff_log.jsonl` (lines 1-3) were
written before the schema was formalized. They use model-prefixed event names
(`codex_ack_start`), long-form model strings (`claude-opus-4-7[1m]`), and a
status (`slice_accepted_partial_P0`) that means "accepted this SLICE but the
PHASE is not complete." The loader normalizes them on read:

- `<model>_<event>` → `<event>` (`codex_ack_start` → `ack_start`)
- `claude-opus-4-7[1m]` → `claude` (full mapping in `LEGACY_MODEL_MAP`)
- `ready_for_claude_review` → `ready_for_review`
- `slice_accepted_partial_P0` → `slice_accepted` with `legacy_partial_phase=True`
  attached; the gate ignores `legacy_partial_phase=True` review rows so the
  partial-acceptance signal is preserved (Codex catch on commit `aea33f85`).

Append-only invariant: the legacy rows are NOT rewritten. New rows from
`HandoffRow.as_dict()` ship with `schema_version=1` and skip normalization.

## CLI

```powershell
# Append a row
python -m tools.debugger handoff add `
  --phase P4 `
  --event ack_start `
  --status in_progress `
  --model claude `
  --primary claude `
  --confidence repo-proven `
  --claim "Claude takes P4 handoff log structural infrastructure" `
  --write-set tools/debugger/handoff_log.py tools/audit/check_two_llm_handoff_log.py

# List rows for a phase
python -m tools.debugger handoff list --phase P4

# Render a phase with mutual_verified status + history
python -m tools.debugger handoff show P4

# Audit the whole store
python -m tools.debugger handoff verify
python -m tools.debugger handoff verify --json
```

## Audit

```powershell
# Warn-only (default) — exits 0 unless rows have schema errors. Wired into
# tools/audit/check_release_smoke.py as the floor for the gate's integrity.
python tools/audit/check_two_llm_handoff_log.py

# Strict — exits 1 on any pending phase. Use at masterpiece-completion time.
python tools/audit/check_two_llm_handoff_log.py --strict
```

## Working idiom

Per `docs/llm_pairing_rules.md` rule #6, the partnership protocol is:

1. Primary model files an `ack_start` declaring write set + safe write set +
   collision risk + intended commit message.
2. Primary model files `slice_update status=ready_for_review` when verification
   is green.
3. Non-primary model adversarially reviews the diff. If it accepts, files
   `slice_review status=slice_accepted confidence=repo-proven` (replayed
   verification listed). If it rejects, `slice_rejected` with critique.
4. When ALL slices of a phase have signed reviews and the phase exit criteria
   from the roadmap are met, primary files `phase_done status=phase_complete`.

The handoff log structurally enforces all of the above via the audit — no
"convention only" gap exists between the rule and the proof.

## See also

- `tools/debugger/handoff_log.py` — module implementation.
- `tools/debugger/tests/test_handoff_log.py` — 16 tests including the AG-NN
  golden lived-bug smoke.
- `tools/audit/check_two_llm_handoff_log.py` — the audit gate.
- `docs/llm_pairing_rules.md` — the pairing protocol the gate enforces.
- `docs/debugger_masterpiece_roadmap_codex_task.md` §5 — partnership protocol
  from which the handoff log is the structural enforcement.
