# Worked Example: Elite Four Gauntlet Resource Carryover Drill

Purpose: practice planning across Will, Koga, Bruno, Karen, and Lance as one
resource-carryover exam. This is not a single solved route. It trains the habit
of preserving HP, status absorbers, PP, berries, one-time trades, and
anti-setup tools across multiple boss fights instead of spending them to make
one battle look clean.

Local evidence:

- Route sheets:
  `will_pre_battle_route_sheet.md`,
  `koga_pre_battle_route_sheet.md`,
  `bruno_pre_battle_route_sheet.md`,
  `karen_pre_battle_route_sheet.md`, and
  `lance_pre_battle_route_sheet.md`.
- Boss route maps:
  `../boss_route_maps/will_turn1_route_sheet.md`,
  `../boss_route_maps/koga_turn1_route_sheet.md`,
  `../boss_route_maps/bruno_turn1_route_sheet.md`,
  `../boss_route_maps/karen_turn1_route_sheet.md`, and
  `../boss_route_maps/lance_turn1_route_sheet.md`.
- Adaptive opening audit:
  `../boss_route_maps/adaptive_lead_audit_2026-05-13.md`.
- Mechanics overview and generated mechanics reference:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.

Expert study anchors:

- Smogon Restricted Sparring material is directly useful for in-game gauntlets:
  HP, PP, and healing timing are resources that should be spent only when the
  later matchup justifies them:
  <https://www.smogon.com/ingame/bc/restricted_sparring>.
- Smogon risk/reward material: when ahead in a gauntlet, preserve the route and
  avoid low-value risk; when behind, accept risk only if it restores a real
  future route:
  <https://www.smogon.com/resources/beginner/bw_risk_reward>.
- Smogon long-term thinking material: each battle should be judged by the next
  route it enables, not only by the current KO:
  <https://www.smogon.com/rs/articles/long_term_thinking>.
- Smogon Getting Started material: team roles and win conditions matter because
  each piece's function determines whether it can be spent:
  <https://www.smogon.com/articles/getting-started>.

## Assumption Switch

Run this drill in one of two modes before giving advice:

```text
strict mode:
  No between-battle healing, status curing, PP restoration, or item use unless
  the user explicitly says it happened.

in-game item mode:
  Between-battle healing and items are allowed only as finite bag resources.
  Track every Full Restore, Revive, Ether, berry, and held-item consumption as
  part of the route.
```

Do not silently assume either mode. If the user is asking for real Elite Four
advice, ask or infer the item policy first. If unknown, give advice that states
which recommendation flips under each mode.

## Starting Gauntlet Map

The gauntlet has five resource questions:

```text
Will:
  Can we exit with the Alakazam / Houndoom / Slowbro answers intact after
  Forretress hazards, Toxic, Protect, Explosion, Starmie spin, and Future Sight?

Koga:
  Can we keep switch freedom and key answers through Toxic, Spider Web, Spikes,
  Tentacruel Haze/Spin, Muk Rest/Curse, Nidoking coverage, and Crobat cleanup?

Bruno:
  Can we deny Onix hazards/phazing while preserving the Machamp, Heracross, and
  Mach Punch endgame answers?

Karen:
  Can we handle Gengar sleep/hazards, Pursuit, Donphan spin/phaze, Safeguard,
  Tyranitar Dragon Dance, and Houndoom sun without spending Lance answers?

Lance:
  Can we still deny repeated Dragon Dance / Quiver Dance waves and final
  Dragonite after four prior fights?
```

The pre-gauntlet plan must name:

```text
primary cleaner:
backup cleaner:
Will special-route answer:
Koga poison/trap buffer:
Bruno Fighting answer:
Karen sleep/Pursuit/sun answer:
Lance anti-setup / Dragonite route:
shared overloaded piece:
finite PP moves:
finite item plan:
pieces allowed to faint before Lance:
pieces not allowed to faint before Lance:
```

## Carryover Ledger

After every fight, update this:

```text
fight completed:
HP states:
status states:
held items consumed:
bag items consumed:
critical PP remaining:
one-time moves spent:
sleep clause / Rest states relevant to next fight:
phazing / Haze / priority tools remaining:
hazard removal / setter tools remaining:
speed-control tools remaining:
piece whose job is complete:
piece whose job is still irreplaceable:
next fight route most threatened:
lead for next fight:
abandon condition for next fight:
```

The ledger should answer:

```text
Did we win the fight in a way that makes the next fight worse than necessary?
```

## Drill

### Stage 0: Pre-Gauntlet Route Reservation

Question:

- Which pieces are reserved for Lance before the first move against Will?

Write the answer map:

```text
Lance Dragonite route:
Lance Gyarados / Kingdra route:
Lance Yanma sleep / Focus Band route:
Karen Tyranitar / Houndoom route:
Bruno Machamp / Heracross route:
Koga Nidoking / Crobat route:
Will Alakazam / Houndoom / Slowbro route:
```

Failure signs:

- Building the Will lead around the best Will matchup while quietly using the
  only Lance anti-setup piece.
- Treating Revives, Full Restores, Ethers, or berries as unlimited.
- Letting one Pokemon be the unspoken answer to every later fight.

### Stage 1: Will Exit Condition

Question:

- Can the team leave Will with special answers and hazard/status control still
  usable?

Will danger branches:

- Forretress Toxic or Explosion hits a later answer.
- Starmie removes the user's hazard route or forces the wrong pivot.
- Slowbro Amnesia/Rest burns PP or forces status.
- Houndoom Pursuit punishes a switch.
- Xatu Future Sight changes the safe landing turn.

Good exit:

- The Alakazam/Houndoom/Slowbro answer map is intact or deliberately replaced.
- Toxic, Spikes, and Explosion were attached to pieces whose later jobs are
  complete or repairable under the chosen item mode.
- No finite PP or item resource was spent just to make the score look cleaner.

Bad exit:

- A key Koga, Bruno, Karen, or Lance answer is poisoned, exploded on, or below
  threshold for no route gain.

### Stage 2: Koga Exit Condition

Question:

- Can the team absorb poison/trap pressure without losing the next three
  fights?

Koga danger branches:

- Ariados traps or poisons an irreplaceable piece.
- Tentacruel erases hazard/setup progress.
- Muk forces Rest/Curse attrition.
- Umbreon turns switching into Toxic / Confuse Ray / Pursuit pressure.
- Nidoking or Crobat punishes the poisoned answer.

Good exit:

- Poison clocks are on expendable or repairable pieces.
- The Bruno Fighting answer and Karen/Lance anti-setup tools remain healthy.
- The player has not spent the only Haze/phaze/status tool just to beat Muk
  faster unless Lance remains covered.

Bad exit:

- The team wins Koga but carries Toxic, low HP, or PP damage on the exact piece
  needed to survive Bruno priority or Lance setup.

### Stage 3: Bruno Exit Condition

Question:

- Can the team answer physical pressure without putting the Lance route into
  priority or crit range?

Bruno danger branches:

- Onix Spikes/Roar chips the real Fighting answers.
- Hitmontop spins or creates Mach Punch cleanup range.
- Hitmonlee Focus Band or Meditate changes the expected KO plan.
- Machamp coverage and crit pressure break the static wall.
- Heracross Focus Energy plus Scope Lens makes a no-crit plan unsafe.

Good exit:

- Mach Punch range is no longer threatening the planned Karen/Lance cleaner.
- The Lance Dragonite answer has not been used as the generic Fighting pivot.
- Any crit or Focus Band risk accepted was necessary and recorded.

Bad exit:

- The team reaches Karen with the Houndoom/Tyranitar answer chipped or the
  Lance final answer already below boosted range.

### Stage 4: Karen Exit Condition

Question:

- Can the team deny disruption without arriving at Lance asleep, trapped,
  Pursuited, or sun-broken?

Karen danger branches:

- Gengar sleeps the Tyranitar/Houndoom/Lance answer.
- Donphan spins, phazes, or forces bad entries.
- Murkrow Pursuit punishes a necessary switch.
- Crobat blocks status with Safeguard or spreads Toxic/confusion.
- Tyranitar Dragon Dances.
- Houndoom starts sun and flips Water/SolarBeam damage.

Good exit:

- The Lance anti-setup route is awake, healthy enough, and has PP.
- The team did not spend its final phazer/Haze/status tool unless Lance is
  covered by another route.
- Any sun or Pursuit damage was assigned to pieces whose Lance jobs are over.

Bad exit:

- The team beats Karen by spending the one route that stops Lance's first setup
  wave.

### Stage 5: Lance Entry Audit

Question:

- Does the team entering Lance still resemble the pre-gauntlet plan?

Before choosing the Lance lead, write:

```text
available anti-setup tools:
available revenge tools:
available status / phaze / Haze tools:
Dragonite answer HP/status/PP:
Kingdra/Gyarados answer HP/status/PP:
Yanma sleep plan:
safe sacrifices remaining:
bag items remaining, if item mode:
forced-risk branches:
```

If one required route is missing, do not pretend the plan is stable. Choose the
Lance line that creates the highest real comeback chance and label the risk.

## Pass Conditions

- The plan names Lance preservation priorities before Will starts.
- Every between-battle heal, item, held-item consumption, or PP restore is
  logged under the selected assumption mode.
- Each fight has an exit condition, not merely a win condition.
- No Pokemon is called expendable until its later gauntlet jobs are checked.
- The ledger records status and PP damage as route damage, not cosmetic damage.
- The final Lance plan explicitly explains which pre-gauntlet assumptions
  survived and which failed.

## Extracted Lesson

The Elite Four is not five isolated boss fights. It is one long resource
allocation problem with five score screens. A move that is correct inside Will
can be wrong for the gauntlet if it spends the Koga poison buffer, the Bruno
priority answer, Karen's sleep/sun answer, or Lance's anti-setup tool. The
mastery skill is exit-condition thinking: winning each fight in the condition
needed to win the next one.
