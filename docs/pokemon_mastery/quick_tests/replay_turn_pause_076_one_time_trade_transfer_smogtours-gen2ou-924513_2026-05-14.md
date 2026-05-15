# Replay Turn-Pause 076 One-Time Trade Transfer - smogtours-gen2ou-924513 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-924513`.

Context source: Smogon ADPL IX Week 4. The thread lists Bohrier vs NotVeryCake
as a GSC OU slot and links this replay in NotVeryCake's April 9, 2026 win post.

Current web sources checked:

- `https://www.smogon.com/forums/threads/adpl-ix-week-4.3780197/`
- `https://www.smogon.com/forums/threads/gsc-ou-global-championship-2026-round-1-stage-2.3781519/`
- `https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-2.3777598/`
- `https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-4.3778203/`

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/policy_cards/cashout_boundary.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/quick_tests/one_time_trade_taxonomy_probe_001_2026-05-14.md`

Mode: spectator public, no keyword screen, fixed species-aware prompt helper.

Contamination control:

- Local docs were searched for `924513`; no prior local use was found.
- The raw log was downloaded and summarized for metadata only before the run.
- No move-keyword screen was used.
- Decisions were frozen turn by turn before revealing the matching turn, except
  p1 turn 12, which is marked unscored because no top answer was committed
  before reveal.
- This is ADPL rather than a GSC Circuit top-cut source, so treat it as current
  public practice evidence, not a final-exam source.

## Score Summary

Scored decisions: 35 side decisions from turns 1-18.

Unscored decision: p1 turn 12, because no frozen answer was committed before
reveal.

Top-match: 16 / 35.

Acceptable-match: 24 / 35.

Severe blunders: 0.

State errors: 1.

Hidden-information errors: 0.

Mechanics errors: 0.

Earliest meaningful error: Turn 2. I wanted Exeggutor to keep using status,
while the actual line preserved it by switching Snorlax into Snorlax.

Main pattern: one-time trade taxonomy still needs transfer. The key miss was
turn 5: after Starmie already removed Spikes with Rapid Spin, Cloyster still
cashed out with Explosion because removing the spinner was the route value.
I treated that as a slower status/control position.

## Focused Transfer Result

| Class | Evidence | Grade |
| --- | --- | --- |
| Spinner-removal cash-out after Spin | Turn 5: missed Cloyster Explosion into Starmie after Rapid Spin. | miss |
| Absorber or preserve branch | Turn 14 and turn 16: switched out sleeping Zapdos/Exeggutor to preserve route pieces. | acceptable |
| Preserve sleeper / Sleep Clause tendency | Turn 16-17 showed mixed behavior: sleeping Skarmory stayed one turn, then p2 pivoted to Snorlax. | partial |
| Rest wake timing | Turn 11: missed Snorlax's Rest wake into Earthquake. | state error |
| Endgame conversion | Not tested in this opening segment. | no evidence |

## Turn Notes

### Turn 1

Public state: p1 Exeggutor 100% versus p2 Raikou 100%.

Frozen answer:

- p1: Sleep Powder; status the lead or receiver before Raikou takes control.
- p2: switch Snorlax or another status receiver.

Actual choices: p2 switched Snorlax. p1 used Stun Spore and missed.

Grade: p1 acceptable, p2 top-match. The status class was right, but paralysis
instead of sleep was the actual route.

### Turn 2

Public state: p1 Exeggutor 100% versus p2 Snorlax 100%.

Frozen answer:

- p1: Stun Spore again.
- p2: Double-Edge.

Actual choices: p1 switched Snorlax. p2 used Double-Edge.

Grade: p1 miss, p2 top-match.

### Turn 3

Public state: p1 Snorlax 71% versus p2 Snorlax 98%.

Frozen answer:

- p1: Double-Edge.
- p2: Double-Edge.

Actual choices: p1 switched Cloyster. p2 used Double-Edge.

Grade: p1 miss, p2 top-match. I was late to the Cloyster support handoff.

### Turn 4

Public state: p1 Cloyster 74% versus p2 Snorlax 99%.

Frozen answer:

- p1: Spikes.
- p2: switch to hazard-control or own Cloyster.

Actual choices: p2 switched Starmie. p1 used Spikes.

Grade: p1 top-match, p2 acceptable-match.

### Turn 5

Public state: p1 Cloyster 80% versus p2 Starmie 100%, Spikes on p2 side.

Frozen answer:

- p1: Toxic; poison the spinner before trying to reset hazards.
- p2: Rapid Spin.

Actual choices: p2 used Rapid Spin and removed Spikes. p1 used Explosion,
removing Starmie.

Grade: p1 miss, p2 top-match. The reusable miss is that cashing out after Spin
can still be correct when the trade removes the spinner and changes all future
hazard turns.

### Turn 6

Public state: p1 Zapdos 100% versus p2 Snorlax 100%.

Frozen answer:

- p1: Thunder.
- p2: Double-Edge.

Actual choices: p1 used Thunder. p2 used Double-Edge.

Grade: both top-match.

### Turn 7

Public state: p1 Zapdos 66% versus p2 Snorlax 72%.

Frozen answer:

- p1: Thunder.
- p2: Double-Edge.

Actual choices: p1 used Thunder, paralyzing Snorlax. p2 used Double-Edge.

Grade: both top-match.

### Turn 8

Public state: p1 Zapdos 25% versus p2 paralyzed Snorlax 38%.

Frozen answer:

- p1: Thunder.
- p2: Double-Edge.

Actual choices: both used Rest.

Grade: both miss. I underpriced mutual route preservation.

### Turn 9

Public state: sleeping Zapdos 100% versus sleeping Snorlax 100%.

Frozen answer:

- p1: switch Exeggutor or another pressure piece.
- p2: switch Raikou to preserve sleeping Snorlax for Sleep Clause value.

Actual choices: p1 switched Tyranitar. p2 used Sleep Talk, calling Rest.

Grade: p1 acceptable, p2 miss. The user-supplied "sleep often switches out" rule
was useful but not a script.

### Turn 10

Public state: p1 Tyranitar 100% versus sleeping Snorlax 100%.

Frozen answer:

- p1: Rock Slide.
- p2: Sleep Talk.

Actual choices: p1 used Rock Slide and missed. p2 used Sleep Talk, calling
Earthquake.

Grade: both top-match.

### Turn 11

Public state: p1 Tyranitar 66% versus sleeping Snorlax 100%.

Frozen answer:

- p1: switch Exeggutor, with Zapdos as the Earthquake-blanking alternative.
- p2: Sleep Talk.

Actual choices: p1 switched Zapdos. p2 woke and used Earthquake.

Grade: p1 acceptable, p2 miss. State error: I missed the Rest wake timing.

### Turn 12

Public state: p1 sleeping Zapdos 100% versus awake Snorlax 100%.

Frozen answer:

- p2: Double-Edge.
- p1: unscored; no answer was committed before reveal.

Actual choices: p1 used Sleep Talk, calling Rest. p2 used Double-Edge.

Grade: p1 unscored, p2 top-match.

### Turn 13

Public state: p1 sleeping Zapdos 64% versus p2 Snorlax 99%.

Frozen answer:

- p1: Sleep Talk.
- p2: Double-Edge.

Actual choices: p1 used Sleep Talk, calling Rest. p2 used Double-Edge.

Grade: both top-match.

### Turn 14

Public state: p1 sleeping Zapdos 60% versus p2 Snorlax 97%.

Frozen answer:

- p1: switch Snorlax or another physical absorber.
- p2: Double-Edge.

Actual choices: p1 switched Exeggutor. p2 used Double-Edge.

Grade: p1 acceptable, p2 top-match.

### Turn 15

Public state: p1 Exeggutor 66% versus p2 Snorlax 95%.

Frozen answer:

- p1: Stun Spore.
- p2: Double-Edge or a defensive switch.

Actual choices: p2 switched Skarmory. p1 used Sleep Powder.

Grade: p1 acceptable, p2 miss. Status into the receiver was correct, but I did
not identify sleep as the route.

### Turn 16

Public state: p1 Exeggutor 73% versus sleeping Skarmory 100%.

Frozen answer:

- p1: switch Tyranitar to exploit the sleeping Skarmory.
- p2: switch out to preserve the sleeper's Sleep Clause value.

Actual choices: p1 switched sleeping Zapdos. p2 stayed in asleep.

Grade: p1 acceptable, p2 miss. The sleeper was not immediately switched out.

### Turn 17

Public state: sleeping Zapdos 66% versus sleeping Skarmory 100%.

Frozen answer:

- p1: Sleep Talk.
- p2: switch Snorlax or Raikou.

Actual choices: both switched Snorlax in.

Grade: p1 miss, p2 acceptable-match.

### Turn 18

Public state: Snorlax mirror, p1 77%, p2 100%.

Frozen answer:

- p1: Double-Edge.
- p2: Double-Edge.

Actual choices: p2 used Double-Edge. p1 used Curse.

Grade: p1 miss, p2 top-match.

## Error Classes

- Spinner-removal cash-out: after Rapid Spin succeeds, removing the spinner may
  still be the correct one-time trade.
- Rest wake timing: I repeated the old wake-count miss on turn 11.
- Status route choice: Exeggutor status turns need better separation between
  sleep, paralysis, and direct switch-preservation.
- Sleeper handling: "switch out the sleeper" is a useful prior, not a hard
  rule; Sleep Talk and one-turn stay lines still need pricing.

## Next Rep

Create `spinner_removed_hazard_cashout_probe_001` from turn 5, then transfer it
to a fresh no-keyword-screen replay. Score whether a support piece can cash out
after the opponent already gets immediate utility, when the lasting route value
is removing that utility piece.
