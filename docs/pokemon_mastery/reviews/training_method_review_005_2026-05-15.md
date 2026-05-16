# Training Method Review 005 - 2026-05-15

Trigger:
After the resisted-Explosion and stall-route budget repairs, packets 038-040
provided 90 fresh side decisions:

- packet 038: 20/30 top, 28/30 acceptable, clean severe/hidden/state/mechanics;
- packet 039: 16/30 top, 26/30 acceptable, clean severe/hidden/state/mechanics;
- packet 040: 13/30 top, 24/30 acceptable, clean severe/hidden/state/mechanics.

Aggregate: 49/90 top, 78/90 acceptable, 0 severe, 0 hidden, 0 state, 0
mechanics. This fails the structural proof gate because exact top did not
stabilize above the target and packet 040 regressed.

## What Improved

- Severe, hidden-info, state, and mechanics gates stayed clean.
- Acceptable-match stayed high enough to show broad route competence.
- Packet 038 showed the compact cards can produce strong exact matching when
  the oracle is clean.
- Packet 039 found a real stall-budget repair without creating a severe error.

## What Is Still Failing

The current bottleneck is not simply "more notes." Two method issues are now
visible:

1. Sparse side-known packets are weak exact-top oracles. Packet 040 exposed only
   five own Pokemon, Zapdos had only `Thunder`, Snorlax had no recovery or
   self-KO move, and the sixth slot was absent. A player-side advisor normally
   knows those facts; the helper did not.
2. Exact top is still vulnerable to branch-rank calibration: Body Slam versus
   Earthquake, Steelix versus Snorlax into Raikou, staying to punish Rapid Spin,
   and Leech Seed timing were mostly covered by existing cards but not applied
   consistently.

This means replay review remains useful, but the selection/scoring method must
stop treating every side-known reconstruction as equally clean.

## Source Check

Current GSC sources support the concrete packet-040 lessons:

- Snorlax Body Slam / Earthquake pressure is a real branch-covering package,
  not just generic damage:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
  `https://www.smogon.com/forums/threads/snorlax-update-qc-2-2-gp-2-2-finished.3467216/`
- Forretress's Giga Drain / Rapid Spin / Spikes triangle against Cloyster and
  Golem is source-supported:
  `https://www.smogon.com/forums/threads/forretress-ou-revamp-done.3647111/`
- Golem's Rapid Spin plus Earthquake makes spin denial and route punishment
  concrete:
  `https://www.smogon.com/forums/threads/golem-ou-revamp-qc-2-2-gp-2-2.3647044/`
- Steelix is a real Raikou answer, while Raikou Hidden Power coverage remains a
  priced branch rather than a reason to avoid Steelix by default:
  `https://www.smogon.com/forums/threads/raikou-analysis.68429/`

## Method Repair

Patch the replay protocol with a side-known completeness gate:

- Before counting a side-known packet toward structural proof, inspect the
  helper's own-side reconstruction at turn 1.
- Prefer sides with six own Pokemon and at least two or three revealed eventual
  moves on the pieces likely to make early decisions.
- If the reconstruction has fewer than six own Pokemon, one-move core pieces,
  or missing recovery/self-KO/coverage on central jobs, label it
  `partial_side_known_sparse`.
- Sparse packets can still be practice and can reveal method errors, but exact
  top-match should not be used as clean proof. Use acceptable-match,
  oracle-quality, and policy-miss labels instead.

Also add a scoring label for `retrieval_failure`: a miss already covered by a
live card but not applied. Do not patch a new heuristic for every retrieval
failure.

## Next Gate

Do not claim progress. Restart fresh replay sampling with the side-known
completeness prefilter. The next countable packet should be side-known complete
or explicitly reported as partial/sparse and excluded from proof claims.
