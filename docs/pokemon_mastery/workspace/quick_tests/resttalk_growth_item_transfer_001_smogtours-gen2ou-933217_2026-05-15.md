# RestTalk/Growth/Item Transfer 001 - smogtours-gen2ou-933217 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933217`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933217.log`

Search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&server=smogtours&page=3`

Mode: spectator-public no-Team-Preview turn pause. Smogtours replay, selected
from current metadata and turn count only. I did not inspect move content or
future turns before freezing answers.

Contamination control:

- Local `rg` found no prior `smogtours-gen2ou-933217` use before selection.
- The log was saved locally at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-933217.log`.
- Prompts used
  `python tools/pokemon_mastery/replay_turn_pause.py ... prompt --turn N`.
- Reveals used
  `python tools/pokemon_mastery/replay_turn_pause.py ... reveal --turn N`.
- Fresh reveals stopped at turn 30 after a large non-perfect packet. No turn 31
  or later move content was inspected.

Players: p1 `fakes`, p2 `just fabbio`.

## Score Summary

Decisions: 58 scored, 2 unscored.

Top-match: 29/58.
Acceptable-match: 50/58.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.
Positive-selection: 45/58.
Route-converting move chosen: 40/58.
Branch-punish chosen: 31/47.
Earliest meaningful error: turn 1.

Result: useful study packet, not progress proof. Severe, hidden-info, state,
and mechanics gates stayed clean, and acceptable/positive metrics were strong.
The run still fails the approved proof gate because top-match stayed under 55%
and several unresolved positive-selection classes repeated: item-first Thief
versus generic lead status, active-removal versus over-handoff, Espeon Growth
and coverage package re-solving, and CurseLax Rest timing into RestTalk
Electric pressure.

Sleep Talk notes before public reveal were treated as conditional side-known
lines with public fallbacks. They are acceptable when the side-owned move would
make the advice legal, but they are not counted as public top-matches before
Sleep Talk was revealed.

## Frozen Answer Log

Candidates are ranked in order. Tags: `P` positive-selection, `R`
route-converting, `B` branch-punish.

| Turn | Side | Frozen top three | Actual | Grade | Tags | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Sleep Powder; Stun Spore; Psychic/Giga Drain or switch if absorber branch stronger | Thief | miss | - | Under-ranked no-item/item-denial Exeggutor; sleep was safe but missed p1's route. |
| 1 | p2 | Sleep Powder; Stun Spore; Psychic/Giga Drain or switch if absorber branch stronger | Sleep Powder | top | P/R | Correct to win the lead sleep race. |
| 2 | p1 | Preserve sleeping Exeggutor to a route owner; stay only for safe wake turns; switch absorber | Tyranitar | top | P/R | Correct to preserve the sleeper and move to the next-board owner. |
| 2 | p2 | Thief or Psychic pressure; Snorlax/Electric handoff; avoid wasting sleep | Thief | top | P/R | Correct item pressure into the sleeping target's handoff. |
| 3 | p1 | Pursuit trap; Crunch/Rock Slide if it stays; coverage only if side-known | Pursuit | top | P/R/B | Correct trap pressure on the weakened Exeggutor branch. |
| 3 | p2 | Cloyster/physical answer switch; status or Explosion if it converts; attack only if staying safe | Cloyster | top by class | P/R/B | Correct support-owner handoff. |
| 4 | p1 | Switch to Cloyster owner/Electric/special pressure; Rock Slide if staying; coverage only if side-known | Rock Slide | acceptable | P | Active chip was defensible, but the clean route was usually handoff. |
| 4 | p2 | Spikes; Surf/coverage if Tyranitar stays; Toxic/Explosion | Spikes | top | P/R | Correct first field job. |
| 5 | p1 | Rock Slide again if it removes support; handoff if Surf/Explosion risk dominates; Pursuit only on Egg | Zapdos | acceptable | P/B | Correct preservation class, exact Zapdos hidden. |
| 5 | p2 | Surf; Explosion if it opens a named route; preserve/switch if future job matters | Surf | top | P/R | Correct active pressure after Spikes. |
| 6 | p1 | Thunder; Rest/preserve if low; double to Electric absorber if switch is forced | Thunder | top | P/R | Correct active removal pressure. |
| 6 | p2 | Electric absorber; Explosion if named follow-up; Surf/Icy Wind if staying | Raikou | top by class | P/R/B | Correct Raikou receiver. |
| 7 | p1 | Special-wall/Ground handoff; Thunder if staying; Rest if revealed | Thunder | acceptable | P/R | Over-handoff risk: Thunder removed Cloyster through the switch. |
| 7 | p2 | Thunder pressure; RestTalk setup later; double to physical owner if handoff obvious | Cloyster | miss | - | Sac/pivot line was not named. |
| 8 | p1 | Cloyster/physical owner; Thunder only if staying chunks through no Rest; status if set | Cloyster | top by class | P/R | Correct Snorlax answer. |
| 8 | p2 | Curse or Body Slam/Double-Edge pressure; Lovely Kiss if set; switch only if phaze/counter risk | Body Slam | top | P/R | Correct immediate Snorlax pressure. |
| 9 | p1 | Spikes; Toxic/Surf; Explosion only with named follow-up | Spikes | top | P/R | Correct equalizing field job. |
| 9 | p2 | Coverage/Thunder if revealed; Curse if expecting Spikes; Body Slam/Double-Edge pressure | Raikou | miss | - | Missed p2's special receiver handoff into the support piece. |
| 10 | p1 | Ground/Tyranitar/Snorlax owner; Explosion only with named Electric follow-up; Surf/Icy Wind if staying | Nidoking | top by class | P/R/B | Correct Ground receiver into Thunder. |
| 10 | p2 | Thunder; Hidden Power for Ground; double to Snorlax/Water answer | Thunder | top | P/R | Correct Electric pressure, blanked by the Ground handoff. |
| 11 | p1 | Earthquake; Lovely Kiss if sleep live and switch likely; coverage only if revealed | Earthquake | top | P/R | Correct removal pressure. |
| 11 | p2 | Switch Skarmory/Exeggutor/Water receiver; Hidden Power if present; Rest only if safe | Hidden Power | acceptable | P | Correct to price revealed/side-owned coverage, not public top before reveal. |
| 12 | p1 | Earthquake to remove or punish switch; Lovely Kiss into switch; preserve only if Nidoking too valuable | Earthquake | top | P/R | Correct active pressure through the switch. |
| 12 | p2 | Switch receiver/sack to preserve Raikou; Hidden Power if staying; Rest if safe | Espeon | acceptable | P/B | Correct leave-Raikou class, exact Espeon hidden. |
| 13 | p1 | Earthquake/attack if it removes Espeon; Tyranitar if Psychic threatens; Lovely Kiss if sleep live | Tyranitar | acceptable | P/B | Correct Psychic-trap owner, though active attack was live. |
| 13 | p2 | Psychic damage; Morning Sun if safe; Baton Pass/setup only if revealed/strongly implied | Morning Sun | acceptable | P/R | Correct recovery when it resets the target. |
| 14 | p1 | Pursuit if Espeon leaves; Crunch/Rock Slide if it stays; switch only if coverage threatens | Crunch | acceptable | P/R | Correct stay-branch punish, but Pursuit was over-ranked. |
| 14 | p2 | Switch Snorlax/physical owner; Morning Sun if it wins Pursuit race; Psychic/coverage if staying | Growth | miss | - | Failed to reclassify Morning Sun Espeon as a Growth package. |
| 15 | p1 | Crunch to remove; Pursuit if it flees; Rock Slide only if equivalent | Crunch | top | P/R | Correct immediate package denial. |
| 15 | p2 | Morning Sun if it survives; switch if Pursuit survivable; boosted Psychic only if it removes TTar | Hidden Power | miss | - | Coverage into Tyranitar was possible and became fact only after reveal. |
| 16 | p1 | Nidoking/Ground to blank Thunder; attack if it removes Raikou; sacrifice only if opens Zapdos | Nidoking | top by class | P/R/B | Correct Ground handoff. |
| 16 | p2 | Hidden Power for Ground; Thunder if no Ground; Rest if safe | Hidden Power | top | P/R/B | Correct revealed branch punish. |
| 17 | p1 | Earthquake if Raikou stays; preservation switch if Nidoking has future job; Lovely Kiss into switch | Snorlax | acceptable | P/B | Preservation switch was defensible, exact Snorlax owner hidden. |
| 17 | p2 | Hidden Power to remove Nidoking; switch sack if preserving Raikou; Rest only if safe | Hidden Power | top | P/R | Correct pressure into Ground. |
| 18 | p1 | Double-Edge/Body Slam to force/remove Raikou; Earthquake if side-known; Rest if timer demands | Double-Edge | top | P/R | Correct pressure before Rest/switch. |
| 18 | p2 | Rest if survives/resets; switch Snorlax if unsafe; Thunder/HP only if it changes route | Snorlax | acceptable | P/B | Correct preservation/handoff line. |
| 19 | p1 | Double-Edge cash-out; Rest if recoil/timer costly; Curse if it changes mirror | Cloyster | miss | - | Missed the support-owner handoff into opposing Snorlax. |
| 19 | p2 | Rest if safe; Body Slam/Double-Edge pressure; switch if preserving | Body Slam | acceptable | P | Active pressure was ranked but not top. |
| 20 | p1 | Explosion with named follow-up; Surf/Toxic if Ghost/absorber branch too live; switch-sack if preserving | Surf | acceptable | P/B | Correct Explosion guard into the Ghost branch. |
| 20 | p2 | Rest if safe; Body Slam/Double-Edge; switch Ghost/Rock resist if Explosion is main branch | Gengar | acceptable | P/B | Correct immunity guard branch. |
| 21 | p1 | Tyranitar trap; Surf if staying; reject Explosion into Ghost | Zapdos | miss | - | Over-handoff to Zapdos gave Gengar the coverage hit; Pursuit owner was cleaner. |
| 21 | p2 | Thunderbolt/coverage; Hypnosis/status if sleep live; switch only if preserving from Pursuit | Thunderbolt | top | P/R | Correct active pressure. |
| 22 | p1 | Thunder pressure; Tyranitar handoff if Gengar leaves/threatens boom; Rest if revealed | Thunder | top | P/R | Correct active removal pressure. |
| 22 | p2 | Electric/Normal answer switch; Thunderbolt if staying; Explosion with guard | Ice Punch | acceptable | P/R | Coverage staying line was real after reveal but not public top. |
| 23 | p1 | Hidden Power/Thunder/safe attack to remove Gengar; switch only for Explosion/preservation; Rest if available | Hidden Power | top | P/R | Correct removal. |
| 23 | p2 | Explosion/cash-out if available; Ice Punch/Thunderbolt if no boom; switch if preserving | no action, fainted first | unscored | - | Fainted before a logged choice. |
| 24 | p1 | Nidoking/Snorlax handoff; Thunder if staying trades; Hidden Power if safer | Rest | miss | - | Missed Zapdos's revealed-side RestTalk preservation route. |
| 24 | p2 | Hidden Power to punish Ground/finish Zapdos; Thunder if no Ground; Rest if safe | Thunder | acceptable | P | Thunder pressure was ranked, but HP branch was over-ranked. |
| 25 | p1 | Sleep Talk if revealed or side-known, else Snorlax/Nidoking switch; keep public fallback explicit | Sleep Talk | acceptable | P/R | Conditional side-known line was right; not a public top before reveal. |
| 25 | p2 | Thunder/Hidden Power pressure; Rest reset if safe; switch Snorlax if Sleep Talk likely | Thunder | top | P/R | Correct pressure into sleeping Zapdos. |
| 26 | p1 | Sleep Talk; switch only if preserving sleep turns | Sleep Talk | top | P/R | Correct revealed RestTalk use. |
| 26 | p2 | Rest or switch if safe; Thunder/HP if trading | fully paralyzed | unscored | - | Chosen move not recoverable from log. |
| 27 | p1 | Sleep Talk; switch only if wake timing/Spikes makes Zapdos needed | Snorlax | acceptable | P/B | Preservation switch was defensible, but Sleep Talk was over-ranked. |
| 27 | p2 | Rest if it survives Sleep Talk; otherwise switch Snorlax; then Thunder/HP | Rest | top | P/R | Correct reset. |
| 28 | p1 | Double-Edge/Body Slam pressure; Curse only if receiver cannot punish; switch if preserving | Curse | acceptable | P/R | Curse was the route, under-ranked but present. |
| 28 | p2 | Sleep Talk if revealed or side-known, else switch Snorlax/burn sleep with fallback | Sleep Talk | acceptable | P/R | Conditional side-known RestTalk line was right; public reveal happened here. |
| 29 | p1 | Double-Edge cash boost; Rest if Thunder/timer demands; Curse only if receiver cannot punish | Curse | acceptable | P/R | Second Curse was stronger than I ranked because it set up Rest conversion. |
| 29 | p2 | Switch Snorlax to stop boosted Lax; Sleep Talk if staying; preserve Raikou | Sleep Talk | acceptable | P/R | Sleep Talk pressure was live but switch was over-ranked. |
| 30 | p1 | Rest if available; Double-Edge if no Rest; reject more Curse | Rest | top | P/R | Correct to spend the boosted Snorlax turn on Rest before Thunder removed it. |
| 30 | p2 | Sleep Talk/Thunder pressure; switch Snorlax if boosted Lax threatens sweep; preserve Raikou | Thunder | top | P/R | Correct wake-and-act pressure. |

## Reusable Lessons

- Item-first utility is not a flavor choice. When a no-item Thief user is
  built to remove Leftovers from a named receiver class, rank Thief beside or
  above generic sleep/status and say what the route buys.
- Active removal is still a branch punish. If Zapdos Thunder removes Cloyster
  through the expected switch, do not over-switch just to meet the receiver.
- Espeon with Morning Sun is often a Growth or coverage package. After Growth
  appears, the opponent must remove, phaze, status, or hand off to a package
  answer before generic Pursuit or damage heuristics.
- Revealed RestTalk Electrics are active pieces while asleep. Sleep Talk and
  wake turns can force Snorlax to Rest, phaze, or attack earlier than a passive
  "sleeping target" script suggests.
- In spectator-public work, pre-reveal Sleep Talk or Hidden Power can be a
  conditional side-known or strong-prior branch, not a public fact. Keep the
  fallback visible and do not count it as a hidden-info top-match.
