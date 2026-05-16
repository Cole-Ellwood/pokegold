# Heuristic: Re-score After Reveal

Status: live tiny card.

Use when: a move reveal changes role, package, timing, or receiver map.

Rule: after a reveal, stop following the old species script and re-score.

Reveals that often matter:
- Growth, Morning Sun, Baton Pass, Agility, Substitute.
- Reflect, Light Screen, Charm, Pursuit, Curse, Rest, Sleep Talk, Roar,
  Whirlwind.
- Sleep Talk calling Rest, because it resets the sleep clock in GSC.
- Mean Look, Perish Song, Pain Split, Thief, Thunder, Hidden Power, lure
  coverage, Lovely Kiss, Self-Destruct, Spin, Explosion.

Ask what two-turn clock or receiver map the reveal creates, then rank the move
that removes, phazes, statuses, pressures, or hands off into that package.
For Growth/Baton Pass, compare boost-now, attack-now, and pass-now by whether
the receiver survives the incoming hit and converts the next board.
If the incoming hit is a Sleep Talk roll, score revealed rolls first and
strong-prior STAB/coverage second; do not assume the roll is harmless just
because the target is asleep.
For trap/perish, re-score every turn around hold -> survive -> count. If Baton
Pass is public, trapping the receiver can beat singing at the passer.
If Perish Song was used before the hold, re-score the receiver immediately:
Mean Look, Destiny Bond, or exit can outrank damage while the user's own count
is ticking.

Do not demote revealed coverage or RestTalk pressure because it was not the
default role before the reveal.
Do not treat Lovely Kiss as only a sleep move after damage has made the user
low; re-score the Self-Destruct/Explosion cash-out before choosing Sleep Talk
or recoil damage.

Archive: `policy_cards/branch_action_after_naming.md`;
`policy_cards/sleep_absorber_and_set_ambiguity.md`.
