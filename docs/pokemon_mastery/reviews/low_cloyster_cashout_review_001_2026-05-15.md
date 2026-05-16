# Low Cloyster Cash-Out Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/low_cloyster_cashout_transfer_001_gen2ou-2605299310_2026-05-15.md`

Reason for study:
The fresh transfer was not perfect. It improved the prior state-error class,
but missed Vaporeon's hidden Ice Beam coverage into Exeggutor and under-ranked
Cloyster's Ice Beam plus Explosion cash-out into Tyranitar.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/cashout_boundary.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/hidden_role_voluntary_entry.md`
- `workspace/quick_tests/spinner_side_recover_transfer_001_gen2ou-2605980867_2026-05-15.md`
- `reviews/spinner_side_recover_review_001_2026-05-15.md`

Current web sources:

- Smogon Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon Cloyster OU Revamp:
  `https://www.smogon.com/forums/threads/cloyster-ou-revamp-qc-2-2-gp-2-2.3652352/`

## Confirmed Source Lessons

Cloyster:
Smogon sources consistently frame Cloyster as both a Spikes setter and an
offensive Explosion threat. Spikes enables teammates, but Cloyster's Surf/Ice
Beam coverage and Explosion are part of why normal resists, Grounds, and
spinners cannot treat it as passive. Therefore, a low Cloyster should not
automatically click Spikes if it has drawn the exact target that blocks the
next route.

Explosion:
The Explosion article emphasizes that trading can simplify the game or remove
a specific blocker for a teammate. That maps to the turn-16 miss: even though
Spikes were absent, Cloyster was low and Tyranitar was the exact active target.
If Cloyster cannot both lay Spikes and later convert them, the cash-out branch
can outrank the first layer.

Vaporeon:
The Threatlist describes Growth Vaporeon as a dangerous endgame sweeper with a
small but effective movepool. Ice Beam is not public until revealed, but when
Exeggutor is the obvious water answer, the coverage branch must be named as the
fallback before treating Sleep Powder as free progress.

## Policy Correction

No new broad card is needed. The existing cards already contain the boundary,
but the cash-out card needs this explicit reminder:

1. A support job that cannot be converted before the piece dies may be
   irrelevant.
2. If the active target is exact and removing it opens the next owner, cash-out
   can beat the undelivered layer.
3. Still name the absorber, immunity, and post-trade owner before making
   Explosion top.
4. Hidden coverage stays possible-only until reveal, but the coverage branch
   must be named when it is the main way the opponent beats the visible owner.

## Measurement Note

Limited positive transfer only. This run clears the provisional gates, but one
good public ladder replay cannot validate mastery or boss-sim readiness.
