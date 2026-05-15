# Mixed Cashout Sleep Handoff Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression. This is not a fresh replay score
or final-exam evidence.

Purpose: convert `replay_turn_pause_057` into forced choices around Snorlax
set ambiguity, sleep absorber preservation, Explosion absorber selection, and
support handoff after Spikes.

Local docs checked:

- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_057_sleep_absorber_trade_handoff_smogtours-gen2ou-922568_2026-05-14.md`

Web sources checked in the parent work block:

- Smogon Forums, An Analysis of Leads in GSC OU:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`
- Smogon Forums, Explosion in GSC:
  `https://www.smogon.com/forums/threads/explosion-in-gsc-qc-2-2-gp-2-2.3484961/`
- Smogon Forums, GSC Zapdos:
  `https://www.smogon.com/forums/threads/gsc-zapdos.3674240/`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Classification hits: 4 / 4.

Route-job hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Follow with a fresh replay transfer
before treating this as stable.

## Scenario 1 - Curse Does Not Rule Out Lovely Kiss

Public state:

```text
Vanilla GSC. Snorlax mirror. Our Snorlax used Curse on turn 1 and took
Double-Edge. Opponent can bring a support Pokemon such as Forretress as a sleep
absorber if Lovely Kiss is live.
```

Tempting move: remove Lovely Kiss from the set model because Curse was already
shown.

Frozen answer: keep Lovely Kiss live until the set is actually narrowed by
reveals or a team sheet. Confidence: medium.

Classification: Snorlax set ambiguity.

Score: pass.

## Scenario 2 - Preserve Sleeping Support

Public state:

```text
Vanilla GSC. Forretress absorbed Lovely Kiss and is now asleep in front of a
boosted Snorlax. Forretress has not revealed Sleep Talk. Sleep Clause now
blocks further induced sleep.
```

Tempting move: leave Forretress in to burn sleep turns.

Frozen answer: switch Forretress out unless its active board job beats
preserving Sleep Clause and future support. Confidence: high.

Classification: sleep-clause support preservation.

Score: pass.

## Scenario 3 - Preserve The Boosted Route From Explosion

Public state:

```text
Vanilla GSC. Boosted Lovely Kiss Snorlax is active against weakened Exeggutor.
Exeggutor can Explode. Zapdos is available and less important than preserving
Snorlax's boosted route.
```

Tempting move: keep Snorlax in because it is the active route piece.

Frozen answer: switch Zapdos or another acceptable absorber if that preserves
the boosted Snorlax route. Confidence: medium.

Classification: defensive absorber selection against route trade.

Score: pass.

## Scenario 4 - Handoff After Spikes

Public state:

```text
Vanilla GSC. Cloyster has just set Spikes against Tyranitar and is at enough HP
to attack once. Machamp is available and pressures the Tyranitar/Snorlax route,
but Zapdos may enter against Machamp.
```

Tempting move: Surf Tyranitar because it is the active target.

Frozen answer: hand off if Machamp creates the stronger next board and
Cloyster's HP/support job is worth preserving. Confidence: medium.

Classification: support handoff before direct damage.

Score: pass.

## Resulting Checklist

For mixed cash-out and support turns:

1. Did the first Snorlax reveal actually rule out sleep?
2. Is the slept support Pokemon more valuable asleep in reserve?
3. If Explosion is live, which route piece should absorb it?
4. After support lands, is direct damage or handoff the route move?
5. Does the handoff invite a predictable counter-pivot that must be priced?

## Next Study Target

Fresh replay transfer on mixed cash-out decisions: set ambiguity, sleeper
preservation, absorber selection, and support handoff.
