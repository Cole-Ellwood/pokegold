# Falkner Turn-1 Route Sheet

Status: local boss route map. This is not a final player plan until the user's
team, HP, moves, items, and current box options are known.

Local evidence:

- Roster source: `data/trainers/parties.asm`
- Boss Pokemon stats/types: `data/pokemon/base_stats/*.asm`; Pidgeotto,
  Spearow, and Noctowl are all Normal/Flying locally.
- Move table: `data/moves/moves.asm` and
  `docs/agent_navigation/hack_mechanics_reference.md`
- Sand Attack, Gust, Fury Attack, Peck, Confusion, Hypnosis, and Quick Attack
  are listed in `docs/agent_navigation/hack_mechanics_reference.md`.
- Priority source: `docs/agent_navigation/gen2_vs_modern_mechanics.md` and
  `data/moves/moves.asm`; Quick Attack uses local `EFFECT_PRIORITY_HIT`.
- Sharp Beak and Mint Berry source:
  `docs/agent_navigation/hack_mechanics_reference.md`; Sharp Beak boosts
  Flying damage, and Mint Berry cures sleep once.
- Contact evidence: `data/moves/contact_flags.asm`; Tackle, Fury Attack, Peck,
  and Quick Attack are contact, while Gust, Sand Attack, Confusion, and
  Hypnosis are not.
- Expert principle sources: Smogon lead, sleep, priority, and Flying-type
  offense material.
- Worked probe threshold note:
  `docs/pokemon_mastery/worked_examples/falkner_pidgeotto_geodude_probe.md`

Boss roster:

```text
Lv12 Pidgeotto @ Sharp Beak:
  Tackle / Sand Attack / Gust / Quick Attack

Lv13 Spearow @ Sharp Beak:
  Peck / Fury Attack / no move / no move

Lv14 Noctowl @ Mint Berry:
  Tackle / Peck / Confusion / Hypnosis
```

## Boss Routes

Pidgeotto route:

- Goal: use Sharp Beak Gust and Quick Attack for early damage while Sand Attack
  turns the player's accurate route into a miss-prone one.
- What it punishes: slow setup, low-accuracy moves, and staying in after
  accuracy drops when the current piece is needed later.
- Denial idea: attack or pivot before Sand Attack compounds. If accuracy falls,
  re-score the turn instead of continuing the same plan as if the move still
  had its original reliability.

Spearow route:

- Goal: use Sharp Beak Peck or Fury Attack to keep physical tempo after
  Pidgeotto has chipped or lowered accuracy.
- What it punishes: fragile answers that survive Pidgeotto only to be picked
  off, and ignoring multi-hit variance from Fury Attack.
- Denial idea: because Spearow is frail, direct pressure usually matters more
  than elaborate setup. Preserve HP for Noctowl if the current Pokemon is the
  sleep or special-pressure answer.

Noctowl route:

- Goal: use Hypnosis to buy tempo, Confusion for special pressure and confusion
  chance, and Mint Berry to punish the player's first sleep attempt.
- What it punishes: sleep-first plans that forget Mint Berry, and using the
  only Noctowl answer as the sleep target.
- Denial idea: treat Hypnosis as a 60-accuracy branch, not a guaranteed stop.
  If it hits, rebuild around the sleeping piece's role; if it misses, cash out
  before Noctowl gets another attempt.

## Player Plan Template

Primary route:

- Falkner is an early accuracy-and-sleep discipline fight. The player should
  stop Pidgeotto from converting Sand Attack into free turns, avoid putting the
  wrong piece in Quick Attack range, and keep a Noctowl plan that does not rely
  on one unverified sleep move.

Backup route:

- If Sand Attack lands or Hypnosis hits, abandon the original script. The new
  plan should name whether the player is switching, attacking through reduced
  accuracy, using a guaranteed move, sacrificing a low-value piece, or waiting
  for a safer entry.

Best lead profile:

- A lead that pressures Pidgeotto immediately with reliable damage, does not
  depend on a single low-accuracy move, and is not the only answer to Noctowl's
  Hypnosis / Confusion route.

Avoid as lead:

- A slow setup lead that lets Pidgeotto stack Sand Attack.
- A lead whose first plan is low-accuracy damage.
- The only Noctowl answer if it can be chipped into sleep or Quick Attack
  range.
- A sleep-only plan into Noctowl before accounting for Mint Berry.

First-turn question:

```text
If Pidgeotto uses Sand Attack, Gust, Quick Attack, or Tackle on turn 1, which
Falkner route becomes easier: accuracy snowball, priority cleanup, Spearow
tempo, or Noctowl sleep control?
```

If Pidgeotto uses Sand Attack:

- Accuracy is now a board-state fact. Prefer a reliable KO, pivot, or line that
  still works after a miss; do not keep clicking the old move without
  re-scoring.

If Pidgeotto uses Quick Attack:

- Track priority range for the current and next Pokemon. A faster player
  Pokemon is not automatically safe if the route depends on surviving at low
  HP.

If Spearow enters:

- Decide whether the live risk is immediate Peck damage, Fury Attack variance,
  or preserving the wrong piece for Noctowl. Do not over-invest in setup
  against the fragile middle piece.

If Noctowl enters:

- Price Hypnosis and Mint Berry together. Player sleep can be a wasted turn if
  the berry cures it, while Noctowl's own Hypnosis can disable the intended
  closer.

Worst plausible branch:

- The player lets Pidgeotto lower accuracy, misses through the accuracy drop,
  gets chipped into Quick Attack or Spearow range, then reaches Noctowl with
  the sleep answer already damaged or with a sleep plan invalidated by Mint
  Berry.

Abandon conditions:

- The active Pokemon has lost accuracy and the plan depends on repeated hits.
- The intended cleaner is in Quick Attack range.
- Noctowl is still holding Mint Berry and the player plan depends on sleep.
- Hypnosis has landed on a piece with an irreplaceable role.
- Type-chart, passive, item, contact, or damage evidence contradicts the
  assumed answer.

Snorlax study transfer:

- Falkner is not a Snorlax-style long game, but it still teaches the same
  discipline in miniature: temporary control only matters if it converts. Sand
  Attack and Hypnosis are scary because they buy turns; the answer is to
  identify what Falkner cashes those turns into and deny that conversion.
