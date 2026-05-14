# Worked Example: Boss AI Opponent Model

Status: local boss-facing study example. This is not exact live turn advice
until the user's team, HP, moves, items, bench, and current battle state are
known.

Purpose: practice combining expert prediction discipline with local Boss AI
evidence. The goal is to avoid both errors: treating the AI as a scripted dummy
and over-modeling it like a tournament human.

Source basis:

- `../cookbook.md` recipe: Boss AI Opponent Model.
- `../boss_route_maps/misty_turn1_route_sheet.md`
- `../boss_route_maps/blue_turn1_route_sheet.md`
- `../../agent_navigation/subsystems/boss_ai_trace.md`
- `../../../audit/boss_ai_trace/misty_live.txt`
- `../../../audit/boss_ai_trace/blue_live.txt`
- `../../../engine/battle/ai/POLICY_DESIGN.md`

Verification note:

- On 2026-05-13, `python tools\audit\check_boss_ai_live_capture_ledger.py`
  failed because the manifest expected trace ROM hash
  `ECE0411C1730CD3720D1E0DC05653949ABBA2E8375800FBBA0ED1F7A86F5B040`, while
  the current `pokegold_trace.gbc` hash was
  `E2DC417F17DB330DEF1A39B9EFABCC101A952CC68C8B09DC102F9A8B349C5382`. Treat
  the examples below as historical training priors, not current live proof,
  until the trace manifest is refreshed or the matching ROM is restored.

## Case 1: Misty Opening

Local trace:

```text
artifact: audit/boss_ai_trace/misty_live.txt
chosen: HYPNOSIS
top_moves: HYPNOSIS:20,SURF:20,ICE_BEAM:20
plan_id: 4
plan_confidence: 84
```

Roster route:

```text
Politoed wants rain, Hypnosis, and Water/Ice pressure to start Misty's weather
and recovery game before Starmie, Quagsire, Lapras, or Lanturn appear.
```

Bad advisor shortcut:

```text
Misty will always click Hypnosis, so lead anything that beats Surf/Ice Beam.
```

Why that shortcut is wrong:

```text
The trace is first-decision evidence, not a whole-fight script. It shows
Hypnosis as the captured chosen move in that state, while Surf and Ice Beam are
also top moves. The route map still has to price rain, direct damage, and the
later Starmie/Lapras/Quagsire/Lanturn routes.
```

Better policy:

```text
Lead with a Pokemon that can tolerate or exploit the sleep branch without being
the only later answer to Starmie or Lapras. If the chosen plan needs speed,
also protect it from later Lanturn Thunder Wave rather than spending it into
Politoed just because Hypnosis is likely.
```

What changes the answer:

- A player team with a dedicated sleep absorber makes direct pressure stronger.
- A player team with only one Starmie/Lapras answer should avoid exposing that
  answer to turn-1 sleep.
- Damage proof that Politoed is immediately forced out can make attack better
  than sleep-buffer pivoting.
- Rain on turn 1 requires a weather ledger even if Hypnosis was the trace
  capture.

## Case 2: Blue Opening

Local trace:

```text
artifact: audit/boss_ai_trace/blue_live.txt
chosen: DOUBLE_EDGE
top_moves: DOUBLE_EDGE:20,STEEL_WING:20,QUICK_ATTACK:20
plan_id: 4
plan_confidence: 84
```

Roster route:

```text
Blue's Pidgeot can apply Choice Band pressure and force the player to reveal
which piece handles Normal/Flying/Steel contact damage before Gyarados,
Arcanine, Alakazam, Exeggutor, or Machamp routes appear.
```

Bad advisor shortcut:

```text
Blue will Double-Edge, so switch to the best immediate Normal resist every
time.
```

Why that shortcut is wrong:

```text
The trace supports Double-Edge as an opening prior in the captured state, but
the full fight is not only Pidgeot. The switch-in must still preserve answers
to Dragon Dance Gyarados, Arcanine priority and coverage, Alakazam, Exeggutor,
and Machamp. A perfect turn-1 resist can be wrong if it spends the only later
answer.
```

Better policy:

```text
Use the trace as a likely opening action, then choose the response that keeps
the full answer map intact. If the Normal resist is also the only Gyarados or
Arcanine answer, consider whether a controlled chip trade, pivot, or different
lead keeps more routes covered.
```

What changes the answer:

- If the player has two durable Normal/Flying answers, the safer resist line
  rises.
- If the resist is also the only answer to Blue's later setup route, preserving
  it rises.
- If Pidgeot's locked move can be exploited after the first hit, a controlled
  entry route may be better than immediate damage.
- If local type/passive evidence changes the supposed resist, the entire line
  must be recalculated.

## Extracted Rule

For bosses, prediction is an evidence-weighted prior plus a route map. Use live
traces to avoid fuzzy guesses, but never let a first-decision trace erase the
boss's remaining team, alternate legal moves, or the user's irreplaceable
pieces.
