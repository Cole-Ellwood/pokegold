# Romhack Play Mastery Transfer

Status: active transfer workbench.
Last updated: 2026-05-17.

Purpose: turn the existing GSC/Pokemon mastery into romhack-specific play skill.
This file is for future sessions that need to play, review, or code boss AI for
this hack without relearning the whole foundation.

This is not a claim that the romhack meta is mastered. It is the first practical
transfer layer: local boss rosters, mechanic rewrites, damage-check habits, and
drill prompts that force GSC strategy to pass through the romhack ruleset.

## Evidence Used In This Packet

Local source/docs inspected:

- `docs/pokemon_mastery/romhack_boss_ai_mastery.md`
- `docs/pokemon_mastery/romhack_deltas/mechanics_inventory.md`
- `docs/pokemon_mastery/boss_route_maps/README.md`
- representative boss route sheets for Clair and Koga
- `data/trainers/parties.asm`, parsed through `tools/audit/trainer_parties.py`
- `docs/agent_navigation/hack_mechanics_reference.md`
- `docs/mechanics_changes_from_base.md`
- `tools/damage_debugger/README.md`
- `tools/debugger/README.md`

Commands used for source-derived checks:

```powershell
python -m tools.damage_debugger.matchup ALAKAZAM:67 MUK:62 PSYCHIC_M --user-item CHOICE_SPECS --json
python -m tools.damage_debugger.matchup ALAKAZAM:67 MUK:62 PSYCHIC_M --json
python -m tools.damage_debugger.matchup ARCANINE:70 VENUSAUR:77 FLAMETHROWER --user-item LIFE_ORB --json
python -m tools.damage_debugger.matchup ARCANINE:70 VENUSAUR:77 FLAMETHROWER --json
python -m tools.damage_debugger.matchup NIDOKING:43 RAICHU:43 EARTHQUAKE --user-item EXPERT_BELT --json
python -m tools.damage_debugger.matchup MAROWAK:58 MAGNETON:58 EARTHQUAKE --opponent-item AIR_BALLOON --json
python -m tools.damage_debugger.matchup MAROWAK:58 MAGNETON:58 EARTHQUAKE --json
python -m tools.damage_debugger.clobber_smoke
python -m tools.debugger triage --symptom "Air Balloon should block Ground damage but quick damage oracle returns damage" --json
python -m tools.debugger provenance --source-file engine\battle\effect_commands.asm --source-file engine\battle\late_gen_held_items.asm --symbol wTypeMatchup --symbol wCurDamage --json
```

Tool status:

- `tools.damage_debugger.matchup` now models Air Balloon Ground immunity in the
  quick damage path: Marowak Earthquake into Magneton @ Air Balloon returns
  0-0 damage, while the same no-item query remains 228-268.
- `tools.damage_debugger.clobber_smoke` now has an `afterhit_air_balloon`
  runtime smoke: nonzero direct-hit damage pops Air Balloon and clears both the
  active defender item and trainer party item. Display text/order is not yet a
  decision-policy fixture.
- Local source still matters for timing: `BattleCheckTypeMatchup` blocks Ground
  before the type chart, and `HandleLateGenAfterHitEffects_Far` pops Air
  Balloon only after nonzero direct-hit damage.
- `tools.debugger` is useful as the ROM-wide router for mechanics questions:
  use `triage`, `provenance`, `slice`, `setup`, and runtime watch/trace commands
  to raise a mechanic from source-checked to runtime-checked.

## Transfer Ladder

Use this sequence for every romhack-facing decision:

1. Start from the GSC strategic concept.
2. Replace vanilla mechanics with romhack mechanics.
3. Rebuild the boss role from local roster, item, moves, stats, and type.
4. Generate role candidates before ranking.
5. Run damage/mechanics checks only for facts that can flip the answer.
6. Score the move by route conversion, denial, branch punish, and resource
   identity.
7. If source/docs and the quick oracle disagree, route through the unified
   debugger before trusting either side.
8. Record whether a miss was candidate generation, route-budget ranking,
   mechanics, hidden-info, or damage-threshold failure.

## Debugger-Assisted Mechanics Rule

When a romhack mechanic can flip a route, future sessions should grade evidence
before using it in play or boss-AI policy:

1. Source-checked: exact local source and constants found.
2. Oracle-checked: `tools.damage_debugger.matchup` or another focused mirror
   returns the expected result and has a regression case.
3. Runtime-checked: `tools.debugger` or a subsystem debugger observes the ROM
   state, trace, or save-state behavior for the mechanic.

Do not import vanilla or later-gen intuition directly. If a mechanic is only
source-checked, use it for candidate generation but keep exact timing, side
effects, and AI scoring constants provisional.

## GSC Concept To Romhack Rewrite

| GSC concept | Romhack rewrite | Check before trusting |
| --- | --- | --- |
| One Spikes layer as long-term pressure. | Three-layer Spikes creates separate 0->1, 1->2, and 2->3 decisions; 3 layers is maxHP/4 grounded entry damage. | Layer count, grounded targets, phazing route, active Rapid Spin, setter survival. |
| Spinblock and hazard retention. | Rapid Spin clears all layers; Ghost interactions need local source/runtime proof before relying on vanilla assumptions. | `spikes_and_rapid_spin.md`, pending index, fixture status. |
| Preserve the Snorlax answer. | Preserve the answer to the boss's actual local anchor or converter: Muk, Kingdra, Scizor, Tyranitar, Gyarados, Alakazam, etc. | Boss roster, item, local stats/types/moves, damage threshold. |
| Punish passive support. | Support may include Air Balloon, Choice lock, type passives, three-layer Spikes, Haze, Encore, phaze, or item-gated legality. | Item behavior, move legality, public information tier. |
| Status creates control turns. | Status can be blocked by Dark shield, cured by berries, punished by Poison contact, reset by Rest, or outpaced by local setup. | Type passive, held item, Rest/Sleep status, route payoff. |
| Explosion simplifies or opens a route. | Explosion remains a route trade, but exact timing/Ghost interactions are still pending. | Source/runtime fixture before hard policy; route owner after trade. |
| Dragon Dance setup. | Dragon Dance uses `bestattackup` plus Speed; Outrage has a Dragon-user category exception. | Current Atk/SpA, Speed after boost, Outrage category, Haze/phaze/revenge. |
| Modern item intuition. | Items are local code: Choice, Life Orb, Eviolite / EVOLITE, Air Balloon, Rocky Helmet, Assault Vest, Shell Bell, Metronome item. | `late_gen_held_items.asm`, generated item table, runtime fixture if exact timing matters. |

## Boss-Meta Families From Current Rosters

These families are source-derived from the current boss rosters and existing
route maps. They are the minimum coverage set for romhack transfer practice.

### Hazard, Spin, And Phaze Economy

Bosses: Jasmine, Pryce, Clair, Brock, Koga, Will, Bruno, Karen, Lt. Surge.

Local examples:

- Jasmine: Magneton and Skarmory place Spikes; Forretress spins; Steelix and
  Skarmory phaze.
- Pryce: Cloyster sets Spikes and can explode; Dewgong spins; Piloswine Roars.
- Clair: Gligar sets Spikes; Mantine spins/Hazes; Steelix Roars.
- Koga: Ariados sets Spikes/traps/statuses; Tentacruel spins/Hazes.
- Lt. Surge: Air Balloon Magneton sets Spikes or trades; Electrode spins or
  screens.

Transfer target: stop treating hazards as one checkbox. Every hazard turn must
say which layer changes which forced switch, Rest, phaze, or KO route.

### Local Setup And Reset Races

Bosses: Bugsy, Clair, Karen, Blue, Red, Misty, Brock, Blaine, Erika, Koga.

Local examples:

- Bugsy: Ledian Quiver Dance plus Baton Pass changes Scyther's route.
- Clair: Kingdra and Dragonair use Dragon Dance under local `bestattackup`
  logic.
- Karen: Tyranitar uses Dragon Dance with Rock/Dark/Ground coverage.
- Blue: Gyarados uses Dragon Dance and Outrage/Surf/Hyper Beam.
- Red: Snorlax Curse/RestTalk and Espeon Calm Mind ask different denial
  questions.

Transfer target: identify whether the setup move changes an immediate damage,
speed, Rest, phaze, or lock threshold. Do not answer setup with generic chip.

### Late-Gen Item Commitments

Bosses: Whitney, Lt. Surge, Erika, Janine, Sabrina, Blaine, Blue, Brock.

Local examples:

- Whitney Clefairy uses Eviolite / EVOLITE and Moonlight/Thunder Wave/Double
  Team support.
- Lt. Surge Magneton uses Air Balloon to block the obvious Ground plan before
  Spikes, Thunder Wave, or Explosion.
- Sabrina Alakazam uses Choice Specs; exploiting or respecting the lock is part
  of the fight.
- Blue Pidgeot uses Choice Band; Arcanine uses Life Orb.
- Brock Golem and Blaine Magcargo use Rocky Helmet.

Transfer target: every item should change either legal candidates, damage
range, contact cost, switch value, or the opponent's commitment clock.

### Type-Passive And Contact Routing

Bosses: Clair, Karen, Lance, Janine, Koga, Sabrina, Will, Red.

Local examples:

- Dragon routes must pass Dragon's Majesty, Imperial Scales, and Outrage
  category checks.
- Poison routes make contact cleanup and status clocks riskier.
- Psychic defenders have small zero-damage branches that matter most on
  irreversible exact-KO turns.
- Dark routes can block first status attempts.

Transfer target: type chart is not enough. Convert chart result to
passive-adjusted result, then to final route label.

### Cash-Out And Sacrifice Routes

Bosses: Pryce, Jasmine, Brock, Lt. Surge, Erika, Janine, Will, Morty, Red.

Local examples:

- Pryce Cloyster and Janine Qwilfish can use Spikes then Explosion.
- Lt. Surge Magneton/Electrode can turn support tempo into Explosion trades.
- Erika Exeggutor uses Life Orb pressure plus Sleep Powder and Explosion.
- Morty Gengar has Destiny Bond.

Transfer target: cash-out moves should be priced as board-shaping route trades,
not as just high-power attacks. Exact Explosion/Ghost behavior still needs
runtime caution.

### Recovery And Reset Anchors

Bosses: Koga, Misty, Will, Red, Blue, Brock, Whitney.

Local examples:

- Koga Muk uses Curse/Toxic/Rest; Umbreon uses Moonlight/Toxic/Confuse Ray.
- Misty Quagsire uses Curse/Rest; Starmie uses Recover.
- Will Slowbro uses Amnesia/Rest.
- Red Snorlax uses Curse/Sleep Talk/Rest.
- Blue Porygon2 uses Recover.

Transfer target: damage that only triggers a reset is not progress unless the
post-reset board is better. Name the controller of the reset cycle before
ranking the active move.

## Damage Range Anchors

These are not universal matchup laws. They are first anchors showing how local
items alter route math and how future sessions should record exact checks.

| Check | Source command | Result | Strategic read |
| --- | --- | --- | --- |
| Sabrina Alakazam Choice Specs Psychic into Muk | `python -m tools.damage_debugger.matchup ALAKAZAM:67 MUK:62 PSYCHIC_M --user-item CHOICE_SPECS --json` | 119-141 damage, 45-53% of max HP | Choice Specs turns Psychic from loose pressure into a likely 2HKO range after modest chip, but still not a clean max-HP OHKO. |
| Same without Choice Specs | `python -m tools.damage_debugger.matchup ALAKAZAM:67 MUK:62 PSYCHIC_M --json` | 79-94 damage, 30-35% | The item is answer-changing; do not score this Alakazam like ordinary GSC Alakazam. |
| Blue Arcanine Life Orb Flamethrower into Venusaur | `python -m tools.damage_debugger.matchup ARCANINE:70 VENUSAUR:77 FLAMETHROWER --user-item LIFE_ORB --json` | 159-188 damage, 55-65% | Life Orb makes the Fire route more forcing, while recoil becomes a future threshold. |
| Same without Life Orb | `python -m tools.damage_debugger.matchup ARCANINE:70 VENUSAUR:77 FLAMETHROWER --json` | 124-146 damage, 43-50% | The two-turn and revenge math changes; exact HP matters. |
| Koga Nidoking Expert Belt Earthquake into Raichu | `python -m tools.damage_debugger.matchup NIDOKING:43 RAICHU:43 EARTHQUAKE --user-item EXPERT_BELT --json` | 153-180 damage, 99-117% | Expert Belt can make the super-effective hit nearly guaranteed but not absolute at full HP; route claims need range language. |
| Marowak Earthquake into Magneton @ Air Balloon | `python -m tools.damage_debugger.matchup MAROWAK:58 MAGNETON:58 EARTHQUAKE --opponent-item AIR_BALLOON --json` | 0-0 damage | Air Balloon rewrites the obvious Ground route; first action must pop, bypass, pivot, or punish the protected support route. |
| Same without Air Balloon | `python -m tools.damage_debugger.matchup MAROWAK:58 MAGNETON:58 EARTHQUAKE --json` | 228-268 damage, guaranteed OHKO | The item alone flips the matchup from no-effect to immediate KO, so boss AI and play notes must gate Ground pressure on Balloon state. |

Air Balloon quick matchup check: the oracle now covers Ground immunity. Runtime
smoke now covers pop timing after nonzero direct-hit damage and active/party
item clear. Text/order is still UI-level, not a move-selection blocker.

## Drill Packet 001: Romhack Transfer Decisions

Use these as open-book transfer drills, not validation. The answer should fit:

```text
Decision ID:
Boss:
Public state:
Top action class:
Top three candidate classes:
Mechanics gates:
Why #1 beats #2:
What would flip:
Failure tag if missed:
```

Machine-readable copy: `romhack_drills/transfer_drills_001.jsonl`.
Scored answers: `romhack_drills/transfer_drills_001_scores.jsonl`.
Packet result: `romhack_drills/transfer_drills_001_results.md`.

### RMT-001: Lt. Surge Air Balloon Opening

Public state: Lt. Surge opens Magneton @ Air Balloon with Spikes /
Thunderbolt / Thunder Wave / Explosion. The player's lead plan was "click
Ground move."

Expected transfer: the GSC habit "Ground beats Electric/Steel" must be
rewritten through Air Balloon. Top candidates must include popping Balloon,
denying Spikes/Thunder Wave, and avoiding Explosion into the irreplaceable
Electric answer.

Mechanics gates: Air Balloon source, quick oracle, and after-hit runtime smoke;
Explosion timing caution; 3-layer Spikes economics.

Failure tag: mechanics if Ground is assumed to hit; route-budget if Balloon is
known but the chosen line still donates Spikes/status/Explosion.

### RMT-002: Clair Gligar Hazard Versus Dragon Answer

Public state: Clair opens Gligar @ Quick Claw with Spikes / Earthquake /
Wing Attack / Toxic. The obvious switch is also the player's best Kingdra
answer.

Expected transfer: preserve the Dragon Dance answer unless it actively denies
Gligar's route. Top candidates must include immediate Gligar pressure, a
status/hazard absorber, and a line that keeps the Kingdra/Dragonair answer
healthy.

Mechanics gates: Quick Claw variance, 3-layer Spikes, Toxic target identity,
Kingdra/Dragonair route map.

Failure tag: resource identity or route-budget.

### RMT-003: Koga Ariados Clock Ownership

Public state: Koga opens Ariados @ Leftovers with Spikes / Toxic / Leech Life /
Spider Web. The player's lead can set up but does not threaten Ariados quickly.

Expected transfer: the setup line is suspect unless it converts before Spikes,
Toxic, or Spider Web changes the board. Top candidates must include immediate
pressure, pivoting before trap/status, and the setup line only if it beats the
clock.

Mechanics gates: trap legality, Toxic target identity, 3-layer Spikes, future
Tentacruel Rapid Spin/Haze role.

Failure tag: script too slow or route-budget.

### RMT-004: Sabrina Choice Specs Lock

Public state: Alakazam @ Choice Specs reveals Psychic. The player's current
Pokemon survives but a bench Dark/Psychic answer may exploit the lock.

Expected transfer: treat the revealed move as both damage threat and
commitment. Candidate set must include staying for immediate progress,
switching to exploit the lock, and preserving the actual Alakazam answer.

Mechanics gates: Choice lock state, local Psychic matchups, damage range, no
hidden player-team reads for boss AI.

Failure tag: item commitment or resource identity.

### RMT-005: Blue Pidgeot Choice Band First Hit

Public state: Blue opens Pidgeot @ Choice Band. It can Wing Attack,
Double-Edge, Steel Wing, or Quick Attack.

Expected transfer: do not treat the first hit as ordinary damage only. The first
revealed move defines the lock and changes the next-board owner. Top candidates
must include immediate punish, scouting/absorbing lock, and preserving the
Gyarados/Arcanine answer.

Mechanics gates: Choice Band lock, move categories, contact/recoil if relevant,
priority range.

Failure tag: item commitment or next-board owner.

### RMT-006: Pryce Cloyster Spikes Or Explosion

Public state: Pryce Cloyster @ NeverMeltIce has Spikes / Surf / Ice Beam /
Explosion. The player's lead can set hazards or attack.

Expected transfer: price Spikes and Explosion together. A move that wins only
if Cloyster neither layers hazards nor trades into the right target is suspect.

Mechanics gates: 3-layer Spikes, Explosion timing caution, grounded switch
count, Dewgong Rapid Spin.

Failure tag: cash-out or reset loop.

### RMT-007: Janine Muk Rocky Helmet RestTalk

Public state: Janine Muk @ Rocky Helmet has Flamethrower / Sludge Bomb /
Sleep Talk / Rest. The player's best immediate damage is contact physical.

Expected transfer: contact damage is not free. Candidate set must include
non-contact damage/status/control if available, contact attack with recoil and
poison/Rest consequences priced, and preserving the Nidoking/Venomoth answer.

Mechanics gates: contact flag, Rocky Helmet, Poison passive, Rest/Sleep Talk
pending status.

Failure tag: mechanics or resource identity.

### RMT-008: Blue Gyarados Dragon Dance

Public state: Blue Gyarados @ Leftovers gets a free Dragon Dance threat with
Outrage / Surf / Hyper Beam.

Expected transfer: this is a setup-race drill, not a generic "hit it hard"
turn. Top candidates must include immediate denial, phaze/Haze/status/revenge,
and a line that exploits Outrage or Hyper Beam commitment if denial fails.

Mechanics gates: Dragon Dance `bestattackup`, Outrage category, Speed after
boost, local Water/Dragon bulk, Leftovers.

Failure tag: setup timing or mechanics.

### RMT-009: Erika Exeggutor Life Orb Sleep Explosion

Public state: Erika Exeggutor @ Life Orb has Psychic / Giga Drain /
Sleep Powder / Explosion.

Expected transfer: Sleep Powder, Life Orb damage, Giga Drain recovery, and
Explosion all compete for the same route. Top candidates must include sleep
absorber, immediate pressure, and cash-out preservation.

Mechanics gates: sleep pending status, Life Orb damage/recoil, Psychic passive
branch, Explosion timing caution.

Failure tag: status allocation or cash-out.

### RMT-010: Will Forretress Hazard Poison Explosion

Public state: Will Forretress @ Leftovers has Spikes / Protect / Toxic /
Explosion. Starmie spinner is still unrevealed or alive.

Expected transfer: the player must decide whether Forretress is currently a
hazard setter, poison clock, scout, or cash-out piece. A hazard plan with no
Starmie answer is incomplete.

Mechanics gates: 3-layer Spikes, Protect timing, Toxic target identity,
Explosion caution, Starmie Rapid Spin.

Failure tag: candidate generation or reset loop.

### RMT-011: Red Snorlax RestTalk Anchor

Public state: Red Snorlax @ Leftovers has Curse / Sleep Talk / Rest /
Body Slam.

Expected transfer: the GSC Snorlax lesson transfers as anchor mapping, but the
answer must be local. Top candidates must include immediate anti-setup,
controller for the Rest cycle, and preservation of the piece that beats boosted
Body Slam.

Mechanics gates: Rest/Sleep Talk pending status, paralysis/body-slam branch,
boost math, phaze/Haze availability.

Failure tag: reset loop or resource identity.

### RMT-012: Clair Steelix Local Typing

Public state: Clair Steelix is Steel/Dragon with Earthquake / Iron Tail /
Outrage / Roar and Spikes are up.

Expected transfer: vanilla Steelix assumptions are unsafe. Top candidates must
include local matchup-checked damage, anti-Roar/hazard route, and preservation
of the Dragon route answer.

Mechanics gates: Steel/Dragon local typing, Ground into Steelix, Outrage
category, Roar with Spikes.

Failure tag: mechanics or route-budget.

## Scoring The Transfer Drills

For each drill, score:

- `local_mechanic_checked`: yes/no
- `boss_route_named`: yes/no
- `player_route_named`: yes/no
- `top_three_cover_roles`: yes/no
- `route_budget_top1`: yes/no
- `hidden_info_clean`: yes/no
- `damage_or_fixture_needed_named`: yes/no
- `failure_tag`: candidate_generation / route_budget / mechanics /
  damage_threshold / hidden_info / reset_loop / cash_out / resource_identity /
  script_too_slow / item_commitment / next_board_owner / setup_timing /
  status_allocation

Promotion rule:

- A romhack lesson graduates from this workbench into a live heuristic or boss
  AI policy only after it improves decisions on multiple drills or a real
  boss-state packet and does not introduce mechanics or hidden-info errors.

## Next Work

1. Convert this drill packet into machine-readable scenarios or boss-advice
   prompts.
2. Add exact damage checks for each drill where a range can flip the answer.
3. Use the now-checked Air Balloon behavior in a fresh or semi-blind boss-state
   packet rather than re-testing the same fixture.
4. Run a focused semi-blind packet from real boss attempts or constructed
   source-state prompts and score the transfer metrics above.
5. Only after measured transfer improves, start coding boss-AI policy changes.
