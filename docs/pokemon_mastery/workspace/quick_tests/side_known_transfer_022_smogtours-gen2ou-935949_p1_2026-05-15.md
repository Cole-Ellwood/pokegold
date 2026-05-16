# Side-Known Transfer 022 - smogtours-gen2ou-935949 p1 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-935949`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-935949.log`

Search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&page=1`

Mode: side-known reconstructed for p1 / melancholy0. Opponent information was
spectator-public only.

Contamination control:

- Local `rg` found no prior `smogtours-gen2ou-935949` use before selection.
- Only metadata and turn count were inspected before turn 1.
- Scored the first 30 turns as the post-GrowthPass repair sample.

## Score Summary

Decisions: 30.
Top-match: 17/30.
Acceptable-match: 25/30.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 1.
Mechanics errors: 0.
Positive-selection: 22/30.
Route-converting move chosen: 19/30.
Branch-punish chosen: 12/18.
Role-package update obeyed: 27/30.
Route-transaction obeyed: 30/30.
Candidate comparison obeyed: 30/30 in form, 22/30 in promotion.
Earliest meaningful error: turn 4.

Verdict: limited transfer, not proof. The score cleared top/acceptable and
severe gates, but failed the hidden-info/strong-prior branch gate on turn 4:
Raikou invited a Ground/Steel counter-owner, and Hidden Power needed to outrank
Thunderbolt before Steelix was revealed.

## Frozen Answer Log

| Turn | Frozen top | Actual | Grade | Lesson |
| --- | --- | --- | --- | --- |
| 1 | Spikes | Toxic | acceptable miss | Toxic owned the mirror setter; Spikes was playable. |
| 2 | Spikes | Spikes | top | Correct hazard job. |
| 3 | Rapid Spin | Switch Raikou | acceptable miss | Spin was playable, but replay chose active Electric pressure. |
| 4 | Thunderbolt | Hidden Power into Steelix | miss | Hidden-info/branch error: Ground/Steel counter-owner was strong-prior. |
| 5 | Hidden Power | Hidden Power into Snorlax switch | top | Correct coverage pressure after the branch was public. |
| 6 | Switch Skarmory | Switch Skarmory | top | Correct Snorlax owner. |
| 7 | Whirlwind | Toxic | acceptable miss | Phaze was playable; timer first was better. |
| 8 | Whirlwind | Whirlwind | top | Correct boost denial. |
| 9 | Switch Raikou | Switch Raikou | top | Correct Electric owner, even through Snorlax double. |
| 10 | Switch Skarmory | Switch Miltank | acceptable miss | Right owner class, wrong route piece; cleric value mattered. |
| 11 | Heal Bell | Heal Bell | top | Correct status-map reset. |
| 12 | Switch Skarmory | Switch Skarmory | top | Correct status absorber into Exeggutor. |
| 13 | Toxic | Toxic into Steelix immunity | top | Exact move matched, but branch result was poor. |
| 14 | Whirlwind | Switch Cloyster | miss | Missed Rapid Spin route setup. |
| 15 | Rapid Spin | Rapid Spin | top | Correct hazard reset. |
| 16 | Switch Raikou | Switch Snorlax | acceptable miss | Electric owner was playable; sleeping Snorlax owner was better. |
| 17 | Curse | Curse | top | Correct sleep-window setup. |
| 18 | Double-Edge | Double-Edge into Steelix | top | Correct active pressure into counter-owner. |
| 19 | Switch Skarmory | Earthquake KO Steelix | miss | Overguarded possible cash-out instead of exact removal. |
| 20 | Switch Skarmory | Double-Edge into Exeggutor | miss | Overpreserved into a non-low Explosion branch. |
| 21 | Switch Skarmory | Snorlax stayed and died to crit Explosion | acceptable miss | Guarding Explosion was coherent; crit makes oracle weak. |
| 22 | Thunderbolt | Thunderbolt into Snorlax switch | top | Correct active pressure. |
| 23 | Thunderbolt | Thunderbolt | top | Correct pressure before RestTalk reset. |
| 24 | Switch Skarmory | Switch Skarmory | top | Correct RestTalk reset denial. |
| 25 | Whirlwind | Curse | acceptable miss | Phaze was playable; replay used Curse to stabilize. |
| 26 | Rest | Rest | top | Correct preservation. |
| 27 | Switch Miltank | Stay asleep as Cloyster entered | acceptable miss | Cleric handoff was playable, but staying preserved Skarm. |
| 28 | Stay with sleeping Skarmory | Switch Nidoking | miss | Overguarded boom/status instead of bringing active pressure. |
| 29 | Thunder | Thunder into Snorlax switch | top | Correct Nidoking pressure. |
| 30 | Lovely Kiss | Lovely Kiss | top | Correct Rest denial. |

## Reusable Lesson

When our Electric enters against a Water/Flying or support target, name the
counter-owner class before choosing STAB. Ground/Steel and Snorlax are
strong-prior counter-owners; if Hidden Power hits the Ground/Steel class and
still leaves the active line acceptable, it can be top before the exact counter
is revealed.

The cash-out repair now needs a boundary against overlearning: guard low
Self-Destruct/Explosion only when the active move does not remove the blocker
before it can reset, phaze, or trade.

