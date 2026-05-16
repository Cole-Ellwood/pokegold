# Branch Absorber Punish Probe 001 - 2026-05-14

Source parent:
`workspace/quick_tests/branch_counter_switch_transfer_002_smogtours-gen2ou-914596_2026-05-14.md`.

Mode: constructed nonblind policy regression. This is not fresh replay proof.
It isolates the turn-10 miss where Zapdos was named as the sleep absorber but
Explosion was not made the top punish.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/workspace/quick_tests/branch_counter_switch_transfer_002_smogtours-gen2ou-914596_2026-05-14.md`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Absorber-punish ranking hits: 4 / 4.

Hidden-information discipline hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Follow with a fresh replay transfer before
treating this boundary as stable.

## Scenario 1 - Cash-Out Into The Sleep Absorber

Public state:

```text
Vanilla GSC spectator-public style. Your Exeggutor faces opposing Exeggutor.
Your Exeggutor has Sleep Powder and Explosion revealed. The opponent has a
healthy Zapdos revealed, and Zapdos is the obvious sleep absorber if you click
Sleep Powder again. Sleep has not landed on the opponent yet.
```

Tempting move:
Use Sleep Powder because sleep is still open.

Frozen top-three:

1. Explosion into the named Zapdos absorber if removing Zapdos opens the route.
2. Switch or double to the Zapdos owner if Explosion is too expensive.
3. Sleep Powder only if Zapdos staying out or absorbing is not the best-priced
   branch.

Answer:
Explosion. Confidence: medium. Once Zapdos is named as the absorber, the
status move is no longer the default; the cash-out directly beats the branch.

Score: pass.

## Scenario 2 - Coverage Into The Status Absorber

Public state:

```text
Vanilla GSC spectator-public style. Your Zapdos faces Cloyster. Thunder is
obvious into Cloyster, but the opponent has repeatedly used Raikou as the
Electric receiver. Your Zapdos has Hidden Power revealed and it heavily chips
Raikou.
```

Tempting move:
Use Thunder because Cloyster is active and weak to it.

Frozen top-three:

1. Hidden Power into the named Raikou receiver.
2. Counter-switch to the Raikou owner if Hidden Power damage does not change
   the next board.
3. Thunder only if Cloyster staying is the dominant branch.

Answer:
Hidden Power. Confidence: medium-high. The receiver is named and revealed
coverage beats it; do not keep the active-target move on top by inertia.

Score: pass.

## Scenario 3 - Counter-Switch Beats The Absorber

Public state:

```text
Vanilla GSC spectator-public style. Your Exeggutor faces Snorlax. Sleep Powder
is available, but the opponent's healthy Sleep Talk Zapdos is revealed and is
the likely absorber. Your Tyranitar is healthy enough to enter Zapdos and
threaten it immediately.
```

Tempting move:
Click Sleep Powder because sleep is open and Snorlax is active.

Frozen top-three:

1. Switch Tyranitar into the named Zapdos absorber if the entry is safe enough.
2. Explosion if trading Exeggutor for Zapdos is better than preserving it.
3. Sleep Powder only if Snorlax staying is more likely or the Tyranitar handoff
   is too expensive.

Answer:
Switch Tyranitar. Confidence: medium. The absorber branch creates a better
next board for Tyranitar than another status attempt.

Score: pass.

## Scenario 4 - Setup/Substitute Beats The Absorber

Public state:

```text
Vanilla GSC spectator-public style. Your Jynx or Gengar-like status threat
faces a target that strongly invites a sleeping RestTalk Raikou absorber.
Substitute is revealed. The absorber cannot break the substitute immediately
without giving up major damage or information.
```

Tempting move:
Repeat the status move because the active target is still vulnerable.

Frozen top-three:

1. Substitute to keep initiative through the named absorber.
2. Coverage or cash-out if it directly punishes the absorber harder.
3. Status only if the absorber branch is no longer the best-priced line.

Answer:
Substitute. Confidence: medium. Setup is the branch-punish action when it keeps
the route against the absorber better than trying status again.

Score: pass.

## Resulting Checklist

Before leaving a sleep or status move on top after naming an absorber:

1. Name the absorber and the next board.
2. Rank cash-out, coverage, counter-switch, setup/Substitute, and status.
3. Keep status top only if it still improves through the absorber or the
   absorber branch is not the best-priced branch.

Next transfer:
Use a fresh replay and score whether absorber-punish ranking survives without
the answer labels.
