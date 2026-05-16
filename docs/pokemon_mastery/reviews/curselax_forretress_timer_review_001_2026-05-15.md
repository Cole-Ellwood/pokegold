# CurseLax/Forretress Timer Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/curselax_forretress_timer_transfer_001_smogtours-gen2ou-933685_2026-05-15.md`

Reason for study:
The fresh transfer was not perfect and was not progress. It stopped at turn 23
after a clear positive-selection miss: p1 had a +3 poisoned Snorlax and I chose
Rest as the top line over immediate Double-Edge; p2 had Forretress in front of
that Snorlax and I promoted unrevealed Explosion over the broader public
Forretress move pool.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `policy_cards/cashout_boundary.md`
- `policy_cards/hidden_role_voluntary_entry.md`
- `reviews/ground_receiver_triangle_review_001_2026-05-15.md`
- `reviews/status_setup_handoff_review_001_2026-05-15.md`
- `reviews/leech_resttalk_phaze_review_001_2026-05-15.md`
- `reviews/rest_spin_phaze_review_001_2026-05-15.md`
- `reviews/spinner_side_recover_review_001_2026-05-15.md`
- `reviews/spinblock_subgrowth_review_001_2026-05-15.md`
- `reviews/low_rest_race_review_001_gen2ou-2544449982_2026-05-14.md`
- `reviews/2026-05-13_smogtours-gen2ou-861526.md`

Current web sources:

- Smogon GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Snorlax update:
  `https://www.smogon.com/forums/threads/snorlax-update-qc-2-2-gp-2-2-finished.3467216/`
- Smogon Forretress OU Revamp:
  `https://www.smogon.com/forums/threads/forretress-ou-revamp-done.3647111/`
- Smogon Rest Forretress and Role Compression:
  `https://www.smogon.com/forums/threads/rest-forretress-and-role-compression-2021-gsc-cup-run-review.3691632/`
- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`
- Smogon Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Pikalytics current GSC Snorlax and Forretress snapshots:
  `https://www.pikalytics.com/pokedex/gsc/Snorlax`
  `https://www.pikalytics.com/pokedex/gsc/Forretress`

## Source-To-Policy Extraction

Boosted Snorlax is not preservation-first:
Smogon frames CurseLax around Curse, Rest, and a strong STAB, with Double-Edge
specifically threatening switch-ins and even Normal resists after boosts.
Current usage also keeps Double-Edge and Rest both high, which matters for tier
discipline: Rest is a strong prior on the set, but Double-Edge is the public
route question once Curse is revealed and boosts are already banked. On turn
23, +3 Double-Edge took Forretress from 96 to 51 through resistance and forced
the board forward before Toxic could outrun the converter.

Toxic is a timer, not an automatic Rest command:
The GSC status and Spikes sources both support using status and hazards to
force Rest, but forcing Rest is only progress if the sleeping board favors the
resting side's opponent. If the poisoned boosted Pokemon can take one more
route-changing hit first, the positive move can be attack now, then Rest or
switch later. My old answer compressed "Toxic landed" into "Rest now."

Forretress has compression, not a single hidden move:
Smogon sources repeatedly describe Forretress as Spikes, Rapid Spin, Toxic,
coverage, and Explosion compression. Pikalytics currently shows Explosion as
common, but also shows Toxic, Rapid Spin, and Hidden Power Fire as live
high-usage options. This means Explosion is a strong prior, not revealed fact.
After Spikes and Toxic are public, the last slots remain ambiguous; the advisor
must price Hidden Power/coverage, switch, and Spin before making Explosion the
main line.

Forretress Explosion is defensive and contextual:
The Explosion guide explicitly treats Forretress Explosion as secondary to
Forretress's main Spikes role and mostly a defensive emergency or endgame trade.
That does not make Explosion wrong into a boosted threat; it makes the
precondition stricter. Name the target, whether Forretress moves before the
target, the expected damage after boosts/Reflect, the post-trade owner, and
the fallback if Explosion is absent or not worth the trade.

Local docs already contained most of the cure:
`cashout_boundary.md` warned not to promote full-health Explosion from species
memory, `hidden_role_voluntary_entry.md` required revealed/strong-prior/
possible-only tiers, and `branch_action_after_naming.md` had setup-into-
receiver language. The missing optimization was a tighter boosted-timer rule:
after the setup is already banked and the status clock starts, re-rank damage,
Rest, more setup, and handoff by which one converts the next two turns.

## Policy Updates Made

- `branch_action_after_naming.md`: added boosted-timer conversion wording so
  Snorlax-like setup pieces rank attack versus Rest versus another boost after
  the status timer starts.
- `hazard_loop_spin_window.md`: tightened Forretress compression so Hidden
  Power/coverage, Spin, Spikes, Toxic, switch, and Explosion stay tiered.
- `cashout_boundary.md`: added a Forretress defensive-Explosion gate.
- `active_context.md`: pointed the next rep at boosted timer conversion,
  Forretress move-tier discipline, and early sleep/receiver assignment.

## Measurement Note

Not progress. Compared with `resttalk_substarmie_phaze_transfer_001`, this
run had 16/45 top versus 20/48, 31/45 acceptable versus 39/48, 36/45 positive
versus 36/48, 33/45 route versus 34/48, and 15/36 branch versus 24/41. Severe,
state, and mechanics stayed at zero, but the hidden-info error repeated and
the core branch-punish measure fell. Severe-blunder avoidance is only a gate;
this packet is study material, not a mastery claim.

## Next Rep

No new replay until the next work block starts again from `active_context.md`.
The next unseen transfer should force:

- boosted Snorlax or similar setup piece after Toxic/poison starts;
- Forretress after Spikes/Toxic with unrevealed fourth-slot ambiguity;
- early Lovely Kiss/Sleep Powder absorber assignment before active damage;
- spinblock/hazard handoff after both sides of Spikes are named.
