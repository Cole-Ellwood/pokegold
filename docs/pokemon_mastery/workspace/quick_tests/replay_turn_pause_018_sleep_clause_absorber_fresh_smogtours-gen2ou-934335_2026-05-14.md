# Replay Turn-Pause 018 Sleep Clause Absorber - smogtours-gen2ou-934335 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-934335`.

Mode: spectator public, semi-blind candidate-screened.

Purpose: test the corrected sleep policy from the user correction: after a
Pokemon is put to sleep in GSC, the common branch is to switch it out and
preserve it as Sleep Clause material, not automatically burn turns waking.

Contamination control:

- The replay was found through recent Smogtours replay search.
- A local script screened several candidate logs only for whether an induced
  sleep move name appeared somewhere in the battle.
- The script did not reveal the sleep turn, actor, target, outcome, or later
  branch.
- Turns were revealed with the local replay helper after each answer was
  frozen.
- This is useful quick-probe evidence, not final-exam-clean evidence.

Local docs checked:

- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/paused_turn_atlas.md`
- `docs/pokemon_mastery/workspace/quick_tests/sleep_clause_absorber_probe_001_2026-05-14.md`

Web sources checked:

- Smogon Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`
- Smogon Gold/Silver OU Metagame Primer:
  `https://www.smogon.com/resources/competitive/gs/gs_ou_primer`
- Pokemon Showdown ladder help:
  `https://pokemonshowdown.com/pages/ladderhelp`

Source note: Smogon's GSC status article frames sleep as real but checked by
Sleep Talk, Heal Bell, wake attacks, and target choice. The GSC primer defines
Sleep Clause Mod as preventing a player from putting another opposing Pokemon
to sleep while the first induced target is still asleep. That makes a sleeping
target a board resource, not just dead material.

## Score Summary

Target turns scored: 6-8.

Context turns 1-5 were used only to reach the first induced sleep event. They
included lead Snorlax switching to Alakazam, both sides setting Spikes, p2
Snorlax revealing Curse and Double-Edge, and p1 Cloyster fainting after setting
Spikes.

Target decisions scored: 5 side-decisions.

Top-match: 3 / 5.

Acceptable-match: 5 / 5.

Severe blunders: 0.

Mechanics errors: 0.

State errors: 0.

Hidden-info errors: 0.

Earliest meaningful target error: turn 7.

## Turn Log

| Turn | Public state focus | My answer | Actual choices | Grade | Lesson |
| --- | --- | --- | --- | --- | --- |
| 6 | Gengar 94 -> 100 vs p2 Snorlax 79, `atk+1 def+1 spe-1`; Spikes on both sides | p1 Hypnosis if Gengar has it; p2 should fear sleep but may attack or switch if it has a direct Gengar answer | p1 Hypnosis hit; p2 Snorlax slept before moving | p1 top; p2 excluded | Hypnosis into non-Sleep Talk revealed Snorlax changed the route immediately and activated Sleep Clause pressure. |
| 7 | Gengar 100 vs sleeping p2 Snorlax 79, still boosted | p2 top switch out to preserve Snorlax as Sleep Clause material; p1 should expect that and attack, pivot, or double rather than repeat Hypnosis | p1 switched to Zapdos; p2 stayed asleep | p1 acceptable; p2 acceptable but not top | The correction is not a hard rule. Staying one turn can be acceptable when the opponent's active Gengar may pivot or Explosion-scout and the direct punish is low. |
| 8 | Zapdos 100 vs sleeping p2 Snorlax 79 | p1 Thunderbolt/Thunder pressure; p2 switch to an Electric answer and preserve sleeping Snorlax | p2 switched Raikou into Spikes; p1 Thunderbolt | both top | The common preservation branch appeared one turn later once Zapdos created direct pressure. Sleeping Snorlax remained Sleep Clause material instead of being spent on wake turns. |

## Error Classes

- Timing overcorrection: after the user's correction, I made "switch out
  immediately" too strong on turn 7. The better policy is switch-out default,
  then price whether the active opponent can actually punish a one-turn sleep
  burn.
- Sleep Clause material retained: turn 8 still confirmed the core correction.
  The sleeping Snorlax was preserved once pressure changed from Gengar to
  Zapdos.
- No hidden-info error: the exact Raikou switch was not public before turn 8,
  but "Electric answer" was a legal public-information category.

## Policy Update

Sleep absorber policy should say: after induced sleep lands, first check the
common branch where the sleeper switches out and remains Sleep Clause material.
Do not turn that into a script. If the opponent's active cannot immediately
punish, or if Explosion/pivot scouting makes staying valuable, burning one
sleep turn can be acceptable before switching under stronger pressure.

## Next Study Target

Run a fresh replay segment where a slept Pokemon has Sleep Talk or Explosion
revealed later, and score whether I preserve the sleeper's later job instead of
treating it as inert.
