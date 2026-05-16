# Replay Turn-Pause 075 Cash-Out Before Status Transfer - gen2ou-2595963523 - 2026-05-14

Source:
`https://replay.pokemonshowdown.com/gen2ou-2595963523-r1532r66y6pldd6vdbt1arhl7eicejlpw`.

Context source: Smogon GSC OU Global Championship 2026 Round 1 Stage 2. The
thread states this is a standard GSC OU tournament and links this replay in
PHB11677's April 27, 2026 "First blood" post.

Current web sources checked:

- `https://www.smogon.com/forums/threads/gsc-ou-global-championship-2026-round-1-stage-2.3781519/`
- `https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-13-losers-bracket-replays-required.3781520/`
- `https://www.smogon.com/forums/threads/spl-xvii-gsc-discussion.3775984/`

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/policy_cards/active_pressure_before_status.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/workspace/quick_tests/cashout_before_status_script_probe_001_2026-05-14.md`

Mode: spectator public, no keyword screen, fixed species-aware prompt helper.

Contamination control:

- Local docs were searched for `2595963523`; no prior local use was found.
- This is from the same public replay post as replay 074, so it is fresh local
  replay evidence with a same-post/set caveat.
- The raw log was downloaded and summarized for metadata only before the run.
- No move-keyword screen was used.
- Decisions were frozen turn by turn before revealing the matching turn.
- Turn 18 p2 was unscored because Snorlax fainted before its selected move, if
  any, was revealed.

## Score Summary

Scored decisions: 35 side decisions from turns 1-18.

Unscored decision: p2 turn 18.

Top-match: 18 / 35.

Acceptable-match: 23 / 35.

Severe blunders: 0.

State errors: 0.

Hidden-information errors: 0.

Mechanics errors: 0.

Earliest meaningful error: Turn 1. I expected a Zapdos mirror to resolve
through a special receiver instead of direct Thunder pressure.

Main pattern: the cash-out-before-status transfer improved in the obvious late
game: I correctly chose Snorlax Self-Destruct into Growth Vaporeon and
Exeggutor Explosion into last Snorlax. It remained unstable on one-time trade
taxonomy: I missed Steelix Explosion into Zapdos, missed Gengar Destiny Bond
into Exeggutor, and overcalled Cloyster Explosion where the actual line used
Gengar to preserve Cloyster while absorbing Hidden Power.

## Focused Transfer Result

| Class | Evidence | Grade |
| --- | --- | --- |
| Explosion/cash-out before setup converter | Turn 17: chose Snorlax Self-Destruct into Growth Vaporeon. | top |
| Endgame Explosion conversion | Turn 18: chose Exeggutor Explosion into last Snorlax. | top |
| One-time trade not named Explosion | Turn 12: missed Gengar Destiny Bond into Exeggutor. | miss |
| Earlier Explosion before phaze/reset | Turn 6: missed Steelix Explosion into Zapdos and expected Roar. | miss |
| Preserve instead of bad cash-out | Turn 10: overcalled Cloyster Explosion; actual switch to Gengar preserved the hazard piece and punished Hidden Power. | miss |
| Explosion absorber branch | Turn 15: switched Cloyster into opposing Cloyster Explosion, preserving Snorlax. | top |

## Turn Notes

### Turn 1

Public state: Zapdos mirror at 100% each.

Frozen answer:

- p1: switch a special receiver such as Snorlax.
- p2: Thunder or a matching receiver line.

Actual choices: both Zapdos used Thunder; p1 hit, p2 missed.

Grade: p1 miss, p2 top-match.

### Turn 2

Public state: p1 Zapdos 100% versus p2 Zapdos 61%.

Frozen answer:

- p1: Thunder, keeping direct pressure.
- p2: switch to a Thunder absorber.

Actual choices: p2 switched Steelix. p1 used Thunder into immunity.

Grade: p1 top-match, p2 acceptable-match by receiver class.

### Turn 3

Public state: p1 Zapdos 100% versus p2 Steelix 100%.

Frozen answer:

- p1: switch to a Water or Ground-checking support piece.
- p2: Roar or Toxic into the expected switch.

Actual choices: p1 used Hidden Power. p2 used Curse.

Grade: both miss. I left too early instead of pricing active coverage into the
Steelix branch.

### Turn 4

Public state: p1 Zapdos 100% versus p2 Steelix 82% at +1 Attack/+1 Defense.

Frozen answer:

- p1: Hidden Power.
- p2: Explosion, with Roar as a serious alternative if Steelix should preserve.

Actual choices: p1 used Hidden Power. p2 used Roar and dragged Alakazam.

Grade: p1 top-match, p2 acceptable-match.

### Turn 5

Public state: p1 Alakazam 100% versus p2 boosted Steelix 63%.

Frozen answer:

- p1: Psychic or Fire Punch pressure.
- p2: Earthquake.

Actual choices: p1 switched Zapdos. p2 used Earthquake into immunity.

Grade: p1 miss, p2 top-match. I missed the clean immunity pivot.

### Turn 6

Public state: p1 Zapdos 100% versus p2 Steelix 69% at +1 Attack/+1 Defense.

Frozen answer:

- p1: Hidden Power.
- p2: Roar to keep phazing; Explosion was the worst branch.

Actual choices: p1 used Hidden Power, critting Steelix to 18%. p2 used
Explosion and removed Zapdos.

Grade: p1 top-match, p2 miss. The Steelix cash-out was the correct one-time
trade before Zapdos kept converting.

Reusable lesson: if Steelix cannot threaten the active Flying target with its
normal attack and phazing no longer improves the route, Explosion must be
priced before another reset.

### Turn 7

Public state: p1 Cloyster 100% versus p2 Snorlax 100%, no hazards yet.

Frozen answer:

- p1: Spikes.
- p2: Double-Edge or Body Slam.

Actual choices: p2 switched Cloyster. p1 used Spikes.

Grade: p1 top-match, p2 miss. I missed the reciprocal hazard entry.

### Turn 8

Public state: Cloyster mirror, Spikes on p2 side.

Frozen answer:

- p1: Toxic.
- p2: Spikes.

Actual choices: p1 used Toxic. p2 used Spikes.

Grade: both top-match.

### Turn 9

Public state: Cloyster mirror, p2 Cloyster poisoned, Spikes on both sides.

Frozen answer:

- p1: Rapid Spin or another hazard-control move.
- p2: Toxic back.

Actual choices: p2 used Hidden Power for super-effective damage. p1 used Surf.

Grade: both miss. I underpriced direct Cloyster-mirror damage.

### Turn 10

Public state: p1 Cloyster 50% versus p2 poisoned Cloyster 66%.

Frozen answer:

- p1: Explosion, treating low Cloyster as spent.
- p2: Hidden Power.

Actual choices: p1 switched Gengar through Spikes. p2 used Hidden Power.

Grade: p1 miss, p2 top-match. This was an overcorrection: p1 Cloyster still
had enough route value, and Gengar was the better way to meet Hidden Power
while preserving the hazard piece.

### Turn 11

Public state: p1 Gengar 73% versus p2 poisoned Cloyster 54%.

Frozen answer:

- p1: Thunderbolt.
- p2: switch a Gengar receiver such as Snorlax.

Actual choices: p2 switched Exeggutor through Spikes. p1 used Thunderbolt,
critting Exeggutor.

Grade: p1 top-match, p2 acceptable-match by receiver class.

### Turn 12

Public state: p1 Gengar 80% versus p2 Exeggutor 62%.

Frozen answer:

- p1: Ice Punch or another direct coverage punish.
- p2: Psychic.

Actual choices: p1 used Destiny Bond. p2 used Psychic, causing both to faint.

Grade: p1 miss, p2 top-match. I saw the active punish but not the one-time
trade class because it was Destiny Bond rather than Explosion.

### Turn 13

Public state: p1 Exeggutor 93% versus p2 Zapdos 67%.

Frozen answer:

- p1: Sleep Powder, preserving a healthy Exeggutor while creating Sleep Clause
  value.
- p2: switch a sleep absorber or use Hidden Power.

Actual choices: p2 used Hidden Power. p1 used Psychic.

Grade: p1 miss, p2 acceptable-match. Psychic was the actual middle line between
sleep and boom.

### Turn 14

Public state: p1 Exeggutor 53% versus p2 Zapdos 37%.

Frozen answer:

- p1: Psychic to remove Zapdos if it stays.
- p2: switch to preserve Zapdos.

Actual choices: p2 switched poisoned Cloyster through Spikes. p1 switched
Snorlax through Spikes.

Grade: p1 miss, p2 acceptable-match. I saw Zapdos preservation but not p1's
Snorlax handoff.

### Turn 15

Public state: p1 Snorlax 93% versus p2 poisoned Cloyster 36%.

Frozen answer:

- p1: switch Cloyster as the Explosion absorber.
- p2: Explosion.

Actual choices: p1 switched Cloyster. p2 used Explosion; both Cloyster fainted.

Grade: both top-match. This was the cleanest branch-action hit in the packet.

### Turn 16

Public state: p1 Snorlax 87% versus p2 Zapdos 43%.

Frozen answer:

- p1: Double-Edge.
- p2: Thunder.

Actual choices: p2 used Thunder. p1 used Double-Edge and KOed Zapdos.

Grade: both top-match.

### Turn 17

Public state: p1 Snorlax 57% versus p2 Vaporeon 93%.

Frozen answer:

- p1: Self-Destruct if available, removing the Growth converter before it
  takes over.
- p2: Growth.

Actual choices: p2 used Growth. p1 used Self-Destruct; both fainted.

Grade: both top-match. This was a direct pass on the replay 074 cash-out miss.

### Turn 18

Public state: p1 Exeggutor 47% plus unrevealed Alakazam versus last p2 Snorlax
93%.

Frozen answer:

- p1: Explosion, converting the final Snorlax immediately.
- p2: unscored because p2's selected move was not revealed.

Actual choices: p1 used Explosion and KOed Snorlax.

Grade: p1 top-match, p2 unscored.

## Error Classes

- One-time trade taxonomy: I still overweight ordinary attacks when the correct
  cash-out is Destiny Bond or a less obvious Explosion timing.
- Cash-out overcorrection: low support does not mean automatic Explosion if a
  pivot preserves the piece and punishes the opponent's expected move.
- Active coverage versus switch: I missed early Hidden Power into Steelix and
  later Psychic into Zapdos because I polarized between switching, status, and
  boom.
- Reciprocal hazard entry: I still undercall the opponent's early Cloyster
  switch into Snorlax-Cloyster openings.

## Next Rep

Create `one_time_trade_taxonomy_probe_001` with four branches: Explosion before
phaze, Destiny Bond as cash-out, preserve low Cloyster through a pivot instead
of bad Explosion, and endgame Self-Destruct/Explosion conversion. Then transfer
that probe to a fresh no-keyword-screen replay.
