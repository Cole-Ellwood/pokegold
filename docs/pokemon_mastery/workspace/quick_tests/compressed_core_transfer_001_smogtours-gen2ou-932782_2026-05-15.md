# Compressed Core Transfer 001 - smogtours-gen2ou-932782 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-932782`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-932782.log`

Search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&server=smogtours&page=3`

Mode: spectator-public no-Team-Preview turn pause. Smogtours replay, selected
from current metadata and turn count only. I did not inspect move content or
future turns before freezing answers.

Context condition:

- This was the first replay packet after the mastery-doc compression.
- Pre-freeze context loaded: `active_context.md`, `live_core.md`,
  `replay_turn_pause_protocol.md`, `heuristic_core/branch_punish_ranking.md`,
  and `heuristic_core/rescore_after_reveal.md`.
- This is therefore a compressed-core-assisted packet, not a strict
  one-card-only packet.

Contamination control:

- Local `rg` found no prior `smogtours-gen2ou-932782` use before selection.
- The log was saved locally at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-932782.log`.
- Turn count was checked mechanically without printing move content.
- Prompts used
  `python tools/pokemon_mastery/replay_turn_pause.py ... prompt --turn N`.
- Reveals used
  `python tools/pokemon_mastery/replay_turn_pause.py ... reveal --turn N`.
- Fresh reveals stopped at turn 15 for exactly 30 side decisions. No turn 16 or
  later move content was inspected.

Players: p1 `isnialan`, p2 `Seanobiwan`.

## Score Summary

Decisions: 30 scored, 0 unscored.

Top-match: 17/30.
Acceptable-match: 27/30.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.
Positive-selection: 24/30.
Route-converting move chosen: 21/30.
Branch-punish chosen: 17/24.
Earliest meaningful error: turn 1.

Result: limited positive transfer, not mastery proof. The packet clears the
basic 30-decision replay gate and beats the recent fresh-transfer top-match
baseline, but it is one compressed-core-assisted run. Do not claim a trend until
another 2-3 fresh packets hold or improve top-match and branch-punish without
raising severe, hidden-info, state, or mechanics errors.

## Frozen Answer Log

Candidates are ranked in order. Tags: `P` positive-selection, `R`
route-converting, `B` branch-punish.

| Turn | Side | Frozen top three | Actual | Grade | Tags | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Sleep Powder; Stun Spore; revealed damage/item line only if route-specific | Thief | miss | P | Item-first utility still under-ranked versus generic lead sleep. |
| 1 | p2 | Switch to sleep absorber/Exeggutor answer; keep Snorlax only if absorber job is intended; active pressure if staying | Zapdos | top by class | P/R/B | Correct next-board owner, exact Zapdos hidden. |
| 2 | p1 | Sleep Powder; switch only if Thunder route is too dangerous; Stun Spore if switch branch dominates | Sleep Powder | top | P/R | Correct active status converter. |
| 2 | p2 | Thunder pressure; switch sleep absorber only if preserving Zapdos route; support move if side-known | Thunder | top | P/R | Correct active pressure. |
| 3 | p1 | Stun Spore into switch; Psychic; handoff if Sleep Talk is side-known | Psychic | acceptable | P | Psychic pressure was ranked; status into a sleeping active was overvalued. |
| 3 | p2 | Switch/preserve sleeping Zapdos; Sleep Talk if side-known; stay only to burn safe turn | Sleep Talk -> Rest | acceptable | P/R | Side-known RestTalk was right, but not public top before reveal. |
| 4 | p1 | Psychic; preserve Exeggutor only if Thunder roll changes route; cash-out only with named follow-up | Psychic | top | P/R | Correct pressure into revealed RestTalk. |
| 4 | p2 | Sleep Talk; switch only if preserving Zapdos beats pressure; stay asleep if safe | Sleep Talk -> Rest | top | P/R | Correct RestTalk loop. |
| 5 | p1 | Psychic; Explosion only if side-known and named follow-up; switch to Snorlax/special owner | Snorlax | acceptable | P/B | Correct route was preservation handoff, but it was under-ranked. |
| 5 | p2 | Sleep Talk; switch only if CurseLax entry is too costly; preserve Zapdos if low | Sleep Talk -> Hidden Power | top | P/R | Correct active RestTalk pressure. |
| 6 | p1 | Curse; Body Slam/Double-Edge if no setup; Rest/preserve only if Thunder clock demands | Curse | top | P/R | Correct setup into sleeping Electric/receiver branch. |
| 6 | p2 | Switch physical owner; Sleep Talk if staying; preserve Zapdos for later status sponge | Cloyster | top by class | P/R/B | Correct boosted-Lax receiver class. |
| 7 | p1 | Body Slam/Double-Edge pressure; switch only if Toxic/Explosion branch dominates; Curse if receiver cannot punish | Cloyster | miss | - | Missed exact spend/save: preserve Snorlax from Toxic/Explosion with Cloyster. |
| 7 | p2 | Explosion if it denies boosted Lax; Toxic; Spikes only after setup threat is stopped | Toxic | acceptable | P/B | Correct status punish was ranked below cash-out. |
| 8 | p1 | Spikes; Toxic/Surf; Explosion only with named follow-up | Spikes | top | P/R | Correct missing layer. |
| 8 | p2 | Spikes; Toxic/Surf; Explosion only with named follow-up | Spikes | top | P/R | Correct equalizing layer. |
| 9 | p1 | Toxic public fallback; Rapid Spin only if side-known; Surf/Explosion if it converts | Toxic | top | P | Correct public move, though Zapdos blanked it by switching in asleep. |
| 9 | p2 | Rapid Spin if side-known; Toxic/Surf; switch sleeping Zapdos as status absorber | Zapdos | acceptable | P/B | Good status-absorber re-entry, under-ranked. |
| 10 | p1 | Snorlax handoff; Explosion high-risk only if side-known and Zapdos removal opens CurseLax; Surf/Toxic low | Snorlax | top | P/R/B | Correct preservation and absorber owner. |
| 10 | p2 | Sleep Talk; preserve Zapdos only if Snorlax route becomes too strong; no passive sleep script | Sleep Talk -> Rest | top | P/R | Correct active RestTalk reset. |
| 11 | p1 | Curse; Body Slam/Double-Edge; switch only if Steelix/Cloyster branch dominates | Body Slam | miss | P | Active chip into the receiver beat my extra setup. |
| 11 | p2 | Switch physical owner; Sleep Talk if staying; preserve Zapdos for later | Steelix | top by class | P/R/B | Correct Steelix receiver class. |
| 12 | p1 | Switch Steelix answer; revealed/side-known coverage only with fallback; reject Body Slam/Curse | Exeggutor | acceptable | P/B | Correct leave-Snorlax route, exact Exeggutor class under-specified. |
| 12 | p2 | Earthquake; Roar if switch loop is stronger; Curse only if receiver cannot punish | Roar | acceptable | P/R/B | Roar branch-punish was ranked but not top. |
| 13 | p1 | Exeggutor/Steelix answer handoff; HP Water only if side-known; stay only with public converter | Exeggutor | top | P/R/B | Correct loop-break handoff. |
| 13 | p2 | Earthquake; Roar if switch loop stays stable; Curse if free boost changes route | Roar | acceptable | P/R/B | Again under-ranked stable Roar loop by one slot. |
| 14 | p1 | Exeggutor handoff; HP Water only if side-known; preserve Raikou | Exeggutor | top | P/R/B | Correct handoff. |
| 14 | p2 | Roar; Earthquake if Exeggutor stays; Curse if receiver cannot punish | Earthquake | acceptable | P/R | Correct active damage was ranked second. |
| 15 | p1 | Psychic; Explosion only if side-known and forced; switch only if Egg must preserve | Psychic | top | P/R | Correct pressure into Steelix/Zapdos branch. |
| 15 | p2 | Roar or Earthquake to continue Steelix loop; switch only if preserving Steelix beats chip | Zapdos | miss | - | Missed sleep-absorber re-entry as the Steelix-preservation branch. |

## Reusable Lessons

- The compressed core helped ranking discipline: I named owners and branch
  actions more consistently, especially around Snorlax handoff, Cloyster
  layers, and Raikou/Exeggutor into Steelix.
- The first miss was the old item-first problem. Exeggutor lead sleep was
  defensible, but the actual route was `Thief` into the expected absorber.
- RestTalk Zapdos must be treated as active pressure even while asleep. Staying
  with `Sleep Talk`, switching it back into status, or handing Snorlax into it
  are all route actions, not passive sleep turns.
- Steelix plus Spikes must be scored as a loop. `Roar` was acceptable in my
  ranking but under-ranked on turns 12-13, then I overcorrected on turn 14.
- The next strict packet should load only `live_core.md` and
  `heuristic_core/converter_before_script.md` or `reset_loop_denial.md`, not
  two tiny cards, to test the routing rule cleanly.
