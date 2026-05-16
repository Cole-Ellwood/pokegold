# Ground Receiver Triangle Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/ground_receiver_triangle_transfer_001_gen2ou-2591556155_2026-05-15.md`

## Miss Pattern

This was a route-conversion miss, not a severe-blunder miss. I often found a
safe action, but I lost top-match and branch obedience when the board became a
receiver triangle:

- Zapdos/Exeggutor/Snorlax repeatedly forced Raikou, Skarmory, and
  Misdreavus handoffs.
- Marowak entered after Raikou was paralyzed and became a finite toxic-clock
  converter.
- Skarmory, Starmie, and Forretress were not just generic walls. Each changed
  the required move: Fire Blast, Earthquake, Recover, Spikes, or a handoff.
- After Skarmory used Rest, I attacked the sleeping target instead of asking
  whether Starmie would enter before any sleep turn was spent.

## Source Study

Web sources read after scoring:

- Smogon GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Marowak revamp:
  `https://www.smogon.com/forums/threads/marowak-revamp-qc-3-2-gp-2-2.3481449/`
- Smogon GSC Spikes:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon Starmie history, GSC section:
  `https://www.smogon.com/articles/starmie-through-years`
- Smogon GSC Speed Tiers:
  `https://www.smogon.com/gs/articles/gsc_speedtiers`
- Smogon GSC Skarmory forum analysis:
  `https://www.smogon.com/forums/threads/gsc-ou-skarmory.3709334/`
- Smogon GSC Status:
  `https://www.smogon.com/resources/competitive/gs/status`

Local docs read after scoring:

- `policy_cards/branch_action_after_naming.md`
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/active_pressure_before_status.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`

## Source-To-Policy Extraction

Marowak is not a generic Ground. Its threat is concentrated enough that the
opponent's receiver choice matters immediately. Smogon sources frame Skarmory
as one of the best Marowak answers, but Fire Blast and boosted Rock Slide are
the exceptions; Starmie and Vaporeon can force Marowak with Surf, but must
respect Earthquake on entry. That maps directly to the turn 21 to 23 miss:
after Fire Blast was public and Skarmory used Rest, the next question was not
"hit the sleeping wall" but "which receiver enters, and which revealed move
punishes it?"

Forretress is mostly a Spikes piece, but source material also emphasizes that
its Explosion and Rapid Spin are defensive compression, not automatic
wallbreaking. In this replay, Forretress entering Snorlax was a hazard/resist
route, not just another Normal immunity like Misdreavus. Missing that weakened
branch-punish scoring.

Starmie source material emphasizes Surf, Recover, and support/spinning rather
than raw offense. The turn 24 miss was exactly this: Surf spent the move on a
stay-in branch, while Recover converted the likely switch and kept the route
piece healthy.

## Policy Updates Made

- `branch_action_after_naming.md`: added repeated-cycle obedience and Ground
  breaker receiver-triangle extensions.
- `support_handoff_after_job.md`: added Rest-to-counter-pivot extension.
- `hazard_loop_spin_window.md`: added Forretress compression extension.
- `active_context.md`: pointed the next rep at receiver-triangle coverage,
  Rest-to-counter-pivot, and Recover conversion.

## Next Rep

Fresh replay transfer or compact drill that tests:

- repeated Electric/physical-wall/Ghost cycles;
- Ground or Steel route-piece entry against paralyzed Electric;
- Fire Blast versus Skarmory/Forretress after coverage is public;
- Earthquake into Starmie/Water after a Rest reset;
- Recover as the route-converting move when the opponent is forced out.
