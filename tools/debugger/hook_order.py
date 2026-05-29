from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
from typing import Any

from tools.trace import runtime as trace_runtime

from .catalog import ROOT


PROBE_ADDRESS = 0xC200
OAM_DMA_SOURCE = 0xC300
VRAM_DMA_SOURCE = 0xC400

PROBE_HOOKS = (
    {
        "id": "inc_hl_pre",
        "scenario_id": "inc_hl",
        "phase": "pre",
        "pc": 0x015C,
        "operation": "inc [hl]",
    },
    {
        "id": "inc_hl_post",
        "scenario_id": "inc_hl",
        "phase": "post",
        "pc": 0x015D,
        "operation": "nop after inc [hl]",
    },
    {
        "id": "push_bc_pre",
        "scenario_id": "push_bc",
        "phase": "pre",
        "pc": 0x0164,
        "operation": "push bc",
    },
    {
        "id": "push_bc_post",
        "scenario_id": "push_bc",
        "phase": "post",
        "pc": 0x0165,
        "operation": "nop after push bc",
    },
    {
        "id": "call_pre",
        "scenario_id": "taken_call",
        "phase": "pre",
        "pc": 0x0169,
        "operation": "call $01d0",
    },
    {
        "id": "call_target",
        "scenario_id": "taken_call",
        "phase": "post",
        "pc": 0x01D0,
        "operation": "call target",
    },
    {
        "id": "rst_pre",
        "scenario_id": "taken_rst",
        "phase": "pre",
        "pc": 0x0170,
        "operation": "rst $30",
    },
    {
        "id": "rst_vector",
        "scenario_id": "taken_rst",
        "phase": "post",
        "pc": 0x0030,
        "operation": "rst vector $0030",
    },
    {
        "id": "interrupt_request_pre",
        "scenario_id": "interrupt_entry",
        "phase": "pre",
        "pc": 0x0180,
        "operation": "ldh [$ff0f], a",
    },
    {
        "id": "interrupt_handler",
        "scenario_id": "interrupt_entry",
        "phase": "post",
        "pc": 0x0040,
        "operation": "interrupt vector $0040",
    },
    {
        "id": "oam_dma_pre",
        "scenario_id": "oam_dma_ff46",
        "phase": "pre",
        "pc": 0x0189,
        "operation": "ldh [$ff46], a",
    },
    {
        "id": "oam_dma_post",
        "scenario_id": "oam_dma_ff46",
        "phase": "post",
        "pc": 0x018B,
        "operation": "nop after FF46 OAM DMA",
    },
    {
        "id": "cgb_vram_dma_pre",
        "scenario_id": "cgb_vram_dma_ff55",
        "phase": "pre",
        "pc": 0x01A0,
        "operation": "ldh [$ff55], a",
    },
    {
        "id": "cgb_vram_dma_post",
        "scenario_id": "cgb_vram_dma_ff55",
        "phase": "post",
        "pc": 0x01A2,
        "operation": "nop after FF55 CGB VRAM DMA",
    },
)

PROBE_SCENARIOS = (
    {
        "id": "inc_hl",
        "operation": "inc [hl]",
        "category": "read_modify_write",
        "pre_hook": "inc_hl_pre",
        "post_hook": "inc_hl_post",
        "expected": {
            "pre": {"c200": "0F", "sp": "FFFE"},
            "post": {"c200": "10", "sp": "FFFE"},
        },
        "required_observations": ("pre_write", "post_write"),
    },
    {
        "id": "push_bc",
        "operation": "push bc",
        "category": "stack_write",
        "pre_hook": "push_bc_pre",
        "post_hook": "push_bc_post",
        "expected": {
            "pre": {"sp": "FFFE"},
            "post": {"sp": "FFFC", "fffc": "34", "fffd": "12"},
        },
        "required_observations": ("pre_write", "post_write"),
    },
    {
        "id": "taken_call",
        "operation": "call $01d0",
        "category": "control_flow_stack_write",
        "pre_hook": "call_pre",
        "post_hook": "call_target",
        "expected": {
            "pre": {"sp": "FFFC"},
            "post": {"pc": "01D0", "sp": "FFFA", "fffa": "6C", "fffb": "01"},
        },
        "required_observations": ("pre_write", "post_write"),
    },
    {
        "id": "taken_rst",
        "operation": "rst $30",
        "category": "control_flow_stack_write",
        "pre_hook": "rst_pre",
        "post_hook": "rst_vector",
        "expected": {
            "pre": {"sp": "FFFA"},
            "post": {"pc": "0030", "sp": "FFF8", "fff8": "71", "fff9": "01"},
        },
        "required_observations": ("pre_write", "post_write"),
    },
    {
        "id": "interrupt_entry",
        "operation": "interrupt vector entry",
        "category": "interrupt_entry",
        "pre_hook": "interrupt_request_pre",
        "post_hook": "interrupt_handler",
        "expected": {
            "pre": {"pc": "0180", "sp": "FFF8"},
            "post": {"pc": "0040", "sp": "FFF6", "fff6": "82", "fff7": "01"},
        },
        "required_observations": ("pre_write", "post_write", "post_interrupt"),
    },
    {
        "id": "oam_dma_ff46",
        "operation": "FF46 OAM DMA write",
        "category": "dma",
        "pre_hook": "oam_dma_pre",
        "post_hook": "oam_dma_post",
        "expected": {
            "pre": {"fe00": "00", "c300": "A5"},
            "post": {"fe00": "A5", "c300": "A5"},
        },
        "required_observations": ("pre_write", "post_dma"),
    },
    {
        "id": "cgb_vram_dma_ff55",
        "operation": "FF55 CGB general VRAM DMA write",
        "category": "dma",
        "pre_hook": "cgb_vram_dma_pre",
        "post_hook": "cgb_vram_dma_post",
        "expected": {
            "pre": {"vram_8000": "00", "c400": "5A", "ff55": "FF"},
            "post": {"vram_8000": "5A", "c400": "5A", "ff55": "FF"},
        },
        "required_observations": ("pre_write", "post_dma"),
    },
)

NINTENDO_LOGO = bytes(
    [
        0xCE,
        0xED,
        0x66,
        0x66,
        0xCC,
        0x0D,
        0x00,
        0x0B,
        0x03,
        0x73,
        0x00,
        0x83,
        0x00,
        0x0C,
        0x00,
        0x0D,
        0x00,
        0x08,
        0x11,
        0x1F,
        0x88,
        0x89,
        0x00,
        0x0E,
        0xDC,
        0xCC,
        0x6E,
        0xE6,
        0xDD,
        0xDD,
        0xD9,
        0x99,
        0xBB,
        0xBB,
        0x67,
        0x63,
        0x6E,
        0x0E,
        0xEC,
        0xCC,
        0xDD,
        0xDC,
        0x99,
        0x9F,
        0xBB,
        0xB9,
        0x33,
        0x3E,
    ]
)


def build_hook_order_probe_report(
    *,
    execute: bool = False,
    frames: int = 90,
    root: Path = ROOT,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if frames < 1:
        errors.append("--frames must be positive")
    observations: list[dict[str, Any]] = []
    if execute and not errors:
        observations, run_errors = execute_hook_order_probe(frames=frames)
        errors.extend(run_errors)
    elif not execute:
        warnings.append("hook-order probe was planned only; rerun with --execute to validate PyBoy hook timing")

    event_matrix = hook_order_event_matrix(observations)
    checks = hook_order_checks(event_matrix)
    passed = bool(execute and checks and all(item["passed"] for item in checks))
    if execute and not observations and not errors:
        errors.append("hook-order probe executed but no probe hooks fired")
    if execute and observations and not passed:
        errors.append("hook-order probe did not observe the expected hook-order matrix")

    rom_bytes = hook_order_probe_rom()
    return {
        "schema_version": 2,
        "kind": "unified_debugger_hook_order_probe",
        "root": str(root),
        "valid": not errors,
        "executed": execute,
        "passed": passed,
        "proof_status": "runtime_observed" if passed else "planned_only",
        "proof_boundary": "debugger_hook_runtime_matrix_not_non_mutating_cpu_event_stream",
        "hook_mechanism": "pyboy_opcode_replacement_breakpoint",
        "non_mutating_instruction_events": False,
        "pre_fetch_runtime_observed": False,
        "pre_fetch_blocker": (
            "PyBoy hooks are reached through debugger breakpoints that replace the opcode byte; "
            "this matrix observes callback state around the original instruction, not a clean original-opcode fetch event."
        ),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "frames": frames,
        "probe_rom_sha256": hashlib.sha256(rom_bytes).hexdigest().upper(),
        "probe_address": f"{PROBE_ADDRESS:04X}",
        "expected_target_count": len(PROBE_HOOKS),
        "scenario_count": len(PROBE_SCENARIOS),
        "observation_count": len(observations),
        "observations": observations,
        "event_matrix_count": len(event_matrix),
        "event_matrix": event_matrix,
        "check_count": len(checks),
        "checks": checks,
        "commands": ["python -m tools.debugger hook-order-probe --execute"],
        "known_limits": [
            "This probe validates PyBoy debugger-hook callback timing for generated CPU, interrupt, and DMA micro-ROM scenarios.",
            "It records whether callbacks observe pre-write, post-write, post-interrupt, and post-DMA state; it does not observe a non-mutating original-opcode pre-fetch event.",
            "PyBoy's hook mechanism is still opcode-replacement breakpoint instrumentation, so this is runtime ground truth for that debugger surface, not a proof-grade CPU event recorder.",
            "The DMA rows observe stock PyBoy's immediate copy behavior; they do not prove hardware-accurate OAM DMA timing, RAM bus restrictions, CGB HDMA timing, or LCD-mode edge behavior.",
        ],
    }


def execute_hook_order_probe(*, frames: int) -> tuple[list[dict[str, Any]], list[str]]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        rom_path = root / "hook_order_probe.gbc"
        rom_path.write_bytes(hook_order_probe_rom())
        pyboy = None
        observations: list[dict[str, Any]] = []
        errors: list[str] = []
        try:
            pyboy = trace_runtime.open_pyboy(
                rom_path,
                "PyBoy is required for hook-order timing validation. Import failed",
            )
            trace_runtime.disable_realtime(pyboy)
            callbacks = {int(target["pc"]): target for target in PROBE_HOOKS}
            for pc, target in callbacks.items():
                pyboy.hook_register(0, pc, make_probe_callback(pyboy, target, observations), None)
            for _frame in range(frames):
                pyboy.tick(1, False, False)
                if len({item["id"] for item in observations}) >= len(PROBE_HOOKS):
                    break
        except SystemExit as exc:
            errors.append(str(exc))
        except Exception as exc:
            errors.append(f"hook-order probe failed: {exc}")
        finally:
            if pyboy is not None:
                for target in PROBE_HOOKS:
                    try:
                        pyboy.hook_deregister(0, int(target["pc"]))
                    except Exception:
                        pass
                try:
                    pyboy.stop(save=False)
                except TypeError:
                    pyboy.stop()
                except Exception:
                    pass
        return observations, errors


def make_probe_callback(pyboy: Any, target: dict[str, Any], observations: list[dict[str, Any]]):
    def callback(_ctx: Any) -> None:
        observations.append(sample_probe_state(pyboy, target=target))

    return callback


def sample_probe_state(pyboy: Any, *, target: dict[str, Any]) -> dict[str, Any]:
    registers = getattr(pyboy, "register_file", None)
    pc = int(getattr(registers, "PC", int(target["pc"]))) if registers is not None else int(target["pc"])
    flags = int(getattr(registers, "F", 0)) if registers is not None else 0
    sp = int(getattr(registers, "SP", 0)) if registers is not None else 0
    sample = {
        "id": str(target["id"]),
        "scenario_id": str(target["scenario_id"]),
        "phase": str(target["phase"]),
        "pc": pc,
        "pc_hex": f"{pc & 0xFFFF:04X}",
        "expected_pc": f"{int(target['pc']) & 0xFFFF:04X}",
        "pc_not_incremented": (pc & 0xFFFF) == (int(target["pc"]) & 0xFFFF),
        "operation": str(target["operation"]),
        "hook_mechanism": "pyboy_opcode_replacement_breakpoint",
        "pre_fetch_observed": False,
        "pre_execute_callback": True,
        "sp": sp,
        "sp_hex": f"{sp & 0xFFFF:04X}",
        "flags": flags,
        "flags_hex": f"{flags & 0xFF:02X}",
        "carry": bool(flags & 0x10),
        "memory": {
            "c200": read_memory_hex(pyboy, PROBE_ADDRESS),
            "c300": read_memory_hex(pyboy, OAM_DMA_SOURCE),
            "c400": read_memory_hex(pyboy, VRAM_DMA_SOURCE),
            "fffc": read_memory_hex(pyboy, 0xFFFC),
            "fffd": read_memory_hex(pyboy, 0xFFFD),
            "fffa": read_memory_hex(pyboy, 0xFFFA),
            "fffb": read_memory_hex(pyboy, 0xFFFB),
            "fff8": read_memory_hex(pyboy, 0xFFF8),
            "fff9": read_memory_hex(pyboy, 0xFFF9),
            "fff6": read_memory_hex(pyboy, 0xFFF6),
            "fff7": read_memory_hex(pyboy, 0xFFF7),
            "fe00": read_memory_hex(pyboy, 0xFE00),
            "vram_8000": read_memory_hex(pyboy, 0x8000),
            "ff55": read_memory_hex(pyboy, 0xFF55),
        },
    }
    for name in ("A", "B", "C", "D", "E", "H", "L"):
        value = int(getattr(registers, name, 0)) if registers is not None else 0
        sample[name] = value
        sample[f"{name.lower()}_hex"] = f"{value & 0xFF:02X}"
    sample["value"] = parse_hex_byte(sample["memory"]["c200"])
    sample["value_hex"] = sample["memory"]["c200"]
    sample["address"] = f"{PROBE_ADDRESS:04X}"
    return sample


def read_memory_hex(pyboy: Any, address: int) -> str:
    try:
        return f"{int(pyboy.memory[address]) & 0xFF:02X}"
    except Exception as exc:
        return f"error:{exc}"


def hook_order_event_matrix(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for item in observations:
        by_id.setdefault(str(item.get("id", "")), item)
    rows: list[dict[str, Any]] = []
    for scenario in PROBE_SCENARIOS:
        pre = by_id.get(str(scenario["pre_hook"]))
        post = by_id.get(str(scenario["post_hook"]))
        expected = scenario.get("expected", {}) if isinstance(scenario.get("expected"), dict) else {}
        pre_expected = expected.get("pre", {}) if isinstance(expected.get("pre"), dict) else {}
        post_expected = expected.get("post", {}) if isinstance(expected.get("post"), dict) else {}
        pre_matches = expected_matches(pre, pre_expected)
        post_matches = expected_matches(post, post_expected)
        required = set(str(item) for item in scenario.get("required_observations", ()))
        observes = {
            "pre_fetch": False,
            "pre_write": bool(pre and pre.get("pc_not_incremented") and pre_matches),
            "post_write": bool(post and post_matches),
            "post_interrupt": bool(
                scenario["category"] == "interrupt_entry"
                and post
                and post.get("pc_hex") == "0040"
                and post_matches
            ),
            "post_dma": bool(scenario["category"] == "dma" and post and post_matches),
        }
        passed = bool(
            pre
            and post
            and pre.get("pc_not_incremented")
            and post.get("pc_not_incremented")
            and all(observes.get(name, False) for name in required)
        )
        rows.append(
            {
                "id": scenario["id"],
                "operation": scenario["operation"],
                "category": scenario["category"],
                "hook_mechanism": "pyboy_opcode_replacement_breakpoint",
                "non_mutating_instruction_event": False,
                "observes_pre_fetch": observes["pre_fetch"],
                "observes_pre_write": observes["pre_write"],
                "observes_post_write": observes["post_write"],
                "observes_post_interrupt": observes["post_interrupt"],
                "observes_post_dma": observes["post_dma"],
                "pre_hook": scenario["pre_hook"],
                "post_hook": scenario["post_hook"],
                "pre_observed": bool(pre),
                "post_observed": bool(post),
                "pre_pc": pre.get("pc_hex", "") if pre else "",
                "post_pc": post.get("pc_hex", "") if post else "",
                "pre_expected": pre_expected,
                "post_expected": post_expected,
                "pre_memory": pre.get("memory", {}) if pre else {},
                "post_memory": post.get("memory", {}) if post else {},
                "pre_sp": pre.get("sp_hex", "") if pre else "",
                "post_sp": post.get("sp_hex", "") if post else "",
                "required_observations": sorted(required),
                "passed": passed,
                "pre_fetch_blocker": (
                    "hook is an opcode-replacement debugger breakpoint, not a non-mutating original opcode fetch event"
                ),
            }
        )
    return rows


def hook_order_checks(event_matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for row in event_matrix:
        checks.append(
            {
                "id": row["id"],
                "operation": row["operation"],
                "category": row["category"],
                "observed": bool(row.get("pre_observed") and row.get("post_observed")),
                "expected_pc": str(row.get("pre_pc", "")),
                "expected_value_hex": str(row.get("post_expected", {}).get("c200", "")),
                "observed_value_hex": str(row.get("post_memory", {}).get("c200", "")),
                "expected_carry": None,
                "observed_carry": None,
                "observes_pre_fetch": bool(row.get("observes_pre_fetch")),
                "observes_pre_write": bool(row.get("observes_pre_write")),
                "observes_post_write": bool(row.get("observes_post_write")),
                "observes_post_interrupt": bool(row.get("observes_post_interrupt")),
                "observes_post_dma": bool(row.get("observes_post_dma")),
                "non_mutating_instruction_event": bool(row.get("non_mutating_instruction_event")),
                "passed": bool(row.get("passed")),
            }
        )
    return checks


def expected_matches(observation: dict[str, Any] | None, expected: dict[str, str]) -> bool:
    if observation is None:
        return False
    for key, expected_value in expected.items():
        if key == "pc":
            actual = str(observation.get("pc_hex", ""))
        elif key == "sp":
            actual = str(observation.get("sp_hex", ""))
        else:
            memory = observation.get("memory") if isinstance(observation.get("memory"), dict) else {}
            actual = str(memory.get(key, ""))
        if actual.upper() != str(expected_value).upper():
            return False
    return True


def parse_hex_byte(value: str) -> int | None:
    try:
        return int(str(value), 16) & 0xFF
    except ValueError:
        return None


def hook_order_probe_rom() -> bytes:
    rom = bytearray([0] * 0x8000)
    rom[0x0030:0x0033] = bytes([0xC3, 0x71, 0x01])
    rom[0x0040:0x0043] = bytes([0xC3, 0x81, 0x01])
    rom[0x0100:0x0104] = bytes([0xC3, 0x50, 0x01, 0x00])
    rom[0x0104:0x0134] = NINTENDO_LOGO
    title = b"HOOKMATRIX"
    rom[0x0134 : 0x0134 + len(title)] = title
    rom[0x0143] = 0x80
    rom[0x0147] = 0x00
    rom[0x0148] = 0x00
    rom[0x0149] = 0x00
    rom[0x0150 : 0x01A5] = bytes(
        [
            0xF3,  # di
            0x31,
            0xFE,
            0xFF,  # ld sp, $fffe
            0xAF,  # xor a
            0xE0,
            0x40,  # ldh [$ff40], a ; LCD off for deterministic VRAM/OAM samples
            0x21,
            0x00,
            0xC2,  # ld hl, $c200
            0x36,
            0x0F,  # ld [hl], $0f
            0x34,  # inc [hl]
            0x00,  # nop
            0x31,
            0xFE,
            0xFF,  # ld sp, $fffe
            0x01,
            0x34,
            0x12,  # ld bc, $1234
            0xC5,  # push bc
            0x00,  # nop
            0x31,
            0xFC,
            0xFF,  # ld sp, $fffc
            0xCD,
            0xD0,
            0x01,  # call $01d0
            0x00,  # nop
            0x31,
            0xFA,
            0xFF,  # ld sp, $fffa
            0xF7,  # rst $30
            0x00,  # nop
            0x31,
            0xF8,
            0xFF,  # ld sp, $fff8
            0xAF,  # xor a
            0xE0,
            0x0F,  # ldh [$ff0f], a
            0x3E,
            0x01,  # ld a, $01
            0xE0,
            0xFF,  # ldh [$ffff], a
            0xFB,  # ei
            0x00,  # nop
            0x3E,
            0x01,  # ld a, $01
            0xE0,
            0x0F,  # ldh [$ff0f], a ; request VBlank interrupt
            0x21,
            0x00,
            0xC3,  # ld hl, $c300
            0x36,
            0xA5,  # ld [hl], $a5
            0x3E,
            0xC3,  # ld a, $c3
            0xE0,
            0x46,  # ldh [$ff46], a ; OAM DMA
            0x00,  # nop
            0x21,
            0x00,
            0xC4,  # ld hl, $c400
            0x36,
            0x5A,  # ld [hl], $5a
            0x3E,
            0xC4,  # ld a, $c4
            0xE0,
            0x51,  # ldh [$ff51], a
            0xAF,  # xor a
            0xE0,
            0x52,  # ldh [$ff52], a
            0x3E,
            0x80,  # ld a, $80
            0xE0,
            0x53,  # ldh [$ff53], a
            0xAF,  # xor a
            0xE0,
            0x54,  # ldh [$ff54], a
            0xAF,  # xor a
            0xE0,
            0x55,  # ldh [$ff55], a ; general CGB VRAM DMA, one block
            0x00,  # nop
            0x18,
            0xFE,  # jr -2
        ]
    )
    rom[0x01D0:0x01D3] = bytes([0xC3, 0x6D, 0x01])
    rom[0x014D] = header_checksum(rom)
    return bytes(rom)


def header_checksum(rom: bytearray) -> int:
    value = 0
    for offset in range(0x0134, 0x014D):
        value = (value - int(rom[offset]) - 1) & 0xFF
    return value
