# Side-Known Transfer 003 - smogtours-gen2ou-923955 p2 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-923955`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-923955.log`

Mode: one-side side-known reconstructed, p2 only, turns 1-16. Opponent
information stayed spectator-public.

Contamination control:
- Local `rg docs` found no prior `smogtours-gen2ou-923955` reference before
  selection.
- Only p2 was advised. No p1 side-known advice was produced.
- The helper supplied p2's own eventually shown roster/moves only. Hidden Power
  type is still not explicit in Showdown logs, so Hidden Power exact-move
  misses are labeled as side-known helper gaps when type was decisive.

Post-score sources:
- Smogon, [GSC OU Sample Teams Breakdown](https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/).
- Smogon Forums, [Scizor OU Revamp](https://www.smogon.com/forums/threads/scizor-ou-revamp.3510707/).

## Score Summary

Decisions: 16 p2 decisions.

Top-match: 10/16.

Acceptable-match: 14/16.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 13/16.

Route-converting move chosen: 12/16.

Branch-punish chosen: 10/15.

Role-package update obeyed: 13/16.

Earliest meaningful error: turn 5, choosing Baton Pass from +1 Espeon instead
of using side-known super-effective Hidden Power to punish Moltres before
Whirlwind.

Verdict: limited positive transfer, not proof. This cleared the top and
acceptable gates and the RestTalk/absorber staging miss did not recur, but it
is only one packet and still shows helper/type and recipient-selection gaps.

## Turn Notes

- Turn 1: Electrode vs Ampharos. Chose Light Screen; actual Light Screen. Top.
- Turn 2: Chose Reflect after Light Screen; actual Reflect. Top.
- Turn 3: Chose Espeon under dual screens; actual Espeon. Top.
- Turn 4: Chose Growth with Espeon; actual Growth as Ampharos switched Moltres.
  Top.
- Turn 5: Chose Baton Pass to Kingdra; actual Hidden Power into Moltres before
  Whirlwind dragged Muk. Miss, not acceptable. Side-known player would know
  Hidden Power type; helper only printed `Hidden Power`.
- Turn 6: Chose Muk Thunder into Moltres; actual Thunder caught Qwilfish. Top.
- Turn 7: Chose Thunder into Qwilfish; actual Thunder miss after Spikes. Top.
- Turn 8: Chose Thunder again; actual Thunder into Ampharos switch. Top.
- Turn 9: Chose Sludge Bomb into Ampharos; actual switch Electrode into
  Thunderbolt. Miss, acceptable. I underweighted re-screening.
- Turn 10: Chose Light Screen; actual Light Screen. Top.
- Turn 11: Chose Reflect; actual Espeon switch into Qwilfish. Miss, acceptable.
  The Qwilfish owner was better than completing screens.
- Turn 12: Chose Psychic into Qwilfish; actual Psychic KO. Top.
- Turn 13: Chose Baton Pass to Porygon2; actual Growth as Porygon2 used
  Double-Edge. Miss, acceptable but too conservative.
- Turn 14: Chose Baton Pass to Porygon2; actual Baton Pass to Lapras. Move
  class correct, recipient miss. Acceptable.
- Turn 15: Chose Hydro Pump with +1 Lapras; actual Hydro Pump into Kingdra
  switch, miss. Top.
- Turn 16: Chose switch Muk into Kingdra; actual Lapras Ice Beam after taking
  super-effective Hidden Power. Miss, acceptable.

## Post-Score Study

The good news is that the previous repeated miss did not appear: no sleeping
RestTalk owner was auto-played over a better absorber switch. The side-known
prompt also helped screen and pass-package decisions: Light Screen -> Reflect
-> Espeon -> Growth was easy to rank because the own team route was visible.

The remaining errors are different:
- Hidden Power type is part of real side-known information, but the helper only
  prints the move name. Turn 5 was a real exact-top miss in the prompt, but a
  helper-oracle gap for player advice.
- Baton Pass requires recipient ranking, not just the move. Turn 14 got the
  action class right but chose the wrong receiver.
- Screens are not a script. After Light Screen, finishing Reflect was not
  always better than moving the enabled owner into the named branch.

## Next Rep

Run one more fresh side-known packet before claiming trend. Track exact move and
receiver separately for Baton Pass, switch, and Explosion lines. Label Hidden
Power type omissions as helper gaps unless the type is public from previous
damage/effectiveness.
