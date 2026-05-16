# Branch Cash-Out Coverage SleepTalk Probe 001 - 2026-05-14

Source parent:
`workspace/quick_tests/branch_handoff_transfer_001_smogtours-gen2ou-914170_2026-05-14.md`.

Mode: constructed nonblind policy regression. This checks whether the
branch-handoff transfer misses can be restated as four compact branch-action
boundaries. It is not fresh replay-transfer evidence.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/workspace/quick_tests/branch_handoff_transfer_001_smogtours-gen2ou-914170_2026-05-14.md`

## Score Summary

Scenarios: 4.

Action-policy hits: 4 / 4.

Branch-class hits: 4 / 4.

Handoff-obedience hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

State errors: 0.

Measurement status: regression only. Follow with fresh replay transfer before
treating this boundary as stable.

## Scenario 1 - Cash Out Over Preserve

Public state:

```text
Vanilla GSC spectator-public style. Your Forretress faces Zapdos on turn 1.
Zapdos is very likely to use Thunder immediately. Forretress can either flee to
a special receiver or use Explosion if it can survive or if the trade is the
route-defining opening.
```

Tempting move: switch a special receiver because Zapdos threatens Forretress.

Frozen answer: use Explosion when removing Zapdos opens the route and
Forretress has not established a clearly more valuable future job. Confidence:
medium. Preservation is wrong if the preserved support piece is less valuable
than deleting the active converter.

Classification: cash-out beats preservation after naming active pressure.

Score: pass.

## Scenario 2 - Revealed Coverage Beats The Receiver

Public state:

```text
Vanilla GSC spectator-public style. Your Snorlax has revealed Thunder and
faces Cloyster. The opponent can name Golem as the Thunder receiver. Snorlax
also has a physical attack or coverage line that still damages the receiver.
```

Tempting move: repeat Thunder because Cloyster is the active target.

Frozen answer: use the move that punishes Golem if the receiver branch is now
the best-priced line. Confidence: medium. Thunder is correct only while
Cloyster staying is more important than the immunity switch.

Classification: revealed receiver requires branch-covering action.

Score: pass.

## Scenario 3 - SleepTalk Sleeper Stays

Public state:

```text
Vanilla GSC spectator-public style. A sleeping Raikou has Sleep Talk revealed
or is strongly likely to have it. It faces a Pokemon that would normally expect
the sleeping target to switch out for Sleep Clause value.
```

Tempting move: assume the sleeper switches and target only the receiver.

Frozen answer: price Sleep Talk first. Confidence: medium-high. A sleeping
RestTalk route piece may stay active and attack; the switch-out prior is weaker
once Sleep Talk is revealed or likely.

Classification: sleeper-stays branch before switch-out prior.

Score: pass.

## Scenario 4 - Handoff After Coverage Is Priced

Public state:

```text
Vanilla GSC spectator-public style. Your poisoned Snorlax faces Golem. Snorlax
has Surf revealed or strongly represented. Golem can Earthquake, but Snorlax
survives the immediate hit and Surf nearly removes Golem. Exeggutor is also a
possible Ground-resist handoff.
```

Tempting move: switch Exeggutor because it is the clean Ground answer.

Frozen answer: use Surf if Snorlax survives and Surf removes or cripples
Golem. Confidence: medium. Only hand off to Exeggutor when Snorlax cannot
survive, when Surf is unavailable, or when preserving Snorlax is route-defining
after the damage.

Classification: active coverage before default handoff.

Score: pass.

## Resulting Checklist

Before obeying a found handoff:

1. Does the active piece have a one-time trade that removes the converter?
2. Does revealed coverage punish the named receiver better than switching?
3. Is the sleeping target a RestTalk piece that can stay and attack?
4. If I switch, what active damage or cash-out am I giving up?

## Next Transfer Check

Run a fresh no-keyword-screen branch-action transfer. Score whether the answer
prices cash-out, coverage, SleepTalk stay, and handoff in that order before
committing to the switch.
