# Policy Card: Hidden Role Voluntary Entry

Status: active boundary card.

Use when: a Pokemon voluntarily enters a bad-looking matchup, reveals an
off-standard move, or takes a line that only makes sense if its role differs
from the default species template.

Trigger:

- A piece enters a matchup where the standard role would look passive or bad.
- A revealed move changes the role more than the species name does.
- The tempting line assumes a common move, item, or role that has not been
  revealed.

Default:

Treat the voluntary entry or set reveal as evidence. Price lure moves,
coverage, cash-out jobs, and one-turn support actions before assigning the
standard role. Use "possible" language until the move is public.

Use a three-tier public-information gate:

- `revealed`: public and usable as fact.
- `strong prior`: affects risk pricing, but the line must still name the
  fallback if wrong.
- `possible only`: branch to cover or mention, not the reason for the main move
  unless the answer is explicitly a high-risk read.

Item-state gate: moves such as Thief, RestTalk item denial, or no-item lure
logic need public item-state evidence before becoming the main line. A Pokemon
at full HP that does not show Leftovers has not revealed no item. If item state
is only possible, rank the move as a read and give the fallback.

Opposite boundary:

Do not invent hidden coverage just because it would be convenient. If the
standard role still explains the entry and no reveal supports the lure, keep
the normal branch map and mark the hidden role as a contingency.

Exceptions:

- Spectator-public mode may not reveal the team context that made the entry
  safe; score by decision class when exact role is unknowable.
- A low or trapped piece may enter as a sack, not as a lure.
- A standard role can still be correct after an off-standard reveal if the next
  board is owned by that standard job.

Worst branch:

You import a common set from species memory, miss the lure or one-time job, and
choose a support move that lets the opponent's actual route convert.

Opposite worst branch:

You overcorrect from prior hidden-role misses, promote a possible-only move to
fact, and choose a line that fails if the unshown move is not real.

Local status:

Vanilla GSC policy source. Romhack role, move, item, type, and AI claims need
local evidence when decision-relevant.

Evidence:

- `workspace/quick_tests/hidden_role_branch_probe_001_2026-05-14.md`
- `workspace/quick_tests/replay_turn_pause_067_hidden_role_transfer_smogtours-gen2ou-912841_2026-05-14.md`
- `workspace/quick_tests/electric_receiver_resttalk_transfer_001_smogtours-gen2ou-920928_2026-05-14.md`
- `workspace/quick_tests/resttalk_hidden_role_correction_probe_001_2026-05-14.md`
- `workspace/quick_tests/hidden_role_electric_transfer_001_smogtours-gen2ou-920951_2026-05-14.md`
- `workspace/quick_tests/hidden_role_electric_transfer_002_smogtours-gen2ou-920961_2026-05-14.md`
- `workspace/quick_tests/support_set_hidden_role_probe_001_2026-05-14.md`
- `workspace/quick_tests/support_set_hidden_role_transfer_001_smogtours-gen2ou-921372_2026-05-14.md`
- `workspace/quick_tests/counter_handoff_loop_transfer_001_smogtours-gen2ou-921389_2026-05-14.md`
- `workspace/quick_tests/setup_hidden_role_stop_probe_001_2026-05-14.md`
- `workspace/quick_tests/setup_hidden_role_stop_transfer_001_smogtours-gen2ou-921412_2026-05-14.md`
- `workspace/quick_tests/screen_phaze_third_owner_probe_001_2026-05-14.md`
- `workspace/quick_tests/spinblock_subgrowth_transfer_001_smogtours-gen2ou-932556_2026-05-15.md`
- `reviews/spinblock_subgrowth_review_001_2026-05-15.md`

Drill:

Give two voluntary-entry positions: one where the entry signals a lure or
off-standard move, and one where the standard role still explains the entry.
