# Replay Turn-Pause 061 Active Pressure Transfer - smogtours-gen2ou-911263 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-911263`.

Context source: Smogon GSC OU Winter Seasonal #8 Round 3 replay post.

Mode: spectator public, no keyword screen, fixed species-aware prompt helper.

Contamination control:

- Local docs were searched for `911263`; no prior local use was found.
- The raw log was downloaded and summarized for metadata only.
- No move-keyword screen was used.
- Each turn was revealed only after freezing the current answer.
- The run stopped after Turn 9 because active-damage underpricing appeared
  twice, satisfying the planned stop condition.

## Score Summary

Decisions: 18 side decisions from turns 1-9.

Top-match: 6 / 18.

Acceptable-match: 9 / 18.

Severe blunders: 0.

State errors: 0.

Hidden-information errors: 0.

Mechanics errors: 0.

Earliest meaningful error: Turn 2. Snorlax Double-Edge was still converting
into Cloyster, but I pivoted away from active damage too early.

## Turn Notes

### Turn 1

Public state: p1 Zapdos 100% versus p2 Umbreon 100%.

Frozen answer:

- p1: switch to a physical pressure piece rather than let Umbreon start a
  passive status/control plan.
- p2: Toxic or control pressure from Umbreon.

Actual choices: p1 switched to Golem. p2 switched to Snorlax.

Grade: p1 acceptable route, p2 miss. The p1 class was right: leave Zapdos and
put a physical piece into the Umbreon structure. I did not identify p2's
immediate Snorlax handoff.

### Turn 2

Public state: p1 Golem 100% versus p2 Snorlax 100%.

Frozen answer:

- p1: Earthquake or immediate Golem pressure.
- p2: Double-Edge, using Snorlax's active damage before the matchup is forced.

Actual choices: p1 switched to Cloyster. p2 used Double-Edge, leaving Cloyster
at 72% after Leftovers.

Grade: p1 miss, p2 top-match. This starts the active-pressure miss: the
replay's route was to meet Snorlax damage with Cloyster, while I kept Golem
active too long.

### Turn 3

Public state: p1 Cloyster 72% versus p2 Snorlax 100%.

Frozen answer:

- p1: Spikes.
- p2: Double-Edge, continuing active damage before Cloyster cashes out or
  pivots.

Actual choices: p1 used Spikes. p2 used Double-Edge, leaving Cloyster at 44%
after Leftovers.

Grade: both top-match.

### Turn 4

Public state: p1 Cloyster 44% versus p2 Snorlax 100%, Spikes on p2 side.

Frozen answer:

- p1: Explosion, trying to cash out the low Cloyster into Snorlax.
- p2: Double-Edge, with a Ghost switch named as the worst branch if Explosion
  is obvious.

Actual choices: p1 switched to Golem. p2 switched to Gengar, taking Spikes.

Grade: p1 miss, p2 acceptable-match. I over-cashed Cloyster; the replay
preserved it and p2 covered the obvious Explosion/Normal branch with Gengar.

### Turn 5

Public state: p1 Golem 100% versus p2 Gengar 94%, Spikes on p2 side.

Frozen answer:

- p1: Earthquake, with Roar or a switch as secondary if expecting the Gengar
  to leave.
- p2: switch to Zapdos to dodge the Golem punish.

Actual choices: p1 switched to Snorlax. p2 switched to Zapdos.

Grade: p1 miss, p2 top-match. I identified p2's switch but did not match p1's
counter-switch to preserve Golem and meet Zapdos.

### Turn 6

Public state: p1 Snorlax 100% versus p2 Zapdos 100%, Spikes on p2 side.

Frozen answer:

- p1: Double-Edge.
- p2: Thunder.

Actual choices: p2 switched to Forretress, taking Spikes. p1 used
Double-Edge, leaving Forretress at 77% after Leftovers.

Grade: p1 top-match, p2 miss. Snorlax damage stayed live even into the
resisted switch.

### Turn 7

Public state: p1 Snorlax 100% versus p2 Forretress 77%, Spikes on p2 side.

Frozen answer:

- p1: active punish into Forretress, ideally Fire Blast if available; otherwise
  the damaging coverage that denies free support.
- p2: Rapid Spin or hazard control.

Actual choices: p2 switched to Zapdos. p1 used Earthquake into the immune
Zapdos.

Grade: p1 acceptable-match by active-punish class, p2 miss. The route was still
to deny Forretress free progress, but the replay used Earthquake while p2
pivoted to Zapdos.

### Turn 8

Public state: p1 Snorlax 100% versus p2 Zapdos 100%, Spikes on p2 side.

Frozen answer:

- p1: Double-Edge.
- p2: Thunder.

Actual choices: p2 used Reflect. p1 used Double-Edge, dropping Zapdos to 81%
after Leftovers.

Grade: p1 top-match, p2 miss. Reflect was a support answer to active pressure,
not a reason for p1 to stop attacking yet.

### Turn 9

Public state: p1 Snorlax 100% versus p2 Zapdos 81% behind Reflect, Spikes on
p2 side.

Frozen answer:

- p1: switch Golem to block Thunder and reset the line after Reflect.
- p2: Thunder.

Actual choices: p2 switched Forretress into Spikes. p1 used Double-Edge,
leaving Forretress at 63% after Leftovers.

Grade: both miss. This is the repeated failure: I again left Snorlax's active
damage too early. Even through Reflect and into a resist, Snorlax damage plus
Spikes was still reducing Forretress and controlling the support loop.

## Error Classes Found

- Active damage underpricing: Snorlax Double-Edge into Cloyster and Forretress
  kept converting even when a support or resist branch was visible.
- Over-cash: low Cloyster after setting Spikes did not have to explode
  immediately, especially with a plausible Ghost/Normal absorber branch.
- Counter-switch miss: after predicting the opponent's Gengar-to-Zapdos switch,
  I still left Golem active instead of finding the Snorlax handoff.
- Support answer misread: Reflect and Forretress entry were responses to
  Snorlax pressure, not automatic signals to stop attacking.

## Reusable Lesson

When a bulky attacker is repeatedly forcing the opponent into resist or support
answers, keep pricing the damage plus hazard clock. Do not pivot just because
the target is a support Pokemon, has Reflect, or could use a support move. The
question is whether the next hit changes the support piece's future job.

## Next Study Target

Run a compact active-damage persistence probe:

1. Continue Snorlax damage into Cloyster before pivoting.
2. Continue Snorlax damage into Forretress through Reflect when the damage
   changes the support map.
3. Preserve low Cloyster when Explosion is covered by a Ghost or Normal
   absorber.
4. Counter-switch after identifying the opponent's switch, rather than taking
   the obvious active move into the absorber.
