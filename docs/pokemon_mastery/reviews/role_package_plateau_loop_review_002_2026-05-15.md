# Role Package Plateau Loop Review 002 - 2026-05-15

Reviewed counted packets:
- `workspace/quick_tests/absorber_transaction_transfer_001_smogtours-gen2ou-932554_2026-05-15.md`
- `workspace/quick_tests/one_for_one_lead_lure_transfer_001_smogtours-gen2ou-933216_2026-05-15.md`
- `workspace/quick_tests/gengar_sleep_handoff_transfer_001_smogtours-gen2ou-932571_2026-05-15.md`

Quarantined packet:
- `workspace/quick_tests/trap_pass_quarantine_001_smogtours-gen2ou-536736_2026-05-15.md`

## Combined Counted Sample

Decisions: 57.

Top-match: 28/57 = 49.1%.

Acceptable-match: 46/57 = 80.7%.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 3.

Mechanics errors: 0.

Positive-selection: 50/57 = 87.7%.

Route-converting move chosen: 44/57 = 77.2%.

Branch-punish chosen: 36/57 = 63.2%.

Role-package update obeyed: 27/36 = 75.0%.

## Verdict

Flat, not progress.

The severe-blunder gate stayed clean and positive/route language improved, but
that is not enough. Top-match stayed around the recent plateau range, acceptable
match fell versus the prior support-ledger packet, and hidden-info errors rose.
Under the plateau loop, broad replay grinding should stop until the method is
repaired again.

## Diagnosis

The simplified docs are not the main blocker anymore. The live core is small
enough to use, and it helped on public packages:

- `932571` turn 5: Exeggutor's sleep job ended, so Forretress absorbed Explosion.
- `932571` turn 10: sleeping Umbreon still owned the Gengar route.
- `932554` turns 5-7: Steelix's phaze job was preserved.

The current blocker is a narrower synthesis error:

```text
Voluntary entry is being overread as hidden coverage proof.
```

In `932554`, Zapdos entering Nidoking was first a sleep-absorber transaction,
not proof that Hidden Power should outrank the public sleep route. In `932571`,
Dragonite entering Golem/Cloyster was treated as a direct coverage clue when it
could also be bait or handoff into the real owner.

There is also a scoring-method issue. Spectator-public exact top-match is a
weak oracle when the actual move depends on private moves, team slots, or a
player-specific line. It should still be tracked, but postmortems must split:

- public-route error I should have known from the prompt;
- side-known oracle gap where exact move was unknowable but class was right;
- true hidden-info error where I let unrevealed information anchor the line.

## Structure Update

Before more broad replays, the next packet must force this triage:

```text
When a Pokemon voluntarily enters a threat, classify it as one of:
direct coverage owner / absorber / bait-handoff.
```

The top line may use hidden coverage only if it is revealed, side-known, or
explicitly a high-risk read with fallback. Otherwise the answer must first name
the public owner and the handoff route.

## Next Loop

Run one focused current-legal transfer or micro-drill on voluntary-entry
triage before another broad replay sample. If the drill passes, restart the
three-packet sample. If it fails, stop replay review and build a side-known
reconstruction workflow or a smaller prompt format that separates public-route
class from exact-move prediction.
