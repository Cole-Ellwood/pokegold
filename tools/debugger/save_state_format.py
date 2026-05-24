from __future__ import annotations

import gzip
from pathlib import Path
from typing import Any


def is_vbam_sgm_path(path: str | Path) -> bool:
    return Path(path).suffix.lower() == ".sgm"


def is_battery_save_path(path: str | Path) -> bool:
    return Path(path).suffix.lower() == ".sav"


def inspect_save_state_header(path: Path) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "extension": path.suffix.lower(),
        "opaque": False,
    }
    if not path.exists() or path.is_dir():
        return metadata
    raw = path.read_bytes()
    metadata["compressed"] = raw.startswith(b"\x1f\x8b")
    try:
        data = gzip.decompress(raw) if metadata["compressed"] else raw
    except (OSError, gzip.BadGzipFile) as exc:
        metadata["format"] = "unknown_save_state"
        metadata["opaque"] = True
        metadata["parse_warning"] = f"could not decompress VBA-M .sgm candidate: {exc}"
        return metadata
    metadata["decompressed_size_bytes"] = len(data)
    if path.suffix.lower() == ".sgm" and len(data) >= 27:
        metadata["format"] = "vbam_sgm"
        metadata["version"] = u32le(data, 0)
        metadata["rom_name"] = ascii_text(data[4:19])
        metadata["suggested_commands"] = [
            f"python -m tools.debugger state-inspect --save-state {path} --rom pokegold.gbc --symbols pokegold.sym",
        ]
    elif path.suffix.lower() == ".sav":
        metadata["format"] = "battery_save"
        metadata["size_bytes"] = len(data)
        metadata["suggested_commands"] = [
            f"python -m tools.debugger state-inspect --save-state {path} --rom pokegold.gbc --symbols pokegold.sym",
            f"python -m tools.debugger watch --battery-save {path} --watch-symbol wScriptBank --watch-symbol wScriptPos --execute",
        ]
    else:
        metadata["format"] = "unknown_save_state"
        metadata["opaque"] = True
    return metadata


def u32le(data: bytes, offset: int) -> int:
    if offset + 3 >= len(data):
        return 0
    return data[offset] | (data[offset + 1] << 8) | (data[offset + 2] << 16) | (data[offset + 3] << 24)


def ascii_text(data: bytes) -> str:
    return "".join(chr(byte) for byte in data if 32 <= byte < 127).strip()
