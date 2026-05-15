# Focus Energy Counter Branch Regression 001 - smogtours-gen2ou-935022 - 2026-05-14

Source: `https://replay.pokemonshowdown.com/smogtours-gen2ou-935022`.

Mode: post-oracle regression. This is not a fresh replay score or holdout. It
uses the revealed turn log from `replay_turn_pause_015` to convert a severe
branch-pricing miss into a repeatable drill.

Purpose: test whether the advisor prices revealed Focus Energy, Counter,
Hidden Power, speed/order, and low-HP attacker branches as one route bundle
instead of treating each as isolated trivia.

Local docs checked:

- `docs/pokemon_mastery/active_goal.md`
- `docs/pokemon_mastery/training_cycle.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/source_to_policy_ledger.md`
- `docs/pokemon_mastery/paused_turn_atlas.md`
- `docs/pokemon_mastery/quick_tests/replay_turn_pause_015_support_status_followup_smogtours-gen2ou-935022_2026-05-14.md`
- `docs/pokemon_mastery/boss_route_maps/bruno_turn1_route_sheet.md`

Web sources checked:

- Smogon GSC OU threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon GSC Nidoking forum spotlight:
  `https://www.smogon.com/forums/threads/gsc-nidoking.3681149/`
- Pokemon Showdown Gen 2 move source:
  `https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/mods/gen2/moves.ts`
- Pokemon Showdown ladder help:
  `https://pokemonshowdown.com/pages/ladderhelp`

Source notes:

- Smogon frames GSC Nidoking as a dangerous mixed attacker with Earthquake,
  Electric/Ice/Fire coverage, useful speed, and high offensive pressure. That
  supports treating low-HP Nidoking as still route-relevant when it can move
  first or force a trade.
- Pokemon Showdown's Gen 2 move source implements Focus Energy as a crit-ratio
  modifier and implements Counter with Gen 2 timing/category behavior. The
  replay itself confirms that Hidden Power into Counter was a legal punish in
  this position.
- The Showdown ladder page was checked only for measurement framing: Elo is a
  proxy, not a universal proof of skill.

## Regression Score

Regression cases: 5.

Complete branch bundles in the prior live answer: 0 / 5.

Partial branch bundles in the prior live answer: 2 / 5.

Severe branch miss reproduced: 1 / 5, turn 16.

Mechanics errors after review: 0. The issue was branch pricing and state
compression, not a known mechanics falsehood.

Hidden-information errors after review: 0. Turn 8 Focus Energy was not public
yet, so the standard is to re-solve after reveal, not to demand exact hidden
move prediction before reveal.

## Case 1 - Turn 8, Before Focus Energy Is Public

Public state:

```text
p2 Nidoking is active. p1 Cloyster is asleep at 82% after Leftovers. p1 has
revealed Zapdos and Misdreavus. Nidoking has shown Earthquake. Focus Energy
and Counter are not yet public.
```

Prior live answer: p1 stay/burn sleep; p2 Thunder or Earthquake.

Actual branch: p1 switched Zapdos; p2 used Focus Energy.

Expected regression answer: do not require exact hidden Focus Energy before it
is revealed, but name that Nidoking can use the sleeping Cloyster turn for
route improvement rather than only immediate damage. If a new setup or punish
move appears, the next turn must be fully re-solved.

Grade: fail on re-solve trigger preparation, not a hidden-info error.

## Case 2 - Turn 9, Zapdos Into Revealed Focus Energy Nidoking

Public state:

```text
p1 Zapdos is 69%. p2 Nidoking is healthy and has just revealed Focus Energy.
Zapdos can attack with Hidden Power; Nidoking can attack, preserve, or punish.
```

Prior live answer: p1 Hidden Power; p2 Ice Beam.

Actual branch: Zapdos used Hidden Power; Nidoking used Counter and KOed
Zapdos.

Expected regression answer: if Zapdos attacks, the answer must name Counter as
the worst plausible branch and decide whether Zapdos is expendable. Hidden
Power is not automatically safe into Counter in Gen 2 practice. If Zapdos is
route-defining, switch or pivot must be ranked above an unqualified attack.

Grade: partial. The attacking move matched, but the branch bundle failed.

## Case 3 - Turn 10, Low Focus Energy Nidoking Still Has A Route

Public state:

```text
p2 Nidoking is at 50% after Leftovers and has revealed Focus Energy and
Counter. p1 sends in Nidoking at 100%.
```

Prior live answer: p2 should switch Zapdos.

Actual branch: p2 Nidoking stayed in, used Earthquake, crit, and KOed p1
Nidoking before it moved.

Expected regression answer: low or damaged does not mean spent. Re-score
whether the focused attacker can stay because it moves first, speed ties,
forces a KO range, threatens a crit branch, or makes the opponent's obvious
attack unsafe.

Grade: fail.

## Case 4 - Turn 16, Tyranitar 52% Versus Nidoking 8%

Public state:

```text
Turn 15 showed p2 Nidoking Earthquake taking Tyranitar from 94% to 46%.
After Leftovers, Tyranitar is 52% and p2 Nidoking is 8%. Tyranitar has just
shown Earthquake and nearly KOed Nidoking.
```

Prior live answer: p1 Rock Slide; p2 Earthquake.

Actual branch: Nidoking used Earthquake and KOed Tyranitar before Tyranitar
moved.

Expected regression answer: before clicking any Tyranitar move, ask whether
Earthquake can KO first from 52%. If yes, either preserve Tyranitar, spend it
as a named forced-risk trade, or state why no safer route exists. Treating 8%
Nidoking as harmless was the severe error.

Grade: fail, severe.

## Case 5 - Turns 17-18, Sleeping Cloyster Versus Low Focus Energy Nidoking

Public state:

```text
p1 Cloyster enters at 76% asleep after Spikes and Leftovers. p2 Nidoking is at
14%, then uses Focus Energy again while Cloyster remains asleep. On turn 18,
Cloyster is 82% asleep and Nidoking is 20%.
```

Prior live answer: p1 Surf if wake; p2 Earthquake.

Actual branch: Nidoking used Thunder into Cloyster; Cloyster woke and KOed
with Surf.

Expected regression answer: Cloyster should Surf if it wakes, but Nidoking's
best route is not just Earthquake or crit. Coverage matters: Thunder is the
live damage route into Cloyster. After Focus Energy, price coverage, crit, and
wake timing together.

Grade: partial. p1's move was correct; p2's branch was underpriced.

## Extracted Checklist

When Focus Energy or another crit-stage setup is revealed:

1. Name the current public boost/setup state.
2. Ask whether our active can be KOed before moving.
3. Ask whether our obvious attack triggers Counter, Mirror Coat, Bide, Destiny
   Bond, or another punish.
4. Ask whether Hidden Power or another odd-category move changes retaliation
   legality.
5. Treat low-HP boosted attackers as live until their speed/order, coverage,
   crit range, and forced-trade value are priced.
6. If attacking anyway, name the trade route and the piece being spent.

## Error Classes

- Branch-pricing error: the prior live answer separated Focus Energy, Counter,
  speed/order, and damage range instead of evaluating the combined route.
- State-compression error: turn 16 ignored the prior-turn damage evidence that
  Earthquake could KO Tyranitar before it acted.
- Calibration error: turn 8 should not be scored as "should have known Focus
  Energy," but should be scored as "must re-solve once an unexpected setup move
  is revealed."

## Policy Update

Add a paused-turn atlas prompt for revealed Focus Energy / retaliation branch
pricing. Link it to `STP-036` and `STP-058`.

## Next Rep

Run a fresh, unrelated 8-10 turn Gen 2 replay segment and stop at the first
revealed setup or punishment move. Score only whether the answer re-solves the
route after the reveal.
