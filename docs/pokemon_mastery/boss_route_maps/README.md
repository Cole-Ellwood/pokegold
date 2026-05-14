# Boss Route Map Index

Purpose: quick retrieval for Gym Leader Lab pre-battle planning. The individual
route sheets remain the authority for each boss. This index answers: "What kind
of Pokemon problem is this fight testing, and which sheet should I open first?"

Source discipline:

- Boss rosters, levels, moves, and item details come from the per-boss sheets,
  which point back to `data/trainers/parties.asm`,
  `data/pokemon/base_stats/*.asm`, `data/moves/moves.asm`, and local mechanics
  docs.
- `source_alignment_audit_2026-05-13.md` records a normalized check that the
  current route maps mention the current boss roster species and source-party
  moves.
- `adaptive_lead_audit_2026-05-13.md` records which current bosses are
  fixed-first openers and which use the source adaptive first-three opener.
- General planning lessons come from expert sources already indexed in
  `../cookbook.md`, especially Smogon's long-term thinking, win-condition, risk,
  prediction/planning, hazard, weather, and status material.
- Do not use this index to answer exact type, passive, damage, or AI questions.
  Check the route sheet and local mechanics evidence when the answer depends on
  those details.
- Boss openings are source-specific. `../romhack_deltas/boss_opening_policy.md`
  records which current bosses use the adaptive-lead opener and which appear to
  use the first listed living party member.

## Route Map Readiness

There are 22 current boss route sheets in this folder. They are source-grounded
boss-side study artifacts, not complete battle advice. Use them to identify the
boss routes, opening policy, obvious punish branches, and pieces that usually
need preservation.

Before giving exact lead or turn advice, fill the missing player-side layer from
`../pre_battle_route_sheet.md` or `../boss_turn_advice_template.md`:

```text
our team / levels / HP / moves / items:
our irreplaceable pieces:
damage or type evidence needed:
what information would flip the lead or move:
```

This matters because a route sheet can say "preserve the Snorlax answer" or
"deny the Scizor route," but the correct move depends on the user's actual
team. The route map should guide the question; it should not become a law that
overrides current HP, status, damage evidence, or a better live route.

## How To Use This Index

1. Start with the boss row below.
2. Name the boss route that wins if ignored.
3. Name the player piece or resource that must survive that route.
4. Check whether the boss has a fixed source lead or adaptive first-three
   opener.
5. Choose a lead that contests the possible opening without spending that
   required piece.
6. Open the full boss sheet before giving turn advice.

This follows the same expert principle from long-game play: form a plan before
turn 1, track whether the battle is developing toward that plan, and keep backup
routes ready when the opponent or RNG changes the board.

## Boss Quick Map

| Boss | Main Decision Problem | Turn-1 Retrieval Cue |
| --- | --- | --- |
| Falkner | Accuracy, priority, and sleep discipline. | Pressure Pidgeotto without depending on a single shaky move or spending the Noctowl answer. |
| Bugsy | Support chain into Scyther conversion. | Stop Ariados/Ledian from changing what Scyther is allowed to do later. |
| Whitney | Evasion/paralysis support into Miltank containment. | Do not let Clefairy disable the piece that must contain Miltank. |
| Morty | Sleep, Curse, Pain Split, and Destiny Bond control. | Keep one awake Ghost answer and do not trade blindly into Destiny Bond. |
| Chuck | Free-turn denial against Focus Punch, hazards, Roar, sleep, and priority. | Pressure Sudowoodo without spending the Poliwrath or Hitmonlee answer. |
| Jasmine | Steel hazard war, spin control, phazing, and Scizor setup. | Prevent free Spikes while preserving the Scizor/Steelix answer. |
| Pryce | Spikes, spin, Explosion, and forced-switch punishment. | Decide early whether to deny Cloyster, remove Spikes, or stop switching freely. |
| Clair | Anti-Dragon Dance preservation under hazards/status. | Contest Gligar without losing the Kingdra/Dragonair plan. |
| Brock | Hazards, recovery, setup, Explosion, and fast Rock pressure. | Decide whether Omastar, Corsola, Golem/Kabutops, or Aerodactyl is the current route. |
| Misty | Adaptive Politoed/Starmie/Quagsire opening, rain clock, sleep, recovery, paralysis, and bulky Water pressure. | Cover the first-three opener set and preserve the Starmie/Quagsire/Lapras answer. |
| Lt. Surge | Air Balloon hazard/status support into fast Electric coverage. | Pop or punish Magneton without spending the Raichu/Electabuzz answer. |
| Erika | Sleep, paralysis, Encore, Leech Seed, sun, setup, and Explosion. | Avoid donating control turns; preserve answers to both Bellossom and Victreebel. |
| Janine | Hazard/spin control plus Explosion into Nidoking or Venomoth routes. | Identify the Nidoking/Venomoth answer before Qwilfish trades into it. |
| Sabrina | Screens, Encore, sleep, paralysis, Choice lock, and recovery. | Pressure Mr. Mime without handing Encore a passive turn or losing the Alakazam/Jynx plan. |
| Blaine | Fire pressure plus Spikes, sun, Safeguard, Agility, recoil, and priority. | Keep the real Fire route answer healthy while denying Magcargo/Ninetales setup. |
| Blue | Full answer-map test with adaptive Pidgeot/Porygon2/Gyarados opening, Choice lock, setup, recovery, breakers, and priority. | Cover the first-three opener set without spending the Gyarados/Arcanine answer. |
| Will | Forretress hazards/status, Starmie spin, Slowbro loop, and special endgame. | Pressure Forretress while preserving answers to Alakazam, Houndoom, and Slowbro. |
| Koga | Poison/hazard/trap/recovery timer ownership. | Make Koga's early clock land on an expendable piece or short-circuit it immediately. |
| Bruno | Hazard/phaze opening into Fighting breaker preservation. | Deny Onix pressure without losing the Machamp/Heracross answers. |
| Karen | Sleep/hazard opener into spin/Roar, Safeguard, Dragon Dance, and sun. | Pressure Gengar while preserving the Tyranitar/Houndoom plan. |
| Lance | Multi-wave setup fight. | Map every anti-setup answer before spending one on Steelix. |
| Red | Full-route exam: coverage lead, screens/setup, RestTalk anchor, sun, Mirror Coat. | Beat Pikachu while preserving the Snorlax, Espeon, sun, and Blastoise plans. |

## Recurring Fight Families

Use these families to transfer study between bosses. The family label is not a
replacement for the full route sheet; it is a reminder of which cookbook recipe
should be active first.

| Family | Bosses | Cookbook Focus |
| --- | --- | --- |
| Support chain into converter | Bugsy, Lt. Surge, Erika, Sabrina, Lance, Red | `Support Chain Stop Test`, `Setup Window Test`, `Long-Term Plan Revision` |
| Hazard/spin/phaze war | Jasmine, Pryce, Brock, Bruno, Will, Janine, Koga, Karen, Clair | `GSC Hazard Pressure`, `Two-Sided Hazard War`, `Forced-Control Move Test` |
| Weather or field-clock ownership | Misty, Blaine, Erika, Karen, Red | `Weather Ownership Test`, `Clock Ownership Test`, `Delayed-Damage Ledger Test` |
| Sleep and temporary-control discipline | Falkner, Morty, Erika, Sabrina, Karen, Misty, Janine, Lance | `Status Clock Test`, `Sleep Plus Hazard Re-Entry Tax`, `Long-Term Plan Revision` |
| Explosion or sacrifice route trade | Brock, Pryce, Janine, Jasmine, Erika, Will, Lt. Surge, Red | `Explosion And Sacrifice`, `Sacrifice As Active-State Reset` |
| Choice lock, priority, or revenge range | Blue, Sabrina, Blaine, Falkner, Lt. Surge, Red | `Locked-Move Commitment Test`, `Priority And Revenge Range Test` |
| Bulky recovery or anchor answer map | Whitney, Misty, Will, Blue, Red, Koga, Brock | `Bulky Anchor Answer Graph`, `Win-Condition Map`, `Preservation Pivot Test` |

## Study Notes

- Snorlax-heavy GSC material transfers here as anchor logic, not species logic.
  The recurring local question is usually "which boss route is the anchor or
  converter?" rather than "where is Snorlax?"
- Later-generation material transfers most cleanly through the ideas of route
  planning, hazard leverage, preserving win-condition pieces, and forcing or
  denying setup windows. Generation-specific mechanics stay quarantined until
  checked against local docs/source.
- A later simulator win-rate gate should use this index as a coverage checklist:
  the test set needs fights from each family, not only the easiest hazard or
  setup cases.
