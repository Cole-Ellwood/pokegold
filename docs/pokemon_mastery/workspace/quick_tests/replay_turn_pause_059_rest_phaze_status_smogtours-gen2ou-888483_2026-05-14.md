# Replay Turn-Pause 059 Rest Phaze Status - smogtours-gen2ou-888483 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-888483`.

Context source: Smogon GSC Last Chance tournament replay.

Mode: spectator public, no keyword screen. Scoring starts at Turn 5.

Contamination control:

- Local docs were searched for `888483`; no prior local use was found.
- The raw log was downloaded and summarized only for metadata at first.
- At the time of this run, the local helper printed nicknames instead of
  species for nicknamed Pokemon, so the opening raw log lines were inspected to
  map public species. That exposed turns 1-4, so turns 1-4 are quarantined and
  not scored. The helper was fixed after this run to print public species names
  beside nicknames.
- No move-keyword screen was used for this replay.
- Future turns after Turn 5 were revealed only after freezing the answer for
  the current prompt.

Nickname map from public pre-Turn-5 state:

- p2 `Bastard` = Snorlax.
- p2 `Bird God` = Zapdos.
- p2 `sDEMON` = Cloyster.
- p2 `Darck Dan` = Steelix.
- p2 `Mr. Internet` = Porygon2.

## Score Summary

Decisions: 18 countable side decisions from turns 5-14. No-action sleep turns
where the selected move was not logged were not scored.

Top-match: 5 / 18.

Acceptable-match: 7 / 18.

Severe blunders: 0.

State errors: 1. I failed to track that Rest Snorlax could wake and act on Turn
10 after two active sleep turns.

Hidden-information errors: 0.

Mechanics errors: 0.

Earliest meaningful error: Turn 6. After matching the first Whirlwind, I moved
off the Skarmory + Spikes phaze route too early.

## Turn Notes

### Turn 5

Public state: p1 Skarmory 100% versus p2 sleeping Snorlax 100%, Spikes on p2
side. Snorlax had just used Rest.

Frozen answer:

- p1: Whirlwind, because Skarmory can convert Spikes while Snorlax is asleep.
- p2: likely stay asleep or switch to an Electric/pressure piece.

Actual choices: p2 stayed asleep. p1 used Whirlwind, dragging Steelix into
Spikes.

Grade: p1 top-match. p2 unscored because sleep prevented a logged move.

### Turn 6

Public state: p1 Skarmory 100% versus p2 Steelix 94%, Spikes on p2 side.

Frozen answer:

- p1: switch Cloyster to meet Steelix and avoid giving Steelix a free route.
- p2: Roar or phazing pressure.

Actual choices: p2 switched Zapdos. p1 used Whirlwind, dragging Porygon2 into
Spikes.

Grade: both miss. The first replay-transfer error was leaving the phaze engine
too early. Whirlwind covered the switch and kept converting Spikes.

### Turn 7

Public state: p1 Skarmory 100% versus p2 Porygon2 94%, Spikes on p2 side.

Frozen answer:

- p1: Whirlwind, continuing the hazard route.
- p2: Thunder or direct pressure if Porygon2 has it.

Actual choices: p2 switched sleeping Snorlax into Spikes. p1 used Toxic, which
failed because Snorlax was already asleep.

Grade: both miss. p2 used the sleeping Snorlax as a status absorber, not only
as a preserved route piece.

### Turn 8

Public state: p1 Skarmory 100% versus p2 sleeping Snorlax 94%, Spikes on p2
side. Skarmory had revealed Toxic and Whirlwind.

Frozen answer:

- p1: Whirlwind.
- p2: switch to Zapdos or another pressure piece.

Actual choices: p2 stayed asleep. p1 used Whirlwind, dragging Cloyster into
Spikes.

Grade: p1 top-match. p2 unscored because sleep prevented a logged move.

### Turn 9

Public state: p1 Skarmory 100% versus p2 Cloyster 88%, Spikes on p2 side.

Frozen answer:

- p1: switch Raikou to threaten Cloyster and price the Rapid Spin window.
- p2: Rapid Spin or Spikes.

Actual choices: p2 switched sleeping Snorlax into Spikes. p1 used Toxic, which
failed again because Snorlax was already asleep.

Grade: both miss. I overreacted to the spinner entry path and under-priced the
status-absorber switch.

### Turn 10

Public state: p1 Skarmory 100% versus p2 sleeping Snorlax 88%, Spikes on p2
side.

Frozen answer:

- p1: Whirlwind.
- p2: sleep/no-action or another passive sleep turn.

Actual choices: Snorlax woke and used Double-Edge, critting Skarmory to 66%.
p1 used Whirlwind and dragged Porygon2 into Spikes.

Grade: p1 top-match, p2 miss. State error: Rest wake timing was material.

### Turn 11

Public state: p1 Skarmory 72% versus p2 Porygon2 88%, Spikes on p2 side.

Frozen answer:

- p1: Toxic, trying to convert the Porygon2 position.
- p2: Thunder Wave, Thunder, or direct pressure.

Actual choices: p2 switched Steelix into Spikes. p1 used Whirlwind, dragging
Snorlax into Spikes.

Grade: both miss. The phaze route was still live; I kept trying to add status
before identifying the opponent's switch cycle.

### Turn 12

Public state: p1 Skarmory 78% versus p2 Snorlax 76%, awake, Spikes on p2 side.

Frozen answer:

- p1: Whirlwind, expecting the Spikes route to remain active.
- p2: Double-Edge.

Actual choices: p1 used Toxic, poisoning Snorlax. p2 used Double-Edge.

Grade: p1 acceptable-match, p2 top-match. This was the correct Toxic boundary:
once Snorlax was awake and poisonable, Toxic forced the next Rest cycle.

### Turn 13

Public state: p1 Skarmory 65% versus p2 poisoned Snorlax 73%, Spikes on p2
side.

Frozen answer:

- p1: Whirlwind, expecting to punish the Rest cycle.
- p2: Rest.

Actual choices: p1 switched to Miltank. p2 used Rest.

Grade: p1 miss, p2 top-match. Miltank was a handoff I did not price from
spectator-public bench knowledge.

### Turn 14

Public state: p1 Miltank 100% versus p2 sleeping Snorlax 100%, Spikes on p2
side.

Frozen answer:

- p1: Growl or Miltank's direct Snorlax-control move.
- p2: switch out to a counter-pivot.

Actual choices: p1 switched to Snorlax. p2 switched to Gengar, taking Spikes.

Grade: p1 miss, p2 acceptable-match by switch-out handoff class. Exact pivot
was wrong, but the sleeping Snorlax did switch out rather than automatically
burn turns.

## Error Classes Found

- Phaze-loop undercommitment: after a healthy Skarmory started converting
  Spikes with Whirlwind, I moved away from the route before the opponent showed
  a branch that beat it.
- Sleep absorber reuse: the sleeping Snorlax repeatedly re-entered to absorb
  Toxic attempts. Preserved sleepers can be route pieces and status sponges.
- Rest wake tracking: Rest timing must be tracked exactly when the next
  Double-Edge, Rest, or Whirlwind turn matters.
- Status timing: Toxic was wrong while Snorlax was already asleep, but correct
  once Snorlax woke and could be forced back into Rest.
- Spectator-public bench limitation: Miltank and Gengar handoffs were not
  visible before reveal, so exact switch matching is weak evidence.

## Reusable Lesson

When Spikes plus a healthy phazer is already converting, keep asking what
actually breaks the loop. A possible spinner, Steelix, or Porygon2 is not
enough by itself; the opponent needs an entry path that removes hazards,
forces damage, lands status, or creates a counter-pivot worth abandoning the
Whirlwind route.

## Next Study Target

Run a four-scenario phaze-loop regression probe:

1. Keep Whirlwind when the switch cycle is still losing to Spikes.
2. Switch out when the spinner entry path is immediate and unpunished.
3. Use a sleeping Pokemon as a status absorber without trying to wake it.
4. Track the exact Rest wake turn before choosing Toxic, Whirlwind, or a
   handoff.
