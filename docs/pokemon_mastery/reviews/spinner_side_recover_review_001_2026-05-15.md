# Spinner Side/Recover Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/spinner_side_recover_transfer_001_gen2ou-2605980867_2026-05-15.md`

Reason for study:
The fresh transfer was not perfect. The main hard error was a state error:
recommending Rapid Spin for Starmie when Spikes were on the opponent's side,
not Starmie's side. The other misses were positive-selection failures around
Starmie Recover, Zapdos/Snorlax pressure handoffs, and Nidoking double-switch
punishment.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/active_pressure_before_status.md`
- `reviews/hazard_ownership_review_001_gen2ou-2544443857_2026-05-14.md`
- `workspace/quick_tests/statused_spinner_handoff_probe_001_2026-05-14.md`
- `workspace/quick_tests/three_check_transfer_001_gen2ou-2544443857_2026-05-14.md`
- `reviews/utility_screen_screech_review_001_2026-05-15.md`

Current web sources:

- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC OU Starmie:
  `https://www.smogon.com/forums/threads/gsc-ou-starmie.3692223/`
- Smogon Forretress OU Revamp:
  `https://www.smogon.com/forums/threads/forretress-ou-revamp-done.3647111/`
- Smogon GSC OU Threat List:
  `https://www.smogon.com/forums/threads/gsc-ou-threat-list-qc-2-2-gp-2.3477110/`
- Smogon Analysis of Leads in GSC OU:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`

## Confirmed Source Lessons

Spikes and Spin:
Smogon emphasizes that Spikes stay on the opponent's side until that side uses
Rapid Spin. Spikes and Rapid Spin have limited distribution, so a spinner or
setter costs team structure and should be used for real field-state progress,
not by species reflex.

Starmie:
Starmie is the premier Rapid Spin user because it combines high Speed with
Recover. It can also threaten Tyranitar, Nidoking, and Steelix with Surf and
has support options such as Thunder Wave and Reflect. In the transfer, this
means Starmie was not just a one-turn Spin button: after clearing Spikes, it
could Recover through repeated Rock Slide until p1 changed the pressure piece.

Forretress:
Forretress is a Spikes and Rapid Spin user, but its support value depends on
whether it keeps Spikes up, clears its own side, or uses coverage/cash-out to
stop the opposing support piece. Hidden Power Fire can swing the Forretress
mirror, and Explosion can be an emergency route tool, but the side and owner
must be named first.

Nidoking:
Nidoking is a mixed attacker with Lovely Kiss and broad coverage. It can punish
Forretress and Starmie-related support branches with sleep or coverage, but its
hidden move should not be treated as known before reveal.

## Policy Correction

Add a side-ownership gate before Rapid Spin:

1. Name the side with Spikes.
2. Confirm the active spinner can clear hazards from its own side.
3. If its own side is clean, do not make Spin top; rank pressure, status,
   recovery, or handoff instead.
4. If Spin succeeds and the spinner has Recover, immediately ask what stops the
   Recover loop before repeating weak damage.
5. If the opponent's support owner is likely to return, rank the double-switch
   or coverage that punishes that return.

## Measurement Note

No broad progress claim. The run improved several positive-selection metrics
but introduced a state error, so it cannot be counted as broad progress under
the active measurement rules.
