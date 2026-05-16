# CurseLax Receiver/Coverage Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/curselax_receiver_coverage_transfer_001_smogtours-gen2ou-932818_2026-05-15.md`

Reason for study:
The fresh transfer was not perfect and stopped early. The new repeated miss was
not catastrophic-error control; it was positive selection. I named plausible
branches, but the top moves did not always convert through the named receiver.

## Sources Read

Local mastery docs:

- `active_context.md`
- `active_goal.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/active_pressure_before_status.md`
- `policy_cards/cashout_boundary.md`
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/hidden_role_voluntary_entry.md`
- `reviews/low_cloyster_ghost_guard_review_001_2026-05-15.md`
- `reviews/snorlax_forretress_counter_handoff_review_001_2026-05-15.md`
- `workspace/quick_tests/early_cycle_counter_handoff_probe_001_2026-05-15.md`
- `workspace/quick_tests/low_support_four_way_probe_001_2026-05-15.md`

Current web sources:

- Smogon Forums, GSC OU Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Forums, GSC OU Gengar:
  `https://www.smogon.com/forums/threads/gengar-wip.3703761/`
- Smogon Forums, GSC OU Viability Rankings Mk. 4:
  `https://www.smogon.com/forums/threads/gsc-ou-viability-rankings-mk-4.3633233/`
- Smogon Forums, GSC OU Threat List:
  `https://www.smogon.com/forums/threads/gsc-ou-threat-list-qc-2-2-gp-2-2.3477110/`

## Confirmed Source Lessons

CurseLax is a package:
Smogon Snorlax material treats Curse, Rest, Body Slam/Double-Edge, and coverage
such as Earthquake as a coherent Snorlax route family. After Curse is public,
the advice must price the coverage receiver map even when the exact fourth move
is not revealed. The information tier still matters: revealed or side-known
Earthquake can anchor the recommendation; unrevealed Earthquake is a strong
prior or possible branch with an explicit fallback.

Cloyster is not just a lead support piece:
Smogon Spikes and Cloyster sources reinforce that Cloyster can set Spikes,
check physical pressure, threaten Explosion, and pressure with coverage/status.
In this replay, hidden Cloyster was the p2 owner into +1 Snorlax after Rest,
not merely a Spikes lead. My p2 Turn 7 answer got the broad switch-out concept
right but overfit to the revealed Gengar guard instead of naming the physical
wall/boom owner class.

Gengar is a guard and a route piece, not a universal answer:
Gengar material supports its role as a Normal immunity, Explosion user, and
utility pivot. It was correct to price Gengar against Cloyster Explosion and
Normal pressure, but once Snorlax coverage is in the branch map, Gengar is not
the whole defensive solve. Earthquake coverage, if present, hits the Gengar
branch and changes the receiver priority.

Spikes amplify receiver decisions:
The Spikes source keeps the focus on repeated switch costs. The correct move is
the one that improves through the likely receiver after entry damage, not the
move that looks best into the sleeping or low active target alone.

## Policy Correction

`branch_action_after_naming.md` needs one narrow extension:

After Snorlax reveals Curse, compare coverage into the named receiver, another
Curse, Rest, and handoff. If Earthquake, Fire Blast, Lovely Kiss, or another
coverage/utility move is revealed or side-known, it can be top. If it is only a
strong prior, rank it by class and name the fallback. If it is possible-only,
keep it below the public route unless explicitly taking a high-risk read.

## Measurement Note

Not progress. The packet scored 4/13 top and 9/13 acceptable with 0 severe,
hidden-info, state, or mechanics errors. Severe-blunder avoidance stayed clean,
but the actual target metric did not: route conversion and branch-punish
obedience stayed below gate.
