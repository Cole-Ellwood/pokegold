# Side-Known Transfer 006 - smogtours-gen2ou-885822 p2 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-885822`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-885822.log`

Mode: one-side side-known reconstructed, p2 only, turns 1-21. Opponent
information stayed spectator-public.

Contamination control:
- Local `rg docs` found no prior `smogtours-gen2ou-885822` reference before
  selection.
- Only p2 was advised. No p1 side-known advice was produced.
- Hidden opponent moves stayed in public tiers.

Post-score sources:
- Smogon Forums, [GSC OU Steelix](https://www.smogon.com/forums/threads/gsc-ou-steelix.3705042/).
- Smogon Forums, [GSC OU Snorlax](https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/).
- Smogon Forums, [GSC OU Sample Teams Breakdown](https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/).

## Score Summary

Decisions: 21 p2 decisions.

Top-match: 13/21.

Acceptable-match: 20/21.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 18/21.

Route-converting move chosen: 17/21.

Branch-punish chosen: 14/19.

Role-package update obeyed: 17/21.

Earliest meaningful error: turn 9, overfocusing on the active Donphan and
missing the Snorlax counter-handoff from the Raikou/Donphan branch.

Verdict: limited positive transfer. The packet clears the top and acceptable
gates, keeps severe/hidden/state/mechanics at zero, and the Rest wake-count
repair held on turn 19. It is not proof by itself.

## Turn Notes

- Turn 1: chose Zapdos Thunder into Forretress; actual Thunder. Top.
- Turn 2: chose Thunder into low Forretress / switch; actual Thunder into
  Raikou miss. Top.
- Turn 3: chose Steelix into Raikou; actual Snorlax as both sides switched
  Snorlax. Miss, acceptable by Electric/Snorlax owner class.
- Turn 4: chose Steelix into opposing Snorlax; actual Forretress into
  Double-Edge. Miss, acceptable by Normal-resist class, but I underweighted
  Forretress's Spikes job.
- Turn 5: chose Forretress Spikes; actual Spikes into Misdreavus. Top.
- Turn 6: chose Steelix into Misdreavus Toxic; actual Steelix. Top.
- Turn 7: chose Steelix Earthquake; actual Earthquake into Donphan. Top.
- Turn 8: chose Starmie into Donphan; actual Zapdos as Donphan spun. Miss,
  acceptable by Donphan-pressure class.
- Turn 9: chose Starmie; actual Snorlax as both sides switched Snorlax. Miss,
  not acceptable. I missed the counter-handoff after Donphan/Raikou.
- Turn 10: chose Forretress into Snorlax; actual Snorlax Double-Edge. Miss,
  acceptable as preservation/support, but direct pressure was better.
- Turn 11: chose Snorlax Rest; actual Rest after surviving Double-Edge. Top.
- Turn 12: chose Sleep Talk; actual Sleep Talk into Skarmory. Top.
- Turn 13: chose Zapdos into Skarmory; actual Sleep Talk as Skarmory
  Whirlwinded. Miss, acceptable but phaze timing was underpriced.
- Turn 14: chose Starmie Surf; actual Surf into Misdreavus. Top.
- Turn 15: chose Steelix into Misdreavus; actual Steelix as Snorlax entered.
  Top.
- Turn 16: chose Steelix Earthquake; actual Zapdos into newly revealed Surf.
  Miss, acceptable. Surf was not public before the turn, so this is not a
  hidden-info error.
- Turn 17: chose Zapdos Thunder; actual Thunder into Raikou miss. Top.
- Turn 18: chose sleeping Snorlax into Raikou; actual Snorlax as both switched
  Snorlax. Top.
- Turn 19: chose Double-Edge, not Sleep Talk, because Snorlax had already used
  two sleeping action turns; actual wake-and-act Double-Edge into Skarmory.
  Top.
- Turn 20: chose Double-Edge into Skarmory/phaze; actual Zapdos switch was
  Whirlwinded to Starmie. Miss, acceptable. I priced phaze but ranked passive
  chip over handoff.
- Turn 21: chose Starmie Surf; actual Surf KOed Forretress. Top.

## Post-Score Study

The Rest/setup timing patch transferred on the cleanest check: turn 19. The
helper still showed Snorlax as asleep, but the public Rest count said it had
already spent two sleeping action turns, so Double-Edge was correct and
Sleep Talk would have been a state/mechanics miss.

The remaining miss class is not Rest/Curse timing. It is counter-handoff
anticipation around Donphan/Raikou/Snorlax and phaze-loop handoff timing into
Skarmory. That should be watched, but not patched yet unless it repeats in the
next fresh packet.

## Next Rep

Collect at least one more fresh side-known packet before making a trend claim.
If counter-handoff misses repeat twice, stop and repair that class instead of
continuing broad replay volume.
