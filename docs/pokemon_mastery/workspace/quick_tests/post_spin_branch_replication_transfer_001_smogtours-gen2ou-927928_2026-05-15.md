# Post-Spin Branch Replication Transfer 001 - smogtours-gen2ou-927928 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-927928`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-927928.log`

Selection metadata:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&server=smogtours&page=7`

Mode: spectator-public no-Team-Preview turn pause. Smogtours current Gen 2 OU
metadata was used only for replay selection. The raw log was downloaded to
`tmp/pokemon_mastery_replays/smogtours-gen2ou-927928.log` and exposed only via
`tools/pokemon_mastery/replay_turn_pause.py` prompt/reveal turns 1-12.

Contamination control:
- Local `rg` found no prior `smogtours-gen2ou-927928` reference in `docs` or
  `tmp` before download.
- No replay UI, team paste, or future turn text was inspected before answers.
- Pre-freeze context was limited to `active_context.md`, `live_core.md`,
  `replay_turn_pause_protocol.md`, and the role/owner/reset tiny cards.
- Post-score study used current Smogon GSC sources only after answers froze.

Post-score web/current sources:
- Smogon, [Explosion in GSC](https://www.smogon.com/gs/articles/guide_to_explosion).
- Smogon Forums, [GSC OU Machamp](https://www.smogon.com/forums/threads/gsc-ou-machamp.3705043/).
- Smogon Forums, [GSC Gengar WIP](https://www.smogon.com/forums/threads/gengar-wip.3703761/).
- Smogon, [Introduction to Competitive GSC](https://www.smogon.com/smog/issue28/gsc).
- Smogon Forums, [GSC OU Threat List, Steelix](https://www.smogon.com/forums/threads/gsc-ou-threat-list-qc-2-2-gp-2-2.3477110/page-2#post-4719214).

## Score Summary

Decisions: 24.

Top-match: 11/24.

Acceptable-match: 22/24.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 1.

Mechanics errors: 0.

Positive-selection: 19/24.

Route-converting move chosen: 17/24.

Branch-punish chosen: 14/23.

Role-package update obeyed: 14/18.

Earliest meaningful error: turn 3 p2, overranking the double-switch owner map
and missing Steelix's forced-turn Curse package.

Verdict: failed replication packet. This is not a broad sample verdict by
itself, but the packet repeated one-cycle converter misses often enough to
trigger study before more replay grinding.

## Turn 1

Public state: p1 Cloyster vs p2 Zapdos.

My p1 answer: switch to Electric absorber, preferably Raikou; alternatives
Spikes, Toxic or Icy Wind if accepting immediate Thunder damage. Public tier:
strong-prior Electric handoff, no hidden team slot assumed.

My p2 answer: Thunder; alternatives switch to Snorlax/Raikou/Ground, or Hidden
Power only as an unrevealed coverage branch.

Actual choices: p1 Raikou, p2 Thunder.

Grade: p1 top, p2 top. Positive-selection both yes.

Reusable lesson: lead Cloyster into Zapdos starts with public owner discipline,
not an automatic Spikes script.

## Turn 2

Public state: p1 Raikou 91 after Leftovers vs p2 Zapdos.

My p1 answer: Thunder; alternatives Roar if owned, or switch only if fearing a
hard Ground handoff. Worst branch: Steelix or Golem blanks Thunder.

My p2 answer: switch Ground/Electric absorber, with Steelix or a similar Ground
as the clean owner; alternatives Thunder paralysis or Snorlax.

Actual choices: p2 Steelix, p1 Thunder.

Grade: p1 top by exact move but branch-punish no; p2 top by class. Positive
yes for both.

Reusable lesson: exact top can still hide a weak branch map.

## Turn 3

Public state: p1 Raikou vs p2 Steelix, no hazards.

My p1 answer: switch Cloyster as the visible Steelix owner; alternatives
Snorlax/Water or stay only as a high-risk read.

My p2 answer: switch Zapdos/Electric owner into the expected Cloyster; ranked
after that Earthquake and Roar. I did not rank Curse.

Actual choices: p1 Cloyster, p2 Curse.

Grade: p1 top. p2 top miss, acceptable only as a side-known/package gap.
Positive-selection p2 yes, but role-package obedience no.

Reusable lesson: a forced switch is not only a counter-handoff spot. If Steelix
has a Curse package, the one-cycle line can be Curse into Explosion or boosted
pressure, not simply "go to the Cloyster owner."

## Turn 4

Public state: p1 Cloyster vs p2 +1 Steelix.

My p1 answer: Surf; alternatives Spikes if expecting switch, Explosion only if
the post-trade owner is named.

My p2 answer: switch Zapdos/Electric owner; alternatives Roar or Explosion as a
cash-out branch after pricing Surf.

Actual choices: p1 Surf, p2 Explosion. Steelix survived Surf at 20% and traded
for Cloyster.

Grade: p1 top. p2 top miss, acceptable but package miss. Route yes, branch no.

Reusable lesson: Smogon Explosion material explicitly supports Steelix baiting
a Water, surviving Surf, and converting with +1 Explosion. Once Curse is
public, Explosion is not flavor text.

## Turn 5

Public state: p1 Raikou vs p2 Snorlax after mutual faint; p1 Cloyster down.

My p1 answer: switch Normal resist or physical owner; Golem/Steelix class top.

My p2 answer: Curse; alternatives Body Slam/Double-Edge or Lovely Kiss if
owned. I missed revealed Earthquake into the Normal-resist branch.

Actual choices: p1 Golem, p2 Earthquake.

Grade: p1 top. p2 not acceptable; branch-punish miss.

Reusable lesson: after Snorlax reveals or strongly implies Earthquake, the
Normal-resist branch must be priced before generic Curse.

## Turn 6

Public state: p1 Golem 67 vs p2 Snorlax with Earthquake revealed.

My p1 answer: Explosion, because Golem is weakened and Snorlax or a Zapdos
switch are both valuable targets; alternatives Earthquake or Roar.

My p2 answer: switch Zapdos as the Earthquake immunity and pressure owner;
alternatives Earthquake if calling no boom.

Actual choices: p2 Zapdos, p1 Earthquake.

Grade: p1 top miss but acceptable; p2 top. Positive-selection p1 yes by route
logic even though actual differed.

Reusable lesson: the oracle can be weaker than the route. The training score
still records the miss, but this was not a reason to demote Explosion thinking.

## Turn 7

Public state: p1 Golem 74 vs p2 Zapdos.

My p1 answer: Rock Slide; alternatives Explosion if choosing the immediate
trade, or switch Raikou. I underpriced the spend.

My p2 answer: switch Snorlax or another owner; Hidden Power Water/Grass was a
possible-only high-risk read, not public fact.

Actual choices: p2 Hidden Power super effective, p1 Explosion; both faint.

Grade: p1 top miss, barely acceptable but positive-selection no. p2 side-known
oracle gap; hidden-info error no because I did not anchor the hidden move.

Reusable lesson: once Golem is low and Zapdos coverage is live, Explosion can
be the correct route spend before Rock Slide damage.

## Turn 8

Public state: p1 Machamp vs p2 Snorlax.

My p1 answer: Cross Chop; alternatives Hidden Power Bug/Ghost or Earthquake
only as set-dependent branches, and switch if a Ghost hard answers.

My p2 answer: switch Ghost/Psychic/Fighting answer, with Gengar class top.

Actual choices: p2 Gengar, p1 Cross Chop.

Grade: p1 top by exact move but branch-punish no; p2 top.

Reusable lesson: top-match is not enough. Cross Chop was the actual move, but
the answer still needed the Ghost receiver plan.

## Turn 9

Public state: p1 Machamp with Cross Chop revealed vs p2 Gengar with no move
revealed.

My p1 answer: Earthquake into Gengar; fallback switch Raikou if Machamp lacked
coverage was not made explicit enough.

My p2 answer: Hypnosis or Explosion; Ice Punch not ranked high enough.

Actual choices: p1 Raikou, p2 Ice Punch.

Grade: p1 top miss, acceptable no, hidden-info error yes for anchoring
unrevealed own Earthquake as if it were available. p2 top miss but acceptable.

Reusable lesson: Machamp often has Cross Chop, Rock Slide, Curse, and a
variable fourth slot. Earthquake into Gengar is strong-prior at most until
revealed or side-known, and the fallback must be top-safe.

## Turn 10

Public state: p1 Raikou 84 vs p2 Gengar with Ice Punch revealed.

My p1 answer: Thunder; alternatives switch Machamp if predicting Snorlax, or
another owner if fearing Explosion.

My p2 answer: Explosion into Raikou or the Machamp branch; alternatives
Hypnosis or Snorlax handoff.

Actual choices: p1 Machamp, p2 Snorlax.

Grade: p1 top miss, acceptable but route-conversion no. p2 top miss,
acceptable.

Reusable lesson: this was the owner-pair check from the review. I named it as
an alternative but did not promote it.

## Turn 11

Public state: p1 Machamp vs p2 Snorlax, Gengar revealed as the prior receiver.

My p1 answer: switch Raikou into the likely Gengar handoff; alternatives Cross
Chop if Snorlax stays, Earthquake only as a high-risk set read.

My p2 answer: switch Gengar.

Actual choices: p2 Gengar, p1 Curse.

Grade: p1 top miss but acceptable; p2 top. Role-package miss for Machamp.

Reusable lesson: setup can be the branch action when the receiver cannot
immediately reset the route or when the boost changes the next board. I
overcorrected from "name owner" into automatic handoff.

## Turn 12

Public state: p1 +1 Machamp vs p2 Gengar with Ice Punch.

My p1 answer: switch Raikou; alternatives Rock Slide or other coverage only if
owned, and Cross Chop rejected into Ghost.

My p2 answer: Explosion to remove the boosted Machamp; alternatives Hypnosis
or Ice Punch chip.

Actual choices: p2 Ice Punch, p1 Rock Slide.

Grade: p1 top miss, acceptable but positive-selection no. p2 top miss,
acceptable.

Reusable lesson: after Curse is public, Machamp's Rock Slide/coverage package
must be priced before a defensive handoff. Smogon Machamp material lists Cross
Chop, Rock Slide, a variable coverage slot, and Curse as the core package.

## Post-Score Study

This was not a broad docs-size failure. The compact docs were readable, but
the new owner-pair rule overcorrected into automatic handoff. The missing step
is a local ranking order:

1. Name the next owner.
2. Price revealed or strong-prior one-cycle active converters into that owner:
   setup, coverage, phaze, Explosion, or Self-Destruct.
3. Only then choose the counter-handoff if it beats those converters or if the
   active converter is possible-only without a fallback.

Current sources support this being central GSC theory, not an isolated replay:
Steelix commonly runs Curse/Earthquake/Roar/Explosion; Gengar's offensive set
uses Ice Punch plus Explosion or utility; Machamp's known package is Cross
Chop, Rock Slide, a variable coverage slot, and Curse. The lesson is not "guess
hidden moves." It is "when the package is public, price the one-turn conversion
before escaping to the named owner."

## Structure Patch

Updated the tiny live structure rather than adding a new broad note:
- `live_core.md`: added one-cycle converter pricing before automatic handoff.
- `heuristic_core/name_next_board_owner.md`: owner naming now checks active
  setup, coverage, phaze, or cash-out before handoff.
- `heuristic_core/role_package_ledger.md`: Curse, coverage, and Explosion
  packages must be priced as this-cycle converters.
- `heuristic_core/branch_punish_ranking.md`: branch punish now explicitly
  includes setup/coverage/cash-out before switch handoff.

## Next Rep

Do not continue broad replay grinding immediately. First run a focused
one-cycle converter check or a fresh transfer that stops early on the first
Curse/coverage/Explosion versus counter-handoff cluster. Fail if an unrevealed
own move anchors the top line without a fallback.
