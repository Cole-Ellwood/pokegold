# Snorlax/Forretress Counter-Handoff Transfer 001 - smogtours-gen2ou-933120 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933120`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933120.log`

Search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&server=smogtours&page=3`

Mode: spectator-public no-Team-Preview turn pause. Smogtours replay, selected
from current metadata and turn count only. I did not inspect move content or
future turns before freezing answers.

## Sources Checked

Local docs checked before or after the scored run:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/active_pressure_before_status.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/cashout_boundary.md`
- `reviews/counter_handoff_review_001_smogtours-gen2ou-907837_2026-05-14.md`
- `workspace/quick_tests/branch_handoff_obedience_probe_001_2026-05-14.md`

Current web sources used only after scoring, before any further replay:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, Forretress OU Revamp:
  `https://www.smogon.com/forums/threads/forretress-ou-revamp-done.3647111/`
- Smogon, GSC OU Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`

## Contamination Control

- Local `rg` found no prior `smogtours-gen2ou-933120` use before selection.
- The log was saved locally at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-933120.log`.
- Prompts used
  `python tools/pokemon_mastery/replay_turn_pause.py ... prompt --turn N`.
- Reveals used
  `python tools/pokemon_mastery/replay_turn_pause.py ... reveal --turn N`.
- Fresh reveals stopped at turn 7 after repeated counter-handoff errors in the
  Snorlax, Forretress, Zapdos, and Cloyster cycle.

## Score Summary

Decisions: 14 scored, 0 unscored.

Top-match: 3/14.
Acceptable-match: 9/14.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.
Positive-selection: 10/14.
Route-converting move chosen: 7/14.
Branch-punish chosen: 6/13.
Earliest meaningful error: turn 2 p1.

Result: not progress. This was an early-stop packet. Severe, hidden-info,
state, and mechanics stayed clean, but top-match, route conversion, and branch
obedience were below target. The repeated class was early-cycle handoff timing:
I over-preserved Snorlax before pricing Rest-enabled Double-Edge pressure, then
missed the p1 and p2 counter-handoffs that met the next board.

## Frozen Answer Log

Candidates are ranked in order. Tags: `P` positive-selection, `R`
route-converting, `B` branch-punish.

| Turn | Side | Frozen top three | Actual | Grade | Tags | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Fire/coverage if available; Curse; active attack if no coverage | Double-Edge | acceptable | P | Conditional coverage was too high; Double-Edge was the real active pressure shown. |
| 1 | p2 | Spikes; Toxic; Explosion high-risk | Toxic | acceptable | P/R/B | Toxic into lead Snorlax was a route timer, not a generic status click. |
| 2 | p1 | Special-pressure or Explosion-guard handoff; Fire/coverage; Double-Edge if no owner | Double-Edge | miss | - | Over-preserved; Rest-capable Snorlax could keep damaging Forretress before clearing Toxic. |
| 2 | p2 | Spikes; Hidden Power/coverage; preserve Forretress | Spikes | top | P/R/B | Correct missing-layer job. |
| 3 | p1 | Ghost/boom guard; Zapdos/special pressure; continue damage only if no owner | Zapdos | acceptable | P/R/B | Correct pressure class but over-ranked Ghost over the revealed Zapdos owner. |
| 3 | p2 | Ghost/Normal immunity handoff; Explosion high-risk; Hidden Power coverage | Hidden Power | acceptable | P | Coverage into the switch was ranked but too low. |
| 4 | p1 | Thunder; Hidden Power if available; preserve Zapdos | Snorlax | miss | - | Missed the double-handoff into the incoming Snorlax board. |
| 4 | p2 | Snorlax/special wall; Electric check; preserve Forretress | Snorlax | top by class | P/R/B | Correctly met Zapdos with the special owner. |
| 5 | p1 | Normal-resist/phazer handoff; Rest if available; Double-Edge | Rest | acceptable | P/R | Rest cleared the Toxic timer; it should have been top once Double-Edge plus Rest was public enough. |
| 5 | p2 | Curse; Double-Edge; Lovely Kiss if available | Forretress | miss | - | Missed Forretress as the handoff into RestLax and possible Sleep Talk/burn-turn branches. |
| 6 | p1 | Sleep Talk if available; Zapdos pressure handoff; burn sleep only if safe | Zapdos | acceptable | P/B | Correctly left the sleeping target, but Sleep Talk was over-ranked before reveal. |
| 6 | p2 | Snorlax handoff; Explosion high-risk; Hidden Power | Toxic | miss | P | Missed Toxic into the Zapdos switch as the branch-punish; Snorlax handoff was too generic. |
| 7 | p1 | Thunder; Hidden Power if available; preserve Zapdos | Cloyster | miss | - | Missed Cloyster as the Snorlax-board owner and repeated active-pressure over handoff. |
| 7 | p2 | Snorlax; Electric check; preserve Forretress | Snorlax | top by class | P/R/B | Correctly met Zapdos again with the Snorlax owner. |

## Main Errors

Turn 2 p1:
I treated Toxic plus Spikes as a reason to leave Snorlax immediately. The replay
showed the opposite: Snorlax had already revealed enough active pressure, and
Rest later cleared the Toxic clock. The next Double-Edge changed Forretress's
future job by taking it from 83% to 66%.

Turns 4 and 7 p1:
I kept Thunder as the default Zapdos pressure move after naming that p2's next
board was Snorlax. The actual p1 answers were Snorlax first, then Cloyster.
Both were counter-handoffs, not attacks into the leaving Forretress.

Turn 5 p2:
I treated healthy Snorlax as a setup invitation and missed the Forretress
handoff into RestLax. Forretress had already delivered Toxic and Spikes, but it
still compressed Normal resistance, coverage, and sleep-turn pressure.

Turn 6 p2:
I missed the revealed Toxic into the Zapdos branch. The move failed, but the
selection was coherent: p2 punished the pressure handoff, not the sleeping
Snorlax that was likely to leave.

## Reusable Lesson

In early GSC lead cycles, do not choose between "attack" and "switch" in the
abstract. Ask:

1. Has the active already revealed a pressure route that changes the support
   piece's future HP, timer, or job?
2. Can Rest, Sleep Talk, or recovery clear the status clock after the pressure
   turn?
3. If the active is leaving, who owns the next board: Snorlax, Forretress,
   Cloyster, Electric, Ghost, Skarmory, or a phazer?
4. Does the top action move that owner in, hit that owner, or explicitly beat
   the branch that punishes the handoff?
