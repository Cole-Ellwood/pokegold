# Rest Curse Tempo Window Drill 001 - 2026-05-15

Mode: constructed nonblind regression from side-known packet 005 and older
policy-card archive. This is not fresh progress evidence.

Sources reviewed:
- `policy_cards/branch_action_after_naming.md` boosted-timer and CurseLax
  Rest-clock extensions.
- `policy_cards/sleep_absorber_and_set_ambiguity.md` Rest wake-count and
  RestTalk pressure extensions.
- `policy_cards/hazard_loop_spin_window.md` Steelix phaze/setup split.
- Smogon Forums, [GSC OU Steelix](https://www.smogon.com/forums/threads/gsc-ou-steelix.3705042/).
- Smogon Forums, [GSC OU Snorlax](https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/).

## Score Summary

Scenarios: 8.

Route-intent match: 8/8.

Exact-move match: 8/8.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Verdict: regression pass only. The drill is useful retrieval practice, not
fresh replay proof.

## Scenarios

1. Steelix at +2 faces CurseLax at 67%, Spikes on the opponent side, and Lax
   can Rest before the next hit. Top: Rock Slide or lowest-cost attack that
   preserves PP while forcing Rest. Route intent: force reset, not overboost.
2. Steelix at +2 faces freshly Rested non-SleepTalk CurseLax at full HP.
   Attacking does not change the next forced choice. Top: Curse. Route intent:
   spend the free sleep turn improving the future damage range.
3. Steelix at +3 faces sleeping CurseLax on the second sleeping action turn and
   Earthquake will force a low wake board. Top: Earthquake. Route intent: cash
   the boost before wake action reopens Rest/Curse.
4. Steelix at +4 faces freshly Rested CurseLax at full HP and no phazer is
   revealed. Top: Earthquake, not another Curse. Route intent: convert the
   already banked boosts before extra setup stops changing the route.
5. Steelix with Roar revealed has Spikes down and faces a boosted CurseLax that
   cannot KO before negative-priority Roar. Top: Roar. Route intent: deny the
   setup loop with hazard conversion.
6. The same Steelix faces boosted CurseLax after Earthquake coverage has shown
   that Steelix drops before Roar resolves. Top: handoff or Explosion branch
   if revealed, not Roar autopilot. Route intent: reprice the damage clock.
7. CurseLax faces RestTalk Electric pressure after one boost; the next Thunder
   forces Rest if it hits. Top: Rest if staying preserves the boosted route;
   Curse only if the extra boost changes the post-Rest board. Route intent:
   avoid boosting into a forced reset.
8. RestTalk Snorlax is sleeping with Double-Edge and Earthquake public while a
   Ghost wants to enter. Top: use the Steel/Rock/Cloyster-style absorber or
   pressure move that survives both Sleep Talk rolls; Ghost is conditional only
   after coverage is public absent. Route intent: branch-price the sleep turn.

## Reusable Rule

In setup-versus-Rest positions, do not ask "is damage good?" Ask whether this
turn changes the next forced choice. If it does not, boost, phaze, hand off, or
preserve the route piece instead of recording cosmetic chip.
