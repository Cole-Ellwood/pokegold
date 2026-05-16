# Compressed Core Transfer Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/compressed_core_transfer_001_smogtours-gen2ou-932782_2026-05-15.md`

Reason for study:
The first compressed-core fresh replay packet was imperfect but better than the
recent fresh-transfer baseline: 17/30 top, 27/30 acceptable, 0 severe, 0
hidden-info, 0 state, 0 mechanics, 24/30 positive, 21/30 route, 17/24 branch.
The main misses were item-first `Thief`, preserving Snorlax from Cloyster's
Toxic/Explosion branch, Steelix `Roar` versus `Earthquake` timing, and sleeping
Zapdos re-entry as a status absorber.

## Sources Read

Local compressed docs:

- `active_context.md`
- `live_core.md`
- `heuristic_core/migration_map.md`
- `heuristic_core/converter_before_script.md`
- `heuristic_core/reset_loop_denial.md`
- `heuristic_core/spend_or_save_piece.md`
- `measurement_minigoal_2026-05.md`

Current web sources:

- Smogon Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon Forums GSC Zapdos:
  `https://www.smogon.com/forums/threads/gsc-zapdos.3674240/`
- Smogon Forums Steelix question:
  `https://www.smogon.com/forums/threads/steelix-question.3550539/`

## Source-To-Heuristic Extraction

Exeggutor sleep can be bait for item or Explosion:
Smogon's sample-team material describes Sleep Powder as a way to draw opposing
Sleep Talkers such as Snorlax and Raikou, which can then become Explosion
targets. This supports the compressed `converter_before_script` rule: sleep is
not the only lead script when item removal or a later cash-out is the route.
Turn 1 still failed this boundary by ranking `Sleep Powder` over `Thief`.

RestTalk Zapdos is an active status sponge:
The GSC threatlist and Zapdos source both frame Zapdos as a RestTalk user that
keeps attacking with Thunder and Hidden Power, not as a passive sleeper. This
explains turns 3-5 and 9-10: `Sleep Talk`, Snorlax handoff, and sleeping-Zapdos
status absorption are all active route choices.

Steelix with Spikes is a shuffle loop:
Smogon's Spikes article explicitly frames Steelix as a Spikes phazer that can
Roar counters after forcing switches. The packet showed improvement over older
Steelix misses because `Roar` stayed in the top three, but it was still
under-ranked on turns 12-13 and overcorrected on turn 14. The compressed rule
should be: when Steelix has revealed `Roar` and own-side Spikes are down, ask
whether the current target is staying to take `Earthquake` or leaving into the
Roar loop.

Spend/save improved, but not perfectly:
Turn 7 exposed the same support-piece boundary in reverse. Preserving boosted
Snorlax from Cloyster's Toxic/Explosion branch by switching to Cloyster was the
route. The compressed core made the line understandable after reveal, but the
pre-freeze answer still preferred active pressure.

## Measurement Note

Limited evidence that doc compression helped. The packet's 17/30 top-match is
above the recent fresh-transfer average and clears the basic gate, while
acceptable, positive, route, branch, severe, hidden-info, state, and mechanics
all stayed healthy. It is not broad progress proof because this is one packet,
it loaded two tiny cards instead of the intended one, and the old item-first
miss appeared immediately.

Next test: run another fresh packet with a stricter pre-freeze context:
`live_core.md`, the prompt, and exactly one tiny card selected before turn 1.
Prefer `converter_before_script.md` if an item/status lead appears, otherwise
`reset_loop_denial.md` when Spikes/RestTalk/phaze appears.
