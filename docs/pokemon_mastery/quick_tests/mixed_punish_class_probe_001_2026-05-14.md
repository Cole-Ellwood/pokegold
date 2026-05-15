# Mixed Punish Class Probe 001 - 2026-05-14

Source parent:
`quick_tests/replay_turn_pause_073_mixed_receiver_action_transfer_smogtours-gen2ou-917839_2026-05-14.md`.

Mode: constructed nonblind policy regression. This checks whether replay 073's
move-class punish misses can be restated as forced branch-action choices. It is
not fresh replay-transfer evidence.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_073_mixed_receiver_action_transfer_smogtours-gen2ou-917839_2026-05-14.md`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Classification hits: 4 / 4.

Route-job hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Follow with fresh replay transfer before
treating mixed punish-class handling as stable.

## Scenario 1 - Immunity Into DynamicPunch

Public state:

```text
Vanilla GSC spectator-public state. Your paralyzed Snorlax faces opposing
Dragonite at 48%. Dragonite has revealed Thunder Wave and DynamicPunch. Your
Gengar is healthy enough to enter through Spikes and is immune to DynamicPunch.
```

Tempting move: Double-Edge because Dragonite is low and Snorlax can remove it.

Frozen answer: switch Gengar when DynamicPunch is the best-priced punish and
the Ghost entry preserves Snorlax while blanking the move. Attack only when
Dragonite cannot act or when Gengar's entry loses to a stronger revealed branch.
Confidence: medium-high.

Classification: immunity into move-class punish.

Score: pass.

## Scenario 2 - Coverage Still Punishes The Receiver

Public state:

```text
Vanilla GSC spectator-public state. Your Gengar faces opposing Dragonite at
54%. Dragonite can switch to Raikou as the Gengar receiver. Gengar has Ice
Punch, and Raikou is taking Spikes on entry.
```

Tempting move: double-switch because Raikou is the receiver.

Frozen answer: use Ice Punch when it KOs or heavily pressures Dragonite and
still deals route-relevant damage to the Raikou receiver after Spikes. Confidence:
medium.

Classification: coverage into receiver.

Score: pass.

## Scenario 3 - Avoid The Explosion Absorber

Public state:

```text
Vanilla GSC spectator-public state. Your Gengar faces opposing Raikou at 64%.
Spikes are on both sides. Opponent has Golem unrevealed or recently revealed as
a possible Normal-resistant absorber. Gengar can Explode or switch to Snorlax.
```

Tempting move: Explosion because Raikou is valuable and in range after Spikes.

Frozen answer: do not blindly Explode if Golem is the best-priced absorber.
Switch or use a non-boom move unless the route still improves if Golem takes
the Explosion. Confidence: medium.

Classification: avoid resisted cash-out absorber.

Score: pass.

## Scenario 4 - Cash Out Into The Receiver

Public state:

```text
Vanilla GSC spectator-public state. Your Cloyster faces opposing Golem at 59%.
Spikes are on both sides. Surf threatens Golem, but the opponent can switch low
Dragonite as the receiver. Cloyster has already set Spikes, and Explosion can
remove Dragonite if it enters.
```

Tempting move: Surf because Golem is active and weak to it.

Frozen answer: Explosion when the Dragonite receiver is the route-defining
branch and Cloyster's support job is complete enough to spend. Surf is correct
when Golem staying is the branch that matters or the Dragonite receiver is not
worth the trade. Confidence: medium.

Classification: cash out into predicted receiver.

Score: pass.

## Resulting Checklist

After naming a move-class punish:

1. Is there an immunity that blanks the punish without losing the route?
2. Does coverage still hit both the active target and the receiver well enough?
3. Can the opponent route Explosion into an absorber?
4. Is cash-out correct because the receiver is the real target?
5. What non-primary branch would make this action class wrong?

## Next Transfer Check

Run a fresh no-keyword-screen replay packet with
`branch_action_after_naming.md` loaded. Score whether move-class punish reads
select immunity, absorber avoidance, coverage, or cash-out correctly under
unseen pressure.
