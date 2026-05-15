# Replay Turn-Pause 039 Sleep Talk Pursuit Transfer - smogtours-gen2ou-931710 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-931710`.

Mode: spectator-public vanilla GSC replay practice.

Selected measurable action: fresh replay transfer after
`sleep_clause_four_choice_probe_001_2026-05-14.md`. The target was to test the
four sleeping-Pokemon classes in a real replay: preserve the sleeper, stay with
Sleep Talk, stay because the active route is better, or spend / cover the
sleeper because a route branch changed.

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs and excluded recent candidates exposed by earlier grep snippets.
- Screening printed only replay ID, first prompt turn, total turns, induced
  sleep count, and file size.
- The selected start was turn 13, immediately after Gengar put Quagsire to
  sleep. Turns 13-27 were answered before reveal.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/sleep_clause_four_choice_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_038_sleep_clause_overcorrection_smogtours-gen2ou-934314_2026-05-14.md`

Web sources checked:

- Smogon Forums, GSC OU Jynx / Sleep Talk absorber discussion:
  `https://www.smogon.com/forums/threads/jynx-gsc-ou-qc-2-2-gp-2-2.3667481/`
- Smogon Forums, GSC Sleep Trap:
  `https://www.smogon.com/forums/threads/gsc-sleep-trap.3622522/`
- Smogon Forums, GSC Introduction to Status:
  `https://www.smogon.com/forums/threads/gsc-introduction-to-status-sleep-paralysis-and-poison-gp-2-2.103998/`
- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`

Source note: the prior policy says a slept Pokemon is often switched out and
preserved as Sleep Clause material. This replay tested the first exception:
Quagsire revealed Sleep Talk immediately, making it an active board piece
instead of inert sleep material. The second reusable branch came from Gengar:
after Houndoom trapped it with Pursuit, Explosion became the route trade.

## Score Summary

Scored decisions: 29 side decisions. Turn 16 p2 was unscored because Houndoom
fainted before its selected move was logged.

Top-match: 9 / 29.

Acceptable-match: 15 / 29.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 13 p2. I wanted to switch sleeping Quagsire
out as Sleep Clause material, but Quagsire revealed Sleep Talk and immediately
hit Gengar with Surf. The correct branch class was "stay with current sleeping
utility."

Main improvements:

- Correctly reclassified Quagsire after Sleep Talk was revealed and accepted
  the turn-14 preservation switch.
- Correctly named Tentacruel as a serious pivot into Tyranitar on turn 21.
- Correctly used the player-known Hidden Power conditional into Dragonite on
  turn 17.

Main errors:

- Turn 13: missed the Sleep Talk exception before it was public.
- Turn 15: named Pursuit as the worst branch but still chose the Gengar switch
  that would get punished by Pursuit. Staying and attacking was better.
- Turn 16: missed the trapped-Gengar Explosion cash-out into Houndoom.
- Turn 18: failed to include "Normal resist / Toxic absorber if available,"
  which would have covered the hidden Steelix switch under no Team Preview.
- Turn 24-27: overfocused on Tentacruel's Rapid Spin window and underpriced
  the Flying / Skarmory / Dragonite pivot chain.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Lesson |
|---|---|---|---|---|---|
| 13 | Gengar vs sleeping Quagsire 66 | p1 Ice Punch; p2 preserve Quagsire | p1 Ice Punch; p2 Sleep Talk Surf | p1 top, p2 miss | Before Sleep Talk is revealed, preserve is plausible; after reveal, the sleeper is active. |
| 14 | Gengar 73 vs sleeping Quagsire 50 with Sleep Talk | p1 Ice Punch; p2 Sleep Talk or preserve | p2 Houndoom; p1 Ice Punch | p1 top, p2 acceptable | Preservation was right, but hidden Houndoom could not be named under no Team Preview. |
| 15 | Gengar vs Houndoom 82 | p1 switch Cloyster; p2 Pursuit | p1 Thunderbolt; p2 Pursuit | p1 miss, p2 top | Naming Pursuit is not enough; the chosen line must actually cover it. |
| 16 | Gengar 48 vs Houndoom 57 | p1 Thunderbolt; p2 direct KO move | p1 Explosion KOed both | p1 miss, p2 unscored | Trapped low Gengar should cash out once Thunderbolt leaves it exposed. |
| 17 | Zapdos vs Dragonite | p1 Hidden Power if Ice / Thunder fallback; p2 Snorlax pivot | p2 Snorlax; p1 Hidden Power | both top | Use player-known Hidden Power type conditionally; do not assume spectator public knows the type. |
| 18 | Zapdos vs Snorlax 82 | p1 Thunder; p2 Toxic | p1 Steelix; p2 Defense Curl | both miss | Hidden Steelix was not knowable, but "Normal resist / Toxic absorber if available" should be named. |
| 19 | Steelix vs +1 Defense Curl Snorlax | p1 Roar if available, else Earthquake/Curse; p2 leave | p1 Curse; p2 Dragonite | both acceptable | Support/setup routes need conditional move ownership, not species assumptions. |
| 20 | +1 Steelix vs Dragonite | p1 Zapdos; p2 coverage/Haze/TWave | p1 Tyranitar; p2 Reflect | both miss | The missing branch was hidden Rock answer plus Dragonite support. |
| 21 | Tyranitar vs Dragonite behind Reflect | p1 Rock Slide; p2 Quagsire/Tentacruel | p2 Tentacruel; p1 Dynamic Punch | p1 miss, p2 top | Tyranitar used anti-pivot confusion pressure instead of direct Dragonite damage. |
| 22 | Tyranitar vs Tentacruel | p1 Earthquake if available; p2 Rapid Spin | p2 Snorlax; p1 Earthquake | p1 top, p2 miss | Spin was tempting, but p2 respected Earthquake by using a bulkier pivot. |
| 23 | Tyranitar vs Snorlax 69 | p1 Dynamic Punch; p2 Toxic or pivot | p2 Tentacruel; p1 Dynamic Punch | p1 top, p2 acceptable | Dynamic Punch was the right pressure into repeated pivots. |
| 24 | Tyranitar vs Tentacruel 69 | p1 Earthquake; p2 Rapid Spin | p2 Skarmory; p1 Rock Slide | both miss | The Flying pivot branch outranked immediate Spin. |
| 25 | Tyranitar vs Skarmory 93 | p1 Zapdos unless Fire coverage; p2 Toxic/Whirlwind | p1 Fire Blast; p2 Toxic | p1 acceptable, p2 top | Conditional ownership matters: Tyranitar had the Skarmory punish. |
| 26 | Toxic Tyranitar vs Skarmory 35 | p1 Earthquake midground; p2 switch | p2 Rest; p1 Dynamic Punch miss | both miss | Low Skarmory could preserve itself with Rest, not only switch or die. |
| 27 | Toxic Tyranitar vs Resting Skarmory 100 | p1 Fire Blast; p2 preserve Skarmory | p2 Dragonite; p1 Rock Slide | p1 miss, p2 acceptable | Resting support can be preserved by a pivot chain; name the likely pivot before attacking. |

## Reusable Update

Sleep classification should happen in this order:

1. If Sleep Talk is revealed, the sleeping Pokemon is still an active attacker
   or absorber. Do not auto-switch it out.
2. If Sleep Talk is not revealed and the sleeper has future route jobs, the
   preserve-default is still strong.
3. If a trapper punishes the preserve switch, stay and attack or cash out
   before the trapper converts.
4. If Rest or a pivot chain preserves a low support Pokemon, do not assume low
   HP means switch-or-die.

The repeated miss was not hidden-information abuse; it was incomplete branch
pricing. I often named the dangerous branch, then chose a line that still lost
to it. The next replay should specifically score whether the final action
actually covers the named worst branch.

## Next Rep

Fresh replay segment with an obvious trap, phaze, or spin branch. Score:

- named worst branch;
- whether the chosen move actually covers it;
- whether hidden teammate conditionals are phrased as conditionals instead of
  assumed facts.
