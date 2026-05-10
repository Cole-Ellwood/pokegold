#!/usr/bin/env python3
"""Release smoke checks for key gameplay and integration invariants."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MART_TERMINATORS = {"-1", "CANCEL"}


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


def parse_item_tokens(path: Path) -> set[str]:
    tokens = set(parse_item_constants(path))
    machine_pat = re.compile(r"^\s*add_(tm|hm)\s+([A-Z0-9_]+)\b")
    for line in path.read_text(encoding="utf-8").splitlines():
        m = machine_pat.match(line)
        if m:
            prefix, move = m.groups()
            tokens.add(f"{prefix.upper()}_{move}")
    return tokens


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


def check_elapsed_seconds_helper_refreshes_minute_flags() -> None:
    require_ordered_text(
        ROOT / "engine/overworld/time.asm",
        (
            "GetSecondsSinceIfLessThan60:",
            "\tld a, [wMinutesSince]\n\tand a\n\tjr nz, GetTimeElapsed_ExceedsUnitLimit",
            "\tld a, [wSecondsSince]\n\tret",
        ),
        "Seconds elapsed helper tests minutes with fresh flags",
    )


def check_bug_contest_exit_flow() -> None:
    require_ordered_text(
        ROOT / "engine/events/misc_scripts.asm",
        (
            "Script_AbortBugContest:",
            "\tcheckflag ENGINE_BUG_CONTEST_TIMER\n\tiffalse .finish",
            "\tsetflag ENGINE_DAILY_BUG_CONTEST\n\tspecial ContestReturnMons",
            ".finish\n\tend",
        ),
        "Bug Contest abort returns held party mons",
    )
    require_ordered_text(
        ROOT / "engine/events/std_scripts.asm",
        (
            "BugContestResultsScript:",
            "\tclearflag ENGINE_BUG_CONTEST_TIMER",
            "\tspecial BugContestJudging",
            "BugContestResults_FinishUp:",
            "\tcheckevent EVENT_LEFT_MONS_WITH_CONTEST_OFFICER\n\tiffalse BugContestResults_DidNotLeaveMons",
            "\twritetext ContestResults_ReturnPartyText\n\twaitbutton\n\tspecial ContestReturnMons",
            "BugContestResults_DidNotLeaveMons:\n\tspecial CheckPartyFullAfterContest",
        ),
        "Bug Contest results restore party before caught-mon placement",
    )
    require_ordered_text(
        ROOT / "engine/overworld/events.asm",
        (
            "WarpToSpawnPoint::",
            "\tres STATUSFLAGS2_SAFARI_GAME_F, [hl]",
            "\tres STATUSFLAGS2_BUG_CONTEST_TIMER_F, [hl]",
        ),
        "field-move spawn warp clears Bug Contest timer",
    )


def parse_map_label_first_code(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    labels: dict[str, str] = {}
    label_pat = re.compile(r"^([A-Za-z0-9_.]+):\s*$")
    for index, line in enumerate(lines):
        label_match = label_pat.match(line)
        if not label_match:
            continue
        for next_line in lines[index + 1 : index + 6]:
            code = next_line.split(";", 1)[0].strip()
            if code:
                labels[label_match.group(1)] = code
                break
    return labels


def check_map_event_script_shapes() -> None:
    for path in sorted((ROOT / "maps").glob("*.asm")):
        labels = parse_map_label_first_code(path)
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith("object_event"):
                parts = [part.strip() for part in line.split(",")]
                if len(parts) < 13:
                    continue
                event_type = parts[9]
                label = parts[11]
                first_code = labels.get(label, "")
                if event_type == "OBJECTTYPE_TRAINER" and not first_code.startswith("trainer "):
                    fail(
                        f"{path.relative_to(ROOT)}:{line_no}: "
                        f"trainer object points at non-trainer script {label}"
                    )
                if event_type == "OBJECTTYPE_ITEMBALL" and not first_code.startswith("itemball"):
                    fail(
                        f"{path.relative_to(ROOT)}:{line_no}: "
                        f"itemball object points at non-itemball script {label}"
                    )
                continue

            if not stripped.startswith("bg_event") or "BGEVENT_ITEM" not in line:
                continue
            parts = [part.strip() for part in line.split(",")]
            if len(parts) < 4:
                continue
            label = parts[3]
            first_code = labels.get(label, "")
            if not first_code.startswith("hiddenitem"):
                fail(f"{path.relative_to(ROOT)}:{line_no}: hidden item points at non-hiddenitem script {label}")


def parse_map_scene_scripts(path: Path) -> set[str]:
    scene_script_pat = re.compile(r"^\s*scene_script\s+[^,]+,\s*([A-Z0-9_]+)\b")
    scene_scripts: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        code = raw.split(";", 1)[0]
        scene_script_match = scene_script_pat.match(code)
        if scene_script_match:
            scene_scripts.add(scene_script_match.group(1))
    return scene_scripts


def parse_map_attribute_labels(path: Path) -> dict[str, str]:
    attr_pat = re.compile(r"^\s*map_attributes\s+([A-Za-z0-9_]+),\s*([A-Z0-9_]+),")
    labels: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        match = attr_pat.match(raw)
        if match:
            label, map_constant = match.groups()
            labels[map_constant] = label
    if not labels:
        fail(f"could not parse map attributes from {path}")
    return labels


def parse_map_dimensions(path: Path) -> dict[str, tuple[int, int]]:
    map_const_pat = re.compile(r"^\s*map_const\s+([A-Z0-9_]+),\s*(\d+),\s*(\d+)")
    dimensions: dict[str, tuple[int, int]] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        match = map_const_pat.match(raw)
        if match:
            map_constant, width_blocks, height_blocks = match.groups()
            dimensions[map_constant] = (int(width_blocks) * 2, int(height_blocks) * 2)
    if not dimensions:
        fail(f"could not parse map dimensions from {path}")
    return dimensions


def is_literal_scene_id(scene: str) -> bool:
    return re.fullmatch(r"(?:\d+|\$[0-9a-fA-F]+)", scene) is not None


def check_coord_events_use_counted_scene_scripts() -> None:
    coord_event_pat = re.compile(r"^\s*coord_event\s+[^,]+,\s*[^,]+,\s*([A-Z0-9_]+)\s*,")

    for path in sorted((ROOT / "maps").glob("*.asm")):
        scene_scripts = parse_map_scene_scripts(path)
        coord_events: list[tuple[int, str]] = []
        for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            code = raw.split(";", 1)[0]
            coord_event_match = coord_event_pat.match(code)
            if coord_event_match:
                coord_events.append((line_no, coord_event_match.group(1)))

        for line_no, scene in coord_events:
            if scene not in scene_scripts:
                fail(
                    f"{path.relative_to(ROOT)}:{line_no}: coord_event uses {scene}, "
                    "but the map scene table does not count it with scene_script"
                )


def check_scene_setting_commands_use_counted_scene_scripts() -> None:
    map_labels = parse_map_attribute_labels(ROOT / "data/maps/attributes.asm")
    map_scene_scripts = {
        path.stem: parse_map_scene_scripts(path)
        for path in sorted((ROOT / "maps").glob("*.asm"))
    }
    setscene_pat = re.compile(r"^\s*setscene\s+([^\s,;]+)")
    setmapscene_pat = re.compile(r"^\s*setmapscene\s+([A-Z0-9_]+),\s*([^\s,;]+)")
    script_paths = [
        *sorted((ROOT / "maps").glob("*.asm")),
        *sorted((ROOT / "engine").rglob("*.asm")),
        *sorted((ROOT / "data").rglob("*.asm")),
    ]

    for path in script_paths:
        for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            code = raw.split(";", 1)[0]
            setscene_match = setscene_pat.match(code)
            if setscene_match and path.parent == ROOT / "maps":
                scene = setscene_match.group(1)
                if not is_literal_scene_id(scene) and scene not in map_scene_scripts.get(path.stem, set()):
                    fail(
                        f"{path.relative_to(ROOT)}:{line_no}: setscene uses {scene}, "
                        "but this map does not count it with scene_script"
                    )

            setmapscene_match = setmapscene_pat.match(code)
            if not setmapscene_match:
                continue
            map_constant, scene = setmapscene_match.groups()
            if is_literal_scene_id(scene):
                continue
            target_label = map_labels.get(map_constant)
            if target_label is None:
                fail(f"{path.relative_to(ROOT)}:{line_no}: setmapscene uses unknown map {map_constant}")
            if scene not in map_scene_scripts.get(target_label, set()):
                fail(
                    f"{path.relative_to(ROOT)}:{line_no}: setmapscene sets {map_constant} to {scene}, "
                    "but the target map does not count that scene with scene_script"
                )


def check_map_event_coordinates_within_bounds() -> None:
    map_labels = parse_map_attribute_labels(ROOT / "data/maps/attributes.asm")
    label_to_map = {label: map_constant for map_constant, label in map_labels.items()}
    map_dimensions = parse_map_dimensions(ROOT / "constants/map_constants.asm")
    event_pats = (
        ("warp_event", re.compile(r"^\s*warp_event\s+(-?\d+),\s*(-?\d+),")),
        ("coord_event", re.compile(r"^\s*coord_event\s+(-?\d+),\s*(-?\d+),")),
        ("bg_event", re.compile(r"^\s*bg_event\s+(-?\d+),\s*(-?\d+),")),
        ("object_event", re.compile(r"^\s*object_event\s+(-?\d+),\s*(-?\d+),")),
    )

    for path in sorted((ROOT / "maps").glob("*.asm")):
        map_constant = label_to_map.get(path.stem)
        if map_constant is None:
            fail(f"{path.relative_to(ROOT)}: no map_attributes row for this map script")
        dimensions = map_dimensions.get(map_constant)
        if dimensions is None:
            fail(f"{path.relative_to(ROOT)}: no map_const dimensions for {map_constant}")
        width, height = dimensions
        for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            code = raw.split(";", 1)[0]
            for event_type, event_pat in event_pats:
                match = event_pat.match(code)
                if not match:
                    continue
                x_coord, y_coord = (int(value) for value in match.groups())
                if not (0 <= x_coord < width and 0 <= y_coord < height):
                    fail(
                        f"{path.relative_to(ROOT)}:{line_no}: {event_type} at "
                        f"{x_coord},{y_coord} is outside {width}x{height}"
                    )


def check_warp_events_target_existing_warps() -> None:
    map_labels = parse_map_attribute_labels(ROOT / "data/maps/attributes.asm")
    warp_pat = re.compile(r"^\s*warp_event\s+-?\d+,\s*-?\d+,\s*([A-Z0-9_]+),\s*(-?\d+)\b")
    warp_counts: dict[str, int] = {}
    warp_targets: list[tuple[Path, int, str, int]] = []

    for path in sorted((ROOT / "maps").glob("*.asm")):
        warp_count = 0
        for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            code = raw.split(";", 1)[0]
            match = warp_pat.match(code)
            if not match:
                continue
            target_map, target_warp = match.groups()
            warp_count += 1
            warp_targets.append((path, line_no, target_map, int(target_warp)))
        warp_counts[path.stem] = warp_count

    for path, line_no, target_map, target_warp in warp_targets:
        target_label = map_labels.get(target_map)
        if target_label is None:
            fail(f"{path.relative_to(ROOT)}:{line_no}: warp_event targets unknown map {target_map}")
        target_warp_count = warp_counts.get(target_label)
        if target_warp_count is None:
            fail(f"{path.relative_to(ROOT)}:{line_no}: warp_event targets missing map file {target_label}")
        if target_warp == -1:
            continue
        if not (1 <= target_warp <= target_warp_count):
            fail(
                f"{path.relative_to(ROOT)}:{line_no}: warp_event targets {target_map} "
                f"warp {target_warp}, but valid warps are 1..{target_warp_count}"
            )


def check_object_constants_match_object_events() -> None:
    const_pat = re.compile(r"^\s*const\s+[A-Z0-9_]+\b")
    for path in sorted((ROOT / "maps").glob("*.asm")):
        lines = path.read_text(encoding="utf-8").splitlines()
        in_object_consts = False
        object_consts = 0
        object_events = 0
        for line in lines:
            stripped = line.strip()
            if stripped == "object_const_def":
                in_object_consts = True
                continue
            if in_object_consts:
                if const_pat.match(line):
                    object_consts += 1
                    continue
                if stripped and not stripped.startswith(";"):
                    in_object_consts = False
            if line.lstrip().startswith("object_event"):
                object_events += 1
        if object_consts and object_consts != object_events:
            fail(
                f"{path.relative_to(ROOT)}: object_const_def has {object_consts} constants "
                f"for {object_events} object_event rows"
            )


def parse_map_itemball_labels(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    labels: dict[str, str] = {}
    label_pat = re.compile(r"^([A-Za-z0-9_]+):\s*$")
    itemball_pat = re.compile(r"^\s*itemball\s+([A-Z0-9_]+)\b")
    for index, line in enumerate(lines[:-1]):
        label_match = label_pat.match(line)
        if not label_match:
            continue
        itemball_match = itemball_pat.match(lines[index + 1])
        if itemball_match:
            labels[label_match.group(1)] = itemball_match.group(1)
    return labels


def parse_map_hiddenitem_labels(path: Path) -> dict[str, tuple[str, str]]:
    labels: dict[str, tuple[str, str]] = {}
    label_pat = re.compile(r"^([A-Za-z0-9_]+):\s*$")
    hiddenitem_pat = re.compile(r"^\s*hiddenitem\s+([A-Z0-9_]+),\s*(EVENT_[A-Z0-9_]+)\b")
    current_label: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        label_match = label_pat.match(line)
        if label_match:
            current_label = label_match.group(1)
            continue
        hiddenitem_match = hiddenitem_pat.match(line)
        if hiddenitem_match and current_label:
            labels[current_label] = (hiddenitem_match.group(1), hiddenitem_match.group(2))
    return labels


def normalize_event_token(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def is_legacy_tm_itemball_slot(label: str, event: str) -> bool:
    # Use raw names; normalized words like MountMortar contain "TM" across letters.
    return "_TM_" in event or re.search(r"TM[A-Z0-9]", label) is not None


def check_itemball_guard_classifier_edges() -> None:
    if is_legacy_tm_itemball_slot(
        "MountMortar1FOutsideGuardSpec",
        "EVENT_MOUNT_MORTAR_1F_OUTSIDE_REVIVE",
    ):
        fail("itemball TM-slot classifier treats MountMortar as a legacy TM slot")
    if not is_legacy_tm_itemball_slot(
        "GoldenrodUndergroundWarehouseTMSleepTalk",
        "EVENT_GOLDENROD_UNDERGROUND_WAREHOUSE_TM_SLEEP_TALK",
    ):
        fail("itemball TM-slot classifier misses a legacy TM reward slot")


def check_itemball_event_cross_swaps() -> None:
    for path in sorted((ROOT / "maps").glob("*.asm")):
        itemball_labels = parse_map_itemball_labels(path)
        rows: list[tuple[int, str, str, str]] = []
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.lstrip().startswith("object_event") or "OBJECTTYPE_ITEMBALL" not in line:
                continue
            parts = [part.strip() for part in line.split(",")]
            if len(parts) < 13:
                continue
            label = parts[11]
            event = parts[12]
            item = itemball_labels.get(label)
            if item and event.startswith("EVENT_"):
                rows.append((line_no, label, item, event))
        for index, (line_a, label_a, item_a, event_a) in enumerate(rows):
            item_a_token = normalize_event_token(item_a)
            event_a_token = normalize_event_token(event_a)
            for line_b, label_b, item_b, event_b in rows[index + 1 :]:
                item_b_token = normalize_event_token(item_b)
                event_b_token = normalize_event_token(event_b)
                if item_a_token in event_b_token and item_b_token in event_a_token:
                    fail(
                        f"{path.relative_to(ROOT)}:{line_a}/{line_b}: "
                        f"itemball flags look swapped between {label_a} and {label_b}"
                    )


def check_non_tm_itemball_event_names() -> None:
    for path in sorted((ROOT / "maps").glob("*.asm")):
        itemball_labels = parse_map_itemball_labels(path)
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.lstrip().startswith("object_event") or "OBJECTTYPE_ITEMBALL" not in line:
                continue
            parts = [part.strip() for part in line.split(",")]
            if len(parts) < 13:
                continue
            label = parts[11]
            event = parts[12]
            item = itemball_labels.get(label)
            if not item or not event.startswith("EVENT_"):
                continue
            item_token = normalize_event_token(item)
            event_token = normalize_event_token(event)
            if item_token in event_token:
                continue
            if is_legacy_tm_itemball_slot(label, event):
                continue
            fail(
                f"{path.relative_to(ROOT)}:{line_no}: "
                f"itemball {label} gives {item} but uses stale-looking flag {event}"
            )


def check_map_item_label_names() -> None:
    for path in sorted((ROOT / "maps").glob("*.asm")):
        itemball_labels = parse_map_itemball_labels(path)
        hiddenitem_labels = parse_map_hiddenitem_labels(path)
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith("object_event") and "OBJECTTYPE_ITEMBALL" in line:
                parts = [part.strip() for part in line.split(",")]
                if len(parts) < 13:
                    continue
                label = parts[11]
                event = parts[12]
                item = itemball_labels.get(label)
                if not item or is_legacy_tm_itemball_slot(label, event):
                    continue
                if normalize_event_token(item) not in normalize_event_token(label):
                    fail(
                        f"{path.relative_to(ROOT)}:{line_no}: "
                        f"itemball label {label} does not name {item}"
                    )
                continue
            if not stripped.startswith("bg_event") or "BGEVENT_ITEM" not in line:
                continue
            parts = [part.strip() for part in line.split(",")]
            if len(parts) < 4:
                continue
            label = parts[3]
            hiddenitem = hiddenitem_labels.get(label)
            if not hiddenitem:
                continue
            item, event = hiddenitem
            if normalize_event_token(item) not in normalize_event_token(label):
                fail(
                    f"{path.relative_to(ROOT)}:{line_no}: "
                    f"hidden item label {label} does not name {item}"
                )
            if normalize_event_token(item) not in normalize_event_token(event):
                fail(
                    f"{path.relative_to(ROOT)}:{line_no}: "
                    f"hidden item {label} gives {item} but uses stale-looking flag {event}"
                )


def check_burned_tower_itemball_flags() -> None:
    require_ordered_text(
        ROOT / "maps/BurnedTower1F.asm",
        (
            "\titemball BURN_HEAL, 1",
            "\titemball X_SPEED, 1",
            "BurnedTower1FBurnHeal, EVENT_BURNED_TOWER_1F_BURN_HEAL",
            "BurnedTower1FXSpeed, EVENT_BURNED_TOWER_1F_X_SPEED",
        ),
        "Burned Tower item balls use matching persistence flags",
    )


def asm_code(raw: str) -> str:
    return raw.split(";", 1)[0].strip()


def parse_mart_pointer_labels(lines: list[str]) -> list[str]:
    labels: list[str] = []
    in_table = False
    pointer_pat = re.compile(r"^dw\s+([A-Za-z0-9_]+)\b")
    for raw in lines:
        code = asm_code(raw)
        if code == "Marts:":
            in_table = True
            continue
        if not in_table:
            continue
        if code.startswith("assert_table_length"):
            return labels
        m = pointer_pat.match(code)
        if m:
            labels.append(m.group(1))
    return labels


def find_mart_inventory_issues(text: str, valid_items: set[str], source_label: str) -> list[str]:
    lines = text.splitlines()
    label_pat = re.compile(r"^([A-Za-z0-9_]+):\s*$")
    db_pat = re.compile(r"^db\s+([^,\s]+)\b")
    mart_labels = parse_mart_pointer_labels(lines)
    label_positions: dict[str, int] = {}
    label_order: list[tuple[str, int]] = []
    issues: list[str] = []

    for index, raw in enumerate(lines):
        m = label_pat.match(asm_code(raw))
        if not m:
            continue
        label = m.group(1)
        label_positions[label] = index
        label_order.append((label, index))

    if not mart_labels:
        issues.append(f"{source_label}: no Marts pointer table found")
    if "DefaultMart" in label_positions:
        mart_labels.append("DefaultMart")

    for label in mart_labels:
        start = label_positions.get(label)
        if start is None:
            issues.append(f"{source_label}: Marts table points at missing label {label}")
            continue

        end = len(lines)
        for _, next_index in label_order:
            if next_index > start:
                end = next_index
                break

        declared_count: int | None = None
        item_count = 0
        saw_terminator = False
        terminator_line: int | None = None
        for line_no, raw in enumerate(lines[start + 1 : end], start + 2):
            code = asm_code(raw)
            if not code:
                continue
            m = db_pat.match(code)
            if not m:
                continue
            token = m.group(1)
            if declared_count is None:
                if not token.isdigit():
                    issues.append(f"{source_label}:{line_no}: {label}: missing numeric mart item count")
                    break
                declared_count = int(token)
                continue
            if token in MART_TERMINATORS:
                if saw_terminator:
                    issues.append(f"{source_label}:{line_no}: {label}: duplicate mart terminator")
                saw_terminator = True
                terminator_line = line_no
                continue
            if saw_terminator:
                issues.append(
                    f"{source_label}:{line_no}: {label}: item after terminator {token}; "
                    "mart readers stop at the terminator"
                )
                continue
            if token not in valid_items:
                issues.append(f"{source_label}:{line_no}: {label}: unknown mart item {token}")
            item_count += 1

        if declared_count is None:
            issues.append(f"{source_label}: {label}: missing mart item count")
            continue
        if terminator_line is None:
            issues.append(f"{source_label}: {label}: missing mart terminator")
        if item_count != declared_count:
            issues.append(
                f"{source_label}: {label}: declared {declared_count} items, "
                f"but {item_count} appear before the terminator"
            )

    return issues


def check_mart_inventory_fixture(valid_items: set[str]) -> None:
    malformed_fixture = """Marts:
\ttable_width 2
\tdw BrokenMart
\tassert_table_length NUM_MARTS

BrokenMart:
\tdb 1 ; # items
\tdb POTION
\tdb CANCEL ; end
\tdb ANTIDOTE
"""
    fixture_issues = find_mart_inventory_issues(malformed_fixture, valid_items, "malformed mart fixture")
    if not any("item after terminator ANTIDOTE" in issue for issue in fixture_issues):
        fail("malformed mart fixture did not catch item after CANCEL/db -1")


def check_mart_inventory_tables(valid_items: set[str]) -> None:
    issues = find_mart_inventory_issues(
        (ROOT / "data/items/marts.asm").read_text(encoding="utf-8"),
        valid_items,
        "data/items/marts.asm",
    )
    if issues:
        fail("mart inventory table audit failed: " + "; ".join(issues))


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
        "FeraligatrEvosAttacks": {"SLASH": 38, "HYDRO_PUMP": 45},
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
    for include in (
        'INCLUDE "engine/battle/ai/boss_platform.asm"',
        'INCLUDE "engine/battle/ai/boss_policy_move.asm"',
        'INCLUDE "engine/battle/ai/boss_policy_switch.asm"',
        'INCLUDE "engine/battle/ai/boss_thunks.asm"',
    ):
        require_text(ROOT / "main.asm", include)
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

    check_elapsed_seconds_helper_refreshes_minute_flags()
    print("PASS: elapsed seconds helper flag check")

    check_bug_contest_exit_flow()
    print("PASS: Bug Contest exit flow checks")

    check_map_event_script_shapes()
    print("PASS: map event script-shape checks")

    check_coord_events_use_counted_scene_scripts()
    print("PASS: coord-event scene-table checks")

    check_scene_setting_commands_use_counted_scene_scripts()
    print("PASS: scene-setting command scene-table checks")

    check_map_event_coordinates_within_bounds()
    print("PASS: map event coordinate bounds checks")

    check_warp_events_target_existing_warps()
    print("PASS: warp target index checks")

    check_object_constants_match_object_events()
    print("PASS: object constant count checks")

    check_itemball_event_cross_swaps()
    print("PASS: itemball event cross-swap checks")

    check_itemball_guard_classifier_edges()
    print("PASS: itemball guard classifier edge checks")

    check_map_item_label_names()
    print("PASS: map item label/name checks")

    check_non_tm_itemball_event_names()
    print("PASS: non-TM itemball flag/name checks")

    check_burned_tower_itemball_flags()
    print("PASS: Burned Tower itemball flag checks")

    item_tokens = parse_item_tokens(ROOT / "constants/item_constants.asm")
    check_mart_inventory_fixture(item_tokens)
    print("PASS: malformed mart fixture catches item after terminator")

    check_mart_inventory_tables(item_tokens)
    print("PASS: mart inventory table checks")

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
        'DayCareServicePamphletText:\n\ttext "DAY-CARE SERVICES"\n\tline "We raise #MON"\n\tcont "for busy TRAINERS."',
    )
    require_text(
        ROOT / "maps/Route34.asm",
        'DayCareSignText:\n\ttext "DAY-CARE"\n\n\tpara "Raise #MON and"\n\tline "remember old"\n\tcont "moves inside."',
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

    check_save_format_version()
    check_no_stale_shipped_claims()
    check_farcall_hl_clobber()
    check_farcall_a_clobber()
    check_ld_a_zero()
    check_cp_zero()
    check_matchup_cli()

    print("ALL RELEASE SMOKE CHECKS PASSED")
    return 0


def _run_subaudit(script: str, label: str) -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools/audit" / script)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.stderr:
        print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n", file=sys.stderr)
    if proc.returncode != 0:
        fail(f"{label} audit failed")
    print(f"PASS: {label} audit")


def check_save_format_version() -> None:
    _run_subaudit("check_save_format_version.py", "save format version")


def check_no_stale_shipped_claims() -> None:
    _run_subaudit("check_no_stale_shipped_claims.py", "no stale shipped claims")


def check_farcall_hl_clobber() -> None:
    _run_subaudit("check_farcall_hl_clobber.py", "farcall hl-clobber")


def check_farcall_a_clobber() -> None:
    _run_subaudit("check_farcall_a_clobber.py", "farcall a-clobber")


def check_ld_a_zero() -> None:
    _run_subaudit("check_ld_a_zero.py", "ld a, 0 -> xor a")


def check_cp_zero() -> None:
    _run_subaudit("check_cp_zero.py", "cp 0 -> and a")


def check_matchup_cli() -> None:
    _run_subaudit("check_matchup_cli.py", "damage matchup CLI")


if __name__ == "__main__":
    raise SystemExit(main())
