# Worked Example: Morty Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Morty as a sleep, Curse,
confusion, Pain Split, Focus Band, and Destiny Bond fight. This is a
team-agnostic planning artifact, not final turn advice.

Local evidence:

- Roster source: `data/trainers/parties.asm`, `MortyGroup`.
- Boss route map: `../boss_route_maps/morty_turn1_route_sheet.md`.
- Type chart, sleep clause, Focus Band, Spell Tag, damage formula, and Ghost
  / Dark / Psychic chart deltas:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.
- Haunter and Gengar local typing:
  `data/pokemon/base_stats/haunter.asm` and
  `data/pokemon/base_stats/gengar.asm`.
- Misdreavus local typing: `data/pokemon/base_stats/misdreavus.asm`.
- Ghost Curse source: `engine/battle/move_effects/curse.asm`.
- Destiny Bond source: `engine/battle/move_effects/destiny_bond.asm`,
  `engine/battle/core.asm`, and `engine/battle/effect_commands.asm`.
- Pain Split source: `engine/battle/move_effects/pain_split.asm`.
- Dream Eater and sleep source: `engine/battle/effect_commands.asm`.
- Move data: `data/moves/moves.asm`.

Expert study anchors:

- GSC status material: sleep is temporary control, and confusion, Ghost Curse,
  Perish Song, Attract, Encore, and Leech Seed are pseudo-status effects that
  can stack but are cleared differently from primary status.
- GSC Misdreavus material: Ghost disruption works by denying normal routes,
  forcing clocks, and creating awkward trade decisions; Pain Split is useful
  but can be played around.
- GSC Gengar / Ghost material: Hypnosis and Destiny Bond-style moves are
  high-swing tools whose value depends on the target and the resulting route,
  not only on whether the move lands.
- Risk/reward and long-term thinking material: before taking an obvious KO,
  compare the immediate reward with the worst plausible trade and the future
  route it opens.

## Inputs Needed

```text
Mechanics profile:
  romhack_gym_leader_lab

Boss:
  Morty

Known boss roster:
  Haunter / Misdreavus / Gengar / Haunter

Our team:
  unknown

Our lead candidates:
  unknown

Our irreplaceable pieces:
  must include one awake Ghost-route answer, a plan for Gengar that does not
  auto-lose to Destiny Bond, a way to stop Misdreavus from owning the
  Toxic/Pain Split/confusion clock, and a second status plan for Focus Band
  Haunter; exact species unknown

Our one-time resources:
  unknown

Known romhack deltas that matter:
  local Sleep Clause, Haunter and Gengar as Ghost/Psychic, Misdreavus as
  Ghost/Ghost, Ghost attacks hitting Psychic for 2x and Fighting for 2x in this
  hack, Dark hitting Ghost for 2x but Steel only neutrally, Ground hitting
  Ghost for 0x, Foresight not lifting the new Ground -> Ghost immunity,
  Hypnosis at 60% accuracy, Dream Eater requiring a sleeping target, Ghost
  Curse removing half the user's max HP and cursing the opponent, Focus Band's
  1/16 survival chance, Spell Tag as a 1.2x Ghost boost item, Shadow Ball as
  physical, and Destiny Bond removing the attacker if it KOs the bonded target

Missing evidence:
  exact player team, HP, levels, moves, items, sleep-clause state, speed
  relations, damage ranges, whether a planned Ghost answer is also the Gengar
  answer, whether the intended KO move triggers Destiny Bond, whether Focus
  Band changes a forced line, and whether local type/passive evidence supports
  each claimed safe switch
```

## Output Shape

Primary route:

- Keep at least one awake, healthy answer to Gengar while preventing Morty's
  temporary control from cashing out. Opening Haunter wants Hypnosis into Dream
  Eater, Curse, or Night Shade; Misdreavus wants confusion/Toxic/Pain Split
  clock ownership; Gengar wants coverage pressure into Destiny Bond; late
  Focus Band Haunter gives Morty a second sleep/confusion swing.

Backup route:

- If the primary answer is slept, cursed, poisoned, confused, or dragged into a
  Pain Split loop, stop trying to sweep through the same script. Pivot to a
  safer clock or sacrifice only if it preserves the Gengar answer and keeps a
  second Haunter plan live.

Boss route priority:

```text
immediate:
  Hypnosis if it hits the only Ghost-route answer; Dream Eater if a sleeping
  target stays in; Gengar Destiny Bond if the obvious move is a KO.

accumulating:
  Ghost Curse damage, Toxic plus Confuse Ray, Pain Split reducing a high-HP
  answer, and Focus Band turning a planned one-hit removal into another control
  turn.

endgame:
  Gengar or the second Haunter wins after the player has spent the awake answer
  on the first Haunter or let Misdreavus chip it below the needed range.
```

Boss route to deny first:

- Deny whichever temporary-control branch attacks the future Gengar answer. If
  the lead can absorb sleep without losing that role, punish Haunter. If sleep
  would remove the only Gengar answer, pivot or status-control first rather
  than gambling the whole fight on Hypnosis missing.

Boss route that can be delayed:

- Misdreavus can be delayed only if its Toxic / Confuse Ray / Pain Split loop
  does not damage the future answer map. It is not urgent because it is
  immediately lethal; it is urgent when the current exchange lets it turn a
  healthy answer into a Destiny Bond target or Focus Band liability.

Best lead:

- A lead that can pressure opening Haunter or absorb one sleep/control attempt
  without being the only Gengar answer. A Dark, Normal, or Ground idea must be
  checked against local typing, move categories, and the hack chart before
  being trusted.

Avoid as lead:

- The only Gengar answer if Hypnosis, Ghost Curse, or Focus Band variance can
  remove its later role.
- A slow setup lead that gives Haunter a free Hypnosis or Curse turn.
- A high-HP wall that lets Misdreavus use Pain Split as recovery and clock
  control.
- A KO-only lead that has no plan when Gengar is in Destiny Bond range.

First move plan:

- Use the first move to force Haunter, break the sleep route, or pivot before
  the wrong piece is disabled. If attacking is chosen, name the punishment for
  both Hypnosis hit and miss branches. If switching is chosen, name what the
  switch preserves for Gengar.

First 3 turns as intentions, not a script:

1. Price opening Haunter's Hypnosis, Dream Eater, Curse, and Night Shade
   branches before deciding whether to attack or pivot.
2. If sleep, Curse, confusion, Toxic, or Pain Split changes the board, rebuild
   from the new state instead of continuing the original route.
3. Before any Gengar KO, check Destiny Bond state, incentive, speed, and
   whether a non-KO move, pivot, or low-value sacrifice keeps the route cleaner.

Piece to preserve:

- The Gengar answer. It must survive not only Shadow Ball / Thunderbolt /
  Psychic, but also the trade logic around Destiny Bond.
- The second status-control piece for the late Focus Band Haunter if the first
  answer has already been slept or cursed.

Piece that can be spent:

- A sleeping or cursed Pokemon can be spent only if Dream Eater, Curse damage,
  and the remaining Morty roster mean its role is gone and the sacrifice gives
  clean entry without exposing the Gengar answer to Destiny Bond.
- A low-HP Pokemon is a useful Destiny Bond buffer only if it cannot still
  perform an irreplaceable role against Misdreavus or the second Haunter.

Worst plausible branch:

- Opening Haunter sleeps or curses the future Gengar answer, Misdreavus turns
  the backup into a Toxic / confusion / Pain Split clock, Gengar trades the
  remaining attacker with Destiny Bond, and Focus Band Haunter gets one more
  Hypnosis or confusion turn after surviving a planned KO.

Abandon conditions:

- Sleep Clause state changes, or Hypnosis lands on the wrong piece.
- Dream Eater is live against a sleeping active Pokemon.
- Ghost Curse is active on a piece still needed for Gengar.
- Misdreavus's Pain Split makes the high-HP answer no longer durable.
- Gengar is low enough that the obvious KO runs into Destiny Bond.
- Focus Band keeps late Haunter alive and gives it another action.
- A local type, passive, item, or damage fact contradicts the planned answer.

What information would flip the lead or first move:

- Whether the lead can tolerate sleep without losing the Gengar role.
- Whether the player has a sleep absorber, sleep cure, or Sleep Clause already
  occupied.
- Whether the lead's attack KOs Haunter through MiracleBerry / Focus Band
  cases, or merely gives it a control turn.
- Whether the team has a non-KO move that beats Destiny Bond timing.
- Whether Misdreavus's Pain Split helps or hurts the user's current HP map.
- Whether the intended Ghost answer is weak to local Ghost/Psychic/Dark
  interactions after checking the hack chart.

## Extracted Lesson

Morty is a temporary-control cash-out fight. Sleep, confusion, Ghost Curse,
Toxic, Pain Split, Focus Band, and Destiny Bond are not separate annoyances;
they are ways to make the player spend the one piece that must remain for the
next route. The correct plan is to preserve the awake Gengar answer, refuse
automatic KOs into Destiny Bond, and rebuild immediately after any control
branch changes the board.
