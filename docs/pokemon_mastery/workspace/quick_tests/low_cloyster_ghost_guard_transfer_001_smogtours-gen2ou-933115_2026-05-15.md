# Low Cloyster/Ghost Guard Transfer 001 - smogtours-gen2ou-933115 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933115`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933115.log`

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
- `policy_cards/cashout_boundary.md`
- `policy_cards/hidden_role_voluntary_entry.md`
- `reviews/low_cloyster_cashout_review_001_2026-05-15.md`
- `workspace/quick_tests/low_cloyster_cashout_transfer_001_gen2ou-2605299310_2026-05-15.md`

Current web sources used only after scoring, before any further replay:

- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, GSC OU Jynx:
  `https://www.smogon.com/forums/threads/jynx-gsc-ou-qc-2-2-gp-2-2.3667481/`
- Smogon Forums, GSC OU Threat List:
  `https://www.smogon.com/forums/threads/gsc-ou-threat-list-qc-2-2-gp-2.3477110/`

## Contamination Control

- Local `rg` found no prior `smogtours-gen2ou-933115` use before selection.
- The log was saved locally at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-933115.log`.
- Prompts used
  `python tools/pokemon_mastery/replay_turn_pause.py ... prompt --turn N`.
- Reveals used
  `python tools/pokemon_mastery/replay_turn_pause.py ... reveal --turn N`.
- Fresh reveals stopped at turn 5 after repeated early-cycle handoff and low
  Cloyster cash-out/guard misses.

## Score Summary

Decisions: 10 scored, 0 unscored.

Top-match: 3/10.
Acceptable-match: 6/10.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.
Positive-selection: 6/10.
Route-converting move chosen: 5/10.
Branch-punish chosen: 4/8.
Earliest meaningful error: turn 2 p1.

Result: not progress. This was an early-stop packet. Severe, hidden-info,
state, and mechanics stayed clean, but top-match, acceptable-match, route
conversion, and branch obedience were below gate. The repeated miss was the
low-support transition after a Cloyster job: I underpriced the Cloyster handoff
into Snorlax pressure, then overcorrected toward Explosion and missed both p1's
Zapdos preservation and p2's Gengar guard.

## Frozen Answer Log

Candidates are ranked in order. Tags: `P` positive-selection, `R`
route-converting, `B` branch-punish.

| Turn | Side | Frozen top three | Actual | Grade | Tags | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Lovely Kiss; Ice Beam/Psychic; Thief/utility | Ice Beam | acceptable | P/R/B | Sleep was defensible, but Ice Beam was the sharper Snorlax-switch punish. |
| 1 | p2 | switch sleep absorber such as Snorlax; Lovely Kiss if staying; coverage | Snorlax | top by class | P/R/B | Correctly met Jynx with the sleep/special owner. |
| 2 | p1 | Lovely Kiss; Ice Beam chip; switch physical/hazard owner | Cloyster | miss | - | Missed Cloyster as the Snorlax-board owner. |
| 2 | p2 | Body Slam/Double-Edge; Earthquake; switch Jynx owner | Earthquake | acceptable attack class | P/R/B | Correct active pressure into the Cloyster branch. |
| 3 | p1 | Spikes; Surf/Toxic; Explosion high-risk | Spikes | top | P/R | Correct missing-layer job. |
| 3 | p2 | Electric/pressure handoff; Double-Edge; Earthquake | Double-Edge | acceptable | P | Active Snorlax pressure was better than my handoff priority. |
| 4 | p1 | preserve Cloyster; Surf; Toxic | Toxic | miss | - | Missed Toxic as the Snorlax timer before Cloyster became expendable. |
| 4 | p2 | Double-Edge; Rest if needed; switch boom/normal guard | Double-Edge | top | P/R/B | Correct active pressure. |
| 5 | p1 | Explosion if no Ghost branch; Surf/Toxic chip; preserve Zapdos | Zapdos | miss | - | Overcorrected into cash-out and missed preserving low Cloyster while moving to pressure. |
| 5 | p2 | Double-Edge; switch Ghost/boom guard; Rest | Gengar | miss | - | Missed the Gengar guard against Explosion/Normal pressure. |

## Main Errors

Turn 2 p1:
Jynx did not keep trying to sleep or chip Snorlax. Cloyster was the
next-board owner: it absorbed Earthquake well enough, set Spikes, and opened
Toxic/cash-out branches. I found the generic physical owner too late.

Turn 4 p1:
After Spikes landed, I moved too quickly to preserve Cloyster. Toxic into
Snorlax changed the timer before Cloyster had to leave or spend itself.

Turn 5 both sides:
I overcorrected from the previous low-Cloyster cash-out lesson. Explosion was a
real branch, but not the only route. p1 preserved Cloyster with Zapdos; p2
guarded the Explosion/Normal branch with Gengar. The correct solve is a
four-way comparison: preserve low Cloyster, coverage/status, cash-out, and the
opponent's Ghost/low-value guard.

## Reusable Lesson

After Cloyster has set Spikes and landed or threatened Toxic, solve the next
turn in this order:

1. What job remains: Spikes retention, Toxic timer, coverage chip, Explosion,
   or defensive sack?
2. Does the active target need to be put on a timer before Cloyster leaves?
3. If Explosion is live, what revealed or plausible Ghost/low-value guard
   punishes it?
4. If preservation is live, which pressure owner enters and what does Cloyster
   still do later?

Do not collapse low Cloyster into "always boom" or "always preserve." The
route-converting move is whichever of status, coverage, cash-out, or handoff
beats the named next-board owner.
