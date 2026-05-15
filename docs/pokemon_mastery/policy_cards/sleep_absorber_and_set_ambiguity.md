# Policy Card: Sleep Absorber And Set Ambiguity

Status: active boundary card.

Use when: sleep, RestTalk, Lovely Kiss, sleep absorber choice, or Snorlax set
uncertainty affects the next route.

Trigger:

- A Pokemon has been put to sleep.
- The sleeper's future value depends on Sleep Clause, wake turns, RestTalk, or
  being saved as an absorber.
- Snorlax or another bulky pivot has unrevealed set information that changes
  the correct response.

Default:

Treat sleep as a route-state change, not a script. A Pokemon put to sleep is
often switched out and preserved to exploit Sleep Clause value instead of
burning wake turns and becoming sleep bait again. Before staying in, name what
the sleeper gains by burning turns now.

Track sleep by side. If the opponent has not slept one of our Pokemon yet, a
live Hypnosis, Lovely Kiss, Sleep Powder, or similar move still demands an
absorber plan even if we already slept one of theirs.

Opposite boundary:

Stay in or spend the sleeper when it has an active job that changes the next
board: absorbing a hit no one else can take, denying setup, forcing damage,
using Sleep Talk into a favorable board, forcing Rest cycles, or buying the
exact handoff the route needs.

Exceptions:

- Do not assume the revealed sleeper is the future sleep source or absorber.
- Do not assign Lovely Kiss, RestTalk, or coverage from species alone.
- RestTalk possibility is not proof to stay; if the opponent's counter-pivot
  takes over, switch out and save the sleeper.
- Do not overcorrect: revealed RestTalk can stay when no public teammate owns
  the branch better, but wake-count tracking must be exact.
- If the opponent's best punish is a double, setup, Explosion, or free Spikes,
  preserving the sleeper may still lose tempo.
- If the opponent acts before a Rest user wakes, status into the still-sleeping
  target may fail; price damage, hazards, setup, or handoff instead.
- If a low target can Rest before our attack lands, do not treat current HP as
  the target. Re-score against the healed or sleeping board before choosing
  recoil, self-KO, or last-hit damage.

Worst branch:

You burn sleep turns out of habit, the sleeper wakes into no job, then gets put
back to sleep or gives the opponent a free converter.

Local status:

Vanilla GSC policy source. Local romhack sleep duration, Sleep Talk, Rest, boss
AI, and clause behavior need local verification when decision-relevant.

Evidence:

- `quick_tests/replay_turn_pause_052_lovely_kiss_snorlax_sleep_pivot_smogtours-gen2ou-923076_2026-05-14.md`
- `quick_tests/unassigned_sleep_source_snorlax_pricing_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_053_curselax_phaze_cashout_smogtours-gen2ou-922830_2026-05-14.md`
- `quick_tests/snorlax_set_ambiguity_phaze_cashout_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_057_sleep_absorber_trade_handoff_smogtours-gen2ou-922568_2026-05-14.md`
- `quick_tests/mixed_cashout_sleep_handoff_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_058_rest_sleeper_handoff_gen2ou-2595967411_2026-05-14.md`
- `quick_tests/rest_sleeper_handoff_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_059_rest_phaze_status_smogtours-gen2ou-888483_2026-05-14.md`
- `quick_tests/phaze_loop_rest_timing_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_060_fixed_helper_phaze_transfer_smogtours-gen2ou-912658_2026-05-14.md`
- `quick_tests/replay_turn_pause_064_branch_action_restatement_smogtours-gen2ou-907834_2026-05-14.md`
- `quick_tests/preservation_boundary_probe_001_2026-05-14.md`
- `quick_tests/replay_turn_pause_066_branch_action_transfer_smogtours-gen2ou-920441_2026-05-14.md`
- `quick_tests/replay_turn_pause_069_support_action_transfer_smogtours-gen2ou-917918_2026-05-14.md`
- `quick_tests/sleeper_spinner_immunity_branch_probe_001_2026-05-14.md`
- `quick_tests/self_ko_absorber_transfer_001_smogtours-gen2ou-921984_2026-05-14.md`
- `quick_tests/branch_cashout_coverage_sleeptalk_transfer_001_smogtours-gen2ou-914172_2026-05-14.md`
- `quick_tests/setup_coverage_sleeptalk_handoff_probe_001_2026-05-14.md`
- `quick_tests/setup_coverage_sleeptalk_handoff_transfer_001_smogtours-gen2ou-914178_2026-05-14.md`
- `quick_tests/paired_handoff_probe_001_2026-05-14.md`
- `quick_tests/paired_handoff_transfer_001_smogtours-gen2ou-920763_2026-05-14.md`
- `quick_tests/rest_sleeper_cleric_trade_probe_001_2026-05-14.md`
- `quick_tests/ghost_electric_trap_phaze_transfer_001_smogtours-gen2ou-920777_2026-05-14.md`
- `quick_tests/electric_receiver_resttalk_transfer_001_smogtours-gen2ou-920928_2026-05-14.md`
- `quick_tests/resttalk_hidden_role_correction_probe_001_2026-05-14.md`
- `quick_tests/hidden_role_electric_transfer_002_smogtours-gen2ou-920961_2026-05-14.md`
- `quick_tests/support_set_hidden_role_probe_001_2026-05-14.md`
- `quick_tests/support_set_hidden_role_transfer_001_smogtours-gen2ou-921372_2026-05-14.md`
- `quick_tests/counter_handoff_loop_transfer_001_smogtours-gen2ou-921389_2026-05-14.md`
- `quick_tests/setup_hidden_role_stop_probe_001_2026-05-14.md`
- `quick_tests/setup_hidden_role_stop_transfer_001_smogtours-gen2ou-921412_2026-05-14.md`
- `quick_tests/low_rest_race_cashout_probe_001_2026-05-14.md`
- `quick_tests/low_rest_race_transfer_001_gen2ou-2544449982_2026-05-14.md`
- `reviews/low_rest_race_review_001_gen2ou-2544449982_2026-05-14.md`

Drill:

Score three sleep positions: immediate switch to preserve Sleep Clause value,
stay to perform an active absorber job, and re-solve after Snorlax reveals a
set-changing move.
