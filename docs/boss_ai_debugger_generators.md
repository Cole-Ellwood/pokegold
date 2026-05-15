# Boss AI Debugger Scenario Generators

Status: Phase-1/Phase-4 bridge.

The generator module in `tools/boss_ai_debugger/generators.py` creates
deterministic JSONL scenarios for the existing ROM-score batch simulator. These
are not full PyBoy materialized states yet. They are high-throughput review
inputs that preserve policy expectations and evidence references.

## Commands

Generate Spikes / Rapid Spin boundary cases:

```powershell
python -m tools.boss_ai_debugger generate --family spikes_spin --count 10000 --seed 1 --out audit\boss_ai_debugger\generated\spikes_spin.jsonl
```

Generate selector edge cases:

```powershell
python -m tools.boss_ai_debugger generate --family selector_edges --count 1000 --seed 1 --out audit\boss_ai_debugger\generated\selector_edges.jsonl
```

Validate and evaluate:

```powershell
python -m tools.boss_ai_debugger state-schema validate --path audit\boss_ai_debugger\generated\spikes_spin.jsonl
python -m tools.boss_ai_debugger batch-simulate --scenarios audit\boss_ai_debugger\generated\spikes_spin.jsonl --limit 50
python -m tools.boss_ai_debugger review-queue --scenarios audit\boss_ai_debugger\generated\spikes_spin.jsonl --limit 50
```

## Families

- `selector_edges`: score-byte selector surfaces such as all-equal scores,
  blocked moves, tied third slots, and wide best-vs-second gaps.
- `spikes_spin`: hazard retention cases around Spikes layers, active revealed
  Rapid Spin, Ghost spinblock, Foresight, reserve Ghosts, bench revealed Spin,
  active species Spin priors, and immediate pressure.
- `all`: round-robin mix of implemented families.

## Review Shape

Each generated scenario includes:

- deterministic `seed` and `case_index`
- generated `family`
- ROM-score moves and deltas
- `best_action_ids`
- `acceptable_action_ids`
- `bad_action_ids`
- `policy_tags`
- `condition_tags`
- `evidence_refs`
- `why`
- `answer_changing_information`

That makes `batch-simulate` useful as a first review queue: it ranks
catastrophic rolls, bad rolls, zero-probability best actions, and ordinary
mismatches before passing cases. The dedicated `review-queue` command can read
either scenarios or a saved batch JSON report and emits the compact list to
stdout or JSON.
