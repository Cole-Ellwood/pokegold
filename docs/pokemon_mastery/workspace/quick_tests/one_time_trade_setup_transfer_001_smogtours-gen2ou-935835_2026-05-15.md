# One-Time Trade Setup Transfer 001 - smogtours-gen2ou-935835 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-935835`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-935835.log`

Replay search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou`

Web/current source checked:

- Pokemon Showdown public replay search API for current Gen 2 OU replays.
- Pokemon Showdown raw replay log for `smogtours-gen2ou-935835`.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/workspace/quick_tests/status_receiver_positive_transfer_002_smogtours-gen2ou-935859_2026-05-15.md`

Mode: spectator public. No Team Preview. No team paste, replay UI, or future
log turns were used before freezing answers. Hidden teammates and unrevealed
moves were treated as revealed, strong-prior, or possible-only.

Contamination control:

- Local `rg` found no prior `935835` use before selection.
- Replay was selected from the current Showdown Gen 2 OU search API without
  keyword screening for Jynx, Thief, Forretress, Toxic, Substitute, Nightmare,
  RestTalk, Explosion, Self-Destruct, or one-time trades.
- Used only the local turn-pause helper before each reveal.
- Scoring covers turns 1-15, exactly 30 side decisions.

Selected action:
Fresh transfer after `status_receiver_positive_transfer_002`, focused on
positive move selection after setup/support pressure. The sample naturally
tested status-capable lead item removal, cash-out restraint after Spikes,
counter-handoff into Tyranitar, and Substitute/Nightmare pressure into RestTalk
Snorlax.

## Score

- Scored decisions: 30
- Top match: 8/30
- Acceptable match: 18/30
- Severe blunders: 0
- State errors: 0
- Hidden-info errors: 0
- Mechanics errors: 0
- Positive-selection: 20/30
- Route-converting move chosen: 10/22 applicable
- Branch-punish chosen: 8/20 applicable
- Earliest meaningful error: turn 1

Interpretation:
Not progress. The severe/hidden-info gate held, and the turn-4 all-in cash-out
overcall was contained as a non-severe miss because the answer named the hidden
Ghost risk and Toxic fallback. The action-quality signal was poor: top-match
and acceptable-match both fell, and the strongest misses were positive move
selection, not safety.

## Turn Notes

| Turn | Side | Frozen ranked candidates | Actual | Grade | Positive-selection tags |
| --- | --- | --- | --- | --- | --- |
| 1 | p1 | 1. Lovely Kiss; 2. Thief; 3. Ice/Psychic chip | Thief | miss; defaulted to sleep over item-route pressure | positive but not route |
| 1 | p2 | 1. switch sleep absorber; 2. Double-Edge; 3. Lovely Kiss if available | Double-Edge | miss; under-ranked active lead punish | none |
| 2 | p1 | 1. Hypnosis; 2. Explosion only as high-risk; 3. Thunder/Dynamic Punch | Forretress | miss; failed to preserve Gengar and hand off | none |
| 2 | p2 | 1. switch absorber; 2. coverage if available; 3. stay pressure | Thunder | miss; missed special coverage into Gengar pivot | none |
| 3 | p1 | 1. Spikes; 2. Toxic; 3. preserve Forretress | Spikes | top-match | positive, route |
| 3 | p2 | 1. coverage into Forretress; 2. switch; 3. Rest later | Thunder | acceptable-match by active coverage | positive |
| 4 | p1 | 1. Explosion high-risk; 2. Toxic fallback; 3. switch/preserve | Toxic | acceptable-match; correct fallback, wrong top | positive, route |
| 4 | p2 | 1. Thunder/coverage; 2. switch answer; 3. Rest later | Thunder | top-match | positive, route |
| 5 | p1 | 1. Gengar handoff; 2. Snorlax handoff; 3. Explosion only as read | Snorlax | acceptable-match by handoff class | positive |
| 5 | p2 | 1. Rest; 2. Thunder; 3. switch | Thunder | acceptable-match | positive active pressure only |
| 6 | p1 | 1. Curse; 2. Double-Edge; 3. Lovely Kiss if available | Double-Edge | acceptable-match; right pressure, wrong order | positive, route |
| 6 | p2 | 1. Rest; 2. switch; 3. Thunder/Double-Edge | Tyranitar | acceptable-match by switch class | positive |
| 7 | p1 | 1. Earthquake/coverage if available; 2. switch owner; 3. Curse | Starmie | miss; failed to name the cleaner Tyranitar owner | none |
| 7 | p2 | 1. Roar/phaze if available; 2. Rock Slide; 3. Dynamic Punch | Dynamic Punch | miss; under-ranked coverage into switch | positive active pressure only |
| 8 | p1 | 1. Surf; 2. Recover; 3. double/counter-switch | Surf | top-match | positive, route |
| 8 | p2 | 1. switch Zapdos/Water answer; 2. stay pressure; 3. sack | Zapdos | top-match by class | positive, branch |
| 9 | p1 | 1. Snorlax handoff; 2. Recover scout; 3. Surf chip | Snorlax | top-match | positive, branch |
| 9 | p2 | 1. Thunder; 2. Thunder Wave; 3. switch | Thunder Wave | miss; status branch under-ranked | positive active pressure only |
| 10 | p1 | 1. Double-Edge; 2. Curse; 3. Rest if available | Earthquake | miss; failed to punish Tyranitar branch with revealed-possible coverage | none |
| 10 | p2 | 1. Thunder/Hidden Power pressure; 2. Tyranitar branch; 3. stay status | Tyranitar | acceptable-match by branch class | positive, branch |
| 11 | p1 | 1. Earthquake; 2. preserve Snorlax; 3. Double-Edge | Forretress | miss; failed to obey preservation handoff | none |
| 11 | p2 | 1. switch Zapdos; 2. Dynamic Punch; 3. Rock Slide | Rock Slide | miss; missed revealed safer punish | none |
| 12 | p1 | 1. Starmie handoff; 2. Snorlax Earthquake; 3. no blind Explosion | Starmie | top-match | positive, branch |
| 12 | p2 | 1. switch to Snorlax/Zapdos; 2. Rock Slide; 3. preserve Tyranitar | Snorlax | acceptable-match by switch class | positive |
| 13 | p1 | 1. Surf; 2. Substitute if expecting Rest; 3. Recover | Substitute | miss; named Rest but did not punish it | none |
| 13 | p2 | 1. Rest; 2. Thunder; 3. switch | Rest | top-match | positive, route |
| 14 | p1 | 1. Surf; 2. Recover; 3. switch/preserve | Nightmare | miss; failed to convert Substitute into sleep punishment | none |
| 14 | p2 | 1. Sleep Talk; 2. switch Zapdos/Starmie; 3. stay asleep if forced | Sleep Talk -> Double-Edge | top-match | positive, route |
| 15 | p1 | 1. Surf; 2. Recover/Substitute; 3. switch/preserve | Substitute | miss; missed continued Sub/Nightmare route | none |
| 15 | p2 | 1. Sleep Talk; 2. switch Starmie/Zapdos; 3. stay only if Nightmare clock acceptable | Starmie | acceptable-match; switch branch named but under-ranked | positive, branch |

## Main Errors

Turn 1:
Jynx into Snorlax repeated the active-context target. I ranked Lovely Kiss over
Thief. The actual item removal was the positive move because it improved
through the obvious Snorlax/sleep-absorber map without relying on sleep
landing.

Turn 4:
I still overcalled Forretress Explosion after Spikes, but this time the failure
stayed bounded: hidden Ghost/immunity was named and Toxic was the fallback. The
actual Toxic confirms the correct direction: support job delivered, then
convert with status before spending the support piece.

Turns 13-15:
The biggest route-conversion miss was Starmie. After Snorlax was forced into
Rest, Substitute was the branch-punish and Nightmare was the route-converting
follow-up. I kept ranking generic Surf pressure and missed the custom
Sub/Nightmare punishment package.

## Reusable Lesson

When a status-capable lead faces an obvious bulky receiver, rank item removal
and coverage before generic sleep if those moves improve through both the
active target and the absorber branch.

When a support piece has already done its job, do not spend it just because a
big target is visible. Ask whether status, coverage, or a handoff converts
through the same target while preserving the one-time trade.

When a move reveals a package, reclassify the route immediately. Substitute
into RestTalk Snorlax is not passive scouting if Nightmare is available; it is
the branch-punish route and should outrank generic Surf pressure.

Next rep:
Fresh replay transfer or expert review focused on item-removal and custom
punishment packages after a set reveal. Keep the cash-out gate active, but do
not treat 0 severe errors as progress unless top-match, acceptable-match,
route conversion, and branch-punish scores also improve.
