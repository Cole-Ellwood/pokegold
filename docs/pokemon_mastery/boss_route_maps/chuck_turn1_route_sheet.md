# Chuck Turn-1 Route Sheet

Status: local boss route map. This is not a final player plan until the user's
team, HP, moves, items, and current box options are known.

Local evidence:

- Roster source: `data/trainers/parties.asm`
- Boss Pokemon stats/types: `data/pokemon/base_stats/*.asm`
- Move table: `data/moves/moves.asm` and
  `docs/agent_navigation/hack_mechanics_reference.md`
- Focus Punch is `EFFECT_FOCUS_PUNCH`, 150 BP, Fighting, physical, contact in
  `data/moves/moves.asm`.
- Local Focus Punch handling in `engine/battle/late_gen_held_items.asm` marks
  lost focus if the selected Focus Punch user takes nonzero damage before
  acting.
- Poliwrath Focus Punch boundary example:
  `docs/pokemon_mastery/worked_examples/chuck_poliwrath_focus_punch_free_turn.md`
- Opening policy:
  `docs/pokemon_mastery/romhack_deltas/boss_opening_policy.md` and
  `docs/pokemon_mastery/boss_route_maps/adaptive_lead_audit_2026-05-13.md`
  list Chuck as adaptive first-three: Sudowoodo / Hitmontop / Hitmonlee.
- Mach Punch uses `EFFECT_PRIORITY_HIT`; priority effects are listed in
  `data/moves/effects_priorities.asm`.
- Foresight source: `docs/agent_navigation/hack_mechanics_reference.md` and
  `data/types/type_matchups.asm`; it removes only Normal/Fighting into Ghost
  immunity.
- Focus Band source: `docs/agent_navigation/gen2_vs_modern_mechanics.md`;
  local note says 1/16 survival at 1 HP.
- Type-boost items are listed in
  `docs/agent_navigation/hack_mechanics_reference.md` and
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`.
- Expert principle sources: Smogon Focus Punch/Substitute articles, Fighting
  move history, GSC Machamp/threat discussion, and general route planning.

Boss roster:

```text
Lv30 Sudowoodo @ Hard Stone:
  Spikes / Rock Slide / Focus Punch / Roar

Lv31 Hitmontop @ Black Belt:
  Rapid Spin / Mach Punch / Rock Slide / Focus Punch

Lv33 Hitmonlee @ Focus Band:
  Focus Punch / Hi Jump Kick / Rock Slide / Foresight

Lv32 Umbreon @ Mint Berry:
  Pursuit / Confuse Ray / Moonlight / Toxic

Lv34 Poliwrath @ Mystic Water:
  Focus Punch / Surf / Ice Punch / Hypnosis
```

Boss likely openings:

- Chuck is source-listed as adaptive first-three, not fixed Sudowoodo.
- Plan for Sudowoodo / Hitmontop / Hitmonlee, with Sudowoodo favored by the
  current weighted opener rule.
- Player-side planning may use this boss roster and opener policy before the
  fight. Chuck's ordinary boss AI still must not know the player's unrevealed
  team, hidden moves, hidden item, private stats, or current-turn input.

## Boss Routes

Sudowoodo route:

- Goal: open with Spikes, then punish passive turns with Focus Punch or use Roar
  to make hazards matter.
- What it punishes: leads that spend turn 1 setting up, switching without a
  plan, or using low-impact status while Sudowoodo gets a hazard or free punch
  turn.
- Denial idea: pressure Sudowoodo immediately if possible. A move that prevents
  Focus Punch or keeps Spikes from becoming a Roar clock can be better than a
  slower "perfect" setup.

Hitmontop route:

- Goal: clear the player's hazards with Rapid Spin, pick off weakened targets
  with Mach Punch, and threaten Focus Punch when the player hesitates.
- What it punishes: hazard plans with no spin punish and endgames that leave a
  low-HP sweeper exposed to priority.
- Denial idea: do not count hazards as lasting progress until Hitmontop's spin
  turn is answered. Preserve priority-safe HP on the piece expected to convert
  late.

Hitmonlee route:

- Goal: force respect with high-power physical attacks, use Foresight if Ghost
  immunity would otherwise block Normal/Fighting damage, and sometimes survive
  a removal attempt with Focus Band.
- What it punishes: relying on an immunity slogan after Foresight, or planning a
  route that needs a guaranteed OHKO without pricing Focus Band.
- Denial idea: if the answer is a Ghost or another immunity-based pivot, check
  Foresight state and local type evidence. If removing Hitmonlee is mandatory,
  keep a backup plan for the 1/16 Focus Band branch.

Umbreon route:

- Goal: turn a Fighting-team battle into attrition with Toxic, Confuse Ray,
  Moonlight, Mint Berry sleep insurance, and Pursuit pressure.
- What it punishes: special attackers or utility pivots that cannot make
  concrete progress and then must switch through Pursuit.
- Denial idea: use Umbreon turns to force a real resource loss: Moonlight PP,
  status that sticks, safe breaker entry, or a pivot into the next Chuck route.
  Do not let it convert confusion plus Toxic into lost tempo.

Poliwrath route:

- Goal: use Hypnosis to create a free Focus Punch or coverage turn, then punish
  the player's chosen answer with Water/Ice/Fighting damage.
- What it punishes: saving all counterplay for Fighting damage while ignoring
  sleep and coverage, or letting the intended Poliwrath answer take earlier
  Spikes/Roar/Mach Punch chip.
- Denial idea: identify the sleep absorber or sleep-risk plan before Poliwrath
  appears. After Hypnosis hits, misses, or is blocked, re-score; do not continue
  the pre-sleep script.

## Player Plan Template

Primary route:

- Deny Chuck's free turns. The boss has multiple ways to make a passive turn
  expensive: Spikes, Roar, Rapid Spin, Focus Punch, Hypnosis, Confuse Ray,
  Moonlight, and priority cleanup.

Backup route:

- If Sudowoodo gets Spikes or Hitmontop keeps spin control, shorten the plan.
  Prioritize direct KO thresholds, safe sleep management, and preserving the
  exact piece that stops Poliwrath or Hitmonlee.

Best lead profile:

- A lead that pressures Sudowoodo, does not donate free Rapid Spin/Mach Punch
  positioning to Hitmontop, and does not let Hitmonlee create a Focus Punch or
  Foresight branch for free. It must not be the only Poliwrath answer.
- A setup lead is good only if it can survive and deny Focus Punch, Roar,
  Spikes, or priority chip from changing the route first.

Avoid as lead:

- A passive setup or status lead that gives Sudowoodo a free Spikes or Focus
  Punch turn.
- A hazard lead if Hitmontop can spin for free and the team has no punish.
- The only sleep absorber if early chip makes Poliwrath's Hypnosis route
  decisive later.
- A Ghost pivot that assumes immunity without checking Foresight.

First-turn question:

```text
Which adaptive opener appeared?

Sudowoodo: can we deny Spikes / Roar / Focus Punch without spending the
Poliwrath or Hitmonlee answer?

Hitmontop: is Rapid Spin, Mach Punch, Rock Slide, or Focus Punch the live route,
and does our lead preserve the cleaner from priority range?

Hitmonlee: can we deny Focus Punch / Hi Jump Kick pressure and price Focus Band
or Foresight before committing the answer?
```

If Sudowoodo sets Spikes:

- Re-score layer count, grounded team members, Roar risk, and whether Hitmontop
  can later spin away the player's hazards without punishment.

If Sudowoodo uses Focus Punch:

- If the player damaged it first, confirm whether Focus Punch lost focus. If the
  player used a slow non-damaging move or switched, evaluate who must now absorb
  the hit and whether the original plan is still live.

If Hitmontop opens, enters, or spins:

- Do not simply re-set hazards unless the next hazard turn is protected by
  pressure, a spin punish, or a route that does not need hazards.
- If Hitmontop opens, first decide whether Mach Punch ranges or Focus Punch
  free turns matter more than the player's hazard plan.

If Hitmonlee opens or enters:

- Price Focus Punch, Focus Band, and Foresight before relying on a single KO or
  immunity pivot. If the answer is immunity-based, verify Foresight state.

If Poliwrath uses Hypnosis:

- On hit, name the sleeping piece's remaining role and whether it can be spent.
  On miss, do not overextend automatically; check Surf, Ice Punch, and Focus
  Punch branches from the new board.

Worst plausible branch:

- The player spends early turns on passive setup or hazards, Sudowoodo starts
  Spikes and Roar pressure, Hitmontop erases the player's hazard plan, Umbreon
  slows the game with Toxic/confusion, and Poliwrath or Hitmonlee cashes in the
  damaged answers with sleep, priority, or Focus Punch.

Abandon conditions:

- The intended Poliwrath answer is asleep, below its needed HP threshold, or no
  longer safe against the revealed coverage.
- Hitmontop can remove hazards without giving the player a decisive punish.
- Focus Punch is getting free turns because the player is switching or using
  slow utility moves.
- Foresight has removed the immunity that a pivot plan relied on.
- Umbreon turns the game into Moonlight/Toxic/Pursuit attrition that the player
  is not winning.
- Type-chart, passive, item, or damage evidence contradicts the assumed answer.

Snorlax study transfer:

- Chuck is not a Snorlax-style Rest-cycle fight. The useful GSC transfer is the
  Fighting-wallbreaker lesson: strong Fighting pressure often needs support,
  positioning, and correct target choice. In this boss fight, that support shows
  up as free-turn creation, spin control, priority cleanup, and sleep.
