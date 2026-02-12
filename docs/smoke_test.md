# Smoke Test Checklist

Manual validation checklist for the `-data-rebalance` build.

## Modified moves (at least 3)

- [ ] Verify `CUT` increased damage and perfect hit rate (`power 60`, `accuracy 100`).
- [ ] Verify `FIRE_SPIN` increased damage and accuracy with reduced PP (`power 25`, `accuracy 85`, `pp 10`).
- [ ] Verify `MUD_SLAP` increased damage (`power 30`) while retaining accuracy drop effect.

## Modified Pokemon statlines (at least 3)

- [ ] Verify `MEGANIUM` statline increase on status screen or in-battle survivability/damage.
- [ ] Verify `TYPHLOSION` statline increase on status screen or in-battle output.
- [ ] Verify `FERALIGATR` statline increase on status screen or in-battle output.

## Modified typing interactions (at least 2)

- [ ] Verify `MEGANIUM` now has `GRASS/NORMAL` interaction (STAB behavior and type effectiveness checks).
- [ ] Verify `FERALIGATR` now has `WATER/FIGHTING` interaction (STAB behavior and type effectiveness checks).

## Learnset changes (at least 3)

- [ ] Verify `MEGANIUM` learns `EARTHQUAKE` at Lv51 instead of `SAFEGUARD`.
- [ ] Verify `TYPHLOSION` learns `THUNDERPUNCH` at Lv45 instead of `SWIFT`.
- [ ] Verify `FERALIGATR` learns `CRUNCH` at Lv47 instead of `SCREECH`.
