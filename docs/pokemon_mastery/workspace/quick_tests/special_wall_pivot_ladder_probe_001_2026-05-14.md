# Special-Wall Pivot Ladder Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression. This is not a fresh replay score
or final-exam evidence.

Purpose: convert `replay_turn_pause_046` into four forced classifications:
double when the active attack is covered, use coverage when it hits the wall
pivot, preserve when a recurring answer exists, and phaze before cashing out.

Local docs checked:

- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_046_special_wall_pivot_ladder_smogtours-gen2ou-925777_2026-05-14.md`

Web sources checked in the parent work block:

- Smogon Forums, GSC OU Espeon:
  `https://www.smogon.com/forums/threads/gsc-ou-espeon-qc-1-1-gp-1-1.3667456/`
- Smogon Forums, GSC OU Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon Forums, GSC Teambuilding Compendium:
  `https://www.smogon.com/forums/threads/gsc-teambuilding-compendium.3547538/`
- Smogon Forums, GSC Mechanics:
  `https://www.smogon.com/forums/threads/gsc-mechanics.3542417/`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Classification hits: 4 / 4.

Route-job hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. This should be followed by a fresh replay
transfer because it is constructed directly from a known miss.

## Scenario 1 - Electric Attack Into Known Sleeping Electric Absorber

Public state:

```text
Vanilla GSC. Our poisoned Raikou is active against Skarmory. The opponent's
Raikou is already asleep and has Thunder revealed. Our Snorlax is healthy in
reserve. No Spikes are down.
```

Named serious branch: opponent switches sleeping Raikou into Raikou's Electric
attack.

Tempting move: Thunder into Skarmory.

Frozen answer: double to Snorlax. Confidence: medium.

Classification: double. The active attack is cleanly covered by a revealed
absorber, and Snorlax gains the seat against the sleeping Electric.

Score: pass.

## Scenario 2 - Snorlax Coverage Into Skarmory

Public state:

```text
Vanilla GSC. Our Snorlax is active against the opponent's sleeping Raikou.
Opponent Skarmory is healthy, has Toxic revealed, and is the obvious wall
pivot. Our Snorlax is known to carry Thunder.
```

Named serious branch: opponent switches Skarmory into Snorlax.

Tempting move: Curse because it is generic active progress.

Frozen answer: use Thunder. Confidence: medium.

Classification: coverage into pivot. Generic setup is worse than the revealed
coverage move when the wall pivot is the branch being punished.

Score: pass.

## Scenario 3 - Preserve Support When A Recurring Answer Exists

Public state:

```text
Vanilla GSC, side-known mode. Our Cloyster has just set Spikes and is at 56%
against +1 Snorlax. Our healthy Golem is unrevealed in reserve and can take a
Double-Edge. Snorlax has Curse and Double-Edge revealed.
```

Named serious branch: Snorlax attacks Cloyster with Double-Edge.

Tempting move: Explosion because Spikes are already delivered.

Frozen answer: switch Golem. Confidence: medium.

Classification: side-known recurring answer. Spikes being delivered does not
make Explosion automatic if a durable answer can enter and preserve the
support piece.

Score: pass.

## Scenario 4 - Phaze Before Explosion

Public state:

```text
Vanilla GSC. Our Golem is active at 80% against +1 Snorlax at full health.
Opponent has Spikes on its side. Golem has Roar and Explosion available.
Snorlax has Curse and Double-Edge revealed.
```

Named serious branch: Snorlax keeps attacking or boosting.

Tempting move: Explosion into the central route piece.

Frozen answer: Roar. Confidence: medium-high.

Classification: route denial. If phazing is reliable and Golem is not forced
to trade now, Roar preserves the one-time cash-out while Spikes tax the new
entry.

Score: pass.

## Resulting Checklist

After a wall pivot is named:

1. If the current attack is absorbed cleanly, double.
2. If known coverage hits the expected wall, use coverage.
3. If setup/status/hazards improve through the expected response, take the
   progress.
4. If a recurring answer denies the active route, use it before Explosion.

## Next Study Target

Fresh replay transfer with the same ladder, but stop after the first two
misses rather than extending the segment.
