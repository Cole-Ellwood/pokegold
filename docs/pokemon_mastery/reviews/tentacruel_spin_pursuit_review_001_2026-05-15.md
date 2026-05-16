# Tentacruel Spin/Pursuit Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/tentacruel_spin_pursuit_transfer_001_smogtours-gen2ou-931770_2026-05-15.md`

Reason for study:
The fresh transfer was imperfect. It kept the severe, hidden-info, state, and
mechanics gates clean and acceptable-match improved, but top-match fell and
branch-punish obedience stayed poor. The main miss was solving individual
moves instead of the full spinner -> spinblock -> Pursuit -> punish sequence.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/support_handoff_after_job.md`
- `reviews/rest_spin_phaze_review_001_2026-05-15.md`

Current web sources:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums, GSC OU sample teams breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon Forums, Tentacruel revamp:
  `https://www.smogon.com/forums/threads/tentacruel-revamp-qc-3-3.3474651/`
- Smogon Forums, Golem OU revamp:
  `https://www.smogon.com/forums/threads/golem-ou-revamp-qc-2-2-gp-2-2.3647044/`
- Smogon, Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`

## Confirmed Source Lessons

Tentacruel is a real spinner but low-synergy:
Smogon's Spikes article identifies Tentacruel as an unconventional but solid
spinner that can beat Cloyster and Forretress one-on-one, while struggling
more than Starmie against Ghost-types and losing Swords Dance when using Rapid
Spin. The Tentacruel revamp/source snippet also supports Protect as a recovery
and scouting move. In the transfer, this means Rapid Spin, Surf, Protect, and
switch all belong in the same branch map.

Spinblock does not end the route:
The Spikes article says Ghosts are the classic way to keep Spikes, but it also
calls out Pursuit support as part of the same subgame. It specifically names
Tyranitar as the strongest Ghost sniper, while warning that it must tread
carefully into Water pressure. The replay matched this: Gengar blocked
Tentacruel's Spin, then Tyranitar entered and Pursuit trapped it.

Gengar can punish the Pursuit step:
The GSC sample-team breakdown says Dynamic Punch gives Gengar a way to turn
around the Tyranitar matchup, preserving health against Pursuit. The threatlist
also names DynamicPunch as coverage for Steelix and Tyranitar. Once Gengar
revealed Dynamic Punch, low paralyzed Tyranitar was not just a trapper; it was
also a branch that Gengar could remove.

Rest counters after switching:
The prior Rest lesson remains correct, and this replay adds the switch-out
edge. Track the number of sleeping action turns actually spent. A Rest user
that switches out before `cant|slp` or Sleep Talk has not burned the same wake
count as one that stays active.

## Policy Corrections

- `hazard_loop_spin_window.md`: add Tentacruel spinner package and
  spinblock-to-Pursuit chain language.
- `branch_action_after_naming.md`: add Dynamic Punch/coverage as the follow-up
  when a Pursuit user enters to trap the spinblocker.
- `sleep_absorber_and_set_ambiguity.md`: extend Rest wake-count wording to say
  switch-out turns do not substitute for sleeping action turns.

## Measurement Note

Mixed but not progress. Compared with `rest_spin_phaze_transfer_001`, this run
improved acceptable-match from 30/49 to 35/49, route from 34/49 to 35/49, and
branch from 12/39 to 16/41 while keeping severe/hidden/state/mechanics at 0.
It is still not progress because top-match fell from 22/49 to 18/49 and
positive-selection fell from 37/49 to 36/49. The severe gate staying clean is
not enough.
