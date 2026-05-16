# Coverage Reveal Absorber Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression. This is not a fresh replay score
or final-exam evidence.

Purpose: convert `replay_turn_pause_049` into three forced choices around
coverage reveals, support order, and sleeping absorber pivots.

Local docs checked:

- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_049_coverage_reveal_absorber_smogtours-gen2ou-924921_2026-05-14.md`

Web sources checked in the parent work block:

- Smogon Forums, GSC OU Skarmory:
  `https://www.smogon.com/forums/threads/gsc-ou-skarmory.3709334/`
- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, GSC Zapdos:
  `https://www.smogon.com/forums/threads/gsc-zapdos.3674240/`
- Smogon Forums, GSC OU Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`

## Score Summary

Scenarios: 3.

Action-policy hits: 3 / 3.

Classification hits: 3 / 3.

Route-job hits: 3 / 3.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. This should be followed by a fresh replay
transfer before treating the coverage-reveal branch as learned.

## Scenario 1 - Coverage Reveal Invalidates Clean Answer

Public state:

```text
Vanilla GSC. Opposing Snorlax is active at high HP and has just revealed Fire
Blast into our Cloyster switch. Before this reveal, Cloyster looked like a
reasonable support answer. Cloyster survived at mid HP.
```

Tempting update: keep treating Cloyster as a clean answer because it entered.

Frozen answer: re-solve immediately. Confidence: high.

Classification: coverage reveal. Cloyster can still act once, but it is no
longer a durable Snorlax answer.

Score: pass.

## Scenario 2 - Support Before Cash-Out

Public state:

```text
Vanilla GSC. Our Cloyster is at mid HP against a Snorlax that has revealed Fire
Blast. No Spikes are on the opponent's side. Cloyster has Spikes and Explosion.
```

Tempting move: Explosion immediately because Fire Blast will remove Cloyster.

Frozen answer: Spikes. Confidence: medium.

Classification: support before cash-out. If Cloyster is fast enough to deliver
the layer before being removed, the layer can improve every later pivot before
Explosion is considered.

Score: pass.

## Scenario 3 - Sleeping Absorber Preserves The Route Piece

Public state:

```text
Vanilla GSC. Our Snorlax has just revealed Fire Blast into opposing Cloyster,
but Cloyster survived and can threaten Explosion. Our Moltres is asleep, has
Rest and Sleep Talk revealed, and is a lower-value absorber than Snorlax in the
current route.
```

Tempting move: keep attacking with Fire Blast.

Frozen answer: switch sleeping Moltres. Confidence: medium.

Classification: sleeping absorber trade. Moltres does not enter to wake or
convert immediately; it enters to protect Snorlax from Explosion while keeping
Sleep Clause active.

Score: pass.

## Resulting Checklist

After a coverage reveal:

1. Which prior hard answer is now invalid?
2. Can the invalidated answer still deliver one support action?
3. Does the coverage user now need protection from Explosion or a one-time
   trade?
4. Is there a lower-value sleeping absorber that preserves the real route
   piece and keeps Sleep Clause active?

## Next Study Target

Fresh replay transfer with both clean-answer and coverage-reveal branches:
counter-setup while coverage is unrevealed, then re-solve to absorber or phaze
after coverage appears.
