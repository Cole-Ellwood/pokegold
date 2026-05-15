# Baton Pass Receiver Branch Probe 001 - 2026-05-14

Source parent:
`quick_tests/replay_turn_pause_071_cashout_branch_transfer_smogtours-gen2ou-921983_2026-05-14.md`.

Mode: constructed nonblind policy regression. This checks whether replay 071's
Baton Pass receiver miss can be restated as forced branch-action choices. It is
not fresh replay-transfer evidence.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_071_cashout_branch_transfer_smogtours-gen2ou-921983_2026-05-14.md`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Classification hits: 4 / 4.

Route-job hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Follow with a fresh replay transfer before
treating Baton Pass receiver handling as stable.

## Scenario 1 - Whirlwind The Immune Receiver

Public state:

```text
Vanilla GSC spectator-public state. Your Zapdos has revealed Thunderbolt and
Whirlwind. Opposing Scizor has received +2 Defense from Mr. Mime, used Agility,
and is now at 61%. You can name Marowak as the likely Baton Pass receiver.
```

Tempting move: Thunderbolt because Scizor is on screen and was already dropped
by Thunderbolt once.

Frozen answer: use Whirlwind. If Scizor Baton Passes to Marowak, Electric
damage fails and the boosted receiver owns the board; Whirlwind beats the named
receiver and resets the pass. Confidence: high.

Classification: phaze the immune receiver.

Score: pass.

## Scenario 2 - Keep Attacking When The Passer Cannot Survive

Public state:

```text
Vanilla GSC spectator-public state. Your Zapdos has Thunderbolt and Whirlwind.
Opposing Scizor is at 18% with no Speed boost and has Baton Pass revealed. The
likely receiver is Marowak, but Scizor must survive the turn to pass.
```

Tempting move: Whirlwind because Marowak is the named receiver.

Frozen answer: attack with Thunderbolt when it KOs Scizor before Baton Pass can
resolve. Phazing is correct only if Scizor can survive or if Thunderbolt is
blocked by the current target. Confidence: medium-high.

Classification: remove passer before receiver exists.

Score: pass.

## Scenario 3 - Counter-Switch When Phaze Is Unavailable

Public state:

```text
Vanilla GSC spectator-public state. Your Raikou faces +2 Speed Scizor. Scizor
has Baton Pass revealed and Marowak is the likely receiver. Raikou does not have
Roar. Your Cloyster is healthy and can take Marowak's Earthquake once while
threatening Surf or Explosion.
```

Tempting move: Thunder because Scizor is on screen.

Frozen answer: switch Cloyster or the best Marowak answer if the pass is the
best branch and Raikou lacks phazing. Do not click Electric damage into the
named Ground receiver. Confidence: medium.

Classification: counter-switch to receiver.

Score: pass.

## Scenario 4 - Cash Out When No Reset Path Exists

Public state:

```text
Vanilla GSC spectator-public state. Your low Cloyster faces +2 Speed Scizor.
Scizor has Baton Pass revealed and the likely receiver is Marowak. Your phazer
is fainted, your Marowak answer is too low to enter, and Explosion can remove
Scizor before the pass.
```

Tempting move: Spikes or Toxic because Cloyster still has support moves.

Frozen answer: Explosion if it removes the passer before the route collapses.
The support job is no longer more valuable than preventing the boosted receiver
from entering. Confidence: medium.

Classification: cash out to prevent receiver.

Score: pass.

## Resulting Checklist

Before choosing into Baton Pass:

1. What receiver am I naming, and does my visible move affect that receiver?
2. Can I phaze before or after the pass resolves?
3. Can I KO the passer before it passes?
4. If I cannot phaze, which counter-switch meets the receiver?
5. If neither phaze nor counter-switch exists, is cash-out the only route?

## Next Transfer Check

Run a fresh no-keyword-screen replay segment with
`branch_action_after_naming.md` loaded. Stop at the first Baton Pass or obvious
receiver-pivot branch and score whether the answer chooses the branch-beating
action rather than the move that only hits the current active Pokemon.
