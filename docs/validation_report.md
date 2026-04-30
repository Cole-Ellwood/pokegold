# Validation Report

Date: 2026-04-28

## Build and artifact checks
- PowerShell `make` lookup : BLOCKED in this Codex PowerShell session (`make` is not on `PATH`)
- WSL `make` lookup : PASS (`/usr/bin/make`)
- `make -j4 ... pokegold.gbc` via WSL with explicit repo-local RGBDS `.exe` tools : PASS
- `make -j4 ... pokesilver.gbc` via WSL with explicit repo-local RGBDS `.exe` tools : PASS
- `make gold silver gold_debug silver_debug` : NOT RUN as a single target group
- `make DEBUG=1 compare` : NOT RUN
- BPS roundtrip: PASS

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
- 2026-04-28 BPS refresh: `dist/pokegold-data-rebalance.bps` was regenerated
  from `.local/roms/pokegold-baseline.gbc` to the current source-built
  `pokegold.gbc`.
- `dist/checksums.txt` now matches the current clean baseline, hacked Gold ROM,
  and BPS patch hashes.
- The ignored local release/play copies
  `.local/roms/pokegold-data-rebalance.gbc`,
  `.local/roms/pokegold-data-rebalance-play.gbc`,
  `.local/roms/pokegold-release.gbc`, and the BPS roundtrip output
  `.local/roms/pokegold-roundtrip-current.gbc` all match current `pokegold.gbc`.
- `roms.sha1` was not updated because this was a BPS package refresh, not a
  full compare/debug/VC artifact pass.
- `docs/RELEASE_NOTES.md` scope updated to include mechanics/AI/script changes.
- `docs/manifest.md` explicitly marked as data-layer-only historical manifest.

## Known residual risk
- No full emulator playthrough is automated in this repository; progression softlock and pacing validation still depend on manual playtesting.
- No automated check can fully validate the First-Playthrough Promise: restored
  uncertainty, scary-but-fair bosses, surprising weak-Pokemon roles, and QoL
  that preserves journey pressure still require play experience.
