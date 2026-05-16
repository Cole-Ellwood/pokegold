# Side-Known Transfer 002 - smogtours-gen2ou-924543 p1 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-924543`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-924543.log`

Mode: one-side side-known reconstructed, p1 only, turns 1-8. Opponent
information stayed spectator-public. Turn 1 was unscored because Cloyster
Exploded before p1's move was logged; turn 4 was unscored because Lovely Kiss
put p1 Snorlax to sleep before its chosen move was logged.

Contamination control:
- Local `rg docs` found no prior `smogtours-gen2ou-924543` reference before
  selection.
- Only p1 was advised; no p2 side-known advice was produced.
- The helper supplied p1's own eventually shown roster/moves only. Exeggutor
  and Marowak had no shown moves, so exact own-move knowledge remained partial.

Post-score sources:
- Smogon Forums, [GSC OU Snorlax](https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/).
- Smogon, [GSC OU Sample Teams Breakdown](https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/).

## Score Summary

Decisions: 6 scored p1 decisions.

Top-match: 1/6.

Acceptable-match: 5/6.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 4/6.

Route-converting move chosen: 3/6.

Branch-punish chosen: 2/6.

Role-package update obeyed: 3/6.

Earliest meaningful error: turn 2, choosing Zapdos Thunder Wave rather than the
Golem handoff into revealed Snorlax pressure.

Verdict: failed early-stop packet. Side-known mode reduced hidden-own-move
noise, but it did not fix move choice. The repeated miss was RestTalk action
autopilot: I chose Sleep Talk while the player preserved the sleeping Snorlax
and used Golem to absorb revealed Double-Edge.

## Turn Notes

- Turn 1: p1 Exeggutor vs p2 Cloyster. I expected a sleep/status route, but p2
  Explosion KOed Exeggutor before p1's move logged. Unscored for p1.
- Turn 2: p1 Zapdos vs p2 Snorlax. I chose Thunder Wave; p1 switched Golem into
  Double-Edge. Miss, acceptable. I underweighted the Normal-resist handoff.
- Turn 3: p1 Golem vs p2 Snorlax with Double-Edge revealed. I chose Roar; p1
  switched Snorlax into Earthquake. Miss, not acceptable. I failed to price the
  Earthquake branch into Golem.
- Turn 4: p1 Snorlax vs p2 Snorlax. I chose Double-Edge; p2 Lovely Kiss slept
  p1 before its action logged. Unscored for p1.
- Turn 5: sleeping p1 Snorlax vs p2 Snorlax. I chose Sleep Talk; p1 switched
  Golem into Double-Edge. Miss, acceptable but route-shallow.
- Turn 6: p1 Golem vs p2 Snorlax. I chose Explosion; p1 used Roar after taking
  Earthquake, dragging Zapdos. Miss, acceptable but premature cash-out.
- Turn 7: p1 Golem vs p2 Zapdos. I chose sleeping Snorlax as the absorber; p1
  switched Snorlax while p2 switched Snorlax. Top.
- Turn 8: sleeping p1 Snorlax vs p2 Snorlax. I again chose Sleep Talk; p1 again
  switched Golem into Double-Edge. Miss, acceptable but repeated error.

## Post-Score Study

This is no longer mainly an information-tier problem. The side-known prompt
made p1's own Snorlax Sleep Talk public, but real play still chose the handoff.
The relevant question is not "can the sleeping Snorlax act?" It is "should the
sleeping Snorlax spend sleep turns now, or should another route piece absorb
the revealed attack and preserve it?"

Current Snorlax sources support why this matters. Snorlax's Double-Edge plus
Earthquake package pressures both Zapdos/opposing Snorlax and Rock/Steel/Ghost
answers, and teams commonly need multiple Snorlax checks because one answer
does not cover every set. Here Golem could absorb Double-Edge but had to fear
Earthquake, so the correct loop was a staged owner map:

1. If Double-Edge is likely, Golem absorbs and preserves sleeping Snorlax.
2. If Earthquake is likely, Snorlax or another owner preserves Golem.
3. If Golem is in and the Earthquake branch is live, Roar can preserve tempo
   before Explosion, but Explosion is not automatic.

## Structure Patch

Updated `heuristic_core/role_package_ledger.md`:

```text
Sleeping RestTalk can act, but Sleep Talk is not automatic. First ask whether a
different owner can absorb the revealed attack and preserve the sleeping piece.
```

## Next Rep

Stop side-known replay volume until this RestTalk/absorber staging rule is
checked. The next packet should be a focused side-known replay or tiny
regression check where a sleeping RestTalk user, a Normal resist, and a
coverage branch must be ranked together.
