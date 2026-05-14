# Worked Example: Red Blastoise Mirror Coat Arbitration

Status: constructed boss-facing turn drill. This is not exact advice until the
user's active Pokemon, HP, moves, items, Speed relation, and damage evidence are
known.

Purpose: convert Red's Blastoise route into a live move-choice recipe. The hard
part is not "avoid special moves." The hard part is deciding whether special
damage KOs or forces a route before Mirror Coat matters, and whether the
Mirror Coat-avoiding line actually improves the fight.

## Source Basis

Expert study anchors:

- Smogon Risk/Reward: compare the likely move with the move that most damages
  the overall strategy.
- Smogon prediction material: prediction needs information and route payoff,
  not fear of every possible punish.
- Smogon long-term planning material: a one-turn hit is useful only if it
  improves the route through the remaining team.
- Smogon Counter/Mirror Coat and Wobbuffet material: the strongest CounterCoat
  cases usually combine category knowledge with trapping, Encore, or forced
  attacks. Red's Blastoise has Mirror Coat, but it does not automatically have
  the same lock.

Local evidence:

- Red route map: `../boss_route_maps/red_turn1_route_sheet.md`.
- Red roster: `data/trainers/parties.asm`, `RedGroup`.
- Blastoise move table:
  `docs/agent_navigation/hack_mechanics_reference.md` and
  `data/moves/moves.asm`.
- Mirror Coat implementation:
  `engine/battle/move_effects/mirror_coat.asm`.
- Mechanics overview:
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`.
- Boss AI tier and public Counter/Mirror Coat policy:
  `data/trainers/ai_tiers.asm`,
  `docs/agent_navigation/subsystems/trainer_boss_roster.md`,
  `docs/boss_ai_spec.md`, and
  `engine/battle/ai/boss_policy_move.asm`.

Local mechanics facts used:

- Red's Blastoise is level 77 with Mystic Water and Earthquake / Surf /
  Blizzard / Mirror Coat.
- Mirror Coat is a fixed-damage Psychic move in the move table, but its effect
  answers the last special-category damaging move.
- The implementation fails if the opponent has not already acted that turn.
  Speed and priority/order therefore matter.
- Mirror Coat does not punish physical damage, status, phazing, Haze, or a
  special hit that KOs Blastoise before it can act. A pivot still has to price
  Surf / Earthquake / Blizzard if Blastoise attacks instead of Mirror Coat.
- Red is a late-tier boss. Local boss AI can encourage Mirror Coat only from
  public conditions: the player has already revealed a special damaging move,
  Blastoise has no KO line, Blastoise is not publicly faster, the player active
  has public threat, and the reflected move can hit the player's visible type.
  This is not current-turn input reading.

## Public State Pattern

```text
Boss active:
  Red Blastoise @ Mystic Water
  Earthquake / Surf / Blizzard / Mirror Coat

Player options:
  strong special attack
  weaker physical attack
  status/control
  pivot
  controlled sacrifice into the real Blastoise answer

Remaining Red routes:
  Espeon screen/setup
  Snorlax Curse / Rest / Sleep Talk
  Venusaur / Charizard sun
  Pikachu ExtremeSpeed if still alive
```

## Candidate Labels

## Expert Transfer Note

Do not import Wobbuffet logic literally. Wobbuffet-style CounterCoat is
threatening because the opponent may be trapped, Encored, choice-locked, or
already committed to an attacking category. Red's Blastoise is different: it
has Mirror Coat plus mixed coverage, but the player may still use physical
damage, status/control, pivoting, sacrifice, or a verified special KO. The
advisor should price Mirror Coat as a public branch, then ask whether avoiding
it lets Surf, Earthquake, Blizzard, Espeon, Snorlax, or sun inherit a better
board.

### Candidate A: strong special attack

Best when:

- public damage evidence says the hit KOs Blastoise before it can move;
- Blastoise is slower and the special hit removes it;
- the special attacker is expendable and trading it to Mirror Coat opens a
  forced route through the remaining Red pieces;
- or every non-special line lets Blastoise, Espeon, Snorlax, or sun convert a
  worse route.

Catastrophic when:

- the hit does not KO;
- the attacker moves before Blastoise;
- Mirror Coat is a legal and severe branch;
- and the special attacker is needed for Espeon, Venusaur, Charizard, or
  another remaining route.

Mirror Coat likelihood rises when:

- the player has already shown a special damaging move with this active;
- Blastoise is not publicly faster;
- Blastoise lacks a direct KO line;
- the player's active threatens Blastoise;
- and Mirror Coat can affect the player's visible type.

Mirror Coat likelihood falls when:

- no relevant special move has been revealed;
- Blastoise has a cleaner coverage KO;
- Blastoise is publicly faster, making Mirror Coat fail on order;
- or a current trace/source artifact says Surf, Earthquake, or Blizzard is the
  stronger route move in this state.

### Candidate B: physical attack

Best or acceptable when:

- it avoids Mirror Coat;
- it crosses a KO, recovery, priority, or safe-entry threshold;
- and the physical attacker survives Surf / Earthquake / Blizzard or is
  expendable after the hit.

Wrong when:

- it is merely weak chip;
- Blastoise attacks and puts the physical attacker or later answer below its
  next-job threshold;
- or Reflect, sun, Snorlax, or Espeon becomes stronger because the player spent
  the turn avoiding a branch that was not actually decisive.

### Candidate C: status/control

Best or acceptable when:

- it disables Blastoise's route, blocks Mirror Coat value, forces a safe entry,
  or prevents Red's next route from inheriting a free turn.

Wrong when:

- it misses the timing and lets Blastoise attack freely;
- it relies on a type/status claim not checked against local mechanics;
- or the control user was the only answer to Red's next converter.

### Candidate D: pivot or controlled sacrifice

Best or acceptable when:

- the special attacker must be preserved;
- the pivot survives Blastoise's attacking coverage;
- or the sacrifice gives clean entry to a piece that forces Blastoise without
  exposing the later Red answer map.

Wrong when:

- the pivot is fake because Surf, Earthquake, Blizzard, hazards, weather, or
  priority removes its future job;
- or the sack is only "momentum" and the next entry does not force progress.

## Live Answer Shape

```text
Recommendation:
  [one move or move class]

Route reason:
  [what Blastoise or later Red route this improves]

Mirror Coat branch:
  [legal / impossible / severe-but-unlikely / tolerable / decisive]

If Blastoise attacks instead:
  [Surf / Earthquake / Blizzard branch and what it damages]

Preserve/spend:
  [which player piece must remain for Espeon, Snorlax, sun, or Blastoise]

Answer-changing information:
  [speed relation, exact damage range, AI trace, HP/item/status, remaining Red
  routes]
```

## Boundary Mutations

Mutation 1: guaranteed special KO

- Blastoise is in verified KO range.
- The special attacker moves first.
- Expected flip: special attack rises because Mirror Coat cannot resolve after
  Blastoise faints.

Mutation 2: non-KO special hit from an irreplaceable attacker

- The special hit deals heavy damage but does not KO.
- The attacker is needed for Espeon or sun.
- Expected flip: special attack falls; physical/control/pivot lines rise.

Mutation 3: physical hit is meaningless

- The physical move avoids Mirror Coat but does not change a threshold.
- Blastoise's Surf / Blizzard / Earthquake damages the only remaining answer.
- Expected flip: avoiding Mirror Coat is not enough; choose a route-changing
  line or accept special risk if safe play loses.

Mutation 4: Mirror Coat severe but not likely

- No relevant special damaging move has been revealed, Blastoise has a coverage
  KO, or a current, state-matched AI trace makes Blastoise's coverage attack
  much more likely than Mirror Coat.
- Expected flip: Mirror Coat remains in the branch list, but it does not
  dominate unless its severity is unacceptable and cheap to cover.

Mutation 5: Blastoise is faster

- Blastoise would move before the player if it selects Mirror Coat.
- Expected flip: Mirror Coat may fail on order, but coverage may still punish.
  The answer must not say "Mirror Coat wins" or "Mirror Coat is irrelevant"
  without checking what Blastoise does if it attacks.

## Extracted Lesson

Retaliation moves turn damage into a route-cost question. The answer is not
"special bad, physical good." The answer is: does the attack remove Blastoise
before Mirror Coat can matter, does avoiding Mirror Coat still make progress,
and which remaining Red route inherits the board after this exchange?
