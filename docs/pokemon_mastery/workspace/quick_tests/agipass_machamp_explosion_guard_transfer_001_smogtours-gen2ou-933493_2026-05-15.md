# AgiPass Machamp/Explosion Guard Transfer 001 - smogtours-gen2ou-933493 - 2026-05-15

Source:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933493`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-933493.log`

Search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&server=smogtours&page=3`

Mode: spectator-public no-Team-Preview turn pause. Smogtours replay, selected
from current metadata and turn count only. I did not inspect move content or
future turns before freezing answers.

Contamination control:

- Local `rg` found no prior `smogtours-gen2ou-933493` use before selection.
- The log was saved locally at
  `tmp/pokemon_mastery_replays/smogtours-gen2ou-933493.log`.
- Prompts used
  `python tools/pokemon_mastery/replay_turn_pause.py ... prompt --turn N`.
- Reveals used
  `python tools/pokemon_mastery/replay_turn_pause.py ... reveal --turn N`.
- Fresh reveals stopped at turn 10 after repeated pass-chain defensive-owner
  and Explosion-immunity lessons.
- The helper omitted Baton Pass boosts after receiver switches, so Jolteon
  `spe+2` and Machamp `spe+2` were manually carried from public reveal lines.

## Score Summary

Decisions: 20 scored, 0 unscored.

Top-match: 7/20.
Acceptable-match: 16/20.
Severe blunders: 0.
State errors: 0.
Hidden-info errors: 0.
Mechanics errors: 0.
Positive-selection: 15/20.
Route-converting move chosen: 12/20.
Branch-punish chosen: 9/16.
Earliest meaningful error: turn 1.

Result: not progress. The sample is an early-stop packet, not a full 30-50
decision proof run. It kept severe/hidden/state/mechanics clean and acceptable
above gate, but top-match and route conversion stayed below target, and the
same pass-chain receiver class remained active.

## Frozen Answer Log

Candidates are ranked in order. Tags: `P` positive-selection, `R`
route-converting, `B` branch-punish.

| Turn | Side | Frozen top three | Actual | Grade | Tags | Lesson |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | p1 | Double-Edge/STAB; Fire coverage read; Electric/Fire pressure owner | Gengar | miss | - | Missed the immediate Gengar handoff into Forretress support. |
| 1 | p2 | Spikes; Toxic; Explosion high-risk | Spikes | top | P/R | Correct first support job. |
| 2 | p1 | Hypnosis; Thunder/coverage; Dynamic Punch utility | Thief | acceptable | P/R/B | Status pressure was defensible, but item denial was the sharper receiver punish. |
| 2 | p2 | Raikou/Snorlax special receiver; Toxic; Rapid Spin later | Jolteon | acceptable | P/R/B | Correct receiver class, exact Agility passer missed. |
| 3 | p1 | Snorlax/special wall; Hypnosis; Explosion high-risk | Snorlax | top | P/R/B | Correct item-job handoff after Thief. |
| 3 | p2 | Thunderbolt; Baton Pass/Agility; Hidden Power | Agility | acceptable | P | Agility pass was ranked but not high enough. |
| 4 | p1 | Lovely Kiss; Curse; STAB/coverage | Curse | acceptable | P/R/B | Curse was the receiver-prep line into Machamp, but under-ranked. |
| 4 | p2 | Baton Pass; Thunderbolt; Substitute/Growth | Baton Pass to Machamp | top | P/R/B | Correct pass route. |
| 5 | p1 | Gengar; Curse; Double-Edge | Double-Edge | miss | - | Over-handoff: +1 Double-Edge put Machamp in revenge range before it converted. |
| 5 | p2 | Cross Chop; Meditate/Curse; Rock Slide | Meditate | acceptable | P/R | Meditate kept speed-pass pressure while preserving coverage. |
| 6 | p1 | Double-Edge; Gengar; Rest | stayed and fainted before action | miss | P | Damage was the right idea only if Cross Chop risk was priced; crit branch punished it. |
| 6 | p2 | Cross Chop; Rock Slide; preserve | Cross Chop | top | P/R/B | Correct high-crit STAB into Snorlax despite boosts. |
| 7 | p1 | Drill Peck/Flying pressure; Thunder; Gengar | Thunder | acceptable | P/R | Correct attack class; exact Zapdos move missed. |
| 7 | p2 | Rock Slide; Cross Chop; preserve | Rock Slide | top | P/R/B | Correct Zapdos branch coverage. |
| 8 | p1 | Gengar pivot; Thunder; sack | Nidoking | miss | - | Missed the Ground receiver that both blocks Electric and threatens sleep. |
| 8 | p2 | Thunderbolt; Agility/Baton Pass; Hidden Power | Agility | acceptable | P | Rebuilding pass pressure was ranked but not top. |
| 9 | p1 | Lovely Kiss; Earthquake; Ice/coverage | Lovely Kiss | top | P/R/B | Correct receiver-punish, though it missed. |
| 9 | p2 | Baton Pass; Hidden Power; Thunderbolt | Baton Pass to Forretress | top | P/R/B | Correct support receiver. |
| 10 | p1 | Earthquake/active damage; Lovely Kiss retry; Gengar/Zapdos | Gengar | acceptable | - | Gengar was named but too low; it was the Explosion guard. |
| 10 | p2 | Toxic/support; Explosion; switch | Explosion | acceptable | - | Explosion was ranked, but the revealed Ghost made it unsafe. |

## Reusable Lessons

- Jolteon Agility means the next question is not only "what does Jolteon do?"
  but "which receiver becomes active with speed?" In this replay the answer was
  Machamp, then Forretress after a second pass.
- Against passed Machamp, Gengar is not automatic. If boosted Snorlax can put
  Machamp in revenge range before the Fighting hit lands, damage may be the
  route. But Cross Chop's high-crit branch must be priced explicitly before
  leaving Snorlax in.
- If the pass receiver has just been chunked low, do not call the route failed;
  name the revenge owner. Here Zapdos removed Machamp after Snorlax fell.
- Nidoking is the correct Electric receiver when public material reveals it:
  it blocks Electric pressure and can threaten Lovely Kiss or coverage. Do not
  preserve Zapdos with a generic Ghost when a Ground receiver is live.
- Forretress with Spikes delivered and Explosion available asks for an
  immunity guard. If Gengar is revealed, healthy, and can enter, rank the Ghost
  handoff before active damage into Forretress.
- Possible Fire Blast on Nidoking was kept out of the main line until revealed;
  that was correct tier discipline even though Fire Blast would have punished
  Forretress.
