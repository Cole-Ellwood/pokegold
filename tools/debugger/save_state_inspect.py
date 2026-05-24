from __future__ import annotations

import gzip
import hashlib
import re
import struct
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .provenance import display_path, parse_symbol_table, resolve_path


KIND = "unified_debugger_save_state_inspection"
PARTY_LENGTH = 6
ROMX_MIN = 0x4000


def build_save_state_inspection_report(
    *,
    save_state: str,
    rom_path: str = "pokegold.gbc",
    symbols_path: str = "pokegold.sym",
    root: Path = ROOT,
) -> dict[str, Any]:
    state = resolve_path(save_state, root=root)
    rom = resolve_path(rom_path, root=root)
    symbols = resolve_path(symbols_path, root=root)
    errors: list[str] = []
    warnings: list[str] = []
    if not state.exists():
        errors.append(f"missing save-state: {save_state}")
    if not symbols.exists():
        errors.append(f"missing symbols: {symbols_path}")
    if not rom.exists():
        warnings.append(f"missing ROM; bank validity checks disabled: {rom_path}")
    if state.exists() and state.suffix.lower() != ".sgm":
        errors.append(
            f"unsupported save-state extension: {state.suffix.lower() or '<none>'}; "
            "this command currently inspects VBA-M .sgm files"
        )

    syms = parse_symbol_table(symbols) if symbols.exists() else {}
    rom_size = rom.stat().st_size if rom.exists() else 0
    snapshot: dict[str, Any] = {}
    selected: dict[str, Any] | None = None
    candidates: list[dict[str, Any]] = []
    memory: dict[str, Any] = {}
    findings: list[dict[str, Any]] = []
    state_format = "unknown"

    if not errors:
        try:
            raw = gzip.decompress(state.read_bytes())
            state_format = "vbam_sgm"
            snapshot = decode_snapshot_header(raw)
            maps = parse_map_constants(root)
            attrs = parse_map_attributes(root)
            species_names = parse_species_constants(root)
            candidates = find_wram_candidates(raw, syms, maps, attrs)
            if candidates:
                selected = candidates[0]
                memory = read_memory_summary(
                    raw,
                    selected,
                    syms,
                    maps=maps,
                    attrs=attrs,
                    species_names=species_names,
                    rom_size=rom_size,
                )
                findings = build_findings(memory, rom_size=rom_size)
            else:
                errors.append("could not locate active WRAM in .sgm from party/map anchors")
        except OSError as exc:
            errors.append(f"could not decode VBA-M .sgm: {exc}")

    blocking = sum(1 for finding in findings if int(finding.get("severity", 3)) <= 2)
    commands = [
        f"python -m tools.debugger inspect-state --save-state {save_state} --rom {rom_path} --symbols {symbols_path} --json-out .local\\tmp\\save_state_inspect.json",
        "python -m tools.debugger script-resume-gate --report .local\\tmp\\save_state_inspect.json",
        "python -m tools.debugger wram-lifetime --symbol wSeenTrainerBank --symbol wScriptAfterPointer --symbol wRunningTrainerBattleScript --through Script_startbattle",
        "python -m tools.debugger wram-ownership --symbol wSeenTrainerBank --symbol wScriptAfterPointer --symbol wRunningTrainerBattleScript",
    ]
    return {
        "schema_version": 1,
        "kind": KIND,
        "root": str(root),
        "valid": not errors,
        "save_state": display_path(state, root=root),
        "save_state_sha256": sha256_file(state) if state.exists() else "",
        "state_format": state_format,
        "rom": display_path(rom, root=root),
        "rom_sha256": sha256_file(rom) if rom.exists() else "",
        "rom_size_bytes": rom_size,
        "rom_bank_count": rom_size // 0x4000 if rom_size else 0,
        "symbols": display_path(symbols, root=root),
        "symbols_sha256": sha256_file(symbols) if symbols.exists() else "",
        "snapshot": snapshot,
        "wram_candidates": candidates[:8],
        "selected_wram": selected,
        "memory": memory,
        "finding_count": len(findings),
        "blocking_finding_count": blocking,
        "findings": findings,
        "commands": commands,
        "errors": errors,
        "warnings": warnings,
        "known_limits": [
            "VBA-M .sgm inspection is static: it diagnoses captured memory but cannot replay input.",
            "Active WRAM is inferred from party/map/script anchors; ambiguous states need a PyBoy .state runtime watch.",
        ],
    }


def decode_snapshot_header(raw: bytes) -> dict[str, Any]:
    if len(raw) < 40:
        raise OSError("VBA-M .sgm payload is too small to contain the GB CPU header")
    version = struct.unpack_from("<I", raw, 0)[0]
    title = raw[4:19].split(b"\0", 1)[0].decode("ascii", errors="replace").strip()
    regs = dict(zip(("pc", "sp", "af", "bc", "de", "hl"), struct.unpack_from("<6H", raw, 27)))
    return {
        "emulator_format": "VBA-M .sgm",
        "version": version,
        "rom_title": title,
        "decompressed_size": len(raw),
        "cpu": {
            name: {"value": value, "hex": f"{value:04X}", "region": memory_region(value)}
            for name, value in regs.items()
        },
    }


def find_wram_candidates(
    raw: bytes,
    syms: dict[str, dict[str, Any]],
    maps: dict[tuple[int, int], dict[str, Any]],
    attrs: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    party = syms.get("wPartyCount")
    if not party:
        return []
    delta = int(party["address"]) - 0xD000
    candidates: list[dict[str, Any]] = []
    seen: set[int] = set()
    for offset in range(0, max(0, len(raw) - PARTY_LENGTH - 2)):
        count = raw[offset]
        if not (1 <= count <= PARTY_LENGTH):
            continue
        if offset + count + 1 >= len(raw) or raw[offset + count + 1] != 0xFF:
            continue
        d000_base = offset - delta
        if d000_base in seen or d000_base < 0 or d000_base + 0x1000 > len(raw):
            continue
        seen.add(d000_base)
        candidate = score_candidate(raw, d000_base, syms, maps, attrs)
        if candidate["score"] > 0:
            candidates.append(candidate)
    candidates.sort(key=lambda item: (-int(item["score"]), str(item["d000_base"])))
    return candidates


def score_candidate(
    raw: bytes,
    d000_base: int,
    syms: dict[str, dict[str, Any]],
    maps: dict[tuple[int, int], dict[str, Any]],
    attrs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    wram0_base = d000_base - 0x1000
    reasons: list[str] = []
    score = 0
    party_count = read_u8(raw, syms, "wPartyCount", wram0_base, d000_base)
    species = read_bytes(raw, syms, "wPartySpecies", party_count or 0, wram0_base, d000_base)
    if party_count and 1 <= party_count <= PARTY_LENGTH and len(species) == party_count:
        score += 20
        reasons.append(f"party count/species plausible ({party_count})")
    map_group = read_u8(raw, syms, "wMapGroup", wram0_base, d000_base)
    map_number = read_u8(raw, syms, "wMapNumber", wram0_base, d000_base)
    if map_group is not None and map_number is not None and (map_group, map_number) in maps:
        score += 20
        reasons.append(f"map id resolves ({map_group}:{map_number})")
        map_constant = str(maps[(map_group, map_number)].get("constant") or "")
        map_attr = attrs.get(map_constant, {})
        live_map_bank = read_u8(raw, syms, "wMapScriptsBank", wram0_base, d000_base)
        live_map_pointer = read_u16(raw, syms, "wMapScriptsPointer", wram0_base, d000_base)
        map_label = map_attr.get("label")
        map_script_symbol = syms.get(f"{map_label}_MapScripts") if isinstance(map_label, str) else None
        expected_map_bank = int(map_script_symbol["bank"]) if map_script_symbol else None
        if isinstance(expected_map_bank, int) and live_map_bank == expected_map_bank and live_map_pointer:
            score += 18
            reasons.append(f"live map script metadata matches source bank (${live_map_bank:02X})")
        elif live_map_bank == 0 or live_map_pointer in {0, None}:
            score -= 18
            reasons.append("known map has empty live map script metadata")
        elif isinstance(expected_map_bank, int) and live_map_bank != expected_map_bank:
            score -= 4
            reasons.append(
                f"live map script bank ${live_map_bank:02X} differs from source ${expected_map_bank:02X}"
            )
    elif map_group == 0 or map_number == 0:
        score -= 8
        reasons.append("map id is zero")
    script_mode = read_u8(raw, syms, "wScriptMode", wram0_base, d000_base)
    script_running = read_u8(raw, syms, "wScriptRunning", wram0_base, d000_base)
    if script_mode is not None and script_mode <= 2:
        score += 8
        reasons.append(f"script mode plausible ({script_mode})")
    elif script_mode is not None:
        score -= 6
        reasons.append(f"script mode implausible ({script_mode})")
    if script_running in {0, 1}:
        score += 8
        reasons.append(f"script running flag plausible ({script_running})")
    elif script_running is not None:
        score -= 6
        reasons.append(f"script running flag implausible ({script_running})")
    battle_mode = read_u8(raw, syms, "wBattleMode", wram0_base, d000_base)
    if battle_mode in {0, 1, 2}:
        score += 5
        reasons.append(f"battle mode plausible ({battle_mode})")
    region = raw[d000_base : d000_base + 0x1000]
    unique_bytes = len(set(region))
    repeated_3900 = sum(
        1
        for idx in range(0, max(0, len(region) - 1), 2)
        if region[idx] == 0x39 and region[idx + 1] == 0x00
    )
    if unique_bytes >= 32:
        score += 4
        reasons.append(f"live-looking byte variety ({unique_bytes})")
    if repeated_3900 > 0x200:
        score -= 20
        reasons.append("39 00 tile-pattern region, not active WRAM")
    return {
        "d000_base": f"0x{d000_base:05X}",
        "wram0_base": f"0x{wram0_base:05X}",
        "score": score,
        "reasons": reasons,
        "party_count": party_count,
        "party_species": [hex_u8(value) for value in species],
        "map_group": map_group,
        "map_number": map_number,
        "script_mode": script_mode,
        "script_running": script_running,
        "script_bank": hex_u8(read_u8(raw, syms, "wScriptBank", wram0_base, d000_base)),
        "script_pos": hex_u16(read_u16(raw, syms, "wScriptPos", wram0_base, d000_base)),
    }


def read_memory_summary(
    raw: bytes,
    selected: dict[str, Any],
    syms: dict[str, dict[str, Any]],
    *,
    maps: dict[tuple[int, int], dict[str, Any]],
    attrs: dict[str, dict[str, Any]],
    species_names: dict[int, str],
    rom_size: int,
) -> dict[str, Any]:
    d000_base = int(str(selected["d000_base"]), 16)
    wram0_base = int(str(selected["wram0_base"]), 16)
    map_group = read_u8(raw, syms, "wMapGroup", wram0_base, d000_base)
    map_number = read_u8(raw, syms, "wMapNumber", wram0_base, d000_base)
    map_record = maps.get((map_group or -1, map_number or -1), {})
    map_name = str(map_record.get("constant") or "")
    attr = attrs.get(map_name, {})
    party_count = read_u8(raw, syms, "wPartyCount", wram0_base, d000_base) or 0
    party_species = read_bytes(raw, syms, "wPartySpecies", party_count, wram0_base, d000_base)
    script_stack = read_script_stack(raw, syms, wram0_base, d000_base)
    sp = 0
    # The CPU header SP is already in the top-level snapshot; read from the usual captured value when present.
    try:
        sp = struct.unpack_from("<H", raw, 29)[0]
    except struct.error:
        pass
    return {
        "map": {
            "group": map_group,
            "number": map_number,
            "name": map_name or None,
            "label": attr.get("label"),
            "source": attr.get("source"),
            "x": read_u8(raw, syms, "wXCoord", wram0_base, d000_base),
            "y": read_u8(raw, syms, "wYCoord", wram0_base, d000_base),
            "map_scripts_bank_live": hex_u8(read_u8(raw, syms, "wMapScriptsBank", wram0_base, d000_base)),
            "map_scripts_pointer_live": hex_u16(read_u16(raw, syms, "wMapScriptsPointer", wram0_base, d000_base)),
            "map_scripts_bank_source": hex_u8(map_script_bank(syms, attr)),
        },
        "battle": {
            "mode": read_u8(raw, syms, "wBattleMode", wram0_base, d000_base),
            "type": read_u8(raw, syms, "wBattleType", wram0_base, d000_base),
            "result": hex_u8(read_u8(raw, syms, "wBattleResult", wram0_base, d000_base)),
        },
        "party": {
            "count": party_count,
            "species": [
                {"slot": index + 1, "id": value, "hex": hex_u8(value), "name": species_names.get(value, f"UNKNOWN_{value:02X}")}
                for index, value in enumerate(party_species)
            ],
        },
        "script_vm": {
            "mode": read_u8(raw, syms, "wScriptMode", wram0_base, d000_base),
            "running": read_u8(raw, syms, "wScriptRunning", wram0_base, d000_base),
            "bank": hex_u8(read_u8(raw, syms, "wScriptBank", wram0_base, d000_base)),
            "bank_value": read_u8(raw, syms, "wScriptBank", wram0_base, d000_base),
            "pos": hex_u16(read_u16(raw, syms, "wScriptPos", wram0_base, d000_base)),
            "pos_value": read_u16(raw, syms, "wScriptPos", wram0_base, d000_base),
            "stack_size": read_u8(raw, syms, "wScriptStackSize", wram0_base, d000_base),
            "stack": script_stack,
        },
        "trainer_context": {
            "seen_trainer_bank": hex_u8(read_u8(raw, syms, "wSeenTrainerBank", wram0_base, d000_base)),
            "seen_trainer_bank_value": read_u8(raw, syms, "wSeenTrainerBank", wram0_base, d000_base),
            "script_after_pointer": hex_u16(read_u16(raw, syms, "wScriptAfterPointer", wram0_base, d000_base)),
            "script_after_pointer_value": read_u16(raw, syms, "wScriptAfterPointer", wram0_base, d000_base),
            "running_trainer_battle_script": hex_u8(read_u8(raw, syms, "wRunningTrainerBattleScript", wram0_base, d000_base)),
            "running_trainer_battle_script_value": read_u8(raw, syms, "wRunningTrainerBattleScript", wram0_base, d000_base),
            "backup_active": read_u8(raw, syms, "wTrainerBattleContextBackupActive", wram0_base, d000_base),
        },
        "cpu_stack": read_cpu_stack(raw, sp, wram0_base, d000_base),
        "rom": {"bank_count": rom_size // 0x4000 if rom_size else 0},
    }


def build_findings(memory: dict[str, Any], *, rom_size: int) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    script = memory.get("script_vm", {})
    battle = memory.get("battle", {})
    map_info = memory.get("map", {})
    trainer = memory.get("trainer_context", {})
    stack = memory.get("cpu_stack", {})
    bank = script.get("bank_value")
    pos = script.get("pos_value")
    running = script.get("running")
    expected_bank = parse_hex_int(map_info.get("map_scripts_bank_source")) or parse_hex_int(map_info.get("map_scripts_bank_live"))
    rom_banks = rom_size // 0x4000 if rom_size else 0
    if running and isinstance(pos, int) and pos < ROMX_MIN:
        findings.append(make_finding("script_pos_rom0_header", 1, f"active script pointer is {hex_u8(bank)}:{hex_u16(pos)}, inside ROM0/header space"))
    if running and isinstance(bank, int) and rom_banks and bank >= rom_banks:
        findings.append(make_finding("invalid_script_bank", 1, f"active script bank {hex_u8(bank)} is outside the ROM bank range"))
    if running and isinstance(bank, int) and isinstance(expected_bank, int) and (bank & 0x7F) != expected_bank:
        findings.append(make_finding("script_bank_not_map_bank", 1, f"active script bank {hex_u8(bank)} does not match current map script bank {hex_u8(expected_bank)}"))
    if running and battle.get("mode") == 0 and (
        (isinstance(pos, int) and pos < ROMX_MIN)
        or (isinstance(bank, int) and rom_banks and bank >= rom_banks)
    ):
        findings.append(make_finding("battle_finished_script_still_active", 1, "battle mode is clear but the script VM is still running from an impossible pointer"))
    if running and trainer.get("running_trainer_battle_script_value") in {0xFF, None}:
        findings.append(make_finding("trainer_resume_context_corrupt", 2, "trainer resume context is empty/corrupt while a post-battle script is still active"))
    top_words = stack.get("top_words") if isinstance(stack, dict) else []
    if top_words and top_words[0].get("region") in {"echo_ram", "unmapped"}:
        findings.append(make_finding("stack_return_into_echo_ram", 1, f"top CPU stack return word points into {top_words[0].get('region')}"))
    findings.append(make_finding("sgm_static_only_not_pyboy_replayable", 3, "VBA-M .sgm was inspected statically; use a PyBoy .state or recreated route for replay proof"))
    return findings


def read_script_stack(raw: bytes, syms: dict[str, dict[str, Any]], wram0_base: int, d000_base: int) -> list[dict[str, Any]]:
    size = read_u8(raw, syms, "wScriptStackSize", wram0_base, d000_base) or 0
    base = offset_for(syms, "wScriptStack", wram0_base, d000_base)
    if base is None:
        return []
    out: list[dict[str, Any]] = []
    for index in range(min(size, 5)):
        pos = base + index * 3
        if pos + 2 >= len(raw):
            break
        bank = raw[pos]
        address = raw[pos + 1] | (raw[pos + 2] << 8)
        out.append({"index": index, "bank": hex_u8(bank), "address": hex_u16(address), "region": memory_region(address)})
    return out


def read_cpu_stack(raw: bytes, sp: int, wram0_base: int, d000_base: int) -> dict[str, Any]:
    base = None
    if 0xC000 <= sp <= 0xCFFF:
        base = wram0_base + (sp - 0xC000)
    elif 0xD000 <= sp <= 0xDFFF:
        base = d000_base + (sp - 0xD000)
    data = raw[base : base + 24] if base is not None and 0 <= base < len(raw) else b""
    return {
        "sp": hex_u16(sp),
        "sp_region": memory_region(sp),
        "top_words": [
            {"offset": index, "address": hex_u16(data[index] | (data[index + 1] << 8)), "region": memory_region(data[index] | (data[index + 1] << 8))}
            for index in range(0, max(0, len(data) - 1), 2)
        ],
    }


def parse_map_constants(root: Path) -> dict[tuple[int, int], dict[str, Any]]:
    path = root / "constants" / "map_constants.asm"
    out: dict[tuple[int, int], dict[str, Any]] = {}
    if not path.exists():
        return out
    group = 0
    map_no = 0
    group_name = ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = re.match(r"\s*newgroup\s+([A-Z0-9_]+)", line)
        if match:
            group += 1
            map_no = 0
            group_name = match.group(1)
            continue
        match = re.match(r"\s*map_const\s+([A-Z0-9_]+),", line)
        if match:
            map_no += 1
            out[(group, map_no)] = {"constant": match.group(1), "group": group, "number": map_no, "group_name": group_name}
    return out


def parse_map_attributes(root: Path) -> dict[str, dict[str, Any]]:
    path = root / "data" / "maps" / "attributes.asm"
    out: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return out
    pattern = re.compile(r"\s*map_attributes\s+([A-Za-z0-9_]+),\s+([A-Z0-9_]+),\s+\$([0-9A-Fa-f]+),\s*(\d+)")
    for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        match = pattern.match(line)
        if match:
            label, constant, bank_hex, _connection = match.groups()
            out[constant] = {"label": label, "constant": constant, "border_block": int(bank_hex, 16), "source": f"data/maps/attributes.asm:{line_no}"}
    return out


def parse_species_constants(root: Path) -> dict[int, str]:
    path = root / "constants" / "pokemon_constants.asm"
    out: dict[int, str] = {}
    if not path.exists():
        return out
    value = 0
    active = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if re.match(r"\s*const_def\s+1\b", line) and not active:
            active = True
            value = 1
            continue
        if line.startswith("DEF NUM_POKEMON"):
            break
        if not active:
            continue
        match = re.match(r"\s*const\s+([A-Z0-9_]+)", line)
        if match:
            out[value] = match.group(1)
            value += 1
        elif re.match(r"\s*const_skip\b", line):
            value += 1
    return out


def map_script_bank(syms: dict[str, dict[str, Any]], attr: dict[str, Any]) -> int | None:
    label = attr.get("label")
    if not isinstance(label, str):
        return None
    entry = syms.get(f"{label}_MapScripts")
    if not entry:
        return None
    return int(entry["bank"])


def read_u8(raw: bytes, syms: dict[str, dict[str, Any]], symbol: str, wram0_base: int, d000_base: int) -> int | None:
    offset = offset_for(syms, symbol, wram0_base, d000_base)
    return raw[offset] if offset is not None and 0 <= offset < len(raw) else None


def read_u16(raw: bytes, syms: dict[str, dict[str, Any]], symbol: str, wram0_base: int, d000_base: int) -> int | None:
    offset = offset_for(syms, symbol, wram0_base, d000_base)
    return raw[offset] | (raw[offset + 1] << 8) if offset is not None and 0 <= offset + 1 < len(raw) else None


def read_bytes(raw: bytes, syms: dict[str, dict[str, Any]], symbol: str, size: int, wram0_base: int, d000_base: int) -> bytes:
    offset = offset_for(syms, symbol, wram0_base, d000_base)
    return raw[offset : offset + size] if offset is not None and 0 <= offset + size <= len(raw) else b""


def offset_for(syms: dict[str, dict[str, Any]], symbol: str, wram0_base: int, d000_base: int) -> int | None:
    entry = syms.get(symbol)
    if not entry:
        return None
    address = int(entry["address"])
    if 0xC000 <= address <= 0xCFFF:
        return wram0_base + (address - 0xC000)
    if 0xD000 <= address <= 0xDFFF:
        return d000_base + (address - 0xD000)
    return None


def make_finding(finding_id: str, severity: int, title: str) -> dict[str, Any]:
    return {"id": finding_id, "severity": severity, "title": title, "detail": title, "evidence": {}}


def parse_hex_int(value: Any) -> int | None:
    if not isinstance(value, str) or not value.startswith("$"):
        return None
    try:
        return int(value[1:], 16)
    except ValueError:
        return None


def memory_region(address: int | None) -> str:
    if address is None:
        return ""
    if 0x0000 <= address <= 0x3FFF:
        return "rom0"
    if 0x4000 <= address <= 0x7FFF:
        return "romx"
    if 0x8000 <= address <= 0x9FFF:
        return "vram"
    if 0xA000 <= address <= 0xBFFF:
        return "sram"
    if 0xC000 <= address <= 0xDFFF:
        return "wram"
    if 0xE000 <= address <= 0xFDFF:
        return "echo_ram"
    if 0xFEA0 <= address <= 0xFEFF:
        return "unmapped"
    if 0xFF00 <= address <= 0xFF7F:
        return "io"
    if 0xFF80 <= address <= 0xFFFE:
        return "hram"
    if address == 0xFFFF:
        return "interrupt_enable"
    return "unknown"


def hex_u8(value: int | None) -> str | None:
    return None if value is None else f"${value & 0xFF:02X}"


def hex_u16(value: int | None) -> str | None:
    return None if value is None else f"${value & 0xFFFF:04X}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()
