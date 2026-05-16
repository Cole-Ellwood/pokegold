# Tournament Variance and Tempo

Load when: the replay is tournament-tier (GSCLT2 / SPL / similar
league play, or rating >= 1400) AND it's an early-game decision
(turns 1-8) OR a setup-vs-pressure choice is on the table.

## The two priors

### 1. Pivot war dominates early game

Tournament-tier early game (t1-t6) is dominated by **double switches**.
Pros frequently pivot rather than play the "obvious" move. Across the
4-replay sample (iters 11, 13, 14, 15), there were 4+ simultaneous
double-switches in 8 early turns -- pivots outnumbered stay-in moves.

Decision rule:

- If your active threatens opp with damage AND opp has a clear better
  switch-in waiting, **assume opp pivots**. Pre-empt with your own
  pivot to the matchup that beats their incoming switch-in.
- If you and opp both have "wait one more turn" plays available
  (chip move vs setup mon), expect a double-switch and predict
  accordingly.
- The exception: if YOUR active is already in the favored matchup
  AND opp has no better pivot, stay in and press.

Signal that pivot is correct (not the move):
- Opp's active has revealed a "wall" or "setter" set (Skarmory,
  Cloyster, Forretress) that won't break your team and is on a
  Spikes/Whirlwind win condition.
- Your active is in a 50/50 matchup where pivoting denies opp's
  best line.
- The current matchup is "stalled" (neither side can break the other
  for several turns).

Signal that stay is correct:
- Your active KOs or 2HKOs opp's active and opp has no resist
  switch-in.
- Opp is on a HP timer (toxic, hazards) and pivoting saves them.
- You're setup'd or have a status that punishes opp's likely move.

### 2. Variance-EV > safe-line at tournament tier

Pros consistently pick the **higher-expected-value move** even when
it's higher variance, over the **safer / lower-variance alternative**.

Documented examples (iter 15 -2588552337):

| Position | Safe line (predicted) | Variance-EV (pro) |
| --- | --- | --- |
| Zap vs Snorlax lead | Thunder Wave (100% para) | Thunder (70% acc; damage + 30% para chance) |
| Snorlax vs Zap lead | Body Slam chip | Curse (commit to wincon) |
| Steelix vs Para CurseLax | Roar (reset setup) | Curse (own setup; win race) |
| CurseLax para vs Curse Steelix | Rest (heal+cure) | Double-Edge (damage commit + recoil) |

Decision rule:

- If a high-variance move's EV is clearly higher than the safe move's
  EV (e.g. Thunder 0.7 * (damage + para chance) > 1.0 * (just para)),
  pick the variance line.
- If the variance line is the team's **wincon** (Curse setup, Boom
  commitment, Lovely Kiss sleep), pick it on the FIRST opportunity --
  pros open with their wincon, they don't drift toward it.
- The exception: if losing the variance roll is **game-losing**
  (e.g. Self-Destruct that doesn't KO the threat), pick safety.

## Anti-patterns to avoid

- Predicting Roar / Whirlwind / Toxic as the "safe response" when the
  position rewards your own setup or own win condition commit.
- Predicting "Body Slam / chip move" as the response to a setup wall
  when the wall can outlast your chip; setup or pivot is correct.
- Predicting "Sleep Powder / Lovely Kiss" as the lead opener when the
  opp lead is 2x weak to a coverage move (e.g. Jynx vs Exeggutor:
  Ice Beam beats Lovely Kiss for EV).
- Predicting "stay-in and keep pressing" when both sides are
  pivot-positive and a double-switch is the pro line.

## Cross-reference

- Case examples: `gen2ou-2588552337_t{1-4}_*_iter15`,
  `gen2ou-2591556155_t{1-4}_*_iter14`, `gen2ou-2588645722_t{1-3}_*_iter13`
- Related cards: `name_next_board_owner.md` (pivot prediction),
  `branch_punish_ranking.md` (move-priority within a branch).
- Open question (post-CONSOLIDATE iter 20+): does the ladder-tier
  (1300) prior REVERSE this pattern? Iter 11 (-2608087104 ladder)
  had 42.9% top-match, suggesting ladder pros lean more toward
  safe-line predictions. Calibrate per-tier.
