# Heuristic: Name Next Board Owner

Status: live tiny card.

Use when: a switch, absorber, sack, Rest handoff, or counter-pivot is likely.

Rule: if the active target may leave, solve the board it leaves behind.

Ask:
- Who enters by class: Snorlax, support, Electric, Ghost, Ground, phazer?
- Which of our pieces owns that board?
- If our owner handoff is obvious, who owns the board after their counter-handoff?
- After our owner enters, what counter-owner does it invite, and what beats it?
- Is the best owner generic bulk, or a typed/status absorber that preserves the
  generic wall for later?
- After a lead support job succeeds, who is the first receiver or counter-handoff?
- Can the current move hit, status, phaze, set up, or hand off into that owner?
- After our Electric enters, is their counter-owner Ground, Steel, Snorlax, or
  Electric, and does coverage beat that owner now?
- For Baton Pass, who is the receiver, what hit lands during the pass, and who
  owns the board after the receiver appears?
- If several handoffs answer the visible threat, which one preserves the
  irreplaceable breaker/wall, uses the lowest future-job absorber, and creates
  the next route action?

Top move must either bring in our owner, punish their owner, or explain why
current active pressure still converts through the branch.
When multiple owners are safe, rank by route budget. Prefer the handoff that
preserves the irreplaceable win pressure or broad wall while still creating the
next action; do not spend the best owner merely to reset the matchup.

After a support job or owner handoff succeeds, re-run the transaction one ply
deeper. If our new owner invites a revealed or strong-prior counter-owner, rank
the move or switch that beats that counter-owner above generic status/setup;
label exact hidden teammates as class reads with fallback.

Opening double-switches count as handoffs. Price the hard-answer chain by class
before default lead scripts such as sleep, Spikes, or direct STAB.

Before making the handoff automatic, ask whether the current active has a
revealed or strong-prior one-cycle converter: setup, coverage, phaze, or
cash-out that beats the next owner now.

Do not click a move that only beats the Pokemon currently on screen after
naming the receiver.
Do not pass a boost to a receiver that loses to the incoming hit unless the
pass itself changes turn order, immunity, or the next KO.

Archive: `policy_cards/support_handoff_after_job.md`;
`policy_cards/branch_action_after_naming.md`.
