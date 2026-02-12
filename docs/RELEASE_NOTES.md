# Pokémon Gold Data-Only Rebalance — Release v1

## Scope
This release includes data-only rebalance updates through Batch 5:
- Pokemon base stats
- Gen 2 type assignments
- Move parameters
- Level-up learnsets
- TM compatibility

This release does not include:
- Engine code or mechanics changes
- Script/map/text changes
- New moves or new type IDs

## Contents
- `dist/pokegold-data-rebalance.bps`
- `dist/checksums.txt`
- `docs/CHANGES.txt`
- `docs/CHANGES_BY_CATEGORY.txt`

## Requirements
Use the expected clean `pret/pokegold` Pokemon Gold base ROM:
- Baseline SHA1: `d8b8a3600a465308c9953dfa04f0081c05bdcb94`
- Baseline SHA256: `fb0016d27b1e5374e1ec9fcad60e6628d8646103b5313ca683417f52b97e7e4e`

If the base ROM differs from this identity, patching should fail or produce invalid output.

## How to apply the patch
### Option A (GUI): Floating IPS (Flips)
1. Open Flips and choose `Apply Patch`.
2. Select `dist/pokegold-data-rebalance.bps`.
3. Select the baseline ROM matching the hashes above.
4. Choose an output filename and save.

### Option B (Web): Rom Patcher JS
1. Open Rom Patcher JS.
2. Load the baseline ROM.
3. Load `dist/pokegold-data-rebalance.bps`.
4. Apply the patch.
5. Download/save the patched ROM.

## Verification
Compute SHA1 of your patched ROM and compare against:
- Patched ROM SHA1: `7de0879a59d3cdfcdc70ea714ecdc7d543f8c7ca`

Also verify the patch file integrity:
- Patch SHA1 (`dist/pokegold-data-rebalance.bps`): `9cda959bd010e842af59cb2e0df8e0545c9ee2e7`

## Changelog (high level)
- Batch 1 through Batch 5 include broad Pokemon base stat rebalances.
- Gen 2 type reassignments were applied to selected species.
- Move parameter adjustments were applied to selected moves.
- Level-up learnsets were updated for selected Pokemon lines.
- TM compatibility updates are included in this data-only release.

Full details:
- `docs/CHANGES.txt`
- `docs/CHANGES_BY_CATEGORY.txt`

## Build notes (for maintainers)
- Build command: `make RGBDS=rgbds-1.0.1/ gold`
- Local ROM path convention: `.local/roms/`
- `dist/` tracks checksums and patch artifacts; ROM binaries are not tracked.

## Provenance
- Branch: `pm/gsc-data-rebalance`
- Latest data batch commit: `2a807415` (`data: batch5 pokemon rebalance`)
- Date: `2026-02-12`
