# Heuristic: Route-Budget Tiebreaking

Status: live tiny card.

Use when: the serious candidates are already plausible, especially when the
actual or pro move is likely to be in the top three but the top rank is flat.

Rule: promote the move that buys the route, not the move that is easiest to
defend afterward.

Branch-resource veto before promotion:

- If the tempting #1 spends, exposes, or fails to include the only piece that
  holds a live route job, it cannot stay #1 unless it converts immediately.
- If the worst plausible branch is already named, the #1 candidate must either
  beat that branch or preserve the piece that beats it. Otherwise promote the
  branch-covering move, switch, Rest, phaze, or setup action.
- If the active-target converter and the branch/resource move are close, rank
  the move that keeps the next board narrower and the unique route piece alive.
- Marginal-delta gate: before promoting boost, setup, preservation switch, or
  damage, say what changes by the next turn. A final boost, safer owner, or
  extra control point is not conversion unless it creates a new KO/Rest/switch/
  phaze/trade threshold before the opponent's route acts. If active damage
  creates the first forced threshold and the boost/switch only makes an already
  live route prettier, promote damage. If damage does not change the next
  forced choice and lets the opponent reboost, reset, or pivot to parity,
  promote the boost, reset-denial, or branch-covering line.
- Payoff-vs-stability gate: when a high-upside active hit or handoff competes
  with a lower-variance route owner, promote the stable owner unless the
  high-upside line creates a concrete next-turn threshold that the stable owner
  cannot. Stability means absorbing revealed or strong-prior pressure,
  preserving the central route piece, and keeping an acceptable punish into
  the likely branch. Do not promote the higher-payoff owner only because it
  has a stronger matchup if the stable owner covers Pursuit, coverage, phaze,
  or switch pressure with lower wrongness cost.

Tiebreak in this order:

1. Route conversion: removes a blocker, forces Rest, phazes setup, keeps
   Spikes while denying Spin, cashes out into a key piece, or opens the
   endgame.
2. Opponent route denial: stops their most important plausible route from this
   board, not just their scariest legal move in the abstract.
3. Resource identity: spends pieces whose job is done and preserves pieces
   that still hold a unique route job.
4. Wrongness cost: demote lines that lose a central route if wrong; promote
   route-winning lines when the miss cost is only tempo or chip.
5. Next-board clarity: prefer the move that creates a narrower next turn you
   understand.

Required discriminator:

- `#1 over #2 because:` name the route value that makes the top move better.
- `#2 becomes #1 if:` name the public fact, branch weight, or damage threshold
  that would flip the ranking.
- `Rejected safe/default line:` name the tempting safe move and why it merely
  avoids punishment, fails to convert, or spends/preserves the wrong resource.
- `Positive-selection check:` say whether the move converts, denies conversion,
  branch-punishes, or makes the correct spend/save decision.
- `Next-turn delta:` state the concrete threshold or branch that changes next
  turn; if none changes, the move cannot be #1 on route-budget grounds.

Miss tags:

- `route_budget`: the right move was in the candidate set but ranked below a
  lower-conversion move.
- `resource_identity`: the ranking spent or preserved the wrong route piece.
- `reset_loop`: Rest, Spin, Recover, phaze, Sleep Talk, or pass reset erased
  the progress.
- `script_too_slow`: a generically good move lost because their route was
  converting now.
- `branch_punish`: a named branch did not promote the move that beats it.

Do not count "safe" as positive selection unless it preserves a named route or
denies the opponent's named route.
Do not chase a final boost or a cleaner preservation switch after the active
hit already creates the first forced threshold. Do not attack just because last
turn they attacked if the current board makes reboost, reset, or pivot the
higher-incentive branch.
Do not choose the flashier owner over the stable owner unless the flashier
owner changes the next forced choice and the stable owner does not.
