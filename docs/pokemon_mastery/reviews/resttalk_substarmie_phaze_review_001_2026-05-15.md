# RestTalk/SubStarmie Phaze Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/resttalk_substarmie_phaze_transfer_001_smogtours-gen2ou-933823_2026-05-15.md`

## Miss Pattern

The replay exposed a repeated positive-selection boundary:

- I sometimes treated support pieces as having one fixed job after the first
  reveal. Steelix was not only Earthquake or only Roar; it had to choose Roar
  while Spikes phazing was live, then Curse once Forretress broke the loop.
- I underweighted revealed RestTalk. After Sleep Talk was public, sleeping
  Zapdos and Raikou were active route pieces, not passive sleepers to switch
  out by default.
- I underweighted Substitute Starmie. Its Substitute was a pressure shield that
  made repeated Surf into Zapdos a route, because Thunder could miss or only
  break the shield.
- I repeated a hidden-info failure class by ranking unrevealed Gengar Fire
  Punch as the main move into Forretress instead of marking it as a high-risk
  coverage read with Thunderbolt/Hypnosis fallback.

## Source Study

Web sources read after scoring:

- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC Status:
  `https://www.smogon.com/resources/competitive/gs/status`
- Smogon GSC Starmie forum analysis:
  `https://www.smogon.com/forums/threads/gsc-ou-starmie.3692223/`
- Smogon GSC OU Threat List:
  `https://www.smogon.com/forums/threads/gsc-ou-threat-list-qc-2-2-gp-2.3477110/`
- Smogon Analysis of Leads in GSC OU:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`
- Smogon GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Bulbapedia Rest:
  `https://bulbapedia.bulbagarden.net/wiki/Rest_(move)`

Local docs read after scoring:

- `policy_cards/branch_action_after_naming.md`
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `reviews/ground_receiver_triangle_review_001_2026-05-15.md`
- `reviews/spinner_side_recover_review_001_2026-05-15.md`
- `reviews/spinblock_subgrowth_review_001_2026-05-15.md`
- `reviews/rest_spin_phaze_review_001_2026-05-15.md`

## Source-To-Policy Extraction

Smogon's Spikes material supports Steelix as a Spikes phazer because it can set
up Curse on common opponents and repeatedly Roar counters through Spikes. The
transfer miss was choosing the wrong half of that package at the wrong time:
Earthquake into Skarmory branches missed Roar, and later Roar overcalled after
Forretress entered to break the loop. The policy needs a split: keep Roar when
the loop is stable; use Curse or coverage when the opponent's loop-breaker is
entering.

Smogon and Bulbapedia confirm two RestTalk mechanics that mattered. Rest fails
at full HP, so Raikou's full-HP Rest did not cure paralysis. In Generation II,
Rest can be called by Sleep Talk and works, which means revealed RestTalk is a
real active route, not only a switch-out signal. This supports a tighter
revealed-RestTalk boundary.

Smogon Starmie material supports Substitute + Surf as a coherent set, not just
a spinner variant. Substitute lets Starmie stay in against Electric-types and
exploit Thunder's miss chance. In this replay, switching Starmie out from
behind Substitute gave up a live Surf route; the right question was whether
Thunder breaks the shield or misses, not whether Electric type advantage
automatically wins.

Smogon lead material also supports the turn-1 correction: Smeargle can set
Spikes, sleep, pass, or surprise, while Electrics use Thunder, Thunder Wave,
Roar, or doubles to expose the opponent's structure. That means early support
choice must identify the route piece it enables; Spore is not automatically
the best support move.

## Policy Updates Made

- `sleep_absorber_and_set_ambiguity.md`: added Rest full-HP failure and
  revealed-RestTalk boundary wording.
- `hazard_loop_spin_window.md`: added Steelix Roar/Curse split and Substitute
  Starmie pressure wording.
- `branch_action_after_naming.md`: added revealed coverage over STAB wording
  for Ghost/Normal branches.
- `active_context.md`: pointed the next rep at revealed RestTalk, SubStarmie,
  Steelix Roar/Curse split, and possible-only coverage discipline.

## Measurement Note

Not progress. Compared with `ground_receiver_triangle_transfer_001`, the
severe/state/mechanics gates stayed clean and acceptable stayed above gate, but
top-match remained below gate, positive-selection and route conversion dipped,
and hidden-info errors stayed at 1. Under the active rules, this is more study
material, not evidence of mastery.
