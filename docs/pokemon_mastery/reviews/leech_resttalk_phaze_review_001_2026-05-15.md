# Leech/RestTalk/Phaze Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/leech_resttalk_phaze_transfer_001_smogtours-gen2ou-933839_2026-05-15.md`

Reason for study:
The fresh transfer was not perfect, and it was not progress. Severe, hidden,
state, and mechanics errors stayed at zero, but top-match, acceptable-match,
positive-selection, route-conversion, and branch-punish rates all fell. The
lesson needs to be learned as positive move selection: seed/item pressure,
RestTalk receiver re-entry, and phaze-loop commitment.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/active_pressure_before_status.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/cashout_boundary.md`
- `reviews/status_setup_handoff_review_001_2026-05-15.md`

Current web sources:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon, Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`
- Smogon Forums, Zapdos GSC OU analysis:
  `https://www.smogon.com/forums/threads/zapdos-qc-2-2-gp-2-2.3673848/`
- Smogon Forums, Exeggutor GSC OU revamp:
  `https://www.smogon.com/forums/threads/exeggutor-revamp-gp-2-2.3646119/`
- Smogon Forums, GSC OU lead analysis:
  `https://www.smogon.com/forums/threads/an-analysis-of-leads-in-gsc-ou.3656620/`
- Smogon Forums, GSC OU sample teams breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Pikalytics current GSC Exeggutor, Zapdos, Cloyster, and Vaporeon snapshots:
  `https://www.pikalytics.com/pokedex/gsc/Exeggutor`
  `https://www.pikalytics.com/pokedex/gsc/Zapdos`
  `https://www.pikalytics.com/pokedex/gsc/Cloyster`
  `https://www.pikalytics.com/pokedex/gsc/Vaporeon`
- PokemonDB Leech Seed mechanics page:
  `https://pokemondb.net/move/leech-seed`

## Confirmed Source Lessons

Exeggutor is not sleep-only:
Smogon threat and analysis material frames Exeggutor as a multi-tool pressure
piece: Sleep Powder, Stun Spore, Psychic/Giga Drain pressure, Leech Seed,
Explosion, and occasional Thief all change different receiver maps. Pikalytics
currently supports this as a live GSC pool: Psychic and Explosion are near-core,
while Sleep Powder, Stun Spore, Thief, and Leech Seed are all real but not
guaranteed. In no-Team-Preview advice, this means Leech/Thief should be priced
when public clues support them, not assumed as facts from species alone.

The replay created exactly that public clue:
Turn 1 showed Exeggutor healing only from Leech Seed, not its own Leftovers,
while Snorlax had Leftovers. That makes Thief much more than a random
possible-only move on turn 2. The correct move selection should have ranked
item removal beside sleep, Explosion, and Psychic because stealing Leftovers
changes Snorlax's recovery, seed clock, and later phaze damage.

Leech Seed is a board-state route:
PokemonDB's mechanics page and the replay log agree that the seeded target is
freed by switching out, while the seeder's replacement can receive the healing.
Smogon's Exeggutor review adds the GSC timing point that Leech Seed damage is
not just generic end-of-turn noise. The decision lesson is practical: after
Leech Seed lands, the next answer must choose among switch-reset, Rest-reset,
active pressure, and cash-out. "Stay and do a safe move" is often the line that
hands the opponent's replacement the route.

RestTalk receivers remain live while asleep:
Smogon's GSC status guide explicitly warns that Sleep Talk is a major sleep
counter and that in GSC, Sleep Talk can successfully call Rest. It lists
Zapdos, Raikou, and Snorlax among common RestTalk users. That explains the
transfer's Raikou sequence: Rest at 50%, switch out asleep, re-enter as the
Zapdos receiver, then Sleep Talk into Hidden Power or Rest. A sleeping
RestTalk Electric is not dead weight; after Rest and Sleep Talk are public, it
is a revealed route piece.

Phaze plus Spikes must be treated as conversion:
Smogon's Spikes article says phazers can force repeated Spikes damage and make
opponents Rest or lose timing. The Raikou threat entry describes Raikou as a
special Roar tank and one of the strongest Spikes abusers. Zapdos Whirlwind is
less universal, but current Pikalytics still shows it as a meaningful GSC move,
and the replay made it revealed fact on turn 12. Once revealed, the correct
discipline is to keep Whirlwind/Roar ranked until the opponent shows a public
branch that breaks the loop.

Cloyster pressure is not just Spikes:
Smogon Spikes and Explosion sources both describe Cloyster as a Spiker with
real offensive pressure through Surf, Toxic, and Explosion. Pikalytics confirms
the same current move bundle. The transfer miss was not "always boom"; it was
failing to choose whether Cloyster's current job was seed reset, Spikes,
special pressure, or cash-out into a named post-trade owner.

## Policy Corrections

The existing card structure remains useful, but five cards needed tighter
positive-selection wording:

- `active_pressure_before_status.md`: add seed/item pressure package language
  so Leech Seed and Thief are ranked before sleep script when public clues
  support them.
- `branch_action_after_naming.md`: add RestTalk receiver re-entry language so a
  sleeping Electric or bulky RestTalk user can be the named receiver.
- `sleep_absorber_and_set_ambiguity.md`: clarify that RestTalk Sleep Talk into
  Rest makes the sleeper a live route piece, not a spent status target.
- `hazard_loop_spin_window.md`: add revealed phaze-loop commitment when
  Whirlwind/Roar plus Spikes is already converting.
- `support_handoff_after_job.md`: add seed/reset handoff language after support
  pressure lands.

## Measurement Note

Not progress. Compared with `status_setup_handoff_transfer_001`, this run fell
from 23/49 top to 19/47, 40/49 acceptable to 32/47, 38/49 positive to 30/47,
34/49 route to 30/47, and 21/43 branch to 13/37. Severe-blunder avoidance
remained clean, but that is only a pass/fail gate. The next claim must be a
fresh unseen decision score where severe/hidden/state/mechanics stay low while
positive-selection, route conversion, and branch obedience improve together.
