# X-item + Evolution-stone Removal Audit — 2026-05-24

**Read-only audit.** User wants to remove X items and evolution stones
since (a) X items aren't usable in trainer battles in this hack, and
(b) all stone evolutions have already been converted to level-up.
This file enumerates every reference site so the cleanup can be planned
in one pass.

## Item scope

**X items (7):** `X_ATTACK`, `X_DEFEND`, `X_SPEED`, `X_SPECIAL`,
`X_ACCURACY`, `DIRE_HIT`, `GUARD_SPEC`.

**Evolution stones (6):** `MOON_STONE`, `FIRE_STONE`, `THUNDERSTONE`,
`WATER_STONE`, `LEAF_STONE`, `SUN_STONE`.

**EVERSTONE (flagged design call, NOT in scope unless approved):** keeps
its breeding side effect (passes mother's species in Gen 2) and is a
"don't evolve this mon" lock for the player. If everyone's level-up,
Everstone still functions as a hold-item opt-out from a level-up at the
exact moment. Recommend keep; but flag for your call.

Verified clean (per `data/pokemon/evos_attacks.asm`): zero
`EVOLVE_ITEM <STONE>` entries remain. The user's premise holds.

## Data-layer references (the part the engine sees)

Removing the 13 items would touch six data files and three engine files.

### 1. `constants/item_constants.asm` — IDs
Lines 16, 30, 31, 32, 41, 42, 49, 52, 57, 59, 60, 61, 120 (EVERSTONE,
keep), 177. **WARNING:** Don't physically delete the `const` lines —
item IDs are positional, so removing one shifts every subsequent ID
and breaks every save. Replace each with `; const <NAME> ; <hex>
RESERVED_UNUSED` or a `db 0` filler entry so IDs stay stable. Save
format is otherwise untouched.

### 2. `data/items/names.asm` — display names
Lines 10, 24, 25, 26, 35, 36, 43, 46, 51, 53, 54, 55, 171. ~14 bytes
each (the `li "NAME"` macro). Same positional warning — replace with
`li "?????"` or a stub name, don't delete the row.

### 3. `data/items/attributes.asm` — price/pocket/menu
Lines 25-26, 53-54, 55-56, 57-58, 75-76, 77-78, 91-92, 97-98, 107-108,
111-112, 113-114, 115-116, 347-348. ~7 bytes each. Same positional
warning. Cleanest path: set price 0, `CANT_SELECT`, `ITEMMENU_NOUSE`,
`ITEMMENU_CLOSE` — keeps the row, makes the item un-buyable and
un-usable.

### 4. `data/items/descriptions.asm` — pointer table + bodies
13 pointer rows (lines 11, 25, 26, 27, 36, 37, 44, 47, 52, 54, 55, 56,
172) + 13 description bodies (lines 290-292, 346-348, 350-352, 354-356,
389-391, 393-395, 421-423, 433-435, 452-454, 459-461, 463-465, 467-469,
921-923). The bodies can shrink to a one-line stub (e.g. `"NOT
USED@"`); the pointers must stay in place.

### 5. `engine/items/item_effects.asm`
- Effects-pointer table (lines 24, 38, 39, 40, 49, 50, 57, 60, 65, 67,
  68, 69): the 6 stones route to `EvoStoneEffect`, X items to their own
  effects. Repoint all 13 to a noop / "WONT_BLOCK_THIS_EFFECT_IS_GONE@"
  fail-message handler — same idiom as other no-op items.
- Effect bodies:
  - `EvoStoneEffect` (lines 1116-1145): **keep** — `EVERSTONE` is also
    routed here, and stones become a "doesn't work on this mon" path
    when no species matches.
  - `XAccuracyEffect` (2085-2090, ~45 bytes): remove
  - `GuardSpecEffect` (2107-2112, ~45 bytes): remove
  - `DireHitEffect` (2114-2119, ~45 bytes): remove
  - `XItemEffect` (2121-2150, ~225 bytes): remove (no other consumers)
  - `data/items/x_stats.asm` (~28 bytes): remove
- `SUBSTATUS_X_ACCURACY` bit (lines 2087, 2089): X-Accuracy is the only
  consumer of this substatus bit. Removing the item makes the bit dead;
  the `SUBSTATUS_*` constant in `constants/battle_constants.asm` can
  stay (it's a bit position, not a byte) and the slot is reusable for
  future features.

### 6. `engine/battle/ai/items.asm`
AI item-use jump table at lines 288-294 (7 entries × 3 bytes = 21
bytes) + their handlers (~105 bytes, lines 716, 723, 730, 736-752).
Boss/trainer AI never selects these items in this hack — confirmed by
user. Safe full removal.

### Data-layer byte savings

Rough total: ~1.0-1.5 KB of ROM, mostly description text and
`XItemEffect`/handler bodies. Banks affected: wherever `data/items/`,
`engine/items/`, and `engine/battle/ai/` link (mostly bank 01 for
descriptions, bank 0b for AI items). The tight ROM banks
(12/15/17/1b/1e at 0 free per `docs/generated/dev_index.md`) are NOT
the same banks, so this doesn't directly relieve them — but it's a
clean shed.

**Important: this is ROM savings, not WRAM. Doesn't affect the
WRAMX bank 1 audit.**

## World references — what needs a replacement chosen

### Marts (24 individual `db ITEM` rows across 6 mart definitions)

`data/items/marts.asm`:

| Mart | Lines | Items present | Suggested theme |
| --- | --- | --- | --- |
| `MartViolet` | 65, 66, 67 | X_DEFEND, X_ATTACK, X_SPEED | Status healers (Antidote / Awakening / Parlyz Heal) or Super Potion / Repel / Great Ball |
| `MartGoldenrod3F` | 118-124 | X_SPEED, X_SPECIAL, X_DEFEND, X_ATTACK, DIRE_HIT, GUARD_SPEC, X_ACCURACY (whole floor) | **Repurpose floor entirely.** Suggest: vitamin floor (HP_UP, PROTEIN, IRON, CARBOS, CALCIUM, ZINC, ...) — mid-game-appropriate, fits "enhancement" theme |
| `MartBlackthorn` | 225, 226 | X_DEFEND, X_ATTACK | Full Heal + Full Restore (late-game-appropriate) |
| `MartCerulean` | 260, 261, 262 | X_DEFEND, X_ATTACK, DIRE_HIT | Status healer trio (Antidote / Ice Heal / Awakening — fits water-route afflictions) |
| `MartCeladon5F2` | 342-348 | X_ACCURACY, GUARD_SPEC, DIRE_HIT, X_ATTACK, X_DEFEND, X_SPEED, X_SPECIAL (whole floor) | **Repurpose floor entirely.** Suggest: parallel vitamin floor or premium consumables (Rare Candy / Max Elixir / Max Revive / Full Restore) |
| `MartSaffron` | 369, 370 | X_ATTACK, X_DEFEND | Full Restore + Revive (postgame-appropriate) |

### `data/items/mom_phone.asm` — Mom's savings buy
Line 20: `momitem 15000, 3000, MOM_ITEM, MOON_STONE`. Once the
player banks 15,000, Mom auto-buys a Moon Stone for 3,000. Swap to a
small-flavor item (Nugget, Heart Scale, or Rare Candy).

### Ground items + hidden items (19 placements, verified by grep)

All confirmed in source. Each tied to a one-time `EVENT_*` flag.

| File | Line | Placement | Item | Region | Suggested replacement |
| --- | ---: | --- | --- | --- | --- |
| `maps/SproutTower2F.asm` | 37 | itemball | X_DEFEND | Johto early | Antidote / Awakening |
| `maps/UnionCave1F.asm` | 79 | itemball | X_ATTACK | Johto early | Super Potion |
| `maps/UnionCaveB1F.asm` | 63 | itemball | X_DEFEND | Johto early-mid | Full Heal |
| `maps/Route46.asm` | 123 | itemball | DIRE_HIT | Johto early-mid | Ether / Repel |
| `maps/BurnedTower1F.asm` | 147 | itemball X_SPEED, 1 | X_SPEED | Johto mid | Revive |
| `maps/MountMortar1FOutside.asm` | 14 | itemball | GUARD_SPEC | Johto mid | Nugget / Escape Rope |
| `maps/WhirlIslandSW.asm` | 10 | itemball | GUARD_SPEC | Johto mid | Hyper Potion |
| `maps/Route45.asm` | 220 | itemball | X_SPECIAL | Johto late | PP Up |
| `maps/TohjoFalls.asm` | 10 | itemball | MOON_STONE | Johto/Kanto bridge | Ultra Ball / Big Pearl |
| `maps/MountMoonSquare.asm` | 76 | hiddenitem | MOON_STONE | Kanto early (Mon-night gated) | Nugget |
| `maps/RockTunnel1F.asm` | 17 | hiddenitem | X_ACCURACY | Kanto early | Escape Rope |
| `maps/RockTunnel1F.asm` | 20 | hiddenitem | X_DEFEND | Kanto early | Nugget |
| `maps/Route2.asm` | 56 | itemball | DIRE_HIT | Kanto early | Hyper Potion |
| `maps/UndergroundPath.asm` | 10 | hiddenitem | X_SPECIAL | Kanto early | Max Ether |
| `maps/VictoryRoad.asm` | 110 | itemball | X_SPECIAL | E4 approach | Full Restore |
| `maps/TeamRocketBaseB1F.asm` | 538 | itemball | X_ACCURACY | Johto late | Revive |
| `maps/TeamRocketBaseB3F.asm` | 208 | itemball | DIRE_HIT | Johto late | Full Heal |
| `maps/SilverCaveRoom1.asm` | 15 | itemball | X_ACCURACY | Postgame | Max Elixir |
| `maps/SilverCaveRoom1.asm` | 21 | hiddenitem | DIRE_HIT | Postgame | Ultra Ball |

### NPC gifts — Bill's Grandfather (4 stones, sequential quest)

`maps/BillsHouse.asm`:

| Line | Item | Event flag | Notes |
| ---: | --- | --- | --- |
| 121 | EVERSTONE | `EVENT_GOT_EVERSTONE_FROM_BILLS_GRANDPA` | Out-of-scope (keep) |
| 132 | LEAF_STONE | `EVENT_GOT_LEAF_STONE_FROM_BILLS_GRANDPA` | Replace |
| 143 | WATER_STONE | `EVENT_GOT_WATER_STONE_FROM_BILLS_GRANDPA` | Replace |
| 154 | FIRE_STONE | `EVENT_GOT_FIRE_STONE_FROM_BILLS_GRANDPA` | Replace |
| 163 | THUNDERSTONE | `EVENT_GOT_THUNDERSTONE_FROM_BILLS_GRANDPA` | Replace |

This NPC is a sequential quest (show specific species → get a stone).
Since the stones are no longer evolution-relevant, the *flavor* of
"Grandpa rewards you with a stone matching the Pokémon" loses its
meaning. Two options:
1. **Replace with thematic TMs:** TM Energy Ball (Oddish→Leaf), TM Surf
   (Staryu→Water), TM Flamethrower (Vulpix/Growlithe→Fire), TM
   Thunderbolt (Pichu→Thunder). Preserves type flavor.
2. **Replace with Rare Candies × 4** to keep the "reward" feel without
   the now-flavorless stone shape.

User taste call. Option 1 preserves more world flavor.

### Special events

| Source | File | Line | Item | Suggested replacement |
| --- | --- | ---: | --- | --- |
| Bug Catching Contest 1st | `engine/events/std_scripts.asm` | 351 | SUN_STONE | Rare Candy or Exp. Share |
| Bug Catching Contest 1st (re-offer) | `maps/Route36NationalParkGate.asm` | 250 | SUN_STONE | Same as above |
| Bug Catching Contest 2nd | `engine/events/std_scripts.asm` | 359 | EVERSTONE | Out-of-scope (keep) |
| Bug Catching Contest 3rd | `engine/events/std_scripts.asm` | 367 | GOLD_BERRY | (not in our removal scope) |

**This is the source of "I have a sun stone from the bug contest"** —
the contest 1st-place prize is `SUN_STONE`, hardcoded in two places
(the std_script that gives it, plus the re-offer at the gate when the
inventory was full). Both need the same replacement.

## What does NOT need cleanup

Confirmed null sets via dedicated grep:
- **Phone scripts** (`data/phone/text/*`): no rematch-trainer or Liz/
  Anthony/Beverly/schoolboy reward gives any of these 13 items.
- **NPC trades** (`data/events/npc_trades.asm`): no trade returns any
  of these items.
- **Game Corner prizes**: no overlap with the 13.
- **Decoration shop, Bargain Shop, apricorn returns from Kurt**: no
  overlap.
- **Lucky Number Show**: checks Pokémon IDs, doesn't drop items.
- **Move Reminder / Move Deleter**: no item gating.
- **Daily NPCs** (Buena's Password, etc.): no overlap.

## Cleanup execution plan

Total reference touch points: **~50 placements** (24 mart rows + 19
ground/hidden + 4 Bill's gifts + 2 Bug Contest sites + Mom's phone),
plus the data-layer cleanup of constants/attributes/names/descriptions/
effects/AI tables.

Recommended ordering:
1. **Phase 1 (data layer, no taste required):** stub out attributes,
   names, descriptions, repoint effects-table to a no-op handler. Keep
   ID slots present (positional). Validates the build still links and
   the items become un-buyable / un-usable. Save format unchanged
   (slots preserved).
2. **Phase 2 (world placements, taste required):** swap the 24 mart
   rows + 19 ground/hidden + 5 NPC gift sites + 2 Bug Contest sites +
   Mom's phone with the replacements you pick. Each row is a one-line
   change to a constant in source; no migration code needed because
   item IDs are stable.
3. **Phase 3 (optional, removes engine code):** delete `XItemEffect`,
   `XAccuracyEffect`, `GuardSpecEffect`, `DireHitEffect`, `x_stats.asm`,
   `SUBSTATUS_X_ACCURACY` consumers, AI item-use entries. This frees
   ~500 bytes of ROM but isn't required if you're fine with dead code.

Save format implications: **none** if positional slots are preserved
(Phase 1 keeps IDs). The `EVENT_*` flags for the existing world
placements stay set in old saves — they refer to "the player already
picked up the item at this spot," and the replacement item picked up
in a new save just uses the same flag. No conflict.

## Open design questions for you

1. **Floor repurposing — Goldenrod 3F and Celadon 5F2.** Both are
   currently "all X items" floors. Suggest vitamin floor or premium
   consumables, but the taste call is yours. Vitamins are
   thematically clean ("enhancement" maps to "permanent stat
   investment") but might be too cheap if priced normally.
2. **Bill's Grandfather quest.** TMs by type (Option 1 above) preserve
   flavor but require choosing which TMs are tier-appropriate. Rare
   Candies × 4 are simpler but less interesting.
3. **EVERSTONE.** Recommend keep. Breeding utility is non-trivial in
   Gen 2 (passes mother's species; preserves move pools for breeding
   strats). And if a player wants to opt out of a level-up evolution,
   it's still functional. Confirm?
4. **Bug Contest 1st prize.** Rare Candy is the easy default;
   Exp. Share is rarer-feeling. Either fits the prize-shaped slot.
5. **Mom's Moon Stone.** A small-flavor item (Nugget / Heart Scale)
   keeps the "Mom found a thing on sale" vibe; Rare Candy upgrades
   the value but might feel weird from Mom.
