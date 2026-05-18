from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
from typing import Any

from tools.trace import runtime as trace_runtime

from .catalog import ROOT


PROBE_ADDRESS = 0xC200
PROBE_TARGETS = (
    {"id": "inc_pre", "pc": 0x0159, "operation": "inc [hl]", "expected_value": "0F", "expected_carry": None},
    {"id": "dec_pre", "pc": 0x015A, "operation": "dec [hl]", "expected_value": "10", "expected_carry": None},
    {"id": "dec_post", "pc": 0x015B, "operation": "scf after dec [hl]", "expected_value": "0F", "expected_carry": None},
    {"id": "rl_pre", "pc": 0x015C, "operation": "rl [hl]", "expected_value": "0F", "expected_carry": True},
    {"id": "rl_post", "pc": 0x015E, "operation": "xor a after rl [hl]", "expected_value": "1F", "expected_carry": False},
    {"id": "rr_pre", "pc": 0x015F, "operation": "rr [hl]", "expected_value": "1F", "expected_carry": False},
    {"id": "rr_post", "pc": 0x0161, "operation": "nop after rr [hl]", "expected_value": "0F", "expected_carry": None},
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

    checks = hook_order_checks(observations)
    passed = bool(execute and checks and all(item["passed"] for item in checks))
    if execute and not observations and not errors:
        errors.append("hook-order probe executed but no probe hooks fired")
    if execute and observations and not passed:
        errors.append("hook-order probe did not observe the expected pre-instruction memory/register state")

    rom_bytes = hook_order_probe_rom()
    return {
        "schema_version": 1,
        "kind": "unified_debugger_hook_order_probe",
        "root": str(root),
        "valid": not errors,
        "executed": execute,
        "passed": passed,
        "proof_status": "runtime_observed" if passed else "planned_only",
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "frames": frames,
        "probe_rom_sha256": hashlib.sha256(rom_bytes).hexdigest().upper(),
        "probe_address": f"{PROBE_ADDRESS:04X}",
        "expected_target_count": len(PROBE_TARGETS),
        "observation_count": len(observations),
        "observations": observations,
        "check_count": len(checks),
        "checks": checks,
        "commands": ["python -m tools.debugger hook-order-probe --execute"],
        "known_limits": [
            "This probe validates PyBoy hook callback timing for a generated ROM with simple CPU memory/register operations.",
            "It proves that the callback samples pre-instruction state for the tested inc/dec/rl/rr [hl] sequence on this runtime, not full CPU reverse execution.",
            "It does not model PPU/audio/timer side effects or prove hook ordering for every possible save-state and interrupt interleaving.",
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
            callbacks = {int(target["pc"]): target for target in PROBE_TARGETS}
            for pc, target in callbacks.items():
                pyboy.hook_register(0, pc, make_probe_callback(pyboy, target, observations), None)
            for _frame in range(frames):
                pyboy.tick(1, False, False)
                if len({item["id"] for item in observations}) >= len(PROBE_TARGETS):
                    break
        except SystemExit as exc:
            errors.append(str(exc))
        except Exception as exc:
            errors.append(f"hook-order probe failed: {exc}")
        finally:
            if pyboy is not None:
                for target in PROBE_TARGETS:
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
    value = int(pyboy.memory[PROBE_ADDRESS]) & 0xFF
    return {
        "id": str(target["id"]),
        "pc": pc,
        "pc_hex": f"{pc & 0xFFFF:04X}",
        "operation": str(target["operation"]),
        "address": f"{PROBE_ADDRESS:04X}",
        "value": value,
        "value_hex": f"{value:02X}",
        "flags": flags,
        "flags_hex": f"{flags & 0xFF:02X}",
        "carry": bool(flags & 0x10),
    }


def hook_order_checks(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for item in observations:
        by_id.setdefault(str(item.get("id", "")), item)
    checks: list[dict[str, Any]] = []
    for target in PROBE_TARGETS:
        observation = by_id.get(str(target["id"]))
        expected_carry = target["expected_carry"]
        carry_ok = True if expected_carry is None or observation is None else observation.get("carry") is expected_carry
        value_ok = bool(observation and observation.get("value_hex") == target["expected_value"])
        checks.append(
            {
                "id": target["id"],
                "operation": target["operation"],
                "expected_pc": f"{int(target['pc']):04X}",
                "expected_value_hex": target["expected_value"],
                "expected_carry": expected_carry,
                "observed": bool(observation),
                "observed_value_hex": observation.get("value_hex", "") if observation else "",
                "observed_flags_hex": observation.get("flags_hex", "") if observation else "",
                "observed_carry": observation.get("carry") if observation else None,
                "passed": bool(observation and value_ok and carry_ok),
            }
        )
    return checks


def hook_order_probe_rom() -> bytes:
    rom = bytearray([0] * 0x8000)
    rom[0x0100:0x0104] = bytes([0xC3, 0x50, 0x01, 0x00])
    rom[0x0104:0x0134] = NINTENDO_LOGO
    title = b"HOOKPROBE"
    rom[0x0134 : 0x0134 + len(title)] = title
    rom[0x0143] = 0x80
    rom[0x0147] = 0x00
    rom[0x0148] = 0x00
    rom[0x0149] = 0x00
    rom[0x0150 : 0x0164] = bytes(
        [
            0xF3,  # di
            0x31,
            0xFE,
            0xFF,  # ld sp, $fffe
            0x21,
            0x00,
            0xC2,  # ld hl, $c200
            0x36,
            0x0F,  # ld [hl], $0f
            0x34,  # inc [hl]
            0x35,  # dec [hl]
            0x37,  # scf
            0xCB,
            0x16,  # rl [hl]
            0xAF,  # xor a
            0xCB,
            0x1E,  # rr [hl]
            0x00,  # nop
            0x18,
            0xFE,  # jr -2
        ]
    )
    rom[0x014D] = header_checksum(rom)
    return bytes(rom)


def header_checksum(rom: bytearray) -> int:
    value = 0
    for offset in range(0x0134, 0x014D):
        value = (value - int(rom[offset]) - 1) & 0xFF
    return value
