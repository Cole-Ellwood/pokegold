# Stall Route Budget Review 001 - 2026-05-15

Parent packet:
`workspace/quick_tests/side_known_transfer_039_gen2ou-2588320660_p1_2026-05-15.md`

## Trigger

Packet 039 did not repeat the resisted-Explosion boundary from packet 038. It
instead showed a stall-route budget problem:

- I clicked or ranked extra damage before Rest when Raikou or Misdreavus had
  already forced poison, Spikes, or Rest pressure.
- I treated Protect as passive instead of a route action when it scouts sleep
  or coverage and buys poison/Leftovers turns.
- I used generic wall handoffs instead of the lower-cost absorber that keeps
  the true RestTalk or phazing job available.

## Source Check

Current GSC sources support the repair:

- Smogon's GSC Spikes article describes how Spikes plus phazing forces switches
  and Rest loops; the value is often in denying the reset rather than adding
  one more chip move.
- Smogon Snorlax material reinforces that Rest is a core route-preservation
  tool, especially into Zapdos and Raikou pressure.
- Smogon sample-team material treats Skarmory and RestTalk Raikou as core stall
  job holders, so spending them into the wrong branch can be a route-budget
  mistake even when the switch is safe.
- Smogon good-cores and Misdreavus material support Misdreavus as a long-game
  spinblocker whose Rest can matter more than one more attack.

Sources:

- `https://www.smogon.com/gs/articles/gsc_spikes`
- `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- `https://www.smogon.com/forums/threads/gsc-good-cores.3536015/`
- `https://www.smogon.com/forums/threads/misdreavus-ou-revamp-done.3643258/`

## Diagnosis

The compact cards correctly demand positive selection, but I am sometimes
misclassifying stall-positive moves. In a poison/Spikes/Rest loop, the positive
move is not always damage, phaze, or immediate status. It can be:

- Protect, when it scouts the support package and buys the clock turn;
- Rest, when the public clock has already forced the opponent into Rest,
  poison, or a switch and the current piece must stay usable;
- a lower-cost handoff, when several owners are safe but only one preserves the
  irreplaceable RestTalker, spinblocker, spinner, or phazer;
- exact chip, when it changes the forced Rest/switch choice more than phazing
  by habit.

## Policy Compression

Patch existing tiny cards only:

1. `reset_loop_denial.md`: add that Protect/Rest can be the converter after a
   poison/Spikes clock is already live.
2. `role_package_ledger.md`: mark Protect and Rest as package actions on
   stall structures, not flavor.
3. `spend_or_save_piece.md`: preserve RestTalker/spinblocker/phazer jobs when
   extra chip does not change the next forced choice.

## Next Gate

Run one small nonblind stall-route budget drill, then restart the fresh sample.
Packets 038-039 are still only 60 side decisions after the repair loop, below
the 90-decision / 3-packet structural gate.
