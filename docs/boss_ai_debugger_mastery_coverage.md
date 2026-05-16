# Boss AI Debugger Mastery And Coverage Indexes

Status: Phase-7 foundation plus early coverage reporting.

## Commands

```powershell
python -m tools.boss_ai_debugger mastery-index build
python -m tools.boss_ai_debugger coverage-report --generated-count 250 --seed 1
python -m tools.boss_ai_debugger coverage-report --changed-file engine\battle\ai\boss_policy_move.asm
```

`mastery-index build` parses:

- `docs/pokemon_mastery/policy_cards/*.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/workspace/quick_tests/*.md`
- `docs/pokemon_mastery/reviews/*.md`

It is the explicit command that writes `audit/boss_ai_debugger/mastery_index.json`.
`coverage-report` reads the same mastery sources but does not refresh that
artifact as a side effect.

`coverage-report` combines:

- Boss AI source rule-map counts
- generated scenario policy tags
- generated scenario condition tags
- generated evidence refs
- policy-card coverage from generated evidence refs
- positive and negative scenario coverage for each policy card
- ROM hook contribution trace artifact summaries when available
- uncovered mapped Boss AI rule ids with suggested generator families
- changed-file rule coverage for targeted Boss AI edits
- known gaps, including the fact that dynamic rule-entry coverage is not full
  public-read slicing

## Current Meaning

This is not final coverage. It is a useful early report that prevents us from
mistaking a narrow generator for broad mastery coverage. For example, the first
generator family covers the hazard/spin card but intentionally leaves other
policy cards uncovered until their scenario families exist.

ROM contribution trace coverage now has two levels. Dynamic rule-entry coverage
means a mapped executable rule label ran in a trace artifact. Score-delta
coverage means a score helper changed or attempted to change a candidate score
inside that rule. Neither level means every false branch or every public memory
read was dynamically proven.

Changed-file coverage is a targeting aid. It identifies mapped source labels in
the supplied files and shows which of those labels are not covered by current
dynamic rule-entry trace artifacts.

Policy-card requirement coverage is stricter than a file reference. Each card
reports whether generated scenarios include at least one expected-best line and
at least one bad or catastrophic line tied to that card.
