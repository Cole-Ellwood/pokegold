# Forced Switch Pivot Damage Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression. This is not a fresh replay score
or final-exam evidence.

Purpose: convert `replay_turn_pause_047` into four forced choices around route
ordering, setup greed, and coverage into pivots.

Local docs checked:

- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_047_special_wall_pivot_ladder_transfer_smogtours-gen2ou-925686_2026-05-14.md`

Web sources checked in the parent work block:

- Smogon Forums, GSC Zapdos:
  `https://www.smogon.com/forums/threads/gsc-zapdos.3674240/`
- Smogon Forums, An Analysis of Leads in GSC OU:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`
- Smogon Forums, Skarmory WIP:
  `https://www.smogon.com/forums/threads/skarmory-wip.3687627/`
- Smogon Forums, GSC OU Espeon:
  `https://www.smogon.com/forums/threads/gsc-ou-espeon-qc-1-1-gp-1-1.3667456/`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Classification hits: 4 / 4.

Route-job hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. This should be followed by another fresh
replay transfer before treating the ladder as learned.

## Scenario 1 - Status Clock Before Hazard

Public state:

```text
Vanilla GSC. Our Cloyster is active at 100% against opposing Snorlax at 100%.
Snorlax is already at +1 Attack / +1 Defense from Curse. No Spikes are down.
Cloyster has Toxic, Spikes, and Explosion available.
```

Tempting move: Spikes because hazards are generally high value.

Frozen answer: Toxic. Confidence: medium-high.

Classification: setup-status progress. The immediate route problem is
Curselax snowballing, so the status clock comes before the hazard layer.

Score: pass.

## Scenario 2 - Hazard After Clock

Public state:

```text
Vanilla GSC. Our Cloyster is active at 55% against +1 Snorlax at 93%. Snorlax
is badly poisoned. No Spikes are down. Cloyster is faster because Snorlax has
used Curse.
```

Tempting move: Explosion because Snorlax is the central route piece.

Frozen answer: Spikes. Confidence: medium.

Classification: hazard progress after status. The status clock is already
running, and Cloyster can still deliver the layer before being hit.

Score: pass.

## Scenario 3 - Forced Switch Is Not Free Setup

Public state:

```text
Vanilla GSC. Our Marowak enters at 100% after Cloyster Exploded into a toxic
+1 Snorlax, leaving Snorlax at 27%. The opponent has Spikes on their side and
must strongly consider switching. Exeggutor is a plausible physical-wall pivot.
Marowak has Earthquake and Swords Dance available.
```

Tempting move: Swords Dance on the forced Snorlax exit.

Frozen answer: Earthquake. Confidence: medium.

Classification: direct damage into pivot. A boost is only correct if the
incoming pivot cannot immediately punish it. Exeggutor can threaten status,
Explosion, or a forcing attack, so chip into the pivot is safer.

Score: pass.

## Scenario 4 - Coverage Before Electric STAB

Public state:

```text
Vanilla GSC. Our Zapdos is active and paralyzed against Exeggutor at 73%.
Opponent has Spikes on their side. Steelix has not been revealed but is a
plausible Ground/Steel pivot in the no-preview branch. Zapdos has Thunder and
Hidden Power available.
```

Tempting move: Thunder into the active Exeggutor.

Frozen answer: Hidden Power. Confidence: medium.

Classification: coverage into pivot. Thunder is the stronger active-target
move, but it fails the Ground/Steel pivot branch. Use the coverage move when
it still pressures the current target and avoids giving Steelix a free turn.

Score: pass.

## Resulting Checklist

Before choosing setup or direct damage on a forced response:

1. Does the active route need a clock before hazards?
2. Has the support already been delivered, or can one more support action
   resolve before the punish?
3. Can the expected pivot punish the setup turn immediately?
4. Does a coverage move hit both the current target and the plausible pivot?

## Next Study Target

Fresh replay transfer with the checklist above and a hard stop after the first
two misses.
