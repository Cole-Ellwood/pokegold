# Setup Coverage SleepTalk Handoff Probe 001 - 2026-05-14

Source parent:
`workspace/quick_tests/branch_cashout_coverage_sleeptalk_transfer_001_smogtours-gen2ou-914172_2026-05-14.md`.

Mode: constructed nonblind policy regression. This turns the 914172 transfer
misses into four compact branch-action boundaries. It is not fresh replay
evidence.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/workspace/quick_tests/branch_cashout_coverage_sleeptalk_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/branch_cashout_coverage_sleeptalk_transfer_001_smogtours-gen2ou-914172_2026-05-14.md`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Branch-class hits: 4 / 4.

Handoff-order hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Follow with fresh replay transfer before
treating this boundary as stable.

## Scenario 1 - Setup Before Active Pressure

Public state:

```text
Vanilla GSC spectator-public style. Your Snorlax faces Cloyster on turn 1.
Cloyster is very likely to set Spikes. Snorlax can either attack immediately or
Curse before attacking.
```

Frozen answer: use Curse when the expected support turn lets Snorlax improve
the next board more than immediate chip. Confidence: medium. Active damage is
correct if Cloyster is about to Toxic, Explode, or deny setup value.

Classification: setup before active pressure.

Score: pass.

## Scenario 2 - Receiver After Revealed Coverage

Public state:

```text
Vanilla GSC spectator-public style. Your Snorlax has revealed Thunder into
Cloyster. The opponent can now answer with a Ground immunity receiver such as
Golem. Snorlax also has a physical move or coverage that can punish that
receiver.
```

Frozen answer: after Thunder is revealed, price the Ground receiver before
repeating Thunder. Confidence: medium. Use the branch-covering attack or switch
when the receiver is now the best branch.

Classification: revealed coverage creates receiver branch.

Score: pass.

## Scenario 3 - SleepTalk Stay Versus Phaze Handoff

Public state:

```text
Vanilla GSC spectator-public style. Your RestTalk Snorlax is asleep against
Tyranitar. Sleep Talk lets Snorlax stay active, but Tyranitar has shown or
strongly represents Roar.
```

Frozen answer: do not auto-stay just because Sleep Talk exists. Confidence:
medium. Price Roar first; if phaze plus Spikes is the punishing branch, hand
off to the Tyranitar answer instead of burning a Sleep Talk turn.

Classification: SleepTalk stay rejected by phaze branch.

Score: pass.

## Scenario 4 - Paired Handoff

Public state:

```text
Vanilla GSC spectator-public style. Your Zapdos has been dragged into
Tyranitar. Golem is the obvious Tyranitar answer, but the opponent can also
switch Tyranitar out to a poisoned Electric or other next-board answer.
```

Frozen answer: name both handoffs before switching. Confidence: medium. If the
opponent's counter-handoff is the best branch, the exact answer may be a
different special wall or pivot rather than the obvious Tyranitar answer.

Classification: paired handoff before exact switch.

Score: pass.

## Resulting Checklist

Before committing to a switch:

1. Does setup beat immediate pressure because the support turn is predictable?
2. Has revealed coverage created a new receiver that must be priced?
3. Does Sleep Talk stay lose to phaze, hazard, or setup handoff?
4. What is the opponent's handoff if I make the obvious handoff?

## Next Transfer Check

Run a fresh no-keyword-screen branch-action transfer and score setup-before-
pressure, revealed-coverage receiver, SleepTalk stay versus phaze handoff, and
paired handoff separately.
