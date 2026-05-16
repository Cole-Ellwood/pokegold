# Utility Screen/Screech Transfer 001 - gen2ou-2592987202 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/gen2ou-2592987202`

Raw log:
`https://replay.pokemonshowdown.com/gen2ou-2592987202.log`

Replay search source:
`https://replay.pokemonshowdown.com/search.json?format=gen2ou&page=5`

Mode: spectator public, vanilla GSC. Replay actual move is a pro-comparison
oracle, not an absolute answer key. No Team Preview: hidden teammates, moves,
items, and roles stayed in revealed / strong-prior / possible-only tiers.

Source-quality caveat: this is a public ladder/search replay, not a confirmed
tournament replay. It was selected because it was fresh to the local docs,
rated 1410 in the search feed, and came from a different player pool than the
same-pair smogtours transfers.

## Sources Checked

Local docs before/during study:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/measurement_minigoal_2026-05.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/policy_cards/active_pressure_before_status.md`
- `docs/pokemon_mastery/policy_cards/support_handoff_after_job.md`
- `docs/pokemon_mastery/policy_cards/hidden_role_voluntary_entry.md`
- `docs/pokemon_mastery/workspace/quick_tests/support_action_branch_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/screen_phaze_third_owner_probe_001_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/support_set_hidden_role_transfer_001_smogtours-gen2ou-921372_2026-05-14.md`
- `docs/pokemon_mastery/workspace/quick_tests/branch_absorber_transfer_001_smogtours-gen2ou-912287_2026-05-14.md`

Web/current sources used after scoring, before any further replay:

- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums, Tyranitar OU Revamp:
  `https://www.smogon.com/forums/threads/tyranitar-ou-revamp-done.3658517/`
- Smogon Forums, Gengar WIP:
  `https://www.smogon.com/forums/threads/gengar-wip.3703761/`
- Smogon Forums, Zapdos QC:
  `https://www.smogon.com/forums/threads/zapdos-qc-2-2-gp-2-2.3673848/`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, Move Analysis: Light Screen / Reflect:
  `https://www.smogon.com/forums/threads/move-analysis-light-screen-reflect.6235/`

## Contamination Control

- Local `rg` found no prior `2592987202` artifact before selection.
- The raw log was downloaded to `tmp/pokemon_mastery_replays/`.
- No future turns were inspected before freezing each turn's top-three
  candidates.
- Web and local study review happened only after the 30 side decisions were
  complete.
- Hidden moves such as Zapdos coverage, Tyranitar Screech, and Gengar Explosion
  were priced as strong priors or possible-only branches until revealed.

## Score Summary

Scored turns: 1-15.

Scorable decisions: 30.

Top-match: 11 / 30.

Acceptable-match: 23 / 30.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 25 / 30.

Route-converting move chosen: 21 / 30.

Branch-punish chosen: 13 / 22 applicable branch decisions.

Earliest meaningful error: turn 4 p1, where I defaulted to Spikes in the
Forretress mirror and missed Hidden Power coverage as the move that converted
against the opposing spiker.

Interpretation:
This is not progress. Severe, hidden-info, state, and mechanics gates held, and
acceptable-match cleared the 70% gate. But top-match fell to 36.7%, positive
selection and route conversion fell from the prior fresh transfer, and the main
errors were route-improving utility misses rather than harmless differences.

## Turn Notes

| Turn | Side | Frozen top three | Actual | Grade | Positive-selection tags |
| --- | --- | --- | --- | --- | --- |
| 1 | p1 | 1. HP/coverage if available; 2. switch absorber; 3. Thunder/status pressure | Thunder | acceptable; Thunder was ranked third and pressured Exeggutor | positive, route |
| 1 | p2 | 1. Sleep Powder; 2. status/item utility; 3. switch owner | Sleep Powder | top | positive, route |
| 2 | p1 | 1. switch to sleep-route owner; 2. Sleep Talk if revealed; 3. stay only with progress | Skarmory | top by class | positive, route, branch |
| 2 | p2 | 1. switch to Snorlax/Ground/support owner; 2. chip; 3. Explosion only with route name | Snorlax | top | positive, route, branch |
| 3 | p1 | 1. phaze Snorlax; 2. Toxic/Drill Peck; 3. switch Steel/Ghost owner | Forretress | acceptable by switch class, not top | positive only |
| 3 | p2 | 1. Curse or switch Skarmory answer; 2. direct attack; 3. support handoff | Forretress | acceptable support handoff, not top | positive, route |
| 4 | p1 | 1. Spikes; 2. Toxic; 3. switch Fire/pressure owner | Hidden Power | miss; missed coverage as mirror converter | none |
| 4 | p2 | 1. Spikes; 2. Toxic; 3. switch pressure owner | Spikes | top | positive, route |
| 5 | p1 | 1. Hidden Power to remove Forretress; 2. Spikes if p2 switches; 3. Spin only after Ghost price | Spikes | acceptable; branch-ranked Spikes landed | positive, route, branch |
| 5 | p2 | 1. switch/preserve Forretress with Ghost or fire owner; 2. Explosion branch; 3. stay only if needed | Gengar | top by class | positive, route, branch |
| 6 | p1 | 1. switch to special/Gengar owner; 2. attack if it pressures; 3. no Spin into Ghost | Raikou | top by class | positive, route, branch |
| 6 | p2 | 1. coverage into Forretress; 2. Explosion branch; 3. Snorlax/preserve if needed | Tyranitar | miss; missed Tyranitar pressure handoff | positive only |
| 7 | p1 | 1. switch to Tyranitar owner, Skarmory class; 2. Sleep Talk if revealed; 3. burn sleep only if safe | Skarmory | top | positive, route, branch |
| 7 | p2 | 1. Fire coverage into Steel branch if available; 2. Rock/Dark pressure; 3. Roar if hazards route | Flamethrower | top by coverage class | positive, route, branch |
| 8 | p1 | 1. switch to real Fire/Tyranitar owner; 2. sleeping Raikou pivot; 3. phaze only if concrete | Toxic | acceptable as preservation, but missed status-into-Gengar branch | positive only |
| 8 | p2 | 1. repeat Fire pressure; 2. Rock/Dark pressure; 3. handoff if Fire owner appears | Gengar | acceptable active pressure, but missed spinblock/status-immune handoff | positive, route |
| 9 | p1 | 1. switch to special/Explosion owner, Snorlax/Raikou class; 2. Forretress only if boom-priced; 3. phaze | Snorlax | acceptable by owner class, not exact | positive, route, branch |
| 9 | p2 | 1. Electric/coverage into Skarmory; 2. Explosion read; 3. switch Tyranitar if Raikou enters | Dynamic Punch | miss; missed anti-Normal utility | none |
| 10 | p1 | 1. Earthquake/coverage if available; 2. switch if no coverage; 3. Rest if preserving is the route | Rest | acceptable fallback, not top | positive, route |
| 10 | p2 | 1. Explosion into Snorlax if spinblock job can be spent; 2. Dynamic Punch; 3. switch if EQ expected | Exeggutor | miss; over-priced cash-out, missed pivot | none |
| 11 | p1 | 1. switch to Explosion/Psychic owner; 2. Sleep Talk if revealed; 3. stay asleep only if safe | Tyranitar | acceptable by defensive-owner class | positive, route, branch |
| 11 | p2 | 1. Stun Spore/status into switch if available; 2. Explosion high-risk; 3. Psychic/Giga chip | Zapdos | miss; missed Zapdos as pressure handoff | positive only |
| 12 | p1 | 1. Rock Slide; 2. Roar if available; 3. switch Raikou only if coverage feared | Rock Slide | top | positive, route |
| 12 | p2 | 1. HP Water/active punish if available; 2. Thunder; 3. switch owner | Reflect | miss; missed screen as branch-punish | positive only |
| 13 | p1 | 1. Roar if available; 2. Rock Slide; 3. switch only if coverage flips it | Rock Slide | acceptable fallback, not top | positive, route, branch |
| 13 | p2 | 1. active punish if available; 2. switch bulky owner; 3. Rest/Whirlwind package if revealed | Tyranitar | acceptable by owner class, not top | positive, route, branch |
| 14 | p1 | 1. switch to Water/Ground/Fighting owner; 2. mirror coverage; 3. Rock Slide only as fallback | Starmie | top by hidden-owner class | positive, route, branch |
| 14 | p2 | 1. mirror coverage if available; 2. Roar/Curse under Reflect; 3. switch owner | Screech | miss; failed to rank Defense-drop utility into receiver | none |
| 15 | p1 | 1. Surf/Water pressure; 2. Spin only after Gengar branch; 3. Recover/switch if needed | Surf | top | positive, route, branch |
| 15 | p2 | 1. physical follow-up if staying; 2. switch Zapdos/Snorlax; 3. Pursuit if Starmie flees | Zapdos | acceptable, not top | positive, route, branch |

## Main Errors

Forretress mirror, turn 4:
I treated Spikes as the default route in a mirror where Hidden Power coverage
was the revealed converter. In a support mirror, the first layer is not always
the first job; damaging the opposing spiker can make every later Spin, Spikes,
and switch cycle easier.

Gengar anti-Normal utility, turns 9-10:
I expected standard special pressure or Explosion and missed Dynamic Punch as
the middle route: it punishes the Snorlax/Tyranitar owner, creates confusion,
and can put the target into later Explosion range without spending Gengar's
spinblock role immediately. The follow-up miss was over-pricing Explosion while
the replay preserved Gengar and pivoted.

Zapdos/Tyranitar support package, turns 12-14:
I read Zapdos versus Tyranitar as HP Water or switch, then missed Reflect as the
route action that blunted Rock Slide and enabled a safer Tyranitar handoff. I
then missed Screech as the move that punished the Water/Starmie receiver under
the screen package.

Starmie route discipline, turn 15:
The one clean transfer was using Surf over Rapid Spin. Gengar was public, so
Spin was not the route until the Ghost branch was covered. Surf punished the
active Tyranitar and still hit the Zapdos handoff.

## Reusable Lesson

When a utility-capable piece voluntarily enters or stays in a bad-looking
matchup, do not reduce the choice to attack-or-switch. Rank the support move
that beats the named receiver:

1. Gengar: Dynamic Punch can be the anti-Normal route before Explosion.
2. Zapdos/Raikou: Reflect can be the branch-punish that creates the next
   physical handoff or phaze window.
3. Tyranitar: Screech can punish the receiver and pair with Rock Slide, Pursuit,
   or a forced switch.
4. Starmie/spinners: if a Ghost is public, active pressure or Ghost coverage
   usually outranks Spin until the Ghost branch is answered.

Next proof must be a fresh unseen transfer. The existing constructed Screech
probe already passed, so another same-shape constructed probe would be
regression only and would not prove transfer.
