# Spinblock/SubGrowth Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/spinblock_subgrowth_transfer_001_smogtours-gen2ou-932556_2026-05-15.md`

Reason for study:
The fresh transfer was imperfect and not progress. Severe errors stayed clean,
but top-match fell, branch-punish obedience was poor, and one hidden-info error
appeared from promoting possible-only item state into a Thief recommendation.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/active_pressure_before_status.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/cashout_boundary.md`
- `policy_cards/hidden_role_voluntary_entry.md`
- `reviews/leech_resttalk_phaze_review_001_2026-05-15.md`

Current web sources:

- Smogon Dex, Forretress GSC:
  `https://www.smogon.com/dex/gs/pokemon/forretress/`
- Smogon Dex, Gengar GSC:
  `https://www.smogon.com/dex/gs/pokemon/gengar/`
- Smogon Dex, Jolteon GSC:
  `https://www.smogon.com/dex/gs/pokemon/jolteon/`
- Smogon Dex, Starmie GSC:
  `https://www.smogon.com/dex/gs/pokemon/starmie/`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums, GSC OU sample teams breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Pikalytics current GSC Forretress, Gengar, Jolteon, and Starmie snapshots:
  `https://www.pikalytics.com/pokedex/gsc/Forretress`
  `https://www.pikalytics.com/pokedex/gsc/Gengar`
  `https://www.pikalytics.com/pokedex/gsc/Jolteon`
  `https://www.pikalytics.com/pokedex/gsc/Starmie`

## Confirmed Source Lessons

Forretress can convert with coverage:
Current Smogon and usage sources continue to frame Forretress as a Spikes,
Spin, Explosion, and coverage Pokemon rather than a passive hazard token. The
transfer made Hidden Power public into Gengar, which changes the whole branch:
the question becomes whether Hidden Power keeps the spinblock from controlling
the hazard loop, not whether Forretress should always hand off because Gengar
is active.

Gengar support moves alter the receiver map:
Smogon material and current usage both support mixed Gengar utility packages:
Ice Punch or elemental coverage, Explosion, Hypnosis, and disruptive options.
Dynamic Punch in this replay was a branch-punish attempt against Forretress:
confusion threatens the revealed Hidden Power line and can buy Gengar or Zapdos
the next board. The correction is to score utility by the follow-up it enables.

Jolteon Substitute/Growth is a package, not a one-turn oddity:
Jolteon commonly threatens Electric pressure, Substitute, Growth, and pass or
cleanup sequences. Against Starmie, repeated Surf was not passive because it
broke Substitute and denied free setup. The handoff to Snorlax became correct
only after Thunderbolt was public; before that, switching too early allowed the
Substitute package to develop.

Starmie must choose between Spin job and active denial:
Smogon Spikes material treats Starmie as a spinner, but the transfer board
made Surf the immediate converter: it KOed Nidoking and then broke Jolteon's
Substitute. Rapid Spin was not the route while Gengar was alive and the active
threat could be denied directly.

Thief requires item-state discipline:
Thief move access is not the same as item-removal permission. The replay's
Nidoking had Thief but later revealed Leftovers, so my turn-11 item-removal
line anchored on possible-only item state. The correction belongs in the item
and hidden-role cards: no item recovery at full HP is not public no-item
evidence, and a Thief recommendation must name the item-state fallback.

## Policy Corrections

- `active_pressure_before_status.md`: tighten item-removal wording so Thief
  requires public no-item evidence or a marked high-risk read.
- `branch_action_after_naming.md`: add revealed-coverage language for support
  pieces that can hit their blocker after the move is public.
- `hazard_loop_spin_window.md`: add spinblock coverage language: when the
  setter has revealed coverage into Gengar, pressure can beat handoff or Spin.
- `support_handoff_after_job.md`: add scout-to-conversion language after Protect
  or a support reveal.
- `hidden_role_voluntary_entry.md`: add an item-state gate for Thief and other
  item-dependent role reads.

## Measurement Note

Mixed but not progress. Compared with `leech_resttalk_phaze_transfer_001`, this
run had higher positive-selection and a barely higher acceptable percentage,
but top-match fell from 19/47 to 14/49, branch-punish fell from 13/37 to 9/38,
and hidden-info errors rose from 0 to 1. No broad progress claim is allowed.
