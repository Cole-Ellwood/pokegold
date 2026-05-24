# X-item + Evolution-stone Removal Plan — 2026-05-24

**Read-only audit; this file is a planning doc only.** Concrete site-by-
site replacement plan. Uses only items that already exist in
`constants/item_constants.asm` (verified). No new items, no new effects.
Companion to
[journal/2026-05-24_xitem_evostone_removal_audit.md](journal/2026-05-24_xitem_evostone_removal_audit.md).

## Context (2026-05-24 update)

- Codex shipped WRAM relief — 411 bytes freed in WRAMX bank 1 by
  cleaning audited padding bands and moving `wBoxNames` to a new
  `sBoxNames` in SRAM. `SAVE_FORMAT_VERSION` bumped 2 → 3 with v2
  migration in `engine/menus/save.asm`. Boss AI Reserve cap kept at
  140. Audit at `tools/audit/check_wramx_bank1_relief.py`. **Do not
  touch the files Codex modified for the WRAM work** (`ram/wram.asm`,
  `ram/sram.asm`, `constants/misc_constants.asm`,
  `engine/menus/save.asm`, `engine/menus/intro_menu.asm`,
  `engine/pokemon/bills_pc.asm`).
- This plan is unaffected: item constants, mart structure, item
  attributes/names/descriptions, item effects, and AI item-use are
  all untouched by the WRAM work.
- **User rule (2026-05-24): no buyable Rare Candy in any mart.**
  Bug Contest 1st prize Rare Candy is fine (NPC gift, not mart sale).
  PP UP at MartGoldenrod3F:120 stays — it has a natural cap (3 per
  move) and is analogous to existing buyable vitamins.

## In scope (13 items)
**X items (7):** `X_ATTACK`, `X_DEFEND`, `X_SPEED`, `X_SPECIAL`,
`X_ACCURACY`, `DIRE_HIT`, `GUARD_SPEC`.
**Evolution stones (6):** `MOON_STONE`, `FIRE_STONE`, `THUNDERSTONE`,
`WATER_STONE`, `LEAF_STONE`, `SUN_STONE`.
**Out of scope (keep):** `EVERSTONE` (breeding utility + level-up opt-out).

## Old-save bag handling

Items already in the player's bag in old saves stay in the bag. Strategy:

- **X-item slots: stub** — set un-buyable, un-usable. Old saves see
  ghost `"?????"` items that can be tossed. Engineering: simplest.
- **Stone slots: repurpose to Heart Scale clones** — keep the slots
  functional but make them call `HeartScaleEffect` (no effect outside
  the move-reminder context — `HEART_SCALE` itself is `KEY_ITEM`-ish
  per its attributes; verify). Old saves with 6 stones now have 6
  Heart Scales, which is a small free gift.

  Alternative for stones: stub same as X items, accept the ghost-bag
  ugliness. Cleaner code, uglier old-save bag.

  Default below assumes stub for everything (cheapest path). Heart-Scale
  conversion is a one-line change to the effect pointer per stone if
  you'd rather do that.

## Floor-level replacement themes

Two whole mart floors need a new identity. Verified existing themes:

- `MartGoldenrod4F` already vitamins (PROTEIN, IRON, CARBOS, CALCIUM,
  HP_UP) — so 3F can't reuse that.
- `MartCeladon5F1` already vitamins (same set).
- `MartGoldenrod3F` (was X items): **new theme — Battle-utility
  consumables (mid-tier).** Fills the PP-restore + premium-consumable
  gap that no other mid-Johto mart covers.
- `MartCeladon5F2` (was X items): **new theme — Premium consumables
  (late-tier).** Maxed-out versions of every category — the obvious
  endgame shopping mecca.

## Site-by-site replacement table

All replacements use existing item constants (verified via
`constants/item_constants.asm`).

### Marts (`data/items/marts.asm`)

| File:Line | Mart | Old | New | Notes |
| --- | --- | --- | --- | --- |
| `data/items/marts.asm:65` | MartViolet | X_DEFEND | `SUPER_POTION` | early-tier healing replaces stat-temp |
| `data/items/marts.asm:66` | MartViolet | X_ATTACK | `GREAT_BALL` | next-tier ball for the early route |
| `data/items/marts.asm:67` | MartViolet | X_SPEED | `BURN_HEAL` | rounds out status-heal coverage |
| `data/items/marts.asm:118` | MartGoldenrod3F | X_SPEED | `ETHER` | floor theme: battle-utility / PP |
| `data/items/marts.asm:119` | MartGoldenrod3F | X_SPECIAL | `ELIXER` | |
| `data/items/marts.asm:120` | MartGoldenrod3F | X_DEFEND | `PP_UP` | |
| `data/items/marts.asm:121` | MartGoldenrod3F | X_ATTACK | `HYPER_POTION` | user rule 2026-05-24: no buyable Rare Candy. Mid-tier healing fits the floor theme without duplicating anything already on the floor. |
| `data/items/marts.asm:122` | MartGoldenrod3F | DIRE_HIT | `REVIVE` | |
| `data/items/marts.asm:123` | MartGoldenrod3F | GUARD_SPEC | `FULL_HEAL` | |
| `data/items/marts.asm:124` | MartGoldenrod3F | X_ACCURACY | `MAX_REPEL` | |
| `data/items/marts.asm:225` | MartBlackthorn | X_DEFEND | `MAX_REVIVE` | late-Johto tier |
| `data/items/marts.asm:226` | MartBlackthorn | X_ATTACK | `FULL_RESTORE` | |
| `data/items/marts.asm:260` | MartCerulean | X_DEFEND | `REVIVE` | mid-Kanto |
| `data/items/marts.asm:261` | MartCerulean | X_ATTACK | `ICE_HEAL` | |
| `data/items/marts.asm:262` | MartCerulean | DIRE_HIT | `MAX_REPEL` | |
| `data/items/marts.asm:342` | MartCeladon5F2 | X_ACCURACY | `MAX_ETHER` | floor theme: premium consumables |
| `data/items/marts.asm:343` | MartCeladon5F2 | GUARD_SPEC | `MAX_ELIXER` | |
| `data/items/marts.asm:344` | MartCeladon5F2 | DIRE_HIT | `MAX_REVIVE` | |
| `data/items/marts.asm:345` | MartCeladon5F2 | X_ATTACK | `FULL_RESTORE` | |
| `data/items/marts.asm:346` | MartCeladon5F2 | X_DEFEND | `FULL_HEAL` | |
| `data/items/marts.asm:347` | MartCeladon5F2 | X_SPEED | `MAX_REPEL` | |
| `data/items/marts.asm:348` | MartCeladon5F2 | X_SPECIAL | `MAX_POTION` | |
| `data/items/marts.asm:369` | MartSaffron | X_ATTACK | `FULL_RESTORE` | postgame tier |
| `data/items/marts.asm:370` | MartSaffron | X_DEFEND | `MAX_REVIVE` | |

### Mom's phone (`data/items/mom_phone.asm`)

| File:Line | Trigger | Old | New | Notes |
| --- | --- | --- | --- | --- |
| `data/items/mom_phone.asm:20` | money ≥ 15000, cost 3000 | MOON_STONE | `NUGGET` | matches "Mom found something shiny" vibe; saleable for ~5000 so the player breaks even ish |

### Ground items + hidden items (`maps/*.asm`)

| File:Line | Type | Old | New | Notes |
| --- | --- | --- | --- | --- |
| `maps/SproutTower2F.asm:37` | itemball | X_DEFEND | `ANTIDOTE` | early Johto, route theme |
| `maps/UnionCave1F.asm:79` | itemball | X_ATTACK | `ESCAPE_ROPE` | cave-appropriate |
| `maps/UnionCaveB1F.asm:63` | itemball | X_DEFEND | `AWAKENING` | caves with sleep mons |
| `maps/Route46.asm:123` | itemball | DIRE_HIT | `ETHER` | utility consumable |
| `maps/BurnedTower1F.asm:147` | itemball X_SPEED, 1 | X_SPEED | `SUPER_POTION` | mid-Johto tier; keep quantity 1 |
| `maps/MountMortar1FOutside.asm:14` | itemball | GUARD_SPEC | `SUPER_REPEL` | cave repellent |
| `maps/WhirlIslandSW.asm:10` | itemball | GUARD_SPEC | `MAX_POTION` | late-Johto cave |
| `maps/Route45.asm:220` | itemball | X_SPECIAL | `MAX_REPEL` | Silver Cave approach |
| `maps/TohjoFalls.asm:10` | itemball | MOON_STONE | `NUGGET` | treasure-shape replacement |
| `maps/MountMoonSquare.asm:76` | hiddenitem | MOON_STONE | `BIG_PEARL` | Mon-night Clefairy event keeps treasure flavor |
| `maps/RockTunnel1F.asm:17` | hiddenitem | X_ACCURACY | `STARDUST` | Rock Tunnel = cave treasure |
| `maps/RockTunnel1F.asm:20` | hiddenitem | X_DEFEND | `NUGGET` | matches cave-treasure theme |
| `maps/Route2.asm:56` | itemball | DIRE_HIT | `SUPER_POTION` | Kanto route mid-tier |
| `maps/UndergroundPath.asm:10` | hiddenitem | X_SPECIAL | `MAX_ETHER` | hidden = premium |
| `maps/VictoryRoad.asm:110` | itemball | X_SPECIAL | `FULL_RESTORE` | endgame approach |
| `maps/TeamRocketBaseB1F.asm:538` | itemball | X_ACCURACY | `REVIVE` | dungeon healing |
| `maps/TeamRocketBaseB3F.asm:208` | itemball | DIRE_HIT | `FULL_HEAL` | pre-boss prep |
| `maps/SilverCaveRoom1.asm:15` | itemball | X_ACCURACY | `MAX_REVIVE` | postgame tier |
| `maps/SilverCaveRoom1.asm:21` | hiddenitem | DIRE_HIT | `MAX_ELIXER` | postgame hidden = premium |

### NPC gifts — Bill's Grandfather (`maps/BillsHouse.asm`)

| File:Line | Old | New | Notes |
| --- | --- | --- | --- |
| `maps/BillsHouse.asm:132` | LEAF_STONE | `HEART_SCALE` | move-relearner currency fits "old Pokémon enthusiast" |
| `maps/BillsHouse.asm:143` | WATER_STONE | `HEART_SCALE` | |
| `maps/BillsHouse.asm:154` | FIRE_STONE | `HEART_SCALE` | |
| `maps/BillsHouse.asm:163` | THUNDERSTONE | `HEART_SCALE` | |

(Line 121 EVERSTONE stays.) Alternative if 4× Heart Scale feels too
samey: cycle `HEART_SCALE`, `RARE_CANDY`, `PP_UP`, `MAX_ELIXER`.

### Special events

| File:Line | Event | Old | New | Notes |
| --- | --- | --- | --- | --- |
| `engine/events/std_scripts.asm:351` | Bug Contest 1st prize (give) | SUN_STONE | `RARE_CANDY` | high-value postgame-worthy prize |
| `maps/Route36NationalParkGate.asm:250` | Bug Contest 1st (re-offer) | SUN_STONE | `RARE_CANDY` | must match above |
| `engine/events/std_scripts.asm:348` | Bug Contest 1st (name string) | SUN_STONE | `RARE_CANDY` | the `getitemname STRING_BUFFER_4, SUN_STONE` line — match the giveitem |
| `engine/events/std_scripts.asm:374` | Bug Contest event flag | `EVENT_CONTEST_OFFICER_HAS_SUN_STONE` | (rename only, e.g. `EVENT_CONTEST_OFFICER_HAS_FIRST_PRIZE`) or leave the name — flag is positional too |

The Bug Contest 2nd-prize (EVERSTONE, lines 356/359/380) stays.

## Data-layer cleanup (engine + data files)

Done once, no per-site work after this.

### `constants/item_constants.asm`

For each of the 13 in-scope items, replace the `const` line with a
comment + reserved placeholder. **Do not delete or reorder lines.**
Pattern:
```
- 	const X_ATTACK     ; 31
+ 	const RESERVED_31  ; 31 — was X_ATTACK, see journal/2026-05-24_xitem_evostone_removal_plan.md
```
(Or keep the original name with a comment marker like `; UNUSED`.)
Either works; the constant just needs to remain at the same numeric
slot.

### `data/items/names.asm`

Same positional rule. 13 lines (10, 24, 25, 26, 35, 36, 43, 46, 51, 53,
54, 55, 171). Stub each to `li "?????"` for the X-item slots; for the
stone slots either `li "?????"` or, if repurposing to Heart Scale,
`li "HEART SCALE"` (but this collides with the real HEART_SCALE name —
prefer `li "?????"` even on repurposed slots).

### `data/items/attributes.asm`

13 attribute rows (lines 25-26, 53-54, 55-56, 57-58, 75-76, 77-78,
91-92, 97-98, 107-108, 111-112, 113-114, 115-116, 347-348). Replace
each row with:
```
item_attribute 0, HELD_NONE, 0, CANT_SELECT, ITEM, ITEMMENU_NOUSE, ITEMMENU_CLOSE
```
This makes the slot exist (positional) but un-buyable in marts and
un-usable from the bag.

### `data/items/descriptions.asm`

Two parts:
1. **Pointer table** (lines 11, 25, 26, 27, 36, 37, 44, 47, 52, 54, 55,
   56, 172): leave the `dw <name>Desc` rows in place but point all 13
   to a single shared stub label `dw UnusedItemDesc`.
2. **Description bodies** (lines 290-292, 346-348, 350-352, 354-356,
   389-391, 393-395, 421-423, 433-435, 452-454, 459-461, 463-465,
   467-469, 921-923): delete all 13 bodies, add one stub:
   ```
   UnusedItemDesc:
       text "An unused item."
       next "Sell or toss."
       done
   ```
   Saves ~500 bytes of description text.

### `engine/items/item_effects.asm`

1. **Effect-pointer table** (lines 24, 38, 39, 40, 49, 50, 57, 60, 65,
   67, 68, 69): repoint all 13 to a single shared `NoEffect` handler
   (probably already exists — grep `ItemEffects` table for the noop
   entry). All 13 become "Won't have any effect."
2. **Effect bodies:**
   - `EvoStoneEffect` (1116-1145): **KEEP** — `EVERSTONE` still uses
     it.
   - `XAccuracyEffect` (2085-2090, ~45 bytes): **DELETE**.
   - `GuardSpecEffect` (2107-2112, ~45 bytes): **DELETE**.
   - `DireHitEffect` (2114-2119, ~45 bytes): **DELETE**.
   - `XItemEffect` (2121-2150, ~225 bytes): **DELETE**.
3. `data/items/x_stats.asm`: **DELETE entire file** (~28 bytes table)
   and remove its `INCLUDE` from `item_effects.asm` line 2153.

### `engine/battle/ai/items.asm`

Delete the 7 jump-table entries at lines 288-294 (`dbw X_ACCURACY,
.XAccuracy` through `dbw X_SPECIAL, .XSpecial`) and the 7 handler
labels (`.XAccuracy`, `.GuardSpec`, `.DireHit`, `.XAttack`, `.XDefend`,
`.XSpeed`, `.XSpecial`) — lines 716, 723, 730, 736-752. ~126 bytes.

The AI never selects these items in this hack (user-confirmed) so no
behavioral risk.

### `constants/battle_constants.asm`

`SUBSTATUS_X_ACCURACY` is now dead. The bit position can stay (bit
position constants are essentially free) but mark it
`; RESERVED_UNUSED — was X_ACCURACY item, removed 2026-05-24`. The
substatus byte itself is shared with other live bits, so don't
attempt to reclaim it.

## Phase order (recommended)

**Phase 0 — pre-flight.** Read this plan + the audit. Decide:
1. Stub the 6 stones, or repurpose to Heart Scale? (default: stub)
2. Bill's Grandpa: 4× Heart Scale, or 4 different items? (default: 4×)
3. Any taste overrides on the floor themes or specific replacements?

**Phase 1 — data layer (no taste required).** Stub the 13 items at
the constants/names/attributes/descriptions/effects/AI level. Build
should still link. Items in old-save bags become un-usable ghost
slots called `?????`. ~30 minutes of mechanical edits.

**Phase 2 — world swaps (taste-locked).** Apply the 47 site-level
replacements per the tables above:
- 24 mart lines
- 1 Mom's phone line
- 19 ground/hidden itemballs
- 4 Bill's Grandpa gifts
- 3 Bug Contest sites (give + re-offer + name-string)

Each is a 1-line constant swap. ~45 minutes if you're going down the
tables in order.

**Phase 3 — verification.**
1. `wsl -e bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make ...'` — confirm it links.
2. Grep for the 13 item constants — should only appear in their own
   const lines, attributes/names/descriptions stubs, the
   `EvoStoneEffect` body, and possibly a comment or two. Anywhere else
   = missed reference.
3. `python tools/audit/check_release_smoke.py` — release-floor audit.
4. Spot-check one save load: the `wItems` slot count in an existing
   save with X items should still be valid (positional preservation
   means the IDs still resolve).
5. Quick playtest: boot a new game, walk into Goldenrod Dept Store
   3F, confirm the new floor inventory shows.

**Phase 4 — optional.** Delete the dead engine code (`XItemEffect`
etc.) for ROM savings. Can be done at any point after Phase 1 ships.
~500 bytes recovered.

## ROM bank impact

Per `docs/generated/dev_index.md`, the tight ROM banks are 12/15/17/
1b/1e (all at 0 free). The bytes saved by this cleanup live in
different banks:
- `data/items/descriptions.asm` is in bank 0x6e (lots of free space
  already).
- `data/items/marts.asm`, `data/items/attributes.asm`, `data/items/
  names.asm` in bank 01 (also lots of room).
- `engine/items/item_effects.asm` in bank 01.
- `engine/battle/ai/items.asm` in bank 0b.

So the ROM relief is real (~500-1000 bytes saved net) but doesn't
solve the tight-bank pressure. Treat this as bookkeeping.

## Open taste calls (defaults committed; override if you disagree)

1. **Stub vs repurpose stones.** Default: stub. Faster, ugly old-save
   bag.
2. **Bill's Grandpa: 4× Heart Scale, or 4 different items?** Default:
   4× Heart Scale (uniform, fits Grandpa-the-enthusiast).
3. **Bug Contest 1st prize: Rare Candy.** Default committed.
4. **Mom's Moon Stone → Nugget.** Default committed.
5. **Goldenrod 3F theme: PP/utility consumables.** Default committed.
6. **Celadon 5F2 theme: premium consumables.** Default committed.
7. **EVERSTONE: keep.** Default committed.
8. **Ground items: tier-matched replacements.** Default committed
   per the table.
