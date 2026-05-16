# Ground Receiver Triangle Transfer 001 - gen2ou-2591556155 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/gen2ou-2591556155`

Raw log:
`https://replay.pokemonshowdown.com/gen2ou-2591556155.log`

Search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&page=6`

Mode: spectator-public no-Team-Preview turn pause. Public ladder replay,
rating 1422, selected from current metadata and turn count only. I did not
inspect move content or future turns before freezing answers.

Contamination control:

- Local `rg` found no prior `gen2ou-2591556155` use before selection.
- The log was saved locally at
  `tmp/pokemon_mastery_replays/gen2ou-2591556155.log`.
- Prompts used
  `python tools/pokemon_mastery/replay_turn_pause.py ... prompt --turn N`.
- Reveals used
  `python tools/pokemon_mastery/replay_turn_pause.py ... reveal --turn N`.
- Web and docs study happened only after turn 25 was scored.

## Score Summary

Decisions: 49 scored, 1 unscored.
Unscored: turn 20 p2, because full paralysis hid the selected move.

Top-match: 20/49.
Acceptable-match: 40/49.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 1.
Mechanics errors: 0.
Positive-selection: 37/49.
Route-converting move chosen: 35/49.
Branch-punish chosen: 24/42.
Earliest meaningful error: turn 2 p2.

Result: better than the prior transfer on several positive-selection metrics,
but not mastery or a stable trend. Top-match is still below gate, branch
punish is still weak, and one hidden-info/set-availability error appeared.

## Frozen Answer Log

Candidates are ranked in order. Tags: `P` positive-selection, `R`
route-converting, `B` branch-punish.

| Turn | Side | Frozen top three | Actual | Grade | Tags | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Sleep Powder; Stun Spore; switch special wall | Stun Spore | acceptable | P/R | Sleep was not absurd, but paralysis was the pro route into Raikou. |
| 1 | p2 | Hidden Power; switch status absorber; Thunder | Hidden Power | top | P/R | Active pressure before status absorber guess. |
| 2 | p1 | Stun Spore; switch Snorlax; Psychic/Giga Drain | Snorlax | acceptable | P/R/B | Status into Skarmory was defensible, but handoff was cleaner. |
| 2 | p2 | Hidden Power; switch Skarmory; switch Ghost | Skarmory | miss | - | I overvalued active chip into an obvious status/switch cycle. |
| 3 | p1 | Fire Blast if available; Lovely Kiss; switch Electric | Zapdos | acceptable | P/R | Coverage into Skarmory was plausible, but Zapdos won the next board. |
| 3 | p2 | Whirlwind; Toxic; switch Ghost | Misdreavus | miss | - | I did not give the Normal immunity enough weight. |
| 4 | p1 | Thunder; switch Exeggutor; switch Snorlax | Exeggutor | miss | - | Named Raikou but failed to obey the counter-handoff. |
| 4 | p2 | switch Raikou; Toxic/Thunder; switch Skarmory | Raikou | top | P/R/B | Correctly used the Electric receiver into Zapdos. |
| 5 | p1 | Stun Spore; switch Snorlax; Psychic/Giga Drain | Snorlax | acceptable | P/R/B | Still acceptable, but repeated cycle favored the Snorlax handoff. |
| 5 | p2 | switch Skarmory; Hidden Power; switch Misdreavus | Skarmory | top | P/R/B | Correctly exited Raikou before paralysis. |
| 6 | p1 | switch Zapdos; Fire Blast if available; Lovely Kiss | Zapdos | top | P/R/B | Correctly met the Ghost branch through Zapdos. |
| 6 | p2 | switch Misdreavus; Whirlwind/Toxic; switch Raikou | Misdreavus | top | P/R/B | Correctly blocked Snorlax. |
| 7 | p1 | switch Exeggutor; Thunder; switch Snorlax | Exeggutor | top | P/R/B | Repeated cycle obeyed. |
| 7 | p2 | switch Raikou; Toxic/Thunder; switch Skarmory | Raikou | top | P/R/B | Repeated cycle obeyed. |
| 8 | p1 | switch Snorlax; Stun Spore; Psychic/Giga Drain | Stun Spore | acceptable | P/R/B | I over-adjusted; status into Skarmory still had value. |
| 8 | p2 | switch Skarmory; Hidden Power; switch Misdreavus | Skarmory | top | P/R/B | Correct. |
| 9 | p1 | Stun Spore; switch Zapdos; switch Snorlax | Zapdos | acceptable | P | Missed the preservation handoff after Skarmory stayed active. |
| 9 | p2 | Drill Peck; Toxic; Whirlwind | Drill Peck | top | P/R | Active pressure beat passive support. |
| 10 | p1 | switch Exeggutor; Thunder; switch Snorlax | Exeggutor | top | P/R/B | Correct counter-handoff. |
| 10 | p2 | switch Raikou; Drill Peck; switch Starmie | Raikou | top | P/R/B | Correct counter-handoff. |
| 11 | p1 | Stun Spore; switch Snorlax; Psychic/Giga Drain | Stun Spore | top | P/R | Converted the Raikou route with paralysis. |
| 11 | p2 | switch Skarmory; Hidden Power; Rest if available | Hidden Power | acceptable | P/R/B | Switch would preserve Raikou; actual spent HP for chip and got punished. |
| 12 | p1 | switch Snorlax; Psychic/Giga Drain; switch Zapdos | Snorlax | top | P/R/B | Preserved Exeggutor after paralysis landed. |
| 12 | p2 | switch Skarmory; Hidden Power; Rest if available | Hidden Power | acceptable | P/R | Actual chipped the handoff; switch remained defensible. |
| 13 | p1 | Earthquake if available; Double-Edge; Lovely Kiss | Double-Edge | miss | hidden | I anchored a possible-only Snorlax coverage move into a Skarmory branch. |
| 13 | p2 | switch Misdreavus; switch Skarmory; Hidden Power | Skarmory | acceptable | P/R/B | Misdreavus blocked the actual move, but Skarmory kept the physical wall. |
| 14 | p1 | switch Zapdos; Fire Blast if available; Double-Edge | Zapdos | top | P/R/B | Correct handoff into the Ghost/Skarmory branch. |
| 14 | p2 | switch Misdreavus; Whirlwind; Toxic | Misdreavus | top | P/R/B | Correct Normal immunity handoff. |
| 15 | p1 | Thunder; switch Exeggutor; switch Marowak/Ground if public | Marowak | acceptable | P/R | Thunder punished Toxic stay, but missed the finite Ground converter. |
| 15 | p2 | switch Raikou; Toxic; switch Skarmory | Toxic | miss | - | I failed to cover the Ground route piece entering Zapdos/Raikou loops. |
| 16 | p1 | Rock Slide; Earthquake; Swords Dance | Fire Blast | acceptable | P/R/B | Correct idea was receiver coverage; exact coverage was Fire Blast. |
| 16 | p2 | switch Skarmory; switch Starmie; Misdreavus utility | Starmie | acceptable | P/R/B | Skarmory was visible, but Starmie was the safer Water answer. |
| 17 | p1 | switch Zapdos; switch Snorlax; switch Exeggutor | Snorlax | acceptable | P/R/B | Correct preserve-Marowak idea; Snorlax was the better Surf receiver. |
| 17 | p2 | Surf; Recover; switch Skarmory | Surf | top | P/R | Correctly forced out Marowak. |
| 18 | p1 | switch Zapdos; Double-Edge; Lovely Kiss if available | Zapdos | top | P/R/B | Correctly met the Starmie/Normal-resist branch. |
| 18 | p2 | switch Misdreavus; switch Forretress; Surf | Forretress | miss | - | Missed the hazard/resist route over another Ghost block. |
| 19 | p1 | Thunder; Hidden Power Fire if available; switch Marowak | Thunder | top | P/R | Correctly pressured Forretress instead of giving free Spikes. |
| 19 | p2 | Spikes; switch Raikou; Explosion high-risk | Raikou | acceptable | P/R | Spikes was route work, but Raikou was the actual branch answer. |
| 20 | p1 | switch Snorlax; switch Marowak; Thunder | Marowak | miss | - | I chose safe absorption over spending the Ground route piece. |
| 20 | p2 | Hidden Power; switch Skarmory; Rest if available | full paralysis | unscored | - | Chosen move not recoverable from log. |
| 21 | p1 | Earthquake; Fire Blast; Rock Slide | Fire Blast | miss | - | I failed the named Skarmory receiver after Fire Blast was the route move. |
| 21 | p2 | switch Starmie; switch Skarmory; Hidden Power | Skarmory | acceptable | P/R/B | Starmie was defensible, but Skarmory directly caught Ground. |
| 22 | p1 | Fire Blast; Earthquake on switch; switch Zapdos | Earthquake | acceptable | P/R | Fire Blast still pressured Rest Skarmory; actual covered the switch. |
| 22 | p2 | switch Starmie; Rest; Drill Peck | Rest | acceptable | - | I preserved but did not reset; Rest was stronger route maintenance. |
| 23 | p1 | Fire Blast; Earthquake on Starmie switch; switch Zapdos | Earthquake | miss | - | After Rest, the counter-pivot was Starmie, not the sleeping Skarmory. |
| 23 | p2 | switch Starmie; stay asleep; switch Raikou | Starmie | top | P/R/B | Correctly left before spending Skarmory sleep turns. |
| 24 | p1 | switch Snorlax; switch Zapdos; Earthquake on Recover | Zapdos | acceptable | P/R/B | Correct preserve-Marowak idea; Zapdos punished Recover better. |
| 24 | p2 | Surf; Recover; switch Raikou | Recover | miss | - | Surf beat only the stay-in branch; Recover converted the forced switch. |
| 25 | p1 | switch Exeggutor; switch Ground/Steel if public; Thunder | Steelix | acceptable | P/R/B | Correct class, hidden exact owner. |
| 25 | p2 | switch Raikou; Recover; Surf | Raikou | top | P/R/B | Correct Electric receiver into Zapdos. |

## Reusable Lessons

- Repeated counter-handoff cycles are evidence, but the answer is the move
  that wins the next node, not a memorized copy of the previous node.
- Once a Ground breaker enters a paralyzed Electric loop, spend the finite
  route piece on the receiver triangle: Fire Blast into Skarmory/Forretress,
  Earthquake into Starmie/Water, or hand off if the required coverage is only
  possible-only.
- After a wall uses Rest, ask whether it stays to spend sleep turns, has
  Sleep Talk, or leaves immediately to a counter-pivot. If it switches out,
  its Rest sleep turns have not been spent.
- When Recover is available and the opponent is likely to preserve the active
  threat, recovery can be the route-converting move; attacking the stay-in
  branch may be merely safe.
