# Worked Example: Entry Creation Ladder In Boss Fights

Status: constructed boss-facing study example. This is a transfer artifact from
expert pivoting material, not a claim about exact Gym Leader Lab move outcomes.

Purpose: practice the question "how does the answer enter?" A Pokemon that wins
from a clean field may be unusable if every entry route spends the HP, status,
item, or PP it needs to perform the job.

Source basis:

- Smogon "Pivots in SM OU" frames pivots as Pokemon that can switch in and out
  repeatedly to generate momentum and get teammates into play:
  <https://www.smogon.com/articles/pivots-sm-ou>.
- The article's later-generation details are not directly imported into GSC or
  the romhack. The transferable idea is the entry ladder: hard switch, soft
  pivot, forced turn, controlled sack, or shorter route.

## Pattern

```text
Route piece:
  the Pokemon or move class that wins/stabilizes if it enters cleanly

Bad hard-switch branch:
  damage, status, trap, lock, setup, weather, hazards, or item loss that makes
  the route piece stop performing its job

Entry method:
  hard switch / soft pivot / forced turn / controlled sack / shorten route

After entry:
  the immediate route-improving action
```

## Case 1: Blue Gyarados Answer

Boss shape:

```text
Blue can open from Pidgeot / Porygon2 / Gyarados.
Gyarados is a live setup route if its answer is spent early.
```

Bad answer:

```text
"Use the Gyarados answer as the lead because it covers Gyarados."
```

Entry-ladder reading:

```text
Route piece:
  Gyarados answer

Bad hard-switch branch:
  Pidgeot Choice Band chip, Porygon2 recovery/coverage, or Tauros/Arcanine
  follow-up damage may put the answer below the setup-answer threshold

Entry method:
  lead a broader piece if possible, then create forced entry by exploiting
  Pidgeot lock, Porygon2 recovery, a KO, or a controlled sack

After entry:
  deny Dragon Dance or force Gyarados out immediately
```

Lesson:

- If the Gyarados answer is also the safest opener, leading it can be correct.
  If it needs full HP or clean status later, the opening plan should create its
  entry rather than spend it.

## Case 2: Lance Final Dragonite Answer

Boss shape:

```text
Lance pressures with repeated setup waves before final Dragonite.
Earlier threats can chip, paralyze, sleep, or bait the same anti-Dragon piece.
```

Bad answer:

```text
"Switch the Dragonite answer into every Dragon-looking attack."
```

Entry-ladder reading:

```text
Route piece:
  final Dragonite answer

Bad hard-switch branch:
  earlier Steelix, Gyarados, Ampharos, Yanma, or Kingdra pressure may status or
  chip the same answer before final Dragonite appears

Entry method:
  use separate early denial when possible; otherwise create entry on Outrage
  lock, Hyper Beam recharge, phaze/Haze timing, a forced KO, or a controlled
  sack

After entry:
  deny setup immediately; do not spend the entry on generic chip
```

Lesson:

- The answer's value is its future entry, not just its matchup label. If the
  boss has several setup waves, each entry must be budgeted before turn 1.

## Case 3: Misty Starmie Or Lapras Cleanup Answer

Boss shape:

```text
Misty can create rain, sleep, paralysis, Recover loops, and bulky Water
pressure. The answer may be strong only if it avoids rain-boosted or status
damage on entry.
```

Bad answer:

```text
"Hard-switch the Water answer now because it resists the active move."
```

Entry-ladder reading:

```text
Route piece:
  Starmie / Lapras / Quagsire answer

Bad hard-switch branch:
  Hypnosis, Thunder Wave, rain-boosted damage, Recover tempo, or Curse setup
  can make the supposed answer stop answering the later route

Entry method:
  force a Recover turn, enter after Politoed spends rain/sleep tempo, use a
  sleep absorber if it has no later unique job, or sack a spent piece to bring
  the real answer in clean

After entry:
  cross a KO/status threshold or deny the recovery/setup window immediately
```

Lesson:

- A clean entry is often worth more than one extra attack from the wrong
  Pokemon. If the answer only wins from clean entry, the plan should name the
  entry method before recommending the switch.

## Transfer Lesson

When advising a live boss turn, do not stop at:

```text
"X answers Y."
```

Write:

```text
X answers Y only if it enters by method Z.
Hard-switching fails to branch A.
The current move should create entry by B, or choose shorter route C if no
entry exists.
```

This avoids a common planning failure: preserving the correct answer in theory
while never creating the board state where it can safely act.
