# RestTalk/Growth/Item Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/resttalk_growth_item_transfer_001_smogtours-gen2ou-933217_2026-05-15.md`

Reason for study:
The fresh transfer was non-perfect. Severe, hidden-info, state, and mechanics
gates stayed clean, but top-match remained below the proof gate and several
positive-selection misses repeated: item-first Thief, active removal over
over-handoff, Espeon Growth/coverage package recognition, and CurseLax timing
against RestTalk Electric pressure.

## Sources Read

Local mastery docs:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/active_pressure_before_status.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `policy_cards/hazard_loop_spin_window.md`
- `reviews/thief_thunder_lure_handoff_review_001_2026-05-15.md`
- `reviews/steelix_curse_roar_split_review_001_2026-05-15.md`
- `reviews/resttalk_substarmie_phaze_review_001_2026-05-15.md`

Current web sources:

- Smogon Forums GSC Exeggutor OU Revamp:
  `https://www.smogon.com/forums/threads/exeggutor-ou-revamp-gp-0-2.3622650/`
- Smogon GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon Forums GSC OU Espeon:
  `https://www.smogon.com/forums/threads/gsc-ou-espeon-qc-1-1-gp-1-1.3667456/`
- Smogon Forums GSC OU Snorlax:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon Forums GSC Zapdos:
  `https://www.smogon.com/forums/threads/gsc-zapdos.3674240/`
- Smogon Forums GSC OU Threat List:
  `https://www.smogon.com/forums/threads/gsc-ou-threat-list-qc-2-2-gp-2-2.3477110/`
- Bulbapedia Sleep Talk:
  `https://bulbapedia.bulbagarden.net/wiki/Sleep_Talk`
- Bulbapedia Sleep status:
  `https://bulbapedia.bulbagarden.net/wiki/Sleep_(status_condition)`

## Source-To-Policy Extraction

Thief is a route move, not just a gimmick:
The Exeggutor source treats Thief as a real option because Exeggutor baits
Electrics, Skarmory, and Tyranitar and can remove Leftovers so Spikes and chip
matter more. The sample-team source also shows modern GSC structures using
Thief pressure to prepare Zapdos or other cleaners. In this transfer, turn 1
and later item-pressure boards exposed the same miss: I treated sleep/status
as the default script instead of first asking whether item denial converted a
named receiver route.

Espeon is a package after Morning Sun or Growth appears:
The Espeon source frames Growth, Morning Sun, Psychic, and Hidden Power as one
offensive package. Growth is not random greed; it threatens a sweep or a pass
route, while Hidden Power Water or Fire targets the specific Pokemon that wall
Psychic. Therefore, after turn 13 Morning Sun and especially turn 14 Growth,
the correct defender question was not only "Pursuit if it leaves." It was
"can I remove, phaze, status, or hand off before the Growth/coverage package
gets a second turn?"

RestTalk Electrics stay active while asleep:
The Zapdos and threat-list sources describe RestTalk Zapdos and Raikou as
offensive and defensive threats, not passive sleepers. Bulbapedia confirms
Generation II Sleep Talk can call Rest if HP is not full, resetting the sleep
counter, and sleeping Pokemon can still use Sleep Talk. This supports the
existing revealed-RestTalk card: once Sleep Talk is public, a sleeping Electric
can stay and apply Thunder/Hidden Power or force Rest timing decisions.

CurseLax needs a two-turn damage-clock solve:
The Snorlax source says Curse forces phaze risk and Rest helps against Zapdos
and Raikou, but Rest without Sleep Talk gives the opponent free turns. In the
transfer, my ranking was too flat. I knew Double-Edge, Curse, and Rest were
live, but I under-ranked the exact sequence: use Curse when it changes the
post-Rest board, then Rest before the next Thunder removes Snorlax. The rule
is not "always attack after boosting" or "always keep setting up"; it is a
two-turn clock against Thunder, wake turns, Spikes, and available phazers.

Active removal can beat predictive handoff:
The Zapdos source emphasizes that Thunder plus Spikes stresses Snorlax and
Raikou switch-ins, but it also notes Cloyster support and Snorlax checks are
central. Turn 7 was a useful opposite-boundary miss: I leaned toward handoff
from Zapdos into Raikou, while Thunder removed Cloyster through the switch and
converted support pressure immediately.

No-Team-Preview boundary:
The exact Sleep Talk, Hidden Power, and receiver slots were not public before
their reveal. The correct spectator-public form is "if side-known/revealed,
Sleep Talk or coverage is top; otherwise treat it as a strong prior or
possible-only branch and name the public fallback." This kept hidden-info
errors at 0 in the transfer and must stay mandatory.

## Policy Updates Made

- `branch_action_after_naming.md`: added narrow Growth/recovery package and
  CurseLax Rest-clock wording.
- `sleep_absorber_and_set_ambiguity.md`: tightened revealed-RestTalk wording
  for setup boards where the sleeper's Sleep Talk or wake action is pressure.
- `active_context.md`: moved the latest fresh-transfer pointer to
  `resttalk_growth_item_transfer_001` and made the next rep focus on
  item-first utility, Growth packages, and CurseLax/RestTalk timing.
- `measurement_progress_ledger.csv`: recorded the fresh transfer and the
  constructed regression probe separately.

## Measurement Note

Not progress proof. This was a larger packet than the prior early stops and
its severe/hidden/state/mechanics gates were clean, but the proof gate still
failed: top-match was 29/58, below 55%, and the same positive-selection
families recurred. The constructed probe is only a repair check. It does not
count as fresh unseen evidence, mastery, or boss-sim validation.
