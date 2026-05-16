# Side-Known Transfer 004 - smogtours-gen2ou-923104 p1 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-923104`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-923104.log`

Mode: one-side side-known reconstructed, p1 only, turns 1-15. Opponent
information stayed spectator-public.

Contamination control:
- Local `rg docs` found no prior `smogtours-gen2ou-923104` reference before
  selection.
- Only p1 was advised. No p2 side-known advice was produced.
- Hidden opponent moves stayed in public tiers.

Post-score sources:
- Smogon Forums, [GSC OU Snorlax](https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/).
- Smogon, [GSC OU Threatlist](https://www.smogon.com/gs/articles/gsc_threats).

## Score Summary

Decisions: 15 p1 decisions.

Top-match: 9/15.

Acceptable-match: 13/15.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 1.

Mechanics errors: 0.

Positive-selection: 12/15.

Route-converting move chosen: 11/15.

Branch-punish chosen: 9/14.

Role-package update obeyed: 11/15.

Earliest meaningful error: turn 5, overranking Cloyster's support job before
Surf pressure into Forretress. Most important error: turn 15 hidden-info error,
switching Gengar into sleeping Snorlax without pricing Sleep Talk Earthquake.

Verdict: mixed, not proof. The packet cleared top and acceptable gates, but the
hidden-info gate failed once.

## Turn Notes

- Turn 1: Snorlax Earthquake into Tyranitar. Top.
- Turn 2: chose Earthquake again; actual Golem switch into Rock Slide. Miss,
  acceptable. I underweighted the Rock-resist owner handoff.
- Turn 3: chose Golem Earthquake; actual Earthquake into Surf Tyranitar. Top.
- Turn 4: chose Cloyster Surf into Tyranitar; actual Surf into Forretress
  switch. Top.
- Turn 5: chose Spikes; actual Surf into Forretress before it set Spikes. Miss,
  acceptable but too scripted.
- Turn 6: chose Surf; actual Spikes as Forretress used Toxic. Miss, acceptable.
  This corrected the support job one turn later.
- Turn 7: chose Surf into Forretress/Zapdos branch; actual Surf into Zapdos.
  Top.
- Turn 8: chose Snorlax into Zapdos; actual Snorlax into Thunder. Top.
- Turn 9: chose Double-Edge; actual Rest as Zapdos switched Forretress. Miss,
  not acceptable. Snorlax needed to reset before the Forretress branch.
- Turn 10: chose Gengar spinblock; actual Gengar into Rapid Spin. Top.
- Turn 11: chose Gengar Thief; actual Thief into Snorlax. Top.
- Turn 12: chose sleeping Snorlax as the Snorlax absorber; actual Zapdos into
  Double-Edge. Miss, acceptable by absorber class.
- Turn 13: chose Protect with Zapdos; actual Protect as Snorlax Rested. Top.
- Turn 14: chose Thunderbolt; actual Thunderbolt into Sleep Talk Double-Edge.
  Top.
- Turn 15: chose Gengar into sleeping Snorlax; actual Cloyster into Sleep Talk
  Earthquake. Miss, not acceptable, hidden-info error. I let unrevealed
  Snorlax coverage be absent by default and overvalued the Normal immunity.

## Post-Score Study

Side-known mode is helping exact own-team routing, but it does not remove
public-tier discipline. The turn 15 miss is the same family as older hidden
coverage errors: a Ghost switch can punish Double-Edge, but RestTalk Snorlax's
coverage roll must be priced before the Ghost becomes top.

Smogon Snorlax material explicitly frames Double-Edge plus Earthquake as a core
coverage package: Double-Edge pressures Zapdos and opposing Snorlax, while
Earthquake hits Rock/Steel/Ghost answers. In no-Team-Preview side-known play,
the opponent's Earthquake was still not revealed before turn 15, so it could
shape the branch but should not be ignored.

## Structure Patch

Updated `heuristic_core/role_package_ledger.md` so RestTalk routing asks what
each revealed or strong-prior Sleep Talk roll does to the proposed absorber.

## Next Rep

Do not claim side-known progress yet. The combined side-known sample is near
the top gate but has a hidden-info error. Next work should either run a focused
RestTalk-coverage regression or a fresh side-known packet that fails fast on
Ghost/absorber switches into sleeping Snorlax.
