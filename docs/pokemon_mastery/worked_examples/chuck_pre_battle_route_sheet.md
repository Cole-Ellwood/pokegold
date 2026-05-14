# Worked Example: Chuck Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Chuck as a free-turn denial,
hazard/phaze, spin, sleep, priority, and attrition fight. This is a
team-agnostic planning artifact, not final turn advice.

Local evidence:

- Roster source: `data/trainers/parties.asm`, `ChuckGroup`.
- Boss route map: `../boss_route_maps/chuck_turn1_route_sheet.md`.
- Spikes / Rapid Spin delta:
  `../romhack_deltas/spikes_and_rapid_spin.md`.
- Focus Punch, Mach Punch priority, Foresight, Focus Band, Mint Berry,
  type-boost items, and local type-chart references:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.

Expert study anchors:

- Smogon Focus Punch material: Focus Punch is a high-payoff move that depends
  on a turn where the user is not damaged first; the strategic question is
  whether the board gives the user that condition.
- Smogon Substitute / SubPunch material: the transferable lesson is not
  Substitute itself, but that protection, switches, sleep, or passive turns can
  manufacture a safe Focus Punch window.
- Smogon Fighting-type material: priority and high-power Fighting attacks
  convert chip into cleanup once the answer has been softened.
- GSC Spikes material: hazards matter when they change switch cost, phazing
  value, answer durability, or endgame ranges.

## Inputs Needed

```text
Mechanics profile:
  romhack_gym_leader_lab

Boss:
  Chuck

Known boss roster:
  Sudowoodo / Hitmontop / Hitmonlee / Umbreon / Poliwrath

Our team:
  unknown

Our lead candidates:
  unknown

Our irreplaceable pieces:
  must include a Poliwrath answer, a Hitmonlee answer, a sleep-risk plan, a way
  to avoid giving Focus Punch free turns, and a hazard/spin plan if the team
  needs repeated switching; exact species unknown

Our one-time resources:
  unknown

Known romhack deltas that matter:
  three-layer Spikes, Rapid Spin clearing all layers, Focus Punch failing when
  the selected user takes nonzero damage before acting, Mach Punch using the
  local priority-hit tier, Foresight lifting only Normal/Fighting into Ghost
  no-effect rows, Focus Band's 1/16 survival branch, Mint Berry healing sleep,
  and Black Belt / Hard Stone / Mystic Water boosting their move types by 1.2x

Missing evidence:
  exact player team, HP, levels, moves, items, groundedness, speed relations,
  damage ranges, passive type states, whether a lead can interrupt Sudowoodo
  before Focus Punch or Spikes matter, whether the Poliwrath answer can absorb
  Hypnosis pressure, and whether Hitmontop's Mach Punch reaches the intended
  cleaner after opening chip
```

## Output Shape

Primary route:

- Deny Chuck's free-turn chain. His team is built to punish turns where the
  player switches, sets slow hazards, uses low-impact status, or tries passive
  setup: Sudowoodo can set Spikes or Roar, multiple users threaten Focus Punch,
  Hitmontop can erase hazards and later clean with Mach Punch, Umbreon can slow
  the game, and Poliwrath can turn Hypnosis into a damage window.

Backup route:

- If Sudowoodo gets Spikes or Hitmontop keeps spin control, shorten the fight.
  Prioritize direct thresholds, sleep management, controlled sacks, and clean
  entries over repeatedly switching through a field Chuck is converting.

Boss route priority:

```text
immediate:
  Sudowoodo Spikes or Focus Punch if the lead is passive.
  Poliwrath Hypnosis if the sleep plan is undefined.
  Hitmonlee Foresight if the plan relies on a Ghost pivot.

accumulating:
  Sudowoodo Roar with Spikes active.
  Hitmontop Rapid Spin if the player's route depends on hazards.
  Umbreon Toxic / Confuse Ray / Moonlight / Pursuit attrition.

endgame:
  Hitmontop Mach Punch cleanup after chip.
  Hitmonlee Focus Band branch if the route requires a guaranteed removal.
  Poliwrath if the answer is asleep, chipped, or forced to absorb coverage.
```

Boss route to deny first:

- Deny the route that creates the first safe Focus Punch or hazard/phaze loop.
  If the lead cannot damage or force Sudowoodo before it converts, the opening
  should preserve the later Poliwrath/Hitmonlee answer while finding a cleaner
  denial line.

Boss route that can be delayed:

- Umbreon can be delayed if the player has a concrete way to force Moonlight
  PP, status it, pressure it, or use it as a safe entry point. It cannot be
  treated as harmless if Toxic plus Confuse Ray makes the team spend turns that
  Chuck's Focus Punch users want.

- Hitmontop can be delayed only when the player's plan does not depend on
  keeping hazards and Mach Punch does not threaten the planned cleaner. If
  either condition is false, Hitmontop is a route piece, not filler.

Best lead profile:

- A lead that can pressure Sudowoodo immediately without being the only
  Poliwrath or Hitmonlee answer. The lead should either interrupt Focus Punch,
  make Spikes/Roar too slow, punish Sudowoodo for opening passively, or create
  a safe handoff into a piece that still covers the later routes.

Avoid as lead:

- A passive setup or status lead that hands Sudowoodo Spikes or Focus Punch.
- A hazard lead if Hitmontop can spin for free and the team has no punish.
- The only sleep absorber if early chip makes Poliwrath decisive later.
- The only cleaner if Mach Punch range can be reached before Hitmontop is
  handled.
- A Ghost pivot whose plan has not accounted for Foresight state and local type
  evidence.

First move plan:

- Give turn 1 one job: deny the highest-value free turn. A small damaging move
  that interrupts Focus Punch or pressures Sudowoodo's hazard turn can be
  stronger than a larger-looking setup, status, or hazard move that lets Chuck
  choose the pace.

First 3 turns as intentions, not a script:

```text
Turn 1:
  Price Sudowoodo's Spikes, Roar, Rock Slide, and Focus Punch branches against
  the lead's later role.

Turn 2:
  If Spikes landed, rebuild around grounded switch cost and Roar risk. If
  Sudowoodo was denied, prepare for Hitmontop spin/priority, Hitmonlee
  Foresight/Focus Band, Umbreon attrition, or Poliwrath sleep.

Turn 3:
  Start the ledger: Spikes layers, Hitmontop spin access, Focus Punch users
  that can be interrupted, sleep clause and sleeping roles, Focus Band branch,
  and whether Mach Punch ranges now matter.
```

Piece to preserve:

- The Poliwrath answer by default. It must account for Hypnosis, Surf, Ice
  Punch, and Focus Punch from the actual board, not from a type slogan.

- The Hitmonlee answer if it is separate. Foresight and Focus Band mean the
  plan needs a backup branch when a single pivot or single KO does not end the
  route.

- The intended cleaner if Hitmontop is alive and Mach Punch range is near.

Piece that can be spent:

- A lead that already denied Sudowoodo and has no unique job against Poliwrath,
  Hitmonlee, Hitmontop, or Umbreon.

- A chipped status absorber only after sleep risk has been resolved or the
  team has another safe way to handle Poliwrath's next entry.

Worst plausible branch:

- The player spends early turns on passive setup or hazards, Sudowoodo creates
  Spikes and Roar pressure, Hitmontop erases the player's hazard progress,
  Umbreon forces status/confusion switches, and Poliwrath or Hitmonlee converts
  the damaged answer map with sleep, Focus Punch, Focus Band variance, or Mach
  Punch cleanup.

Abandon conditions:

- Focus Punch is getting free turns because the player keeps switching, using
  slow utility, or attacking with moves that do not act before the punch.
- Sudowoodo has Spikes plus a Roar loop and the player cannot remove, punish,
  or shorten through it.
- Hitmontop can remove the player's hazards without giving up a route.
- The intended Poliwrath answer is asleep, below its threshold, or no longer
  safe against revealed coverage.
- Umbreon turns the middle game into Toxic / Confuse Ray / Moonlight / Pursuit
  attrition that the player is not winning.
- Foresight, Focus Band, type evidence, passive evidence, item evidence, or
  damage evidence contradicts the assumed answer.

What information would flip the lead or first move:

- Damage evidence showing the lead can interrupt or remove Sudowoodo before
  Spikes or Focus Punch matter.
- Whether the player has a separate Poliwrath answer that can absorb sleep
  risk without losing the Hitmonlee route.
- Whether Hitmontop's Mach Punch reaches the intended cleaner after one Spikes
  entry, Rock Slide, or status turn.
- Whether the player's hazard plan still wins if Hitmontop spins once.
- Whether Umbreon gives the player a free breaker entry or instead forces the
  player into a losing attrition loop.
- Whether a Ghost-based pivot remains valid after Foresight and the local type
  chart are applied.

## Extracted Lesson

Chuck is not solved by "bring the right type into Fighting." Chuck is a
free-turn denial fight. The player must stop the boss from manufacturing the
turns that Focus Punch, Spikes/Roar, Hypnosis, spin control, priority cleanup,
and Umbreon attrition need. The best opening is the one that denies that chain
while preserving the actual Poliwrath and Hitmonlee answers.
