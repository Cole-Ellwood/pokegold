# Build Notes

## Environment
- Repo: `pokemon gold hack`
- Date refreshed: 2026-04-25
- Required build tools: `make`, `gcc`, `python`, and RGBDS.
- Release patch tooling: `flips`.
- Windows note: this Codex PowerShell session may not have `make` on `PATH`.
  Before declaring builds blocked, check WSL: `bash -lc 'command -v make'`.
  In this checkout, WSL provides `/usr/bin/make`.

Build verification proves assembly/link status, not the First-Playthrough
Promise. Do not treat a successful build as proof that bosses feel fair,
Pokemon roles create discovery, or QoL preserves journey pressure.

## Baseline identity (clean pret/pokegold Gold)
- SHA1: `d8b8a3600a465308c9953dfa04f0081c05bdcb94`
- SHA256: `fb0016d27b1e5374e1ec9fcad60e6628d8646103b5313ca683417f52b97e7e4e`

## Build commands
```bash
make tidy
make -j2
make DEBUG=1 compare
```

## Codex Windows/WSL command pattern
When running from a Codex PowerShell session in this Windows checkout, use WSL
`make` with explicit repo-local RGBDS Windows executables. Do not rely on
`RGBDS=rgbds-1.0.1/` from WSL, because the Makefile will look for extensionless
Linux binaries like `rgbds-1.0.1/rgbasm`.

```powershell
bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'
```

`PYTHON=python3` is required: WSL Ubuntu has no `python` symlink, only `python3`. Without the override, `make tidy` and `make compare` fail with `python: No such file or directory`.

Known-good verification on 2026-04-25:
- `pokegold.gbc` built successfully with the command pattern above.
- `pokesilver.gbc` built successfully with the command pattern above.

## Release artifact workflow
```bash
flips --create --bps .local/roms/pokegold-baseline.gbc pokegold.gbc dist/pokegold-data-rebalance.bps
flips --apply dist/pokegold-data-rebalance.bps .local/roms/pokegold-baseline.gbc .local/roms/pokegold-roundtrip-current.gbc
```

**`flips` is not installed in this environment.** As of 2026-04-30, `which flips` returns not found in both Windows shell and WSL bash on this checkout. Install it before any `dist/*` BPS regen — `tools/make_patch.exe` exists in the repo but produces VC patches, not BPS, and is not a substitute. Per `docs/RELEASE_NOTES.md` source-cleanup branch policy, regenerated ROM/BPS artifacts aren't committed on cleanup branches anyway, so deferring to a release pass is the normal path.

Release ROMs, patches, and checksum summaries are generated artifacts. Keep them out of ordinary source cleanup commits unless cutting a release.
