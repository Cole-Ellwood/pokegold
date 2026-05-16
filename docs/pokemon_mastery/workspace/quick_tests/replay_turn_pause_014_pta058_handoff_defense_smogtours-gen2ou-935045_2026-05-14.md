# Replay Turn-Pause 014 PTA-058 Handoff Defense - smogtours-gen2ou-935045 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-935045`.

Discovery source: Pokemon Showdown replay search API,
`https://replay.pokemonshowdown.com/search.json?format=gen2ou`.

Mode: spectator public.

Purpose: fresh regression for `PTA-058`, focused on whether the support
cash-out checklist can both avoid premature Explosion and preserve the right
route piece when an opposing support attacker becomes dangerous.

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/training_cycle.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/paused_turn_atlas.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_013_pta058_preserve_boundary_smogtours-gen2ou-933556_2026-05-14.md`

Web sources checked:

- Smogon `GSC OU Winter Seasonal #8: Signups`:
  `https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-signups.3776852/`
- Smogon `GSC OU Winter Seasonal #8: Round 12 [REPLAYS Required]`:
  `https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-12-replays-required.3781144/latest`
- Pokemon Showdown replay search API:
  `https://replay.pokemonshowdown.com/search.json?format=gen2ou`
- Pokemon Showdown replay:
  `https://replay.pokemonshowdown.com/smogtours-gen2ou-935045`

Contamination control:

- Local search found no prior `935045` artifact.
- Other candidate replays were rejected if already reviewed or if their logs
  were exposed during candidate screening.
- The raw `.log` was downloaded to `.local/pokemon_mastery/replay_logs/`.
- I did not watch the replay UI.
- Turns 1-16 were answered before each reveal with
  `tools/pokemon_mastery/replay_turn_pause.py`.

## Score Summary

Turns: 1-16.

Decisions scored: 32 side-decisions.

Top-match: 11 / 32.

Acceptable-match: 16 / 32.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Earliest meaningful error: turn 2.

Targeted result: mixed. The defensive half improved on turn 13: after Cloyster
woke, set Spikes, and threatened Marowak, I correctly wanted Marowak preserved
with a lower-value absorber. I missed the exact absorber, but the actual line
used Smeargle, then let Smeargle set Spikes before dying. The cash-out half
still has a regression: on turn 5 I overcalled Exeggutor Explosion into
paralyzed Raikou instead of seeing that Psychic chip could force Rest and allow
a Marowak handoff.

## Turn Log

| Turn | Public state focus | My answer | Actual choices | Grade | Lesson |
| --- | --- | --- | --- | --- | --- |
| 1 | Smeargle vs Cloyster lead | p1 Spore; p2 avoid or absorb sleep | p1 Spore; p2 stayed and slept | p1 top, p2 miss | Smeargle lead can claim immediate sleep when Cloyster stays. |
| 2 | Smeargle after sleep | p1 Agility; p2 switch pressure | p1 Spikes; p2 Golem | both miss | After sleep, Spikes can be the first route support before pass pressure. |
| 3 | Smeargle vs Golem, p2 side Spikes | p1 preserve/anti-Spin line; p2 Rapid Spin | p1 Exeggutor; p2 Rapid Spin | p1 miss, p2 top | Golem spinning is clear, but Exeggutor punish can be chosen over hard spinblock. |
| 4 | Exeggutor vs Golem | p1 Giga/Psychic; p2 possible cash-out | p1 Stun Spore; p2 Raikou | both miss | Status on the Electric receiver mattered more than immediate damage. |
| 5 | Exeggutor vs paralyzed Raikou | p1 Explosion; p2 switch absorber | p1 Psychic; p2 Thunder miss | both miss | This was the key regression: support status did not make cash-out forced. |
| 6 | Exeggutor vs chipped paralyzed Raikou | p1 Psychic; p2 Thunder | p1 Marowak; p2 Rest | both miss | Once status and chip force Rest, hand off to the breaker before booming. |
| 7 | Marowak vs sleeping Raikou | p1 Swords Dance; p2 Cloyster | p1 Earthquake; p2 Exeggutor | p1 acceptable, p2 miss | Earthquake covered the sleeping Raikou and still punished the Grass switch. |
| 8 | Marowak vs Exeggutor | p1 preserve Marowak; p2 Sleep Powder | p1 Zapdos; p2 Sleep Powder missed | p1 acceptable, p2 top | Correct route class: do not leave Marowak in front of Sleep Powder/Giga. |
| 9 | Zapdos vs Exeggutor | p1 attack; p2 sleep again | p1 Marowak; p2 Snorlax | both miss | I missed the double-switch route that reset Marowak onto Snorlax. |
| 10 | Marowak vs Snorlax | p1 Earthquake; p2 switch Exeggutor | p1 Earthquake crit KO; p2 stayed | p1 top, p2 miss | Marowak attacking was correct; the crit makes p2's unstated move hard to judge. |
| 11 | Marowak vs sleeping Cloyster | p1 preserve; p2 stay | p1 Earthquake; p2 slept | p1 miss, p2 top | I over-preserved while the sleep turn still let Marowak cash damage. |
| 12 | Marowak vs low sleeping Cloyster | p1 Earthquake; p2 Surf if wake | p1 Earthquake; p2 woke and set Spikes | p1 top, p2 miss | Cloyster chose route support before attacking even at low HP. |
| 13 | Marowak vs awake low Cloyster | p1 preserve Marowak; p2 attack | p1 Smeargle; p2 Ice Beam | p1 acceptable, p2 acceptable | Good defense clause: spend the lower-value piece, not Marowak. |
| 14 | Smeargle low vs Cloyster low | p1 Spikes; p2 Ice Beam | p1 Spikes; p2 Ice Beam KO | both top | Once Smeargle is the absorber, it can still deliver one final support action. |
| 15 | Zapdos vs low Cloyster | p1 Thunder; p2 Golem | p1 Thunder; p2 Golem | both top | Golem handoff to deny Thunder and threaten Spin was correctly priced. |
| 16 | Zapdos vs Golem | p1 switch Exeggutor; p2 Rapid Spin | p1 Hidden Power; p2 Rapid Spin | p1 miss, p2 top | I undercalled Zapdos staying to damage Golem before Spin. |

## Error Classes

- Premature cash-out: turn 5 repeated the old error in a new form. Status on
  Raikou created a Rest/handoff route; it did not force Exeggutor Explosion.
- Handoff timing: turns 6 and 9 show that I still miss the moment when prior
  status or pressure lets the breaker come in safely.
- Support-before-attack ordering: turn 12 showed low Cloyster setting Spikes
  before attacking Marowak. I expected immediate damage.
- Preservation success, partial: turn 13 improved over the prior Snorlax miss.
  I preserved Marowak, but did not name the exact lower-value absorber.
- Hazard-retention pricing: turn 16 showed Zapdos could stay and damage Golem
  before Rapid Spin, instead of always switching to punish Spin.

## Policy Update

Add this to the support/cash-out checklist:

```text
If status or chip on the target makes Rest or a passive reset likely, ask
whether that reset gives a route handoff before cashing out. The right sequence
may be status -> chip -> breaker handoff, not status -> Explosion.
```

## Next Study Target

Run a short regression that starts after a route support action lands and asks:
"Does the status force a reset, a switch, a cash-out, or a preserve-and-handoff?"
Score the answer before revealing the next turn.
