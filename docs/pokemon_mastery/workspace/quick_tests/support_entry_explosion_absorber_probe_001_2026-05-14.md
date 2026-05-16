# Support Entry Explosion Absorber Probe 001 - 2026-05-14

Mode: constructed nonblind policy regression. This is not a fresh replay score
or final-exam evidence.

Purpose: convert `replay_turn_pause_051` into three forced choices around
support-seat entry and side-known Explosion absorption.

Local docs checked:

- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_progress_ledger.csv`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_051_support_entry_explosion_absorber_smogtours-gen2ou-923748_2026-05-14.md`

Web sources checked in the parent work block:

- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, Forretress OU Revamp:
  `https://www.smogon.com/forums/threads/forretress-ou-revamp-done.3647111/`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC forum index:
  `https://www.smogon.com/forums/forums/gsc/`

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
transfer before treating the support-entry branch as stable.

## Scenario 1 - Support Seat Before Hard Answer

Public state:

```text
Vanilla GSC. Our Steelix is active against opposing Machamp. Exeggutor is
revealed and is the obvious Fighting-resistant hard answer. Cloyster is also
available and can set Spikes before being heavily pressured.
```

Tempting move: switch Exeggutor because it is the hard answer.

Frozen answer: switch Cloyster if the plan needs the support seat now.
Confidence: medium.

Classification: support-seat entry. The correct response tree is not only
hard answer versus active attack; support can enter first if the support action
changes the route before the active threat punishes it.

Score: pass.

## Scenario 2 - Low Cloyster Explosion Is Live

Public state:

```text
Vanilla GSC. Cloyster has set Spikes and is now at 40% against Machamp.
Machamp threatens to KO with Cross Chop if Cloyster stays passive. Cloyster has
Explosion available.
```

Tempting move: preserve Cloyster because it set Spikes.

Frozen answer: Explosion is live and must be covered. Confidence: high.

Classification: support cash-out. Once the support job is delivered and the
support piece is low, the one-time trade is a serious branch.

Score: pass.

## Scenario 3 - Side-Known Ghost Absorber

Public state:

```text
Vanilla GSC, side-known mode. The opponent's low Cloyster has set Spikes and
is likely to Explode into our Machamp. We have a healthy Gengar in reserve and
Gengar is not our only remaining answer to a higher-value threat.
```

Tempting move: attack with Machamp because the public prompt cannot prove a
Ghost is available.

Frozen answer: switch Gengar. Confidence: high.

Classification: side-known Explosion absorber. Spectator-public study can
only name Explosion as live; player-side advice must use the known Ghost if
the lost Gengar role is acceptable.

Score: pass.

## Resulting Checklist

When a support piece enters against an active threat:

1. Did it enter because it is the hard answer, or because the support seat
   matters now?
2. After support resolves, is Explosion or another one-time trade live?
3. In spectator-public mode, can the absorber be known?
4. In side-known mode, is the Ghost or lower-value absorber available without
   losing a larger route?

## Next Study Target

Fresh replay transfer with support-entry, support-coverage, and Explosion
absorber classifications together.
