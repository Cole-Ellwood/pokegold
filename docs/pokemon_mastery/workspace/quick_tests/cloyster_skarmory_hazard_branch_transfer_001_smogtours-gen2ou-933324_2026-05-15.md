# Cloyster/Skarmory Hazard Branch Transfer 001 - smogtours-gen2ou-933324 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933324`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933324.log`

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
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/support_handoff_after_job.md`
- `reviews/hazard_ownership_review_001_gen2ou-2544443857_2026-05-14.md`
- `reviews/tempo_coverage_sack_review_001_2026-05-15.md`
- `reviews/spinner_side_recover_review_001_2026-05-15.md`

Current web sources used only after scoring, before any further replay:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon, GSC OU Speed Tiers:
  `https://www.smogon.com/gs/articles/gsc_speedtiers`
- Smogon, Gold/Silver OU Metagame Primer:
  `https://www.smogon.com/resources/competitive/gs/gs_ou_primer`

## Contamination Control

- Local `rg` found no prior `smogtours-gen2ou-933324` use before selection.
- The log was saved locally at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-933324.log`.
- Prompts used
  `python tools/pokemon_mastery/replay_turn_pause.py ... prompt --turn N`.
- Reveals used
  `python tools/pokemon_mastery/replay_turn_pause.py ... reveal --turn N`.
- Fresh reveals stopped at turn 7 after repeated branch-cycle misses in the
  Steelix, Cloyster, and Skarmory hazard sequence.

## Score Summary

Decisions: 14 scored, 0 unscored.

Top-match: 8/14.
Acceptable-match: 11/14.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.
Positive-selection: 13/14.
Route-converting move chosen: 12/14.
Branch-punish chosen: 9/13.
Earliest top-match miss: turn 1 p2.
Earliest meaningful route error: turn 5 p1.

Result: not progress. The sample is an early-stop packet, not a full 30-50
decision proof run. Severe, hidden-info, state, and mechanics gates held, and
acceptable stayed above gate, but the run stopped because I repeated the same
hazard-branch failure: naming a switch or support cycle, then ranking a safe
field-job move above the action that converted the named next board.

## Frozen Answer Log

Candidates are ranked in order. Tags: `P` positive-selection, `R`
route-converting, `B` branch-punish.

| Turn | Side | Frozen top three | Actual | Grade | Tags | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Sleep Powder; Giga Drain/Psychic; switch if Ice pressure dominates | Sleep Powder | top | P/R | Correct sleep attempt; miss variance did not change the frozen choice. |
| 1 | p2 | Spikes; Ice Beam; switch sleep absorber | Ice Beam | acceptable | P/R | Spikes was defensible, but Ice Beam was the sharper active punish into Exeggutor. |
| 2 | p1 | Electric special-pressure owner; Snorlax/special sponge; high-risk Sleep Powder | Zapdos | top by class | P/R/B | Correct preservation and pressure handoff after Ice Beam. |
| 2 | p2 | Spikes; Ice Beam; preserve Cloyster | Spikes | top | P/R/B | Correctly punished the forced switch with the layer. |
| 3 | p1 | Thunder; Thunder Wave only if switch target needs status; preserve Zapdos | Thunder | top | P/R | Correct active pressure into Cloyster and its receiver. |
| 3 | p2 | Electric check such as Raikou; Snorlax/special wall; preserve Cloyster | Raikou | top by class | P/R/B | Correct receiver class, with exact hidden teammate scored by class. |
| 4 | p1 | Ground/Electric answer such as Steelix; Snorlax; stay only if coverage route exists | Steelix | top by class | P/R/B | Correct Thunder immunity handoff. |
| 4 | p2 | Roar if present with Spikes; Thunder fallback; Rest only if timer matters | Thunder | acceptable | P/R/B | I over-ranked strong-prior Roar, but kept Thunder as the fallback active-pressure line. |
| 5 | p1 | Earthquake; Roar/phaze; preserve Steelix | Cloyster | miss | - | Missed the counter-handoff to Cloyster as the Skarmory branch appeared. |
| 5 | p2 | Ground-immune physical owner such as Skarmory; bulky Water/Cloyster; stay only on read | Skarmory | top by class | P/R/B | Correctly left Raikou and moved to the Earthquake-immune owner. |
| 6 | p1 | Rapid Spin; Spikes; Surf/Toxic pressure | Spikes | acceptable | P/R | Hazard job ordering was defensible, but actual prioritized setting the missing layer before clearing. |
| 6 | p2 | Toxic; switch Electric pressure; Whirlwind | Toxic | top | P/R/B | Correctly put the opposing Cloyster on a timer. |
| 7 | p1 | Rapid Spin; Surf; switch/preserve | Surf | miss | P/R | Over-ranked Spin after Toxic and missed Surf into the opposing Cloyster hazard branch. |
| 7 | p2 | Raikou/Electric pressure; Whirlwind; stay if Spin must be denied by tempo | Cloyster | miss | P/R | Missed the opposing Cloyster as the immediate hazard-cycle owner. |

## Main Errors

Turn 5 p1:
I named that Raikou was leaving but still chose Earthquake. The actual line
double-switched Cloyster into Skarmory, converting the next board instead of
hitting the empty active matchup.

Turn 7 p1:
I treated Rapid Spin as the default once Cloyster was poisoned and both sides
had Spikes. The actual Surf punished p2's Cloyster entering the hazard cycle.
The lesson is not "never Spin"; it is "before Spin, name the setter or pressure
owner that enters, then rank the move that beats that owner."

Turn 7 p2:
I named generic Electric pressure instead of the opposing Cloyster mirror. In a
Cloyster/Skarmory cycle, the next owner may be another Cloyster even though it
does not block Spin, because it preserves Skarmory, pressures the spinner, and
keeps Surf/Toxic/Explosion branches live.

## Reusable Lesson

In a GSC hazard cycle, the support job is only the first question. Before
choosing Spikes or Rapid Spin, name:

1. whose side is taxed by Spikes;
2. whether the missing layer can be set now;
3. whether the opponent's next owner is their setter, spinner, flyer, Electric,
   Ghost, or passive phazer;
4. which move beats that owner: Surf, Toxic, Icy Wind, Explosion, counter-handoff,
   Spikes, or Spin.

Rapid Spin is positive when it stabilizes the entry map. It is not top by
default if Surf or a counter-handoff converts the opposing setter/pressure
branch first.
