# Branch Absorber Transfer 001 - smogtours-gen2ou-912287 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-912287`

Raw log:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-912287.log`

Tournament source:
`https://www.smogon.com/forums/threads/smogon-premier-league-xvii-week-7.3778180/`

Web/current source checked:

- Smogon SPL XVII Week 7 GSC OU replay posts.
- Pokemon Showdown replay log for `smogtours-gen2ou-912287`.

Local docs checked:

- `docs/pokemon_mastery/active_context.md`
- `docs/pokemon_mastery/replay_turn_pause_protocol.md`
- `docs/pokemon_mastery/policy_cards/branch_action_after_naming.md`
- `docs/pokemon_mastery/workspace/quick_tests/branch_absorber_punish_probe_001_2026-05-14.md`

Mode: spectator public. No Team Preview. Hidden teammates and unrevealed moves
were treated as revealed, strong-prior, or possible-only.

Contamination control:

- Local `rg` found no prior `912287` use before selection.
- Replay was selected from current SPL results without keyword screening for
  sleep absorbers, Explosion, Gengar, or Steelix loops.
- Used only the local turn-pause helper before each reveal.
- Scoring uses the first 30 scored side decisions. Later turns were used only
  as extra calibration notes.

Selected action:
Fresh transfer after `branch_absorber_punish_probe_001`, testing whether the
absorber-punish rule survives outside the constructed probe.

## Score

- Scored decisions: 30
- Top match: 10/30
- Acceptable match: 15/30
- Severe blunders: 1
- State errors: 0
- Hidden-info errors: 1
- Mechanics errors: 0
- Positive-selection: 17/30
- Route-converting move chosen: 9/21 applicable
- Branch-punish chosen: 6/18 applicable
- Earliest meaningful error: turn 1

Interpretation:
This was not positive move-selection progress. Severe blunders did not stay at
zero, and the top/acceptable agreement was poor. The important miss was not a
safe-generic move; it was an over-aggressive Explosion line that failed to
price a no-Team-Preview Ghost switch.

## Turn Notes - First 30 Scored Side Decisions

| Turn | Side | Frozen top | Actual | Grade |
| --- | --- | --- | --- | --- |
| 1 | p1 | Lovely Kiss | Psychic | miss; defaulted to sleep instead of punishing likely absorber |
| 1 | p2 | Switch sleep absorber | Zapdos | top by class |
| 2 | p1 | Switch to Electric check | Thief | miss; failed to keep branch-punish pressure with Jynx |
| 2 | p2 | Thunder | Snorlax | miss; missed sleep/item absorber pivot |
| 3 | p1 | Lovely Kiss | Lovely Kiss | top |
| 3 | p2 | Switch sleep absorber | Double-Edge | miss; actual punished the miss |
| 4 | p1 | Lovely Kiss | Cloyster | miss; did not preserve low Jynx |
| 4 | p2 | Double-Edge | Double-Edge | top |
| 5 | p1 | Spikes | Spikes | top |
| 5 | p2 | Switch Cloyster | Zapdos | acceptable pressure switch, not top |
| 6 | p1 | Switch Electric answer | Steelix | top by class |
| 6 | p2 | Thunder | Cloyster | miss; missed counter-pivot |
| 7 | p1 | Switch Cloyster | Jynx | acceptable exit, but less converting than actual |
| 7 | p2 | Spikes | Spikes | top |
| 8 | p1 | Lovely Kiss | Lovely Kiss | top |
| 8 | p2 | Switch Zapdos absorber | Snorlax | acceptable absorber class |
| 9 | p1 | Lovely Kiss | Lovely Kiss | top |
| 10 | p1 | Psychic | Psychic | top |
| 10 | p2 | Switch sleeping Snorlax | Sleep Talk | miss; Sleep Talk was hidden, but switch was overcalled |
| 11 | p1 | Switch Steelix | Gengar | acceptable by role, not top |
| 11 | p2 | Double-Edge | Rest | miss; failed to value RestTalk route reset |
| 12 | p1 | Explosion | Dynamic Punch | miss; over-cashed healthy Gengar |
| 12 | p2 | Sleep Talk | Sleep Talk -> Earthquake | top |
| 13 | p1 | Explosion | Snorlax | severe + hidden-info; line loses to the hidden Gengar switch |
| 13 | p2 | Sleep Talk | Gengar | miss; missed Explosion-block switch |
| 14 | p1 | Earthquake if available | Curse | miss; possible-only coverage was over-weighted |
| 14 | p2 | Hypnosis | Cloyster | miss; missed reset to physical stop |
| 15 | p1 | Switch Gengar | Curse | miss; over-defended Explosion/Toxic |
| 15 | p2 | Explosion | Toxic | acceptable boosted-Lax answer, not top |
| 16 | p1 | Curse | Double-Edge | miss; failed to cash pressure before Toxic clock mattered |

## Main Errors

Turn 1 branch-punish miss:
Jynx faced Cloyster with sleep open, but the actual line used Psychic into the
likely Zapdos sleep absorber. My default Lovely Kiss was too generic. If the
absorber is likely, the first question is not "is sleep available?" but "what
move improves through the absorber?"

Turn 12 over-cash:
Gengar at 94% faced a sleeping RestTalk Snorlax. I wanted Explosion, but the
actual line used Dynamic Punch. The replay preserved Gengar while threatening
confusion and not paying the full cash-out cost.

Turn 13 severe hidden-info error:
After seeing Sleep Talk Earthquake, I kept Explosion as top with low Gengar.
The actual branch was an opposing Gengar switch. In no-Team-Preview GSC, a
hidden Ghost is not revealed, but Explosion still requires a Ghost/immunity
fallback. My line would spend Gengar for no damage on the actual branch.

Turn 16 cash timing miss:
At +2 Snorlax versus Cloyster, I left Curse on top after Toxic had already been
shown. The actual Double-Edge converted the boost immediately and removed
Cloyster. This is a positive-selection miss: the safe continuation was worse
than cashing pressure before the poison clock mattered.

## Extra Calibration From Later Turns

- Turns 18-22 reinforced that Steelix + Spikes can become a phaze-loop route.
  The repeated Roar line was often better than trying to win the active
  matchup immediately.
- Turns 23-25 showed the sleep-clause absorber pattern directly: a sleeping
  RestTalk Snorlax can be switched back into Jynx to blank further sleep value.
  That branch must be priced before choosing another status move.
- Turns 27-30 showed the opposite boundary: Earthquake into Tyranitar was still
  reasonable even though Zapdos could switch in, but once Zapdos was active,
  Roar was the route-converting move.

## Reusable Lesson

Before Explosion or any all-in cash-out in no-Team-Preview GSC:

1. Name revealed immunities.
2. Name the legal hidden immunity class that would blank the move.
3. If that branch is plausible and the cash-out spends an irreplaceable piece,
   prefer pressure, setup, phaze, coverage, or a handoff unless the answer is
   explicitly marked as a high-risk read.

Before repeating sleep/status into a side that already has a sleeping RestTalk
piece:

1. Name the sleeping absorber.
2. Price the switch that preserves sleep clause value.
3. Prefer the move that improves through that absorber unless status still
   changes the route.

Next rep:
Construct one small regression card for `Explosion into hidden/revealed
immunity` plus one fresh transfer focused on "cash-out must name the immunity
owner before becoming top."
