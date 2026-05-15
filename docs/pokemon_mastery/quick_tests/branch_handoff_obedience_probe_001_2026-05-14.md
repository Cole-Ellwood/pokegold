# Branch Handoff Obedience Probe 001 - 2026-05-14

Source parent:
`quick_tests/branch_action_gate_003_smogtours-gen2ou-913366_2026-05-14.md`.

Mode: constructed nonblind policy regression. This checks whether the gate-003
misses can be restated as four compact branch-action choices. It is not fresh
replay-transfer evidence.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/quick_tests/branch_action_gate_003_smogtours-gen2ou-913366_2026-05-14.md`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Branch-found hits: 4 / 4.

Handoff-obedience hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-info errors: 0.

State errors: 0.

Measurement status: regression only. Follow with fresh replay transfer before
treating the handoff-obedience boundary as stable.

## Scenario 1 - Active Pressure Still Beats The Receiver

Public state:

```text
Vanilla GSC spectator-public style. Your Snorlax faces Skarmory around 60%.
Snorlax has Double-Edge revealed. You can name Forretress or another physical
resist as the likely receiver, but Double-Edge still deals useful damage and
keeps Snorlax's route pressure live.
```

Tempting move: switch to a special attacker because Skarmory or Forretress is
the named branch.

Frozen answer: use Double-Edge. Confidence: medium. The branch is real, but
active pressure still beats it enough; a speculative switch can walk into Toxic,
Spikes, phaze, or the wrong receiver.

Classification: named receiver, active pressure still enough.

Score: pass.

## Scenario 2 - Counter-Switch Found And Must Be Obeyed

Public state:

```text
Vanilla GSC spectator-public style. Your Forretress faces Snorlax before you
have set any route-changing support. Snorlax's revealed line is direct
Double-Edge pressure. Skarmory is available and answers that branch without
giving up immediate route value.
```

Tempting move: set Spikes because Forretress is the support piece.

Frozen answer: switch Skarmory. Confidence: medium-high. The branch is Snorlax
continuing direct pressure; the counter-switch is found and should be obeyed
because staying only trades support for avoidable damage.

Classification: counter-switch found and obeyed.

Score: pass.

## Scenario 3 - Found Counter-Switch Rejected

Public state:

```text
Vanilla GSC spectator-public style. Your Snorlax faces Skarmory. You can name
Zapdos or another pressure piece as the counter-switch, but Skarmory's best
branch is Toxic this turn and the pressure piece hates taking that status.
Snorlax can keep damaging Skarmory or its receiver.
```

Tempting move: switch Zapdos because it pressures Skarmory.

Frozen answer: stay and use Double-Edge, or Rest if the poison clock is already
the deciding issue. Confidence: medium. The counter-switch is found but should
be rejected because it walks into the named branch.

Classification: counter-switch found, rejected for branch punish.

Score: pass.

## Scenario 4 - Support Tempting, Damage Or Handoff Better

Public state:

```text
Vanilla GSC spectator-public style. Your Cloyster faces Tyranitar after being
dragged in. Tyranitar is in range where Surf threatens major damage, and the
opponent can either stay to Crunch/Roar or switch to an Electric pressure piece.
Spikes are tempting because Cloyster is the support piece.
```

Tempting move: Spikes because Cloyster finally has a field turn.

Frozen answer: use Surf. Confidence: medium-high. Surf punishes both the stay
and many receivers enough to improve the route now; support is worse if it lets
Tyranitar or the receiver keep initiative.

Classification: support rejected for branch-covering damage.

Score: pass.

## Resulting Checklist

Before choosing into a named branch:

1. Did I actually name the best counter-switch or handoff?
2. If I found it, am I obeying it?
3. If I reject it, what branch punishes that switch?
4. Does active damage already punish both stay and receiver?
5. Is the support move route-changing now, or just the familiar job?

## Next Transfer Check

Run a fresh no-keyword-screen branch-action transfer and score the extra
fields separately: branch found, handoff found, handoff obeyed, and rejection
reason if the handoff is not obeyed.
