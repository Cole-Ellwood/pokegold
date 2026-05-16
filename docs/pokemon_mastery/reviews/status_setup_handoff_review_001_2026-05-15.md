# Status Setup/Handoff Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/status_setup_handoff_transfer_001_smogtours-gen2ou-934420_2026-05-15.md`

Reason for study:
The fresh transfer was not perfect. It improved top and route-conversion counts
but failed the positive-selection and branch-obedience trend test. The main
misses were Smeargle support-lead order, Snorlax as a status-tolerant special
receiver, Machamp setup into Starmie, and Dragonite's status sacrifice into the
Machamp route.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `policy_cards/cashout_boundary.md`
- `policy_cards/support_handoff_after_job.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/active_pressure_before_status.md`
- `reviews/pass_package_sleeper_handoff_review_001_2026-05-15.md`

Current web sources:

- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums, GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon Forums, GSC Good Cores:
  `https://www.smogon.com/forums/threads/gsc-good-cores.3536015/`
- Smogon Forums, Dragonite OU Revamp:
  `https://www.smogon.com/forums/threads/dragonite-ou-revamp-done.3647144/`
- Pikalytics current GSC Smeargle usage snapshot:
  `https://pikalytics.com/pokedex/gsc/Smeargle`

## Confirmed Source Lessons

Smeargle:
Smogon Spikes material says Smeargle can set Spikes effectively, especially
because Spore discourages immediate spinner entry, but also warns that Smeargle
is too frail for a long Spikes war and often wants Baton Pass. Current Pikalytics
usage also supports the Spore + Baton Pass + Agility + Spikes package. The
transfer miss was treating "Smeargle can sleep" as "Smeargle must sleep now."

Spikes plus status:
The Spikes article frames paralysis and poison as ways to make Spikes convert,
not as independent annoyances. This supports the replay's early Thunder Wave
and the later Starmie Thunder Wave: status can be the route move when it gives
the next receiver a cleaner board.

Snorlax and Steelix:
The GSC threatlist says no single Pokemon counters all Snorlax sets and lists
Steelix, Machamp, Explosion, and other checks as partial answers. It also
describes Steelix's Curse + Roar package and Explosion option. The review lesson
is to stop flattening Steelix into "Roar now"; sometimes the route is Curse,
then Earthquake or Roar.

Machamp:
Smogon sample-team and core sources describe Machamp as a late-game or support
offensive piece whose checks include Starmie, Psychics, and Flying-types. The
turn-21 miss was not that Machamp can attack Snorlax; it was that Starmie was
the obvious receiver and Curse was the move that changed the receiver board.

Dragonite:
Dragonite sources support both Thunder Wave utility and Haze/Reflect defensive
roles. The transfer correction is tier discipline: voluntary entry into boosted
Snorlax makes Haze a strong prior, but Thunder Wave was the revealed route move
that enabled Machamp. Do not let the hidden Haze package hide the revealed
status sacrifice line.

## Policy Corrections

The existing card structure is enough, but three cards needed tighter wording:

- `active_pressure_before_status.md`: add support-lead order so Smeargle-like
  leads are not treated as sleep-only once Spikes or Thunder Wave appears.
- `branch_action_after_naming.md`: add status-tolerant receiver and setup-into-
  receiver language.
- `support_handoff_after_job.md`: add status-sacrifice handoff for low support
  pieces that create a named converter.

## Measurement Note

Mixed but not progress. The fresh packet improved top-match, acceptable-match,
and route-converting count from the previous run, but positive-selection fell
from 42/49 to 38/49 and branch-punish obedience fell by percentage. Do not
claim broad progress until positive selection and branch obedience improve
together while the severe/hidden/state/mechanics gates stay clean.
