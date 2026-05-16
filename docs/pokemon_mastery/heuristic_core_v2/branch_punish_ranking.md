# Heuristic: Branch Punish Ranking

Status: live tiny card.

Use when: the answer names a receiver, absorber, immunity, setup branch, or
counter-pivot, but the top move may still only beat the active target.

Rule: a named branch must change the ranking.

Ask:
- What action beats the branch: coverage, status, phaze, setup, switch, cash-out?
- Does active pressure already hit the branch hard enough?
- Is the branch revealed, strong-prior, or possible-only?

Promote the branch-punish when it wins the next board. Keep active pressure
when it beats both active and branch.

Do not name a branch and then leave its punish below a generic safe move.

Archive: `policy_cards/branch_action_after_naming.md`;
`policy_cards/hidden_role_voluntary_entry.md`.
