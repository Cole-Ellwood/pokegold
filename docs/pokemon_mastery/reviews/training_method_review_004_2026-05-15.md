# Training Method Review 004 - 2026-05-15

Trigger:
After adding `oracle_quality`, packets 035-037 produced 42/92 raw top with
high acceptable-match and 0 severe/hidden/mechanics errors. Packet 036 had a
good clean-oracle subset, but packet 037 fell back to 13/30 raw and 13/25
clean-oracle top. That is flat enough to stop replay grinding.

## What Improved

The simplified docs and role-package ledger are helping with floor control:

- severe blunders stayed at 0 across packets 032-037;
- hidden-info and mechanics errors stayed clean in packets 035-037;
- answers are usually positive and route-aware rather than generic safe moves;
- pre-boom survival checks transferred on packet 036 and several packet 037
  turns.

## What Is Still Failing

Top-rank calibration is weak. I am now often finding a valid converter, then
ranking it first even when a reversible move or handoff preserves the same
route and keeps the irreversible converter available.

The pattern is not "docs too large" anymore. It is a ranking policy problem:

- T9 packet 037: GrowthPass handoff was a plausible route, but Curse was the
  lower-commitment line that still handled the sleeping-Cloyster branch and the
  Snorlax handoff.
- T11 packet 037: Self-Destruct was correct soon, but one more Curse made it
  cleaner.
- T18/T19/T24/T29 packet 037: Explosion was playable, but ordinary Earthquake,
  preservation, or loop pressure often covered the switch branch while keeping
  Steelix's boom available.
- T26/T27 packet 037: Alakazam Encore and Special Defense drops mean "status or
  switch" is not automatically better than continuing the live damage route.

## Sources Read

Local:

- `live_core.md`
- `heuristic_core/spend_or_save_piece.md`
- `heuristic_core/branch_punish_ranking.md`
- `heuristic_core/reset_loop_denial.md`
- `heuristic_core/role_package_ledger.md`
- `replay_turn_pause_protocol.md`

Web:

- Smogon Forums, Alakazam:
  `https://www.smogon.com/forums/threads/alakazam-done.3665488/post-8489045`
- Smogon Forums, GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`

## Method Repair

Add one compact calibration rule to `spend_or_save_piece.md`:

If a reversible move or handoff covers the active target and named branch while
preserving the Explosion, Self-Destruct, Baton Pass, or other irreversible
converter for the next forced choice, rank the reversible line first. Make the
irreversible converter top only when delay lets the target reset, escape,
remove the user, or invalidate the route.

This keeps positive selection but should reduce premature cash-out top ranks.

## Next Gate

Do not claim progress from this review. Run one small regression drill for
irreversible-converter calibration, then restart a fresh packet. The fresh
packet must report raw top, clean-oracle top, acceptable, positive selection,
route conversion, branch punish, and severe/hidden/state/mechanics together.
