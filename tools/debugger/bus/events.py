"""OTel-shaped event schema for the debugger.

Every observable event is a Span in a tree. Spans nest: a battle_turn
contains score_rules which contain memory_reads; a damage_chain contains
BattleCommand_* calls.

This module defines the data model. Storage backends (JSONL, Parquet,
DuckDB) consume these objects.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SpanKind(Enum):
    INSTRUCTION = "instruction"
    MEMORY_WRITE = "memory_write"
    MEMORY_READ = "memory_read"
    REGISTER_CHANGE = "register_change"
    FUNCTION_CALL = "function_call"
    FUNCTION_RETURN = "function_return"
    SCORE_RULE = "score_rule"
    BATTLE_TURN = "battle_turn"
    DAMAGE_CHAIN = "damage_chain"
    SCENARIO = "scenario"
    AUDIT = "audit"
    CUSTOM = "custom"


@dataclass
class Span:
    """One event in the debugger trace tree."""
    trace_id: str
    span_id: str
    name: str
    kind: SpanKind = SpanKind.CUSTOM
    parent_span_id: str = ""
    start_cycle: int = 0
    end_cycle: int = 0
    attributes: dict[str, Any] = field(default_factory=dict)
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "name": self.name,
            "kind": self.kind.value,
            "start_cycle": self.start_cycle,
            "end_cycle": self.end_cycle,
            "timestamp_ns": self.timestamp_ns,
            "attributes": self.attributes,
        }
        if self.parent_span_id:
            d["parent_span_id"] = self.parent_span_id
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Span:
        return cls(
            trace_id=d["trace_id"],
            span_id=d["span_id"],
            name=d["name"],
            kind=SpanKind(d.get("kind", "custom")),
            parent_span_id=d.get("parent_span_id", ""),
            start_cycle=d.get("start_cycle", 0),
            end_cycle=d.get("end_cycle", 0),
            attributes=d.get("attributes", {}),
            timestamp_ns=d.get("timestamp_ns", 0),
        )


def new_trace_id(prefix: str = "run") -> str:
    return f"{prefix}_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"


def new_span_id() -> str:
    return uuid.uuid4().hex[:16]


SpanCallback = Any  # Callable[[Span], None]


class EventBus:
    """Pub/sub event bus for debugger spans.

    Subscribers register interest by span name or kind. Only matching
    spans are delivered, keeping overhead bounded.
    """

    def __init__(self) -> None:
        self._subscribers_by_name: dict[str, list[SpanCallback]] = {}
        self._subscribers_by_kind: dict[SpanKind, list[SpanCallback]] = {}
        self._catch_all: list[SpanCallback] = []
        self._span_count = 0

    def subscribe(self, name_or_kind: str | SpanKind, callback: SpanCallback) -> None:
        if isinstance(name_or_kind, SpanKind):
            self._subscribers_by_kind.setdefault(name_or_kind, []).append(callback)
        else:
            self._subscribers_by_name.setdefault(name_or_kind, []).append(callback)

    def subscribe_all(self, callback: SpanCallback) -> None:
        self._catch_all.append(callback)

    def emit(self, span: Span) -> None:
        self._span_count += 1
        for cb in self._catch_all:
            cb(span)
        for cb in self._subscribers_by_name.get(span.name, ()):
            cb(span)
        for cb in self._subscribers_by_kind.get(span.kind, ()):
            cb(span)

    @property
    def span_count(self) -> int:
        return self._span_count

    def reset(self) -> None:
        self._span_count = 0
