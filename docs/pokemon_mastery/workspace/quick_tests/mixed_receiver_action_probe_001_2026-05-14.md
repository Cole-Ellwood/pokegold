# Mixed Receiver Action Probe 001 - 2026-05-14

Source parent:
`workspace/quick_tests/replay_turn_pause_072_branch_action_full_transfer_smogtours-gen2ou-917932_2026-05-14.md`.

Mode: constructed nonblind policy regression. This checks whether replay 072's
receiver-action misses can be restated as distinct branch-beating choices. It
is not fresh replay-transfer evidence.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/workspace/quick_tests/replay_turn_pause_072_branch_action_full_transfer_smogtours-gen2ou-917932_2026-05-14.md`

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
treating the mixed receiver-action boundary as stable.

## Scenario 1 - Counter-Switch Beats The Receiver

Public state:

```text
Vanilla GSC spectator-public state. Your poisoned Zapdos faces opposing
Skarmory. Spikes are on your side. You can name Raikou as the likely Zapdos
receiver, and your Tyranitar is available to meet Raikou.
```

Tempting move: Thunder because Skarmory is active and Raikou still takes chip.

Frozen answer: switch Tyranitar when Raikou is the best-priced receiver and
Tyranitar changes the next board more than resisted Thunder chip. Confidence:
medium.

Classification: counter-switch after naming receiver.

Score: pass.

## Scenario 2 - Active Damage Still Beats The Receiver

Public state:

```text
Vanilla GSC spectator-public state. Your Zapdos faces opposing Cloyster with
Spikes on your side. You can name Raikou as the likely receiver. Raikou is not
statused and would be forced into a risky route if Thunder lands paralysis.
```

Tempting move: double-switch immediately because Raikou is the receiver.

Frozen answer: use Thunder when the active move threatens route-changing damage
or paralysis into both Cloyster and Raikou. Confidence: medium.

Classification: active damage/status still punishes receiver.

Score: pass.

## Scenario 3 - Status-Immune Handoff Beats The Punish

Public state:

```text
Vanilla GSC spectator-public state. Your Tyranitar faces opposing Skarmory.
Skarmory has revealed Toxic pressure, and your Forretress is available. You do
not need Tyranitar to take Toxic to preserve the route this turn.
```

Tempting move: Fire Blast or Rock Slide because Skarmory is on screen.

Frozen answer: switch Forretress when Toxic is the best-priced punish and the
status immunity wins the branch without giving up a route-defining Tyranitar
job. Confidence: medium.

Classification: counter-switch to status immunity.

Score: pass.

## Scenario 4 - Support Setup Before Removal

Public state:

```text
Vanilla GSC spectator-public state. Your Forretress faces opposing Skarmory.
Spikes are on your side, but the opponent's side has no Spikes. Skarmory can
Whirlwind, Toxic, or switch. You can set Spikes or Rapid Spin.
```

Tempting move: Rapid Spin because your side is already taking Spikes damage.

Frozen answer: set Spikes first when reciprocal hazard pressure is the
route-defining job and immediate Spin does not stop Skarmory from phazing or
rebuilding pressure. Confidence: medium.

Classification: support setup before hazard removal.

Score: pass.

## Resulting Checklist

After naming a receiver or punish:

1. Does a counter-switch beat the next board harder than active chip?
2. Does the active move still create route-changing damage or status into the
   receiver?
3. Is the real branch a status or utility punish that an immunity can blank?
4. Is the support job to create reciprocal pressure before removing hazards?
5. What happens if the opponent uses the non-primary punish instead?

## Next Transfer Check

Run a fresh no-keyword-screen replay packet with
`branch_action_after_naming.md` loaded. Score whether receiver reads select the
right action class rather than always defaulting to damage or always defaulting
to a counter-switch.
