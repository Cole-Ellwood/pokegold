# CurseLax Receiver/Coverage Transfer 001 - smogtours-gen2ou-932818 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-932818`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-932818.log`

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
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/hidden_role_voluntary_entry.md`
- `reviews/low_cloyster_ghost_guard_review_001_2026-05-15.md`
- `reviews/snorlax_forretress_counter_handoff_review_001_2026-05-15.md`
- `workspace/quick_tests/early_cycle_counter_handoff_probe_001_2026-05-15.md`
- `workspace/quick_tests/low_support_four_way_probe_001_2026-05-15.md`

Current web sources used only after stopping and scoring, before any further
fresh replay:

- Smogon Forums, GSC OU Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, GSC OU Gengar:
  `https://www.smogon.com/forums/threads/gengar-wip.3703761/`
- Smogon Forums, GSC OU Viability Rankings Mk. 4:
  `https://www.smogon.com/forums/threads/gsc-ou-viability-rankings-mk-4.3633233/`
- Smogon Forums, GSC OU Threat List:
  `https://www.smogon.com/forums/threads/gsc-ou-threat-list-qc-2-2-gp-2-2.3477110/`

## Contamination Control

- Local `rg` found no prior `smogtours-gen2ou-932818` artifact before this run.
- The log was saved locally at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-932818.log`.
- Prompts used
  `python tools/pokemon_mastery/replay_turn_pause.py ... prompt --turn N`.
- Reveals used
  `python tools/pokemon_mastery/replay_turn_pause.py ... reveal --turn N`.
- Fresh reveals stopped at turn 7 after repeated receiver-action misses:
  low-support Ghost guard on turn 2, Snorlax handoff/setup timing on turns 5-6,
  and coverage into the CurseLax receiver on turn 7.

## Score Summary

Decisions: 13 scored, 1 unscored.

Top-match: 4/13.
Acceptable-match: 9/13.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.
Positive-selection: 8/13.
Route-converting move chosen: 6/13.
Branch-punish chosen: 5/12.
Earliest meaningful error: turn 2 p1.

Result: not progress. The severe, hidden-info, state, and mechanics gates stayed
clean, but this was another early-stop packet with low top-match and weak
route-conversion. Acceptable-match was near the gate only because several
answers named the right broad branch class too low; the top moves were still
too safe or generic when a receiver-punish move existed.

## Frozen Answer Log

Candidates are ranked in order. Tags: `P` positive-selection, `R`
route-converting, `B` branch-punish.

| Turn | Side | Frozen top three | Actual | Grade | Tags | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Spikes; Toxic; Surf/Explosion high-risk | Spikes | top | P/R | Correct first support job. |
| 1 | p2 | Double-Edge/Body Slam pressure; Lovely Kiss if available; switch owner | Double-Edge | top | P/R | Correct active pressure into Cloyster. |
| 2 | p1 | Toxic; switch pressure owner; Surf/Explosion high-risk with Ghost named | Explosion | miss | - | Status before leaving was too generic once boom/guard branches were live. |
| 2 | p2 | Double-Edge; Gengar/boom guard; Rest or switch owner | Gengar | miss | - | Named the guard but failed to obey it as the top branch. |
| 3 | p1 | Thunder; switch absorber; Roar/pressure if available | Thunder | top | P/R | Correct pressure into the Gengar/Snorlax route. |
| 3 | p2 | Explosion or utility; Snorlax owner; Hypnosis/status | Snorlax | acceptable | P/B | The owner handoff was ranked, but utility into Raikou was over-ranked. |
| 4 | p1 | Thunder; Roar if available; switch only if forced | Thunder | top | P/R | Correctly kept pressure on the Rest threshold. |
| 4 | p2 | coverage attack; Rest; Double-Edge or switch | Surf | acceptable coverage class | P | Correct class, but exact coverage was not public before reveal. |
| 5 | p1 | Thunder; Roar if available; Snorlax only if setup-owner route needed | Snorlax | miss | - | Under-ranked the Snorlax handoff into a low/paralyzed RestLax board. |
| 5 | p2 | unscored: full paralysis hid the chosen move | full paralysis | unscored | - | No logged chosen move. |
| 6 | p1 | Double-Edge/Body Slam; Curse; coverage if available | Curse | acceptable | P | Setup into forced Rest was live and should have been priced higher. |
| 6 | p2 | Rest; Gengar/switch guard; Surf/Double-Edge | Rest | top | P/R | Correct recovery route. |
| 7 | p1 | Curse; attack if available; pressure handoff | Earthquake | miss | - | Missed coverage into the receiver after Curse showed the route. |
| 7 | p2 | switch revealed Gengar/owner; Sleep Talk if available; stay asleep | Cloyster | acceptable by owner class | P/B | Correct to leave sleeping Snorlax, but the better owner class was physical wall/boom pressure, not just Gengar. |

## Main Errors

Turn 2:
After Cloyster set Spikes, both sides had to solve cash-out and guard together.
I named Explosion and Gengar but did not rank the guard high enough for p2, and
my p1 top was a status script that did not improve through the actual guard.

Turns 5-6:
I was slow to move from "Raikou keeps pressing" to "Snorlax owns the low,
paralyzed RestLax board." Curse was a live conversion action once p1 Snorlax
entered, not just a passive setup move.

Turn 7:
This is the central new miss. Once p1 Snorlax revealed Curse, the next question
was not only "attack the sleeping Snorlax or Curse again." The receiver map had
to include Cloyster, Gengar, Skarmory/phazer, and Rock/Steel owners. If
Earthquake is revealed or side-known, it is the branch-punish into several of
those receivers. In spectator-public mode before reveal, Earthquake should be
treated as a strong-prior CurseLax coverage branch with a fallback, not as a
possible-only fact and not as an ignored option.

## Reusable Lesson

After Snorlax reveals Curse, solve the receiver before choosing another setup
turn:

1. Name the expected receiver or sleep-cycle action: stay asleep, Gengar,
   Cloyster, Skarmory/phazer, Rock/Steel, or special pressure owner.
2. If coverage is revealed or side-known, rank the coverage that hits that
   receiver before generic STAB or another Curse.
3. If coverage is only a strong prior, write the fallback: setup or Rest if the
   coverage is absent; coverage if the side-known set has it.
4. Do not treat unseen Earthquake as a fact in spectator-public mode, but do
   not erase it from the branch map after Curse has made the set family clear.
