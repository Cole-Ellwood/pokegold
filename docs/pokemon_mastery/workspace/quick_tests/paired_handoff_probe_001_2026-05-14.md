# Paired Handoff Probe 001 - 2026-05-14

Source parent:
`workspace/quick_tests/setup_coverage_sleeptalk_handoff_transfer_001_smogtours-gen2ou-914178_2026-05-14.md`.

Mode: constructed nonblind policy regression. This turns the paired-handoff
misses from the 914178 transfer into four compact branch-action choices. It is
not fresh replay evidence.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`
- `docs/pokemon_mastery/workspace/quick_tests/setup_coverage_sleeptalk_handoff_transfer_001_smogtours-gen2ou-914178_2026-05-14.md`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Paired-handoff hits: 4 / 4.

Receiver-damage hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Follow with fresh replay transfer before
treating paired handoff as stable.

## Scenario 1 - Sleep Branch Double Handoff

Public state:

```text
Vanilla GSC spectator-public style. Your Snorlax faces Exeggutor on turn 1.
You can name Exeggutor's sleep or status branch, so your obvious line is a
sleep absorber such as Umbreon. The opponent can also read that and hand off
Exeggutor to a support piece such as Forretress.
```

Tempting move: switch the sleep absorber and stop thinking.

Frozen answer: switch the absorber only after naming the opponent's likely
counter-handoff. Confidence: medium. If the support handoff is best for them,
your next plan must already cover Spikes or Forretress pressure.

Classification: sleep branch creates paired handoff.

Score: pass.

## Scenario 2 - Spinblock Handoff

Public state:

```text
Vanilla GSC spectator-public style. Your Starmie faces Forretress after Spikes
are set. Rapid Spin is the obvious first-order action. The opponent may have a
Ghost handoff even if the Ghost was not visible before this cycle.
```

Tempting move: Rapid Spin without pricing the opponent's handoff.

Frozen answer: Rapid Spin is still reasonable, but the branch bundle must name
the spinblock handoff and the next action if Gengar or another Ghost enters.
Confidence: medium.

Classification: hazard branch with spinblock counter-handoff.

Score: pass.

## Scenario 3 - Active Pressure Hits Receiver Enough

Public state:

```text
Vanilla GSC spectator-public style. Your Skarmory faces Exeggutor. You can name
Forretress as the likely receiver, but Drill Peck or the active attack still
does route-relevant damage to the receiver.
```

Tempting move: choose generic Toxic only because a receiver is likely.

Frozen answer: use the active attack when it punishes both stay and receiver
better than speculative utility. Confidence: medium.

Classification: active pressure into receiver.

Score: pass.

## Scenario 4 - Setup After Naming Handoff Out

Public state:

```text
Vanilla GSC spectator-public style. Your Shuckle has just absorbed a missed
Lovely Kiss from Snorlax. Snorlax can switch to a support answer such as
Forretress, while Shuckle can either make direct progress or use its setup
route.
```

Tempting move: Toxic or switch immediately because Shuckle looks passive.

Frozen answer: setup is only correct if you first name the opponent's handoff
out and the setup changes that next board. Confidence: low-medium. Do not
choose setup as a script; choose it when it improves the post-handoff route.

Classification: setup after handoff-out is named.

Score: pass.

## Resulting Checklist

Before taking the obvious handoff:

1. What is my handoff?
2. What is their counter-handoff if I take it?
3. Does my active move still punish their receiver enough?
4. If I set up, how does the boost change the next board after their handoff?

## Next Transfer Check

Run a fresh no-keyword-screen branch-action transfer and score paired-handoff
bundles separately from normal top/acceptable move agreement.
