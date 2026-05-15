# Counter-Handoff Review 001 - smogtours-gen2ou-907837 - 2026-05-14

Source replay:
`https://replay.pokemonshowdown.com/smogtours-gen2ou-907837`

Parent transfer:
`quick_tests/positive_selection_transfer_002_smogtours-gen2ou-907837_2026-05-14.md`

Mode: targeted expert replay review after reveal. This is not a fresh score.

Selected action:
Review only the repeated counter-handoff turns from the parent transfer and
extract a compact trigger for future fresh recommendations.

## Reviewed Turns

### Turn 2

Board:
p1 Zapdos was at 13% against full p2 Zapdos.

Expert line:
p1 switched Snorlax. p2 switched Forretress.

Lesson:
p2 did not spend the turn hitting a nearly dead active because that active was
unlikely to stay. The route move was to meet the expected Snorlax board with
the Spikes setter.

### Turn 5

Board:
p1 Resting Zapdos faced p2 Snorlax.

Expert line:
p1 switched Forretress. p2 switched Zapdos.

Lesson:
Once the sleeping Zapdos was likely to leave, p2 did not default to Snorlax
progress. Zapdos met the Forretress branch and denied a free support turn.

### Turn 7

Board:
p1 Snorlax at 62% faced p2 Zapdos.

Expert line:
p2 switched Skarmory as p1 used Body Slam.

Lesson:
Zapdos could keep attacking, but p1's likely route was Snorlax pressure.
Skarmory met the route owner directly, turning the turn into containment
instead of trading more Zapdos damage.

### Turns 10-11

Board:
p1 sleeping Zapdos faced p2 Quagsire, then p1 Forretress faced p2 Snorlax.

Expert line:
p1 switched Forretress; p2 switched Snorlax. Then p1 set Spikes; p2 switched
Zapdos.

Lesson:
The line kept asking "what board is next?" Quagsire did not set up into the
expected Forretress handoff, and Snorlax did not stay into the support board.
p2 repeatedly moved the next owner into place.

## Extracted Trigger

Use this when a tempting active move looks safe:

1. Name the opponent's likely next board, not only their current active.
2. Name our owner for that next board.
3. If our owner enters safely and creates progress, choose the counter-handoff.
4. If no owner enters safely, keep active pressure or choose a midground.

Counter-handoff is strongest when:

- the current active is low, asleep, walled, or obviously forced out;
- the opponent's replacement has a known job, such as Snorlax pressure,
  Forretress support, Skarmory containment, spinner entry, or Electric
  immunity;
- the direct attack only affects the Pokemon that is unlikely to stay;
- our handoff creates a route action immediately: Spikes, Spin, phaze, status,
  setup denial, or special pressure.

## Exceptions

- Do not hand off if the current active is the real route piece and staying
  threatens a KO, Rest, setup, or support action that matters more.
- Do not hand off into a possible-only hidden move as if it were revealed.
  State the read and fallback if the handoff depends on unrevealed coverage.
- Do not over-dance when the active move already improves through the expected
  receiver, such as setup into a passive wall or coverage into the absorber.
- Do not ignore Spikes damage: a counter-handoff is fake if the owner cannot
  re-enter or loses its later route job.

## Next Fresh-Replay Check

Before each nontrivial recommendation, write:

`next board owner: [our owner for their likely next board, or none]`

If the owner is not `none`, the top action must either move that owner in,
hit the next board, or explicitly explain why active pressure beats the
counter-handoff.
