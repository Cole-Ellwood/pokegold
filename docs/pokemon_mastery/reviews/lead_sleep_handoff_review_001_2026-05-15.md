# Lead Sleep/Handoff Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/lead_sleep_handoff_transfer_001_smogtours-gen2ou-935831_2026-05-15.md`

Reason for study:
The fresh transfer was not perfect and stopped early. The repeated miss was
lead sleep into counter-handoff: once the sleep absorber did its job, I kept
looking at the sleeping target or generic active pressure instead of naming the
next-board owner.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/hidden_role_voluntary_entry.md`
- `policy_cards/active_pressure_before_status.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `reviews/curselax_receiver_coverage_review_001_2026-05-15.md`
- `workspace/quick_tests/curselax_receiver_coverage_probe_001_2026-05-15.md`
- `reviews/snorlax_forretress_counter_handoff_review_001_2026-05-15.md`
- `workspace/quick_tests/early_cycle_counter_handoff_probe_001_2026-05-15.md`

Current web sources:

- Smogon Forums, An Analysis of Leads in GSC OU:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`
- Smogon Forums, Nidoking Revamp:
  `https://www.smogon.com/forums/threads/nidoking-revamp-qc-3-2-gp-2-2.3481273/`
- Smogon Forums, GSC OU Heracross:
  `https://www.smogon.com/forums/threads/gsc-ou-heracross.3699588/`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC OU Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon Forums, GSC Zapdos:
  `https://www.smogon.com/forums/threads/zapdos-qc-2-2-gp-2-2.3673848/`

## Confirmed Source Lessons

Lead Cloyster is a field-job piece:
The GSC leads article says Cloyster can get an excellent start against some
leads with Spikes, but is disadvantaged into Nidoking and other pressure leads.
That means both sides have a live branch: Cloyster wants its layer, while
Nidoking can disrupt with Lovely Kiss or coverage. If the sleep move misses,
the next turn is not a reset; Spikes are now public and the receiver map has
changed.

Nidoking is sleep plus prediction, not one button:
The Nidoking analysis supports Lovely Kiss, Thunder, and prediction-heavy
double-switch play. The correction is not "always click sleep" or "always
click coverage." Once a sleep absorber enters, choose between public pressure,
handoff, and coverage by information tier. Possible-only Fire coverage into
Heracross cannot anchor the main recommendation.

Heracross can absorb sleep but still leave:
Heracross sources support Rest/Sleep Talk sets and its ability to check some
physical attackers, but the local sleep card already says a sleeper may be
preserved after doing its job. A voluntary sleep absorption is evidence of
absorber value; it is not proof that Sleep Talk is public or that staying is
the route.

Zapdos pressure needs the Snorlax/Cloyster owner map:
Zapdos sources and the Spikes article support Zapdos as a dominant attacker,
especially with Spikes support, but Snorlax can still meet it when the opponent
is not taking Spikes. In this replay p1 had Spikes on its own side, not p2's.
That made "Thunder into Snorlax" less route-converting than the Cloyster
handoff into a Curse-capable Snorlax.

## Policy Correction

`sleep_absorber_and_set_ambiguity.md` should add one narrow lead-sleep handoff
extension:

After a lead sleep absorber takes sleep, immediately ask whether its job is
done. If Sleep Talk is not revealed, compare preserving the sleeper and moving
the next-board owner against attacking or burning sleep. Do not let possible
coverage into the sleeping absorber outrank the public handoff unless the
coverage is revealed, side-known, or explicitly a high-risk read.

## Measurement Note

Not progress. The packet scored 2/8 top and 6/8 acceptable with 0 severe,
state, or mechanics errors, but 1 hidden-info error. The main target metrics
were weak: only 5/8 positive-selection, 3/8 route-converting, and 4/8
branch-punish.

