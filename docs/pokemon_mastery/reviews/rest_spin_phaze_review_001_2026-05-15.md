# Rest/Spin/Phaze Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/rest_spin_phaze_transfer_001_smogtours-gen2ou-931755_2026-05-15.md`

Reason for study:
The fresh transfer was imperfect. It had no severe or hidden-info errors, but
it introduced a Rest wake-count mechanics/state error and repeated misses
against Golem's Rapid Spin + Roar package.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/hidden_role_voluntary_entry.md`
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `reviews/spinblock_subgrowth_review_001_2026-05-15.md`

Current web sources:

- Smogon Forums, Golem OU revamp:
  `https://www.smogon.com/forums/threads/golem-ou-revamp-qc-2-2-gp-2-2.3647044/`
- Smogon Forums, GSC OU Heracross:
  `https://www.smogon.com/forums/threads/gsc-ou-heracross.3699588/`
- Smogon Forums, Exeggutor revamp:
  `https://www.smogon.com/forums/threads/exeggutor-revamp-gp-2-2.3646119/`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon, Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`
- Bulbapedia, Rest:
  `https://bulbapedia.bulbagarden.net/wiki/Rest_(move)`
- PokemonDB, Rest:
  `https://pokemondb.net/move/rest`

## Confirmed Source Lessons

Rest wake timing:
Current mechanics references agree that from Generation II onward, Rest makes
the user spend two turns asleep and then wake able to act on the next turn.
Smogon's GSC status source also stresses that Pokemon can act on the turn they
wake. The correction is operational: count the Rest turn and two sleeping
action turns manually; do not rely only on a prompt's status label.

Golem is a spinner and phazer:
The Golem revamp explicitly describes the set as Earthquake, Rapid Spin,
Explosion, and Roar or Fire Blast with Leftovers. It also says Golem's selling
point over other Normal resists is combining Rapid Spin, Roar, and Explosion
pressure. The transfer miss was treating Golem like a generic boom or Ground
instead of a route piece that can remove Spikes and then phaze.

Heracross receiver map:
Smogon Heracross material confirms Megahorn, RestTalk, and Curse/Seismic Toss
as the usual pressure package, with Skarmory, Steelix, and Zapdos as important
answers. The transfer correction is not "always attack with Heracross"; a low
Heracross can also leave to reset the board if the opponent is expected to
cover Megahorn.

Exeggutor branch split:
Smogon's Exeggutor analysis supports the branch split that mattered here:
Sleep Powder or Stun Spore, Psychic, coverage, and Explosion are all real route
moves. When Exeggutor is low and paralyzed, the answer still has to choose
which branch is live: sleep, Psychic, Explosion, or preservation switch.

## Policy Corrections

- `sleep_absorber_and_set_ambiguity.md`: add a Rest wake-count extension so
  Rest wake turns are manually tracked and Sleep Talk is not recommended on the
  wake-and-act turn.
- `hazard_loop_spin_window.md`: add Golem/Rock spinner package wording so
  Rapid Spin + Roar + Explosion is priced before generic Rock/Ground damage.

## Measurement Note

Not progress. Top-match improved from 14/49 to 22/49 and hidden-info returned
to 0, but acceptable-match fell to 30/49, positive-selection and route
conversion stayed below target, branch obedience remained weak, and a mechanics
error appeared. Severe-blunder avoidance stayed clean, but that is only a
gate.
