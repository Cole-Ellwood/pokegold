# Branch Action Coverage Probe 001 - 2026-05-14

Source parent:
`quick_tests/replay_turn_pause_065_preservation_transfer_smogtours-gen2ou-920439_2026-05-14.md`.

Mode: constructed nonblind policy regression. This checks whether the replay
065 branch-action misses can be restated as forced choices. It is not fresh
replay-transfer evidence.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/policy_cards/hazard_loop_spin_window.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_065_preservation_transfer_smogtours-gen2ou-920439_2026-05-14.md`

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
treating this branch-action boundary as stable.

## Scenario 1 - Forced Electric Exit Into Counter-Switch

Public state:

```text
Vanilla GSC spectator-public state. Your Marowak is active at 100% against an
opposing Raikou at 100%. No hazards are up. Raikou is very likely to leave
because Earthquake threatens it. You expect Skarmory or another Marowak answer.
You have Cloyster available and it can meet Skarmory while claiming Spikes.
```

Tempting move: Swords Dance because the Electric is forced out.

Frozen answer: counter-switch Cloyster if the Skarmory branch is the best
branch. Swords Dance is correct only when the expected receiver cannot reset
the route or when the boost changes the next board more than meeting the
receiver now. Confidence: medium.

Classification: named forced switch requires the action that beats the receiver.

Score: pass.

## Scenario 2 - Fire Blast Into Named Skarmory Switch

Public state:

```text
Vanilla GSC spectator-public state. Your Snorlax is active at 84% and
paralyzed against opposing Raikou at 70%. Spikes are on the opponent's side.
You expect Raikou to leave to Skarmory. Your Snorlax has Fire Blast and
Double-Edge available.
```

Tempting move: Double-Edge because it is generic Snorlax pressure.

Frozen answer: use Fire Blast if the named branch is Skarmory. Double-Edge is
only better if the receiver branch is uncertain enough that neutral chip across
multiple targets beats the coverage move. Confidence: medium-high.

Classification: coverage move cashes in the named switch branch.

Score: pass.

## Scenario 3 - Lower-Value Cloyster Handoff Into CurseLax

Public state:

```text
Vanilla GSC spectator-public state. Your paralyzed Snorlax is active at 96%
after revealing Defense Curl and Fire Blast. Opposing Snorlax is healthy and
has not revealed its set. Your Cloyster is poisoned but still high enough to
take a hit and use Reflect. Marowak and Zapdos are preserved.
```

Tempting move: keep Snorlax active because it already started its own setup.

Frozen answer: switch Cloyster if the opponent's best branch is Curse and
Cloyster can buy Reflect or a later cash-out while preserving the central
Snorlax. The lower-value absorber is not a throwaway if its entry creates the
handoff the route needs. Confidence: medium.

Classification: lower-value support handoff before setup tunnel vision.

Score: pass.

## Scenario 4 - Curse Tyranitar Under Reflect

Public state:

```text
Vanilla GSC spectator-public state. Your Tyranitar is active at 100% against an
opposing Snorlax at +3 Attack and +3 Defense. Reflect is active on your side.
Snorlax's main shown attack is Double-Edge, which Tyranitar resists. Tyranitar
has Curse available; Roar is not revealed.
```

Tempting move: assume Tyranitar entered to phaze because boosted Snorlax is
scary.

Frozen answer: use Curse if Reflect plus Normal resistance lets Tyranitar
contest the damage race and no phaze move is confirmed. Roar is correct when it
is known, necessary, and better than using the current resisted-hit window.
Confidence: medium.

Classification: re-solve after hard-answer reveal instead of assuming the
standard phaze job.

Score: pass.

## Resulting Checklist

When a branch is named:

1. What receiver or punish is actually being named?
2. Which action beats that receiver: attack, coverage, counter-switch, phaze,
   setup, status, Reflect, Explosion, or sacrifice?
3. Does the tempting active move beat the named branch, or only the current
   board?
4. Is the hard answer's job revealed, or am I importing a standard role?
5. If a set reveal changes the answer, re-solve before continuing the old plan.

## Next Transfer Check

Run a fresh no-keyword-screen replay packet with
`policy_cards/branch_action_after_naming.md` loaded. On every likely switch or
support branch, write the branch and the branch-beating action as separate
lines before revealing.
