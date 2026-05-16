# One-Cycle Converter Check 002 - smogtours-gen2ou-926958 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-926958`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-926958.log`

Selection metadata:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&server=smogtours&page=8`

Mode: spectator-public no-Team-Preview focused transfer, turns 1-12. This was
run after adding the one-cycle packet, but before adding side-known helper
support.

Contamination control:
- Local `rg` found no prior `smogtours-gen2ou-926958` references before
  download.
- The raw log was exposed only through prompt/reveal turns 1-12.
- No replay UI, team paste, or future turn text was inspected before answers.

Post-score sources and docs:
- Smogon Forums, [GSC OU Steelix](https://www.smogon.com/forums/threads/gsc-ou-steelix.3705042/).
- Smogon, [GSC OU Threatlist](https://www.smogon.com/gs/articles/gsc_threats).
- Local cards: `spend_or_save_piece.md`, `reset_loop_denial.md`,
  `role_package_ledger.md`, `name_next_board_owner.md`,
  `branch_punish_ranking.md`.

## Score Summary

Decisions: 24.

Top-match: 11/24.

Acceptable-match: 22/24.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 19/24.

Route-converting move chosen: 17/24.

Branch-punish chosen: 14/23.

Role-package update obeyed: 15/20.

Earliest meaningful error: turn 1 p1, underpricing Curse as the lead Snorlax
route after Zapdos Thunder pressure.

Verdict: still flat/regressing. Severe and hidden-info gates stayed clean, but
top-match remained far below the prior post-Spikes/Spin sample. The repeated
problem is now method-level: spectator-public prompts hide the advised side's
own moves and teammates, then exact-move scoring pushes training toward
oscillating guesses.

## Turn Notes

- Turn 1: p1 Snorlax used Curse into Zapdos Thunder. I expected sleep or
  active damage; p2 Thunder was correct.
- Turn 2: p1 used a second Curse as p2 switched Steelix. I chose attack; p2
  Steelix was correct. Missed setup as the branch action into the owner.
- Turn 3: p1 attacked with Body Slam into Steelix and p2 Roared. I got p2
  Roar; p1 was acceptable but not exact.
- Turn 4: both sides double-switched, p1 Tyranitar to Zapdos and p2 Steelix to
  Snorlax. I overranked direct Steelix/Tyranitar moves.
- Turn 5: p1 Thunder hit and paralyzed Snorlax; p2 Double-Edge punished. I got
  p1, missed p2's immediate attack over Curse.
- Turn 6: p1 switched Cloyster as p2 Rested. I got Rest but not the support
  handoff.
- Turn 7: p1 Spikes into p2 Starmie switch. Correct p1 support job; exact p2
  spinner was side-known.
- Turn 8: p2 Rapid Spin cleared Spikes before p1 Toxic. I overcalled Explosion
  again; Toxic preserved Cloyster and put the spinner on a timer.
- Turn 9: p1 switched Zapdos into Starmie; p2 Toxic caught it. Correct owner
  handoff for p1, missed p2's status branch.
- Turn 10: both switched, p1 Zapdos to Cloyster and p2 Starmie to sleeping
  Snorlax. I stayed too active with Thunder.
- Turn 11: p1 Spikes as p2 returned to poisoned Starmie. Correct on both.
- Turn 12: p2 Rapid Spin cleared Spikes as p1 went Snorlax. I overcalled
  Explosion into Starmie again.

## Method Diagnosis

The compact docs are not the main failure. The live path is small enough to
read, and the relevant cards now exist. The recurring distortion is that
spectator-public mode asks for exact move advice without the advised player's
own team and moves. Real move choice is side-known: p1 knew it had Steelix,
Starmie, Cloyster's exact move set, Snorlax's lack of Earthquake, and Zapdos's
limited coverage. The public prompt did not.

This produces two bad training incentives:
- I overuse species priors for unrevealed own moves, then count the miss as a
  hidden-info or top-match failure.
- After one replay punishes underusing Explosion, the next replay overpromotes
  Explosion even where the player had a better own-team handoff.

## Structure Patch

Added `side-prompt` mode to `tools/pokemon_mastery/replay_turn_pause.py`.
Future exact-move training should use one advised side per replay:

```text
python tools/pokemon_mastery/replay_turn_pause.py path/to/replay.log side-prompt --turn N --side p1
```

The helper includes only that side's reconstructed own roster and shown moves
from the replay, while keeping the opponent spectator-public. It is still
imperfect because unused own moves are missing, but it better matches real play
than pure spectator-public exact-top scoring.

Do not advise both sides from side-known prompts in one packet unless isolated;
seeing p1's side-known roster contaminates p2 advice. Use one side per replay
or separate isolated runs.

## Next Rep

Run a one-side side-known packet, 12-18 decisions, with the one-cycle card set.
Score exact top there. Keep spectator-public packets for route-class
calibration, not as the main exact-move progress proxy.
