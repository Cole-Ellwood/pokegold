from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from tools.trace import runtime as trace_runtime

from .catalog import ROOT
from .ingest import sha256_file
from .provenance import display_path, parse_symbol_table, resolve_path
from .workflow import command_is_runnable


DEFAULT_ROM = "pokegold.gbc"
DEFAULT_SYMBOLS = "pokegold.sym"
AUDIO_STATE_SYMBOLS = {
    "wMusicID": 1,
    "wMusicBank": 1,
    "wMapMusic": 1,
    "wMusicFade": 1,
    "wMusicFadeID": 2,
    "wPokegearRadioMusicPlaying": 1,
    "wChannel1Flags1": 1,
    "wChannel2Flags1": 1,
    "wChannel3Flags1": 1,
    "wChannel4Flags1": 1,
}
AUDIO_REGISTERS = {
    "rAUD1SWEEP": 0xFF10,
    "rAUD1LEN": 0xFF11,
    "rAUD1ENV": 0xFF12,
    "rAUD1LOW": 0xFF13,
    "rAUD1HIGH": 0xFF14,
    "rAUD2LEN": 0xFF16,
    "rAUD2ENV": 0xFF17,
    "rAUD2LOW": 0xFF18,
    "rAUD2HIGH": 0xFF19,
    "rAUD3ENA": 0xFF1A,
    "rAUD3LEN": 0xFF1B,
    "rAUD3LEVEL": 0xFF1C,
    "rAUD3LOW": 0xFF1D,
    "rAUD3HIGH": 0xFF1E,
    "rAUD4LEN": 0xFF20,
    "rAUD4ENV": 0xFF21,
    "rAUD4POLY": 0xFF22,
    "rAUD4GO": 0xFF23,
    "rAUDVOL": 0xFF24,
    "rAUDTERM": 0xFF25,
    "rAUDENA": 0xFF26,
}
WAVE_RAM_START = 0xFF30
WAVE_RAM_SIZE = 0x10
SOUND_BUFFER_SAMPLE_BYTES = 512


def build_audio_snapshot_report(
    *,
    rom_path: str = DEFAULT_ROM,
    symbols_path: str = DEFAULT_SYMBOLS,
    save_state: str = "",
    frames: int = 0,
    execute: bool = False,
    root: Path = ROOT,
) -> dict[str, Any]:
    rom = resolve_path(rom_path, root=root)
    sym = resolve_path(symbols_path, root=root)
    save = resolve_path(save_state, root=root) if save_state else None
    errors: list[str] = []
    warnings: list[str] = []
    if frames < 0:
        errors.append("--frames must be non-negative")
    if not rom.exists():
        errors.append(f"missing ROM: {rom_path}")
    if not sym.exists():
        errors.append(f"missing symbols: {symbols_path}")
    if execute and not save_state:
        errors.append("--execute requires --save-state")
    if save is not None and not save.exists():
        errors.append(f"missing save-state: {save_state}")

    symbol_table = parse_symbol_table(sym) if sym.exists() else {}
    planned_symbols = planned_audio_symbols(symbol_table)
    commands = audio_snapshot_commands(
        rom_path=rom_path,
        symbols_path=symbols_path,
        save_state=save_state,
        frames=frames,
    )
    report = {
        "schema_version": 1,
        "kind": "unified_debugger_audio_snapshot",
        "root": str(root),
        "valid": not errors,
        "proof_status": "runtime_observed" if execute and not errors else "planned_only",
        "evidence_class": "pyboy_audio_snapshot",
        "hardware_behavior_proven": False,
        "hardware_proof_status": "not_proven",
        "hardware_proof_boundary": "PyBoy APU register and sound-buffer digests are emulator-observed, not hardware audio proof.",
        "executed": execute and not errors,
        "rom": display_path(rom, root=root),
        "rom_sha256": sha256_file(rom) if rom.exists() else "",
        "symbols": display_path(sym, root=root),
        "symbols_sha256": sha256_file(sym) if sym.exists() else "",
        "save_state": display_path(save, root=root) if save is not None else "",
        "frames": frames,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "planned_symbol_count": len(planned_symbols),
        "planned_symbols": planned_symbols,
        "symbol_state_count": 0,
        "symbol_state": [],
        "register_count": 0,
        "registers": {},
        "register_details": [],
        "audio_state": {},
        "channel_state": [],
        "wave_ram": {},
        "sound_buffer_count": 0,
        "sound_buffer": {},
        "command_count": len(commands),
        "commands": commands,
        "runnable_commands": [command for command in commands if command_is_runnable(command)],
        "blocked_commands": [command for command in commands if not command_is_runnable(command)],
        "known_limits": [
            "This captures CPU-visible audio engine state and hardware registers from a bounded runtime point; it is not a full audio playback or mixer mirror.",
            "Sound buffer evidence is a bounded PyBoy frame buffer digest/sample; it proves emulator-visible samples existed at this capture point but does not prove full song playback quality.",
            "Audio output quality still requires listening, waveform capture, or a dedicated APU mirror.",
            "Use effect traces or dynamic taint to prove which instruction wrote an audio register or music-engine state after a snapshot differs from expectation.",
        ],
    }
    if errors or not execute:
        return report

    report.update(
        execute_audio_snapshot(
            rom=rom,
            save_state=save,
            frames=frames,
            symbol_table=symbol_table,
        )
    )
    return report


def planned_audio_symbols(symbol_table: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for symbol, size in AUDIO_STATE_SYMBOLS.items():
        entry = symbol_table.get(symbol)
        out.append(
            {
                "symbol": symbol,
                "found": bool(entry),
                "bank": entry.get("bank_hex", "") if entry else "",
                "address": entry.get("address_hex", "") if entry else "",
                "size": size,
            }
        )
    return out


def execute_audio_snapshot(
    *,
    rom: Path,
    save_state: Path | None,
    frames: int,
    symbol_table: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    pyboy = trace_runtime.open_pyboy(
        rom,
        "PyBoy is required for audio snapshot capture. Import failed",
    )
    trace_runtime.disable_realtime(pyboy)
    try:
        if save_state is not None:
            with save_state.open("rb") as fh:
                pyboy.load_state(fh)
        for _ in range(frames):
            pyboy.tick(1, False, False)
        registers = {
            name: f"{read_byte(pyboy, address):02X}"
            for name, address in AUDIO_REGISTERS.items()
        }
        wave_ram = memory_block_snapshot(
            pyboy,
            name="wave_ram",
            address=WAVE_RAM_START,
            size=WAVE_RAM_SIZE,
        )
        symbol_state = audio_symbol_state(pyboy, symbol_table=symbol_table)
        sound_buffer = sound_buffer_snapshot(pyboy)
        return {
            "symbol_state_count": len(symbol_state),
            "symbol_state": symbol_state,
            "register_count": len(registers),
            "registers": registers,
            "register_details": audio_register_details(registers),
            "audio_state": audio_state(registers),
            "channel_state": channel_state(registers),
            "wave_ram": wave_ram,
            "sound_buffer_count": 1 if sound_buffer else 0,
            "sound_buffer": sound_buffer,
        }
    finally:
        try:
            pyboy.stop(save=False)
        except TypeError:
            pyboy.stop()


def audio_symbol_state(pyboy: Any, *, symbol_table: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for symbol, size in AUDIO_STATE_SYMBOLS.items():
        entry = symbol_table.get(symbol)
        if not entry:
            continue
        address = int(entry["address"])
        bank = int(entry["bank"])
        values, bank_read = read_memory_range(pyboy, address=address, size=size, bank=bank)
        out.append(
            {
                "symbol": symbol,
                "address": f"{address:04X}",
                "bank": f"{bank:02X}",
                "size": size,
                "bank_read": bank_read,
                "value_hex": bytes(values).hex().upper(),
                "value": values[0] if size == 1 and values else None,
            }
        )
    return out


def memory_block_snapshot(pyboy: Any, *, name: str, address: int, size: int) -> dict[str, Any]:
    values, bank_read = read_memory_range(pyboy, address=address, size=size, bank=None)
    return {
        "name": name,
        "address": f"{address:04X}",
        "size": size,
        "bank_read": bank_read,
        "sha256": hashlib.sha256(bytes(values)).hexdigest(),
        "nonzero_count": sum(1 for value in values if value),
        "unique_byte_count": len(set(values)),
        "sample_hex": bytes(values).hex().upper(),
    }


def sound_buffer_snapshot(pyboy: Any) -> dict[str, Any]:
    sound = getattr(pyboy, "sound", None)
    if sound is None:
        return {}
    buffer_value, source = sound_buffer_value(sound)
    data = buffer_to_bytes(buffer_value)
    if not data:
        return {}
    sample = data[:SOUND_BUFFER_SAMPLE_BYTES]
    digest = hashlib.sha256(data).hexdigest()
    shape = buffer_shape(buffer_value)
    out: dict[str, Any] = {
        "kind": "pyboy_sound_buffer",
        "evidence_class": "pyboy_sound_buffer_digest",
        "hardware_behavior_proven": False,
        "source": source,
        "sample_rate": int_or_zero(getattr(sound, "sample_rate", 0)),
        "raw_buffer_head": int_or_zero(getattr(sound, "raw_buffer_head", 0)),
        "raw_buffer_format": str(getattr(sound, "raw_buffer_format", "")),
        "raw_buffer_length": int_or_zero(getattr(sound, "raw_buffer_length", 0)),
        "byte_count": len(data),
        "sample_size": len(sample),
        "sha256": digest,
        "buffer": f"sha256:{digest}",
        "sample_hex": sample.hex().upper(),
        "truncated": len(sample) < len(data),
    }
    if shape:
        out["shape"] = shape
        out["sample_count"] = int_or_zero(shape[0])
        if len(shape) > 1:
            out["channel_count"] = int_or_zero(shape[1])
    dtype = getattr(buffer_value, "dtype", "")
    if dtype:
        out["dtype"] = str(dtype)
    return out


def sound_buffer_value(sound: Any) -> tuple[Any, str]:
    try:
        value = getattr(sound, "ndarray")
        if callable(value):
            value = value()
        copied = buffer_copy(value)
        if buffer_to_bytes(copied):
            return copied, "pyboy.sound.ndarray"
    except Exception:
        pass
    try:
        raw = getattr(sound, "raw_buffer")
        if callable(raw):
            raw = raw()
        head = int_or_zero(getattr(sound, "raw_buffer_head", 0))
        if head > 0:
            raw = raw[:head]
        return buffer_copy(raw), "pyboy.sound.raw_buffer"
    except Exception:
        return b"", ""


def buffer_copy(value: Any) -> Any:
    copier = getattr(value, "copy", None)
    if callable(copier):
        try:
            return copier()
        except Exception:
            return value
    return value


def buffer_to_bytes(value: Any) -> bytes:
    if value is None:
        return b""
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, memoryview):
        return value.tobytes()
    tobytes = getattr(value, "tobytes", None)
    if callable(tobytes):
        try:
            data = tobytes()
        except Exception:
            data = b""
        return bytes(data) if data else b""
    if isinstance(value, (list, tuple)):
        return bytes(flatten_buffer_values(value))
    try:
        return bytes(value)
    except (TypeError, ValueError):
        return b""


def flatten_buffer_values(value: Any) -> list[int]:
    if isinstance(value, (list, tuple)):
        out: list[int] = []
        for item in value:
            out.extend(flatten_buffer_values(item))
        return out
    try:
        return [int(value) & 0xFF]
    except (TypeError, ValueError):
        return []


def buffer_shape(value: Any) -> list[int]:
    shape = getattr(value, "shape", None)
    if shape is None:
        return []
    try:
        return [int(part) for part in shape]
    except (TypeError, ValueError):
        return []


def int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def audio_register_details(registers: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "address": f"{address:04X}",
            "value_hex": registers.get(name, "00"),
            "value": int(registers.get(name, "00"), 16),
        }
        for name, address in AUDIO_REGISTERS.items()
    ]


def read_memory_range(pyboy: Any, *, address: int, size: int, bank: int | None) -> tuple[list[int], str]:
    if bank is None:
        return ([read_byte(pyboy, (address + offset) & 0xFFFF) for offset in range(size)], "unbanked")
    try:
        return (
            [
                int(pyboy.memory[bank, (address + offset) & 0xFFFF]) & 0xFF
                for offset in range(size)
            ],
            "exact",
        )
    except Exception:
        return ([read_byte(pyboy, (address + offset) & 0xFFFF) for offset in range(size)], "fallback_unbanked")


def read_byte(pyboy: Any, address: int) -> int:
    return int(pyboy.memory[address]) & 0xFF


def audio_state(registers: dict[str, str]) -> dict[str, Any]:
    audena = int(registers.get("rAUDENA", "00"), 16)
    audvol = int(registers.get("rAUDVOL", "00"), 16)
    audterm = int(registers.get("rAUDTERM", "00"), 16)
    return {
        "audio_enabled": bool(audena & 0x80),
        "channel_enable_mask": audena & 0x0F,
        "left_volume": (audvol >> 4) & 0x07,
        "right_volume": audvol & 0x07,
        "left_vin": bool(audvol & 0x80),
        "right_vin": bool(audvol & 0x08),
        "terminal_mask": audterm,
    }


def channel_state(registers: dict[str, str]) -> list[dict[str, Any]]:
    enabled = int(registers.get("rAUDENA", "00"), 16) & 0x0F
    return [
        {
            "channel": 1,
            "enabled": bool(enabled & 0x01),
            "dac_enabled": bool(int(registers.get("rAUD1ENV", "00"), 16) & 0xF8),
            "frequency_low": registers.get("rAUD1LOW", "00"),
            "frequency_high": registers.get("rAUD1HIGH", "00"),
        },
        {
            "channel": 2,
            "enabled": bool(enabled & 0x02),
            "dac_enabled": bool(int(registers.get("rAUD2ENV", "00"), 16) & 0xF8),
            "frequency_low": registers.get("rAUD2LOW", "00"),
            "frequency_high": registers.get("rAUD2HIGH", "00"),
        },
        {
            "channel": 3,
            "enabled": bool(enabled & 0x04),
            "dac_enabled": bool(int(registers.get("rAUD3ENA", "00"), 16) & 0x80),
            "frequency_low": registers.get("rAUD3LOW", "00"),
            "frequency_high": registers.get("rAUD3HIGH", "00"),
        },
        {
            "channel": 4,
            "enabled": bool(enabled & 0x08),
            "dac_enabled": bool(int(registers.get("rAUD4ENV", "00"), 16) & 0xF8),
            "noise_poly": registers.get("rAUD4POLY", "00"),
            "trigger": registers.get("rAUD4GO", "00"),
        },
    ]


def audio_snapshot_commands(*, rom_path: str, symbols_path: str, save_state: str, frames: int) -> list[str]:
    base = ["python -m tools.debugger audio-snapshot"]
    if rom_path:
        base.extend(["--rom", quote_arg(rom_path)])
    if symbols_path:
        base.extend(["--symbols", quote_arg(symbols_path)])
    if save_state:
        base.extend(["--save-state", quote_arg(save_state)])
    if frames:
        base.extend(["--frames", str(frames)])
    if save_state:
        commands = [" ".join([*base, "--execute"])]
    else:
        commands = [" ".join([*base, "--save-state", "<state>", "--execute"])]
    trace = ["python -m tools.debugger trace-instructions"]
    if rom_path:
        trace.extend(["--rom", quote_arg(rom_path)])
    if symbols_path:
        trace.extend(["--symbols", quote_arg(symbols_path)])
    if save_state:
        trace.extend(["--save-state", quote_arg(save_state)])
    else:
        trace.extend(["--save-state", "<state>"])
    for symbol in ("PlayMusic", "_PlayMusic", "ParseMusic", "ParseMusicCommand"):
        trace.extend(["--symbol", symbol])
    for symbol in ("wMusicID", "wMusicBank"):
        trace.extend(["--watch-symbol", symbol])
    commands.append(" ".join([*trace, "--execute", "--require-hit"]))
    commands.append("python -m tools.debugger dynamic-taint --report <audio-trace.json> --sink-symbol wMusicID --sink-address FF26")
    commands.append("python -m tools.debugger visualize --report <audio-snapshot.json> --format html --out .local\\tmp\\audio_snapshot.html")
    return commands


def quote_arg(value: Any) -> str:
    text = str(value)
    if not text:
        return '""'
    if any(char.isspace() for char in text):
        return '"' + text.replace('"', '\\"') + '"'
    return text
