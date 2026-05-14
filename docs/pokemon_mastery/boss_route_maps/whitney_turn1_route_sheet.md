# Whitney Turn-1 Route Sheet

Status: local boss route map. This is not a final player plan until the user's
team, HP, moves, and items are known.

Local evidence:

- Roster source: `data/trainers/parties.asm`
- Item mechanics: `docs/agent_navigation/gen2_vs_modern_mechanics.md`
- Rollout mechanics: `../romhack_deltas/present_rollout_function_reclassification.md`
- Worked example: `../worked_examples/whitney_miltank_rollout_commitment.md`
- Worked example: `../worked_examples/whitney_clefairy_encore_reflect_trap.md`
- Clefairy Eviolite: Eviolite boosts Defense and Special Defense by 3/2 if the
  species can evolve.
- Miltank Mint Berry: Mint Berry is a one-shot sleep-healing item.
- Milk Drink: heals 50% max HP.

Boss roster:

```text
Lv19 Clefairy @ EVOLITE:
  Moonlight / Thunder Wave / Double Team / Doubleslap

Lv20 Girafarig @ TWISTEDSPOON:
  Psybeam / Headbutt / Shadow Ball / Crunch

Lv21 Miltank @ MINT_BERRY:
  Milk Drink / Body Slam / Rollout / Attract
```

## Boss Routes

Clefairy route:

- Goal: burn turns with Thunder Wave, Double Team, and Moonlight until the
  player loses tempo or accuracy reliability.
- What it punishes: passive openings, setup that does not immediately force
  progress, and leads that cannot stop evasion/recovery.
- Denial idea: pressure it before Double Team stacks, or use a plan that does
  not care about evasion. If using type-effectiveness language, verify the
  romhack chart first.

Girafarig route:

- Goal: punish narrow answers with four-attack coverage and create damage
  before Miltank enters.
- What it punishes: preserving only one special or physical pivot without
  checking which move family is actually dangerous.
- Denial idea: do not expose the only Miltank answer to Girafarig chip unless
  that chip buys a concrete route.

Miltank route:

- Goal: use Body Slam and Attract to disrupt action, heal with Milk Drink, then
  threaten a Rollout lock once the player's answer is statused, low, or unable
  to act.
- What it punishes: spending the healthy Miltank answer on Clefairy/Girafarig
  for low-value chip, relying on a one-shot sleep plan into Mint Berry, or
  letting Rollout begin after paralysis/Attract has already made switching bad.
- Denial idea: preserve at least one healthy Miltank answer, track gender and
  paralysis risk, and do not call Rollout safe or bad without checking current
  HP and whether the first hit changes the route.

## Player Plan Template

Primary route:

- Remove or shut down Clefairy's support route before it stacks evasion, while
  keeping the Miltank answer healthy.

Backup route:

- If Clefairy cripples the opener, pivot to a stable Miltank answer and treat
  Girafarig as a damage-management phase rather than trying to sweep through it.

Best lead profile:

- A lead that either forces Clefairy to heal/switch quickly or creates durable
  progress without being the only answer to Miltank.

Avoid as lead:

- A single irreplaceable Miltank answer if it can be paralyzed, attracted, or
  chipped before Miltank appears.
- A fragile sweeper that needs several setup turns into Thunder Wave or Double
  Team.
- A sleep-only plan that forgets Miltank's Mint Berry.

First-turn question:

```text
Does our lead make immediate route progress before Clefairy can stack support?
```

If yes:

- Attack, status, or set up only if that action forces recovery, disables the
  support route, or creates a clear Miltank endgame.

If no:

- Pivot early rather than donating the first paralysis/evasion turn.

Worst plausible branch:

- Clefairy paralyzes the piece needed to keep Miltank contained or gets evasion
  boosts against it, so Miltank later gets Body Slam / Milk Drink / Rollout
  turns without a healthy answer.

Abandon conditions:

- Our Miltank answer is paralyzed, attracted, or below the HP needed to take the
  first Body Slam/Rollout sequence.
- Clefairy gets multiple Double Team boosts and our line depends on ordinary
  accuracy.
- Girafarig reveals damage that makes the planned Miltank pivot unsafe.
- Type-chart, passive, or item evidence contradicts the assumed matchup.

Snorlax study transfer:

- GSC Snorlax material is useful here only as an anchor lesson: name the boss
  route, preserve the answer, and do not spend that answer for low-value chip.
  Do not assume Miltank is Snorlax; this route map comes from Whitney's actual
  local roster.
