# Boss AI Debugger Metamorphic Checks

Status: Phase-5 foundation.

`tools/boss_ai_debugger/metamorphic.py` captures relations that should hold
across families of scenarios even when there is no separate hand-authored label
for every state.

## Command

```powershell
python -m tools.boss_ai_debugger metamorphic --generated 100 --seed 1 --fail-on-mismatch
```

## Current Relations

- Equal scores roll only the first best and first second slot.
- Blocked scores have zero selector probability.
- A third slot tied for second is still never rolled.
- Active revealed Rapid Spin discourages extra Spikes layers when no spinblock
  protects the stack.
- Unrevealed Rapid Spin does not suppress third-layer Spikes.
- Active non-Foresighted Ghost spinblock softens revealed-spin panic enough to
  keep Spikes live.
- Generated smoke scenarios do not roll catastrophic actions.

## Role

Metamorphic checks are not a replacement for ROM traces. They are cheap,
high-throughput guardrails for invariants that should survive refactors,
generator changes, and future Python mirror work.
