# Snorlax/Forretress Counter-Handoff Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/snorlax_forretress_counter_handoff_transfer_001_smogtours-gen2ou-933120_2026-05-15.md`

Reason for study:
The fresh transfer was not perfect and stopped early. The repeated miss was
counter-handoff timing in a common lead-cycle shell: Snorlax, Forretress,
Zapdos, Cloyster, and Snorlax again. I did not lose a central piece, but I also
did not choose the move that converted the named next board.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/active_pressure_before_status.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/cashout_boundary.md`
- `reviews/counter_handoff_review_001_smogtours-gen2ou-907837_2026-05-14.md`
- `workspace/quick_tests/branch_handoff_obedience_probe_001_2026-05-14.md`

Current web sources:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, Forretress OU Revamp:
  `https://www.smogon.com/forums/threads/forretress-ou-revamp-done.3647111/`
- Smogon, GSC OU Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`

## Confirmed Source Lessons

Forretress compression:
Smogon material treats Forretress as a Spikes and Rapid Spin piece with Toxic,
coverage, and Explosion pressure. The local cards already encode that
Forretress should not be collapsed into "Spikes only." In this replay,
Forretress used Toxic, then Spikes, then Hidden Power, and later stayed useful
as the handoff into RestLax.

Snorlax pressure plus Rest:
Snorlax is a route piece, not just a passive status target. Once Double-Edge
was public, the next hit into Forretress changed the support piece's HP and
future trade map. Rest then converted the poisoned Snorlax from a timed piece
back into a sleep-cycle route piece. The correction is to price one more
pressure turn before fleeing from Toxic if Rest is live.

Counter-handoff obedience:
The existing counter-handoff review had the exact shape: when the active is
likely to leave, the expert line often moves the owner of the next board into
place. The current replay repeated that pattern with p1 Snorlax into p2
Snorlax, p2 Forretress into RestLax, and p1 Cloyster into p2 Snorlax.

No-Team-Preview discipline:
The exact hidden owners were not facts before reveal. The scoring should reward
owner-class answers, but future advice must still say "Snorlax owner," "Normal
resist," "Electric pressure owner," or "Cloyster/hazard owner" with a fallback
instead of assuming a hidden teammate exists.

## Policy Correction

Two compact policy corrections are enough:

1. Add a Rest-capable pressure note to `active_pressure_before_status.md`: Toxic
   does not automatically force a bulky attacker out if its direct hit changes
   the support piece's future job and Rest can later reset the clock.
2. Add an early-cycle handoff note to `branch_action_after_naming.md`: after
   Spikes, Toxic, Rest, or an obvious forced switch, name the next-board owner
   and obey that owner unless active pressure still hits the branch.

## Measurement Note

Not progress. This packet continued the same "clean severe gate, weak positive
conversion" pattern: 0 severe/state/hidden/mechanics errors, but low top-match,
low branch obedience, and only a 14-decision early-stop sample.
