# Cash-Out Before Status Script Probe 001 - 2026-05-14

Source parent:
`workspace/quick_tests/replay_turn_pause_074_mixed_punish_transfer_gen2ou-2595957046_2026-05-14.md`.

Mode: constructed nonblind policy regression. This checks whether replay 074's
turn 10 miss can be restated as a forced decision boundary. It is not fresh
replay-transfer evidence.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/active_pressure_before_status.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_074_mixed_punish_transfer_gen2ou-2595957046_2026-05-14.md`

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
treating cash-out before status as stable.

## Scenario 1 - Explosion Before Sleep

Public state:

```text
Vanilla GSC spectator-public state. Your Exeggutor is at 66% and faces opposing
Zapdos at 83%. Zapdos has shown Thunder and may have Hidden Power. Sleep Clause
is open. Exeggutor has Sleep Powder and Explosion.
```

Tempting move: Sleep Powder because sleep is open and Zapdos is valuable.

Frozen answer: use Explosion when removing Zapdos is the concrete converter and
Hidden Power pressure may erase Exeggutor's future job. Sleep Powder is correct
only when Zapdos sleeping creates a stronger route than removing it or when the
opponent's best branch is a sleep absorber. Confidence: medium.

Classification: cash-out before status script.

Score: pass.

## Scenario 2 - Sleep Before Cash-Out

Public state:

```text
Vanilla GSC spectator-public state. Your Exeggutor is healthy and faces opposing
Snorlax at 90%. Snorlax has not revealed RestTalk. Your Explosion does not open
a clear follow-up KO route, but sleep would force the opponent to play under
Sleep Clause and give your hazards time to convert.
```

Tempting move: Explosion because Snorlax is famous and valuable.

Frozen answer: use Sleep Powder when sleep changes the route and Explosion only
creates damage without a named converter. Re-score if Snorlax has already
shown RestTalk or if a teammate immediately converts the boom. Confidence:
medium.

Classification: status before cash-out when status is the converter.

Score: pass.

## Scenario 3 - Avoid The Absorbed Boom

Public state:

```text
Vanilla GSC spectator-public state. Your Gengar faces opposing Raikou at 64%.
The opponent has Golem revealed and healthy enough to absorb Explosion after
Spikes. Gengar has Hypnosis, Explosion, and a non-boom attack.
```

Tempting move: Explosion because Raikou is the active target.

Frozen answer: do not boom blindly if Golem is the best-priced absorber. Use a
non-boom action or switch unless the route still improves if Golem takes the
Explosion. Status is also risky if it hands the opponent the same absorber
entry. Confidence: medium.

Classification: absorber avoidance before cash-out.

Score: pass.

## Scenario 4 - Spend Completed Support

Public state:

```text
Vanilla GSC spectator-public state. Your Cloyster has already set Spikes and is
unlikely to re-enter safely after this turn. It faces Golem, but the opponent's
Dragonite receiver is low enough that Explosion removes it on entry. Toxic or
Surf only lets Dragonite keep the route alive.
```

Tempting move: Toxic or Surf because they are the visible support/active moves.

Frozen answer: use Explosion when the receiver is the real route target and
Cloyster's remaining support job is less valuable than removing that receiver.
Preserve only if Cloyster still has a needed Spin, Spikes, or physical-check
job. Confidence: medium.

Classification: cash-out into route receiver.

Score: pass.

## Resulting Checklist

Before choosing sleep, status, or a low-cost support move with a one-time piece:

1. Is the active target already the route converter that must be removed?
2. Will the opponent's next attack erase this piece's cash-out window?
3. Does status create a better route than removal, or only feel useful?
4. Is there a named absorber, immunity, or sack that makes Explosion fail?
5. If this piece is preserved, what exact future entry or job justifies it?

## Next Transfer Check

Run a fresh no-keyword-screen replay with `active_pressure_before_status.md`,
`cashout_boundary.md`, and `branch_action_after_naming.md` loaded. Score whether
status-capable or boom-capable Pokemon price immediate cash-out before defaulting
to sleep/status, especially when the active target is already the converter.
