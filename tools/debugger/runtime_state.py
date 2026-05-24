from __future__ import annotations

import gzip
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog import ROOT
from .content_mirror import load_rom_mirror_context, rom_offset_for_symbol
from .ingest import display_path, resolve_path, sha256_file
from .save_state_format import is_vbam_sgm_path


DEFAULT_ROM = "pokegold.gbc"
DEFAULT_SYMBOLS = "pokegold.sym"
SCRIPT_STACK_CAPACITY = 5
SCRIPT_MODES = {
    0: "SCRIPT_OFF",
    1: "SCRIPT_READ",
    2: "SCRIPT_WAIT_MOVEMENT",
    3: "SCRIPT_WAIT",
}
WATCH_SYMBOLS = (
    "wScriptBank",
    "wScriptPos",
    "wScriptStackSize",
    "wScriptStack",
    "wScriptRunning",
    "wScriptMode",
)
SCRIPT_CONTEXT_SYMBOLS = (
    "wScriptMode",
    "wScriptRunning",
    "wScriptBank",
    "wScriptPos",
    "wScriptStackSize",
    "wScriptStack",
    "wScriptVar",
    "wScriptDelay",
    "wMapGroup",
    "wMapNumber",
    "wMapScriptsBank",
    "wMapScriptsPointer",
    "wBattleMode",
    "wBattleType",
    "wBattleResult",
    "wBattleScriptFlags",
    "wSeenTrainerBank",
    "wScriptAfterPointer",
    "wRunningTrainerBattleScript",
    "wTrainerBattleContextBackupActive",
    "wEvolutionOldSpecies",
    "wEvolutionNewSpecies",
)


@dataclass(frozen=True)
class Snapshot:
    state_format: str
    supported: bool
    memory: "MemoryReader | None"
    cpu: dict[str, int]
    metadata: dict[str, Any]
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


class MemoryReader:
    def __init__(
        self,
        data: bytes,
        *,
        c000_base: int | None = None,
        d000_base: int | None = None,
    ) -> None:
        self.data = data
        self.c000_base = c000_base
        self.d000_base = d000_base

    def read(self, address: int, size: int = 1, *, bank: int = 0) -> bytes | None:
        if size <= 0:
            return b""
        base: int | None
        if 0xC000 <= address <= 0xCFFF:
            base = self.c000_base
            offset = address - 0xC000
        elif 0xD000 <= address <= 0xDFFF:
            base = self.d000_base
            offset = address - 0xD000
        elif 0xE000 <= address <= 0xFDFF:
            mirror = address - 0x2000
            return self.read(mirror, size, bank=bank)
        else:
            return None
        if base is None:
            return None
        start = base + offset
        end = start + size
        if start < 0 or end > len(self.data):
            return None
        return self.data[start:end]


class PyBoyMemoryReader:
    def __init__(self, pyboy: Any) -> None:
        self.pyboy = pyboy

    def read(self, address: int, size: int = 1, *, bank: int = 0) -> bytes | None:
        values: list[int] = []
        try:
            if 0xD000 <= address <= 0xDFFF and bank:
                try:
                    for offset in range(size):
                        values.append(int(self.pyboy.memory[bank, address + offset]))
                    return bytes(values)
                except Exception:
                    old_bank = int(self.pyboy.memory[0xFF70])
                    self.pyboy.memory[0xFF70] = bank
                    try:
                        for offset in range(size):
                            values.append(int(self.pyboy.memory[address + offset]))
                    finally:
                        self.pyboy.memory[0xFF70] = old_bank
                    return bytes(values)
            for offset in range(size):
                values.append(int(self.pyboy.memory[address + offset]))
        except Exception:
            return None
        return bytes(values)


def build_runtime_state_report(
    *,
    rom_path: str = DEFAULT_ROM,
    symbols_path: str = DEFAULT_SYMBOLS,
    save_state: str = "",
    root: Path = ROOT,
) -> dict[str, Any]:
    rom = resolve_path(rom_path, root=root)
    symbols = resolve_path(symbols_path, root=root)
    state_path = resolve_path(save_state, root=root) if save_state else None
    errors: list[str] = []
    warnings: list[str] = []
    if not save_state:
        errors.append("--save-state is required")
    elif state_path is not None and not state_path.exists():
        errors.append(f"missing save-state: {save_state}")
    if not rom.exists():
        errors.append(f"missing ROM: {rom_path}")
    if not symbols.exists():
        errors.append(f"missing symbols: {symbols_path}")

    rom_context = load_rom_mirror_context(rom_path=rom_path, symbols_path=symbols_path, root=root)
    labels: dict[str, dict[str, int]] = dict(rom_context.get("labels", {}))
    rom_bytes = rom_context.get("rom_bytes", b"") if isinstance(rom_context.get("rom_bytes", b""), bytes) else b""
    map_catalog = load_map_catalog(root=root, labels=labels)
    snapshot = (
        load_snapshot(state_path, labels=labels, map_catalog=map_catalog, root=root)
        if state_path is not None and state_path.exists()
        else Snapshot("missing", False, None, {}, {}, ())
    )
    warnings.extend(snapshot.warnings)
    errors.extend(snapshot.errors)

    values: dict[str, dict[str, Any]] = {}
    if snapshot.memory is not None:
        values = read_context_values(snapshot.memory, labels)

    map_context = describe_map_context(values=values, labels=labels, map_catalog=map_catalog)
    script_vm = describe_script_vm(
        values=values,
        labels=labels,
        rom_bytes=rom_bytes,
        rom_bank_count=rom_bank_count(rom_bytes),
        map_context=map_context,
    )
    cpu_report = describe_cpu(
        cpu=snapshot.cpu,
        memory=snapshot.memory,
        labels=labels,
        rom_bank_count=rom_bank_count(rom_bytes),
    )
    trainer_context = describe_trainer_context(values)
    evolution_context = describe_evolution_context(values)

    findings = build_findings(
        cpu_report=cpu_report,
        map_context=map_context,
        script_vm=script_vm,
        trainer_context=trainer_context,
        evolution_context=evolution_context,
        save_state=save_state,
    )
    commands = suggested_commands(
        save_state=save_state,
        rom_path=rom_path,
        symbols_path=symbols_path,
        map_context=map_context,
    )
    warnings.extend(map_catalog.get("warnings", []))
    errors.extend(map_catalog.get("errors", []))

    return {
        "schema_version": 1,
        "kind": "unified_debugger_runtime_state_report",
        "root": str(root),
        "valid": not errors,
        "passed": not findings,
        "state_supported": snapshot.supported,
        "state_format": snapshot.state_format,
        "save_state": display_path(state_path, root=root) if state_path is not None else "",
        "rom": display_path(rom, root=root),
        "rom_sha256": sha256_file(rom) if rom.exists() else "",
        "symbols": display_path(symbols, root=root),
        "symbols_sha256": sha256_file(symbols) if symbols.exists() else "",
        "rom_bank_count": rom_bank_count(rom_bytes),
        "cpu": cpu_report,
        "map": map_context,
        "script_vm": script_vm,
        "trainer_context": trainer_context,
        "evolution_context": evolution_context,
        "finding_count": len(findings),
        "findings": findings,
        "commands": commands,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "snapshot_metadata": snapshot.metadata,
        "known_limits": [
            "VBA-M .sgm support is a read-only crash-state inspector; it does not execute or replay the state.",
            "Battery .sav support boots a temporary ROM through Continue and inspects the resulting live state; it does not auto-navigate from the save.",
            "Script range checks are strongest for map-local scripts; far jumps to common scripts may need follow-up trace proof.",
            "CPU stack signatures are crash evidence, not root-cause proof without a preceding write trace.",
        ],
    }


def load_snapshot(
    path: Path,
    *,
    labels: dict[str, dict[str, int]],
    map_catalog: dict[str, Any],
    root: Path,
) -> Snapshot:
    suffix = path.suffix.lower()
    if suffix == ".sgm":
        return load_vbam_sgm_snapshot(path, labels=labels, map_catalog=map_catalog, root=root)
    if suffix == ".state":
        return load_pyboy_snapshot(path, root=root)
    if suffix == ".sav":
        return load_battery_save_snapshot(path, root=root)
    return Snapshot(
        suffix.lstrip(".") or "unknown",
        False,
        None,
        {},
        {"path": display_path(path, root=root)},
        errors=(f"unsupported save-state extension: {suffix or '<none>'}",),
    )


def load_vbam_sgm_snapshot(
    path: Path,
    *,
    labels: dict[str, dict[str, int]],
    map_catalog: dict[str, Any],
    root: Path,
) -> Snapshot:
    warnings: list[str] = []
    errors: list[str] = []
    try:
        raw = path.read_bytes()
        data = gzip.decompress(raw) if raw.startswith(b"\x1f\x8b") else raw
    except OSError as exc:
        return Snapshot("vbam_sgm", False, None, {}, {}, errors=(f"could not read .sgm: {exc}",))
    except gzip.BadGzipFile as exc:
        return Snapshot("vbam_sgm", False, None, {}, {}, errors=(f"could not decompress .sgm: {exc}",))

    d000_base, anchor_report = find_d000_base(data, labels, map_catalog=map_catalog)
    c000_base = d000_base - 0x1000 if d000_base is not None and d000_base >= 0x1000 else None
    if d000_base is None:
        errors.append("could not locate live D000 WRAM bank in .sgm")
    cpu = parse_vbam_cpu(data)
    if not cpu:
        warnings.append("could not parse VBA-M CPU register header")
    metadata = {
        "path": display_path(path, root=root),
        "compressed_size": len(raw),
        "decompressed_size": len(data),
        "version": u32le(data, 0) if len(data) >= 4 else None,
        "rom_name": ascii_text(data[4:19]) if len(data) >= 19 else "",
        "d000_base": hex_or_none(d000_base),
        "c000_base": hex_or_none(c000_base),
        "wram_anchor_candidates": anchor_report[:12],
    }
    memory = MemoryReader(data, c000_base=c000_base, d000_base=d000_base) if d000_base is not None else None
    return Snapshot("vbam_sgm", True, memory, cpu, metadata, tuple(warnings), tuple(errors))


def load_pyboy_snapshot(path: Path, *, root: Path) -> Snapshot:
    try:
        from tools.trace import runtime as trace_runtime
    except Exception as exc:
        return Snapshot("pyboy_state", False, None, {}, {}, errors=(f"PyBoy runtime import failed: {exc}",))
    rom = root / DEFAULT_ROM
    if not rom.exists():
        return Snapshot("pyboy_state", False, None, {}, {}, errors=(f"missing ROM for PyBoy state load: {DEFAULT_ROM}",))
    pyboy = trace_runtime.open_pyboy(
        rom,
        "PyBoy is required for runtime state inspection. Import failed",
    )
    trace_runtime.disable_realtime(pyboy)
    try:
        with path.open("rb") as fh:
            pyboy.load_state(fh)
        cpu = pyboy_cpu(pyboy)
        data = bytes(int(pyboy.memory[address]) for address in range(0xC000, 0xE000))
        return Snapshot(
            "pyboy_state",
            True,
            MemoryReader(data, c000_base=0, d000_base=0x1000),
            cpu,
            {"path": display_path(path, root=root)},
        )
    except Exception as exc:
        try:
            pyboy.stop(save=False)
        except TypeError:
            pyboy.stop()
        return Snapshot("pyboy_state", False, None, {}, {}, errors=(f"could not load PyBoy state: {exc}",))
    finally:
        try:
            pyboy.stop(save=False)
        except TypeError:
            pyboy.stop()
        except Exception:
            pass


def load_battery_save_snapshot(path: Path, *, root: Path) -> Snapshot:
    try:
        from tools.trace import runtime as trace_runtime
    except Exception as exc:
        return Snapshot("battery_save_continue", False, None, {}, {}, errors=(f"PyBoy runtime import failed: {exc}",))
    rom = root / DEFAULT_ROM
    if not rom.exists():
        return Snapshot("battery_save_continue", False, None, {}, {}, errors=(f"missing ROM for battery save load: {DEFAULT_ROM}",))
    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    try:
        temp_dir = tempfile.TemporaryDirectory(prefix="runtime_state_sav_")
        work_rom = Path(temp_dir.name) / rom.name
        shutil.copy2(rom, work_rom)
        shutil.copy2(path, work_rom.with_suffix(work_rom.suffix + ".ram"))
        pyboy = trace_runtime.open_pyboy(
            work_rom,
            "PyBoy is required for battery save state inspection. Import failed",
        )
        trace_runtime.disable_realtime(pyboy)
        try:
            press_continue(pyboy)
            cpu = pyboy_cpu(pyboy)
            data = bytes(int(pyboy.memory[address]) for address in range(0xC000, 0xE000))
            return Snapshot(
                "battery_save_continue",
                True,
                MemoryReader(data, c000_base=0, d000_base=0x1000),
                cpu,
                {
                    "path": display_path(path, root=root),
                    "boot_continue": True,
                    "source": "battery_save",
                },
            )
        finally:
            try:
                pyboy.stop(save=False)
            except TypeError:
                pyboy.stop()
            except Exception:
                pass
    except Exception as exc:
        return Snapshot("battery_save_continue", False, None, {}, {}, errors=(f"could not inspect battery save: {exc}",))
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


def press_continue(pyboy) -> None:
    pyboy.tick(1800, False, False)
    for button in ("start", "a", "a", "a"):
        pyboy.button(button, delay=8)
        pyboy.tick(180, False, False)


def find_d000_base(
    data: bytes,
    labels: dict[str, dict[str, int]],
    *,
    map_catalog: dict[str, Any] | None = None,
) -> tuple[int | None, list[dict[str, Any]]]:
    offsets = symbol_offsets(labels, base=0xD000)
    required = ("wPartyCount", "wPartySpecies", "wMapGroup", "wMapNumber", "wScriptMode", "wScriptStackSize")
    if not all(name in offsets for name in required):
        return None, [{"score": 0, "reason": "missing required WRAM symbols for D000 anchor"}]
    maps = map_catalog.get("maps", {}) if isinstance(map_catalog, dict) else {}
    candidates: list[dict[str, Any]] = []
    max_base = max(0, len(data) - 0x1000)
    for base in range(max_base + 1):
        score = 0
        evidence: list[str] = []
        party_count = byte_at(data, base + offsets["wPartyCount"])
        if party_count is not None and 1 <= party_count <= 6:
            party_species_start = base + offsets["wPartySpecies"]
            species = data[party_species_start:party_species_start + party_count + 1]
            if len(species) == party_count + 1 and species[-1] == 0xFF and all(1 <= item <= 0xFD for item in species[:-1]):
                score += 50 + party_count * 4
                evidence.append(f"party_count={party_count} party_species={species.hex()}")
                if party_count >= 2:
                    score += 8
                if party_count == 6:
                    score += 4
        map_group = byte_at(data, base + offsets["wMapGroup"])
        map_number = byte_at(data, base + offsets["wMapNumber"])
        if map_group is not None and map_number is not None and 1 <= map_group <= 40 and 1 <= map_number <= 120:
            evidence.append(f"map={map_group}:{map_number}")
            map_info = maps.get(f"{map_group}:{map_number}") if isinstance(maps, dict) else None
            if isinstance(map_info, dict):
                score += 40
                evidence.append(f"known_map={map_info.get('label') or map_info.get('const')}")
                if "wMapScriptsBank" in offsets:
                    map_scripts_bank = byte_at(data, base + offsets["wMapScriptsBank"])
                    scripts_symbol = map_info.get("scripts_symbol") if isinstance(map_info.get("scripts_symbol"), dict) else None
                    expected_bank = scripts_symbol.get("bank") if isinstance(scripts_symbol, dict) else None
                    if map_scripts_bank is not None and expected_bank is not None:
                        if int(map_scripts_bank) == int(expected_bank):
                            score += 30
                            evidence.append(f"map_scripts_bank_matches={map_scripts_bank:02x}")
                        elif (int(map_scripts_bank) & 0x7F) == (int(expected_bank) & 0x7F):
                            score += 20
                            evidence.append(f"map_scripts_bank_masked_match={map_scripts_bank:02x}")
            else:
                score += 12
        script_mode = byte_at(data, base + offsets["wScriptMode"])
        stack_size = byte_at(data, base + offsets["wScriptStackSize"])
        if script_mode is not None and script_mode in SCRIPT_MODES:
            score += 12
            evidence.append(f"script_mode={script_mode}")
            if script_mode:
                score += 12
        if stack_size is not None and stack_size <= SCRIPT_STACK_CAPACITY:
            score += 8
            evidence.append(f"script_stack_size={stack_size}")
            if stack_size:
                score += 6
        script_running = byte_at(data, base + offsets.get("wScriptRunning", -1)) if "wScriptRunning" in offsets else None
        if script_running is not None and script_running in {0, 1}:
            score += 8
            evidence.append(f"script_running={script_running}")
            if script_running and script_mode:
                score += 20
        if "wMapScriptsBank" in offsets:
            map_scripts_bank = byte_at(data, base + offsets["wMapScriptsBank"])
            if map_scripts_bank is not None and 1 <= map_scripts_bank <= 0x7F:
                score += 6
                evidence.append(f"map_scripts_bank={map_scripts_bank:02x}")
        if score:
            candidates.append({"base": base, "base_hex": f"0x{base:x}", "score": score, "evidence": evidence})
    candidates.sort(key=lambda item: (-int(item["score"]), int(item["base"])))
    if not candidates or int(candidates[0]["score"]) < 80:
        return None, candidates[:20]
    return int(candidates[0]["base"]), candidates[:20]


def symbol_offsets(labels: dict[str, dict[str, int]], *, base: int) -> dict[str, int]:
    out: dict[str, int] = {}
    for name in SCRIPT_CONTEXT_SYMBOLS + ("wPartyCount", "wPartySpecies", "wXCoord", "wYCoord"):
        entry = labels.get(name)
        if not entry:
            continue
        address = int(entry["address"])
        if base <= address <= base + 0xFFF:
            out[name] = address - base
    return out


def read_context_values(memory: MemoryReader | PyBoyMemoryReader, labels: dict[str, dict[str, int]]) -> dict[str, dict[str, Any]]:
    values: dict[str, dict[str, Any]] = {}
    for name in SCRIPT_CONTEXT_SYMBOLS:
        entry = labels.get(name)
        if not entry:
            continue
        size = symbol_size(name)
        data = memory.read(int(entry["address"]), size, bank=int(entry.get("bank", 0)))
        values[name] = {
            "found": data is not None,
            "bank": int(entry.get("bank", 0)),
            "address": int(entry["address"]),
            "bank_address": f"{int(entry.get('bank', 0)):02X}:{int(entry['address']):04X}",
            "size": size,
            "bytes": list(data) if data is not None else [],
            "hex": data.hex() if data is not None else "",
            "value": value_from_bytes(data) if data is not None else None,
        }
    return values


def symbol_size(name: str) -> int:
    if name in {"wScriptPos", "wMapScriptsPointer", "wScriptAfterPointer"}:
        return 2
    if name == "wScriptStack":
        return SCRIPT_STACK_CAPACITY * 3
    return 1


def describe_map_context(
    *,
    values: dict[str, dict[str, Any]],
    labels: dict[str, dict[str, int]],
    map_catalog: dict[str, Any],
) -> dict[str, Any]:
    group = value_of(values, "wMapGroup")
    number = value_of(values, "wMapNumber")
    map_key = f"{group}:{number}" if group is not None and number is not None else ""
    map_info = map_catalog.get("maps", {}).get(map_key, {})
    name = str(map_info.get("label") or map_info.get("const") or "")
    scripts_label = f"{name}_MapScripts" if name else ""
    events_label = f"{name}_MapEvents" if name else ""
    scripts_symbol = labels.get(scripts_label, {})
    events_symbol = labels.get(events_label, {})
    expected_bank = int(scripts_symbol["bank"]) if scripts_symbol else None
    expected_addr = int(scripts_symbol["address"]) if scripts_symbol else None
    events_addr = int(events_symbol["address"]) if events_symbol else None
    script_range = None
    if expected_bank is not None and expected_addr is not None:
        end = events_addr if events_addr is not None and events_addr > expected_addr else None
        script_range = {
            "bank": expected_bank,
            "start": expected_addr,
            "start_hex": f"{expected_addr:04X}",
            "end": end,
            "end_hex": f"{end:04X}" if end is not None else "",
            "label": scripts_label,
            "events_label": events_label if events_symbol else "",
        }
    return {
        "group": group,
        "number": number,
        "key": map_key,
        "name": name,
        "constant": map_info.get("const", ""),
        "source_file": f"maps/{name}.asm" if name else "",
        "wMapScriptsBank": value_of(values, "wMapScriptsBank"),
        "wMapScriptsPointer": value_of(values, "wMapScriptsPointer"),
        "expected_script_bank": expected_bank,
        "expected_script_address": expected_addr,
        "script_range": script_range,
        "known": bool(map_info),
    }


def describe_script_vm(
    *,
    values: dict[str, dict[str, Any]],
    labels: dict[str, dict[str, int]],
    rom_bytes: bytes,
    rom_bank_count: int,
    map_context: dict[str, Any],
) -> dict[str, Any]:
    bank = value_of(values, "wScriptBank")
    pos = value_of(values, "wScriptPos")
    stack_size = value_of(values, "wScriptStackSize")
    stack_bytes = bytes(values.get("wScriptStack", {}).get("bytes", []))
    current = describe_script_pointer(
        bank=bank,
        address=pos,
        raw_bank=bank,
        rom_bytes=rom_bytes,
        rom_bank_count=rom_bank_count,
        labels=labels,
        map_context=map_context,
    )
    frames = []
    active_frames = min(
        len(stack_bytes) // 3,
        SCRIPT_STACK_CAPACITY,
        int(stack_size) if stack_size is not None else 0,
    )
    for index in range(active_frames):
        raw_bank = stack_bytes[index * 3]
        address = stack_bytes[index * 3 + 1] | (stack_bytes[index * 3 + 2] << 8)
        frames.append(
            {
                "index": index,
                **describe_script_pointer(
                    bank=raw_bank & 0x7F,
                    address=address,
                    raw_bank=raw_bank,
                    rom_bytes=rom_bytes,
                    rom_bank_count=rom_bank_count,
                    labels=labels,
                    map_context=map_context,
                ),
            }
        )
    return {
        "mode": value_of(values, "wScriptMode"),
        "mode_name": SCRIPT_MODES.get(value_of(values, "wScriptMode") or -1, "UNKNOWN"),
        "running": value_of(values, "wScriptRunning"),
        "bank": bank,
        "pos": pos,
        "bank_address": format_bank_address(bank, pos),
        "current": current,
        "stack_size": stack_size,
        "stack_capacity": SCRIPT_STACK_CAPACITY,
        "stack_frames": frames,
        "script_var": value_of(values, "wScriptVar"),
        "script_delay": value_of(values, "wScriptDelay"),
    }


def describe_script_pointer(
    *,
    bank: int | None,
    address: int | None,
    raw_bank: int | None,
    rom_bytes: bytes,
    rom_bank_count: int,
    labels: dict[str, dict[str, int]],
    map_context: dict[str, Any],
) -> dict[str, Any]:
    if bank is None or address is None:
        return {
            "raw_bank": raw_bank,
            "bank": bank,
            "address": address,
            "bank_address": "",
            "valid_executable_address": False,
            "in_current_map_script_range": False,
            "current_byte": None,
            "nearest_label": "",
        }
    valid_exec = valid_rom_pointer(bank, address, rom_bank_count)
    in_range = in_map_script_range(bank, address, map_context)
    current_byte = None
    if valid_exec and rom_bytes:
        offset = rom_offset_for_symbol(bank=bank, address=address)
        if 0 <= offset < len(rom_bytes):
            current_byte = rom_bytes[offset]
    return {
        "raw_bank": raw_bank,
        "raw_bank_hex": f"{raw_bank:02X}" if raw_bank is not None else "",
        "bank": bank,
        "address": address,
        "bank_address": format_bank_address(bank, address),
        "valid_executable_address": valid_exec,
        "in_current_map_script_range": in_range,
        "current_byte": current_byte,
        "current_byte_hex": f"{current_byte:02X}" if current_byte is not None else "",
        "nearest_label": nearest_label(labels, bank, address),
    }


def describe_cpu(
    *,
    cpu: dict[str, int],
    memory: MemoryReader | PyBoyMemoryReader | None,
    labels: dict[str, dict[str, int]],
    rom_bank_count: int,
) -> dict[str, Any]:
    pc = cpu.get("pc")
    sp = cpu.get("sp")
    signatures: list[dict[str, Any]] = []
    if pc is not None:
        pc_sig = pc_signature(pc, rom_bank_count=rom_bank_count)
        if pc_sig:
            signatures.append(pc_sig)
    top_return = None
    if sp is not None and memory is not None:
        data = memory.read(sp, 2)
        if data is not None and len(data) == 2:
            top_return = data[0] | (data[1] << 8)
            ret_sig = stack_return_signature(top_return)
            if ret_sig:
                signatures.append(ret_sig)
    if sp is not None and not (0xC000 <= sp <= 0xDFFF):
        signatures.append(
            {
                "id": "sp_outside_wram_stack",
                "severity": 82,
                "title": "SP is outside normal WRAM stack space",
                "evidence": [f"SP=${sp:04X}"],
            }
        )
    return {
        "available": bool(cpu),
        "pc": pc,
        "pc_hex": f"{pc:04X}" if pc is not None else "",
        "sp": sp,
        "sp_hex": f"{sp:04X}" if sp is not None else "",
        "top_stack_return": top_return,
        "top_stack_return_hex": f"{top_return:04X}" if top_return is not None else "",
        "registers": {key: f"{value:04X}" if key in {"pc", "sp", "af", "bc", "de", "hl"} else f"{value:02X}" for key, value in cpu.items()},
        "nearest_pc_label": nearest_label(labels, 0, pc) if pc is not None and pc < 0x4000 else "",
        "crash_signatures": signatures,
    }


def describe_trainer_context(values: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "wSeenTrainerBank": value_of(values, "wSeenTrainerBank"),
        "wScriptAfterPointer": value_of(values, "wScriptAfterPointer"),
        "wRunningTrainerBattleScript": value_of(values, "wRunningTrainerBattleScript"),
        "wTrainerBattleContextBackupActive": value_of(values, "wTrainerBattleContextBackupActive"),
        "available": any(value_of(values, name) is not None for name in (
            "wSeenTrainerBank",
            "wScriptAfterPointer",
            "wRunningTrainerBattleScript",
            "wTrainerBattleContextBackupActive",
        )),
    }


def describe_evolution_context(values: dict[str, dict[str, Any]]) -> dict[str, Any]:
    old_species = value_of(values, "wEvolutionOldSpecies")
    new_species = value_of(values, "wEvolutionNewSpecies")
    return {
        "wEvolutionOldSpecies": old_species,
        "wEvolutionNewSpecies": new_species,
        "available": old_species is not None or new_species is not None,
        "active": bool(new_species),
    }


def build_findings(
    *,
    cpu_report: dict[str, Any],
    map_context: dict[str, Any],
    script_vm: dict[str, Any],
    trainer_context: dict[str, Any],
    evolution_context: dict[str, Any],
    save_state: str,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    current = script_vm.get("current", {})
    if script_vm.get("running") and not current.get("valid_executable_address"):
        findings.append(
            finding(
                "invalid_script_pc",
                94,
                "Script VM is running from an invalid ROM address",
                [
                    f"wScriptBank:wScriptPos={script_vm.get('bank_address')}",
                    f"map={map_context.get('name') or map_context.get('key')}",
                    f"current_pointer={current.get('bank_address', '')}",
                ],
                save_state=save_state,
            )
        )
        new_species = evolution_context.get("wEvolutionNewSpecies")
        if new_species is not None and script_vm.get("bank") == new_species:
            findings.append(
                finding(
                    "script_bank_matches_evolution_species",
                    92,
                    "Active script bank matches the just-evolved species id",
                    [
                        f"wScriptBank=${int(script_vm.get('bank')):02X}",
                        f"wEvolutionNewSpecies=${int(new_species):02X}",
                        "A species id in the script bank is a strong post-evolution WRAM clobber signature.",
                    ],
                    save_state=save_state,
                )
            )
    if script_vm.get("running") and map_context.get("expected_script_bank") is not None:
        bank = script_vm.get("bank")
        expected_bank = map_context.get("expected_script_bank")
        if bank != expected_bank:
            findings.append(
                finding(
                    "script_bank_mismatch_current_map",
                    91,
                    "Active script bank does not match the current map script bank",
                    [
                        f"wScriptBank=${int(bank):02X}" if bank is not None else "wScriptBank=<unreadable>",
                        f"expected=${int(expected_bank):02X}",
                        f"map={map_context.get('name')}",
                    ],
                    save_state=save_state,
                )
            )
        elif not current.get("in_current_map_script_range"):
            findings.append(
                finding(
                    "script_pos_outside_current_map_range",
                    88,
                    "Active script pointer is outside the current map script range",
                    [
                        f"wScriptBank:wScriptPos={script_vm.get('bank_address')}",
                        f"range={format_script_range(map_context.get('script_range'))}",
                    ],
                    save_state=save_state,
                )
            )
    stack_size = script_vm.get("stack_size")
    if stack_size is not None and int(stack_size) > SCRIPT_STACK_CAPACITY:
        findings.append(
            finding(
                "script_stack_size_out_of_range",
                90,
                "Script stack size exceeds engine capacity",
                [f"wScriptStackSize={stack_size}", f"capacity={SCRIPT_STACK_CAPACITY}"],
                save_state=save_state,
            )
        )
    for frame in script_vm.get("stack_frames", []):
        if not frame.get("valid_executable_address"):
            findings.append(
                finding(
                    "invalid_script_stack_frame",
                    86,
                    "Script stack contains an invalid return pointer",
                    [
                        f"frame={frame.get('index')}",
                        f"raw_bank=${int(frame.get('raw_bank', 0)):02X}",
                        f"masked={frame.get('bank_address')}",
                    ],
                    save_state=save_state,
                )
            )
        elif map_context.get("script_range") and not frame.get("in_current_map_script_range"):
            findings.append(
                finding(
                    "script_stack_frame_outside_current_map",
                    58,
                    "Script stack frame is outside the current map script range",
                    [
                        f"frame={frame.get('index')}",
                        f"raw_bank=${int(frame.get('raw_bank', 0)):02X}",
                        f"masked={frame.get('bank_address')}",
                        f"nearest={frame.get('nearest_label', '')}",
                    ],
                    save_state=save_state,
                )
            )
    for sig in cpu_report.get("crash_signatures", []):
        findings.append(
            finding(
                str(sig.get("id")),
                int(sig.get("severity", 80)),
                str(sig.get("title")),
                list(sig.get("evidence", [])),
                save_state=save_state,
            )
        )
    if (
        trainer_context.get("wRunningTrainerBattleScript")
        and script_vm.get("running")
        and script_vm.get("bank") is not None
        and script_vm.get("bank") == trainer_context.get("wSeenTrainerBank")
        and not current.get("valid_executable_address")
    ):
        findings.append(
            finding(
                "trainer_resume_context_points_to_bad_script",
                92,
                "Trainer after-battle context points the script VM at invalid code",
                [
                    f"wSeenTrainerBank=${int(trainer_context.get('wSeenTrainerBank')):02X}",
                    f"wScriptAfterPointer=${int(trainer_context.get('wScriptAfterPointer') or 0):04X}",
                    f"wRunningTrainerBattleScript={trainer_context.get('wRunningTrainerBattleScript')}",
                ],
                save_state=save_state,
            )
        )
    running_trainer = trainer_context.get("wRunningTrainerBattleScript")
    if running_trainer is not None and int(running_trainer) not in {0, 1} and not current.get("valid_executable_address"):
        findings.append(
            finding(
                "trainer_resume_flag_corrupt",
                86,
                "Trainer resume flag contains an impossible boolean value",
                [
                    f"wRunningTrainerBattleScript=${int(running_trainer):02X}",
                    f"wScriptBank:wScriptPos={script_vm.get('bank_address')}",
                    "This points at WRAM union/stale-context corruption around the after-battle resume path.",
                ],
                save_state=save_state,
            )
        )
    return findings


def finding(
    finding_id: str,
    severity: int,
    title: str,
    evidence: list[str],
    *,
    save_state: str,
) -> dict[str, Any]:
    return {
        "id": finding_id,
        "type": "runtime_state_impossible",
        "severity": severity,
        "confidence": 0.9 if severity >= 85 else 0.72,
        "title": title,
        "evidence": evidence,
        "related_symbols": list(WATCH_SYMBOLS),
        "next_actions": state_followup_commands(
            save_state=save_state,
            rom_path=DEFAULT_ROM,
            symbols_path=DEFAULT_SYMBOLS,
            map_context={},
        )[:4],
    }


def suggested_commands(
    *,
    save_state: str,
    rom_path: str,
    symbols_path: str,
    map_context: dict[str, Any],
) -> list[str]:
    return state_followup_commands(
        save_state=save_state,
        rom_path=rom_path or DEFAULT_ROM,
        symbols_path=symbols_path or DEFAULT_SYMBOLS,
        map_context=map_context,
    )


def state_followup_commands(
    *,
    save_state: str,
    rom_path: str,
    symbols_path: str,
    map_context: dict[str, Any],
) -> list[str]:
    commands = [
        f"python -m tools.debugger state-inspect --save-state {save_state} --rom {rom_path} --symbols {symbols_path} --json-out .local\\tmp\\runtime_state.json",
        "python -m tools.debugger provenance --symbol wScriptBank --symbol wScriptPos --symbol wSeenTrainerBank --symbol wScriptAfterPointer",
        "python -m tools.debugger wram-ownership --symbol wSeenTrainerBank --symbol wScriptAfterPointer --symbol wRunningTrainerBattleScript",
        "python -m tools.debugger script-resume-gate --report .local\\tmp\\runtime_state.json",
    ]
    suffix = Path(save_state).suffix.lower()
    if suffix == ".sav":
        commands.insert(
            1,
            f"python -m tools.debugger watch --watch-symbol wScriptBank --watch-symbol wScriptPos --watch-symbol wScriptStackSize --battery-save {save_state} --out-initial-state .local\\tmp\\runtime_state_continue.state --execute",
        )
    elif not is_vbam_sgm_path(save_state):
        commands.insert(
            1,
            f"python -m tools.debugger watch --watch-symbol wScriptBank --watch-symbol wScriptPos --watch-symbol wScriptStackSize --save-state {save_state} --execute",
        )
        commands.insert(
            2,
            f"python -m tools.debugger trace-instructions --symbol ScriptEvents --symbol GetScriptByte --watch-symbol wScriptBank --watch-symbol wScriptPos --save-state {save_state} --execute --require-hit",
        )
    source = str(map_context.get("source_file") or "")
    if source:
        commands.append(f"python -m tools.debugger content-mirror --source-file {source}")
    return commands


def load_map_catalog(*, root: Path, labels: dict[str, dict[str, int]]) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    const_to_label = parse_map_attribute_labels(root / "data" / "maps" / "attributes.asm")
    maps: dict[str, dict[str, Any]] = {}
    path = root / "constants" / "map_constants.asm"
    if not path.exists():
        return {"maps": maps, "warnings": warnings, "errors": [f"missing map constants: {path}"]}
    group = 0
    number = 0
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        code = raw.split(";", 1)[0].strip()
        if not code:
            continue
        if code.startswith("newgroup "):
            group += 1
            number = 0
            continue
        match = re.match(r"map_const\s+([A-Z0-9_]+)\b", code)
        if not match:
            continue
        number += 1
        const = match.group(1)
        label = const_to_label.get(const, camel_from_const(const))
        maps[f"{group}:{number}"] = {
            "group": group,
            "number": number,
            "const": const,
            "label": label,
            "scripts_symbol": labels.get(f"{label}_MapScripts"),
            "events_symbol": labels.get(f"{label}_MapEvents"),
        }
    return {"maps": maps, "warnings": warnings, "errors": errors}


def parse_map_attribute_labels(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    pattern = re.compile(r"^\s*map_attributes\s+([A-Za-z0-9_]+)\s*,\s*([A-Z0-9_]+)\b")
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = pattern.match(raw.split(";", 1)[0])
        if match:
            out[match.group(2)] = match.group(1)
    return out


def parse_vbam_cpu(data: bytes) -> dict[str, int]:
    register_offset = 27
    if len(data) < register_offset + 12:
        return {}
    return {
        "pc": u16le(data, register_offset),
        "sp": u16le(data, register_offset + 2),
        "af": u16le(data, register_offset + 4),
        "bc": u16le(data, register_offset + 6),
        "de": u16le(data, register_offset + 8),
        "hl": u16le(data, register_offset + 10),
    }


def pyboy_cpu(pyboy: Any) -> dict[str, int]:
    register_file = getattr(pyboy, "register_file", None)
    if register_file is None:
        return {}
    out: dict[str, int] = {}
    for key in ("PC", "SP", "A", "F", "B", "C", "D", "E", "H", "L"):
        if hasattr(register_file, key):
            out[key.lower()] = int(getattr(register_file, key))
    if {"a", "f"} <= out.keys():
        out["af"] = (out["a"] << 8) | out["f"]
    if {"b", "c"} <= out.keys():
        out["bc"] = (out["b"] << 8) | out["c"]
    if {"d", "e"} <= out.keys():
        out["de"] = (out["d"] << 8) | out["e"]
    if {"h", "l"} <= out.keys():
        out["hl"] = (out["h"] << 8) | out["l"]
    return out


def value_of(values: dict[str, dict[str, Any]], name: str) -> int | None:
    value = values.get(name, {}).get("value")
    return int(value) if value is not None else None


def value_from_bytes(data: bytes | None) -> int | None:
    if data is None:
        return None
    if len(data) == 1:
        return data[0]
    if len(data) == 2:
        return data[0] | (data[1] << 8)
    return None


def valid_rom_pointer(bank: int, address: int, rom_bank_count_value: int) -> bool:
    if bank < 0:
        return False
    if rom_bank_count_value and bank >= rom_bank_count_value:
        return False
    if bank == 0:
        return 0x0000 <= address < 0x4000
    return 0x4000 <= address < 0x8000


def in_map_script_range(bank: int, address: int, map_context: dict[str, Any]) -> bool:
    script_range = map_context.get("script_range")
    if not isinstance(script_range, dict):
        return False
    if bank != script_range.get("bank"):
        return False
    start = script_range.get("start")
    end = script_range.get("end")
    if start is None:
        return False
    if end is None:
        return address >= int(start)
    return int(start) <= address < int(end)


def nearest_label(labels: dict[str, dict[str, int]], bank: int, address: int | None) -> str:
    if address is None:
        return ""
    candidates = [
        (name, int(entry["address"]))
        for name, entry in labels.items()
        if int(entry.get("bank", -1)) == bank and int(entry.get("address", 0)) <= address
    ]
    if not candidates:
        return ""
    name, label_address = max(candidates, key=lambda item: item[1])
    offset = address - label_address
    if offset == 0:
        return name
    if offset <= 0x1000:
        return f"{name}+0x{offset:X}"
    return ""


def pc_signature(pc: int, *, rom_bank_count: int) -> dict[str, Any] | None:
    if 0xE000 <= pc <= 0xFDFF:
        return {
            "id": "pc_in_echo_ram",
            "severity": 95,
            "title": "PC points into echo RAM",
            "evidence": [f"PC=${pc:04X}"],
        }
    if pc in {0x0000, 0x0100}:
        return {
            "id": "pc_at_reset_or_entry_vector",
            "severity": 88,
            "title": "PC is at a reset/start vector",
            "evidence": [f"PC=${pc:04X}"],
        }
    if 0x8000 <= pc < 0xFF80:
        return {
            "id": "pc_in_non_executable_memory",
            "severity": 90,
            "title": "PC points into non-ROM memory",
            "evidence": [f"PC=${pc:04X}"],
        }
    return None


def stack_return_signature(address: int) -> dict[str, Any] | None:
    if 0xE000 <= address <= 0xFDFF:
        return {
            "id": "stack_return_to_echo_ram",
            "severity": 93,
            "title": "Top stack return address points into echo RAM",
            "evidence": [f"return=${address:04X}"],
        }
    if 0x8000 <= address < 0xFF80:
        return {
            "id": "stack_return_to_non_executable_memory",
            "severity": 86,
            "title": "Top stack return address points into non-ROM memory",
            "evidence": [f"return=${address:04X}"],
        }
    return None


def rom_bank_count(rom_bytes: bytes) -> int:
    return len(rom_bytes) // 0x4000 if rom_bytes else 0


def format_bank_address(bank: int | None, address: int | None) -> str:
    if bank is None or address is None:
        return ""
    return f"{bank:02X}:{address:04X}"


def format_script_range(script_range: Any) -> str:
    if not isinstance(script_range, dict):
        return "<unknown>"
    end = script_range.get("end_hex") or "????"
    return f"{int(script_range.get('bank', 0)):02X}:{script_range.get('start_hex', '????')}-{end}"


def camel_from_const(value: str) -> str:
    return "".join(part.title() for part in value.lower().split("_"))


def u16le(data: bytes, offset: int) -> int:
    if offset + 1 >= len(data):
        return 0
    return data[offset] | (data[offset + 1] << 8)


def u32le(data: bytes, offset: int) -> int:
    if offset + 3 >= len(data):
        return 0
    return data[offset] | (data[offset + 1] << 8) | (data[offset + 2] << 16) | (data[offset + 3] << 24)


def byte_at(data: bytes, offset: int) -> int | None:
    if 0 <= offset < len(data):
        return data[offset]
    return None


def ascii_text(data: bytes) -> str:
    return "".join(chr(byte) for byte in data if 32 <= byte < 127).strip()


def hex_or_none(value: int | None) -> str:
    return f"0x{value:x}" if value is not None else ""
