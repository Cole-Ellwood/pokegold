# Transaction Prompt Shape Review 001 - 2026-05-15

Trigger:
`workspace/quick_tests/side_known_transfer_008_gen2ou-2592387014_p2_2026-05-15.md`

## Verdict

The current wall is prompt shape/retrieval, not another missing long note.

Evidence:
- `side_known_transfer_007` failed immediately on lead item/status and
  counter-handoff despite compact card patches.
- `lead_item_counter_handoff_drill_001` passed, so the lesson exists in the
  archive and can be recalled in constructed form.
- `side_known_transfer_008` repeated the live failure twice in two turns:
  first missing Snorlax as the counter-handoff, then overcorrecting into
  Explosion while Forretress was the counter-handoff.

## Patch

Make the transaction line mandatory before ranked candidates:

`their package -> our absorber/converter -> their next owner -> our punish`

This is intentionally a prompt-shape patch, not a new pile of matchup notes.
It should force the existing role-package, next-owner, branch-punish, and
spend/save cards to run in order.

## Next Test

One fresh side-known packet. Score the usual metrics, and also reject the run
as invalid if the transaction line is absent before the first nontrivial
candidate ranking.
