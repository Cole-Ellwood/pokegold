# Absorber Transaction Transfer 001 - 2026-05-15

Source:
- Replay: https://replay.pokemonshowdown.com/smogtours-gen2ou-932554
- Log: https://replay.pokemonshowdown.com/smogtours-gen2ou-932554.log

Mode: spectator public.

Contamination control: raw log was revealed only through each scored turn
before freezing answers. Turns after 10 were read only after the packet stopped
at 20 side decisions and are postmortem evidence, not scored frozen answers.

Pre-freeze packet:
- `active_context.md`
- `live_core.md`
- `heuristic_core/role_package_ledger.md`
- `replay_turn_pause_protocol.md`

Post-score source checks:
- Smogon GSC Nidoking analysis: Nidoking is a mixed attacker with Earthquake,
  BoltBeam coverage, and Lovely Kiss or Thief as the fourth-slot pressure.
- Smogon GSC Zapdos analysis and sample-team notes: RestTalk Zapdos commonly
  combines offensive pressure, Spikes immunity, and status-sponge value.

## Score Summary

Decisions: 20 side decisions, turns 1-10.

Top-match: 13/20.

Acceptable-match: 17/20.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 1.

Mechanics errors: 0.

Positive-selection: 17/20.

Route-converting move chosen: 16/20.

Branch-punish chosen: 13/20.

Role-package update obeyed: 6/9 relevant package decisions.

Earliest meaningful error: turn 8 p1. I kept the active Electric mirror script
and did not name the Nidoking counter-handoff branch that Snorlax covered.

Stop condition: turn 9 p1 and turn 10 p1 repeated the same support-package
miss. Zapdos entering Nidoking was a public sleep-absorber transaction before
it was a hidden-coverage clue.

## Turn Table

| Turn | Side | Frozen top / ranked route | Actual | Grade | Tags |
| --- | --- | --- | --- | --- | --- |
| 1 | p1 | Spikes; Toxic; Surf/Explosion | Spikes | top | positive, route |
| 1 | p2 | Body Slam/Double-Edge; Curse; Electric/Forretress switch | Zapdos | acceptable | positive, branch |
| 2 | p1 | Raikou/Snorlax special owner; Toxic; Explosion read | Raikou | top | positive, route, branch |
| 2 | p2 | Thunder/Thunderbolt; switch; Rest | Hidden Power | acceptable | positive, route |
| 3 | p1 | Thunder; Roar; switch | Thunder | top | positive, route |
| 3 | p2 | Snorlax/Ground switch; attack; Rest | Snorlax | top | positive, route, branch |
| 4 | p1 | Thunder; switch Steel/Skarm; Roar | Thunder | top | positive, route |
| 4 | p2 | Attack; Curse; Rest | Curse | acceptable | positive, route |
| 5 | p1 | Steelix/Normal resist; Thunder; Roar | Steelix | top | positive, route, branch |
| 5 | p2 | Attack; Curse; Rest | Earthquake | acceptable | positive, branch |
| 6 | p1 | Roar; Earthquake; Explosion | Roar | top | positive, route, package |
| 6 | p2 | Earthquake; Rest; switch | Earthquake | top | positive, route |
| 7 | p1 | Raikou/Snorlax switch; Roar; Explosion | Raikou | top | positive, route, save-piece |
| 7 | p2 | Hidden Power; switch; Thunder | Hidden Power | top | positive, route |
| 8 | p1 | Thunder; Roar; switch if Snorlax branch dominates | Snorlax | miss | route error |
| 8 | p2 | Snorlax/Ground switch; attack; Rest | Nidoking | top | positive, route, branch |
| 9 | p1 | Body Slam/Double-Edge; switch Steelix/Cloyster if sleep; Curse/Rest | Zapdos | miss | package miss |
| 9 | p2 | Lovely Kiss; Thief/status; Earthquake/Thunder | Lovely Kiss | top | positive, route |
| 10 | p1 | Hidden Power if side-known/strong prior; switch fallback; RestTalk if set | Thunder | miss | package miss, hidden-info error |
| 10 | p2 | Lovely Kiss; Thunder/Ice Beam; switch | Lovely Kiss | top | positive, route |

## Postmortem

The new role ledger helped in the early phaze and preservation sequence:
Steelix's Roar job was identified, then preserved at 27%.

The miss was not "Zapdos has coverage" knowledge. That knowledge is true as a
strong prior in GSC, but it was the wrong first question. When Zapdos voluntarily
entered a revealed Lovely Kiss Nidoking, the public transaction was:

```text
Zapdos is accepting sleep or threatening Sleep Talk/value preservation.
After sleep lands, the next owner is probably Snorlax or another Nidoking
answer; Zapdos should not be treated mainly as active coverage until coverage
or Sleep Talk is public or side-known.
```

Turn 11, read only after stopping, confirmed the route: p1 switched sleeping
Zapdos out to Snorlax while Nidoking used Ice Beam. That continuation is not
part of the frozen score, but it supports the lesson.

## Local Rule Update

Add this to the live role-package check:

```text
Sleep absorber transaction beats coverage read. If a Pokemon enters into a
live Lovely Kiss/Hypnosis/Sleep Powder lane, first decide whether its public
job is to take sleep, stay via revealed Sleep Talk, or leave after Sleep Clause
is active. Hidden coverage is only a strong-prior branch with fallback.
```

## Progress Call

This is not proof that the simplified docs are better or worse. Top-match was
higher than the previous support-ledger packet, but the hidden-info count rose
from 0 to 1 and the repeated absorber/package miss reappeared. Under the
plateau loop, this packet counts as sample item 1 and requires a corrective
next packet before claiming any trend.
