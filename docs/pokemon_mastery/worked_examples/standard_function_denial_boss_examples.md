# Worked Example: Standard-Function Denial In Boss Fights

Status: constructed boss-facing study example. These are not exact live-turn
answers without the user's team, HP, PP, and local damage evidence.

Purpose: practice the stallbreaker transfer lesson. The useful abstraction is
not "use a stallbreaker." It is: identify what the opposing piece is trying to
do for the team, then choose the move that denies that job if raw damage does
not already solve the route.

Expert-source framing:

- Smogon's ORAS stallbreaker article defines the role by preventing defensive
  Pokemon from executing their usual strategy, not merely by hitting harder:
  <https://www.smogon.com/articles/ou-stallbreakers>.
- Smogon's older stallbreaker guide repeatedly uses Taunt, status pressure,
  setup timing, item denial, and recovery denial as ways to make passive
  structures collapse:
  <https://www.smogon.com/smog/issue18/stallbreakers>.

## Case 1: Will Forretress

Public boss shape:

```text
Will opener:
  Forretress with Spikes / Toxic / Protect / Explosion

Will's team jobs from this piece:
  start the three-layer hazard clock;
  poison or scout the answer;
  make Explosion trade hard to punish;
  enable Starmie, Slowbro, Alakazam, Houndoom, or Xatu to inherit a damaged
  board.
```

Wrong abstraction:

```text
Hit Forretress with the strongest attack because Forretress is the lead.
```

Better question:

```text
Which first action stops Forretress from doing its job?
```

Move-class labels:

- Best class when damage evidence supports it: immediate pressure that prevents
  the first layer, makes Explosion unfavorable, or forces Forretress to spend
  its turn defensively.
- Acceptable class: pivot to a piece that can absorb Toxic or punish Protect
  while preserving the later Alakazam / Houndoom / Slowbro answer.
- Catastrophic class: slow hazards, setup, or weak status that lets Forretress
  place layers and still threaten Explosion before the player has a route.

Answer-changing information:

- Whether the user's lead can actually deny a first layer before Forretress
  acts.
- Whether the user's Forretress answer is also the only answer to Will's later
  special routes.
- Whether Explosion timing or Protect scouting has been locally verified for
  the exact state.

## Case 2: Misty Starmie

Public boss shape:

```text
Misty Starmie:
  Recover / Hydro Pump / Psychic / Thunder

Misty's team jobs from this piece:
  outspeed and force damage;
  erase weak progress with Recover;
  create cleanup bands for Lapras, Lanturn, Politoed, or Quagsire;
  punish the player for using a slow answer after rain or paralysis.
```

Wrong abstraction:

```text
Keep chipping Starmie because damage is progress.
```

Better question:

```text
Does this move deny Recover stabilization or only feed it?
```

Move-class labels:

- Best class when possible: cross a KO or forced-recovery threshold, status it
  if legal and useful, or pivot to a route that punishes Recover rather than
  letting Starmie reset the exchange.
- Acceptable class: preserve the Starmie answer if the current active cannot
  cross the threshold and would become the wrong sacrifice.
- Catastrophic class: weak attacks that let Recover reset the same position
  while the user's Starmie answer takes rain, paralysis, or chip elsewhere.

Answer-changing information:

- Exact damage and Speed evidence for the active matchup.
- Whether rain, paralysis, or item state changes the Recover window.
- Whether the user's next piece converts after Starmie spends or skips Recover.

## Case 3: Sabrina Mr. Mime

Public boss shape:

```text
Sabrina opener:
  Mr. Mime with screen support and Encore-style control

Sabrina's team jobs from this piece:
  make the next special attacker harder to punish;
  trap a passive move with Encore;
  turn the opening into safer Jynx, Espeon, Alakazam, or Hypno entries.
```

Wrong abstraction:

```text
Set up or recover first because Mr. Mime is not the final sweeper.
```

Better question:

```text
Can Mr. Mime convert this passive turn into screens, lock, or a better entry?
```

Move-class labels:

- Best class when available: pressure Mr. Mime immediately, deny the support
  turn, or use a move that remains useful if Encore catches it.
- Acceptable class: switch to a piece that does not care about the expected
  support state and still preserves the answer to Sabrina's next route.
- Catastrophic class: setup, recovery, hazards, or low-value status that gives
  Mr. Mime the exact support or lock turn Sabrina wants.

Answer-changing information:

- Whether Mr. Mime's current move order and Encore behavior are verified in the
  local mechanics profile.
- Whether the user's active can punish screens immediately or must preserve a
  later answer.
- Whether the next Sabrina route is Jynx, Espeon, Alakazam, or Hypno from the
  current boss state.

## Transfer Lesson

Do not classify a defensive or support Pokemon only by how hard it is to KO.
Classify it by its standard function in the current team route. A good
stallbreaker-style turn can be direct damage, status, Taunt-like control,
Encore-proof pressure, item denial, trapping, pivoting, or a sacrifice, but the
move is only good if it stops the function that makes the opposing route work.

When advising a boss turn, write this before picking the move:

```text
Opponent piece:
Standard function this turn:
What happens if it performs that function:
Candidate that denies the function:
Candidate that only looks active:
Piece we must preserve while denying it:
Information that would flip the answer:
```
