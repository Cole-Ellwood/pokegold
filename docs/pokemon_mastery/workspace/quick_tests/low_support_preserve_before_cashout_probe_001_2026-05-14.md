# Low Support Preserve Before Cashout Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression. This is not a fresh replay score
or final-exam evidence.

Purpose: convert `replay_turn_pause_055` into forced choices around low
Cloyster preservation, Toxic before Explosion, Ghost pivoting, and Thief as a
Ghost-matchup progress move.

Local docs checked:

- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_055_low_cloyster_preserve_ghost_pivot_smogtours-gen2ou-922579_2026-05-14.md`

Web sources checked in the parent work block:

- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, Explosion in GSC:
  `https://www.smogon.com/forums/threads/explosion-in-gsc-qc-2-2-gp-2-2.3484961/`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`

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

## Scenario 1 - Preserve Zapdos With Cloyster

Public state:

```text
Vanilla GSC. Zapdos leads into Snorlax. Snorlax has not revealed its set, but
Double-Edge is a serious immediate branch. Cloyster is available and can absorb
Double-Edge while still setting Spikes.
```

Tempting move: keep Zapdos in and Thunder immediately.

Frozen answer: switch Cloyster if preserving Zapdos is worth more than one
Thunder attempt and Cloyster still gets a support turn afterward. Confidence:
medium.

Classification: lower-value absorber preserves Electric route.

Score: pass.

## Scenario 2 - Toxic Before Boom At 48

Public state:

```text
Vanilla GSC. Cloyster has set Spikes and is at 48% in front of Snorlax.
Snorlax is still healthy and has shown Double-Edge. Cloyster has Toxic and
Explosion.
```

Tempting move: Explosion because Cloyster is low and Snorlax is valuable.

Frozen answer: Toxic is live if it changes Snorlax's route and Cloyster can
still preserve or cash out later. Confidence: medium.

Classification: support status before cash-out.

Score: pass.

## Scenario 3 - Preserve Low Cloyster With Ghost Pivot

Public state:

```text
Vanilla GSC. Cloyster is at 23% after missing Toxic. Snorlax is active, but
the opponent has a likely Ghost or absorber for Explosion. You have Gengar
available and no hazard on your side.
```

Tempting move: Explosion because Cloyster may not get another chance.

Frozen answer: switch Gengar if it preserves Cloyster's one-time trade and
covers the opponent preserving Snorlax with a Ghost. Confidence: medium.

Classification: double-preservation cash-out delay.

Score: pass.

## Scenario 4 - Thief As Ghost Progress

Public state:

```text
Vanilla GSC. Gengar is active against Misdreavus after both sides preserved
their central pieces. Misdreavus is a spinblock/Normal-immunity route piece and
has Leftovers. Gengar has Thief.
```

Tempting move: reduce Gengar's options to Thunder, Hypnosis, Explosion, or
switch.

Frozen answer: use Thief if item removal weakens Misdreavus's long-term job or
improves the later hazard/Explosion map. Confidence: medium-high.

Classification: item-removal progress in Ghost matchup.

Score: pass.

## Resulting Checklist

When a low support Pokemon wants to cash out:

1. Is low HP the only reason to Explode?
2. Is Toxic, Spin, Surf, Thief, or a pivot still a real route move?
3. Can both sides preserve their main route piece on the same turn?
4. Does a Ghost pivot keep the one-time trade available for later?
5. Is item removal a route move in the Ghost matchup?

## Next Study Target

Fresh replay transfer focused on low-support preservation before cash-out.
