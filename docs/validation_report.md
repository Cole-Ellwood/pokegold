# Validation Report

Date: 2026-04-25

## Build and artifact checks
- PowerShell `make` lookup : BLOCKED in this Codex PowerShell session (`make` is not on `PATH`)
- WSL `make` lookup : PASS (`/usr/bin/make`)
- `make -j4 ... pokegold.gbc` via WSL with explicit repo-local RGBDS `.exe` tools : PASS
- `make -j4 ... pokesilver.gbc` via WSL with explicit repo-local RGBDS `.exe` tools : PASS
- `make gold silver gold_debug silver_debug` : NOT RUN as a single target group
- `make DEBUG=1 compare` : NOT RUN
- BPS roundtrip: NOT RUN

## Automated gameplay/config audits
- `python tools/audit/check_docs_navigation.py` : PASS
- `python tools/audit/check_release_smoke.py` : PASS
- `python tools/audit/check_ai_tiers.py` : PASS
- `python tools/audit/check_boss_ai_gating.py` : PASS
- `python tools/audit/check_boss_ai_no_cheat.py` : PASS
- `python tools/audit/check_boss_items_present.py` : PASS
- `python tools/audit/check_boss_moves_complete.py` : PASS
- `python tools/audit/check_battle_math_safety.py` : PASS

## Release metadata sync
- `dist/checksums.txt` and regenerated BPS artifacts are intentionally not committed on the source cleanup branch.
- `roms.sha1` was not updated because a full compare/release artifact pass was not run.
- `docs/RELEASE_NOTES.md` scope updated to include mechanics/AI/script changes.
- `docs/manifest.md` explicitly marked as data-layer-only historical manifest.

## Known residual risk
- No full emulator playthrough is automated in this repository; progression softlock and pacing validation still depend on manual playtesting.
