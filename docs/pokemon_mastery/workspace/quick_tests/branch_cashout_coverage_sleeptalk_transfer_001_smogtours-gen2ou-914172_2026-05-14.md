# Branch Cash-Out Coverage SleepTalk Transfer 001 - smogtours-gen2ou-914172 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-914172`.

Context source:
`https://www.smogon.com/forums/threads/gsc-trios-won-by-les-mehbouls.3776135/page-4`.

Mode: focused spectator-public vanilla GSC replay transfer. No team sheet was
supplied, no Team Preview was assumed, and only the public state revealed so
far was used.

Selected measurable action: transfer
`branch_cashout_coverage_sleeptalk_probe_001` to a fresh no-keyword-screen
replay. The checklist before switching was: price cash-out, coverage,
SleepTalk stay, then handoff.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/workspace/quick_tests/branch_cashout_coverage_sleeptalk_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`

Web sources checked:

- Smogon GSC Trios final page.
- Replay source `smogtours-gen2ou-914172`.

Contamination control:

- Local docs were searched for `914172`; no prior local use was found.
- Raw `.log` was downloaded to `tmp/pokemon_mastery_replays/`.
- The replay UI was not watched.
- The replay was selected from the GSC Trios source list before content
  screening.

## Score Summary

Focused branch-scored decisions: 23 from turns 1-12.

Unscored: p1 turn 3, because Cloyster's Explosion removed the target before
p1's selected move was logged.

Top-match: 8 / 23.

Acceptable-match: 12 / 23.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Earliest focused error: turn 1 p1. I chose immediate Double-Edge pressure with
Snorlax into Cloyster; the replay used Curse before attacking.

Repeated error: the checklist helped with obvious cash-out and some SleepTalk
pricing, but the miss shifted to exact handoff identity and set timing. I
missed Curse before attack, Golem as the Thunder receiver, Umbreon/Snorlax
handoff timing around poisoned Raikou, and Golem handoff into Tyranitar after
Sleep Talk was revealed.

## Focused Turn Notes

### Turn 1

Public state: p1 Snorlax vs p2 Cloyster.

Frozen p1 answer: Double-Edge. Branch read: active damage is enough into
Cloyster or its early receiver.

Frozen p2 answer: Spikes.

Actual choices: p2 Spikes; p1 Curse.

Grade: p1 miss, p2 top. Lesson: setup can be the route action before active
damage when the first support turn is predictable.

### Turn 2

Public state: p1 Snorlax at `atk+1 def+1` vs p2 Cloyster after Spikes.

Frozen p1 answer: Double-Edge.

Frozen p2 answer: Toxic, with Explosion a serious cash-out if Snorlax becomes
unmanageable.

Actual choices: p2 Toxic; p1 Double-Edge, critting Cloyster to 7%.

Grade: both top. Lesson: status before cash-out was correct while Cloyster
could still put a clock on the boosted Rest route.

### Turn 3

Public state: p1 boosted poisoned Snorlax 87% vs p2 Cloyster 13%.

Frozen p2 answer: Explosion. Cash-out now because Cloyster has already set
Spikes and landed Toxic.

Actual choice: p2 Explosion, Snorlax survived at 27%.

Grade: p2 top. p1 unscored because no p1 move was logged after the target
fainted.

### Turn 4

Public state: p1 Snorlax 33% poisoned, boosted, vs p2 Tyranitar 100%.

Frozen p1 answer: Rest.

Frozen p2 answer: Roar or phaze if available.

Actual choices: p2 Curse; p1 Rest.

Grade: p1 top, p2 miss. Lesson: Tyranitar chose to match setup before phazing.

### Turn 5

Public state: p1 Rested Snorlax asleep, no Sleep Talk revealed, vs boosted
Tyranitar.

Frozen p1 answer: Sleep Talk if present, otherwise stay only if the sleep turn
is affordable.

Frozen p2 answer: Roar or direct Rock Slide pressure.

Actual choices: p1 switched Umbreon; p2 Rock Slide.

Grade: p1 miss, p2 acceptable. Lesson: before Sleep Talk is revealed, the
sleeping Rest piece may hand off instead of staying.

### Turn 6

Public state: p1 Umbreon 58% vs p2 boosted Tyranitar.

Frozen p1 answer: Charm or other route-stopper; Toxic if the receiver is the
priced branch.

Frozen p2 answer: continue pressure or hand off to a special attacker if
Umbreon stops Tyranitar.

Actual choices: p2 switched Raikou; p1 Toxic.

Grade: p1 acceptable, p2 top. Lesson: status into the handoff was the branch
action.

### Turn 7

Public state: p1 Umbreon 64% vs poisoned p2 Raikou.

Frozen p1 answer: stay and recover if pressured.

Frozen p2 answer: Thunder.

Actual choices: p2 Thunder missed; p1 Moonlight.

Grade: both top. Lesson: do not hand off if the active wall has the recovery
route and the opponent's progress is poison-limited.

### Turn 8

Public state: p1 Umbreon 100% vs poisoned p2 Raikou.

Frozen p1 answer: Toxic into a possible switch; I did not price the sleeping
Snorlax handoff enough.

Frozen p2 answer: switch Tyranitar as the counter-pivot.

Actual choices: p1 switched Snorlax; p2 Thunder.

Grade: both miss. Lesson: p1 used sleeping Snorlax as the special handoff
despite Spikes; p2 kept active pressure instead of switching.

### Turn 9

Public state: p1 sleeping Snorlax 64% vs poisoned p2 Raikou.

Frozen p1 answer: stay and absorb; Sleep Talk if present.

Frozen p2 answer: Thunder.

Actual choices: p2 switched Tyranitar; p1 Sleep Talk called Rest.

Grade: p1 acceptable, p2 miss. Lesson: Sleep Talk stay transferred after the
set reveal, but p2 used the receiver branch instead of another Thunder.

### Turn 10

Public state: p1 revealed RestTalk Snorlax asleep vs p2 Tyranitar.

Frozen p1 answer: Sleep Talk because the set can stay active.

Frozen p2 answer: Curse or Rock Slide.

Actual choices: p1 switched Golem; p2 Roar dragged Zapdos.

Grade: both miss. Lesson: SleepTalk being revealed does not make staying a
script. Tyranitar's phaze branch made Golem the handoff.

### Turn 11

Public state: p1 Zapdos vs p2 Tyranitar after Roar.

Frozen p1 answer: switch Golem into Tyranitar pressure.

Frozen p2 answer: Rock Slide or continue Tyranitar pressure.

Actual choices: p1 switched Umbreon; p2 switched poisoned Raikou.

Grade: both miss. Lesson: both sides solved the next board, not the active
visible matchup. My Golem handoff missed the Raikou counter-handoff.

### Turn 12

Public state: p1 Umbreon 94% vs poisoned p2 Raikou.

Frozen p1 answer: stay and recover.

Frozen p2 answer: Thunder.

Actual choices: p1 switched sleeping Snorlax; p2 Thunder.

Grade: p1 miss, p2 top. Lesson: the Snorlax special handoff repeated even with
Sleep Talk and Spikes involved.

## Error Classes

- Setup before attack: missed Snorlax Curse on turn 1.
- Coverage/receiver pricing: missed Golem after Snorlax revealed Thunder.
- SleepTalk is not a script: correctly stayed once after reveal, then
  over-stayed when Tyranitar's phaze branch made Golem the handoff.
- Handoff identity: missed Umbreon/Snorlax and Tyranitar/Raikou paired
  handoffs.

## Next Rep

Make a four-scenario micro-probe from this transfer:

1. Setup before active pressure.
2. Receiver after revealed coverage.
3. SleepTalk stay versus phaze handoff.
4. Paired handoff where both sides switch to the next-board answer.
