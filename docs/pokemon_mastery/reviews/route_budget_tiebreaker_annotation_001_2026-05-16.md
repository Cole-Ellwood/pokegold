# Route-Budget Tiebreaker Annotation 001 - 2026-05-16

Source packet:
`workspace/quick_tests/side_known_transfer_044_smogtours-gen2ou-821941_p1_2026-05-16.md`

Purpose:
Non-fresh expert annotation after packet 044. These are not proof decisions.
They extract the tiebreaker from turns where the actual move was in the frozen
top three but not ranked first.

## Turn 18

Pressure already created: Skarmory had completed Rest and p2 already had
Spikes on its side. Forretress entered on Skarmory's sleep turn, but p1 still
had healthy Cloyster for the later hazard mirror.

Scarce route piece: Cloyster's HP and status as the only spinner/hazard mirror.
Switching it immediately would spend that piece into a possible Explosion or
status branch before Forretress had shown Spin.

Actual branch covered: Forretress used Spikes, not Rapid Spin. Staying with
sleeping Skarmory preserved Cloyster for the two-sided hazard position that
existed afterward.

Tiebreaker: On a guaranteed Rest sleep turn, if the sleeper is high HP and the
spinner/hazard mirror is still unspent, preserve the mirror unless the
opponent's hazard action creates an immediate unrecoverable reset.

## Turn 19

Pressure already created: both sides had Spikes, Skarmory was waking, and
Forretress had already spent the previous turn setting p1-side Spikes.

Scarce route piece: the precise damage turn before the opponent switched. A
generic phaze kept the route moving, but it did not target the likely Snorlax
receiver as directly as Hidden Power.

Actual branch covered: Snorlax switched in through Spikes and took Hidden Power
chip. My Whirlwind line named Snorlax but converted less precisely.

Tiebreaker: When no setup or immediate reset must be denied, direct damage into
a named receiver can outrank phazing if it improves the forced-choice range on
that receiver.

## Turn 24

Pressure already created: Raikou had absorbed Zapdos but was paralyzed, p1-side
Spikes made future entries costly, and p2 had sleeping Snorlax/Rhydon/Forretress
as grounded counter-owners.

Scarce route piece: Raikou's future Zapdos ownership. Thunderbolt would add
pressure, but it would leave Raikou at a worse entry budget in a game where
Zapdos was repeatedly forcing Spikes tax and phaze sequences.

Actual branch covered: Snorlax switched in while Raikou Rested, preserving the
Electric owner instead of taking the immediate chip line.

Tiebreaker: If the correct absorber is already statused and below future-entry
budget, Rest can be the converter before more damage when the named receivers
do not punish the recovery immediately.

## Turn 28

Pressure already created: Zapdos had revealed Whirlwind, and Heracross was
dragged in by phaze with p1-side Spikes active. Raikou was asleep but still the
typed Zapdos owner.

Scarce route piece: Heracross's HP as a later Snorlax/Rhydon pressure piece.
Megahorn punished Whirlwind/switch branches, but it exposed Heracross to
Thunderbolt for damage that did not force a clear next route.

Actual branch covered: Zapdos stayed and used Thunderbolt. Raikou absorbed the
hit despite paying Spikes.

Tiebreaker: Against revealed Electric/phaze Zapdos, use the typed owner over a
resisted or accuracy-based branch punish unless the attack forces a concrete
range before the Electric hit matters.

## Turn 30

Pressure already created: Zapdos was chipped to 70%, p2-side Spikes were up,
and Snorlax was already the special sponge but had fallen to 63% with p1-side
Spikes still active.

Scarce route piece: Snorlax's HP and future entry count. Double-Edge into the
named Rhydon branch would chip but leave Snorlax low in front of the counter-
owner.

Actual branch covered: Rhydon switched in while Snorlax used Rest, converting
the predicted counter-owner turn into preservation instead of a low-value chip
trade.

Tiebreaker: When the named grounded counter-owner arrives as your absorber is
near future-entry failure, Rest before contact beats chip unless the chip
creates an immediate forced KO, Rest, or phaze-denial route.

## Carry-Forward Rule

Before ranking chip/status/branch punish first, ask:

1. Has Spikes, Rest, phaze, status, or correct-owner handoff already created
   the pressure?
2. Is the current route piece about to become scarce because of future entry
   tax, sleep state, or counter-owner timing?
3. Does the active move force the next choice, or only add damage while the
   scarce piece gets worse?

If pressure already exists and the active move does not force the next choice,
rank preservation, Rest, phaze-on-sleep, or the lower-cost handoff first.
