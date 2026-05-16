# Steelix Curse/Roar Split Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/steelix_curse_roar_split_transfer_001_smogtours-gen2ou-933317_2026-05-15.md`

Reason for study:
The fresh transfer was imperfect and stopped early. It did not create severe,
hidden-info, state, or mechanics errors, but it repeated a positive-selection
miss: I treated Steelix as either Earthquake or Roar and under-ranked Curse
when the receiver cycle gave Steelix a boost turn before the phaze loop.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/active_pressure_before_status.md`
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/hazard_loop_spin_window.md`
- `reviews/ground_receiver_triangle_review_001_2026-05-15.md`
- `workspace/quick_tests/ground_receiver_triangle_transfer_001_gen2ou-2591556155_2026-05-15.md`
- `workspace/quick_tests/resttalk_substarmie_phaze_transfer_001_smogtours-gen2ou-933823_2026-05-15.md`
- `reviews/resttalk_substarmie_phaze_review_001_2026-05-15.md`

Current web sources:

- Smogon Forums GSC OU Steelix:
  `https://www.smogon.com/forums/threads/gsc-ou-steelix.3705042/`
- Smogon GSC OU Threatlist, Steelix section:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon Forums GSC OU Skarmory:
  `https://www.smogon.com/forums/threads/gsc-ou-skarmory.3709334/`
- Smogon GSC Good Cores:
  `https://www.smogon.com/forums/threads/gsc-good-cores.3536015/`

## Source-To-Policy Extraction

Steelix is a Curse plus Roar package:
Smogon Steelix material frames Earthquake, Curse, Roar, and Explosion as one
set. Earthquake threatens Electrics, Curse increases offensive presence and
lets Steelix contest physical routes, and Roar converts Spikes damage after
Steelix gets in on Raikou or Zapdos. The transfer miss was choosing the wrong
part of the package: Roar was right after the first boost, but Curse was right
before that loop was strong enough.

Skarmory can be a setup invitation and a coverage threat:
Smogon Skarmory material emphasizes physical walling, Toxic or Drill Peck,
Curse, Whirlwind or Sleep Talk, and Rest. This makes Skarmory a natural
receiver into physical pressure, but the replay also showed Hidden Power into
Steelix. The policy boundary is two-sided: before Hidden Power reveal, do not
anchor on it; after reveal, Steelix must price the damage clock before boosting
or phazing again.

Raikou Rest changes the loop:
The sample-team and Steelix sources both show Raikou/Steelix interactions as
central. When Raikou rests in front of Steelix, the route is not automatically
Earthquake into a helpless sleeper. The next question is whether Raikou stays
with Sleep Talk, switches to Skarmory or Starmie, or lets Steelix use Curse to
make future Roar and Earthquake more threatening.

Do not confuse progress with more phazing:
Hazard chip is progress only when the loop is stable. If a receiver lets
Steelix bank a boost without immediate danger, Curse can be the positive
selection. If Starmie, Surf, or revealed Hidden Power forces Steelix out or
KOs it before Roar, the handoff is the positive move instead.

## Policy Updates Made

- `hazard_loop_spin_window.md`: refined the Steelix phaze/setup split with a
  Curse-before-Roar reminder and a revealed-coverage damage-clock guard.
- `active_context.md`: moved the latest fresh-transfer pointer to
  `steelix_curse_roar_split_transfer_001` and made the next rep focus on
  Steelix-like phaze/setup split decisions.
- `measurement_progress_ledger.csv`: recorded the early-stop transfer and the
  constructed regression probe separately.

## Measurement Note

Mixed but not progress. The transfer went 10/22 top and 17/22 acceptable with
0 severe, hidden-info, state, and mechanics errors. Positive-selection was
16/22, route conversion 14/22, and branch-punish obedience 10/18. Those are
better than the prior early stop, but the packet is only 22 decisions and the
same Curse/Roar under-ranking repeated, so it is not a proof run.

The regression probe below is a local repair check only. It is not fresh
unseen evidence and cannot be used to claim mastery or boss-sim validation.
