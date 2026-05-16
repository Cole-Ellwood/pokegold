# Training Method / Oracle Review 001 - 2026-05-15

Parent transfers:

- `docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_012_gen2ou-2609886103_p2_2026-05-15.md`
- `docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_013_gen2ou-2610130811_p1_2026-05-15.md`

Reason for study:
After the mastery-doc compression, the issue is no longer only retrieval load.
The compact rules are readable and the prompt now forces transaction and
candidate comparison, but fresh top-match remains flat/regressing in opening
branch chains.

## Evidence

Packet 012 failed by turn 3: 0/3 top, 1/3 acceptable, 0 severe/hidden/state/
mechanics. The missed class was opening lead-cycle counter-map selection.

Packet 013 improved the form of reasoning but not top-choice accuracy: 4/12
top, 9/12 acceptable, 0 severe/hidden/state/mechanics. The misses were mostly
branch-punish promotion, not document recall.

## Sources Used

Local docs:

- `live_core.md`
- `replay_turn_pause_protocol.md`
- `heuristic_core/name_next_board_owner.md`
- `heuristic_core/branch_punish_ranking.md`
- `heuristic_core/role_package_ledger.md`
- `reviews/candidate_comparison_prompt_shape_review_001_2026-05-15.md`

Current web sources:

- Smogon Forums, An Analysis of Leads in GSC OU:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`
- Smogon Forums, GSC OU Jynx:
  `https://www.smogon.com/forums/threads/gsc-ou-jynx.3699576/`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums, GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`

## Diagnosis

The docs are smaller enough to use. The live failures now come from calibration:
when several branch punishes are plausible, I am not reliably promoting the one
an expert player chose.

Raw replay top-match is a weak standalone oracle in opening double-switch
clusters. The actual move often encodes private team confidence, opponent
modeling, or a mixed-strategy read. It is still useful, but not as the only
training signal.

Side-known reconstructed from a replay log is partial side-known, not a full
team sheet. Unused own moves are missing, so recommendations that depend on an
unused own move must be labeled as own-move reconstruction gaps rather than
scored as clean full-information advice.

## Training Change

Before more broad fresh replay grinding, run expert branch reviews on failed
opening clusters:

1. Freeze the turn as before.
2. Score exact top and acceptable match.
3. Add a post-reveal branch map: active target, next owner, counter-owner,
   public tier, and why the actual player promoted that branch.
4. Extract only one compact rule or reject note.
5. Resume fresh packets only after the branch map can be reproduced in a small
   regression drill.

This does not replace fresh replay work. It changes the loop from "grind more
turns after a flat result" to "repair branch calibration, then test transfer."

## Next Test

Do an expert branch review of turns 1-12 from `gen2ou-2610130811`, focusing on
Gengar -> Tyranitar, Tyranitar -> Alakazam, Donphan/Gengar handoffs, and
Alakazam status/passing interactions. Then run one small nonblind drill before
the next fresh side-known packet.

