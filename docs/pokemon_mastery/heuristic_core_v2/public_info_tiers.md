# Heuristic: Public Info Tiers

Status: live tiny card.

Use when: hidden coverage, item state, teammate identity, lure role, or
side-known information affects the recommendation.

Rule: label every decision-relevant nonpublic claim.

Tiers:
- `revealed`: public fact; can anchor the top move.
- `strong prior`: price the branch and name fallback if wrong.
- `possible only`: mention or cover, not main-line proof.

Spectator-public answers may score by class when exact team context is hidden.

Do not use no-Team-Preview leaks, future turns, hidden items, hidden moves, or
private team slots as facts.

Archive: `policy_cards/hidden_role_voluntary_entry.md`;
`measurement_minigoal_2026-05.md`.
