# Side-Known Transfer 001 - smogtours-gen2ou-924896 p1 - 2026-05-15

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-924896`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-924896.log`

Mode: one-side side-known reconstructed, p1 only, turns 1-16. Opponent
information stayed spectator-public. Turns 11 and 12 were unscored because
full paralysis hid p1's chosen move.

Command shape:

```text
python tools/pokemon_mastery/replay_turn_pause.py tmp/pokemon_mastery_replays/smogtours-gen2ou-924896.log side-prompt --turn N --side p1
```

Contamination control:
- Local `rg` found no prior `smogtours-gen2ou-924896` references before
  download.
- Only p1 was advised. I did not produce p2 side-known advice after seeing p1's
  reconstructed roster.
- The helper revealed p1's own eventual shown moves only; unused own moves may
  still be missing.

Post-score sources:
- Smogon, [GSC OU Sample Teams Breakdown](https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/).
- Smogon Forums, [Scizor OU Revamp](https://www.smogon.com/forums/threads/scizor-ou-revamp.3510707/).

## Score Summary

Decisions: 14 scored p1 decisions.

Top-match: 8/14.

Acceptable-match: 14/14.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 13/14.

Route-converting move chosen: 12/14.

Branch-punish chosen: 10/13.

Role-package update obeyed: 12/14.

Earliest meaningful error: turn 1, not recognizing that the side-known team was
an immediate Scizor/Espeon/Porygon2 pass route rather than a Dragonite Thunder
lead route.

Verdict: limited positive transfer, not proof. Side-known mode removed the
hidden-own-move noise and improved exact top versus the failed
spectator-public checks, but the sample is small and from an unusual Baton Pass
team.

## Turn Notes

- Turn 1: I chose Dragonite Thunder; p1 switched Scizor as p2 switched Hypno.
  Miss, acceptable. The pass route should have been first.
- Turn 2: I chose Scizor Agility; p1 used Curse as p2 switched Charizard. Miss,
  acceptable. Scizor's current package was physical boost first.
- Turn 3: I chose Dragonite into Charizard; p1 switched Dragonite as p2 went
  Lapras. Top.
- Turn 4: I chose Porygon2 into Lapras; p1 chose Scizor. Miss, acceptable. The
  team wanted the passer back in, not the generic bulky owner.
- Turn 5: I chose Agility with Scizor; p1 used Agility as p2 switched
  Charizard. Top.
- Turn 6: I chose Baton Pass to Dragonite; p1 Baton Passed to Espeon as p2
  switched Lapras. Move class correct, recipient miss.
- Turn 7: I chose Growth with passed Espeon; p1 used Growth as p2 switched
  Hypno. Top.
- Turn 8: I chose Baton Pass to Typhlosion; p1 passed to Porygon2 and absorbed
  Thunder Wave. Move class correct, recipient miss.
- Turn 9: I chose Curse with Porygon2; p1 used Curse as p2 switched Porygon2.
  Top.
- Turn 10: I chose another Curse; p1 used Double-Edge before the mirror got out
  of hand. Miss, acceptable; attack was the better tempo converter.
- Turns 11-12: p1 full paralysis; unscored.
- Turn 13: I chose Curse to keep up after p2 reached +3; p1 used Curse. Top.
- Turn 14: I chose Recover at 53%; p1 used Recover after taking Double-Edge.
  Top.
- Turn 15: I chose Recover again; p1 used Recover as p2 Cursed. Top.
- Turn 16: I chose Curse from full to keep pace with +4 Porygon2; p1 used
  Curse. Top.

## Post-Score Study

The side-known mode changed the shape of the errors. Instead of guessing
whether own Earthquake, Explosion, or hidden teammates existed, the miss was
mostly recipient selection inside a known Baton Pass route. Smogon sample-team
material describes GSC Baton Pass as dangerous but inconsistent because phazing
disrupts chains; Scizor's niche is passing boosts, not sweeping by itself.
That matches the turn sequence: Scizor's job was to create a boost transaction,
then choose the recipient that survives the current answer.

Reusable rule:

```text
On side-known pass teams, rank the pass recipient, not just the Baton Pass
button. The recipient must beat the active answer and the likely phazer/status
branch.
```

## Helper Patch

This packet exposed that the local helper did not carry Baton Pass boosts into
the next prompt. `tools/pokemon_mastery/replay_turn_pause.py` now carries
boosts and tracked decision-relevant volatiles on `[from] Baton Pass` switches,
with a regression test.

## Next Rep

Replicate side-known mode on a more standard team. Target 12-18 one-side
decisions, and score exact move plus recipient when the action is a switch or
Baton Pass.
