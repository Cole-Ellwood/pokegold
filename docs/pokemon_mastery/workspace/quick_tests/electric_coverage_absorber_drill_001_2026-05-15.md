# Electric Coverage Absorber Drill 001 - 2026-05-15

Mode: constructed nonblind regression probe from
`side_known_transfer_019_gen2ou-2608645646`. This is not fresh progress proof.

## Score Summary

Scenarios: 4.
Policy hits: 4/4.
Severe blunders: 0.
Hidden-info errors: 0.
Mechanics errors: 0.

## Scenario 1 - Current Status Converts

Prompt:
Zapdos faces unrevealed Jolteon. Nidoking can absorb Electric STAB, but
Jolteon commonly carries Hidden Power Ice or Water. Zapdos can safely Thunder
Wave Jolteon this turn.

Frozen answer:
Use Thunder Wave. Do not make Nidoking top unless the Hidden Power fallback is
acceptable or the current move fails to convert.

Answer key: hit.

## Scenario 2 - Ground Absorber Still Correct

Prompt:
Zapdos is too low to survive or cannot meaningfully status/damage Jolteon, and
Nidoking survives the likely Hidden Power while threatening sleep or Earthquake.

Frozen answer:
Switch Nidoking, explicitly naming Hidden Power as the priced fallback.

Answer key: hit.

## Scenario 3 - Revealed Electric Only

Prompt:
Jolteon has revealed only Thunderbolt and Baton Pass, and the branch is a dry
pass rather than coverage. Nidoking enters safely and creates immediate sleep
pressure.

Frozen answer:
Nidoking can be top, with coverage still labeled as a fallback branch.

Answer key: hit.

## Scenario 4 - Revealed Coverage

Prompt:
Jolteon has revealed Hidden Power Ice and Nidoking is in range to be removed.

Frozen answer:
Do not use Nidoking as the owner. Keep current status/damage or use a special
wall that survives the revealed coverage.

Answer key: hit.

