#!/usr/bin/env python3
"""Release smoke checks for key gameplay and integration invariants."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def parse_moves(path: Path) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    pat = re.compile(
        r"^\s*move\s+([A-Z0-9_]+),\s*([A-Z0-9_]+),\s*(\d+),\s*([A-Z0-9_]+),\s*(\d+),\s*(\d+),\s*(\d+)"
    )
    for line in path.read_text(encoding="utf-8").splitlines():
        m = pat.match(line)
        if not m:
            continue
        name, effect, power, move_type, acc, pp, chance = m.groups()
        out[name] = {
            "effect": effect,
            "power": power,
            "type": move_type,
            "accuracy": acc,
            "pp": pp,
            "chance": chance,
        }
    return out


def parse_base_stats(path: Path) -> tuple[list[int], tuple[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    stats_pat = re.compile(r"^\s*db\s+(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)")
    type_pat = re.compile(r"^\s*db\s+([A-Z0-9_]+),\s*([A-Z0-9_]+)\s*;\s*type\b")
    stats: list[int] | None = None
    types: tuple[str, str] | None = None
    for line in lines:
        if stats is None:
            m = stats_pat.match(line)
            if m:
                stats = [int(x) for x in m.groups()]
                continue
        if types is None:
            m = type_pat.match(line)
            if m:
                types = (m.group(1), m.group(2))
                continue
        if stats is not None and types is not None:
            break
    if stats is None or types is None:
        fail(f"could not parse stats/types from {path}")
    return stats, types


def parse_levelup_block(path: Path, label: str) -> dict[str, int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    in_block = False
    out: dict[str, int] = {}
    move_pat = re.compile(r"^\s*db\s+(\d+),\s*([A-Z0-9_]+)\s*$")
    for line in lines:
        if line.strip() == f"{label}:":
            in_block = True
            continue
        if not in_block:
            continue
        if line.strip() == "db 0 ; no more level-up moves":
            return out
        m = move_pat.match(line)
        if m:
            level = int(m.group(1))
            move = m.group(2)
            out[move] = level
    fail(f"did not find level-up terminator for {label}")
    return {}


def check_levelup_move_order(path: Path) -> None:
    current_label: str | None = None
    in_moves = False
    previous_level: int | None = None
    previous_line: int | None = None
    label_pat = re.compile(r"^([A-Za-z0-9_]+EvosAttacks):\s*$")
    move_pat = re.compile(r"^db\s+(\d+),\s*[A-Z0-9_]+\b")

    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        label_match = label_pat.match(raw)
        if label_match:
            current_label = label_match.group(1)
            in_moves = False
            previous_level = None
            previous_line = None
            continue

        if current_label is None:
            continue

        code = raw.split(";", 1)[0].strip()
        if not code:
            continue

        if code.startswith("db 0"):
            if in_moves:
                current_label = None
                in_moves = False
            else:
                in_moves = True
                previous_level = None
                previous_line = None
            continue

        if not in_moves:
            continue

        move_match = move_pat.match(code)
        if not move_match:
            continue

        level = int(move_match.group(1))
        if previous_level is not None and level < previous_level:
            fail(
                f"{current_label}: level-up moves descend at line {line_no}: "
                f"Lv{level} follows Lv{previous_level} from line {previous_line}"
            )
        previous_level = level
        previous_line = line_no


def require_text(path: Path, needle: str) -> None:
    text = path.read_text(encoding="utf-8")
    if needle not in text:
        fail(f"missing '{needle}' in {path}")


def require_ordered_text(path: Path, needles: tuple[str, ...], label: str) -> None:
    text = path.read_text(encoding="utf-8")
    cursor = -1
    for needle in needles:
        next_cursor = text.find(needle, cursor + 1)
        if next_cursor == -1:
            fail(f"{label}: missing or out-of-order '{needle}' in {path}")
        cursor = next_cursor


def parse_item_constants(path: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    in_items = False
    value = 0
    const_pat = re.compile(r"^\s*const\s+([A-Z0-9_]+)\b")
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "const_def":
            in_items = True
            value = 0
            continue
        if not in_items:
            continue
        if line.startswith("DEF NUM_ITEMS"):
            return out
        m = const_pat.match(line)
        if not m:
            continue
        out[m.group(1)] = value
        value += 1
    fail(f"could not parse item constants from {path}")
    return {}


def parse_item_names(path: Path) -> dict[int, str]:
    out: dict[int, str] = {}
    in_names = False
    item_id = 1
    name_pat = re.compile(r'^\s*li\s+"([^"]+)"')
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "ItemNames::":
            in_names = True
            continue
        if not in_names:
            continue
        if "assert_list_length NUM_ITEMS" in line:
            return out
        m = name_pat.match(line)
        if not m:
            continue
        out[item_id] = m.group(1)
        item_id += 1
    fail(f"could not parse item names from {path}")
    return {}


def parse_key_item_attributes(path: Path) -> set[str]:
    out: set[str] = set()
    item: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("; "):
            item = stripped[2:].split()[0]
            continue
        if stripped.startswith("item_attribute"):
            if item is not None and "KEY_ITEM" in stripped:
                out.add(item)
            item = None
    if not out:
        fail(f"could not parse key item attributes from {path}")
    return out


def parse_equ(path: Path, name: str) -> int:
    pat = re.compile(rf"^\s*DEF\s+{re.escape(name)}\s+EQU\s+(\d+)\b")
    for line in path.read_text(encoding="utf-8").splitlines():
        m = pat.match(line)
        if m:
            return int(m.group(1))
    fail(f"could not parse {name} from {path}")
    return 0


def check_documented_gold_silver_bugfixes() -> None:
    require_ordered_text(
        ROOT / "data/text/common_3.asm",
        (
            "_CoinCaseCountText::",
            '\ttext "Coins:"',
            "\ttext_end",
        ),
        "Coin Case count text terminates without fallthrough",
    )
    require_ordered_text(
        ROOT / "engine/events/halloffame.asm",
        (
            "HallOfFame::",
            "\tld a, [wSavedAtLeastOnce]\n\tand a\n\tjr nz, .saved",
            "\tfarcall ErasePreviousSave\n.saved",
        ),
        "Hall of Fame clears previous save before first-save entry",
    )
    require_text(
        ROOT / "engine/events/lucky_number.asm",
        "\tcp NUM_BOXES\n\tjr c, .BoxesLoop",
    )
    require_text(
        ROOT / "data/text/battle.asm",
        'PresentFailedText:\n\ttext "<TARGET>"\n\tline "refused the gift!"',
    )
    require_ordered_text(
        ROOT / "engine/events/overworld.asm",
        (
            ".TrySurf:",
            "\tcall CheckDirection\n\tjr c, .cannotsurf",
            "\tfarcall CheckFacingObject\n\tjr c, .cannotsurf",
        ),
        "Surf checks facing object before starting",
    )
    require_text(
        ROOT / "data/maps/maps.asm",
        "\tmap CeruleanGym, TILESET_PORT, INDOOR, LANDMARK_CERULEAN_CITY, MUSIC_GYM, TRUE, PALETTE_DAY, FISHGROUP_NONE",
    )
    require_text(
        ROOT / "maps/Route15.asm",
        'Route15SignText:\n\ttext "ROUTE 15"',
    )


def check_no_stale_reward_receipt_texts() -> None:
    stale_receipt_pat = re.compile(
        r"^(?P<label>[A-Za-z0-9_]*Received(?:TM|HM)[A-Za-z0-9_]*):\s*;\s*unreferenced\b"
    )
    stale: list[str] = []
    for path in sorted((ROOT / "maps").glob("*.asm")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = stale_receipt_pat.match(line)
            if match:
                stale.append(f"{path.relative_to(ROOT)}:{line_no}:{match.group('label')}")
    if stale:
        fail("stale unreferenced reward receipt text labels: " + ", ".join(stale))


def check_phone_delete_guard_refreshes_flags() -> None:
    require_ordered_text(
        ROOT / "engine/phone/phone.asm",
        (
            "CheckCanDeletePhoneNumber:",
            "\tld a, c\n\tcall GetCallerTrainerClass\n\tld a, c\n\tand a\n\tret nz",
            "\tcp PHONECONTACT_MOM\n\tret z\n\tcp PHONECONTACT_ELM\n\tret z",
        ),
        "Pokegear phone deletion refreshes trainer-class flags",
    )


def check_move_reorder_refreshes_battle_mode_flags() -> None:
    require_ordered_text(
        ROOT / "engine/pokemon/mon_menu.asm",
        (
            "\tcall .copy_move\n\tld a, [wBattleMode]\n\tand a\n\tjr z, .swap_moves",
        ),
        "Move reorder tests battle mode with fresh flags",
    )


def main() -> int:
    moves = parse_moves(ROOT / "data/moves/moves.asm")
    expected_moves = {
        "CUT": {"effect": "EFFECT_NORMAL_HIT", "power": "70", "accuracy": "100", "pp": "30"},
        "FIRE_SPIN": {"effect": "EFFECT_TRAP_TARGET", "power": "25", "accuracy": "85", "pp": "10"},
        "MUD_SLAP": {"effect": "EFFECT_ACCURACY_DOWN_HIT", "power": "30", "accuracy": "100", "pp": "10"},
    }
    for move, checks in expected_moves.items():
        if move not in moves:
            fail(f"missing move {move}")
        for key, expected in checks.items():
            actual = moves[move][key]
            if actual != expected:
                fail(f"{move} {key}: expected {expected}, got {actual}")
    print("PASS: key move table checks")

    expected_species = {
        "meganium.asm": ([110, 82, 100, 80, 83, 100], ("GRASS", "GRASS")),
        "typhlosion.asm": ([78, 84, 78, 100, 130, 85], ("FIRE", "NORMAL")),
        "feraligatr.asm": ([85, 105, 100, 87, 95, 83], ("WATER", "FIGHTING")),
    }
    for filename, (expected_stats, expected_types) in expected_species.items():
        stats, types = parse_base_stats(ROOT / "data/pokemon/base_stats" / filename)
        if stats != expected_stats:
            fail(f"{filename} stats mismatch: expected {expected_stats}, got {stats}")
        if types != expected_types:
            fail(f"{filename} types mismatch: expected {expected_types}, got {types}")
    print("PASS: starter final evolution stat/type checks")

    evos_path = ROOT / "data/pokemon/evos_attacks.asm"
    check_levelup_move_order(evos_path)
    print("PASS: level-up move order checks")

    expected_level_moves = {
        "MeganiumEvosAttacks": {"HEAL_BELL": 33, "SOLARBEAM": 41},
        "TyphlosionEvosAttacks": {"FIRE_BLAST": 37, "ANCIENTPOWER": 45},
        "FeraligatrEvosAttacks": {"DRAGON_DANCE": 38, "HYDRO_PUMP": 45},
        "AriadosEvosAttacks": {"SPIKES": 22, "SPIDER_WEB": 37},
        "YanmaEvosAttacks": {"LEECH_LIFE": 17, "WING_ATTACK": 25},
    }
    for label, checks in expected_level_moves.items():
        learned = parse_levelup_block(evos_path, label)
        for move, level in checks.items():
            actual = learned.get(move)
            if actual != level:
                fail(f"{label} {move}: expected Lv{level}, got {actual}")
    print("PASS: key learnset checks")

    require_text(ROOT / "main.asm", 'INCLUDE "engine/events/move_reminder.asm"')
    require_text(ROOT / "main.asm", 'INCLUDE "engine/events/tm_tutor.asm"')
    require_text(ROOT / "main.asm", 'INCLUDE "engine/battle/ai/boss.asm"')
    require_text(ROOT / "data/events/special_pointers.asm", "add_special MoveReminder")
    print("PASS: core module integration checks")

    require_text(ROOT / "home/region.asm", "\tld a, [wPlayerMapY]\n\tadd $4\n\tld e, a")
    print("PASS: overworld XY compare offset check")

    require_text(
        ROOT / "engine/pokemon/move_mon.asm",
        "\tld a, MON_LEVEL\n\tcall GetPartyParamLocation\n\tld a, [hl]\n\tld [wCurPartyLevel], a",
    )
    print("PASS: NPC trade stat recompute level check")

    require_text(
        ROOT / "engine/link/link.asm",
        "\tld de, wLinkOTMail\n\tld bc, wLinkOTMailEnd - wLinkOTMail\n\tcall CopyBytes",
    )
    print("PASS: link trade mail receive bounds check")

    require_text(
        ROOT / "engine/battle/core.asm",
        "\tld a, [wMagikarpLength]\n\tcp 5\n\tjr nz, .CheckMagikarpArea",
    )
    require_text(
        ROOT / "engine/battle/core.asm",
        "\tld a, [wMapGroup]\n\tcp GROUP_LAKE_OF_RAGE\n\tjr nz, .Happiness",
    )
    require_text(
        ROOT / "engine/battle/core.asm",
        "\tld a, [wMagikarpLength]\n\tcp 3\n\tjr c, .GenerateDVs ; try again\n\tjr nz, .Happiness\n\tld a, [wMagikarpLength + 1]\n\tcp 4",
    )
    print("PASS: wild Magikarp size gate checks")

    check_documented_gold_silver_bugfixes()
    print("PASS: documented Gold/Silver bugfix checks")

    check_no_stale_reward_receipt_texts()
    print("PASS: stale reward receipt text checks")

    check_phone_delete_guard_refreshes_flags()
    print("PASS: phone deletion guard flag check")

    check_move_reorder_refreshes_battle_mode_flags()
    print("PASS: move reorder battle-mode flag check")

    require_ordered_text(
        ROOT / "engine/events/tm_tutor.asm",
        (
            "TMTutorTeachAnyTM:",
            "\tld a, [wCurItem]\n\tpush af\n\tld a, NO_ITEM\n\tld [wCurItem], a\n\tfarcall TeachTMHM\n\tjr c, .taught_restore_cur_item",
            "\tpop af\n\tld [wCurItem], a\n\tld a, 2\n\tld [wScriptVar], a",
            ".taught_restore_cur_item\n\tpop af\n\tld [wCurItem], a\n.taught\n\tld a, 1",
        ),
        "TM Tutor selected-item restore",
    )
    print("PASS: TM Tutor item-state restore check")

    item_constants = parse_item_constants(ROOT / "constants/item_constants.asm")
    item_names = parse_item_names(ROOT / "data/items/names.asm")
    expected_tool_names = {
        "PRUNERS": "PRUNERS",
        "SKY_PASS": "SKY PASS",
        "SURFBOARD": "SURFBOARD",
        "POWER_GLOVE": "POWER GLOVE",
        "LANTERN": "LANTERN",
        "WHIRL_KIT": "WHIRL KIT",
        "CLIMB_GEAR": "CLIMB GEAR",
    }
    seen_tool_names: dict[str, str] = {}
    reverse_items = {value: name for name, value in item_constants.items()}
    for item, expected_name in expected_tool_names.items():
        item_id = item_constants.get(item)
        if item_id is None:
            fail(f"missing item constant {item}")
        actual_name = item_names.get(item_id)
        if actual_name != expected_name:
            fail(f"{item} name slot: expected {expected_name}, got {actual_name}")
        seen_tool_names[expected_name] = reverse_items[item_id]
    for item_id, name in item_names.items():
        if name not in expected_tool_names.values():
            continue
        owner = reverse_items.get(item_id, f"${item_id:02x}")
        if owner != seen_tool_names[name]:
            fail(f"{name} appears in wrong item slot {owner}")
    key_items = parse_key_item_attributes(ROOT / "data/items/attributes.asm")
    max_key_items = parse_equ(ROOT / "constants/item_data_constants.asm", "MAX_KEY_ITEMS")
    if len(key_items) > max_key_items:
        fail(f"key item pocket capacity: {len(key_items)} key items exceeds MAX_KEY_ITEMS {max_key_items}")
    for item in expected_tool_names:
        if item not in key_items:
            fail(f"{item} is not assigned to the key item pocket")
        require_text(
            ROOT / "data/items/attributes.asm",
            f"; {item}\n\titem_attribute 0, HELD_NONE, 0, CANT_TOSS, KEY_ITEM, ITEMMENU_CLOSE, ITEMMENU_NOUSE",
        )
    for name in ("TM51", "TM52", "TM53", "TM54", "TM55", "TM56", "TM57"):
        require_text(ROOT / "data/items/names.asm", f'\tli "{name}"')
    require_text(
        ROOT / "maps/NationalPark.asm",
        '\tpara "There are {d:NUM_TM_HM} kinds"\n\tline "of TM."',
    )
    require_text(
        ROOT / "maps/Route14.asm",
        'BirdKeeperRoyAfterBattleText:\n\ttext "You can use FLY"\n\tline "with a SKY PASS?"',
    )
    require_text(
        ROOT / "maps/SproutTower1F.asm",
        'SproutTower1FSage1Text:\n\ttext "Only if you reach"\n\tline "the top will you"\n\tcont "obtain a tool."',
    )
    for label, text in (
        ("Surf prompt", '_AskSurfText::\n\ttext "The water is calm."\n\tline "Use SURFBOARD?"'),
        ("Waterfall prompt", '_AskWaterfallText::\n\ttext "Use CLIMB GEAR?"'),
        ("Strength prompt", '_AskStrengthText::\n\ttext "This boulder looks"\n\tline "movable."\n\n\tpara "Use POWER GLOVE?"'),
        ("Whirlpool prompt", '_AskWhirlpoolText::\n\ttext "A whirlpool is in"\n\tline "the way."\n\n\tpara "Use WHIRL KIT?"'),
        ("Cut prompt", '_AskCutText::\n\ttext "This tree can be"\n\tline "CUT."\n\n\tpara "Use PRUNERS?"'),
        ("Power Glove boulder text", '_PowerGloveMoveBoulderText::\n\ttext "The POWER GLOVE"\n\tline "can move boulders."'),
    ):
        require_text(ROOT / "data/text/common_2.asm", text)
    for rel_path, text in (
        (
            "maps/VioletGym.asm",
            '\tpara "It also enables"\n\tline "your LANTERN to"\n\n\tpara "use FLASH in"\n\tline "dark places."',
        ),
        (
            "maps/AzaleaGym.asm",
            '\tpara "PRUNERS will be"\n\tline "able to CUT"\n\n\tpara "outside"\n\tline "of battle too."',
        ),
        (
            "maps/GoldenrodGym.asm",
            '\ttext "PLAINBADGE lets"\n\tline "the POWER GLOVE"\n\n\tpara "move boulders"\n\tline "outside battle."',
        ),
        (
            "maps/EcruteakGym.asm",
            '\tpara "Also, with FOG-"\n\tline "BADGE, SURFBOARD"\n\n\tpara "can cross water"\n\tline "anytime."',
        ),
        (
            "maps/CianwoodGym.asm",
            '\tpara "It also lets the"\n\tline "SKY PASS use FLY"\n\n\tpara "outside battle."',
        ),
        (
            "maps/MahoganyGym.asm",
            '\tpara "It also lets the"\n\tline "WHIRL KIT clear"\n\tcont "real whirlpools."',
        ),
        (
            "maps/DragonsDenB1F.asm",
            '\ttext "RISINGBADGE lets"\n\tline "CLIMB GEAR scale"\n\n\tpara "waterfalls."',
        ),
        (
            "maps/CianwoodCity.asm",
            '\tpara "It would be much"\n\tline "easier with a"\n\n\tpara "SKY PASS…"',
        ),
        (
            "maps/CianwoodCity.asm",
            '\ttext "But you can\'t use"\n\tline "SKY PASS without"\n\tcont "this GYM BADGE."',
        ),
        (
            "maps/OlivineCafe.asm",
            '\tpara "BADGE to use the"\n\tline "POWER GLOVE."',
        ),
        (
            "maps/OlivineCafe.asm",
            '\tpara "You\'ll need a"\n\tline "WHIRL KIT to get"\n\n\tpara "over whirlpools."',
        ),
    ):
        require_text(ROOT / rel_path, text)
    require_ordered_text(
        ROOT / "engine/events/overworld.asm",
        (
            "TrySurfOW::",
            "\tld a, SURFBOARD\n\tcall CheckFieldTool\n\tjr nc, .quit",
            "TryWaterfallOW::",
            "\tld a, CLIMB_GEAR\n\tcall CheckFieldTool\n\tjr nc, .failed",
            "TryStrengthOW:",
            "\tld a, POWER_GLOVE\n\tcall CheckFieldTool\n\tjr nc, .nope",
            "TryWhirlpoolOW::",
            "\tld a, WHIRL_KIT\n\tcall CheckFieldTool\n\tjr nc, .failed",
            "TryCutOW::",
            "\tld a, PRUNERS\n\tcall CheckFieldTool\n\tjr nc, .cant_cut",
        ),
        "HM field tools replace overworld party-move checks",
    )
    require_ordered_text(
        ROOT / "engine/events/overworld.asm",
        (
            "CheckFieldTool:",
            "\tld [wCurItem], a\n\tld hl, wNumKeyItems\n\tcall CheckItem\n\tret c",
            "\tcall CheckLegacyFieldToolEvent\n\tret nc",
            "\tld a, 1\n\tld [wItemQuantityChange], a\n\tld hl, wNumItems\n\tcall ReceiveItem\n\tscf\n\tret",
            "CheckLegacyFieldToolEvent:",
        ),
        "legacy HM event fallback backfills missing field tools",
    )
    for item, label, event in (
        ("PRUNERS", ".cut", "EVENT_GOT_HM01_CUT"),
        ("SKY_PASS", ".fly", "EVENT_GOT_HM02_FLY"),
        ("SURFBOARD", ".surf", "EVENT_GOT_HM03_SURF"),
        ("POWER_GLOVE", ".strength", "EVENT_GOT_HM04_STRENGTH"),
        ("LANTERN", ".flash", "EVENT_GOT_HM05_FLASH"),
        ("WHIRL_KIT", ".whirlpool", "EVENT_GOT_HM06_WHIRLPOOL"),
        ("CLIMB_GEAR", ".waterfall", "EVENT_GOT_HM07_WATERFALL"),
    ):
        require_ordered_text(
            ROOT / "engine/events/overworld.asm",
            (
                f"\tcp {item}\n\tjr z, {label}",
                f"{label}\n\tld de, {event}",
            ),
            f"{item} legacy HM event maps to the matching field tool",
        )
    require_text(ROOT / "home/hm_moves.asm", "IsHMMove::\n\tand a\n\tret")
    require_text(
        ROOT / "data/text/common_3.asm",
        '_MoveCantForgetHMText::\n\ttext "That move can\'t"\n\tline "be forgotten here."',
    )
    require_text(
        ROOT / "engine/items/tmhm.asm",
        "\tld a, [wCurItem]\n\tand a\n\tjr z, .learned_move\n\n\tld c, HAPPINESS_LEARNMOVE",
    )
    require_ordered_text(
        ROOT / "engine/events/field_moves.asm",
        (
            "FlyFunction_InitGFX:",
            "\tld a, [wCurItem]\n\tcp SKY_PASS\n\tjr nz, .party_mon",
            "\tld a, PIDGEY\n\tjr .got_species",
            ".party_mon\n\tld a, [wCurPartyMon]",
            ".got_species\n\tld [wTempIconSpecies], a",
        ),
        "Sky Pass fly animation avoids stale party-mon icon",
    )
    require_ordered_text(
        ROOT / "engine/items/item_effects.asm",
        (
            "FieldToolEffect:",
            "\tld a, [wFieldMoveSucceeded]\n\tcp $1\n\tjr z, .done",
            "\tld a, $2\n.done\n\tld [wItemEffectSucceeded], a",
        ),
        "failed field-tool use is marked handled, not generic-Oak failure",
    )
    require_ordered_text(
        ROOT / "engine/events/overworld.asm",
        (
            ".UsedPowerGlove:",
            "\twritetext .UsePowerGloveText\n\twritetext .PowerGloveMoveBoulderText",
            ".PowerGloveMoveBoulderText:\n\ttext_far _PowerGloveMoveBoulderText",
        ),
        "Power Glove success text does not depend on party-mon name buffer",
    )
    require_ordered_text(
        ROOT / "engine/items/pack.asm",
        (
            ".Field:",
            "\tcall DoItemEffect\n\tld a, [wItemEffectSucceeded]\n\tand a\n\tjr z, .Oak",
            "\tcp $2\n\tjr z, .didnt_use_field_item",
            "\tld a, PACKSTATE_QUITRUNSCRIPT",
            ".didnt_use_field_item\n\txor a\n\tld [wItemEffectSucceeded], a",
            "\tldh [hBGMapMode], a\n\tcall Pack_InitGFX\n\tcall WaitBGMap_DrawPackGFX\n\tcall Pack_InitColors",
        ),
        "field-tool bag failure avoids duplicate generic text",
    )
    require_ordered_text(
        ROOT / "engine/overworld/select_menu.asm",
        (
            ".Overworld:",
            "\tld a, [wItemEffectSucceeded]\n\tcp 2\n\tjr z, ._handled_no_effect",
            "\tcp 1\n\tjr nz, ._cantuse",
            "\tld a, HMENURETURN_SCRIPT",
            "._handled_no_effect\n\tand a\n\tret",
        ),
        "registered field-tool failure avoids duplicate generic text",
    )
    for rel_path, item, tm, event, fail_branch in (
        ("maps/IlexForest.asm", "PRUNERS", "HM_CUT", "EVENT_GOT_HM01_CUT", ".Done"),
        ("maps/CianwoodCity.asm", "SKY_PASS", "HM_FLY", "EVENT_GOT_HM02_FLY", ".Done"),
        ("maps/DanceTheater.asm", "SURFBOARD", "HM_SURF", "EVENT_GOT_HM03_SURF", ".Done"),
        ("maps/OlivineCafe.asm", "POWER_GLOVE", "HM_STRENGTH", "EVENT_GOT_HM04_STRENGTH", ".Done"),
        ("maps/SproutTower3F.asm", "LANTERN", "HM_FLASH", "EVENT_GOT_HM05_FLASH", ".Done"),
        ("maps/TeamRocketBaseB2F.asm", "WHIRL_KIT", "HM_WHIRLPOOL", "EVENT_GOT_HM06_WHIRLPOOL", ".BagFull"),
        ("maps/IcePath1F.asm", "CLIMB_GEAR", "HM_WATERFALL", "EVENT_GOT_HM07_WATERFALL", ".Done"),
    ):
        require_ordered_text(
            ROOT / rel_path,
            (
                f"\tcheckitem {item}",
                f"\tverbosegiveitem {item}",
                f"\tiffalse {fail_branch}",
                f"\tverbosegiveitem {tm}",
                f"\tiffalse {fail_branch}",
                f"\tsetevent {event}",
            ),
            f"{item} reward gives field tool before converted TM and guards both gifts",
        )
    require_ordered_text(
        ROOT / "maps/CianwoodCity.asm",
        (
            "\tcheckevent EVENT_GOT_HM02_FLY\n\tiftrue .CheckLegacySkyPass",
            ".CheckLegacySkyPass:\n\tcheckitem SKY_PASS\n\tiftrue .GotFly",
            "\tverbosegiveitem SKY_PASS\n\tiffalse .Done\n\tpromptbutton\n\twritetext ChucksWifeFlySpeechText\n\tpromptbutton\n\tsjump .GotFly",
        ),
        "legacy Fly saves can revisit Chuck's wife for Sky Pass",
    )
    require_ordered_text(
        ROOT / "maps/SproutTower3F.asm",
        (
            "\tcheckevent EVENT_GOT_HM05_FLASH\n\tiftrue .CheckLegacyLantern",
            "\tcheckevent EVENT_BEAT_SAGE_LI\n\tiftrue .GiveFlash",
            "\tstartbattle\n\treloadmapafterbattle\n\tsetevent EVENT_BEAT_SAGE_LI\n\topentext\n.GiveFlash:",
        ),
        "Sage Li keeps battle-win state separate from Flash reward claim",
    )
    require_ordered_text(
        ROOT / "maps/SproutTower3F.asm",
        (
            "\tcheckevent EVENT_GOT_HM05_FLASH\n\tiftrue .CheckLegacyLantern",
            ".CheckLegacyLantern:\n\tcheckitem LANTERN\n\tiftrue .GotFlash",
            "\tverbosegiveitem LANTERN\n\tiffalse .Done\n\tpromptbutton\n\twritetext SageLiFlashExplanationText\n\twaitbutton\n\tsjump .Done",
        ),
        "legacy Flash saves can revisit Sage Li for Lantern",
    )
    print("PASS: HM field-tool and converted-TM checks")

    require_text(
        ROOT / "engine/debug/debug_room.asm",
        "\tpaged_value wDebugRoomItemID,       1, HM_WATERFALL, MASTER_BALL, .ItemNameString, DebugRoom_PrintItemName, FALSE",
    )
    require_text(
        ROOT / "engine/debug/debug_room.asm",
        "\tpaged_value wDebugRoomMonItem,          1,   HM_WATERFALL, MASTER_BALL,   DebugRoom_BoxStructStrings.Item,      DebugRoom_PrintItemName2,   FALSE",
    )
    print("PASS: debug item picker valid-item bound check")

    item_desc_path = ROOT / "data/items/descriptions.asm"
    for label, first_line, second_line in (
        ("TMVoucherDesc", "Redeem at DAY-CARE", "for 3 TM lessons."),
        ("ChoiceBandDesc", "Raises ATTACK;", "locks move. (HOLD)"),
        ("ChoiceSpecsDesc", "Raises SPCL.ATK;", "locks move. (HOLD)"),
        ("ChoiceScarfDesc", "Raises SPEED;", "locks move. (HOLD)"),
        ("AssaultVestDesc", "Raises SPCL.DEF;", "no status moves."),
        ("EvioliteDesc", "Unevolved only:", "DEF/SPCL.DEF up."),
        ("AirBalloonDesc", "Immune to GROUND", "until hit. (HOLD)"),
        ("ShellBellDesc", "Heals on damage", "dealt. (HOLD)"),
    ):
        require_text(
            item_desc_path,
            f'{label}:\n\tdb   "{first_line}"\n\tnext "{second_line}@"',
        )
    require_text(
        ROOT / "maps/DayCare.asm",
        'DayCareServicePamphletText:\n\ttext "DAY-CARE SERVICES"\n\tline "TM TUTOR:"\n\tcont "1 VOUCHER buys"\n\tcont "3 TM lessons."',
    )
    require_text(
        ROOT / "maps/Route34.asm",
        'DayCareSignText:\n\ttext "DAY-CARE"\n\n\tpara "Raise #MON,"\n\tline "TM lessons and"\n\tcont "old moves inside."',
    )
    require_ordered_text(
        ROOT / "maps/EarlsPokemonAcademy.asm",
        (
            'AcademyNotebookText:\n\ttext "It\'s a battle"\n\tline "notes booklet',
            '\tpara "JOHTO LEAGUE"\n\tline "uses SET rules."',
            '\tpara "Trainer battles:"\n\tline "no PACK breaks."',
            'AcademyNotebookText1:\n\ttext "GYM LEADERS"\n\tline "remember public"\n\tcont "moves."',
            '\tpara "Show THUNDERPUNCH,"\n\tline "and they may"\n\tcont "play around it."',
            'AcademyNotebookText2:\n\ttext "Type habits are"\n\tline "stronger now."',
            '\tpara "POISON may hurt"\n\tline "contact attackers."',
            '\tpara "GRASS may heal"\n\tline "between turns."',
            '\tpara "DRAGON can bend"\n\tline "matchups."',
            'AcademyNotebookText3:\n\ttext "Held items are"\n\tline "serious now."',
            '\tpara "Some boost stats"\n\tline "but lock moves."',
            '\tpara "Read ITEM text"\n\tline "before a GYM."',
        ),
        "Earl's Academy fair-hard notebook",
    )
    print("PASS: QoL communication text checks")

    require_ordered_text(
        ROOT / "engine/events/std_scripts.asm",
        (
            "PokecenterNurseScript:",
            "\twritetext NurseTakePokemonText\n\tpause 10\n\tturnobject LAST_TALKED, LEFT\n\tpause 5\n\tspecial HealParty",
            "\tspecial HealMachineAnim\n\tpause 15\n\tspecial RestartMapMusic\n\tturnobject LAST_TALKED, DOWN\n\tpause 5",
            "\twritetext NurseReturnPokemonText\n\tpause 10",
        ),
        "Pokemon Center pause trim",
    )
    repel_path = ROOT / "engine/events/repel.asm"
    require_ordered_text(
        repel_path,
        (
            "RepelWoreOffScript::",
            "\twritetext .RepelWoreOffText",
            "\tcheckflag ENGINE_BUG_CONTEST_TIMER",
            "\tiftrue .NoRenewal",
            "\tcheckitem MAX_REPEL",
            "\tiftrue .OfferMaxRepel",
            "\tcheckitem SUPER_REPEL",
            "\tiftrue .OfferSuperRepel",
            "\tcheckitem REPEL",
            "\tiftrue .OfferRepel",
            "\twaitbutton",
            "\tclosetext",
            "\tend",
            ".NoRenewal:",
            "\twaitbutton",
            "\tclosetext",
            "\tend",
        ),
        "Repel contest guard, no-item fallback, and priority",
    )
    for label, branch, item, steps in (
        ("MAX REPEL renewal", ".OfferMaxRepel:", "MAX_REPEL", "250"),
        ("SUPER REPEL renewal", ".OfferSuperRepel:", "SUPER_REPEL", "200"),
        ("REPEL renewal", ".OfferRepel:", "REPEL", "100"),
    ):
        require_ordered_text(
            repel_path,
            (
                branch,
                "\tyesorno",
                f"\ttakeitem {item}",
                f"\tsetval {steps}",
                "\twritemem wRepelEffect",
            ),
            label,
        )
    print("PASS: QoL script flow checks")

    print("ALL RELEASE SMOKE CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
