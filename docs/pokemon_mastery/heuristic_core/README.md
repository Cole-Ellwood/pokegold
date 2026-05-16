# Heuristic Core

Purpose: tiny live cards for fresh unseen move choice. Load `live_core.md`,
the prompt, and whichever cards are needed before freezing an answer.

These cards compress repeated lessons from `policy_cards/`, reviews, quick
tests, and the measurement ledger. They do not replace the archive; use
`migration_map.md` after scoring to trace evidence. Use `../canon/` for compact
GSC topic facts when the public board needs a mechanics or matchup lookup.

## Cards

| Card | Load when |
| --- | --- |
| `name_current_owner.md` | You are not sure whose route currently matters. |
| `name_next_board_owner.md` | A switch, sack, absorber, or handoff is likely. |
| `converter_before_script.md` | A safe script move may be hiding the converter. |
| `public_info_tiers.md` | A hidden move, item, teammate, or lure matters. |
| `role_package_ledger.md` | A reveal or entry changes a Pokemon's public job. |
| `spend_or_save_piece.md` | A support piece may preserve, sack, or cash out. |
| `reset_loop_denial.md` | Spikes, Spin, Rest, Recover, phaze, or pass loops matter. |
| `rest_curse_tempo_window.md` | Rest, Curse, phaze, or attack timing decides the window. |
| `rescore_after_reveal.md` | A reveal changes the set or package. |
| `branch_punish_ranking.md` | The branch is named but the top move may not punish it. |

## Routing Rule

For fresh replay decisions, do not load long policy cards, cookbook, source
ledger, paused atlas, live drills, reviews, scored workspace quick tests, or
raw external research until after answers are frozen. After scoring, use them
freely for postmortem, evidence audit, and card revision.

Card count is not a metric. Use the smallest useful set for the current board;
add cards when separate uncertainties matter, and use none when the live core is
enough.
