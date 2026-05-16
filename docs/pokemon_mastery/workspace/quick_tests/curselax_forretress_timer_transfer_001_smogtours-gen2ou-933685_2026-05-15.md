# CurseLax/Forretress Timer Transfer 001 - smogtours-gen2ou-933685 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933685`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933685.log`

Search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&page=2`

Mode: spectator-public no-Team-Preview turn pause. Smogtours replay, selected
from current metadata and turn count only. I did not inspect move content or
future turns before freezing answers.

Contamination control:

- Local `rg` found no prior `smogtours-gen2ou-933685` use before selection.
- The log was saved locally at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-933685.log`.
- Prompts used
  `python tools/pokemon_mastery/replay_turn_pause.py ... prompt --turn N`.
- Reveals used
  `python tools/pokemon_mastery/replay_turn_pause.py ... reveal --turn N`.
- Fresh reveals stopped at turn 23 after the first clearly imperfect
  positive-selection miss. Web and docs study happened only after scoring.

## Score Summary

Decisions: 45 scored, 1 unscored.
Unscored:

- turn 9 p2, because full paralysis hid the selected move.

Top-match: 16/45.
Acceptable-match: 31/45.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 1.
Mechanics errors: 0.
Positive-selection: 36/45.
Route-converting move chosen: 33/45.
Branch-punish chosen: 15/36.
Earliest meaningful error: turn 1.

Result: not progress. Severe/state/mechanics gates stayed clean and
positive-selection stayed high, but top-match and acceptable-match fell below
gate, branch obedience fell hard, and hidden-info anchoring repeated. The run
shows better willingness to choose active pressure in some places, but not
better unseen move choice overall.

## Frozen Answer Log

Candidates are ranked in order. Tags: `P` positive-selection, `R`
route-converting, `B` branch-punish.

| Turn | Side | Frozen top three | Actual | Grade | Tags | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Thunder; sleep-absorber switch; Hidden Power/Drill Peck | Hidden Power | acceptable | P/R | Active pressure was right; exact attack and Raikou branch were only third. |
| 1 | p2 | Sleep Powder; Stun Spore; Psychic/Explosion | Raikou | miss | P/R | Exeggutor was not forced to sleep; Raikou was the immediate Electric receiver. |
| 2 | p1 | switch special wall/Snorlax class; switch Ground; attack | Raikou | top | P/R/B | Correct special-wall class. |
| 2 | p2 | Thunder; Roar; Rest | Thunder | top | P/R | Correct pressure. |
| 3 | p1 | Thunder; Roar; switch Snorlax/Ground | Thunder | top | P/R | Correct mirror pressure. |
| 3 | p2 | Thunder; Roar; switch Exeggutor/Snorlax | Thunder | top | P/R | Correct mirror pressure. |
| 4 | p1 | Rest if available; switch Snorlax if no Rest; Thunder | Thunder | acceptable | - | I over-preserved; Thunder punished the Snorlax branch. |
| 4 | p2 | Thunder; switch Snorlax; Rest | Snorlax | acceptable | P/R | Switch was ranked, but not top. |
| 5 | p1 | Thunder; Roar; switch Normal-resist/Ghost | Cloyster | miss | - | I did not name the sleep absorber before Snorlax used Lovely Kiss. |
| 5 | p2 | Rest; Double-Edge; Curse | Lovely Kiss | miss | - | Snorlax set ambiguity: Lovely Kiss had to be priced. |
| 6 | p1 | Spikes; Toxic; Explosion high-risk | Spikes | top | P/R | Correct field work. |
| 6 | p2 | switch Electric/Raikou; Rest; Lovely Kiss again | Lovely Kiss | acceptable | P/R/B | Lovely Kiss was ranked but too low. |
| 7 | p1 | switch Normal-resist/Ghost route; stay/Sleep Talk if present; preserve | Zapdos | acceptable | P/R | Correct to leave Cloyster asleep, exact owner missed. |
| 7 | p2 | Rest; switch spinner/Electric; Double-Edge | Curse | miss | - | Setup into a passive switch was the converter. |
| 8 | p1 | Whirlwind if available, fallback Thunder; switch Normal-resist/Golem/Ghost | Golem | acceptable | P/R/B | Correct route class, wrong top. |
| 8 | p2 | Rest; Double-Edge; Curse | Double-Edge | acceptable | P/R | Damage punished the Golem handoff. |
| 9 | p1 | Roar; Explosion if no Roar; Earthquake | Roar | top | P/R/B | Correct phaze-loop response to boosted Snorlax. |
| 9 | p2 | unscored | full paralysis | unscored | - | Chosen move hidden. |
| 10 | p1 | Earthquake; Roar; Explosion | Earthquake | top | P/R/B | Correct active pressure into Forretress. |
| 10 | p2 | Rapid Spin; Spikes; Explosion/switch | Spikes | acceptable | P/R | I underweighted setting the missing layer before clearing. |
| 11 | p1 | Rapid Spin if available; Earthquake; Roar | Gengar | miss | P/R | I missed the spinblock/status-immune handoff. |
| 11 | p2 | Rapid Spin; Explosion; switch Ghost/Skarmory | Toxic | miss | P | Forretress had to punish the spinblock branch, not autopilot Spin. |
| 12 | p1 | Hypnosis; Thunder; Fire Punch high-risk/Explosion | Dynamic Punch | miss | P | Dynamic Punch utility into the receiver map was missed. |
| 12 | p2 | switch Raikou/Snorlax special wall; Explosion; Toxic | Raikou | top | P/R/B | Correct receiver class. |
| 13 | p1 | switch Golem/Ground; Dynamic Punch; Explosion high-risk | Raikou | miss | P/R/B | I found a switch but not the double-switch owner. |
| 13 | p2 | Thunder; Rest; Roar/switch Snorlax | Golem | miss | P | I missed the Ground receiver branch. |
| 14 | p1 | switch Gengar; switch Zapdos; switch Snorlax | Raikou stayed and fainted | acceptable | P/R/B | The replay's action was bad; our switch avoided the Earthquake loss. |
| 14 | p2 | Rapid Spin; Earthquake; Rock Slide | Earthquake | acceptable | P/R | Earthquake was ranked but should have been top into Raikou. |
| 15 | p1 | Hidden Power; Thunder; Rest | Snorlax | miss | P/R | Missed the Snorlax handoff into Rapid Spin. |
| 15 | p2 | Rapid Spin; Rock Slide if available; switch Raikou/Snorlax | Rapid Spin | top | P/R | Correct hazard clear. |
| 16 | p1 | switch Gengar; Earthquake if revealed; Double-Edge/Curse | Zapdos | acceptable | P/R/B | Correct EQ-immune class, exact owner missed. |
| 16 | p2 | Earthquake; Roar/Explosion; switch | Earthquake | top | P/R | Correct active punish. |
| 17 | p1 | Hidden Power; Thunder; switch Snorlax | Thunder | acceptable | P/R | Thunder was the better switch-punish, but ranked second. |
| 17 | p2 | switch Raikou/Snorlax; Explosion high-risk; Rock Slide if available | Snorlax | top | P/R/B | Correct receiver class. |
| 18 | p1 | Thunder; switch Golem/Gengar; Hidden Power | Thunder | top | P/R/B | Correct Electric receiver punish. |
| 18 | p2 | Rest; Double-Edge; switch Golem/Raikou | Raikou | acceptable | P/R | Raikou was ranked but too low. |
| 19 | p1 | switch Snorlax; Thunder; Hidden Power | Snorlax | top | P/R/B | Correct special wall handoff. |
| 19 | p2 | Rest; Thunder; switch Golem | Thunder | acceptable | P/R | Thunder was ranked but too low. |
| 20 | p1 | Rest if available, fallback Double-Edge; switch Golem | Curse | miss | - | I missed setup into the Forretress receiver. |
| 20 | p2 | Rest; Thunder; switch Golem/Snorlax | Forretress | miss | - | Missed the Normal-resist support receiver. |
| 21 | p1 | Rest if available; coverage high-risk; switch Gengar | Curse | miss | - | I over-defended instead of continuing setup while Forretress could not punish enough yet. |
| 21 | p2 | Toxic; Explosion high-risk; switch Golem/Skarmory | Toxic | top | P/R/B | Correct to put boosted Snorlax on a timer. |
| 22 | p1 | Curse; Rest; attack/coverage cash-out | Curse | top | P/R/B | Correct to keep boosting through first Toxic tick. |
| 22 | p2 | Toxic; Explosion; defensive switch | Toxic | top | P/R/B | Correct status retry. |
| 23 | p1 | Rest if available; attack/cash-out if no Rest; Curse | Double-Edge | acceptable | - | Preservation lost to route conversion; +3 Double-Edge was the timer cash-out. |
| 23 | p2 | Explosion strong-prior; Golem/Snorlax handoff; Toxic/fallback | Hidden Power | miss | hidden | I let unrevealed Explosion anchor the move instead of tiering Forretress's coverage/utility pool. |

## Reusable Lessons

- A boosted Snorlax on a poison clock must ask what damage converts now before
  defaulting to Rest. Rest is a strong prior on CurseLax, but it is not a
  command to surrender a +3 attack window.
- Double-Edge remains the standard CurseLax cash-out into even Normal resists
  after boosts. If it chunks the support receiver and forces a new response
  before Toxic/recoil steals the clock, it can outrank preservation.
- Forretress can have Spikes, Rapid Spin, Toxic, Explosion, Hidden Power, Giga
  Drain, Rest, or coverage. Explosion is real, but it is not guaranteed just
  because Forretress faces a boosted threat. Mark it as strong-prior or
  high-risk unless the sweep emergency, target, post-trade owner, and fallback
  are all explicit.
- After Forretress lands Toxic on CurseLax, its next job is not automatic. It
  may chip with coverage, switch to a phazer/resist, Spin or reset hazards, or
  use Explosion if the game state really requires the trade.
- The worst positive-selection miss in this packet was not a catastrophic
  blunder; it was choosing safe/generic preservation when the route wanted a
  converting attack.
