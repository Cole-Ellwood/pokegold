#!/usr/bin/env python3
"""Case-library retrieval for the Compounding Loop.

Given a public-state fingerprint, return K nearest past cases. This is
the heart of the compounding mechanism — at fresh prediction time the
predictor queries this to surface lessons that should fire.

Retrieval policy: four-level relaxation. We try the narrowest match
first; if that returns fewer than K results, relax one dimension and
try again, accumulating without duplicates.

  L0 EXACT — same active_user.species + active_opp.species + turn_bucket
             + side_conditions (sorted equal).
  L1 RELAX_TURN — same actives, side_conditions, any turn_bucket.
  L2 RELAX_SIDES — same actives, any turn_bucket, any side_conditions.
  L3 SINGLE_SIDE — at least one of (user.species, opp.species) matches.

Each returned case carries a `match_level` (0..3) so the predictor can
prioritize tighter matches.

This module reads tier=study cases only. Validation and sealed_exam
cases (if any contamination ever slipped through) are filtered out
defensively — verify_loop_state.py is the primary guard but defense
in depth is cheap.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LIB = HERE / "case_library"


@dataclass
class RetrievedCase:
    case: dict[str, Any]
    match_level: int


def _species(actor: dict[str, Any] | None) -> str:
    if not actor:
        return ""
    return actor.get("species") or ""


def _norm_sides(conds: list[str] | None) -> tuple[str, ...]:
    return tuple(sorted(conds or []))


def load_cases(cases_path: Path) -> list[dict]:
    if not cases_path.exists():
        return []
    rows: list[dict] = []
    for line in cases_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return [c for c in rows if c.get("tier") == "study"]


def _level0(fp: dict, cases: list[dict]) -> list[dict]:
    user_sp = _species(fp.get("active_user"))
    opp_sp = _species(fp.get("active_opp"))
    tb = fp.get("turn_bucket")
    us = _norm_sides(fp.get("side_conditions_user"))
    os = _norm_sides(fp.get("side_conditions_opp"))
    out = []
    for c in cases:
        cfp = c.get("fingerprint", {})
        if _species(cfp.get("active_user")) != user_sp:
            continue
        if _species(cfp.get("active_opp")) != opp_sp:
            continue
        if cfp.get("turn_bucket") != tb:
            continue
        if _norm_sides(cfp.get("side_conditions_user")) != us:
            continue
        if _norm_sides(cfp.get("side_conditions_opp")) != os:
            continue
        out.append(c)
    return out


def _level1(fp: dict, cases: list[dict]) -> list[dict]:
    user_sp = _species(fp.get("active_user"))
    opp_sp = _species(fp.get("active_opp"))
    us = _norm_sides(fp.get("side_conditions_user"))
    os = _norm_sides(fp.get("side_conditions_opp"))
    out = []
    for c in cases:
        cfp = c.get("fingerprint", {})
        if _species(cfp.get("active_user")) != user_sp:
            continue
        if _species(cfp.get("active_opp")) != opp_sp:
            continue
        if _norm_sides(cfp.get("side_conditions_user")) != us:
            continue
        if _norm_sides(cfp.get("side_conditions_opp")) != os:
            continue
        out.append(c)
    return out


def _level2(fp: dict, cases: list[dict]) -> list[dict]:
    user_sp = _species(fp.get("active_user"))
    opp_sp = _species(fp.get("active_opp"))
    out = []
    for c in cases:
        cfp = c.get("fingerprint", {})
        if _species(cfp.get("active_user")) != user_sp:
            continue
        if _species(cfp.get("active_opp")) != opp_sp:
            continue
        out.append(c)
    return out


def _level3(fp: dict, cases: list[dict]) -> list[dict]:
    user_sp = _species(fp.get("active_user"))
    opp_sp = _species(fp.get("active_opp"))
    out = []
    for c in cases:
        cfp = c.get("fingerprint", {})
        cu = _species(cfp.get("active_user"))
        co = _species(cfp.get("active_opp"))
        if cu == user_sp or co == opp_sp:
            out.append(c)
    return out


def retrieve(
    fp: dict,
    cases: list[dict],
    *,
    k: int = 5,
) -> list[RetrievedCase]:
    """Return up to k cases ordered by match_level (tightest first).

    Within a level, order is stable (insertion order from cases.jsonl —
    older cases first). Duplicates across levels are filtered.
    """
    seen_ids: set[str] = set()
    out: list[RetrievedCase] = []
    for level, fn in enumerate([_level0, _level1, _level2, _level3]):
        if len(out) >= k:
            break
        for c in fn(fp, cases):
            cid = c.get("case_id")
            if cid in seen_ids:
                continue
            seen_ids.add(cid)
            out.append(RetrievedCase(case=c, match_level=level))
            if len(out) >= k:
                break
    return out


def format_retrieval_for_predictor(retrieved: list[RetrievedCase]) -> str:
    """Render retrieved cases as a compact string for inclusion in the
    pre-freeze context. Keeps each case to one line; predictor sees
    lesson + match_level."""
    if not retrieved:
        return "(no cases fired)"
    lines = [f"Retrieved {len(retrieved)} case(s):"]
    for r in retrieved:
        c = r.case
        cid = c.get("case_id", "?")
        cls = c.get("pro_reasoning_class", "?")
        fm = c.get("failure_mode", "?")
        lesson = c.get("lesson", "")
        lines.append(f"  L{r.match_level} {cid} [{cls}/{fm}] {lesson}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fingerprint", type=Path, required=True, help="path to a JSON file with the fingerprint")
    parser.add_argument("--cases", type=Path, default=LIB / "cases.jsonl")
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args(argv)
    fp = json.loads(args.fingerprint.read_text(encoding="utf-8"))
    if "fingerprint" in fp:
        fp = fp["fingerprint"]
    cases = load_cases(args.cases)
    retrieved = retrieve(fp, cases, k=args.k)
    print(format_retrieval_for_predictor(retrieved))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
