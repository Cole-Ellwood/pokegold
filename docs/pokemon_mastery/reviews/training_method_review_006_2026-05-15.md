# Training Method Review 006 - 2026-05-15

Trigger:
After side-known completeness and wake-prompt repairs, packets 041-043 produced
89 scored fresh side decisions:

- packet 041: 16/30 top, 23/30 acceptable, 1 state/mechanics error;
- packet 042: 14/30 top, 24/30 acceptable, clean severe/hidden/state/mechanics;
- packet 043: 18/29 top, 25/29 acceptable, clean severe/hidden/state/mechanics.

Aggregate: 48/89 top, 72/89 acceptable, 0 severe, 0 hidden, 1 state, 1
mechanics. This is not meaningful progress versus packets 038-040 at 49/90
top and 78/90 acceptable.

## Diagnosis

The compact docs are not the main wall now. Startup context stayed small:
`active_context.md`, `live_core.md`, and a few tiny cards were enough to avoid
Team Preview leakage, severe blunders, and most mechanics mistakes. Packet 043
also showed the compact system can execute known route patterns: lead sleep,
Spikes -> spinblock, Reflect -> Whirlwind, and Substitute/Growth Jolteon.

The wall is top-rank branch calibration. I often have the actual move in the
top three, but rank a different branch first:

- preserve versus spend: Gengar Explosion was over-ranked on packet 043 turn
  11, then correctly ranked on turn 22;
- exact removal versus overguard: packet 043 turn 19 should have kept Snorlax
  in for Earthquake instead of switching;
- hazard loop order: packet 042 turns 6-9 alternated between Spikes-first,
  Spin-first, and spinblock choices;
- setup timing: packet 043 turns 24-26 showed Thunder -> Growth -> Substitute,
  while I swapped the first two steps.

Replay review is still useful, but exact imitation alone is too noisy to
diagnose the wall. Actual replay moves include hidden player reads, style,
full paralysis/confusion/no-action gaps, and team-context branches that the
side-known helper only partially reconstructs.

## Method Repair

Keep replay review, but score branch-ranking explicitly so the next loop knows
whether the problem is missing candidates or misordering them.

Add these labels to fresh replay artifacts:

- `actual_in_top_three`: whether the actual move/switch was one of the frozen
  ranked candidates.
- `actual_branch_named`: whether the receiver, absorber, cash-out, setup, or
  reset branch that happened was named before reveal.
- `top_rank_failure`: one of `branch_probability`, `route_budget`,
  `oracle_style`, `own_move_gap`, `state`, `mechanics`, `hidden_info`, or
  `missing_candidate`.

Interpretation:

- If `actual_in_top_three` is high but top-match is flat, train branch
  probability and route-budget ordering rather than adding more cards.
- If `actual_branch_named` is low, the live prompt is not forcing enough
  opponent-branch construction.
- If `missing_candidate` repeats, patch the relevant tiny card or source note.
- If `oracle_style` dominates, stop treating that packet as exact-top proof and
  use acceptable/route metrics.

## Next Loop

Run the next fresh packet with the new labels. Do not claim progress from this
sample. The target is no longer just "more exact top"; it is:

- exact top above the recent 54% level;
- acceptable at least stable;
- actual-in-top-three high enough to prove candidates are being generated;
- branch-probability failures decreasing;
- severe/hidden/state/mechanics still low.

If top stays flat and actual-in-top-three is already high, shift one work block
away from replay prediction into expert replay annotation: pause before key
turns and write why the pro ranked that branch first, without scoring it as a
fresh packet.
