# Pokemon Gold Gameplay Overhaul — Release Candidate

Date: 2026-04-25

## Scope
This build is no longer data-only. It includes:
- Data rebalance (stats, moves, types, learnsets, trainers, wilds, items)
- Battle mechanics additions (type passives, late-gen held effects, hazard rework)
- Boss AI and trainer AI tiering logic
- Progression/script additions (TM Tutor, Move Reminder, gym voucher rewards)
- Evolution flow changes (branching level-evolution choice handling)

Detailed mechanics summary:
- `docs/mechanics_changes_from_base.md`

## Release artifacts
Release ROMs, patches, and checksum summaries are generated separately when cutting a release.
The source cleanup branch intentionally does not commit regenerated ROM/BPS artifacts.

## Required clean base ROM
- Baseline SHA1: `d8b8a3600a465308c9953dfa04f0081c05bdcb94`
- Baseline SHA256: `fb0016d27b1e5374e1ec9fcad60e6628d8646103b5313ca683417f52b97e7e4e`

## Validation status
- Source audits: release smoke, boss AI, trainer tier, item/move completeness, and battle math checks pass.
- Build pipeline: PowerShell does not have `make` on `PATH`, but WSL `make`
  works in this checkout with explicit repo-local RGBDS `.exe` variables; Gold
  and Silver normal ROM builds passed on 2026-04-25.
- Report: `docs/validation_report.md`

## Notes
- `make compare` now uses a repo-local Python hash verifier (`tools/verify_sha1.py`) instead of requiring `shasum`/`sha1sum`.
- `make tidy`/`make clean` now use repo-local cross-platform file removal helpers, so cleanup works in Windows shells without `rm`.
