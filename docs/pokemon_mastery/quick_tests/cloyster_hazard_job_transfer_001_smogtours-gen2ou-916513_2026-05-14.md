# Cloyster Hazard Job Transfer 001 - smogtours-gen2ou-916513 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-916513`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-916513.log`

Tournament source:
`https://www.smogon.com/forums/threads/smogon-premier-league-xvii-week-9.3778834/`

Web/current source checked:

- Smogon GSC forum index and recent tournament results.
- SPL XVII Week 9, selected because it was high-level current GSC OU material.

Contamination control:

- Local `rg` found no prior `916513` use before selection.
- No keyword screen for Cloyster, Spikes, Rapid Spin, or teams.
- Used only spectator-public prompts from the local replay helper before each
  reveal.

Selected action:
Fresh 30-side-decision replay transfer after the previous miss where active
Cloyster was wrongly priced as a spinner before setting missing Spikes.

## Score

- Decisions: 30
- Top match: 17/30
- Acceptable match: 29/30
- Severe blunders: 0
- State errors: 0
- Hidden-info errors: 0
- Mechanics errors: 0
- Positive-selection: 25/30
- Route-converting move chosen: 16/22 applicable
- Branch-punish chosen: 9/15 applicable
- Earliest meaningful error: turn 6 p2

Interpretation:
This is a better positive-selection packet than the prior hazard transfer, but
not proof of broad improvement. The Cloyster hazard-job correction transferred
on the two direct tests. The remaining problem is counter-switching after a
forced exit: I often named the likely switch but ranked the active punish above
the counter-handoff.

## Turn Notes

| Turn | Side | Frozen top | Actual | Grade |
| --- | --- | --- | --- | --- |
| 1 | p1 | Thunder | Thunder | top; active pressure into setter |
| 1 | p2 | Switch to Zapdos owner | Raikou | top by class |
| 2 | p1 | Switch to Electric owner | Snorlax | top by class |
| 2 | p2 | Thunder | Thunder | top |
| 3 | p1 | Double-Edge | Double-Edge | top |
| 3 | p2 | Switch Cloyster or support owner | Thunder | acceptable; active pressure alternative |
| 4 | p1 | Double-Edge | Double-Edge | top |
| 4 | p2 | Rest if available | Cloyster | acceptable; hazard-route handoff |
| 5 | p1 | Double-Edge | Double-Edge | top |
| 5 | p2 | Spikes | Spikes | top; corrected hazard ordering |
| 6 | p1 | Switch out of Explosion lane | Zapdos | acceptable |
| 6 | p2 | Explosion | Golem | miss; named switch but did not counter-switch |
| 7 | p1 | HP coverage if available | Exeggutor | acceptable; fallback switch priced |
| 7 | p2 | Rock Slide | Raikou | acceptable, but branch counter-switch under-ranked |
| 8 | p1 | Sleep Powder if available | Psychic | acceptable |
| 8 | p2 | Switch sleep absorber | Hidden Power | acceptable; active coverage alternative |
| 9 | p1 | Switch to Raikou owner | Tyranitar | top by class |
| 9 | p2 | Hidden Power | Hidden Power | top |
| 10 | p1 | Rock Slide or physical punish | Crunch | acceptable |
| 10 | p2 | Switch to Tyranitar owner | Heracross | top by class |
| 11 | p1 | Switch Zapdos | Zapdos | top |
| 11 | p2 | Megahorn | Raikou | acceptable, but counter-switch under-ranked |
| 12 | p1 | Switch to Electric owner | Snorlax | top by class |
| 12 | p2 | Counter-switch to Snorlax/Tyranitar owner | Thunder | acceptable |
| 13 | p1 | Rest if available | Rest | top |
| 13 | p2 | Thunder | Snorlax | acceptable, but Rest branch was under-punished |
| 14 | p1 | Switch to Snorlax owner | Cloyster | top by class |
| 14 | p2 | Curse | Curse | top |
| 15 | p1 | Toxic | Toxic | top; setup threat outranked hazard jobs |
| 15 | p2 | Attack Cloyster | Curse | acceptable; boosted route continued |

## Direct Hazard Tests

Turn 5:

Public state:
p1 Snorlax at 76%, p2 Cloyster at 72%, no hazards on either side. Cloyster was
active and p1's side lacked Spikes.

Frozen answer:
p2 Cloyster should set Spikes before Spin, Explosion, Surf, or pivoting.

Actual:
Cloyster used Spikes.

Lesson:
The previous correction transferred: if the setter is already active and the
opponent's side is unspiked, setting missing Spikes is the first hazard job
unless an immediate route threat overrides it.

Turn 15:

Public state:
p1 Cloyster at 94% faced p2 Snorlax at +1 Attack/+1 Defense. p1's side had
Spikes; p2's side had none.

Frozen answer:
p1 Cloyster should Toxic if available, with Explosion second and Spikes/Spin
below the boosted Snorlax problem.

Actual:
Cloyster used Toxic.

Lesson:
Hazard ownership is subordinate to a live setup route. When a boosted Snorlax
can convert immediately, status or cash-out can beat both setting missing
Spikes and clearing owned-side Spikes.

## Main Error

Turn 6 exposed the next bottleneck. I recommended Cloyster Explosion after
also saying p1 should switch Snorlax out of the Explosion lane. The actual
p2 line switched Golem, preserving low Cloyster and countering the Zapdos
handoff. This was not hidden-info abuse; it was branch-action failure after
correctly naming the likely exit.

Related misses appeared on turns 7, 11, and 13: after a side created a forced
exit, I often kept the active punish as top instead of ranking the
counter-switch that meets the likely owner.

## Next Rep

Fresh branch-counter-switch transfer:
when a move or matchup forces the opponent out, name the likely owner and rank
counter-switch, active punish, setup/status, and cash-out before choosing.
