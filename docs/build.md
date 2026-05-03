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

## Release artifact workflow (retired)

The `dist/` BPS distribution channel was retired 2026-05-03. The
artifacts (`dist/pokegold-data-rebalance.bps`, `dist/checksums.txt`)
were removed because the `flips` tool that generated them is no longer
available in this environment, so the channel could not be kept fresh.
Stale BPS patches that would produce a non-current ROM are worse than
no patches.

If you set up a new release pipeline, the prior recipe was:

```bash
flips --create --bps .local/roms/pokegold-baseline.gbc pokegold.gbc dist/pokegold-data-rebalance.bps
flips --apply dist/pokegold-data-rebalance.bps .local/roms/pokegold-baseline.gbc .local/roms/pokegold-roundtrip-current.gbc
```

`tools/make_patch.exe` produces VC patches, not BPS, and is not a
substitute. Pick a tool, recreate `dist/`, and update CLAUDE.md's
"Never hand-edit these" note + this section.

Release ROMs, patches, and checksum summaries remain generated
artifacts. Keep them out of ordinary source cleanup commits unless
cutting a release.
