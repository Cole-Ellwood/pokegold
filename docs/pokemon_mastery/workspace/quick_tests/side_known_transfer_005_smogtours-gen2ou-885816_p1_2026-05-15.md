# Side-Known Transfer 005 - smogtours-gen2ou-885816 p1 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-885816`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-885816.log`

Mode: one-side side-known reconstructed, p1 only, turns 1-21. Opponent
information stayed spectator-public.

Contamination control:
- Local `rg docs` found no prior `smogtours-gen2ou-885816` reference before
  selection.
- Only p1 was advised. No p2 side-known advice was produced.
- Hidden opponent moves stayed in public tiers.

Post-score sources:
- Smogon Forums, [GSC OU Steelix](https://www.smogon.com/forums/threads/gsc-ou-steelix.3705042/).
- Smogon Forums, [GSC OU Snorlax](https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/).
- Smogon Forums, [GSC OU Sample Teams Breakdown](https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/).

## Score Summary

Decisions: 20 p1 decisions. Turn 4 was unscored because sleep prevented the
chosen p1 move from being logged.

Top-match: 11/20.

Acceptable-match: 18/20.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 18/20.

Route-converting move chosen: 16/20.

Branch-punish chosen: 13/18.

Role-package update obeyed: 16/20.

Earliest meaningful error: turn 1, overpreserving Cloyster with Tyranitar
instead of matching the Jynx lead with Zapdos. Main repeated error: turns
17-21, poor timing in Steelix versus Rest/Curse Snorlax, especially when to
boost during Rest turns versus attack into the next reset.

Verdict: mixed and flat. This preserves the high acceptable rate and clean
severe/hidden/state/mechanics gates, but top-match is still not improving.

## Turn Notes

- Turn 1: chose Tyranitar into Jynx; actual Zapdos into Psychic. Miss,
  acceptable by special-answer class, but I overprotected Cloyster.
- Turn 2: chose Tyranitar again; actual Snorlax into Ice Beam. Miss,
  acceptable, but Snorlax was the better early sleep/special sponge.
- Turn 3: chose Curse with Snorlax; actual Curse. Top.
- Turn 4: unscored; Jynx used Lovely Kiss and Snorlax could not act.
- Turn 5: chose Cloyster after Sleep Clause was active; actual Cloyster as the
  opponent also switched Cloyster. Top.
- Turn 6: chose Spikes; actual Toxic into opposing Cloyster. Miss, acceptable.
- Turn 7: chose Spikes; actual Spikes. Top.
- Turn 8: chose Starmie to deny the opposing Spikes loop; actual Starmie.
  Top.
- Turn 9: chose Rapid Spin; actual Rapid Spin into Snorlax. Top.
- Turn 10: chose Thunder Wave into Snorlax; actual Thunder Wave. Top.
- Turn 11: chose Steelix into CurseLax; actual Steelix into Double-Edge. Top.
- Turn 12: chose Steelix Curse; actual Curse. Top.
- Turn 13: chose Steelix Curse again; actual Curse. Top.
- Turn 14: chose Earthquake after reaching +2; actual Earthquake. Top.
- Turn 15: chose Earthquake; actual Rock Slide as Snorlax Rested. Miss,
  acceptable, but I did not rank the Rock Slide branch/PP line.
- Turn 16: chose Earthquake; actual Rock Slide into sleeping Snorlax. Miss,
  acceptable, same timing family.
- Turn 17: chose Rock Slide after seeing that branch; actual Curse. Miss, not
  acceptable. I attacked instead of exploiting the Rest window.
- Turn 18: chose Earthquake at +3; actual Earthquake after Snorlax woke and
  used Double-Edge. Top.
- Turn 19: chose Earthquake; actual Rock Slide after Snorlax Cursed. Miss,
  acceptable by pressure class, but still exact timing noise.
- Turn 20: chose Earthquake; actual Curse as Snorlax Rested. Miss, not
  acceptable. The route was to spend the Rest turn boosting, not chip into the
  reset.
- Turn 21: chose Curse at +4; actual Earthquake. Miss, acceptable. The prior
  miss overcorrected into one boost too many.

## Post-Score Study

Smogon Steelix material frames Curse as the way Steelix gains enough offensive
presence to fight Curse Snorlax one-on-one. Smogon Snorlax material also notes
that Rest without Sleep Talk gives opponents a chance to set up or phaze
safely. The replay exposed a missing live calculation: I know Rest loops matter
in words, but I was not comparing the two-turn Rest clock before ranking
Steelix's Curse, Earthquake, and Rock Slide.

The issue is not broad docs size in this packet. The compact docs were usable.
The bottleneck is a small game-theory subskill: in setup-versus-Rest mirrors,
the top move depends on whether the current hit crosses a wake/Rest threshold
or whether the free sleep turn should be spent improving the future damage
range. Same-role attacks can remain acceptable, but they will not improve
top-match until that timing is trained directly.

## Structure Patch

Update the reset-loop card and live core so Rest-loop decisions require a
two-turn clock: compare boost now then attack next versus attack now then let
Rest reset, and only count chip as progress if it changes the next forced
choice.

## Next Rep

Stop broad replay grinding for this mini-loop. Run a training-method review and
add a focused Rest/setup timing drill before collecting the next side-known
packet.
