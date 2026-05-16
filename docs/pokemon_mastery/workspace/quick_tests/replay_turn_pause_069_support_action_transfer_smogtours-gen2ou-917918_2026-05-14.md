# Replay Turn-Pause 069 Support Action Transfer - smogtours-gen2ou-917918 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-917918`.

Context source: Smogon GSC OU Winter Seasonal #8 Round 6 replay post.

Mode: spectator public, no keyword screen, fixed species-aware prompt helper.

Contamination control:

- Local docs were searched for `917918`; no prior local use was found.
- Web search confirmed the replay link in the Smogon Winter Seasonal Round 6
  thread.
- The raw log was downloaded and summarized for metadata only before the run.
- No move-keyword screen was used.
- Each turn was revealed only after freezing the current answer and explicitly
  treating support, setup, sleep preservation, and hazard handoff actions as
  live candidates.

## Score Summary

Decisions: 30 side decisions from turns 1-15.

Top-match: 11 / 30.

Acceptable-match: 14 / 30.

Severe blunders: 0.

State errors: 0.

Hidden-information errors: 0.

Mechanics errors: 0.

Earliest meaningful error: Turn 2. I named Zapdos's Thunder branch but did not
choose the Nidoking counter-switch that beat it.

Main pattern: the branch-action miss is narrower now. I often named the
receiver or support branch correctly, but still failed to choose the exact
counter-action in the same turn, especially around Starmie, Quagsire, and the
saved sleeping Zapdos.

## Turn Notes

### Turn 1

Public state: p1 Nidoking 100% versus p2 Zapdos 100%.

Frozen answer:

- p1: Lovely Kiss, status, or direct Nidoking pressure.
- p2: switch to a Nidoking answer or use active Zapdos pressure.

Actual choices: p1 switched Snorlax. p2 used Hidden Power into Snorlax.

Grade: p1 miss, p2 acceptable-match. I treated Nidoking as the center of the
turn and missed the immediate Snorlax handoff.

### Turn 2

Public state: p1 Snorlax 95% versus p2 Zapdos 100%; Zapdos revealed Hidden
Power.

Frozen answer:

- p1: direct Snorlax pressure.
- p2: Thunder.

Actual choices: p1 switched Nidoking. p2 used Thunder into immunity.

Grade: p1 miss, p2 top-match. This was the cleanest early branch-action miss:
I named Thunder but did not choose the action that beat it.

### Turn 3

Public state: p1 Nidoking 100% versus p2 Zapdos 100%; Zapdos revealed Hidden
Power and Thunder.

Frozen answer:

- p1: Lovely Kiss.
- p2: switch to a sleep receiver or absorber.

Actual choices: p2 used Hidden Power, dropping Nidoking to 56%. p1 used Lovely
Kiss and put Zapdos to sleep.

Grade: p1 top-match, p2 miss. Zapdos cashed damage before becoming the Sleep
Clause piece.

### Turn 4

Public state: p1 Nidoking 62% versus sleeping p2 Zapdos 100%.

Frozen answer:

- p1: hit the expected receiver or counter-switch if the receiver is clear.
- p2: switch sleeping Zapdos out to preserve Sleep Clause value.

Actual choices: p2 switched Snorlax. p1 switched Snorlax.

Grade: p1 acceptable-match, p2 top-match. The sleep-preservation read was
correct; the frozen p1 action was not clean enough to claim exact top-match.

### Turn 5

Public state: p1 Snorlax 100% versus p2 Snorlax 100%; p2 Zapdos asleep.

Frozen answer:

- p1: Curse or direct Snorlax mirror pressure.
- p2: Lovely Kiss or Double-Edge.

Actual choices: p1 switched Nidoking. p2 used Double-Edge, dropping Nidoking to
12% before Leftovers.

Grade: p1 miss, p2 top-match. I did not price the low-Nidoking handoff as the
branch action into Snorlax pressure.

### Turn 6

Public state: p1 Nidoking 18% versus p2 Snorlax 98%; Snorlax revealed
Double-Edge.

Frozen answer:

- p1: switch a hard Normal answer, ideally a Ghost if available.
- p2: Double-Edge.

Actual choices: p1 switched Misdreavus. p2 used Lick into Misdreavus.

Grade: p1 top-match, p2 miss. I found the Ghost handoff but missed the revealed
Snorlax coverage action that punished that branch.

### Turn 7

Public state: p1 Misdreavus 93% versus p2 Snorlax 100%; Snorlax revealed
Double-Edge and Lick.

Frozen answer:

- p1: Toxic, Perish Song, or other Misdreavus utility into Snorlax.
- p2: Lick again or switch.

Actual choices: p1 switched Snorlax. p2 switched Skarmory.

Grade: both miss. Both sides reset the board instead of playing the visible
Ghost/Snorlax exchange.

### Turn 8

Public state: p1 Snorlax 100% versus p2 Skarmory 100%.

Frozen answer:

- p1: Fire Blast or other coverage into Skarmory if available.
- p2: Toxic or Whirlwind.

Actual choices: p1 switched Nidoking. p2 used Curse.

Grade: both miss. Curse was the setup support action that changed the receiver
map before Skarmory attacked.

### Turn 9

Public state: p1 Nidoking 24% versus p2 +1 Atk / +1 Def / -1 Spe Skarmory
100%.

Frozen answer:

- p1: punish Skarmory with coverage.
- p2: Drill Peck or Whirlwind.

Actual choices: p1 switched Cloyster. p2 used Drill Peck.

Grade: p1 miss, p2 top-match. I did not choose the actual physical wall handoff
after Skarmory committed to setup.

### Turn 10

Public state: p1 Cloyster 81% versus p2 +1 Skarmory 100%; no Spikes up.

Frozen answer:

- p1: Spikes.
- p2: Whirlwind, Drill Peck, or another Skarmory support action.

Actual choices: p2 switched Starmie. p1 used Spikes.

Grade: p1 top-match, p2 miss. The Spikes call was correct, but I underpriced
the immediate Starmie entry as the hazard answer.

### Turn 11

Public state: p1 Cloyster 87% versus p2 Starmie 100%; Spikes on p2 side.

Frozen answer:

- p1: switch Misdreavus to block Rapid Spin.
- p2: Rapid Spin.

Actual choices: p1 switched Zapdos. p2 used Thunder Wave into Zapdos.

Grade: both miss. Starmie did not spin immediately; it used status to change
the Zapdos route before the hazard loop was resolved.

### Turn 12

Public state: p1 paralyzed Zapdos 100% versus p2 Starmie 100%; Spikes on p2
side.

Frozen answer:

- p1: Thunder.
- p2: switch Snorlax or another Zapdos receiver.

Actual choices: p2 switched Quagsire through Spikes. p1 switched Nidoking.

Grade: both miss. I missed both sides of the electric-immunity branch: Quagsire
as the receiver and Nidoking as the counter-switch.

### Turn 13

Public state: p1 Nidoking 30% versus p2 Quagsire 94%; Spikes on p2 side.

Frozen answer:

- p1: switch Cloyster as the known Quagsire answer.
- p2: Earthquake.

Actual choices: p1 switched Cloyster. p2 used Earthquake.

Grade: both top-match. This was a clean receiver-to-counter-receiver handoff.

### Turn 14

Public state: p1 Cloyster 71% versus p2 Quagsire 100%; Quagsire revealed
Earthquake.

Frozen answer:

- p1: Toxic to punish Quagsire or the expected receiver.
- p2: switch Starmie or another Cloyster answer.

Actual choices: p2 switched sleeping Zapdos. p1 used Toxic and missed.

Grade: p1 top-match, p2 miss. The important lesson is that the sleeping Zapdos
was preserved and then reused as a status absorber, exactly the sleep-clause
pattern the policy card warns about.

### Turn 15

Public state: p1 Cloyster 77% versus sleeping p2 Zapdos 100%; Spikes on p2
side.

Frozen answer:

- p1: Toxic again to catch the sleeping Zapdos switch-out or the incoming
  Starmie.
- p2: switch sleeping Zapdos out, most likely to Starmie.

Actual choices: p2 switched Starmie through Spikes. p1 switched Snorlax.

Grade: p1 acceptable-match, p2 top-match. The receiver read was right, but the
branch action was still soft: Snorlax met Starmie directly instead of merely
trying to poison the incoming spinner.

## Error Classes

- Branch action after naming: turns 2, 6, 12, and 15. The receiver or punish was
  often visible, but the selected action did not always beat it.
- Hazard-loop handoff: turns 10-11 and 15. Starmie was not just a spinner; it
  could status first, then threaten the hazard route.
- Sleep preservation and absorber reuse: turns 4, 14, and 15. A slept Zapdos
  was switched out, preserved for Sleep Clause value, then returned to absorb a
  support move before leaving again.

## Policy Extraction

Trigger:
  A sleeping Pokemon has already created Sleep Clause value and a support move
  is likely into its team.

Default:
  Price the sleeper as a reusable absorber and switch resource, not as a piece
  that automatically stays in to burn wake turns.

Exceptions:
  Stay in only if burning sleep turns performs a concrete job, such as denying
  setup, forcing damage, using Sleep Talk, or buying the exact handoff.

Worst branch:
  You aim status or passive progress at a receiver, the opponent routes it into
  the sleeping absorber, then switches the sleeper back out with the route still
  intact.

Local status:
  Vanilla GSC replay evidence. Local romhack sleep and clause behavior still
  require local verification when decision-relevant.

Drill:
  Build a four-position probe where the right answer is, respectively, switch
  the sleeper out, stay with Sleep Talk, use the sleeper as a status absorber,
  and punish the opponent's attempt to save the sleeper.
