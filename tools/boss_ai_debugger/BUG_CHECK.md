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

## 2026-06-06 - God-level gate bug check

Commands:

```powershell
python -m tools.boss_ai_debugger rule-map check
python tools\audit\check_boss_ai_debugger_foundations.py
python tools\audit\check_boss_ai_debugger_god.py --baseline --read-only
python -m tools.boss_ai_debugger universe
```

Confirmed fixes:

- Refreshed `audit/boss_ai_debugger/rule_map.json` so stored source hashes match
  the current Boss AI source.
- Generated policy-question decision inputs now write their scenario JSONL beside
  an explicit `--decision-input-manifest-out` path instead of mutating the shared
  `.local/tmp/boss_ai_debugger/generated_inputs` cache.
- The deity coverage worklist is again scoped to dynamic coverage targets; the
  God gate owns exhaustive witness-role blockers.

Resolution:

- Restamped the 16 default counterfactual witness materialization artifact
  envelopes to the current universe `class_identity`. A one-off restamp check proved
  the existing witness packets close all 160 missing roles before touching the
  checked-in artifacts.
- `python -m tools.boss_ai_debugger universe` now reports
  `proof_status=complete` and `missing_witness_role_count=0`.
- `python tools\audit\check_boss_ai_debugger_god.py --baseline --read-only`
  now reports `boss_ai_god_ready=True`.
