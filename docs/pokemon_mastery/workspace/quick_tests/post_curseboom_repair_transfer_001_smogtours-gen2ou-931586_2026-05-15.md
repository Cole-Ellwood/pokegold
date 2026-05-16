# Post-CurseBoom Repair Transfer 001 - 2026-05-15

Source:
- Replay: https://replay.pokemonshowdown.com/smogtours-gen2ou-931586
- Log: https://replay.pokemonshowdown.com/smogtours-gen2ou-931586.log

Mode: spectator public.

Contamination control: selected from current Showdown search metadata after
local `rg` found no prior use of `931586`. Raw log turns were revealed through
the helper one turn at a time. Stopped after turn 12 at 24 scored side
decisions.

Pre-freeze packet:
- `active_context.md`
- `live_core.md`
- `replay_turn_pause_protocol.md`
- `heuristic_core/role_package_ledger.md`
- `heuristic_core/reset_loop_denial.md`
- `heuristic_core/public_info_tiers.md`
- `heuristic_core/name_next_board_owner.md`
- `heuristic_core/branch_punish_ranking.md`

Post-score sources:
- Smogon GSC Moltres analysis: Moltres is a Fire Blast/Sunny Day offensive
  route that uses RestTalk for longevity and can act as a sleep sponge.
- Smogon GSC Zapdos analysis: Hidden Power Ice is preferred, but it remains
  hidden information until revealed or side-known; Zapdos also forces switches
  that pair with Spikes.
- Smogon GSC sample teams: Fire offense uses Jynx, Snorlax, and Exeggutor to
  weaken or remove special walls so Fire-types can enter.

## Score Summary

Decisions: 24.

Top-match: 11/24.

Acceptable-match: 19/24.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 1.

Mechanics errors: 0.

Positive-selection: 22/24.

Route-converting move chosen: 18/24.

Branch-punish chosen: 15/24.

Role-package update obeyed: 14/18 relevant package decisions.

Side-known oracle gaps: 1, turn 11 p1. Switching to a Zapdos owner was right
by class, but exact Snorlax over Nidoking was side-known.

Earliest meaningful error: turn 1. I missed the double-switch route: p1 left
Nidoking for Cloyster and p2 left Snorlax for Moltres. My answer stayed on the
generic sleep/absorber script.

Repeated-error check:
- Voluntary-entry hidden-coverage overread: 1 instance, turn 6 p1.
- Boosted boom-before-phaze survival miss: 0 instances.

This starts a restarted sample after the CurseBoom repair. It is not progress
proof.

## Turn Notes

| Turn | Side | Frozen route | Actual | Grade |
| --- | --- | --- | --- | --- |
| 1 | p1 | Lovely Kiss / Earthquake / Thief | Cloyster | miss |
| 1 | p2 | switch sleep/status absorber; attack fallback | Moltres | miss |
| 2 | p1 | switch Fire answer; Surf/Explosion fallback | Spikes | acceptable |
| 2 | p2 | Fire Blast | Fire Blast | top |
| 3 | p1 | switch Fire answer | Tyranitar | top by class |
| 3 | p2 | Fire Blast | Fire Blast | top |
| 4 | p1 | Rock Slide | Rock Slide | top |
| 4 | p2 | switch out of Rock pressure | Exeggutor | acceptable |
| 5 | p1 | preserve Tyranitar; switch absorber/sack | Zapdos | acceptable |
| 5 | p2 | Sleep Powder; Explosion; Giga Drain | Giga Drain | acceptable |
| 6 | p1 | Hidden Power if carried; Thunder fallback | Thunder | acceptable, hidden-info error |
| 6 | p2 | Sleep Powder; Explosion | Explosion | acceptable |
| 7 | p1 | switch Tyranitar | Tyranitar | top |
| 7 | p2 | Fire Blast | Fire Blast | top |
| 8 | p1 | Rock Slide | Rock Slide | top |
| 8 | p2 | switch Ground/Rock owner | Golem | top by class |
| 9 | p1 | switch off Tyranitar, sack or Golem owner | Machamp | miss |
| 9 | p2 | Earthquake | Earthquake | top |
| 10 | p1 | Cross Chop / attack | Cross Chop | top |
| 10 | p2 | switch Flying/Psychic answer | Zapdos | acceptable |
| 11 | p1 | switch Zapdos owner by class | Snorlax | acceptable, oracle gap |
| 11 | p2 | Thunder or Hidden Power pressure | Hidden Power | top |
| 12 | p1 | attack or Curse with Snorlax | Nidoking | miss |
| 12 | p2 | switch out of Snorlax pressure | Cloyster | acceptable |

## Reusable Lesson

The CurseBoom fix held in this packet because no phaze/Explosion timing miss
recurred. The voluntary-entry rule still needs pressure: Zapdos entering
Exeggutor made Hidden Power Ice a strong prior, but not public proof. The
correct answer shape is:

```text
Zapdos package: direct pressure or absorber; Hidden Power is strong prior.
Top public line can be Thunder/status/pressure with Hidden Power named as
side-known or read-based, not as revealed fact.
```

The bigger route miss was first-turn double-switch ownership. When both leads
have obvious scripts, the next owner can matter more than the active exchange:

```text
Nidoking vs Snorlax is not only sleep versus absorber.
Ask which side wants Cloyster, Moltres, or another owner on the next board.
```
