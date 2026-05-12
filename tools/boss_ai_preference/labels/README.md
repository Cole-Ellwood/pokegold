# Boss AI Preference Feedback

The default pairwise preference file is `boss_ai_pairwise_preferences.jsonl`.
The older single-action label file is `boss_ai_labels.jsonl`.
Multi-turn Coach Mode writes trajectory preferences to
`boss_ai_trajectory_preferences.jsonl` and missing-plan demonstrations to
`boss_ai_plan_demonstrations.jsonl`.

It is intentionally not pre-populated. Use either the local UI or the CLI:

```powershell
python -m tools.boss_ai_preference serve
python -m tools.boss_ai_preference plan-queue
python -m tools.boss_ai_preference trajectory-report
python -m tools.boss_ai_preference final-report
python -m tools.boss_ai_preference prefer --fixture-id <id> --action-a-id <id> --action-b-id <id> --choice a_better
python -m tools.boss_ai_preference label --fixture-id <id> --action-id <id> --label best
```

Coach Mode saves all shown plan pairs covered by one answer and records source
hashes. After roster or fixture edits, run `final-report` to find stale or
incomplete training signal before using the notes for scoring work.
