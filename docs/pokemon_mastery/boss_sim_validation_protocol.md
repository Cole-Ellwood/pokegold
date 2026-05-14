# Boss Simulation Validation Protocol

Status: later-stage proof gate. This is not the main curriculum.

Purpose: test whether study is producing better Gym Leader Lab advice by
running real boss fights against the romhack AI or another non-self opponent
model. The target is not to prove mastery by a single win streak; it is to
stress route planning, turn-by-turn adaptation, and romhack-specific mechanics.

Source basis:

- Smogon's Getting Started guide frames the start of battle as matchup reading:
  identify both sides' threats, form a plan, choose a lead, and avoid giving the
  opponent a free setup route.
- Smogon's long-term thinking and risk/reward material both treat strong play
  as repeatedly checking whether the battle is developing toward the plan.
- Local route maps in `boss_route_maps/` define the boss-specific problems that
  the validation set must cover.

## When This Gate Counts

Only count a boss-sim run when:

1. The mechanics profile is declared.
2. The player team, levels, items, moves, and ruleset are declared.
3. The opponent controller is not the same policy being evaluated.
4. The relevant romhack mechanics are trusted enough for the fight family:
   type chart, passives, Spikes, Rapid Spin, sleep, Rest, damage, items, and AI
   behavior where they affect the plan.
5. The policy writes a pre-battle route plan before turn 1.
6. Each battle logs at least the chosen move, current route, opponent route,
   irreplaceable piece, and abandon condition when the plan changes.

Do not count a run if the simulator is known to disagree with source or emulator
evidence on a mechanic that matters to that fight.

## Test Set Shape

Use at least 50 battles for a declared player team.

The set should be stratified by fight family, not padded with the easiest boss:

```text
support chain into converter:
hazard / spin / phaze war:
weather or field-clock ownership:
sleep and temporary-control discipline:
Explosion or sacrifice route trade:
choice lock, priority, or revenge range:
bulky recovery or anchor answer map:
multi-wave full-route exam:
```

Use `boss_route_maps/README.md` as the coverage index. A good validation set
should include early bosses, late gyms, Elite Four, Lance, and Red rather than
only fights that match one comfortable recipe.

## Minimum 50-Battle Matrix

Use this as the default proof set once the simulator is trusted. The exact
player team can change by run, but the run must declare one player team,
ruleset, and mechanics profile before the first battle.

```text
Early fixed-lead gyms: 6 battles
  Falkner x2
  Bugsy x2
  Whitney x2

Midgame control gyms: 8 battles
  Morty x2
  Chuck x2
  Jasmine x2
  Pryce x2

Late adaptive gyms: 12 battles
  Clair x2
  Brock x2
  Misty x2
  Lt. Surge x2
  Erika x2
  Janine x2

Late-route stress gyms: 6 battles
  Sabrina x2
  Blaine x2
  Blue x2

Elite Four: 12 battles
  Will x2
  Koga x2
  Bruno x2
  Karen x2
  Lance x4

Final full-route exam: 6 battles
  Red x6
```

This matrix totals 50 battles and covers every current boss route sheet at
least twice, with extra weight on Lance and Red because they test serial route
planning more than a single opening matchup.

The declared run passes the numeric gate only at 40+ wins out of 50, but the
number alone is not enough. It also needs:

- at least one battle from every route family in `boss_route_maps/README.md`;
- no known simulator mismatch in the mechanics that decided a recorded win;
- every loss reviewed for earliest meaningful error;
- every lucky win reviewed for decision quality;
- at least one missed/crit/status/item-variance branch logged and handled
  without script-following;
- no repeated catastrophic error from an already documented recipe.

Do not expand the matrix by adding more easy repeats before the first 50 are
complete. If the player team cannot realistically beat a boss family, record
that as a team-route problem rather than hiding it in aggregate win rate.

## Battle Record Shape

```text
Run id:
Simulator / emulator build:
Mechanics profile:
Player team:
Boss:
Boss route family:
Pre-battle primary route:
Pre-battle backup route:
Chosen lead:
Turn-1 job:
Result:
Main reason for result:
Earliest meaningful error, if any:
Simulator or mechanics mismatch, if any:
Notebook recipe confirmed / revised:
```

## Passing Target

The working target is at least 80% wins across 50+ battles for the declared
team and ruleset.

That number is only useful with quality checks:

- Losses must be reviewed for decision error, unavoidable variance, bad team
  matchup, simulator mismatch, or missing local mechanic.
- Lucky wins still need decision review. A bad plan that wins because the boss
  chose poorly is not evidence of strong play.
- Repeated wins against one route family do not prove coverage of another
  family.
- A policy that wins by memorizing fixed boss scripts has not learned enough
  unless it also handles mutations: misses, crits, status, unexpected damage,
  alternate leads, and changed player teams.

## Failure Review

For every loss or lucky win, extract one of these:

- a notebook recipe update;
- a boss route-map correction;
- a mechanics verification task;
- a constructed scenario for branch practice;
- a simulator mismatch report.

The important question after a failed run is not "which final turn lost?" It is
"which earlier decision reduced the live winning routes, and was that avoidable
from public information?"

## Current Status

This gate is not passed. It is a future validation target after more expert
study, more battle review, and enough local mechanics confidence to trust the
simulation results.
