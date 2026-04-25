# Smoke Test Checklist

Automated release-smoke checks for this branch.

Command:
```bash
python tools/audit/check_release_smoke.py
```

Status (2026-04-25):
- [x] Key move entries validated (`CUT`, `FIRE_SPIN`, `MUD_SLAP`).
- [x] Starter final evolution stats/types validated (`MEGANIUM`, `TYPHLOSION`, `FERALIGATR`).
- [x] Key learnset entries validated for final evolutions.
- [x] Core module wiring validated (`move_reminder`, `tm_tutor`, `boss ai`, specials pointer).

Additional automated audits (run separately):
- [x] `python tools/audit/check_docs_navigation.py`
- [x] `python tools/audit/check_ai_tiers.py`
- [x] `python tools/audit/check_boss_ai_gating.py`
- [x] `python tools/audit/check_boss_ai_no_cheat.py`
- [x] `python tools/audit/check_boss_items_present.py`
- [x] `python tools/audit/check_boss_moves_complete.py`
- [x] `python tools/audit/check_battle_math_safety.py`
