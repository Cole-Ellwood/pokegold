# Poison Clock Spin Loop Unlabeled Probe 001 - 2026-05-14

Mode: constructed unlabeled regression. This is not a fresh replay score,
holdout, or final exam. I authored the prompts, so count it only as a quick
probe that checks whether the threshold question is now named before choosing
Surf, Rapid Spin, Recover, or status in Starmie/Cloyster hazard loops.

Purpose: test the `replay_turn_pause_032` lesson without scenario labels. The
target mistake is treating "damage the Cloyster" or "spin the Spikes" as a
fixed rule instead of first asking whether damage removes the setter before it
can reset Spikes, whether our side is already clear, and whether Starmie is too
low to spend.

Local docs checked:

- `docs/pokemon_mastery/quick_tests/poison_clock_spin_loop_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_032_spin_vs_damage_boundary_transfer_smogtours-gen2ou-852072_2026-05-14.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`

Web sources checked:

- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC OU Cloyster discussion:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`

Source note: the Spikes article frames GSC hazard play around Cloyster,
Starmie, Rapid Spin, Toxic pressure, Recover timing, and the need to keep or
remove Spikes as a route subgame. This probe does not add a new policy entry;
it tests the existing STP-053 boundary.

## Procedure

Six neutral cases were written as A-F instead of policy labels. The answer key
was frozen before comparing the cases against the prior probe. Because the
same session generated the cases, this is weak calibration and should not be
treated as evidence of fresh transfer.

Scoring fields:

- action-policy hit: selected the right action class;
- threshold-check hit: explicitly named the condition that flips the move;
- severe blunder: gave the opponent a clean hazard/spinner conversion or spent
  Starmie without a route.

## Case A

Public state:

```text
Vanilla GSC. Our Starmie is 58% and badly poisoned. It has Rapid Spin, Surf,
Recover, and Thunder. Both sides have Spikes. Opposing Cloyster is 43% and
poisoned. Surf does not remove Cloyster before it can reset Spikes.
```

Recommendation: Rapid Spin, confidence medium-high.

Route reason: if Surf is not a confirmed removal threshold, the current route
is to clear our side while poison handles Cloyster and forces later timing.

Serious alternatives: Recover if Starmie must survive a later Electric or
Ground check; Surf only if a calc or observed roll makes removal real.

Worst branch: Cloyster resets Spikes again or switches, but Rapid Spin at least
keeps our side from losing the loop immediately.

Score: action-policy hit, threshold-check hit.

## Case B

Public state:

```text
Vanilla GSC. Our Starmie is 61% and badly poisoned. Our side is clear; the
opponent's side has Spikes. Opposing Cloyster is 76% and poisoned. Starmie has
Rapid Spin, Surf, Recover, and Thunder.
```

Recommendation: Surf or Recover depending on the preservation map; do not
Rapid Spin.

Route reason: there is no value in spinning when our side is already clear.
Use the turn to damage Cloyster or keep Starmie alive for the next hazard
cycle.

Serious alternatives: Recover if poison plus future entries will otherwise
remove Starmie before it can spin again.

Worst branch: Surf damage is too low and Cloyster resets later, but no-value
Spin would spend the turn without improving any route.

Score: action-policy hit, threshold-check hit.

## Case C

Public state:

```text
Vanilla GSC. Our Starmie is 50% and badly poisoned. Both sides have Spikes.
Opposing Cloyster is 32% and poisoned. Surf looks tempting, but prior damage
does not prove that Surf KOs from this band.
```

Recommendation: Rapid Spin unless the observed damage range confirms Surf KOs.

Route reason: this is the false-KO range. If Surf leaves Cloyster alive, it
resets Spikes and poison was already doing the removal work.

Serious alternatives: Surf becomes correct only after exact range evidence.
Recover is plausible if Starmie cannot survive the next poison/entry sequence.

Worst branch: overcalling the KO lets Cloyster keep the hazard loop while
Starmie loses poison budget.

Score: action-policy hit, threshold-check hit.

## Case D

Public state:

```text
Vanilla GSC. Our Starmie is 45% and badly poisoned. Both sides have Spikes.
Opposing Cloyster is 23-27% and poisoned. Observed Surf damage confirms the KO.
```

Recommendation: Surf, confidence high.

Route reason: once damage removes Cloyster before a reset, attacking is cleaner
than spinning because it deletes the setter and keeps our Spikes pressure live.

Serious alternatives: Rapid Spin only if Starmie's survival or a specific
endgame requires the clear field more than removing Cloyster.

Worst branch: damage range was misread; if Surf fails, Cloyster resets and the
loop reopens.

Score: action-policy hit, threshold-check hit.

## Case E

Public state:

```text
Vanilla GSC. Our Starmie is 31% and badly poisoned with Rapid Spin, Surf, and
Recover revealed. Both sides have Spikes. Opposing Cloyster is 36% and poisoned.
Surf is not a KO. Starmie is still needed later for a Ground check and one more
hazard-control turn.
```

Recommendation: Recover or switch/preserve, confidence medium.

Route reason: do not autopilot Rapid Spin if Starmie is the irreplaceable
future piece. Spin is correct only if this is Starmie's last required job or if
the clear field immediately unlocks the endgame.

Serious alternatives: Rapid Spin if the rest of the team wins once hazards are
removed; Surf is low value without a KO threshold.

Worst branch: Recover gives Cloyster another setup turn, but losing Starmie can
make the later Ground or hazard route unplayable.

Score: action-policy hit, threshold-check hit.

## Case F

Public state:

```text
Vanilla GSC, reverse side. Our Cloyster is 88% and poisoned with Spikes, Surf,
Toxic, and Explosion revealed. Opposing Starmie is 57%, healthy, and has Rapid
Spin revealed. Both sides have Spikes.
```

Recommendation: Toxic if it can land on Starmie, confidence medium-high.

Route reason: poison is the route pressure that can eventually force Recover
over repeated Rapid Spin. Surf is damage, but Toxic changes the future spin
loop.

Serious alternatives: Surf if Starmie is already in a concrete damage range or
Toxic is blocked by a better absorber; switch if a teammate is the real
spin-punish.

Worst branch: Starmie spins immediately and later Recovers through poison, so
the follow-up must force it out before it can heal freely.

Score: action-policy hit, threshold-check hit.

## Score Summary

Scenarios: 6.

Action-policy hits: 6 / 6.

Threshold-check hits: 6 / 6.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-information errors: 0.

Measurement status: regression only. The false-KO case was useful, but this
still needs fresh replay transfer with unlabeled HP bands.

## Extracted Check

Before choosing Surf or Rapid Spin in the poisoned Starmie/Cloyster loop:

1. Is our side already clear?
2. Does damage remove Cloyster before it can reset Spikes?
3. If damage does not remove Cloyster, is poison already doing that job?
4. Is Starmie too low or too irreplaceable to spend on this turn?
5. Does status change the future spin timing more than immediate damage?
6. What happens after the next poison tick, Recover, reset Spikes, or switch?

## Next Rep

Run a fresh replay transfer with Starmie/Cloyster hazard loops and no prior
HP-band labels. Score whether the answer names the KO threshold before choosing
Surf, Rapid Spin, Recover, Toxic, or a pivot.
