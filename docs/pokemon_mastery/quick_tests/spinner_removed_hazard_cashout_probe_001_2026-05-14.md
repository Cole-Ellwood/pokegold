# Spinner-Removed Hazard Cash-Out Probe 001 - 2026-05-14

Source parent:
`quick_tests/replay_turn_pause_076_one_time_trade_transfer_smogtours-gen2ou-924513_2026-05-14.md`.

Mode: constructed nonblind policy regression. This checks whether replay 076's
turn 5 miss can be restated as a forced support-piece cash-out boundary. It is
not fresh replay-transfer evidence.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_076_one_time_trade_transfer_smogtours-gen2ou-924513_2026-05-14.md`

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
treating this boundary as stable.

## Scenario 1 - Boom The Spinner After Spin

Public state:

```text
Vanilla GSC spectator-public state. Your Cloyster set Spikes and faces opposing
Starmie. Starmie can Rapid Spin before Cloyster acts this turn. Cloyster has
Explosion, Toxic, and ordinary attacks. You do not have a confirmed spinblocker.
```

Tempting move: Toxic because Starmie is the spinner and status keeps pressure.

Frozen answer: use Explosion when Starmie will remove Spikes now but the
lasting route value is deleting the spinner so future Spikes can matter. The
cash-out is not invalidated just because the immediate Spin succeeds.
Confidence: medium.

Classification: spinner-removal cash-out after immediate utility.

Score: pass.

## Scenario 2 - Spinblock Before Utility

Public state:

```text
Vanilla GSC spectator-public state. Your Cloyster faces Starmie before Rapid
Spin. Your healthy Gengar is revealed and can enter safely enough. Keeping
Spikes this turn is more valuable than damaging Starmie.
```

Tempting move: Explosion after accepting Spin.

Frozen answer: switch Gengar when preventing the Spin is the concrete route and
Gengar's entry does not lose to Starmie's best coverage. Boom is worse if it
lets Spin happen and spends the hazard setter unnecessarily. Confidence:
medium.

Classification: spinblock before cash-out.

Score: pass.

## Scenario 3 - Preserve The Low Setter

Public state:

```text
Vanilla GSC spectator-public state. Your Cloyster is low but still has a needed
future Spikes reset. Opposing Starmie is already poisoned and cannot safely
remove hazards without giving a strong answer free entry.
```

Tempting move: Explosion because Cloyster is low and Starmie is annoying.

Frozen answer: preserve Cloyster when the spinner is already controlled and
the future Spikes reset is route-defining. Low support is not spent support
until its future job and entry path are gone. Confidence: medium.

Classification: preserve over unnecessary cash-out.

Score: pass.

## Scenario 4 - Cash Out Into Non-Spinner Converter

Public state:

```text
Vanilla GSC spectator-public state. Your support piece has completed its job and
faces a setup or wallbreaking converter. The opponent can get one action this
turn, but if the converter remains alive, slow play loses.
```

Tempting move: preserve because the opponent already gets immediate utility.

Frozen answer: cash out when the remaining board after the trade is better
than any preserve line. The important question is the post-trade route, not
whether the opponent got a one-turn benefit first. Confidence: medium.

Classification: cash-out after accepted immediate utility.

Score: pass.

## Resulting Checklist

When a support piece can trade after the opponent gets immediate utility:

1. What lasting resource remains after the utility action resolves?
2. Does removing the utility piece change all future hazard, setup, or pivot
   turns?
3. Is there a spinblock, absorber, or pivot that prevents the utility without
   spending the support piece?
4. If preserving, what future job and entry path justify it?

## Next Transfer Check

Run a fresh no-keyword-screen replay with `cashout_boundary.md` loaded. Score
whether the answer distinguishes spinblock-before-utility, cash-out-after-
utility, and preserve-over-unnecessary-cash-out.
