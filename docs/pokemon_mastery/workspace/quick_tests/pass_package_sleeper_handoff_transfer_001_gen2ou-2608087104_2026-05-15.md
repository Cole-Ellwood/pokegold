# Pass Package/Sleeper Handoff Transfer 001 - gen2ou-2608087104 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/gen2ou-2608087104`

Raw log:
`https://replay.pokemonshowdown.com/gen2ou-2608087104.log`

Replay search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&page=1`

Mode: spectator public, vanilla GSC. Replay actual move is a comparison oracle,
not an absolute answer key. No Team Preview: hidden teammates, moves, items,
and roles stayed in revealed / strong-prior / possible-only tiers.

Source-quality caveat: public ladder/search replay, not confirmed tournament.
Selected because it was unused locally, from a different player pair than the
previous replay, and long enough for a 30-50 decision sample.

## Sources Checked

Local docs before/during sealed work:

- `active_context.md`
- `replay_turn_pause_protocol.md`
- `measurement_minigoal_2026-05.md`
- `policy_cards/branch_action_after_naming.md`
- `policy_cards/cashout_boundary.md`
- `policy_cards/hazard_loop_spin_window.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `policy_cards/support_handoff_after_job.md`

Web/current sources used after scoring, before any further replay:

- Smogon GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Jynx GSC OU:
  `https://www.smogon.com/forums/threads/jynx-gsc-ou-qc-2-2-gp-2-2.3667481/`
- Smogon Snorlax GSC OU:
  `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- Smogon Zapdos GSC OU:
  `https://www.smogon.com/forums/threads/zapdos-qc-2-2-gp-2-2.3673848/`
- Smogon GSC Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- Smogon Introduction to Status in GSC:
  `https://www.smogon.com/resources/competitive/gs/status`
- Remembering Our Roots Redux, Vaporeon section:
  `https://www.smogon.com/smog/issue35/remembering-our-roots`

## Contamination Control

- Local `rg` found no prior `2608087104` artifact before selection.
- Candidate screening used only current search-feed metadata, local prior-use
  checks, and turn count.
- The raw log was downloaded to `tmp/pokemon_mastery_replays/`.
- No future turns were inspected before freezing each turn's top-three
  candidates.
- Web and broad local study happened only after the scored decisions were
  complete.
- Turns 26-29 were frozen and revealed, but not counted. I capped the score at
  the first 49 scorable side decisions to stay inside the 30-50 target and avoid
  overweighting one public ladder replay.

## Score Summary

Scored turns: 1-25.

Scorable decisions: 49.

Unscored: turn 15 p2 because Blissey was put to sleep before its selected move
was logged. Turns 26-29 were extra sealed continuation only and are not in the
score.

Top-match: 17 / 49.

Acceptable-match: 38 / 49.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0. Own-side unrevealed moves in spectator-public mode were
handled as "if available" branches with fallbacks, not as facts.

Mechanics errors: 0.

Positive-selection: 42 / 49.

Route-converting move chosen: 26 / 49.

Branch-punish chosen: 20 / 31 applicable branch decisions.

Earliest meaningful error: turn 2 p1, where I kept Rhydon on immediate
Earthquake pressure and missed Cloyster as the support/status-handoff owner.

Interpretation:
Not progress. Severe, hidden-info, state, and mechanics gates held, but top
match and route-conversion both fell below the prior fresh transfer. The higher
acceptable and positive counts do not prove improvement because too many moves
were safe, generic, or only conditionally useful instead of actually converting
the named route.

## Turn Table

| Turn | p1 frozen top | p1 actual / grade | p2 frozen top | p2 actual / grade |
| --- | --- | --- | --- | --- |
| 1 | Snorlax physical pressure; LK; Curse | Rhydon; acceptable by physical-pressure owner class | Toxic/status; physical owner; support | Toxic; top |
| 2 | Earthquake; Curse; coverage | Cloyster; miss, missed support owner | physical owner switch; Toxic; support | Toxic; acceptable |
| 3 | Spikes; Surf; Toxic | Spikes; top | switch pressure/spinner class; support; stay attack | Cloyster; top by owner class |
| 4 | Toxic; Surf; handoff | Toxic; top | Spikes; Toxic; Explosion branch | Spikes; top |
| 5 | Surf; Explosion read; special/Electric handoff | Zapdos; acceptable only as late handoff | Surf; Explosion; pressure handoff | Gengar; miss |
| 6 | Thunder; Snorlax handoff; switch | Thunder; top | Blissey handoff; Hypnosis/Explosion; Ice Punch | Hypnosis; acceptable active route |
| 7 | poisoned Cloyster absorber; Snorlax; Thunder | Thunder; acceptable pressure but not top | Thunder into absorber; Explosion; Hypnosis | Hypnosis; acceptable but missed branch |
| 8 | Thunder finish; absorber switch; preserve | Thunder into Destiny Bond; top, no severe | Explosion cash-out; Hypnosis; Blissey | Destiny Bond; acceptable cash-out class |
| 9 | Snorlax; Rhydon; stay | Snorlax; top | Thunderbolt; HP Ice read; status | Thunderbolt; top |
| 10 | Body Slam/Double-Edge; Lovely Kiss; Curse | Rest; miss, Rest reset underpriced | Cloyster owner; continue Zapdos; support | Tyranitar; acceptable owner class |
| 11 | Vaporeon; Sleep Talk; Cloyster | Cloyster; acceptable water/physical owner | Roar/Curse; Rock Slide; switch | Rock Slide; acceptable |
| 12 | Surf if available; Explosion; switch | Toxic; miss | statused Cloyster/Blissey switch; Rock Slide | Rock Slide; acceptable removal |
| 13 | Growth if available; Surf; Baton Pass | Baton Pass to Jynx; acceptable late package | Blissey; Zapdos; stay | Blissey; top |
| 14 | Lovely Kiss; Substitute; attack | Substitute; acceptable, missed package top | toxic Tyranitar absorber; Toxic; Cloyster | Heal Bell; miss |
| 15 | Lovely Kiss; Ice Beam; switch | Lovely Kiss; top | unscored | slept before move logged |
| 16 | Nightmare if available; attack; Vaporeon switch | Vaporeon; acceptable fallback | Tyranitar switch; Flamethrower on wake; stay | Flamethrower; acceptable |
| 17 | Growth/Baton Pass; Rhydon; Surf | sleeping Snorlax; miss, status-absorber handoff missed | Toxic; Zapdos; Heal Bell | Toxic; top |
| 18 | Sleep Talk; switch; burn turn | Sleep Talk Double-Edge; top | Tyranitar; Cloyster; Flamethrower | Cloyster; acceptable owner class |
| 19 | Rhydon into Explosion; Sleep Talk; Vaporeon | Sleep Talk Curse; acceptable | Explosion; Ice Beam branch; switch | Ice Beam; miss, failed named-branch punish |
| 20 | Double-Edge/Sleep Talk; Rest; switch | Double-Edge after wake; top | Explosion; switch; Ice Beam | Curse; miss |
| 21 | Double-Edge; Rhydon; Rest | Rhydon; acceptable, not top | Explosion; Ice Beam; switch | Explosion; top |
| 22 | Vaporeon; Earthquake; Snorlax | Vaporeon; top | Zapdos; Earthquake; Rock Slide | Earthquake; acceptable |
| 23 | Hydro Pump/Surf; Baton Pass; Rest | Hydro Pump; top despite miss | Blissey; Zapdos; stay | Zapdos; acceptable |
| 24 | Snorlax; Rhydon; Jynx | Ice Beam; miss, coverage route missed | Thunderbolt; HP Ice read; switch | Whirlwind; miss |
| 25 | Ice Beam; Lovely Kiss; Substitute | Substitute; miss, package safety missed | Whirlwind; Thunderbolt; switch | Thunderbolt; acceptable |

## Main Errors

Rest and sleeping-status handoff:
Turn 10 missed Snorlax's Rest reset after Zapdos paralysis pressure. Turn 17
then missed the revealed RestTalk Snorlax as a status absorber into Blissey's
Toxic. The correction is to ask whether an already-sleeping RestTalk piece can
blank status and preserve the active passer before trying a generic setup or
pass line.

Vaporeon/Jynx package:
The Vaporeon + Jynx structure was not just "water switches from Electric." Dry
Baton Pass to Jynx, Jynx Substitute before sleep pressure, and Vaporeon Ice
Beam into low Zapdos all converted specific branches. I was too willing to
switch out of visible pressure instead of asking which package move beat the
next board.

Cleric status reset:
Blissey revealed Heal Bell, which means old poisoned absorbers and Toxic clocks
cannot be carried forward by inertia. After Heal Bell, re-solve who can absorb
sleep/status and who is newly vulnerable.

Cloyster cash-out branch:
Explosion was live, but after naming Rhydon as the likely defensive owner I
still over-ranked Explosion on turn 19. Cloyster's Ice Beam, Curse, or other
setup/coverage can be the branch-punish that makes the later cash-out real.

Low phazer pressure:
Turn 24 missed Vaporeon's Ice Beam into a low Zapdos phazer. A low Flying phazer
does not take Spikes and may still convert with Whirlwind, so coverage that
removes or cripples it can beat a conservative switch.

## Reusable Lesson

When a package is partially revealed, stop treating each species as a standalone
standard set. Ask:

1. What is the package trying to pass, shield, sleep, phaze, or reset?
2. Which branch beats the visible active matchup?
3. Does the correct move spend the active piece, preserve it, or bring in a
   sleeping/statused owner to blank the opponent's answer?

Next proof should be a fresh replay only after the review: Vaporeon/Jynx or
similar package positions, RestTalk status-absorber handoffs, and self-KO
branches where a named resist or immunity changes the top move.
