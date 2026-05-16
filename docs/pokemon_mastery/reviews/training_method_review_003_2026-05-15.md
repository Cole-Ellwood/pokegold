# Training Method Review 003 - 2026-05-15

Trigger:
Post-repair packets 032-034 after the compact role/package structure.

## Sample Result

Fresh post-repair side decisions:

- Packet 032: 21/30 top, 29/30 acceptable, 0 severe.
- Packet 033: 14/30 top, 27/30 acceptable, 0 severe.
- Packet 034: 12/30 top, 28/30 acceptable, 0 severe.

Combined: 47/90 top-match, 84/90 acceptable-match, 0 severe, 0 hidden-info,
0 mechanics. This is not progress. Severe-blunder control is repaired for this
sample, but exact top-match is flat/below gate and state/route misses still
move between related role-package classes.

## Diagnosis

The docs are not currently too large to retrieve. The live failures were not
caused by reading the wrong archive cards; the compact core was consistently
available and the helper enforced route transaction plus critical ledger.

The blocker is now mixed:

- Real play gaps remain: Pursuit trap spend/save, spinner status budget, and
  branch-punish timing after sleep/passive turns.
- Exact replay top-match is a noisy oracle when actual players choose
  high-variance or style-specific lines. Packet 034's repeated Thunder into
  Umbreon is informative but should not be overfit into "always keep clicking
  Thunder" as a policy rule.
- Side-known reconstruction is partial. The helper reports only moves shown in
  the replay, so exact choices involving unshown own moves or Hidden Power
  type should be tagged as own-move gaps.

Replay review is still useful because it exposed Pursuit-trap and hazard-tempo
misses. Replay review alone is not enough if exact-match is treated as the
only proof signal.

## Training Structure Change

Keep fresh replay transfer as the main practice loop, but every packet after
this must report:

1. exact `top_match`;
2. `acceptable_match`;
3. positive-selection / route conversion / branch punish;
4. severe/hidden/state/mechanics;
5. `oracle_quality` notes for exact-move mismatches:
   clean, route_equivalent, style_or_variance, own_move_gap, or unscored.

Do not let `oracle_quality` excuse a bad top move. Use it to decide what gets
patched:

- If the top move loses the route, patch the live heuristic or drill.
- If the top move is route-equivalent and actual is style/variance, record the
  top miss but do not add a new rule.
- If own moves are missing, label the turn and prefer future full-team-sheet
  or one-side reconstruction sources before making exact-move claims.

## Next Loop

Do not claim the compact system worked. Restart the sample loop only after the
Pursuit-trap drill and protocol change are in place. The next fresh packet must
track exact top, acceptable, route metrics, and oracle quality together.

If exact top remains low while acceptable and route metrics stay high, the next
method experiment should be expert-adjudicated replay review: fewer turns, but
with a post-score route-quality ruling from source-backed policy rather than
only actual-move agreement.
