# RestTalk/SubStarmie Phaze Transfer 001 - smogtours-gen2ou-933823 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933823`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933823.log`

Search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&page=2`

Mode: spectator-public no-Team-Preview turn pause. Smogtours replay, selected
from current metadata and turn count only. I did not inspect move content or
future turns before freezing answers.

Contamination control:

- Local `rg` found no prior `smogtours-gen2ou-933823` use before selection.
- The log was saved locally at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-933823.log`.
- Prompts used
  `python tools/pokemon_mastery/replay_turn_pause.py ... prompt --turn N`.
- Reveals used
  `python tools/pokemon_mastery/replay_turn_pause.py ... reveal --turn N`.
- Web and docs study happened only after turn 25 was scored.

## Score Summary

Decisions: 48 scored, 2 unscored.
Unscored:

- turn 3 p2, because full paralysis hid the selected move.
- turn 25 p1, because sleep prevented action and the selected move was not
  logged.

Top-match: 20/48.
Acceptable-match: 39/48.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 1.
Mechanics errors: 0.
Positive-selection: 36/48.
Route-converting move chosen: 34/48.
Branch-punish chosen: 24/41.
Earliest meaningful error: turn 3.

Result: not progress. Severe/state/mechanics gates stayed clean and
acceptable stayed above gate, but top-match stayed below gate, positive and
route conversion dipped from the previous transfer, and a hidden-info
coverage-anchor error repeated.

## Frozen Answer Log

Candidates are ranked in order. Tags: `P` positive-selection, `R`
route-converting, `B` branch-punish.

| Turn | Side | Frozen top three | Actual | Grade | Tags | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Spore; Thunder Wave; Spikes | Thunder Wave | acceptable | P/R | Smeargle support is not sleep-only; early Electric paralysis can be the route. |
| 1 | p2 | Thunder; Hidden Power; switch status absorber | Hidden Power | acceptable | P/R | Active pressure was right; exact attack was not. |
| 2 | p1 | Spikes; Baton Pass/Agility; switch | Spikes | top | P/R | Correct field order after paralysis. |
| 2 | p2 | Hidden Power; Thunder; switch Normal/sleep absorber | Thunder | acceptable | P/R | Correct pressure class, wrong exact move. |
| 3 | p1 | switch Ground/Snorlax class; use last support; preserve sack | Destiny Bond | miss | - | Low Smeargle had a cash-out button; I preserved by habit. |
| 3 | p2 | unscored | full paralysis | unscored | - | Chosen move hidden. |
| 4 | p1 | Destiny Bond; switch Snorlax; switch Ground | Snorlax | acceptable | P/R | Preservation handoff beat repeating Destiny Bond. |
| 4 | p2 | switch Normal-resist/sleep absorber; Rest if chipped; attack | Rest | acceptable | P/B | Rest at full HP failed to cure paralysis; note the mechanics gate. |
| 5 | p1 | Double-Edge; Earthquake if revealed; Lovely Kiss if available | Double-Edge | top | P/R | Correct active pressure into expected resist. |
| 5 | p2 | switch Normal resist; switch Ghost; attack | Forretress | acceptable | P/R/B | Correct class but hidden exact owner. |
| 6 | p1 | Double-Edge; switch spinblocker; Fire coverage high-risk | Gengar | acceptable | - | I underweighted the support handoff to Gengar. |
| 6 | p2 | Spikes; Rapid Spin; switch Ghost answer | Spikes | top | P/R | Correct to set the missing layer before clearing. |
| 7 | p1 | Fire Punch high-risk; Hypnosis; Thunderbolt | Thunderbolt | miss | hidden | I let possible-only Fire coverage anchor the line. |
| 7 | p2 | switch Raikou; switch Snorlax; stay with support | Raikou | top | P/R/B | Correct special receiver into Gengar. |
| 8 | p1 | switch Ground/Steel; switch Snorlax; Thunderbolt | Steelix | acceptable | P/R/B | Correct class, hidden exact owner. |
| 8 | p2 | Thunder; Hidden Power; switch Forretress | Rest | miss | - | Missed that chipped Rest cures paralysis and resets Raikou. |
| 9 | p1 | Earthquake; Roar; Curse | Roar | miss | - | With Spikes up, Roar into the switch was the converter. |
| 9 | p2 | switch Skarmory/Water; stay to burn sleep; switch Forretress | Skarmory | top | P/R/B | Correct counter-pivot. |
| 10 | p1 | Roar; Earthquake; Curse | Roar | top | P/R/B | Correct phaze-loop commitment. |
| 10 | p2 | switch Skarmory; switch Water; stay asleep | Skarmory | top | P/R/B | Correct counter-pivot despite Roar punishment. |
| 11 | p1 | Earthquake; Roar; switch Snorlax | Roar | miss | - | I attacked the active Ghost instead of obeying the repeated switch loop. |
| 11 | p2 | switch Skarmory; Toxic; switch Forretress | Skarmory | top | P/R/B | Correct physical-wall branch. |
| 12 | p1 | Roar; Earthquake; Curse | Curse | acceptable | P/R | Curse converted when Forretress broke the Roar loop. |
| 12 | p2 | stay and Toxic; switch Forretress; switch Skarmory | Forretress | acceptable | P/B | Correct idea was breaking the loop; exact owner missed. |
| 13 | p1 | Earthquake; Roar; Curse | Earthquake | top | P/R/B | Correct active punish before Spin. |
| 13 | p2 | Rapid Spin; Explosion emergency; switch Skarmory | Rapid Spin | top | P/R/B | Correct hazard ownership and Spin window. |
| 14 | p1 | Earthquake; switch Zapdos; Explosion high-risk | Zapdos | acceptable | P/R | Earthquake would break Starmie's Sub, but Zapdos was the cleaner owner. |
| 14 | p2 | Surf; Substitute; Recover | Substitute | acceptable | P/R | Substitute was the pressure package, not a passive scout. |
| 15 | p1 | Thunder; Thunderbolt; switch Snorlax | Thunder | top | P/R/B | Correct pressure through Sub, but accuracy failed. |
| 15 | p2 | switch Raikou; Surf; Recover | Surf | miss | - | I retreated from a SubSurf route that was already converting. |
| 16 | p1 | Thunder; switch Snorlax; Rest | Thunder | top | P/R/B | Correct to keep forcing the Sub. |
| 16 | p2 | Surf; Recover; switch Raikou | Surf | top | P/R | Correct active pressure under the shield. |
| 17 | p1 | switch Snorlax; Thunder; Rest | Rest | acceptable | P/R/B | Rest preserved the Zapdos route better than a switch. |
| 17 | p2 | Surf; switch Raikou; Recover | Surf | top | P/R | Correct pressure. |
| 18 | p1 | switch Snorlax; Sleep Talk if present; switch Gengar | Sleep Talk | acceptable | P/R | After RestTalk reveal, staying becomes a real route. |
| 18 | p2 | Surf; switch Raikou; Recover | Surf | top | P/R | Correct. |
| 19 | p1 | Sleep Talk; switch Snorlax; switch Steelix | Sleep Talk | top | P/R/B | Correct after Sleep Talk was public. |
| 19 | p2 | Surf; switch Raikou; Recover | Raikou | miss | - | Missed the sleeping Electric receiver into Zapdos's Sleep Talk. |
| 20 | p1 | Thunder on wake; switch Snorlax; switch Steelix | Snorlax | acceptable | P/R | Waking pressure was defensible, but Snorlax caught Sleep Talk Thunder. |
| 20 | p2 | stay with Sleep Talk/burn sleep; switch Skarmory; switch Starmie | Sleep Talk | acceptable | P/R/B | Correct to treat revealed RestTalk Raikou as active. |
| 21 | p1 | Double-Edge; Earthquake; switch Zapdos | Earthquake | miss | - | After naming Misdreavus, Earthquake had to outrank STAB. |
| 21 | p2 | switch Misdreavus; switch Skarmory; Sleep Talk | Misdreavus | top | P/R/B | Correct Normal immunity branch. |
| 22 | p1 | switch sleeping Zapdos; Earthquake; switch Steelix | Earthquake | acceptable | P/R/B | Zapdos would blank Toxic, but replay cashed damage instead. |
| 22 | p2 | switch Skarmory; Toxic; Rest | Toxic | acceptable | - | Safe pivot missed the converting status. |
| 23 | p1 | Earthquake; switch Zapdos; Rest if revealed | Earthquake | top | P/R/B | Correct pressure into low Misdreavus. |
| 23 | p2 | switch Skarmory; Rest; Pain Split if available | Rest | acceptable | - | Rest reset was sharper than preservation by switch. |
| 24 | p1 | Earthquake; Rest; switch Zapdos | Rest | miss | - | Toxic Snorlax had to reset before the Skarmory pivot. |
| 24 | p2 | switch Skarmory; stay asleep; switch Starmie | Skarmory | top | P/R/B | Correct Rest-to-counter-pivot. |
| 25 | p1 | unscored | slept, no move logged | unscored | - | Chosen move hidden. |
| 25 | p2 | Whirlwind; Drill Peck; Curse | Whirlwind | top | P/R/B | Correct to convert p1-side Spikes with phazing. |

## Reusable Lessons

- Rest at full HP fails, so it does not cure paralysis or poison unless the
  user is actually below full HP and Rest succeeds.
- Once Sleep Talk is public, a sleeping Zapdos/Raikou/Snorlax can stay active;
  before the reveal, price it as a strong prior with a fallback, not a fact.
- Steelix with Spikes and Roar is not on autopilot. Roar is correct while the
  switch loop is stable; Curse is correct when the opponent's break is entering
  Forretress, Skarmory, or another piece that lets Steelix turn the loop into
  direct pressure.
- Substitute Starmie can be the converter even without immediate Spin. If it
  is behind a Substitute against Thunder, Surf can exploit misses and force
  Rest; switching out too early gives up the route.
- After a Ghost absorbs or baits Snorlax STAB and Earthquake is public, the
  revealed coverage must outrank generic Double-Edge.
