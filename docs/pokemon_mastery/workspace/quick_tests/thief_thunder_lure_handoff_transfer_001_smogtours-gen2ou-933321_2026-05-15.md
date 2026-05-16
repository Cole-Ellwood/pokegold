# Thief/Thunder Lure Handoff Transfer 001 - smogtours-gen2ou-933321 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933321`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933321.log`

Search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&server=smogtours&page=3`

Mode: spectator-public no-Team-Preview turn pause. Smogtours replay, selected
from current metadata and turn count only. I did not inspect move content or
future turns before freezing answers.

Contamination control:

- Local `rg` found no prior `smogtours-gen2ou-933321` use before selection.
- The log was saved locally at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-933321.log`.
- Prompts used
  `python tools/pokemon_mastery/replay_turn_pause.py ... prompt --turn N`.
- Reveals used
  `python tools/pokemon_mastery/replay_turn_pause.py ... reveal --turn N`.
- Fresh reveals stopped at turn 5 after repeated item/lure package and
  counter-handoff misses.
- No later replay turns were inspected after stopping.

Players: p1 `tylerkehne`, p2 `exguardian`.

## Score Summary

Decisions: 10 scored, 0 unscored.

Top-match: 4/10.
Acceptable-match: 7/10.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.
Positive-selection: 7/10.
Route-converting move chosen: 5/10.
Branch-punish chosen: 4/8.
Earliest meaningful error: turn 1.

Result: not progress. Severe, hidden-info, state, and mechanics gates stayed
clean and acceptable was at the nominal threshold, but top-match, route
conversion, and branch-punish obedience were weak. The repeated error was
missing route-improving package actions after public clues: `Thief` over
generic sleep on turn 1, Snorlax handoff after the item job on turn 2, and the
Steelix/Cloyster counter-handoff after `Thunder` revealed on turn 5.

## Frozen Answer Log

Candidates are ranked in order. Tags: `P` positive-selection, `R`
route-converting, `B` branch-punish.

| Turn | Side | Frozen top three | Actual | Grade | Tags | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Lovely Kiss; Earthquake; coverage or switch punish | Thief | miss | - | Repeated old miss: Nidoking can use Thief before sleep when the bulky/Electric receiver route loses Leftovers value. |
| 1 | p2 | Switch to sleep/Ground answer class; Rock Slide or attack if staying; coverage/status if side-known | Zapdos | top by class | P/R/B | Correct to leave Tyranitar; exact Zapdos was hidden but the class was right. |
| 2 | p1 | Lovely Kiss; Ice/Thunder coverage if side-known; keep Nidoking in unless coverage risk flips | Snorlax | miss | - | After Thief did its job, the route was handoff to the Zapdos coverage answer, not another generic active attempt. |
| 2 | p2 | Hidden Power coverage into Nidoking; switch to sleep absorber if lacking coverage; reject Thunder into Ground immunity | Hidden Power | top | P/R/B | Correct strong-prior coverage with fallback discipline. |
| 3 | p1 | Double-Edge or Body Slam pressure; Curse into receiver; set-specific sleep/coverage | Double-Edge | top | P/R | Correct active pressure after Snorlax caught Zapdos coverage. |
| 3 | p2 | Tyranitar/physical-answer handoff; Thunder pressure; phaze if revealed or side-known | Cloyster | acceptable | P/R/B | Correct receiver class, exact Spiker missed. |
| 4 | p1 | Double-Edge active damage; preservation if Explosion risk dominates; setup only if receiver cannot reset | Thunder | acceptable | P | Same route class, but hidden Thunder was the sharper Cloyster lure. No hidden-info error because it was not public before this turn. |
| 4 | p2 | Spikes; Explosion cash-out; Toxic or Surf | Spikes | top | P/R | Correct first support job. |
| 5 | p1 | Thunder; Double-Edge if accuracy damage matters; preservation if Explosion branch dominates | Cloyster | miss | - | Once Thunder was public, the next question was the Steelix/Golem-style absorber and our counter-handoff, not repeat Thunder into the active. |
| 5 | p2 | Explosion; Toxic/Surf; switch to Normal/Electric absorber | Steelix | acceptable | P/R/B | The absorber class was present but under-ranked. Cloyster's Spikes job was done and Steelix preserved it while blocking the lure. |

## Reusable Lessons

- Nidoking lead is not sleep-only. When it faces or draws an obvious bulky
  receiver, `Thief` can be the first route move because item denial changes the
  later Spikes, sleep-turn, and damage clocks.
- After item removal lands, ask whether the item remover's current job is
  complete. If the receiver can now fire coverage, the next positive move may
  be the handoff, not a second utility attempt.
- Snorlax `Double-Edge` plus `Thunder` is a Cloyster-lure package. Once
  `Thunder` is public, expect the defender to price Steelix, Golem, Tyranitar,
  or another Normal/Electric absorber before letting Cloyster take another hit.
- The second lure turn needs a receiver ledger: active target, absorber, our
  owner into the absorber, and fallback if the active stays. Here the replay
  used Steelix into Snorlax and Cloyster into Steelix.
- Do not turn "Cloyster has delivered Spikes" into auto-Explosion. If a hard
  answer can enter and preserve Cloyster's future Spin/Explosion/checking job,
  the switch can convert more than cash-out.
- No-Team-Preview discipline still applies. The exact hidden Cloyster or
  Steelix should be recommended by class until revealed, with a fallback if the
  owner is unavailable.
