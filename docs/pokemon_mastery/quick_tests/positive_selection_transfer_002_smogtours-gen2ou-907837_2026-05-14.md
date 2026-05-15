# Positive Selection Transfer 002 - smogtours-gen2ou-907837 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-907837`

Context source:
Smogon, `GSC OU Winter Seasonal #8: Round 2`:
`https://www.smogon.com/forums/threads/gsc-ou-winter-seasonal-8-round-2.3777598/`

Mode: focused fresh replay transfer, spectator-public vanilla GSC. No team
sheet was supplied, no Team Preview was assumed, and actual replay moves are a
weak pro-comparison oracle rather than absolute truth.

Selected action:
Fresh transfer after `positive_selection_correction_probe_001`, testing whether
the correction transferred to unseen play: after naming a branch, choose the
move or handoff that affects that branch.

## Sources Checked

Local docs:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/policy_cards/hidden_role_voluntary_entry.md`
- `docs/pokemon_mastery/quick_tests/positive_selection_correction_probe_001_2026-05-14.md`

Web/current sources:

- Smogon Winter Seasonal #8 Round 2 thread above.
- Pokemon Showdown replay source above.
- Raw log: `https://replay.pokemonshowdown.com/smogtours-gen2ou-907837.log`

## Contamination Control

Local search found no prior `907837` artifact before selection. The raw log was
downloaded to `tmp/pokemon_mastery_replays/`. Future turns were not inspected;
each prompt was generated with `tools/pokemon_mastery/replay_turn_pause.py` and
revealed only after the answer was frozen.

Stopped after turn 11 because the same target error repeated several times:
I missed counter-handoffs into the expected branch, especially p2 using
Forretress, Zapdos, Snorlax, and Zapdos again to meet the board that p1 was
likely to create.

## Score Summary

Turns scored: 1-11.

Scorable side decisions: 22.

Top-match: 10 / 22.

Acceptable-match: 17 / 22.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Positive-selection: 17 / 22.

Route-converting move chosen: 6 / 12 target converter decisions.

Branch-punish chosen: 5 / 11 named-branch decisions.

Earliest meaningful error: turn 2 p2. I chose Thunder to finish or punish the
low Zapdos, but the replay's Forretress switch converted the obvious p1
Snorlax handoff into a Spikes board.

Main bottleneck: the correction transferred for some direct branch checks, but
not for counter-handoff chains. I still overvalue the move that attacks the
current board and undervalue the switch that meets the board the opponent is
about to create.

## Focused Turn Notes

### Turn 2 - Missed Counter-Handoff

Public state:
p1 Zapdos at 13% against p2 full Zapdos.

Frozen p1 answer:
Switch to the special/Electric answer, with Snorlax as the visible class.

Frozen p2 answer:
Thunder to finish Zapdos or punish the switch.

Actual:
p1 switched Snorlax. p2 switched Forretress.

Score:
p1 top and positive. p2 miss: no top, no acceptable, no branch-punish. The
route move was not "hit the thing"; it was "meet the thing that replaces it."

### Turns 3-4 - Support And Preservation

Public state:
p1 Snorlax into p2 Forretress, then low p1 Zapdos into Forretress.

Frozen answer quality:
I hit p2 Spikes on turn 3, but only had p1's Zapdos handoff and Rest as
alternatives rather than top actions. This is acceptable in spectator-public
mode because own-side moves and bench are hidden, but it still shows that Rest
and low-piece preservation must be priced earlier.

Actual:
p1 moved Zapdos into Forretress, p2 set Spikes, then p1 used Rest as p2 moved
Snorlax into Zapdos.

Score:
No severe or hidden-info error. Positive selection was partial: the correct
route was preserving Zapdos and turning the Forretress board into a RestTalk
Zapdos board, not just attacking Forretress.

### Turn 5 - Missed Second Counter-Handoff

Public state:
Resting Zapdos faced Snorlax.

Frozen p1 answer:
Switch to a Snorlax answer or phazer if available.

Frozen p2 answer:
Use Snorlax pressure or setup; Lovely Kiss if the set supports it.

Actual:
p1 switched Forretress. p2 switched Zapdos.

Score:
p1 acceptable by class. p2 miss: the stronger line met the Forretress branch
instead of spending a Snorlax turn into the board that was likely to appear.

### Turns 6-9 - Mixed Transfer

Public state:
Forretress faced Zapdos; then Snorlax faced Zapdos; then sleeping Zapdos faced
Skarmory.

Frozen answer quality:
I correctly used Thunder for p2 on turn 6, Body Slam pressure for p1 on turn 7,
and Sleep Talk as a strong-prior-but-not-fact line on turn 9. I also found the
p2 switch-to-answer class on turn 9.

Actual:
p1 switched Snorlax into Thunder, p1 Body Slammed as p2 went Skarmory, Skarmory
Whirlwinded sleeping Zapdos in, and p2 switched Quagsire into Sleep Talk.

Score:
Good transfer on Sleep Talk tiering: it was treated as a strong prior with a
fallback, then became revealed. Still, turn 7 p2 was another exact
counter-handoff miss: I did not make the Skarmory handoff the top line.

### Turns 10-11 - Repeated Counter-Handoff Miss

Public state:
Sleeping Zapdos faced Quagsire. Then Forretress faced Snorlax.

Frozen answers:
p1 should switch to a Quagsire answer, with Forretress as an acceptable class.
p2 should set up with Quagsire. On the next board, p1 should Rapid Spin with
Forretress while p2 should punish with Snorlax coverage or pressure.

Actual:
p1 switched Forretress. p2 switched Snorlax. Then p1 set Spikes while p2
switched Zapdos.

Score:
p1 mostly acceptable and positive. p2 was the repeated failure: instead of
using the current active's generic progress, the stronger line kept meeting the
next board. This repeated the turn 2 and turn 5 miss, so the transfer stopped.

## Error Classes

- Severe: none.
- Hidden-info: none. Unrevealed own-side moves such as Rest, Sleep Talk, Rapid
  Spin, Fire Blast, or exact bench owners were handled as conditional or
  spectator-public limitations, not as public facts.
- State/mechanics: none found.
- Positive-selection failure: repeated counter-handoff underpricing.

## Transfer Rule

When the opponent's current active is likely to leave or be replaced by a known
role owner, score two boards before choosing:

1. What happens if I hit the current active?
2. What happens if I meet the board they are about to create?

If board 2 is the opponent's best route and my current top move does not affect
it, the top move must usually become a counter-handoff, coverage move, setup,
phaze, or support move that changes board 2.

## Next Rep

Do not make another broad constructed probe. The next useful rep is either:

- a short expert replay review of `907837` turns 2, 5, 7, 10, and 11 focused
  only on counter-handoff triggers; or
- a fresh unseen transfer that forces a written "next board owner" before each
  p2 recommendation.
