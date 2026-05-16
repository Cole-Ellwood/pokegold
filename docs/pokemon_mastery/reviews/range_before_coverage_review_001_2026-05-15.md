# Range Before Coverage Review 001 - 2026-05-15

Trigger:
`workspace/quick_tests/side_known_transfer_009_gen2ou-2604345272_p2_2026-05-15.md`

## Verdict

The transaction prompt shape helped, but it is not sufficient. The latest wall
is damage/survival range checking before choosing obvious super-effective
coverage from a low defensive route piece.

## Evidence

In packet 009, the transaction line was obeyed on every scored turn. Early
Baton Pass routing improved: Whirlwind was found on the actual pass turn, and
the Tyranitar and Starmie handoffs were correct. The failure came when Starmie
was at 44% against Machamp at 71%. I chose Psychic because it was the visible
coverage move, but it did not remove Machamp before Hidden Power removed
Starmie. The actual Recover preserved Starmie and kept the Machamp check alive.

## Compact Repair

Do not add another broad card. Add one sentence to `spend_or_save_piece.md`:
low defensive converters must prove the attack changes the next forced choice
before spending their HP. If the attack does not KO and the return hit removes
the route piece, Recover, handoff, or preservation outranks coverage.

## Next Test

Run a regression drill for low Starmie versus Machamp, then restart fresh
side-known replay. The next fresh packet must keep the transaction line active
and score severe blunders as a hard fail.
