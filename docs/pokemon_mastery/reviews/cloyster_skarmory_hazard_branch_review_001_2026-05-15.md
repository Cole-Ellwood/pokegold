# Cloyster/Skarmory Hazard Branch Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/cloyster_skarmory_hazard_branch_transfer_001_smogtours-gen2ou-933324_2026-05-15.md`

Reason for study:
The fresh transfer was not perfect and stopped early. The repeated miss was
not severe-blunder avoidance; it was positive move selection in a hazard
cycle. I kept choosing the field job or active-target move before ranking the
action that beat the named next-board owner.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/support_handoff_after_job.md`
- `reviews/hazard_ownership_review_001_gen2ou-2544443857_2026-05-14.md`
- `reviews/tempo_coverage_sack_review_001_2026-05-15.md`
- `reviews/spinner_side_recover_review_001_2026-05-15.md`

Current web sources:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, GSC OU Cloyster:
  `https://www.smogon.com/forums/threads/gsc-ou-cloyster.3708121/`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon, GSC OU Speed Tiers:
  `https://www.smogon.com/gs/articles/gsc_speedtiers`
- Smogon, Gold/Silver OU Metagame Primer:
  `https://www.smogon.com/resources/competitive/gs/gs_ou_primer`

## Confirmed Source Lessons

Spikes are important, but they are not a standalone win condition:
Smogon's Spikes guide says GSC has only one Spikes layer and warns against
being too passive or focusing too much on Spikes. This directly explains the
turn 7 miss: Rapid Spin was a real route move, but not automatically the best
move when Surf could punish the incoming opposing Cloyster.

Cloyster is not just a layer button:
Smogon describes Cloyster as a Spiker that also creates offensive pressure
through Surf and Explosion. The GSC OU Cloyster writeup specifically gives
Surf a deterrent job against Rapid Spin users and Explosion switch-ins, and
Toxic a role against Starmie, opposing Cloyster, and Curse Snorlax. In this
replay, Surf into the opposing Cloyster was the same family of lesson:
coverage can be the hazard-loop conversion.

Skarmory and flyers alter hazard math:
The local hazard ownership review already warned that flyers and special
pressure owners can be the next-board owner in Cloyster mirrors. The Smogon
Spikes guide also notes that Zapdos and Skarmory reduce the value of simple
Spikes-plus-phaze loops because they avoid Spikes damage. This keeps the
decision from collapsing into "Spin because hazards exist."

No-Team-Preview discipline still held:
Exact teammates such as Zapdos, Raikou, Steelix, Skarmory, and Cloyster were
hidden before reveal. The correct move-choice form is "name the owner class
and fallback," not "assume the hidden species exists." The score therefore
counts exact hidden switches by class and does not convert possible-only
teammates into facts.

## Policy Correction

The existing cards are mostly right. The missing compact rule is a Cloyster
mirror branch extension for `hazard_loop_spin_window.md`:

1. Before Cloyster uses Rapid Spin into Skarmory, Cloyster, or another passive
   hazard-cycle piece, name the opponent's next owner.
2. If the owner is opposing Cloyster, Surf, Toxic, Icy Wind, or Explosion may
   convert more than Spin because they damage the setter/spinner that keeps the
   loop alive.
3. If the owner is a flyer or Electric, a counter-handoff or status/coverage
   may beat both Spin and Spikes.
4. Spin stays top when own-side Spikes are the route blocker and the opponent
   cannot immediately reset or pressure the spinner for a real cost.

## Measurement Note

Not progress. This packet had clean severe, hidden-info, state, and mechanics
counts, but it was only 14 decisions and repeated a known branch-conversion
failure. The next rep should either drill Cloyster/Skarmory hazard branches or
run a fresh replay with this exact four-question hazard checklist active.
