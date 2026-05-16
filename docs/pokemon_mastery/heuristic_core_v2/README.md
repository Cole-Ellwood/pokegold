# Heuristic Core

Purpose: tiny live cards for fresh unseen move choice. Load `live_core.md`,
the prompt, and at most one card before freezing an answer.

These cards compress repeated lessons from `policy_cards/`, reviews, quick
tests, and the measurement ledger. They do not replace the archive; use
`migration_map.md` after scoring to trace evidence.

## Cards

| Card | Load when |
| --- | --- |
| `name_current_owner.md` | You are not sure whose route currently matters. |
| `name_next_board_owner.md` | A switch, sack, absorber, or handoff is likely. |
| `converter_before_script.md` | A safe script move may be hiding the converter. |
| `public_info_tiers.md` | A hidden move, item, teammate, or lure matters. |
| `spend_or_save_piece.md` | A support piece may preserve, sack, or cash out. |
| `reset_loop_denial.md` | Spikes, Spin, Rest, Recover, phaze, or pass loops matter. |
| `rescore_after_reveal.md` | A reveal changes the set or package. |
| `branch_punish_ranking.md` | The branch is named but the top move may not punish it. |

## Routing Rule

For fresh replay decisions, do not load long policy cards, cookbook, source
ledger, paused atlas, live drills, reviews, scored quick tests, or external
research until after answers are frozen. After scoring, use them freely for
postmortem, evidence audit, and card revision.
