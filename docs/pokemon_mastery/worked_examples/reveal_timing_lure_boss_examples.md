# Worked Example: Reveal Timing And Lure Resources

Purpose: practice using a hidden move, item, or one-time resource only when it
changes the route map.

Source basis:

- Smogon How To Effectively Surprise Your Opponent:
  https://www.smogon.com/articles/surprise-your-opponent
- Smogon The Concept of Lures:
  https://www.smogon.com/smog/issue1/concept_of_lures
- Smogon Effective Lures in OU:
  https://www.smogon.com/smog/issue37/effective-lures-in-ou

## Pattern

Public state:

```text
Our route:
Route blocker:
Reveal resource:
What happens if revealed now:
What happens if held:
Boss response that punishes reveal:
Boss response that punishes waiting:
Evidence needed:
```

Decision:

```text
Reveal when:
  the blocker is present or forced;
  the reveal removes or cripples that blocker;
  the revealed resource is more valuable now than later;
  and the boss cannot use the reveal turn to start a worse route.
```

Do not reveal because the move is unusual. Reveal because the game state makes
the unusual move useful.

## Bugsy Shape

Boss route:

- Ledian can pass support and Scyther can convert it.

Reveal resource:

- A coverage move, status move, Haze/phaze option, or one-time item that stops
  Ledian support or removes Scyther.

Good reveal:

- Use the resource when Ledian is about to pass a useful state or when Scyther
  is the route blocker. The reveal must either deny the pass or put Scyther in
  a state where Swords Dance / Quick Attack cleanup no longer wins.

Bad reveal:

- Spending the resource on Ariados for generic damage while Ledian and Scyther
  remain live.

Answer-changing information:

- Whether the resource still works through Reflect.
- Whether Ledian can Baton Pass before being removed.
- Whether Scyther survives and converts after the reveal.

## Misty Shape

Boss route:

- Misty rotates weather, sleep, recovery, paralysis, and bulky Water pressure
  until Starmie, Quagsire, Lapras, or Lanturn owns the endgame.

Reveal resource:

- A route-specific move or item that removes the recovery anchor, stops
  Quagsire's setup, or prevents rain from turning Thunder and Water damage into
  the main clock.

Good reveal:

- Use the resource on the Pokemon that blocks the intended endgame. For example,
  if Starmie is the recovery piece that invalidates chip, revealing the answer
  there can be correct. If Quagsire is the Curse/Rest anchor, the same reveal
  may need to be held for Quagsire instead.

Bad reveal:

- Revealing into Politoed only because it is the lead, then losing the route
  because Starmie, Quagsire, or Lapras was the real blocker.

Answer-changing information:

- Rain turns remaining.
- Whether the target can Recover or Rest through the reveal.
- Whether the reveal depends on a type/passive/damage claim that has local
  evidence.

## Karen Shape

Boss route:

- Karen can use Gengar's sleep/hazard pressure, Donphan's spin/phaze control,
  Crobat's disruption, and Tyranitar or Houndoom as converters.

Reveal resource:

- A move or item that removes Tyranitar, Houndoom, or Crobat before it starts
  the route that beats the team.

Good reveal:

- Reveal when the converter or its required support piece is in front and the
  result changes the rest of the fight. Removing Crobat can matter if Safeguard
  or Toxic is what stops the user's status route. Removing Houndoom matters if
  sun would invalidate the intended answer.

Bad reveal:

- Revealing the tech into Gengar or Donphan if the actual route blocker is still
  Tyranitar or Houndoom and the reveal user cannot repeat the job later.

Answer-changing information:

- Whether Crobat has Safeguard active.
- Whether Tyranitar has Dragon Dance.
- Sun turns if Houndoom has already used Sunny Day.
- Whether Donphan can Roar or Rapid Spin away the route after the reveal.

## Transfer Rule

Against human opponents, lures also work by shaping expectations. Against a
fixed boss AI, do not assume expectation management unless the AI behavior is
known. The safe transfer is narrower:

```text
Use the route-specific resource on the route-specific blocker.
Do not spend it on the first target that makes the move look good.
```

If the reveal is one-time, treat it like Explosion or a sacrifice: name the
route opened and the route closed before recommending it.
