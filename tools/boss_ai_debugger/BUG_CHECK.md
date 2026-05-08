# Boss AI Debugger Bug Check

## 2026-05-08 - Phase 1 fixture-backed debugger

Commands:

```powershell
python -m compileall -q tools\boss_ai_debugger tools\boss_ai_preference tools\audit\check_boss_ai_preference.py tools\audit\check_boss_ai_policy_contract.py
python -m tools.boss_ai_debugger list
python -m tools.boss_ai_debugger inspect --fixture-id clair_dragonite_vs_suicune_hidden_ice_beam
python tools\audit\check_boss_ai_preference.py
python tools\audit\check_boss_ai_policy_contract.py
```

Expected:

- fixture-backed inspection prints ranked actions with rule contributions
- judgment recording delegates to the BOSSAI-004 JSONL corpus
- policy contract audit confirms the current source has the accepted simplified
  public-info architecture components
