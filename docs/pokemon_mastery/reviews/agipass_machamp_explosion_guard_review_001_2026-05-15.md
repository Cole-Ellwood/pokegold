# AgiPass Machamp/Explosion Guard Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/agipass_machamp_explosion_guard_transfer_001_smogtours-gen2ou-933493_2026-05-15.md`

Reason for study:
The fresh transfer was imperfect and stopped early. It showed the same
compound Baton Pass ledger problem as the prior packet, but with a different
receiver boundary: Machamp can punish Snorlax through Cross Chop crit risk,
yet immediate damage can still be the positive follow-up if it puts Machamp
in revenge range. The second boundary was Forretress Explosion into a revealed
Ghost.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/active_pressure_before_status.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/cashout_boundary.md`
- `policy_cards/hazard_loop_spin_window.md`
- `reviews/bp_chain_revealed_coverage_review_001_2026-05-15.md`
- `reviews/pass_package_sleeper_handoff_review_001_2026-05-15.md`

Current web sources:

- Smogon GSC Baton Pass:
  `https://www.smogon.com/forums/threads/gsc-bp.3541165/`
- Smogon GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon GSC OU Machamp:
  `https://www.smogon.com/forums/threads/gsc-ou-machamp.3705043/`
- Smogon Nidoking Revamp:
  `https://www.smogon.com/forums/threads/nidoking-revamp-qc-3-2-gp-2-2.3481273/`
- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC OU Threat List, Forretress section:
  `https://www.smogon.com/forums/threads/gsc-ou-threat-list-qc-2-2-gp-2.3477110/`

## Source-To-Policy Extraction

Jolteon pass asks for the receiver first:
Smogon Baton Pass material describes Jolteon as a classic Agility passer, while
the sample-team source explicitly lists Agility + Baton Pass enabling Snorlax,
Marowak, or Machamp. This transfer was a clean test of the new boost-ledger
policy. Once Jolteon used Agility, the answer had to name Machamp as a possible
receiver and then re-score Snorlax, Gengar, and Zapdos by that board.

Machamp is not solved by one defensive script:
Smogon Machamp material emphasizes Cross Chop's damage and increased critical
hit rate, and the BP source describes the passed Machamp set with Cross Chop,
Rock Slide, Hidden Power, and Meditate. The lesson is a two-sided boundary:
switching Gengar is correct when it covers Fighting pressure without giving
Machamp a better setup turn; staying with Snorlax is correct only if the hit
meaningfully puts Machamp into revenge range and the Cross Chop crit branch is
priced.

Support follow-up can be damage:
The turn-4 Curse was support into the Machamp receiver, but the turn-5 follow-up
was not another safe handoff. Double-Edge put Machamp from full to 35 after
Leftovers, which made the later Zapdos revenge route possible. The old
overcorrection would switch every Snorlax away from Machamp. The correction is
to ask whether the support move created a damage threshold before switching.

Nidoking is the real Electric receiver when revealed:
Smogon Nidoking material supports Lovely Kiss, Electric immunity, Toxic
immunity, and broad coverage, with Fire Blast as a real but optional Forretress
punish. In this replay, the correct turn-8 handoff was not generic Gengar
preservation; it was Nidoking, because it blanked Electric pressure and
threatened the next Baton Pass receiver. Fire Blast stayed possible-only until
public, which was the correct information tier.

Forretress Explosion needs the revealed Ghost check:
Smogon Spikes and threat-list material frame Forretress as Spikes, Spin,
physical wall, and Explosion compression. Explosion can change a game, but this
replay had Gengar revealed and healthy. Once Forretress had already set Spikes
and was facing Nidoking, the defensive question was whether the Ghost handoff
covers Explosion while preserving route pressure. It did, and the replay used
that handoff.

## Policy Updates Made

- `branch_action_after_naming.md`: added passed-Fighting receiver wording for
  Agility-pass Machamp, Cross Chop crit risk, and revenge-range damage.
- `support_handoff_after_job.md`: added damage-threshold follow-up wording after
  support moves like Curse or Reflect.
- `cashout_boundary.md`: added a defending support-Explosion guard when a
  revealed Ghost or immunity owner can enter.
- `active_context.md`: pointed the next rep at pass-receiver defensive-owner
  choice, damage thresholds after support, and Forretress Explosion guards.

## Measurement Note

Not progress. This was an early-stop packet with only 20 scored decisions, so
it is study material rather than a primary proof run. Severe, hidden, state,
and mechanics stayed clean and acceptable was above gate, but top-match was
7/20 and route conversion was 12/20. The pass-chain error class repeated, so
the next countable work should either target that boundary directly or choose a
fresh replay and stop only after the pass receiver ledger is handled cleanly.
