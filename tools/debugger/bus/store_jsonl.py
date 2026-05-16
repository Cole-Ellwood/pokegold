"""JSONL streaming event store.

Append-only: every span is written as one JSON line. Suitable for
streaming runs and as the canonical intermediate format before batch
conversion to Parquet/DuckDB.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from .events import Span


class JSONLStore:
    """Append-only JSONL event store."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._count = 0

    @property
    def path(self) -> Path:
        return self._path

    @property
    def count(self) -> int:
        return self._count

    def open(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, span: Span) -> None:
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(span.to_dict(), separators=(",", ":")) + "\n")
        self._count += 1

    def append_many(self, spans: list[Span]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as f:
            for span in spans:
                f.write(json.dumps(span.to_dict(), separators=(",", ":")) + "\n")
                self._count += 1

    def read_all(self) -> list[Span]:
        if not self._path.exists():
            return []
        spans: list[Span] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                spans.append(Span.from_dict(json.loads(line)))
        return spans

    def iter_spans(self) -> Iterator[Span]:
        if not self._path.exists():
            return
        with self._path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield Span.from_dict(json.loads(line))

    def iter_dicts(self) -> Iterator[dict[str, Any]]:
        if not self._path.exists():
            return
        with self._path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

    def filter_by_name(self, name: str) -> list[Span]:
        return [s for s in self.iter_spans() if s.name == name]

    def filter_by_attr(self, key: str, value: Any) -> list[Span]:
        return [s for s in self.iter_spans() if s.attributes.get(key) == value]
