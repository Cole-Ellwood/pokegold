# Replay Turn-Pause 052 Lovely Kiss Snorlax Sleep Pivot - smogtours-gen2ou-923076 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-923076`.

Mode: spectator-public vanilla GSC replay practice with side-known conditionals
marked when my recommendation depended on unrevealed own-team slots.

Selected measurable action: fresh transfer after
`support_entry_explosion_absorber_probe_001_2026-05-14.md`. The target was a
combined support-entry / support-coverage / Explosion-absorber transfer. The
replay instead exposed a more valuable current bottleneck: team-level sleep
source assignment around Lovely Kiss Snorlax, plus damage-and-recoil pricing
against Snorlax after Sleep Clause is active.

Contamination control:

- Candidate selection excluded replay IDs already referenced in local mastery
  docs and contaminated `934420`.
- Screening printed only replay ID, selected start turn, total turns, route
  move count, and file size.
- The selected replay was `smogtours-gen2ou-923076`.
- The selected start was turn 1. Turns 1-9 were answered before reveal.

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_051_support_entry_explosion_absorber_smogtours-gen2ou-923748_2026-05-14.md`
- `docs/pokemon_mastery/quick_tests/support_entry_explosion_absorber_probe_001_2026-05-14.md`

Web sources checked:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, SPL XVII GSC Discussion:
  `https://www.smogon.com/forums/threads/spl-xvii-gsc-discussion.3775984/`

Source note: the current SPL XVII discussion specifically highlights Lovely
Kiss / Double-Edge / Earthquake / Explosion Snorlax on Raikou offense, and
notes that this can free Exeggutor and Gengar from needing sleep moves. That
explains why the replay punished my species-based "Exeggutor probably sleeps"
and "Gengar should Hypnosis" assumptions.

## Score Summary

Scored decisions: 18 side decisions.

Top-match: 11 / 18.

Acceptable-match: 12 / 18.

Classification hits: 11 / 18.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Earliest meaningful error: turn 1 p1. I assumed lead Exeggutor should use
Sleep Powder into Cloyster, but the actual Psychic put Cloyster into
Explosion range and fit a team where Snorlax carried Lovely Kiss.

Main improvement:

- Turns 2 and 4 transferred the support/Explosion and sleep-clause rules:
  Gengar absorbed low Cloyster's Explosion, then sleeping Exeggutor was
  switched out rather than left active to burn sleep turns.
- Turns 6 and 7 correctly identified the Raikou handoff and Hidden Power Ice
  midground into the Zapdos/Nidoking/Snorlax pivot map.

Main errors:

- Turn 1 p1: over-assumed Exeggutor as the sleep source instead of pricing
  Psychic damage into Cloyster's support-cash-out map.
- Turn 3 both sides: missed the team-level sleep plan. Gengar did not stay to
  use Hypnosis; Exeggutor became the Sleep Clause absorber while Snorlax
  revealed Lovely Kiss.
- Turn 8 p1: over-pivoted Raikou out of Snorlax. The actual line accepted
  Double-Edge damage because Hidden Power plus recoil pushed Snorlax down
  while Raikou survived.
- Turn 9 p1: picked the wrong Snorlax absorber. Gengar covered Double-Edge
  but lost value into the Earthquake branch; Cloyster was the better revealed
  midground.

## Turn Table

| Turn | Public focus | Frozen answer | Actual | Grade | Lesson |
|---|---|---|---|---|---|
| 1 | Lead Exeggutor vs Cloyster | p1 Sleep Powder; p2 Spikes | p2 Spikes; p1 Psychic | p1 miss, p2 top | Do not assign sleep by species alone; Psychic can set up the support-cash-out map. |
| 2 | Exeggutor 100 vs Cloyster 34 after Spikes | p1 Gengar if side-known, otherwise Psychic; p2 Explosion | p1 Gengar; p2 Explosion | both top | Side-known Ghost absorber transferred. |
| 3 | Gengar 94 vs Snorlax 100 | p1 Hypnosis; p2 Earthquake | p1 Exeggutor; p2 Lovely Kiss | both miss | Sleep was a team resource: Snorlax carried it, Exeggutor absorbed it. |
| 4 | sleeping Exeggutor 94 vs Snorlax 100 | p1 switch sleeper out; p2 improve route with Curse/attack | p1 Cloyster; p2 Nidoking | p1 top, p2 acceptable | Preserve the sleeper; opponent can double after Sleep Clause is active. |
| 5 | Cloyster 94 vs Nidoking 100 | p1 Spikes; p2 Thunder | p2 Zapdos; p1 Spikes | p1 top, p2 miss | Support seat was right; missed the Zapdos pressure handoff. |
| 6 | Cloyster 99 vs Zapdos 100 | p1 Raikou or special wall; p2 Thunder | p1 Raikou; p2 Thunder | both top | Clean special-wall handoff. |
| 7 | Raikou 73 vs Zapdos 100 | p1 Hidden Power Ice; p2 Snorlax | p2 Snorlax; p1 Hidden Power | both top | HP Ice covered Zapdos and punished Nidoking while still chipping Snorlax. |
| 8 | Raikou 79 vs Snorlax 83 | p1 switch Snorlax answer; p2 strong progress move | p1 Hidden Power; p2 Double-Edge | p1 miss, p2 top | Survivable damage plus recoil can beat immediate pivoting. |
| 9 | Raikou 40 vs Snorlax 69 | p1 Gengar; p2 Earthquake/double if read | p1 Cloyster; p2 Earthquake | p1 miss, p2 top | Choose the absorber that covers the likely coverage branch, not only the obvious STAB. |

## Reusable Lessons

Sleep source is a team resource, not a species label. In modern GSC offense,
Lovely Kiss Snorlax can carry the sleep job, which changes what Exeggutor and
Gengar are trying to do. If a line only works because "Exeggutor probably has
Sleep Powder" or "Gengar probably has Hypnosis," downgrade it unless the move
is revealed or the team structure makes it necessary.

After Sleep Clause is active, the sleeping Pokemon is usually preserved rather
than left in to wake. This replay matched that directly: Exeggutor absorbed
Lovely Kiss and immediately left the field while still blocking further sleep.

Do not auto-switch a healthy Electric out of Snorlax if the damage race is
priced. On turn 8, Raikou survived Double-Edge, added Hidden Power chip, and
made Snorlax pay recoil. The switch became mandatory only after Raikou fell
into KO range.

When switching into Snorlax after Lovely Kiss and Double-Edge are revealed,
cover the likely coverage branch. Gengar covers Normal, but Cloyster covered
the actual Earthquake branch while preserving Gengar.

## Source-To-Policy Extraction

Trigger:
  Early GSC offense where Exeggutor or Gengar could be a sleep carrier, but
  Snorlax has not revealed its set.

Default:
  Treat sleep as an unassigned team resource until revealed. Prefer the move
  that improves the concrete route without assuming a standard sleep move.
  Once sleep lands, preserve the sleeping Pokemon as Sleep Clause material
  unless its active job is worth more.

Exceptions:
  Revealed Sleep Powder, Hypnosis, Sleep Talk, boosted active sleeper,
  immediate wake/action payoff, or a forced damage trade that is better than
  preserving the sleeping slot.

Worst branch:
  The advisor spends the turn chasing a guessed sleep move while the opponent's
  actual sleep source or coverage branch advances the route.

Local status:
  Vanilla GSC replay evidence. Transfer to the romhack only after verifying
  local sleep, Rest, Sleep Talk, and Sleep Clause behavior.

Drill:
  Build a three-prompt regression: lead Exeggutor vs Cloyster with LK Snorlax
  possible; Gengar vs Snorlax with Exeggutor as sleep absorber; low Raikou vs
  Snorlax choosing between HP chip, Gengar, and Cloyster.

## Next Rep

Run a fresh replay transfer focused on unassigned sleep source, post-sleep
doubles, and damage/recoil pricing into Snorlax. The regression artifact is
`quick_tests/unassigned_sleep_source_snorlax_pricing_probe_001_2026-05-14.md`.
