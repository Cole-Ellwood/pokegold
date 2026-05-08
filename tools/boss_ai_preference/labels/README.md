# Boss AI Preference Feedback

The default pairwise preference file is `boss_ai_pairwise_preferences.jsonl`.
The older single-action label file is `boss_ai_labels.jsonl`.

It is intentionally not pre-populated. Use either the local UI or the CLI:

```powershell
python -m tools.boss_ai_preference serve
python -m tools.boss_ai_preference prefer --fixture-id <id> --action-a-id <id> --action-b-id <id> --choice a_better
python -m tools.boss_ai_preference label --fixture-id <id> --action-id <id> --label best
```
