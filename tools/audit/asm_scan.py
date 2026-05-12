from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SKIP_DIR_PARTS = {
    ".git",
    "rgbds-1.0.1",
    "tools",
    "scripts",
    ".local",
    "workspace",
    ".claude",
}
TOP_LABEL_RE = re.compile(r"^(?P<label>[A-Za-z_][A-Za-z0-9_]*):{1,2}\s*(?:;.*)?$")
LOCAL_LABEL_RE = re.compile(r"^\s*(?P<label>\.[A-Za-z_][A-Za-z0-9_]*):?\s*(?:;.*)?$")
SECTION_RE = re.compile(r'^\s*SECTION\s+"', re.IGNORECASE)


@dataclass(frozen=True)
class AsmFile:
    path: Path
    lines: list[str]


@dataclass
class AsmCache:
    _lines: dict[Path, list[str]]

    def __init__(self) -> None:
        self._lines = {}

    def lines(self, path: Path) -> list[str]:
        if path not in self._lines:
            self._lines[path] = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return self._lines[path]


def code_part(line: str) -> str:
    return line.split(";", 1)[0].strip()


def has_keep_marker(line: str) -> bool:
    if ";" not in line:
        return False
    comment = line.split(";", 1)[1].lower()
    return "keep" in comment


def iter_asm_paths(
    *,
    root: Path = ROOT,
    roots: Iterable[Path] | None = None,
    skip_dir_parts: set[str] = DEFAULT_SKIP_DIR_PARTS,
) -> list[Path]:
    base_roots = list(roots) if roots is not None else [root]
    files: list[Path] = []
    for base in base_roots:
        if not base.exists():
            continue
        for path in base.rglob("*.asm"):
            rel_parts = path.relative_to(root).parts
            if any(part in skip_dir_parts for part in rel_parts):
                continue
            files.append(path)
    return sorted(files)


def iter_asm_files(
    *,
    root: Path = ROOT,
    roots: Iterable[Path] | None = None,
    skip_dir_parts: set[str] = DEFAULT_SKIP_DIR_PARTS,
    cache: AsmCache | None = None,
) -> list[AsmFile]:
    source_cache = cache or AsmCache()
    return [
        AsmFile(path=path, lines=source_cache.lines(path))
        for path in iter_asm_paths(root=root, roots=roots, skip_dir_parts=skip_dir_parts)
    ]
