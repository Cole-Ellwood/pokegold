# Damage Delta Heatmap

Generated from `tools/audit/balance_diff.py` using `tools.damage_debugger.oracle`.

## Scope

- Schema: `damage-delta-heatmap.v1`
- Levels: 50
- Base combinations scored: 50000
- Variant rows scored: 146354
- Truncated by max-combo limit: True
- Stats use a deterministic max-DV/no-stat-exp level proxy, not party data.
- Variants compare against no item / no weather / no badge baseline.

## Largest Deltas

| Delta | Pct | Variant | Damage | Base | Level | Attacker | Defender | Move | Type | Cat |
| ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- | --- | --- |
| +751 | +49.6% | `choice_specs` | 2266 | 1515 | 50 | `BELLOSSOM` | `WOOPER` | `SOLARBEAM` | `GRASS` | special |
| +681 | +49.7% | `choice_specs` | 2052 | 1371 | 50 | `BELLOSSOM` | `RHYHORN` | `SOLARBEAM` | `GRASS` | special |
| +681 | +49.7% | `choice_specs` | 2052 | 1371 | 50 | `BELLOSSOM` | `GEODUDE` | `SOLARBEAM` | `GRASS` | special |
| +515 | +49.5% | `choice_specs` | 1556 | 1041 | 50 | `BELLOSSOM` | `KABUTO` | `SOLARBEAM` | `GRASS` | special |
| +502 | +49.5% | `choice_specs` | 1516 | 1014 | 50 | `BELLOSSOM` | `RHYDON` | `SOLARBEAM` | `GRASS` | special |
| +502 | +49.5% | `choice_specs` | 1516 | 1014 | 50 | `BELLOSSOM` | `ONIX` | `SOLARBEAM` | `GRASS` | special |
| +502 | +49.5% | `choice_specs` | 1516 | 1014 | 50 | `BELLOSSOM` | `GRAVELER` | `SOLARBEAM` | `GRASS` | special |
| +501 | +49.4% | `choice_specs` | 1515 | 1014 | 50 | `BAYLEEF` | `WOOPER` | `SOLARBEAM` | `GRASS` | special |
| -494 | -32.6% | `eviolite_defender` | 1021 | 1515 | 50 | `BELLOSSOM` | `WOOPER` | `SOLARBEAM` | `GRASS` | special |
| -494 | -32.6% | `assault_vest` | 1021 | 1515 | 50 | `BELLOSSOM` | `WOOPER` | `SOLARBEAM` | `GRASS` | special |
| +489 | +49.8% | `choice_specs` | 1470 | 981 | 50 | `BELLSPROUT` | `WOOPER` | `SOLARBEAM` | `GRASS` | special |
| +462 | +49.9% | `choice_band` | 1388 | 926 | 50 | `BEEDRILL` | `CHANSEY` | `SLUDGE_BOMB` | `POISON` | physical |
| -456 | -33.3% | `eviolite_defender` | 915 | 1371 | 50 | `BELLOSSOM` | `RHYHORN` | `SOLARBEAM` | `GRASS` | special |
| -456 | -33.3% | `assault_vest` | 915 | 1371 | 50 | `BELLOSSOM` | `RHYHORN` | `SOLARBEAM` | `GRASS` | special |
| +456 | +48.8% | `choice_specs` | 1390 | 934 | 50 | `BELLOSSOM` | `LARVITAR` | `SOLARBEAM` | `GRASS` | special |
| -456 | -33.3% | `eviolite_defender` | 915 | 1371 | 50 | `BELLOSSOM` | `GEODUDE` | `SOLARBEAM` | `GRASS` | special |
| -456 | -33.3% | `assault_vest` | 915 | 1371 | 50 | `BELLOSSOM` | `GEODUDE` | `SOLARBEAM` | `GRASS` | special |
| +448 | +48.5% | `choice_specs` | 1371 | 923 | 50 | `BAYLEEF` | `RHYHORN` | `SOLARBEAM` | `GRASS` | special |
| +448 | +48.5% | `choice_specs` | 1371 | 923 | 50 | `BAYLEEF` | `GEODUDE` | `SOLARBEAM` | `GRASS` | special |
| +445 | +49.4% | `choice_specs` | 1345 | 900 | 50 | `BELLOSSOM` | `MAGIKARP` | `SOLARBEAM` | `GRASS` | special |
| +437 | +49.2% | `choice_specs` | 1326 | 889 | 50 | `BELLSPROUT` | `RHYHORN` | `SOLARBEAM` | `GRASS` | special |
| +437 | +49.2% | `choice_specs` | 1326 | 889 | 50 | `BELLSPROUT` | `GEODUDE` | `SOLARBEAM` | `GRASS` | special |
| +433 | +48.7% | `choice_specs` | 1322 | 889 | 50 | `BELLOSSOM` | `OMANYTE` | `SOLARBEAM` | `GRASS` | special |
| +418 | +49.6% | `choice_band` | 1260 | 842 | 50 | `AZUMARILL` | `CHANSEY` | `DYNAMICPUNCH` | `FIGHTING` | physical |
| -414 | -50.2% | `rain` | 410 | 824 | 50 | `ARCANINE` | `WEEDLE` | `FIRE_BLAST` | `FIRE` | special |
| -414 | -50.2% | `rain` | 410 | 824 | 50 | `ARCANINE` | `CATERPIE` | `FIRE_BLAST` | `FIRE` | special |
| +412 | +50.0% | `sun` | 1236 | 824 | 50 | `ARCANINE` | `WEEDLE` | `FIRE_BLAST` | `FIRE` | special |
| +412 | +50.0% | `choice_specs` | 1236 | 824 | 50 | `ARCANINE` | `WEEDLE` | `FIRE_BLAST` | `FIRE` | special |
| +412 | +50.0% | `sun` | 1236 | 824 | 50 | `ARCANINE` | `CATERPIE` | `FIRE_BLAST` | `FIRE` | special |
| +412 | +50.0% | `choice_specs` | 1236 | 824 | 50 | `ARCANINE` | `CATERPIE` | `FIRE_BLAST` | `FIRE` | special |
| -396 | -50.0% | `rain` | 396 | 792 | 50 | `ARCANINE` | `PARAS` | `FIRE_BLAST` | `FIRE` | special |
| +396 | +50.0% | `sun` | 1188 | 792 | 50 | `ARCANINE` | `PARAS` | `FIRE_BLAST` | `FIRE` | special |
| +388 | +49.0% | `choice_specs` | 1180 | 792 | 50 | `ARCANINE` | `PARAS` | `FIRE_BLAST` | `FIRE` | special |
| +385 | +49.5% | `choice_specs` | 1162 | 777 | 50 | `BELLOSSOM` | `SHELLDER` | `SOLARBEAM` | `GRASS` | special |
| +385 | +49.5% | `choice_specs` | 1162 | 777 | 50 | `BELLOSSOM` | `KRABBY` | `SOLARBEAM` | `GRASS` | special |
| +385 | +49.5% | `choice_specs` | 1162 | 777 | 50 | `BELLOSSOM` | `HORSEA` | `SOLARBEAM` | `GRASS` | special |
| +359 | +49.0% | `choice_specs` | 1092 | 733 | 50 | `BELLOSSOM` | `QUAGSIRE` | `SOLARBEAM` | `GRASS` | special |
| +358 | +50.0% | `choice_band` | 1074 | 716 | 50 | `BEEDRILL` | `BLISSEY` | `SLUDGE_BOMB` | `POISON` | physical |
| +358 | +50.0% | `choice_band` | 1074 | 716 | 50 | `ARIADOS` | `CHANSEY` | `SLUDGE_BOMB` | `POISON` | physical |
| -358 | -50.1% | `rain` | 356 | 714 | 50 | `ARCANINE` | `METAPOD` | `FIRE_BLAST` | `FIRE` | special |

## Type Summary

| Move Type | Rows | Avg Abs Delta | Max Abs Delta |
| --- | ---: | ---: | ---: |
| `GRASS` | 12990 | 29.40 | 751 |
| `POISON` | 4305 | 23.51 | 462 |
| `FIGHTING` | 7995 | 12.91 | 418 |
| `FIRE` | 10944 | 34.22 | 414 |
| `STEEL` | 5535 | 23.80 | 342 |
| `NORMAL` | 41820 | 16.07 | 308 |
| `ELECTRIC` | 9526 | 25.50 | 296 |
| `ICE` | 12124 | 21.49 | 268 |
| `DARK` | 5535 | 15.89 | 240 |
| `PSYCHIC_TYPE` | 8660 | 27.74 | 228 |
| `ROCK` | 1230 | 18.65 | 213 |
| `BUG` | 3075 | 9.70 | 200 |
| `GROUND` | 7504 | 12.54 | 190 |
| `GHOST` | 1845 | 10.19 | 188 |
| `WATER` | 8208 | 14.07 | 183 |
| `FLYING` | 2460 | 25.02 | 180 |
| `DRAGON` | 2598 | 18.83 | 90 |
