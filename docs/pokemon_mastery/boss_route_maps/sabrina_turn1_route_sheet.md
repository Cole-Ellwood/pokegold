# Sabrina Turn-1 Route Sheet

Status: local boss route map. This is not a final player plan until the user's
team, HP, moves, items, and current box options are known.

Local evidence:

- Roster source: `data/trainers/parties.asm`
- Boss Pokemon stats/types: `data/pokemon/base_stats/*.asm`; Sabrina's roster
  here is Psychic-heavy but not one-dimensional because it layers screens,
  sleep, Perish Song, Baton Pass, Choice Specs, paralysis, and recovery.
- Move table: `data/moves/moves.asm` and
  `docs/agent_navigation/hack_mechanics_reference.md`
- Opening policy:
  `docs/pokemon_mastery/romhack_deltas/boss_opening_policy.md` and
  `docs/pokemon_mastery/boss_route_maps/adaptive_lead_audit_2026-05-13.md`
  list Sabrina as adaptive first-three: Mr. Mime / Jynx / Espeon.
- Light Screen / Reflect source: `engine/battle/effect_commands.asm`; local
  screens last five turns and fail if already active on that side.
- Encore source: `engine/battle/move_effects/encore.asm`; local Encore lasts
  3-6 turns and locks the target into its last legal move.
- Lovely Kiss, Perish Song, Baton Pass, Morning Sun, Rest, Thunder Wave,
  Seismic Toss, Psychic, Ice Beam, and elemental punches are listed in
  `docs/agent_navigation/hack_mechanics_reference.md`.
- Morning Sun source:
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`; recovery depends on
  weather and time of day.
- Choice Specs source:
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`; it boosts special
  damage by 1.5x and locks the user to the first chosen move until reset.
- Expert principle sources: Smogon GSC Jynx, GSC Espeon, Baton Pass chain,
  priority, status, and win-condition planning material.

Boss roster:

```text
Lv61 Mr. Mime @ TwistedSpoon:
  Light Screen / Reflect / Encore / Psychic

Lv61 Jynx @ NeverMeltIce:
  Lovely Kiss / Ice Beam / Psychic / Perish Song

Lv62 Espeon @ TwistedSpoon:
  Hidden Power / Psychic / Morning Sun / Baton Pass

Lv67 Alakazam @ Choice Specs:
  Psychic / Ice Punch / ThunderPunch / Fire Punch

Lv63 Hypno @ Leftovers:
  Seismic Toss / Rest / Thunder Wave / Psychic
```

Boss likely openings:

- Sabrina is source-listed as adaptive first-three, not fixed Mr. Mime.
- Plan for Mr. Mime / Jynx / Espeon, with Mr. Mime favored by the current
  weighted opener rule.
- Player-side planning may use this boss roster and opener policy before the
  fight. Sabrina's ordinary boss AI still must not know the player's unrevealed
  team, hidden moves, hidden item, private stats, or current-turn input.

## Boss Routes

Mr. Mime route:

- Goal: turn the opening into a five-turn screen window, then punish passive
  setup, recovery, or status attempts with Encore.
- What it punishes: leading a slow setup or recovery plan that cannot afford to
  be Encored, and assuming Mr. Mime is harmless because it is not the ace.
- Denial idea: decide whether turn 1 must prevent screens, attack through the
  weaker defensive category, or avoid giving Encore a decisive target. If a
  screen goes up, start a five-turn ledger instead of continuing the old damage
  plan blindly.

Jynx route:

- Goal: use Lovely Kiss to buy a tempo turn, force switches with dual STAB
  pressure, and use Perish Song to force an end to passive or setup positions.
- What it punishes: relying on one special answer that cannot absorb sleep,
  and treating Perish Song as flavor rather than a three-turn route clock.
- Denial idea: price Lovely Kiss's hit and miss branches. If sleep lands, name
  the cash-out turn; if Perish Song lands, plan the switch sequence before the
  count reaches zero.

Espeon route:

- Goal: use high Speed, strong Psychic pressure, Morning Sun, Hidden Power
  coverage, and Baton Pass to preserve position or escape a bad response.
- What it punishes: chip-only lines that let Morning Sun erase progress, and
  assuming the current Espeon matchup remains fixed after Baton Pass.
- Denial idea: force a damage threshold, status, or pivot decision that cannot
  be healed away. Treat Baton Pass as a position-preservation move first; only
  assume specific pass value when the current boosted or trapped state proves
  it.

Alakazam route:

- Goal: use Choice Specs plus Psychic / Ice Punch / ThunderPunch / Fire Punch
  to make the player's pivot map collapse, then keep pressure after locking
  into the least-punishable coverage move.
- What it punishes: type-slogan switching, leaving the special answer chipped,
  and failing to exploit the lock once the move is revealed.
- Denial idea: before Alakazam moves, preserve a special sponge or revenge
  route for all four attacks. After it moves, update the lock immediately and
  ask which player piece can turn that lock into progress.

Hypno route:

- Goal: use bulk, Leftovers, Thunder Wave, Seismic Toss, Rest, and Psychic to
  slow the fight and make Sabrina's faster attackers easier to position.
- What it punishes: trying to win a long exchange with shallow chip, and
  letting Thunder Wave disable the only Alakazam or Jynx answer.
- Denial idea: force Rest only when the sleep turns can be converted. If Hypno
  paralyzes the speed-control piece, rebuild the plan around slower sequencing
  instead of assuming the same revenge route still works.

## Player Plan Template

Primary route:

- Sabrina is a support-and-lock fight. The player should deny screen/Encore
  snowballing, avoid losing the sleep or paralysis target that matters most,
  and be ready to exploit Alakazam's Choice Specs lock once revealed.

Backup route:

- If screens, sleep, Perish Song, paralysis, or a Choice lock changes the
  battle, stop treating the fight as "beat Psychic types." Rebuild around the
  active clock: screen turns, sleep turns, perish count, Rest turns, or the
  locked coverage move.

Best lead profile:

- A lead that pressures Mr. Mime without handing Encore a passive move, keeps a
  plan for Jynx's Lovely Kiss, and can make Espeon's recovery/Baton Pass route
  costly. It must not spend the only Alakazam answer before its Choice Specs
  lock is known.

Avoid as lead:

- A setup or recovery lead that Mr. Mime can Encore.
- The only sleep absorber or Jynx answer if Lovely Kiss can remove it from the
  fight.
- A one-pivot special-defense plan that loses to Alakazam's coverage spread.
- A chip-only route that Espeon or Hypno can heal through.

First-turn question:

```text
Which adaptive opener appeared?

Mr. Mime: can we deny screens / Encore without donating a passive lock?

Jynx: can we price Lovely Kiss and Perish Song without losing the Alakazam or
Espeon answer?

Espeon: can we cross a damage/status threshold before Morning Sun or Baton Pass
resets the position?
```

If Mr. Mime sets a screen:

- Count five turns. Decide whether to attack through the other category, deny
  Encore, pivot, status, or wait out the screen without losing route material.

If Mr. Mime uses Encore:

- Check whether the locked move is harmless, useful, or a catastrophe. A locked
  recovery/status/setup move may force an immediate switch even if the active
  matchup looks fine.

If Jynx opens or uses Lovely Kiss:

- Separate decision quality from outcome. A miss may give the player a tempo
  turn; a hit requires a new plan around the sleeping piece's role and whether
  sleep clause is now spent.

If Jynx uses Perish Song:

- Start a perish-count ledger. The question is not only "can we KO Jynx?" It is
  whether the required switch gives Sabrina a free entry to Alakazam, Espeon,
  or Hypno.

If Espeon opens or enters:

- Decide whether damage, status, pivot denial, or preserving the special answer
  matters most before Morning Sun erases chip or Baton Pass exits the bad
  branch.

If Alakazam attacks:

- Record the locked move immediately. Exploit the lock only if the chosen pivot
  is not also the irreplaceable answer to Jynx, Espeon, or Hypno.

Worst plausible branch:

- The player opens with passive setup into Encore or screens, loses the key
  special answer to Lovely Kiss or Thunder Wave, fails to exploit Alakazam's
  Choice Specs lock, and then gets forced through screen turns, Perish Song
  switches, and recovery cycles without a concrete route.

Abandon conditions:

- A screen is active and the current route depends on the blocked damage
  category.
- The current Pokemon is Encored into a move that does not improve a route.
- The planned sleep absorber or Alakazam answer is asleep, paralyzed, or below
  its required threshold.
- Perish Song is active and the next forced switch gives Sabrina the better
  board.
- Alakazam's locked move contradicts the assumed pivot map.
- Morning Sun recovery, type-chart, passive, item, or damage evidence
  contradicts the assumed answer.

Snorlax study transfer:

- Sabrina teaches clock discipline. The GSC transfer is to treat screens,
  sleep, Perish Song, Rest, recovery, and Choice lock as turn clocks that alter
  route value. The right move is the one that uses or denies the active clock,
  not the one with the best type label.
