# Thief/Thunder Lure Handoff Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/thief_thunder_lure_handoff_transfer_001_smogtours-gen2ou-933321_2026-05-15.md`

Reason for study:
The fresh transfer was imperfect and stopped early. It did not produce severe,
hidden-info, state, or mechanics errors, but it repeated a positive-selection
failure: after item or lure information appeared, I kept choosing the safe
visible active line instead of the move that converted through the receiver.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/active_pressure_before_status.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/hidden_role_voluntary_entry.md`
- `policy_cards/cashout_boundary.md`
- `policy_cards/hazard_loop_spin_window.md`
- `reviews/item_removal_revealed_package_review_001_2026-05-15.md`
- `reviews/jolteon_agipass_receiver_review_001_2026-05-15.md`
- `workspace/quick_tests/branch_action_gate_001_smogtours-gen2ou-909834_2026-05-14.md`
- `workspace/quick_tests/branch_action_focus_002_gen2ou-2595974016_2026-05-14.md`
- `workspace/quick_tests/branch_action_mixed_probe_001_2026-05-14.md`

Current web sources:

- Smogon Forums GSC Nidoking:
  `https://www.smogon.com/forums/threads/gsc-nidoking.3681149/`
- Smogon Forums An Analysis of Leads in GSC OU:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`
- Smogon Forums GSC OU Steelix:
  `https://www.smogon.com/forums/threads/gsc-ou-steelix.3705042/`
- Smogon GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`

## Source-To-Policy Extraction

Thief competes with generic sleep:
The Nidoking source says Lovely Kiss remains strong, but Thief has become a
real competitor because it removes Leftovers from Sleep Talk and bulky checks,
then Spikes support reduces their durability. This transfer repeated an older
Nidoking miss: I saw a sleep-capable lead and defaulted to Lovely Kiss instead
of asking whether item removal was the route-converting first move.

Lead Snorlax can be a Cloyster lure:
The lead-analysis source explicitly describes early Snorlax using Double-Edge
plus Thunder to lure Cloyster that wants early Spikes. That makes turn 4 only
the reveal. Turn 5 is the decision point: after Thunder is public, the defender
can move to an absorber, and the attacker must price a counter-handoff instead
of repeating the lure into the obvious answer.

Steelix plus Cloyster is a known support structure:
The Steelix and sample-team sources frame Steelix as an Electric-immune
physical wall/phazer that benefits from Cloyster's Spikes, while Cloyster
checks important physical threats and keeps future Spin/Explosion utility.
Therefore p2's turn-5 Steelix switch was not just "avoid Thunder"; it preserved
Cloyster after Spikes and improved the Steelix phaze/support route.

Cloyster cash-out must be compared to preservation:
The GSC threatlist emphasizes Cloyster's Spikes, Rapid Spin, and Explosion
compression. Explosion is real, but the cash-out card already says not to spend
a support piece just because the move exists. In this transfer I overranked
Explosion after Spikes and missed the higher-value hard-answer handoff.

No-Team-Preview boundary:
The exact hidden p1 Cloyster and p2 Steelix were not public before turn 5. The
correct spectator-public answer should not pretend to know them. It should say
"counter-switch to the Steelix/Golem/Tyranitar absorber class if available" or
"handoff to the Water/Ground-answer class if available," with active pressure
as fallback if the owner is absent or the active cannot leave.

## Policy Updates Made

- `branch_action_after_naming.md`: added a revealed-lure second-turn extension
  that forces the absorber and counter-handoff ledger after moves like Thunder,
  Fire Blast, or Hidden Power become public.
- `active_context.md`: moved the latest fresh-transfer pointer to
  `thief_thunder_lure_handoff_transfer_001` and made the next rep focus on
  item/lure second-turn handoffs.
- `measurement_progress_ledger.csv`: recorded the early-stop transfer and the
  constructed regression probe separately.

## Measurement Note

Not progress. The packet went 4/10 top and 7/10 acceptable with 0 severe,
hidden-info, state, and mechanics errors. Positive-selection was 7/10, but
route conversion was only 5/10 and branch-punish obedience was 4/8. Acceptable
match was helped by broad class matches; the actual top move still missed the
route-converting package action too often.

The constructed probe is a repair check only. It is not fresh unseen evidence
and cannot be used as mastery or boss-sim validation.
