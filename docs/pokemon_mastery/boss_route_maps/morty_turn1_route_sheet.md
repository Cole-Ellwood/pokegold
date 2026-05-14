# Morty Turn-1 Route Sheet

Status: local boss route map. This is not a final player plan until the user's
team, HP, moves, and items are known.

Local evidence:

- Roster source: `data/trainers/parties.asm`
- Move table: `docs/agent_navigation/hack_mechanics_reference.md`
- Haunter and Gengar local typing: Ghost / Psychic in
  `data/pokemon/base_stats/haunter.asm` and
  `data/pokemon/base_stats/gengar.asm`
- Misdreavus local typing: Ghost / Ghost in
  `data/pokemon/base_stats/misdreavus.asm`
- Dream Eater requires the target to be asleep:
  `engine/battle/effect_commands.asm`
- Ghost Curse: fails into hidden/substitute targets, then applies curse and
  removes half the user's max HP in `engine/battle/move_effects/curse.asm`
- Destiny Bond sets `SUBSTATUS_DESTINY_BOND` in
  `engine/battle/move_effects/destiny_bond.asm`; the faint check removes the
  attacker if it KOs the bonded target, and core turn flow clears the state
  around actions.

Boss roster:

```text
Lv22 Haunter @ MIRACLEBERRY:
  Hypnosis / Dream Eater / Curse / Night Shade

Lv23 Misdreavus @ LEFTOVERS:
  Confuse Ray / Toxic / Pain Split / Shadow Ball

Lv26 Gengar @ SPELL_TAG:
  Shadow Ball / Thunderbolt / Destiny Bond / Psychic

Lv24 Haunter @ FOCUS_BAND:
  Hypnosis / Shadow Ball / Psybeam / Confuse Ray
```

## Boss Routes

Opening Haunter route:

- Goal: land Hypnosis, then cash out with Dream Eater, Curse, or Night Shade.
- What it punishes: assuming sleep is a permanent disable, or letting the
  sleeping answer sit in front of Dream Eater without a pivot plan.
- Denial idea: if sleep lands, immediately re-score around sleep state and the
  next cash-out. If sleep misses, do not over-respect the old threat; punish the
  tempo loss if the matchup allows it.

Misdreavus route:

- Goal: stretch the game with Confuse Ray, Toxic, Pain Split, Leftovers, and
  Shadow Ball until the player loses tempo or a clean answer.
- What it punishes: relying on one big hit that can be delayed by confusion or
  Pain Split, or poisoning/statusing without checking whether the clock favors
  the player.
- Denial idea: use reliable pressure, Haze/phazing if available, or status only
  when it changes the Pain Split/Toxic clock. Do not call confusion safe; it is
  a short chance-based agency tax, not a wall.

Gengar route:

- Goal: apply immediate coverage pressure, then use Destiny Bond to punish the
  obvious KO or preserve trade value.
- What it punishes: autopilot "take the KO" turns when Gengar is in Destiny
  Bond range or likely to click it.
- Denial idea: before KOing Gengar, ask whether Destiny Bond is active or
  heavily incentivized. If so, consider a non-KO move, switch, status, setup,
  or sacrifice only if it preserves the long-game route.

Second Haunter route:

- Goal: repeat sleep/confusion pressure with Focus Band variance.
- What it punishes: assuming the Morty plan is solved after the first sleep
  user is removed.
- Denial idea: keep a second status plan or stable attacker for the late Haunter
  instead of spending every clean answer on Misdreavus and Gengar.

## Player Plan Template

Primary route:

- Keep at least one awake, healthy Ghost-answer while denying Morty's temporary
  control from becoming Dream Eater, Curse, Pain Split, or Destiny Bond value.

Backup route:

- If the primary answer is slept or poisoned, pivot to damage control: waste
  sleep turns only when safe, prevent Dream Eater cash-out, and preserve a
  separate Gengar answer for Destiny Bond timing.

Best lead profile:

- A lead that either threatens opening Haunter immediately or can absorb one
  control attempt without becoming the only answer to Gengar later.

Avoid as lead:

- The only Gengar answer if Hypnosis, Curse, or Toxic would remove its later
  role.
- A slow setup Pokemon that lets Hypnosis or Confuse Ray define the first
  exchange.
- A KO-only plan that has no answer when Gengar trades with Destiny Bond.

First-turn question:

```text
If Morty gets one temporary-control turn, what is his cash-out, and do we still
have the piece that stops Gengar?
```

If control misses or fails:

- Punish the tempo loss with direct progress, but still track Focus Band and
  Destiny Bond later.

If control lands:

- Stop the script. Rebuild from the actual state: sleep turns, status, HP,
  whether Dream Eater works, whether Curse is active, and whether a safe pivot
  exists.

Worst plausible branch:

- The player lets one answer sleep through Dream Eater or Curse pressure, then
  takes an automatic KO into Gengar's Destiny Bond and no longer has a stable
  route for the second Haunter.

Abandon conditions:

- A planned attacker is asleep and Dream Eater is live.
- Curse is active and the cursed piece is also needed for Gengar.
- Misdreavus has turned the exchange into a Toxic/Pain Split clock the player
  cannot win.
- Gengar is low enough to invite Destiny Bond and our chosen move would KO.
- Type-chart, passive, Focus Band, or damage evidence contradicts the assumed
  line.

Snorlax study transfer:

- Morty teaches the same route discipline as GSC anchor play, but through
  temporary control rather than bulk. The transferable lesson is to keep asking
  "so what does this status or KO actually buy?" and to preserve the piece that
  handles the future route, not only the current matchup.
