# Hazard Loop Spin Window Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression. This is not a fresh replay score
or final-exam evidence.

Purpose: convert `replay_turn_pause_054` into forced choices around preserving
Cloyster from Zapdos lead pressure, using Cloyster as a lower-value Snorlax
absorber, choosing Rapid Spin on a predicted Explosion absorber switch, and
re-solving after the opponent resets Spikes.

Local docs checked:

- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_054_hazard_loop_spin_window_smogtours-gen2ou-922676_2026-05-14.md`

Web sources checked in the parent work block:

- Smogon Forums, GSC OU Steelix:
  `https://www.smogon.com/forums/threads/gsc-ou-steelix.3705042/`
- Smogon Forums, Explosion in GSC:
  `https://www.smogon.com/forums/threads/explosion-in-gsc-qc-2-2-gp-2-2.3484961/`
- Smogon Forums, Is Snorlax Banworthy in GSC OU?:
  `https://www.smogon.com/forums/threads/is-snorlax-banworthy-in-gsc-ou.3541958/`

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

## Scenario 1 - Preserve Cloyster From Zapdos Lead Pressure

Public state:

```text
Vanilla GSC. Our lead Cloyster faces opposing lead Zapdos. No hazards are up.
Cloyster can set Spikes, but Zapdos can immediately Thunder and force heavy
damage. Raikou is available as the Electric answer.
```

Tempting move: set Spikes because Cloyster is the lead support piece.

Frozen answer: switch Raikou if preserving Cloyster's later Spikes, Spin,
Explosion, or Snorlax-absorber job is worth more than the immediate layer.
Confidence: medium.

Classification: support preservation before first layer.

Score: pass.

## Scenario 2 - Preserve Raikou With Lower-Value Cloyster

Public state:

```text
Vanilla GSC. Raikou is healthy in front of Snorlax. Snorlax has revealed
Double-Edge. Cloyster is available and can still set or remove Spikes later.
```

Tempting move: leave Raikou in to Thunder once.

Frozen answer: switch Cloyster if Raikou is the longer-term Electric answer
and Cloyster can absorb Double-Edge without losing a larger route. Confidence:
medium-high.

Classification: lower-value absorber preserves route piece.

Score: pass.

## Scenario 3 - Spin On The Predicted Boom Absorber

Public state:

```text
Vanilla GSC. Our Cloyster is low, has already set Spikes, and our side also has
Spikes. Opposing Snorlax is active and valuable. The opponent has a healthy
Cloyster that can switch into a likely Explosion as a lower-value absorber.
Our Cloyster has Rapid Spin.
```

Tempting move: Explosion because Cloyster is low and Snorlax is valuable.

Frozen answer: Rapid Spin if the opponent is likely to cover Explosion by
switching the absorber and if clearing Spikes changes the route. Confidence:
medium.

Classification: predicted-cash-out Spin window.

Score: pass.

## Scenario 4 - Re-Solve After The Reset Layer

Public state:

```text
Vanilla GSC. Our Cloyster used Rapid Spin on the opposing Cloyster switch. The
opponent's Cloyster reset Spikes immediately. Both Cloysters remain active,
and our Raikou is available but hates Toxic.
```

Tempting move: repeat Rapid Spin automatically or hand off automatically.

Frozen answer: re-rank Surf chip, Toxic, another Spin, Raikou handoff, or
Explosion. If Toxic into Raikou is likely and another Spin does not stick,
direct support pressure can be better than repeating the previous answer.
Confidence: medium.

Classification: hazard-loop re-solve after reset.

Score: pass.

## Resulting Checklist

When Cloyster is low in a hazard loop:

1. Is immediate Spikes worth losing Cloyster's later support job?
2. Which route piece is being preserved by using Cloyster as absorber?
3. If Explosion is obvious, who is the expected absorber?
4. Does that absorber switch make Rapid Spin clean?
5. After Spin, did the opponent reset the layer or change the support mirror?
6. Is the next support move Spin, Surf, Toxic, handoff, or Explosion?

## Next Study Target

Fresh replay transfer focused on hazard-loop Spin windows after support-cash-out
threats.
