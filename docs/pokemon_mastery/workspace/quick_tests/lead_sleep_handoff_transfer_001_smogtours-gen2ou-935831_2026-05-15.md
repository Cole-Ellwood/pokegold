# Lead Sleep/Handoff Transfer 001 - smogtours-gen2ou-935831 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-935831`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-935831.log`

Search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&server=smogtours&page=1`

Mode: spectator-public no-Team-Preview turn pause. Smogtours replay, selected
from current replay metadata and local non-use only. I did not inspect move
content or future turns before freezing answers.

## Sources Checked

Local docs checked before or after the scored run:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/hidden_role_voluntary_entry.md`
- `policy_cards/active_pressure_before_status.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `reviews/curselax_receiver_coverage_review_001_2026-05-15.md`
- `workspace/quick_tests/curselax_receiver_coverage_probe_001_2026-05-15.md`
- `reviews/snorlax_forretress_counter_handoff_review_001_2026-05-15.md`
- `workspace/quick_tests/early_cycle_counter_handoff_probe_001_2026-05-15.md`

Current web sources used only after stopping and scoring, before any further
fresh replay:

- Smogon Forums, An Analysis of Leads in GSC OU:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`
- Smogon Forums, Nidoking Revamp:
  `https://www.smogon.com/forums/threads/nidoking-revamp-qc-3-2-gp-2-2.3481273/`
- Smogon Forums, GSC OU Heracross:
  `https://www.smogon.com/forums/threads/gsc-ou-heracross.3699588/`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC OU Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon Forums, GSC Zapdos:
  `https://www.smogon.com/forums/threads/zapdos-qc-2-2-gp-2-2.3673848/`

## Contamination Control

- Local `rg` found no prior `smogtours-gen2ou-935831` use before selection.
- The log was saved locally at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-935831.log`.
- Prompts used
  `python tools/pokemon_mastery/replay_turn_pause.py ... prompt --turn N`.
- Reveals used
  `python tools/pokemon_mastery/replay_turn_pause.py ... reveal --turn N`.
- Fresh reveals stopped at turn 4 after repeated lead sleep/counter-handoff
  misses: I overvalued hitting or Sleep Talking the sleeping absorber, then
  missed the Cloyster handoff and Curse setup into the Snorlax board.

## Score Summary

Decisions: 8 scored, 0 unscored.

Top-match: 2/8.
Acceptable-match: 6/8.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 1.
Mechanics errors: 0.
Positive-selection: 5/8.
Route-converting move chosen: 3/8.
Branch-punish chosen: 4/8.
Earliest clean meaningful error: turn 3 p1.

Result: not progress. This was an early-stop packet with a clean severe gate
but poor top-match, route conversion, and branch obedience. The acceptable
score is inflated by top-three inclusion; the actual top actions repeatedly
failed to convert through the next-board owner. One hidden-info error was
counted because I let possible-only Fire coverage on Nidoking anchor the p1
turn 3 recommendation.

## Frozen Answer Log

Candidates are ranked in order. Tags: `P` positive-selection, `R`
route-converting, `B` branch-punish.

| Turn | Side | Frozen top three | Actual | Grade | Tags | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Thunder/electric coverage if in set; Lovely Kiss; mixed attack | Lovely Kiss | acceptable | P/R/B | Sleep was the real lead converter; coverage was a strong prior but should not eclipse revealed sleep value. |
| 1 | p2 | switch sleep/special absorber; Surf/Ice Beam pressure; Spikes | Spikes | acceptable | P/B | Cloyster's Spikes job mattered, but this oracle is noisy because Lovely Kiss missed. |
| 2 | p1 | Lovely Kiss again; Thunder/coverage; Earthquake into absorber | Lovely Kiss | top | P/R/B | Correctly used the still-live sleep route. |
| 2 | p2 | switch sleep absorber; Surf/Ice Beam; preserve Cloyster | Heracross | top by class | P/R/B | Correctly moved the sleep absorber after Spikes landed. |
| 3 | p1 | Fire/coverage into Heracross if available; Zapdos handoff; Nidoking attack | Zapdos | acceptable but hidden-info error | - | Possible-only Fire coverage was not enough to stay top; the handoff should have owned the next board. |
| 3 | p2 | Sleep Talk if set; switch owner; burn a safe sleep turn | Snorlax | miss | P | Voluntary sleep absorption did not prove Heracross should stay; preserving it and moving Snorlax owned the next board. |
| 4 | p1 | Thunder; support/status if available; switch physical owner | Cloyster | miss | - | Missed Cloyster as the Snorlax/Curse owner through own Spikes. |
| 4 | p2 | Body Slam/Double-Edge; Lovely Kiss if available; Curse/Rest | Curse | acceptable | - | Curse was the positive setup move into Zapdos/Cloyster; active damage was too generic. |

## Main Errors

Turn 3 p1:
I recognized that Heracross could be a sleep absorber, but I overfocused on
damaging the sleeping target. Nidoking Fire coverage was possible, not public;
Zapdos was the cleaner handoff when the absorber had already done its job and
p2 could move to Snorlax.

Turn 3 p2:
Heracross entering into Lovely Kiss was evidence of absorber value, not proof
that Heracross should burn sleep immediately. The actual switch to Snorlax
preserved Heracross and met the expected Zapdos/Nidoking continuation.

Turn 4 both sides:
The same handoff/setup problem repeated. I kept Zapdos Thunder and Snorlax
active damage too high. The actual line moved Cloyster into the Snorlax board
while p2 used Curse to convert through the expected Zapdos switch.

## Reusable Lesson

After a lead sleep exchange, do not stop at "sleep landed" or "absorber is
asleep." Ask what job the sleeper just completed and who owns the next board.

1. If the absorber's job was to take sleep, preserve it unless Sleep Talk is
   revealed or staying changes the board.
2. If the active attacker needs possible-only coverage to punish the sleeper,
   rank the handoff or public pressure above that coverage.
3. Against Zapdos into Snorlax with no Spikes on the opponent, name whether
   Thunder actually converts or whether Cloyster, a phazer, or another owner
   must enter.
4. For the Snorlax side, price Curse as the branch-punish into an expected
   switch before defaulting to Body Slam or Double-Edge.

