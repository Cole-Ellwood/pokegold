# Replay Turn-Pause 074 Mixed Punish Transfer - gen2ou-2595957046 - 2026-05-14

Source:
`https://replay.pokemonshowdown.com/gen2ou-2595957046-qonhqihjgq6rspmobahjo7g171lexhxpw`.

Context source: Smogon GSC OU Global Championship 2026 Round 1 Stage 2. The
thread states this is a standard GSC OU tournament and links this replay in
PHB11677's April 27, 2026 "First blood" post.

Current web sources checked:

- `https://www.smogon.com/forums/threads/gsc-ou-global-championship-2026-round-1-stage-2.3781519/`
- `https://www.smogon.com/forums/forums/gsc/`
- `https://www.smogon.com/forums/threads/your-one-stop-shop-for-gsc-ou-statistics.3780415/`

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/master_index.md`
- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/training_cycle.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/active_pressure_before_status.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/workspace/quick_tests/mixed_punish_class_probe_001_2026-05-14.md`

Mode: spectator public, no keyword screen, fixed species-aware prompt helper.

Contamination control:

- Local docs were searched for `2595957046`; no prior local use was found.
- The raw log was downloaded and summarized for metadata only before the run.
- No move-keyword screen was used.
- Decisions were frozen turn by turn before revealing the matching turn.
- Turn 6 p1 was unscored because paralysis prevented the selected move from
  being revealed.

## Score Summary

Scored decisions: 31 side decisions from turns 1-16.

Unscored decision: p1 turn 6, because full paralysis hid the selected move.

Top-match: 12 / 31.

Acceptable-match: 22 / 31.

Severe blunders: 0.

State errors: 0.

Hidden-information errors: 0.

Mechanics errors: 0.

Earliest meaningful error: Turn 1. I defaulted to direct Zapdos pressure and
missed the lead Cloyster entry route into Snorlax.

Main pattern: move-class punish transfer improved on immunity pivots,
absorber-avoidance, and coverage into a receiver, but turn 10 showed a live
cash-out miss: I wanted Sleep Powder from Exeggutor when Explosion immediately
removed Zapdos before Hidden Power pressure could erase the window.

## Focused Transfer Result

| Class | Evidence | Grade |
| --- | --- | --- |
| Immunity or resist pivot | Turn 12: picked a Normal immunity class into Double-Edge, actual was Golem as the resist. Turn 15: picked a Ground/boom immunity pivot, actual was Zapdos into Earthquake. | acceptable |
| Absorber avoidance | Turn 14: kept Earthquake instead of blind Explosion as p2 could route to Golem. | top |
| Coverage into receiver | Turn 16: used Zapdos Hidden Power into Golem/Snorlax branch; Snorlax entered and still took route-relevant damage. | top |
| Cash-out into active converter | Turn 10: missed Exeggutor Explosion into Zapdos and chose a sleep/status script. | miss |

## Turn Notes

### Turn 1

Public state: p1 Zapdos 100% versus p2 Snorlax 100%.

Frozen answer:

- p1: Thunder; direct Electric pressure before revealing the support map.
- p2: Body Slam or another active Normal attack.

Actual choices: p1 switched Cloyster. p2 used Double-Edge.

Grade: p1 miss, p2 acceptable. I missed the immediate spiker-entry route.

### Turn 2

Public state: p1 Cloyster 73% versus p2 Snorlax 100%.

Frozen answer:

- p1: Spikes.
- p2: Double-Edge.

Actual choices: p2 switched Cloyster. p1 used Spikes.

Grade: p1 top-match, p2 miss. I underpriced the reciprocal hazard branch.

### Turn 3

Public state: Cloyster mirror, p1 79%, p2 100%, Spikes on p2 side.

Frozen answer:

- p1: Toxic or otherwise punish opposing Cloyster before it spins or pivots.
- p2: Spikes.

Actual choices: p1 used Hidden Power for super-effective damage. p2 used
Spikes.

Grade: p1 acceptable, p2 top-match. Correct class, wrong exact punish.

### Turn 4

Public state: p1 Cloyster 85% versus p2 Cloyster 51%, Spikes on both sides.

Frozen answer:

- p1: Hidden Power to pressure or remove low Cloyster.
- p2: switch Snorlax or another Hidden Power absorber to preserve Cloyster.

Actual choices: p1 switched Gengar. p2 switched Zapdos.

Grade: p1 miss, p2 acceptable. I missed p1's anti-Spin or anti-boom pivot.

### Turn 5

Public state: p1 Gengar 93% versus p2 Zapdos 100%, Spikes on p1 side.

Frozen answer:

- p1: Hypnosis; serious alternative was switching a special wall if Thunder was
  the main branch.
- p2: Thunder.

Actual choices: p1 switched Snorlax. p2 used Thunder.

Grade: p1 acceptable, p2 top-match. The top answer overused status, but the
serious alternative matched the route.

### Turn 6

Public state: p1 paralyzed Snorlax 66% versus p2 Zapdos 100%.

Frozen answer:

- p1: Double-Edge.
- p2: switch Snorlax or another physical receiver.

Actual choices: p2 switched Golem. p1 was fully paralyzed.

Grade: p1 unscored, p2 miss. I did not name the Golem Normal-resist branch.

### Turn 7

Public state: p1 paralyzed Snorlax 72% versus p2 Golem 93%.

Frozen answer:

- p1: switch Gengar to blank Earthquake or Explosion; Cloyster was the safer
  general Golem answer if Rock Slide was priced higher.
- p2: Explosion, with Earthquake as the non-cash-out line.

Actual choices: p1 switched Cloyster. p2 used Earthquake.

Grade: both acceptable. I found the switch-out class, but overweighted boom.

### Turn 8

Public state: p1 Cloyster 49% versus p2 Golem 99%.

Frozen answer:

- p1: Surf.
- p2: switch Zapdos.

Actual choices: p2 switched Zapdos. p1 used Surf.

Grade: both top-match. Surf still punished the Zapdos receiver enough.

### Turn 9

Public state: p1 Cloyster 55% versus p2 Zapdos 77%.

Frozen answer:

- p1: switch Snorlax or another Thunder sponge.
- p2: Thunder.

Actual choices: p1 switched Exeggutor. p2 used Thunder.

Grade: p1 acceptable, p2 top-match. Correct switch-out class, better actual
receiver.

### Turn 10

Public state: p1 Exeggutor 66% versus p2 Zapdos 83%.

Frozen answer:

- p1: Sleep Powder.
- p2: switch low Cloyster as sleep absorber.

Actual choices: p2 used Hidden Power. p1 used Explosion; both fainted.

Grade: both miss. This was the clearest new miss: I over-scripted sleep and
missed that Explosion immediately removed Zapdos before Hidden Power pressure
could reduce Exeggutor to a low-value piece.

Reusable lesson: before clicking sleep with a one-time support piece, ask
whether the active target is already the converter that Explosion must remove.

### Turn 11

Public state: p1 Zapdos 100% versus p2 Snorlax 93%, after the double KO.

Frozen answer:

- p1: Thunder.
- p2: Double-Edge.

Actual choices: p1 used Thunder and missed. p2 used Double-Edge.

Grade: both top-match.

### Turn 12

Public state: p1 Zapdos 56% versus p2 Snorlax 91%.

Frozen answer:

- p1: switch Gengar as the cleanest Double-Edge immunity.
- p2: Double-Edge.

Actual choices: p1 switched Golem. p2 used Double-Edge.

Grade: p1 acceptable, p2 top-match. Correct Normal-punish class, wrong
species.

### Turn 13

Public state: p1 Golem 77% versus p2 Snorlax 94%.

Frozen answer:

- p1: Earthquake; avoid blind Explosion while p2 has Golem/Cloyster branches.
- p2: switch Cloyster or another Golem answer.

Actual choices: p1 used Earthquake. p2 used Earthquake.

Grade: p1 top-match, p2 miss. I missed Snorlax's coverage into Golem.

### Turn 14

Public state: p1 Golem 45% versus p2 Snorlax 70%.

Frozen answer:

- p1: Earthquake again; Explosion loses value if p2 routes to Golem.
- p2: Earthquake.

Actual choices: p2 switched Golem. p1 used Earthquake.

Grade: p1 top-match, p2 miss. The absorber branch was real, but I only applied
it to p1's side.

### Turn 15

Public state: Golem mirror, p1 51%, p2 36%.

Frozen answer:

- p1: switch Gengar into the Earthquake or Explosion branch.
- p2: Explosion, with Earthquake as the lower-cost line.

Actual choices: p1 switched Zapdos. p2 used Earthquake.

Grade: both acceptable. Correct immunity-pivot class, wrong exact receiver and
wrong top p2 move.

### Turn 16

Public state: p1 Zapdos 62% versus p2 Golem 42%.

Frozen answer:

- p1: Hidden Power if available; it punishes Golem and still chips the Snorlax
  receiver.
- p2: Rock Slide or Explosion if staying in.

Actual choices: p2 switched Snorlax. p1 used Hidden Power.

Grade: p1 top-match, p2 miss. Coverage into the receiver was the correct p1
class; I underpriced p2 preserving Golem.

## Error Classes

- Cash-out before status script: Exeggutor versus Zapdos on turn 10 required
  pricing immediate Explosion before Sleep Powder.
- Reciprocal hazard opener: p2's early Cloyster switch on turn 2 was missed.
- Absorber branch asymmetry: I used p2's possible Golem absorber to avoid p1
  Explosion on turn 14, but did not select the same absorber route for p2.
- Hidden bench limitation: several acceptable grades are by action class rather
  than exact species because the run was spectator-public with no team sheet.

## Next Rep

Create a small `cashout_before_status_script_probe_001` from this miss. Then
transfer it to a fresh no-keyword-screen replay and check whether active
Explosion/cash-out is priced before status when the target is already the route
converter.
