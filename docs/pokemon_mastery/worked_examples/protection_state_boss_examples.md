# Worked Example: Protection State In Boss Fights

Purpose: practice checking whether a move reaches the real target or gets
absorbed by Substitute, Protect, Endure, Focus Band, or a similar survival
branch.

Source basis:

- Smogon's Substitute analysis describes Substitute as protection, scouting,
  Focus Punch support, setup support, and PP pressure.
- `../reviews/2026-05-13_smogtours-gen2ou-917190.md` shows Substitute as a
  possible endgame route that also taxes the user if the defender keeps
  breaking it.
- `../reviews/2026-05-13_smogtours-gen2ou-909431.md` shows Substitute helping
  Starmie and Jolteon create protected actions in a long GSC game.
- Local evidence: `data/moves/moves.asm` defines Substitute, Protect, Detect,
  and Endure; `data/moves/effects_priorities.asm` gives Protect/Endure priority
  3; `data/trainers/parties.asm` includes boss Protect and Focus Band cases.

## Recipe Used

Before choosing a move into possible protection, fill this out:

```text
protection branch:
who owns it:
what it blocks:
what it costs:
what it gains:
best follow-up if it happens:
move that punishes it:
```

If the planned move is still good only when protection is ignored, the plan is
not ready.

## Brock: Protect Plus Leftovers / Spikes Timing

Local evidence:

- Brock Omastar has Protect.
- Brock Aerodactyl has Protect.
- Protect has 10 PP and priority 3 locally.

Bad default:

- "Attack because it is the strongest move."

Why that fails:

- If Omastar uses Protect while Leftovers, Spikes, or a switch clock matters,
  a weak attack may make no route progress. The boss has not merely skipped a
  turn; it may have scouted the player's answer, gained recovery, or burned a
  weather/status/lock turn.

Better policy:

- If the player can use the Protect turn to set up, pivot, recover, deny
  Spikes, or prepare a KO threshold, protection can be punished.
- If the only plan is repeated weak damage into Protect plus recovery, switch
  to a route that forces Omastar to choose between Protect and losing the
  hazard/recovery map.

Answer-changing information:

- Current Leftovers, hazard, poison, weather, and lock-in state.
- Whether the player has a setup or pivot move that exploits Protect.
- Whether Omastar is already in a forced KO range even after Protect.

## Will / Jasmine: Protect Around Toxic And Explosion

Local evidence:

- Will Forretress has Protect, Toxic, Spikes, and Explosion.
- Jasmine Forretress also uses Protect-like timing around hazard and trade
  pressure in the route sheets.

Bad default:

- "Use the one-time trade now because Forretress is the support piece."

Why that fails:

- A plausible Protect branch can make Explosion, status, or a route-specific
  attack miss the real target. Even when Protect does not block every plan, it
  can scout the user's answer and make the next Explosion or Toxic turn easier
  for the boss.

Better policy:

- Spend the one-time trade only when Protect is already unavailable, low-value,
  or the follow-up after Protect is still route-positive.
- Use the Protect turn to move into the correct answer, deny hazards, set up a
  safer threshold, or force Forretress to choose between support and survival.

Answer-changing information:

- Whether Protect was just used and local consecutive-use behavior matters.
- Whether the player has a second trade or pressure route if the first is
  blocked.
- Whether Forretress's Explosion is still required for the boss route.

## Morty / Bruno / Lance: Focus Band Survival Branch

Local evidence:

- Morty Haunter, Bruno Hitmonlee, and Lance Yanma carry Focus Band in local boss
  rosters.

Bad default:

- "This move KOs, so the route is solved."

Why that fails:

- Focus Band can leave the target alive for one more Hypnosis, Focus Punch,
  priority, setup, status, or damage turn. If that extra action removes the
  only answer, the KO line was not guaranteed in route terms.

Better policy:

- If the route cannot tolerate Focus Band, use a line that covers survival:
  priority after damage, residual damage, phazing/Haze, status, a sack that
  creates safe re-entry, or preserving a backup answer.
- If the extra Focus Band turn is survivable and the current move still opens
  the route, take the KO attempt but name the survival follow-up.

Answer-changing information:

- Whether Focus Band has already activated or been removed.
- Whether residual damage or multi-hit mechanics can cover the survival branch.
- Whether the target's one extra move is merely annoying or route-ending.

## Player Substitute: Protection Is Not Free

Expert-transfer evidence:

- Smogon's Substitute article values Substitute because it can block status,
  scout, and protect Focus Punch or setup.
- The GSC reviews show that Substitute is strongest when it creates protected
  route progress and weakest when it only spends HP while the defender breaks it
  cleanly.

Bad default:

- "Use Substitute because it is safe."

Why that fails:

- Substitute costs HP. If the boss can break it while keeping the same route,
  the player may be lowering its own revenge, priority, or hazard thresholds.

Better policy:

- Use Substitute when it blocks a specific status, punishes a switch, protects
  a setup/Focus Punch turn, scouts decisive coverage, or makes the boss spend
  scarce PP.
- Do not use it when the boss's obvious attack breaks it and the HP cost makes
  the user's later job worse.

Answer-changing information:

- Speed order.
- Whether the boss's common hit breaks the Substitute.
- Whether the protected turn creates setup, Focus Punch, status immunity, or
  safe Baton Pass value.

## Extracted Lesson

Protection states change move labels. A KO, status, sleep, Explosion, trap, or
Focus Punch is only as good as its branch into Substitute, Protect, Endure,
Focus Band, and similar survival states. Always name the follow-up after the
block or survival before calling the move safe.
