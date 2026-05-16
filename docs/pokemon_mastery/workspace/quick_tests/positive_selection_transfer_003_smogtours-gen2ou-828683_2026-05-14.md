# Positive Selection Transfer 003 - smogtours-gen2ou-828683 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-828683`

Context source:
Smogon, `GSC OU Winter Seasonal #7: Round 8`:
`https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-7-round-8.3762076/`

Mode: focused fresh replay transfer, spectator-public vanilla GSC. No team
sheet was supplied, no Team Preview was assumed, and replay actual moves are a
weak pro-comparison oracle rather than absolute truth.

Selected action:
Fresh transfer with mandatory `next board owner: X/none` before each
nontrivial recommendation. This tested whether the counter-handoff lesson from
`positive_selection_transfer_002` improved unseen move choice or created an
overprediction error.

## Sources Checked

Local docs:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/reviews/counter_handoff_review_001_smogtours-gen2ou-907837_2026-05-14.md`

Web/current sources:

- Smogon Winter Seasonal #7 Round 8 thread above.
- Pokemon Showdown replay source above.
- Raw log: `https://replay.pokemonshowdown.com/smogtours-gen2ou-828683.log`

## Contamination Control

Local search found no prior `828683` artifact before selection. The raw log was
downloaded to `tmp/pokemon_mastery_replays/`. Future turns were not inspected;
each prompt was generated with `tools/pokemon_mastery/replay_turn_pause.py` and
revealed only after the answer was frozen.

Stopped after turn 15 because the packet reached 30 side decisions and already
showed both sides of the new boundary: correct counter-handoffs on turns 4,
10, and 13; over-handoffs on turns 5 and 14.

## Score Summary

Turns scored: 1-15.

Scorable side decisions: 30.

Top-match: 19 / 30.

Acceptable-match: 25 / 30.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 26 / 30.

Route-converting move chosen: 17 / 23 target converter decisions.

Branch-punish chosen: 14 / 21 named-branch decisions.

Earliest meaningful error: turn 5 p2. I correctly named p1's likely Skarmory
handoff, but overcorrected by choosing Zapdos when Snorlax's Double-Edge still
made useful progress without paying Spikes switch cost.

Main bottleneck:
The forced `next board owner` step improved counter-handoff recognition, but
it needs an active-pressure boundary. Before switching to the owner, ask
whether the current move already affects the next board through damage,
coverage, status, phaze, or hazard progress.

## Turn Score Table

| Turn | Side | Next board owner | Frozen top | Actual | Top | Accept | Positive | Route convert | Branch punish | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | none | Thunderbolt | Thunderbolt | 1 | 1 | 1 | 1 | n/a | Active pressure hit the Snorlax branch. |
| 1 | p2 | Snorlax | Switch Snorlax | Switch Snorlax | 1 | 1 | 1 | 1 | 1 | Correct Electric-answer handoff. |
| 2 | p1 | Skarmory/class | Switch Snorlax answer | Skarmory | 1 | 1 | 1 | 1 | 1 | Correct answer class. |
| 2 | p2 | none | Double-Edge | Double-Edge | 1 | 1 | 1 | 1 | n/a | Active pressure was enough into likely Skarmory. |
| 3 | p1 | Raikou for Zapdos | Toxic midground | Toxic | 1 | 1 | 1 | 1 | 1 | Toxic affected Snorlax stay and Zapdos switch. |
| 3 | p2 | Zapdos | Switch Zapdos | Switch Zapdos | 1 | 1 | 1 | 1 | 1 | Correct Skarmory counter-handoff. |
| 4 | p1 | Raikou | Switch Raikou | Switch Raikou | 1 | 1 | 1 | 1 | 1 | Correct forced handoff. |
| 4 | p2 | Snorlax | Switch Snorlax | Switch Snorlax | 1 | 1 | 1 | 1 | 1 | Correct counter-handoff into Raikou. |
| 5 | p1 | Skarmory | Switch Skarmory | Switch Skarmory | 1 | 1 | 1 | 1 | 1 | Correct repeat answer. |
| 5 | p2 | Zapdos | Switch Zapdos | Double-Edge | 0 | 1 | 1 | 0 | 1 | Over-handoff: Double-Edge still improved the Skarmory board. |
| 6 | p1 | Raikou for Zapdos | Toxic | Toxic | 1 | 1 | 1 | 0 | 0 | Move failed into unrevealed Forretress, but no hidden-info abuse. |
| 6 | p2 | Zapdos | Switch Zapdos | Forretress | 0 | 0 | 0 | 0 | 0 | Missed poison-immune support absorber. |
| 7 | p1 | Raikou | Switch Raikou | Cloyster | 0 | 0 | 0 | 0 | 0 | Missed anti-hazard owner; spectator-public exact bench limitation. |
| 7 | p2 | none | Spikes | Spikes | 1 | 1 | 1 | 1 | n/a | Correct free support conversion. |
| 8 | p1 | none | Rapid Spin | Spikes | 0 | 1 | 1 | 1 | n/a | Removal was live, but actual claimed own layer first. |
| 8 | p2 | none | Toxic | Toxic | 1 | 1 | 1 | 1 | 1 | Correct spinner/setter punishment. |
| 9 | p1 | none | Rapid Spin | Rapid Spin | 1 | 1 | 1 | 1 | n/a | Correct hazard removal. |
| 9 | p2 | none | Rapid Spin | Zapdos switch | 0 | 0 | 1 | 1 | 0 | Our spin line was active, but actual preserved Forretress and applied pressure. |
| 10 | p1 | Raikou | Switch Raikou | Switch Raikou | 1 | 1 | 1 | 1 | 1 | Correct Zapdos answer. |
| 10 | p2 | Snorlax | Switch Snorlax | Switch Snorlax | 1 | 1 | 1 | 1 | 1 | Correct counter-handoff through Spikes. |
| 11 | p1 | Skarmory/class | Switch physical answer | Misdreavus | 0 | 1 | 1 | 1 | 1 | Correct answer class; missed Ghost owner. |
| 11 | p2 | none | Double-Edge | Double-Edge | 1 | 1 | 1 | 1 | n/a | Active line got punished by unrevealed Ghost, but no public fact was ignored. |
| 12 | p1 | Raikou for Zapdos | Misdreavus pressure | Skarmory | 0 | 0 | 0 | 0 | 0 | Missed the paired handoff shape after revealing Misdreavus. |
| 12 | p2 | Zapdos | Switch Zapdos | Switch Zapdos | 1 | 1 | 1 | 1 | 1 | Correct Ghost-answer handoff. |
| 13 | p1 | Raikou | Switch Raikou | Switch Raikou | 1 | 1 | 1 | 1 | 1 | Correct forced handoff. |
| 13 | p2 | Snorlax | Switch Snorlax | Switch Snorlax | 1 | 1 | 1 | 1 | 1 | Correct counter-handoff. |
| 14 | p1 | Misdreavus/class | Switch Snorlax answer | Skarmory | 0 | 1 | 1 | 1 | 1 | Correct answer class, wrong owner. |
| 14 | p2 | Zapdos | Switch Zapdos | Earthquake | 0 | 0 | 0 | 0 | 0 | Coverage into Raikou/Misdreavus beat the over-handoff. |
| 15 | p1 | Raikou/Forretress branch | Whirlwind/phaze | Drill Peck | 0 | 1 | 1 | 0 | 0 | Phaze was too ambitious; Drill Peck covered Zapdos switch with chip. |
| 15 | p2 | Forretress/Zapdos | Switch Forretress | Zapdos | 0 | 1 | 1 | 1 | 1 | Correct switch class, wrong owner. |

## Lessons

1. Next-board forcing helped immediately. Turns 4, 10, and 13 were clean
   counter-handoff hits: Skarmory forced to Raikou, Zapdos forced to Snorlax,
   and Cloyster forced to Raikou.
2. The new risk is over-handoff. Turns 5 and 14 show that switching to the
   next-board owner is not always better than using a current move that already
   affects the likely next board.
3. For hazard pieces, the first route job is not always Spin. Turn 8 showed
   Cloyster setting its own layer before removing the opponent's layer.
4. Possible-only absorbers stayed quarantined. I did not count Forretress,
   Misdreavus, or hidden Rapid Spin as known before reveal; misses there were
   scored as spectator-public owner misses, not hidden-info facts.

## Updated Boundary

Before choosing a counter-handoff, compare three actions:

1. Active pressure that still affects the expected branch.
2. Coverage/status/phaze/setup that affects the expected branch.
3. The handoff to the next-board owner.

Choose the handoff only when it clearly beats the active or coverage line after
switch cost, Spikes damage, recoil, and information loss are priced.

## Next Rep

Run one fresh segment or targeted review focused on the over-handoff boundary:
positions where a visible active move or coverage move already improves the
next board enough that switching to the owner is excessive.
