# Case Library

This is the persistent "brain" of the Pokemon Mastery Compounding Loop.
Both Claude /pgoal sessions and Codex sessions read from and write to
these files. Operator runbook is at
[docs/pokemon_mastery/compounding_loop.md](../../../docs/pokemon_mastery/compounding_loop.md).

## Files

| File | Role | Append-only? |
| --- | --- | --- |
| `schema.json` | JSON schema for case rows, replay rows, metrics rows; reasoning_class and failure_mode enums | No (versioned changes ok) |
| `loop_state.json` | Iteration count, phase rotation hints, gate target, EMA params | No (overwritten per iteration) |
| `replay_index.jsonl` | Every replay tagged study / validation / sealed_exam at fetch time | **YES** |
| `cases.jsonl` | Extracted case rows: fingerprint + pro_action + lesson | **YES** |
| `metrics.jsonl` | Rolling-window aggregate scores; validation-tier row is the headline | Append (new windows; never edit prior) |
| `regression/<id>.json` | Constructed probes for recurring failure modes | Add freely; never delete |

## Tier invariants (enforced by verify_loop_state.py)

- `cases.jsonl` rows may only carry `tier=study`. Cases extracted from
  validation or sealed_exam replays will fail the verifier — that's the
  contamination guard for the headline metric.
- `replay_index.jsonl` is append-only at fetch time; tier assignment is
  fixed per replay forever.
- Every `case_row.replay_id` must exist in `replay_index.jsonl` with a
  matching tier.

## Hash discipline

`tools/pokemon_mastery/fingerprint.py:fingerprint_hash` is the single
source of truth for the distinct-fingerprint count. `verify_case_breadth.py`
imports it; the verifier and the loop cannot drift.

## Reading the data

Quick counts:

```bash
wc -l tools/pokemon_mastery/case_library/cases.jsonl
wc -l tools/pokemon_mastery/case_library/replay_index.jsonl
```

Distinct fingerprints:

```bash
python tools/pokemon_mastery/verify_case_breadth.py
```

Latest validation metrics:

```bash
python tools/pokemon_mastery/verify_progress_gate.py
```

## Safety

If a file in this directory becomes corrupt:

- `replay_index.jsonl` / `cases.jsonl`: do NOT rewrite. Find the bad line
  and append a correction case row pointing at it; or restore from git
  history. The append-only contract is what lets two sessions write
  safely.
- `loop_state.json`: regenerate from prior commits if needed; the
  iteration counter is recoverable from `git log --grep="pokemon-mastery-loop"`.
- `metrics.jsonl`: deletable in emergencies, but the verifier will
  reset to "no validation window yet" until new rows accumulate.

Never delete `schema.json` or `loop_state.json`.
