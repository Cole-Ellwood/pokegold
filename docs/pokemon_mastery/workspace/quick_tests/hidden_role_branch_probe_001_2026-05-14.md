# Hidden Role Branch Probe 001 - 2026-05-14

Source parent:
`workspace/quick_tests/replay_turn_pause_066_branch_action_transfer_smogtours-gen2ou-920441_2026-05-14.md`.

Mode: constructed nonblind policy regression. This checks whether replay 066's
hidden-role and branch-action misses can be restated as forced choices. It is
not fresh replay-transfer evidence.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/hazard_loop_spin_window.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_066_branch_action_transfer_smogtours-gen2ou-920441_2026-05-14.md`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Classification hits: 4 / 4.

Route-job hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Follow with a fresh replay transfer from a
different player pair before treating this as stable.

## Scenario 1 - Snorlax Mirror Hard Answer Before Sleep Script

Public state:

```text
Vanilla GSC spectator-public state. Your Snorlax leads into opposing Snorlax.
You have Skarmory available. No sleep has been used. Opposing Snorlax may have
Lovely Kiss, but Double-Edge or early Curse pressure is also live. Your Snorlax
is valuable later and does not need to win the mirror immediately.
```

Tempting move: Lovely Kiss because Snorlax often carries sleep and sleep is
powerful.

Frozen answer: switch Skarmory or another hard answer if the immediate
Double-Edge/Curse branch is the more concrete punish. Sleep is a route tool, not
a default script for every Snorlax mirror. Confidence: medium.

Classification: hard-answer handoff before sleep over-script.

Score: pass.

## Scenario 2 - Counter-Switch Into Named Snorlax Receiver

Public state:

```text
Vanilla GSC spectator-public state. Your Raikou is active against opposing
Cloyster. You expect Cloyster to leave for Snorlax rather than stay into
Electric pressure. Forretress is available and can enter on Snorlax to scout,
set support, or force a different branch.
```

Tempting move: Thunder because it is active pressure and still chips some
receivers.

Frozen answer: counter-switch Forretress if Snorlax is the named best branch.
Thunder is correct only if Cloyster staying is likely enough or if the Snorlax
chip changes a concrete route more than meeting the receiver. Confidence:
medium.

Classification: named receiver requires counter-switch, not generic pressure.

Score: pass.

## Scenario 3 - Protect Before Spinning Into Revealed Gengar

Public state:

```text
Vanilla GSC spectator-public state. Your Forretress is at 64% against a poisoned
Cloyster. Spikes are on both sides. Gengar has been revealed on the opponent's
team and can block Rapid Spin. Forretress has Protect and Leftovers.
```

Tempting move: Rapid Spin immediately before Forretress takes more Surf damage.

Frozen answer: Protect when the Gengar switch is live and scouting plus
Leftovers changes the next branch. Spin is correct when Cloyster staying is the
best branch or when the Ghost has no realistic entry; here Protect prices both
Cloyster staying and Gengar entering. Confidence: medium.

Classification: scout the spinblock branch before committing Spin.

Score: pass.

## Scenario 4 - Misdreavus Into Golem Rapid Spin

Public state:

```text
Vanilla GSC spectator-public state. Your Skarmory is active against opposing
Golem. Spikes are on both sides. Golem can threaten Explosion or Rock Slide, but
Rapid Spin is also a live support role because it removes your hazard progress.
You have Misdreavus available.
```

Tempting move: Whirlwind because Skarmory is healthy and hazards are up.

Frozen answer: switch Misdreavus if Rapid Spin is the branch that most damages
your route. Phazing is useful only if the spinner branch is less important or if
the Ghost has no safe entry. Confidence: medium.

Classification: hidden support role beats standard attacker role.

Score: pass.

## Resulting Checklist

Before choosing a branch-beating action:

1. Is this Pokemon's standard attacking role actually the route-relevant role?
2. What support job would hurt me most if I ignore it?
3. Is Protect/scout the best way to price the branch before spending a turn?
4. Does my answer preserve the piece that must answer the hidden role later?
5. Am I choosing a move for the active matchup or for the named branch?

## Next Transfer Check

Run a fresh no-keyword-screen replay from a different player pair. Load
`policy_cards/branch_action_after_naming.md` and explicitly ask, before every
switch or support branch, whether the opponent's current Pokemon is acting as a
standard attacker or a hidden support role.
