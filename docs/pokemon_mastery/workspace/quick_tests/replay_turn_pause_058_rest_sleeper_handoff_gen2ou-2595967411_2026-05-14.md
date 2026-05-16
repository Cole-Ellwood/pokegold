# Replay Turn-Pause 058 Rest Sleeper Handoff - gen2ou-2595967411 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/gen2ou-2595967411-32o0jwig5yhd7ibl9iidu1k9leh02kcpw`.

Context source: 2026 GSC OU Global Championship replay post on Smogon.

Mode: spectator public, semi-blind candidate-screened.

Contamination control:

- The replay id was not found in existing local docs before use.
- A candidate screen checked only broad keyword presence across four downloaded
  logs. It exposed that this replay contained Spikes, Sleep Powder, Rest,
  Sleep Talk, Explosion, phazing, and Curse somewhere in the log, but not turn
  order or outcomes.
- Public prompts were generated with
  `tools/pokemon_mastery/replay_turn_pause.py`.
- Bench switches to unrevealed Pokemon are weaker comparison points in
  spectator-public mode because the prompt cannot list the player's private
  team.

## Score Summary

Decisions: 23 countable side decisions. Turn 4 p1 was unscored because the
flinch hid the attempted move.

Top-match: 5 / 23.

Acceptable-match: 9 / 23.

Severe blunders: 0.

State errors: 0 hard public-state misses.

Hidden-info errors: 0.

Mechanics errors: 0.

Earliest meaningful error: Turn 1 exact mismatch from an unrevealed immediate
Spiker pivot. If bench-limited decisions are discounted, the first clean
route-pricing miss is Turn 6.

## Turn Notes

### Turn 1

Public state: p1 Zapdos 100% versus p2 Snorlax 100%, no moves revealed.

Frozen answer:

- p1: Thunder or direct pressure, medium-low confidence. Serious alternative:
  pivot if a defined sleep or Normal-resist plan exists.
- p2: immediate attacking pressure, medium-low confidence. Serious alternative:
  Curse if planning to claim tempo from the lead matchup.

Actual choices: p1 switched to Forretress. p2 used Curse.

Grade: p1 miss, p2 miss. The useful lesson is that immediate Spiker/Normal
resist pivots must stay live against lead Snorlax even before the set is known.

### Turn 2

Public state: p1 Forretress 100% versus p2 +1 Defense/+1 Attack Snorlax 100%.

Frozen answer:

- p1: Spikes, high confidence.
- p2: Fire Blast or direct punish if available; otherwise switch to a pressure
  piece that prevents free Forretress turns.

Actual choices: p2 switched to Tyranitar. p1 used Spikes.

Grade: p1 top-match. p2 acceptable-match by route class, because Tyranitar
immediately revealed Fire Blast pressure on the Forretress slot.

### Turn 3

Public state: p1 Forretress 100% versus p2 Tyranitar 100%, Spikes on p2 side.

Frozen answer:

- p1: switch out of Fire Blast danger, naming Zapdos as the only public pivot.
- p2: Fire Blast, medium-high confidence.

Actual choices: p1 switched to Snorlax. p2 used Fire Blast, critting Snorlax
to 68% before Leftovers.

Grade: p1 acceptable route but wrong absorber; p2 top-match. The route class
was correct: preserve Forretress from Fire Blast. The specific absorber was not.

### Turn 4

Public state: p1 Snorlax 74% versus p2 Tyranitar 100%.

Frozen answer:

- p1: Earthquake if available, otherwise immediate damaging pressure.
- p2: switch away from a likely Snorlax punish.

Actual choices: p2 used Rock Slide. p1 flinched, so its selected move was not
revealed.

Grade: p1 unscored, p2 miss.

### Turn 5

Public state: p1 Snorlax 51% versus p2 Tyranitar 100%.

Frozen answer:

- p1: Earthquake or direct punish; staying active looked better than giving
  Tyranitar another free hit.
- p2: Rock Slide, medium confidence, because it keeps pressure and can flinch.

Actual choices: p1 switched to Raikou. p2 used Rock Slide, leaving Raikou at
73% after Leftovers.

Grade: p1 miss, p2 top-match.

### Turn 6

Public state: p1 Raikou 73% versus p2 Tyranitar 100%.

Frozen answer:

- p1: Reflect or a stabilizing move, with Hidden Power Water noted only as an
  if-available possibility.
- p2: Rock Slide, with Earthquake noted as a possible coverage punish.

Actual choices: p1 used super-effective Hidden Power. p2 used Earthquake,
leaving Raikou at 10% after Leftovers.

Grade: both miss. This was the cleanest route-pricing error: voluntary Raikou
entry into Tyranitar should have made Hidden Power Water or a planned cash-out
much more salient, and Tyranitar's best punish was Earthquake, not more Rock
Slide.

### Turn 7

Public state: p1 Raikou 10% versus p2 Tyranitar 77%.

Frozen answer:

- p1: Hidden Power again, cashing Raikou for Tyranitar damage.
- p2: Earthquake, high confidence.

Actual choices: p1 used Hidden Power, dropping Tyranitar to 49%. p2 used
Earthquake and KOed Raikou.

Grade: both top-match.

### Turn 8

Public state: p1 Gengar 100% versus p2 Tyranitar 55%, Spikes on p2 side.

Frozen answer:

- p1: Explosion, trying to remove Tyranitar and open Zapdos.
- p2: switch to preserve Tyranitar from a Gengar punish, naming Snorlax as the
  rough target class.

Actual choices: p2 switched to Exeggutor, taking Spikes to 87%. p1 used Dynamic
Punch and missed.

Grade: p1 miss, p2 acceptable route. The miss is an over-cash: Dynamic Punch
kept Gengar's future Normal immunity and Explosion resource while still
threatening Tyranitar.

### Turn 9

Public state: p1 Gengar 100% versus p2 Exeggutor 93%.

Frozen answer:

- p1: switch Snorlax as the likely sleep/Psychic absorber.
- p2: Sleep Powder, with Psychic and Explosion as serious alternatives.

Actual choices: p1 switched to Zapdos. p2 used Psychic, leaving Zapdos at 68%
after Leftovers.

Grade: both miss. I over-weighted the candidate-screened Sleep Powder presence
and under-priced the immediate Psychic punish into Gengar.

### Turn 10

Public state: p1 Zapdos 68% versus p2 Exeggutor 99%.

Frozen answer:

- p1: Hidden Power Ice if available; otherwise direct Zapdos pressure.
- p2: Sleep Powder, with status pressure as the route class.

Actual choices: p1 used Thunder and crit Exeggutor to 42%. p2 used Stun Spore,
paralyzing Zapdos.

Grade: p1 acceptable route, p2 miss. Exact status mattered: paralysis changed
Zapdos's speed and Rest incentives without spending Sleep Clause pressure.

### Turn 11

Public state: p1 Zapdos 74% paralyzed versus p2 Exeggutor 48%.

Frozen answer:

- p1: switch to Forretress to preserve Zapdos and cover Explosion/Psychic.
- p2: Explosion, trying to remove a route-defining Zapdos.

Actual choices: p2 used Psychic. p1 used Rest, healing Zapdos to full and
changing paralysis into sleep.

Grade: both miss. I missed the Rest line as a way to preserve a damaged,
paralyzed Zapdos without giving up the route.

### Turn 12

Public state: p1 Zapdos 100% asleep with Thunder and Rest revealed versus p2
Exeggutor 54%.

Frozen answer:

- p1: Sleep Talk if available; otherwise switch only if the sleeping Zapdos has
  no active job.
- p2: Explosion, trying to prevent a RestTalk Zapdos from continuing pressure.

Actual choices: p1 switched to Gengar. p2 switched to Snorlax, taking Spikes
to 87%.

Grade: both miss. This is the key sleeper-handoff lesson: even when RestTalk
may exist, the sleeping Pokemon can still be switched out and saved while
another piece handles the opponent's counter-pivot.

## Error Classes Found

- Voluntary-entry intent under-read: Raikou entering Tyranitar should increase
  the prior on Hidden Power Water or planned cash-out.
- Over-cash: spending Gengar with Explosion into Tyranitar looked active, but
  Dynamic Punch preserved Gengar's later jobs while still threatening progress.
- Sleep/status over-script: Exeggutor presence plus candidate-screened Sleep
  Powder made me over-predict sleep instead of pricing Psychic, Stun Spore, and
  switch branches.
- Rest sleeper handoff miss: a Rested Zapdos can be switched out and saved;
  Sleep Talk pressure is live, but not automatic.

## Reusable Lesson

After a support or status sequence, do not choose between "stay in forever" and
"switch forever." Name the next board. Here, Rest preserved Zapdos, but the
next board was better handled by switching the sleeping Zapdos to Gengar as the
Snorlax counter-pivot arrived.

## Next Study Target

Run a short regression probe with three positions:

1. Voluntary Electric entry into Tyranitar implies Hidden Power Water and a
   possible cash-out.
2. Gengar can threaten Tyranitar without immediately spending Explosion.
3. Rested Zapdos may stay active with Sleep Talk or switch out and preserve
   Sleep Clause/route value, depending on the opponent's counter-pivot.
