# Replay Turn-Pause 034 Sleep Clause Wake Cash-Out Transfer - smogtours-gen2ou-934415 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-934415`.

Mode: spectator-public vanilla GSC replay practice.

Contamination control: selected from unused cached Smogtours logs by broad
sleep-move and sleep-status counts, then opened only the prompt before turn 17.
Future turns were revealed one at a time with
`tools/pokemon_mastery/replay_turn_pause.py`. This is semi-blind replay
practice, not a sealed exam.

Selected measurable action: score the first sleep-clause follow-up after a
sleep absorption, because the current bottleneck is whether the sleep-clause
preservation rule transfers without turning into a script.

Local docs checked:

- `docs/pokemon_mastery/master_index.md`
- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/training_cycle.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/boss_turn_advice_template.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/cookbook.md`
- `docs/pokemon_mastery/study_roadmap_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/sleep_clause_absorber_probe_001_2026-05-14.md`

Web sources checked:

- Smogon, Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`
- Smogon, Gold/Silver OverUsed Metagame Primer:
  `https://www.smogon.com/resources/competitive/gs/gs_ou_primer`
- Smogon Forums, Gen 2 Jynx GSC OU analysis:
  `https://www.smogon.com/forums/threads/jynx-gsc-ou-qc-2-2-gp-2-2.3667481/`
- Pokemon Showdown ladder help:
  `https://pokemonshowdown.com/pages/ladderhelp`

Source note: Smogon status material reinforces that GSC sleep is checked by
Sleep Talk and wake turns, while the GSC primer defines simulator Sleep Clause.
The Jynx analysis makes the absorber pattern concrete: Sleep Talk users can
come in, activate Sleep Clause, and threaten back immediately. The replay below
tests the adjacent branch where a non-Sleep Talk target is already asleep but
may still be better left in for one or two turns before the opponent cashes out.

## Score Summary

Scored decisions: 7 side decisions.

Top-match: 4 / 7.

Acceptable-match: 5 / 7.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 17, over-preferring immediate preservation
when the sleeping Pokemon resisted the active punish and could safely burn one
turn.

Primary error class: wake-window cash-out was underpriced on turn 19. Staying
with the sleeping target was acceptable on turns 17 and 18, but the position
needed to be re-solved before the likely wake window because Exeggutor could
use Explosion to remove Alakazam before it woke and KOed Exeggutor.

## Turn 17

Public state:

```text
p1 Alakazam 100% asleep vs p2 Exeggutor 8%.
p1 has seen Alakazam, Cloyster fainted, Gengar 100, Snorlax 78, Zapdos fainted.
p2 has seen Espeon 73, Exeggutor 8, Raikou fainted, Snorlax fainted.
Spikes are on p2's side only.
Exeggutor has revealed Sleep Powder and Thief; Alakazam has revealed Psychic,
Thief, and Toxic.
```

My p1 answer: switch to Gengar to preserve Alakazam as Sleep Clause material,
with stay-in as a low-punish alternative if Exeggutor only chips with Psychic.

My p2 answer: Psychic, because it chips Alakazam and punishes the obvious
Gengar Explosion-cover switch; Explosion is the serious cash-out alternative.

Actual choices:

```text
Alakazam stayed asleep.
Exeggutor used Psychic.
Alakazam went to 85% after Leftovers.
Exeggutor healed to 14%.
```

Grade: p1 acceptable but not top; p2 top.

Reusable lesson: preserving Sleep Clause material is a default branch, but an
asleep Pokemon that resists the active punish can sometimes stay one turn
without losing its future value.

## Turn 18

Public state:

```text
p1 Alakazam 85% asleep vs p2 Exeggutor 14%.
Exeggutor has now revealed Psychic, Sleep Powder, and Thief.
Spikes remain on p2's side.
```

My p1 answer: stay and click Psychic if awake. Switching Gengar now is worse
because Psychic is revealed and Exeggutor is not forcing enough damage.

My p2 answer: Psychic again, with Explosion as the route-conversion alternative
if Alakazam's wake turn becomes too dangerous.

Actual choices:

```text
Alakazam stayed asleep.
Exeggutor used Psychic.
Alakazam went to 70% after Leftovers.
Exeggutor healed to 20%.
```

Grade: both top.

Reusable lesson: the correction to the correction matters. Do not switch a
sleeping Pokemon out just because it is asleep; first ask whether the current
active can actually punish the burn turn.

## Turn 19

Public state:

```text
p1 Alakazam 70% asleep vs p2 Exeggutor 20%.
Alakazam may soon wake and KO Exeggutor with Psychic.
Exeggutor has revealed Psychic, Sleep Powder, and Thief; Explosion remains a
serious common possibility but not public fact yet.
```

My p1 answer: stay and click Psychic if awake; Gengar remains the Explosion
cover but now loses hard if Exeggutor repeats Psychic.

My p2 answer: switch Espeon to cover the wake-and-Psychic branch while keeping
Exeggutor as a later sack.

Actual choices:

```text
Alakazam stayed asleep.
Exeggutor used Explosion.
Alakazam and Exeggutor fainted.
p1 sent Snorlax; p2 sent Cloyster, which took Spikes.
```

Grade: p1 top on branch, but risk explanation incomplete; p2 miss.

Reusable lesson: once the sleeper's wake can remove the sleep user, the opponent
may cash out instead of continuing safe chip or switching. Re-score every turn:
the correct turn-17 stay did not make turn-19 stay free.

## Turn 20

Public state:

```text
p1 Snorlax 78% vs p2 Cloyster 94%.
p1 Alakazam, Cloyster, and Zapdos are fainted; p1 Gengar remains known.
p2 Exeggutor, Raikou, and Snorlax are fainted; p2 Espeon 73 remains known.
p2 side has Spikes.
```

My p1 answer: Double-Edge if restricted to revealed pieces, with Gengar as the
Explosion-cover alternative.

My p2 answer: Spikes or another support move, with Surf as the anti-switch
coverage alternative.

Actual choices:

```text
p1 switched to previously unrevealed Jolteon.
Cloyster used Surf.
Jolteon went to 75% after Leftovers.
```

Grade: p1 excluded from exact scoring because the decisive Jolteon slot was
unrevealed in spectator-public mode; p2 miss.

Reusable lesson: spectator-public replay advice should sometimes phrase the
recommendation as "Electric if available" rather than only ranking revealed
teammates. That is not Team Preview if it is marked as a conditional.

## Error Classes

- Overcorrected sleep preservation on turn 17: immediate switch was not
  mandatory because the sleeping target resisted the active attack.
- Underpriced wake-window cash-out on turn 19: Explosion became stronger once
  waking Alakazam threatened to remove Exeggutor before more chip could happen.
- Did not express the hidden-team conditional on turn 20: the public-state
  answer could have said "fast Electric if available" without claiming the slot
  was known.

## Next Rep

Run a fresh unlabeled Starmie/Cloyster hazard-control transfer segment, because
the previous constructed pressure-handoff probe scored cleanly and now needs an
unlabeled replay check.
