"""LLM-assisted hypothesis tracker.

Persists debug hypotheses with verifications, outcomes, and citations.
Every LLM claim must cite file:line — the citation grounder rejects
claims without verifiable source references.

Storage: ``audit/hypothesis_tree.jsonl``
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Citation:
    """A source-grounded citation."""
    file: str
    line: int = 0
    text: str = ""
    verified: bool = False

    def __str__(self) -> str:
        loc = f"{self.file}:{self.line}" if self.line else self.file
        tag = "✓" if self.verified else "?"
        return f"[{tag}] {loc}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "line": self.line,
            "text": self.text,
            "verified": self.verified,
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> Citation:
        return Citation(
            file=d.get("file", ""),
            line=d.get("line", 0),
            text=d.get("text", ""),
            verified=d.get("verified", False),
        )


@dataclass
class Hypothesis:
    """One debug hypothesis with verification state."""
    id: str = ""
    parent_id: str = ""
    statement: str = ""
    status: str = "open"  # open, confirmed, rejected, refined, blocked
    confidence: float = 0.5
    citations: list[Citation] = field(default_factory=list)
    evidence_for: list[str] = field(default_factory=list)
    evidence_against: list[str] = field(default_factory=list)
    verification_cmd: str = ""
    verification_result: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: float = 0.0
    updated_at: float = 0.0
    session_id: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.created_at:
            self.created_at = time.time()
        self.updated_at = self.created_at

    def confirm(self, evidence: str = "") -> None:
        self.status = "confirmed"
        if evidence:
            self.evidence_for.append(evidence)
        self.updated_at = time.time()

    def reject(self, evidence: str = "") -> None:
        self.status = "rejected"
        if evidence:
            self.evidence_against.append(evidence)
        self.updated_at = time.time()

    def refine(self, new_statement: str) -> Hypothesis:
        self.status = "refined"
        self.updated_at = time.time()
        child = Hypothesis(
            parent_id=self.id,
            statement=new_statement,
            confidence=self.confidence,
            tags=list(self.tags),
            session_id=self.session_id,
        )
        return child

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "statement": self.statement,
            "status": self.status,
            "confidence": self.confidence,
            "citations": [c.to_dict() for c in self.citations],
            "evidence_for": self.evidence_for,
            "evidence_against": self.evidence_against,
            "verification_cmd": self.verification_cmd,
            "verification_result": self.verification_result,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "session_id": self.session_id,
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> Hypothesis:
        h = Hypothesis(
            id=d.get("id", ""),
            parent_id=d.get("parent_id", ""),
            statement=d.get("statement", ""),
            status=d.get("status", "open"),
            confidence=d.get("confidence", 0.5),
            evidence_for=d.get("evidence_for", []),
            evidence_against=d.get("evidence_against", []),
            verification_cmd=d.get("verification_cmd", ""),
            verification_result=d.get("verification_result", ""),
            tags=d.get("tags", []),
            created_at=d.get("created_at", 0.0),
            updated_at=d.get("updated_at", 0.0),
            session_id=d.get("session_id", ""),
        )
        h.citations = [Citation.from_dict(c) for c in d.get("citations", [])]
        return h


class CitationGrounder:
    """Validates that LLM claims cite real file:line references."""

    def __init__(self, project_root: Path) -> None:
        self.root = project_root

    def validate(self, citation: Citation) -> bool:
        """Check that the cited file:line exists."""
        path = self.root / citation.file
        if not path.exists():
            return False

        if citation.line > 0:
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
                if citation.line > len(lines):
                    return False
            except OSError:
                return False

        citation.verified = True
        return True

    def ground_all(self, hypothesis: Hypothesis) -> list[Citation]:
        """Validate all citations in a hypothesis. Return unverified ones."""
        unverified = []
        for c in hypothesis.citations:
            if not self.validate(c):
                unverified.append(c)
        return unverified


class HypothesisTracker:
    """Persistent hypothesis tree stored as JSONL."""

    def __init__(self, store_path: Path) -> None:
        self.store_path = store_path
        self._hypotheses: dict[str, Hypothesis] = {}
        self._load()

    def _load(self) -> None:
        if not self.store_path.exists():
            return
        for line in self.store_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                h = Hypothesis.from_dict(d)
                self._hypotheses[h.id] = h
            except (json.JSONDecodeError, KeyError):
                continue

    def _save(self) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(h.to_dict(), separators=(",", ":")) for h in self._hypotheses.values()]
        self.store_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def add(self, hypothesis: Hypothesis) -> Hypothesis:
        self._hypotheses[hypothesis.id] = hypothesis
        self._save()
        return hypothesis

    def get(self, hypothesis_id: str) -> Hypothesis | None:
        return self._hypotheses.get(hypothesis_id)

    def update(self, hypothesis: Hypothesis) -> None:
        hypothesis.updated_at = time.time()
        self._hypotheses[hypothesis.id] = hypothesis
        self._save()

    def list_all(self, status: str | None = None) -> list[Hypothesis]:
        result = list(self._hypotheses.values())
        if status:
            result = [h for h in result if h.status == status]
        return sorted(result, key=lambda h: h.updated_at, reverse=True)

    def children(self, hypothesis_id: str) -> list[Hypothesis]:
        return [h for h in self._hypotheses.values() if h.parent_id == hypothesis_id]

    def tree_summary(self, max_depth: int = 3) -> str:
        roots = [h for h in self._hypotheses.values() if not h.parent_id]
        lines: list[str] = []
        for root in sorted(roots, key=lambda h: h.created_at, reverse=True):
            self._render_tree(root, lines, 0, max_depth)
        return "\n".join(lines) if lines else "(empty hypothesis tree)"

    def _render_tree(self, h: Hypothesis, lines: list[str], depth: int, max_depth: int) -> None:
        if depth >= max_depth:
            return
        indent = "  " * depth
        status_icon = {"open": "?", "confirmed": "+", "rejected": "-",
                       "refined": "~", "blocked": "!"}
        icon = status_icon.get(h.status, "?")
        cites = f" ({len(h.citations)} cites)" if h.citations else ""
        lines.append(f"{indent}[{icon}] {h.id}: {h.statement}{cites}")
        for child in self.children(h.id):
            self._render_tree(child, lines, depth + 1, max_depth)

    @property
    def count(self) -> int:
        return len(self._hypotheses)


__all__ = [
    "Citation",
    "CitationGrounder",
    "Hypothesis",
    "HypothesisTracker",
]
