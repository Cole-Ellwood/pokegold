# Boss AI Debugger Mastery And Coverage Indexes

Status: Phase-7 foundation plus early coverage reporting.

## Commands

```powershell
python -m tools.boss_ai_debugger mastery-index build
python -m tools.boss_ai_debugger coverage-report --generated-count 250 --seed 1
```

`mastery-index build` parses:

- `docs/pokemon_mastery/policy_cards/*.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/*.md`
- `docs/pokemon_mastery/reviews/*.md`

`coverage-report` combines:

- Boss AI source rule-map counts
- generated scenario policy tags
- generated scenario condition tags
- generated evidence refs
- policy-card coverage from generated evidence refs
- known gaps, including lack of full ROM scoring contribution trace coverage

## Current Meaning

This is not final coverage. It is a useful early report that prevents us from
mistaking a narrow generator for broad mastery coverage. For example, the first
generator family covers the hazard/spin card but intentionally leaves other
policy cards uncovered until their scenario families exist.
