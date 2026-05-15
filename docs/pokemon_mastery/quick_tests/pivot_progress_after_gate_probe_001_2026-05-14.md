# Pivot Progress After Gate Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression. This is not a fresh replay score
or final-exam evidence.

Purpose: convert `replay_turn_pause_044` into a four-prompt check. After a
serious pivot is named, the answer must decide whether to double, attack the
active target, or use an active progress move that still improves through the
expected response.

Local docs checked:

- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_044_active_target_after_pivot_gate_smogtours-gen2ou-929268_2026-05-14.md`

Web sources checked in the parent work block:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Pokemon Showdown ladder help:
  `https://pokemonshowdown.com/pages/ladderhelp`
- Smogon Forums, GSC OU Discussion Thread page 3:
  `https://www.smogon.com/forums/threads/gsc-ou-discussion-thread.3688141/page-3`
- Smogon Forums, An Analysis of Leads in GSC OU:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Pivot-progress classification hits: 4 / 4.

Route-job hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. These prompts are constructed from a
known failure class and should be followed by a fresh replay transfer.

## Scenario 1 - Active Attack Is Too Easy To Cover

Public state:

```text
Vanilla GSC. Opponent Zapdos is active at 100% against our Skarmory at 80%.
Our Raikou is revealed and healthy. Opponent Snorlax is revealed at 96% with
Curse and Double-Edge. No Spikes are down.
```

Named serious branch: we switch Skarmory to Raikou to cover Zapdos's Electric
attack.

Tempting move: Zapdos Thunder into Skarmory.

Frozen answer: opponent should double to Snorlax. Confidence: medium.

Classification: double. The active attack is real, but it is cleanly covered
by the already revealed Raikou response. Snorlax regains the active route
against Raikou and forces the next defensive choice.

Score: pass.

## Scenario 2 - Active Progress Beats The Immediate Double

Public state:

```text
Vanilla GSC. Opponent Snorlax is active at 100% against our Raikou at 100%.
Snorlax has Curse and Double-Edge revealed. Our Skarmory is revealed at 80% and
has Whirlwind revealed. Opponent Zapdos is revealed at 100%.
```

Named serious branch: we switch Raikou to Skarmory.

Tempting move: opponent doubles to Zapdos because Skarmory is likely.

Frozen answer: opponent can use Curse. Confidence: medium.

Classification: active progress. Curse does not only hit the current target;
it improves Snorlax's board through the expected Skarmory response and keeps
the Snorlax route live. The Zapdos double is playable, but it is not mandatory
just because the pivot is obvious.

Score: pass.

## Scenario 3 - Phaze The Active Route Before Admiring The Pivot

Public state:

```text
Vanilla GSC. Our Skarmory is active at 86% against +1 Attack / +1 Defense
Snorlax at 100%. Skarmory has Whirlwind revealed. Opponent Zapdos is revealed
at 100%. No Spikes are down.
```

Named serious branch: opponent may switch Snorlax out to Zapdos to escape the
Skarmory seat.

Tempting move: double to Raikou immediately.

Frozen answer: use Whirlwind or a direct anti-setup action first. Confidence:
medium-high.

Classification: active route denial. The current +1 Snorlax is the route that
must be reset. If the opponent switches manually, Snorlax's boost route is
already interrupted; if it stays, Whirlwind denies the setup.

Score: pass.

## Scenario 4 - Own-Team Information Can Beat Spectator-Public Generic Play

Public state:

```text
Vanilla GSC, side-known mode. Our Skarmory is active at 86% against +1
Snorlax at 100%. We know our own Misdreavus is healthy in reserve. Snorlax has
Curse and Double-Edge revealed but has not revealed Earthquake, Lovely Kiss,
or Rest. No Spikes are down.
```

Named serious branch: Snorlax uses Double-Edge or keeps boosting.

Tempting move: Whirlwind with Skarmory because it is the spectator-public
generic answer.

Frozen answer: switch Misdreavus. Confidence: medium.

Classification: side-known answer. The player knows the Ghost pivot exists,
and it converts Double-Edge from pressure into a blank turn while preserving
Skarmory. This answer should not be demanded in spectator-public scoring
unless the own-team sheet is supplied.

Score: pass.

## Resulting Checklist

Before finalizing a move after the named-pivot gate:

1. Is the active option only damage into the current target, or does it also
   change the next board?
2. If the expected response cleanly covers the active attack, consider the
   double.
3. If setup, status, phazing, trapping, or recovery improves through the
   expected response, do not double automatically.
4. If own-team information supplies a cleaner answer than spectator-public
   state, record the mode difference instead of calling it a hidden-info miss.

## Next Study Target

Fresh replay transfer with a `classification` column:

```text
active attack / active progress / double / route denial / side-known answer
```
