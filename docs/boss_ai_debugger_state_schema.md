# Boss AI Debugger State Schema

Status: Phase-1 foundation for
`docs/boss_ai_debugger_state_of_art_implementation_plan_2026-05-15.md`.

The debugger now has a small canonical validation layer in
`tools/boss_ai_debugger/state_schema.py`. It is not the final rich battle schema
yet. It is the compatibility floor that current fixtures, generated scenarios,
and live trace captures must pass before deeper ROM/Python differential tooling
trusts them.

## Commands

Validate the current fixture corpus and live trace corpus:

```powershell
python -m tools.boss_ai_debugger state-schema validate
```

Validate explicit inputs:

```powershell
python -m tools.boss_ai_debugger state-schema validate --fixtures --trace-dir audit\boss_ai_trace
python -m tools.boss_ai_debugger state-schema validate --path path\to\scenario.json
python -m tools.boss_ai_debugger state-schema validate --path audit\boss_ai_trace\falkner_live.txt
```

Emit JSON:

```powershell
python -m tools.boss_ai_debugger state-schema validate --json
```

## Current Contract

Fixture and scenario states must keep these concepts structured:

- `state.boss.active`
- `state.player.active`
- active `species`
- active `hp`
- active `status`
- optional `state.field`
- action or move `id`
- action or move `name`
- optional generated `state_hash`, `rom_sha256`, and `symbols_sha256` as
  uppercase SHA-256 hex digests

Trace captures must include:

- `trace_rom_sha256`
- `trace_symbols_sha256`
- `tier`
- four `move_ids`
- four `move_scores`
- optional four `pre_model_scores`
- optional four `post_model_scores`

The validator rejects public-only data containing obvious hidden/private fields,
including `hidden_moves`, `hidden_move_slots`, `private_moves`, `move_slots`,
`current_input`, `selected_move`, and `selected_action`.

## Why This Exists

The next debugger phases need one input surface for:

- preference fixtures
- generated JSON/JSONL scenarios
- live trace captures
- minimized repros
- mastery-derived quick tests

This validation layer is intentionally stricter than normal prose docs. If a
future scenario needs hidden data for a Haki-only or oracle-only task, it should
mark that explicitly instead of slipping private information into a public-only
state.
