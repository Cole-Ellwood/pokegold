# Sleeper Spinner Immunity Branch Probe 001 - 2026-05-14

Source parent:
`quick_tests/replay_turn_pause_069_support_action_transfer_smogtours-gen2ou-917918_2026-05-14.md`.

Mode: constructed nonblind policy regression. This checks whether replay 069's
saved-sleeper, Starmie status-before-Spin, Quagsire receiver, and counter-switch
misses can be restated as forced branch-action choices. It is not fresh
replay-transfer evidence.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/hazard_loop_spin_window.md`
- `docs/pokemon_mastery/policy_cards/sleep_absorber_and_set_ambiguity.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_069_support_action_transfer_smogtours-gen2ou-917918_2026-05-14.md`

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
treating this combined branch pattern as stable.

## Scenario 1 - Saved Sleeper As Reusable Absorber

Public state:

```text
Vanilla GSC spectator-public state. Your Zapdos was put to sleep by Lovely
Kiss, switched out immediately, and still has Sleep Clause value. Later, your
Quagsire faces opposing Cloyster. Cloyster can use Toxic, Surf, Spikes, or
switch. You have Starmie and Snorlax available, but Zapdos can absorb Toxic
without taking a new status.
```

Tempting move: keep Quagsire in or go Starmie because Cloyster is the active
matchup and Starmie is the obvious spinner.

Frozen answer: switch the sleeping Zapdos into Toxic or passive support when it
preserves Quagsire and Starmie for their route jobs. Do not stay in just to burn
sleep turns later unless Zapdos has an active job on that board. Confidence:
medium.

Classification: saved sleeper as reusable status absorber.

Score: pass.

## Scenario 2 - Starmie Status Before Spin

Public state:

```text
Vanilla GSC spectator-public state. Your Starmie has entered after the opponent
set Spikes with Cloyster. The opponent can go Zapdos to pressure Starmie, a
Ghost to block Rapid Spin, or Snorlax to absorb special pressure. Starmie has
Rapid Spin and Thunder Wave.
```

Tempting move: Rapid Spin immediately because hazards are up and Starmie is the
spinner.

Frozen answer: use Thunder Wave when the best opposing answer is a fast pressure
piece such as Zapdos and paralyzing it improves the hazard route more than
spinning this turn. Spin immediately only when the removal is likely to resolve
or delay gives the opponent a free converter. Confidence: medium.

Classification: spinner support move before hazard removal.

Score: pass.

## Scenario 3 - Quagsire As Electric-Immunity Receiver

Public state:

```text
Vanilla GSC spectator-public state. Your Starmie faces opposing Zapdos after
Starmie has used Thunder Wave. Spikes are on your side, so every switch has a
cost. Your team has Quagsire unrevealed or unrevealed in this sequence. Zapdos
can click Thunder, use Hidden Power, or switch.
```

Tempting move: switch Snorlax because it is the familiar Zapdos receiver and
does not reveal another piece.

Frozen answer: switch Quagsire when the live branch is Thunder and the immunity
keeps Starmie from absorbing damage while denying Zapdos immediate progress.
Use Snorlax when Zapdos's non-Electric pressure or the long-term special
absorber map matters more than the immunity. Confidence: medium.

Classification: immunity receiver over generic bulky receiver.

Score: pass.

## Scenario 4 - Counter-Switch After Naming Quagsire

Public state:

```text
Vanilla GSC spectator-public state. Your paralyzed Zapdos faces opposing
Starmie, and Spikes are on the opponent's side. You can attack Starmie with
Thunder, but you can also name Quagsire as the likely Electric-immune receiver.
Your Nidoking is available and beats or pressures Quagsire on entry.
```

Tempting move: Thunder because Starmie is on screen and the active matchup says
Zapdos should punish it.

Frozen answer: switch Nidoking when Quagsire is the best-priced receiver and
Nidoking is the action that beats that receiver. Thunder is correct when
Starmie staying or a non-Ground receiver is the branch that most changes the
route. Confidence: medium.

Classification: counter-switch after naming the receiver.

Score: pass.

## Resulting Checklist

Before choosing into a receiver or hazard branch:

1. If a Pokemon is asleep, can it be saved or reused as a status absorber
   instead of burning turns?
2. If Starmie is active with Spikes up, is Rapid Spin the route job now, or does
   Thunder Wave first change the anti-spinner map?
3. If an Electric attack is obvious, is the Ground immunity the real receiver
   over the generic special sponge?
4. After naming that receiver, what move or switch actually beats it?
5. Does the branch action preserve a concrete win route, or only answer the
   Pokemon currently on screen?

## Next Transfer Check

Run a fresh no-keyword-screen replay with `branch_action_after_naming`,
`hazard_loop_spin_window`, and `sleep_absorber_and_set_ambiguity` loaded. Score
whether the answer chooses the branch-beating action after naming saved sleepers,
spinners, Electric immunities, and counter-switch receivers.
