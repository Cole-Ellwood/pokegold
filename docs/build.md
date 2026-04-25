# Build Notes

## Environment
- Repo: `pokemon gold hack`
- Date refreshed: 2026-04-25
- Required build tools: `make`, `gcc`, `python`, and RGBDS.
- Release patch tooling: `flips`.
- Windows note: this Codex PowerShell session did not have `make` on `PATH`; use MSYS2/Git Bash or another shell with `make` available.

## Baseline identity (clean pret/pokegold Gold)
- SHA1: `d8b8a3600a465308c9953dfa04f0081c05bdcb94`
- SHA256: `fb0016d27b1e5374e1ec9fcad60e6628d8646103b5313ca683417f52b97e7e4e`

## Build commands
```bash
make tidy
make -j2
make DEBUG=1 compare
```

## Release artifact workflow
```bash
flips --create --bps .local/roms/pokegold-baseline.gbc pokegold.gbc dist/pokegold-data-rebalance.bps
flips --apply dist/pokegold-data-rebalance.bps .local/roms/pokegold-baseline.gbc .local/roms/pokegold-roundtrip-current.gbc
```

Release ROMs, patches, and checksum summaries are generated artifacts. Keep them out of ordinary source cleanup commits unless cutting a release.
