# Counter-Handoff Transfer 001 - smogtours-gen2ou-932564 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-932564`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-932564.log`

Search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&server=smogtours&page=4`

Mode: spectator-public no-Team-Preview turn pause. Smogtours replay, selected
from current metadata and turn count only. I did not inspect move content or
future turns before freezing answers.

Context condition:

- Pre-freeze live docs: `active_context.md`, `live_core.md`,
  `replay_turn_pause_protocol.md`, and the tiny `heuristic_core/*.md` cards.
- Test focus from active context: before locking each answer, name the likely
  counter-handoff to my own obvious handoff.
- No scored quick tests, future turns, raw answer labels, long policy cards, or
  external research returns were opened after this replay was selected and
  before answers were frozen.

Contamination control:

- Local `rg` found no prior `smogtours-gen2ou-932564` use before selection.
- The log was saved locally at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-932564.log`.
- Turn count was checked mechanically without printing move content.
- Prompts used
  `python tools/pokemon_mastery/replay_turn_pause.py ... prompt --turn N`.
- Reveals used
  `python tools/pokemon_mastery/replay_turn_pause.py ... reveal --turn N`.
- Fresh reveals stopped at turn 15 for 30 side decisions. No turn 16 or later
  move content was inspected.
- Manual state note: p2 Forretress was under Whirlpool partial trapping before
  turn 15; the helper prompt did not display it, so it was carried manually.

Players: p1 `Bohrier`, p2 `Kanha Greninja`.

## Score Summary

Decisions: 30 scored, 0 unscored.

Top-match: 8/30.
Acceptable-match: 22/30.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.
Positive-selection: 24/30.
Route-converting move chosen: 18/30.
Branch-punish chosen: 13/23.
Earliest meaningful error: turn 1.

Result: not progress. The flexible-card protocol and counter-handoff sentence
did not raise top-match; exact prediction fell well below gate. The useful
transfer was narrow: Lapras voluntary entry was correctly read as
Whirlpool/Perish trapping, and the Forretress missing-layer decision on turn 7
was correct. The repeated misses were support-package identities: Dragonite
Reflect, Umbreon Charm/Pursuit, Skarmory Curse, Forretress as a counter-handoff
after Charm, and Raikou/Lapras hidden owner routing.

## Frozen Answer Log

Candidates are ranked in order. Tags: `P` positive-selection, `R`
route-converting, `B` branch-punish.

| Turn | Side | Frozen top three | Actual | Grade | Tags | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Fire Blast/coverage if present, with Body Slam fallback; Double-Edge/Body Slam pressure; Curse | Curse | acceptable | P | Hidden coverage was priced with fallback, but setup was the actual route. |
| 1 | p2 | Switch to Snorlax/Fire-status absorber; Spikes; Toxic/status | Spikes | acceptable | P/R | Forretress accepted the Fire/status risk and took the missing layer. |
| 2 | p1 | Fire Blast/coverage if present; Double-Edge/Body Slam pressure; Curse if Forretress lacks punish | Curse | acceptable | P | Setup stayed acceptable but still over-worried about immediate Forretress punish. |
| 2 | p2 | Toxic; Explosion if boosted Lax snowballs; switch Normal-resist/phazer | Skarmory | acceptable | P/B | Correct receiver class was ranked too low. |
| 3 | p1 | Switch to Skarmory breaker; Fire Blast if present; Body Slam/Double-Edge pressure | Double-Edge | acceptable | P/R | Damage into Skarmory was more converting than I credited. |
| 3 | p2 | Whirlwind; Toxic/Drill Peck; switch only if Fire coverage is public | Whirlwind | top | P/R/B | Correct phaze conversion. |
| 4 | p1 | Thunder/Fire coverage; switch Electric/special owner; setup/support | Reflect | miss | - | Missed Dragonite as a screen support package after forced entry. |
| 4 | p2 | Switch special wall; Whirlwind again; Toxic/Drill Peck | Blissey | top | P/B | Correct special-wall counter-handoff. |
| 5 | p1 | Snorlax handoff; coverage/status if side-known; support/reset | Snorlax | top | P/R/B | Correct screen-to-physical handoff. |
| 5 | p2 | Ice Beam/active hit if present; Toxic/status; switch Skarmory | Toxic | acceptable | P/R | Correct timer branch, not top. |
| 6 | p1 | Double-Edge pressure; Curse; switch if Toxic timer dominates | Forretress | miss | - | Missed Forretress as the hazard owner after Snorlax was poisoned. |
| 6 | p2 | Switch Skarmory; Softboiled/Heal Bell if side-known; status/support | Skarmory | top | P/B | Correct physical-wall handoff. |
| 7 | p1 | Spikes before Spin; Rapid Spin; Toxic/coverage/Explosion branch | Spikes | top | P/R | Correct missing-layer priority. |
| 7 | p2 | Switch Zapdos/Fire/special pressure; Whirlwind; spinner/hazard owner | Starmie | acceptable | P/B | Correct broad counter-handoff, exact Starmie under-specified. |
| 8 | p1 | Hidden Power Bug/coverage if present; Rapid Spin; Toxic | Toxic | acceptable | P/R | Toxic was a valid spinner-control converter but ranked too low. |
| 8 | p2 | Rapid Spin; Surf; switch preserve Starmie | Surf | acceptable | P/R | Surf pressure before Spin was valid tempo. |
| 9 | p1 | Toxic again; Rapid Spin; switch Electric/Ghost/Pursuit owner | Umbreon | acceptable | P/B | Pursuit/support owner was ranked but too low. |
| 9 | p2 | Rapid Spin; Surf; switch to preserve Starmie from Toxic | Skarmory | acceptable | P/B | Preservation switch was live, exact Skarmory under-ranked. |
| 10 | p1 | Charm/check setup; Forretress handoff; Dragonite/Reflect reset | Charm | acceptable | P/R | Correct move existed, but I did not make support identity central soon enough. |
| 10 | p2 | Whirlwind; switch Forretress/hazard owner; Drill Peck | Curse | miss | - | Missed Skarmory Curse as a package reveal, not only phaze. |
| 11 | p1 | Charm again; Forretress handoff; Dragonite/Reflect reset | Pursuit | miss | - | Missed Pursuit as the branch punish once a switch was likely. |
| 11 | p2 | Whirlwind; Curse; Drill Peck | Forretress | miss | - | Missed Forretress as the counter-handoff after Charm/Pursuit pressure. |
| 12 | p1 | Forretress mirror/spin owner; Dragonite coverage/support; Snorlax pressure | Raikou | miss | - | Missed hidden Electric owner; no hidden-info error because it was not public. |
| 12 | p2 | Rapid Spin; switch Skarmory/Blissey if fearing pressure; support reset | Skarmory | miss | - | Counter-handoff map stayed one layer short. |
| 13 | p1 | Roar if available; Thunder; double to Snorlax/Umbreon into Blissey | Lapras | miss | - | Missed Lapras as the Blissey-targeted package owner. |
| 13 | p2 | Blissey; Forretress/Starmie preserve; Skarmory stay only if needed | Blissey | top | P/B | Correct special-wall owner. |
| 14 | p1 | Whirlpool trap; Perish Song; Sing/Surf pressure | Whirlpool | top | P/R/B | Correct voluntary-entry trap package. |
| 14 | p2 | Toxic; switch Starmie/Forretress before trap; Softboiled/Heal Bell | Forretress | acceptable | P/B | Correct switch-before-trap branch was ranked. |
| 15 | p1 | Perish Song; Surf/coverage; switch only if Spin escape dominates | Perish Song | top | P/R | Correct trap conversion. |
| 15 | p2 | Rapid Spin if it escapes trap; Explosion; Toxic | Toxic | acceptable | P | Toxic was ranked behind escape/cash-out. |

## Reusable Lessons

- The Lapras lesson transferred: voluntary Lapras into Blissey was correctly
  read as a Whirlpool/Perish route rather than generic Water damage.
- The support-package lesson did not transfer. Reflect, Charm, Pursuit, and
  Skarmory Curse all changed the route map, but I treated them as side notes
  instead of role reveals.
- Counter-handoff writing helped only when the owner was already familiar
  (Blissey into Raikou, Starmie into Forretress). It failed when the next owner
  was hidden or support-shaped: Raikou, Lapras, Umbreon, Forretress.
- Next correction is not more archive loading. The tiny card needs to remind me
  that screens, Charm, Pursuit, and support Curse reclassify a Pokemon's job.
