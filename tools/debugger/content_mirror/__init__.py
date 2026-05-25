"""Content-mirror package: source-vs-built-ROM byte comparisons for RGBDS data.

Eight per-content-type modules (maps, audio, incbin, asset_tables, scripts,
text, movement, labeled_data) sit next to a thin orchestrator in
``invariants.py``. The public surface re-exported here is what the rest of
``tools/debugger`` and the test suite call.
"""

from __future__ import annotations

from .helpers import (
    INCBIN_RE,
    code_after_label,
    first_token,
    parse_int_literal,
    split_label,
    strip_comment,
    unique_list,
)
from .invariants import build_content_mirror_report
from .movement import parse_movement_blocks
from .rom_context import load_rom_mirror_context, rom_offset_for_symbol
from .scripts import parse_script_blocks
from .text import parse_text_blocks

__all__ = [
    "INCBIN_RE",
    "build_content_mirror_report",
    "code_after_label",
    "first_token",
    "load_rom_mirror_context",
    "parse_int_literal",
    "parse_movement_blocks",
    "parse_script_blocks",
    "parse_text_blocks",
    "rom_offset_for_symbol",
    "split_label",
    "strip_comment",
    "unique_list",
]
