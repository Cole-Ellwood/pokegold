# Wake-Action Prompt Clarity Review 001 - 2026-05-15

Trigger:
`docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_041_gen2ou-2577573223_p1_2026-05-15.md`

## Diagnosis

Packet 041 was not a clean continuation of the repair sample. It scored 16/30
top and 23/30 acceptable, and it reintroduced a Rest wake-action
state/mechanics error on turn 32.

The lesson was not missing. `rest_curse_tempo_window.md`,
`training_method_review_002_2026-05-15.md`, and
`rest_spin_phaze_review_001_2026-05-15.md` already say that GSC Rest wake turns
must be treated as action turns. The prompt wording was still too easy to
misread: `wake/act next in GSC` looked like the following turn, not the turn
currently being prompted.

## Source Check

Current GSC sources support the same existing rule:

- Smogon status guide: GSC Pokemon can act on the turn they wake, and Sleep
  Talk can call Rest successfully in GSC.
  `https://www.smogon.com/gs/articles/status`
- Smogon Snorlax update: Curse, Double-Edge, and Rest define the CurseLax
  clock; the two-turn Rest/Curse window is central, not a side detail.
  `https://www.smogon.com/forums/threads/snorlax-update-qc-2-2-gp-2-2-finished.3467216/`
- Bulbapedia Destiny Bond: Destiny Bond lasts until the user moves again, so a
  wake-turn setup move can beat the active trade threat without attacking.
  `https://bulbapedia.bulbagarden.net/wiki/Destiny_Bond`

Related packet sources:

- Smogon GSC threatlist and sample-team material support Jolteon/Agility/Baton
  Pass to Marowak as a real route, which packet 041 handled well on turns
  23-26:
  `https://www.smogon.com/gs/articles/gsc_threats`
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon Houndoom and Gengar material support the Gengar -> Houndoom/Pursuit
  branch, which packet 041 handled correctly only after the wake-turn miss:
  `https://www.smogon.com/forums/threads/houndoom-ou-revamp-qc-2-2-gp-2-2.3653682/`
  `https://www.smogon.com/articles/gengar-through-ages`

## Repair

Keep the docs compact. Do not add another general sleep essay.

Implemented:

- `tools/pokemon_mastery/replay_turn_pause.py`: changed the prompt marker to
  `will wake and can act this prompted turn in GSC`.
- `tools/pokemon_mastery/tests/test_replay_turn_pause.py`: updated the
  regression expectation.
- `heuristic_core/rest_curse_tempo_window.md`: replaced the old wake wording
  with the same prompted-turn language.

## Next Gate

Run the helper test suite, then continue with a fresh side-known packet. If a
`Rest sleep actions 2` turn is missed again, stop replay volume immediately and
turn this into a mechanics fixture before any more replay scoring.
