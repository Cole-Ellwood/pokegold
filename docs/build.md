# Build Notes

## Milestone 0 (Baseline, unmodified)

- Base repo: `https://github.com/pret/pokegold`
- Branch for work: `pm/gsc-data-rebalance`
- Build date: 2026-02-12 10:18:15 -06:00

### Toolchain used

- `rgbds` local folder: `rgbds-1.0.1/` (from official `v1.0.1` Windows release)
- `make` + `gcc` run under MSYS2 bash

### Baseline build command

```bash
cd '/c/Users/Owner/Downloads/pokemon gold hack'
make RGBDS=rgbds-1.0.1/ clean
make RGBDS=rgbds-1.0.1/ gold
```

### Baseline ROM checksums (`pokegold.gbc`)

- SHA1: `d8b8a3600a465308c9953dfa04f0081c05bdcb94`
- SHA256: `fb0016d27b1e5374e1ec9fcad60e6628d8646103b5313ca683417f52b97e7e4e`

## Rebalance build (data-only edits)

### Rebuild command after edits

```bash
cd '/c/Users/Owner/Downloads/pokemon gold hack'
make RGBDS=rgbds-1.0.1/ gold
```

### Rebalance ROM checksums (`pokegold.gbc`)

- SHA1: `6c3f9be8d65f17e21b0d05f7a7f3a0c63ca4dcde`
- SHA256: `fa4560065e4525071b7387c84463dfd4acb6afa16d0ab081b830387ebeb51e25`

### Outputs

- Rebalance ROM copy: `dist/pokegold-data-rebalance.gbc`
- Baseline ROM copy (for diffing): `dist/pokegold-baseline.gbc`
- Patch: `dist/pokegold-data-rebalance.bps`
- Checksums summary: `dist/checksums.txt`
