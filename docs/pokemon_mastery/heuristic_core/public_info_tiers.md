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
Strong-prior coverage that immediately removes the proposed setup or defensive
route piece must be priced before that setup or preservation line becomes top.
Strong-prior STAB/status can promote a typed or status-tolerant absorber over a
generic wall, but the fallback must say what happens if coverage appears.
For Zapdos, Raikou, and Jolteon, Hidden Power coverage is a strong prior, not
possible-only. Do not make a Ground or role-targeted absorber top if revealed
status or damage from the current piece converts while coverage could punish
the absorber.
For lead Jynx, Thief after sleep is a strong-prior package branch. For RestTalk
Snorlax, Normal STAB and Earthquake are strong-prior attacking rolls once Sleep
Talk is public unless revealed moves disprove them.
The inverse is also live: when our Electric enters, Ground/Steel counter-owner
is a strong-prior class even if the exact slot is hidden. Coverage into that
class can be top when it also keeps the active target route acceptable.

Do not use no-Team-Preview leaks, future turns, hidden items, hidden moves, or
private team slots as facts.

Archive: `policy_cards/hidden_role_voluntary_entry.md`;
`measurement_minigoal_2026-05.md`.
