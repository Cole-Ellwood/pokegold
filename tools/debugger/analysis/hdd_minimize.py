"""Hierarchical Delta Debugging (HDD) over scenario JSON trees.

Drops whole turns first, then individual moves, then byte-level
fields.  Much faster convergence than vanilla ddmin on structured
battle scenarios.

Reference: Misherghi & Su, "HDD: Hierarchical Delta Debugging",
           ICSE 2006.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Any, Callable


TestFunc = Callable[[dict[str, Any]], bool]


@dataclass
class MinimizeResult:
    """Result of an HDD minimization pass."""
    original_size: int
    minimized_size: int
    reduction_ratio: float
    original: dict[str, Any]
    minimized: dict[str, Any]
    iterations: int = 0
    fields_removed: list[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        return (
            f"Reduced {self.original_size} → {self.minimized_size} "
            f"fields ({self.reduction_ratio:.0%} reduction, "
            f"{self.iterations} iterations)"
        )


def _count_leaves(obj: Any) -> int:
    if isinstance(obj, dict):
        return sum(_count_leaves(v) for v in obj.values())
    if isinstance(obj, list):
        return sum(_count_leaves(v) for v in obj)
    return 1


def _json_size(obj: Any) -> int:
    return len(json.dumps(obj, separators=(",", ":")))


def _ddmin_list(
    items: list[Any],
    test_fn: Callable[[list[Any]], bool],
    granularity: int = 2,
) -> list[Any]:
    """Classic ddmin on a list: find minimal failing subset."""
    if len(items) <= 1:
        return items

    n = min(granularity, len(items))
    chunk_size = max(1, len(items) // n)

    for i in range(n):
        start = i * chunk_size
        end = start + chunk_size if i < n - 1 else len(items)
        complement = items[:start] + items[end:]
        if test_fn(complement):
            return _ddmin_list(complement, test_fn, 2)

    for i in range(n):
        start = i * chunk_size
        end = start + chunk_size if i < n - 1 else len(items)
        chunk = items[start:end]
        if test_fn(chunk):
            return _ddmin_list(chunk, test_fn, 2)

    if n < len(items):
        return _ddmin_list(items, test_fn, min(2 * n, len(items)))

    return items


def minimize_scenario(
    scenario: dict[str, Any],
    test_fn: TestFunc,
    *,
    preserve_keys: set[str] | None = None,
) -> MinimizeResult:
    """HDD minimize a scenario JSON tree.

    Args:
        scenario: The full scenario dict.
        test_fn: Returns True if the (possibly reduced) scenario still
                 triggers the bug / mismatch being investigated.
        preserve_keys: Top-level keys that must not be removed (e.g.
                       ``{"scenario_id", "seed"}``).
    """
    preserve = preserve_keys or {"scenario_id"}
    original_size = _count_leaves(scenario)
    best = copy.deepcopy(scenario)
    iterations = 0
    removed: list[str] = []

    removable_keys = [k for k in best if k not in preserve]
    for key in removable_keys:
        candidate = copy.deepcopy(best)
        del candidate[key]
        iterations += 1
        if test_fn(candidate):
            best = candidate
            removed.append(key)

    for key in list(best.keys()):
        if key in preserve:
            continue
        val = best[key]
        if isinstance(val, list) and len(val) > 1:
            def list_test(subset: list[Any], k: str = key, b: dict = best) -> bool:
                c = copy.deepcopy(b)
                c[k] = subset
                return test_fn(c)

            minimized_list = _ddmin_list(val, list_test)
            iterations += 1
            if len(minimized_list) < len(val):
                best[key] = minimized_list
                removed.append(f"{key}[{len(val)}→{len(minimized_list)}]")

    for key in list(best.keys()):
        if key in preserve:
            continue
        val = best[key]
        if isinstance(val, dict):
            inner_removable = [k for k in val if k not in preserve]
            for inner_key in inner_removable:
                candidate = copy.deepcopy(best)
                del candidate[key][inner_key]
                iterations += 1
                if test_fn(candidate):
                    best = candidate
                    removed.append(f"{key}.{inner_key}")

    for key in list(best.keys()):
        if key in preserve:
            continue
        val = best[key]
        if isinstance(val, list):
            for i, item in enumerate(val):
                if isinstance(item, dict):
                    item_removable = [k for k in item if k not in preserve]
                    for inner_key in item_removable:
                        candidate = copy.deepcopy(best)
                        del candidate[key][i][inner_key]
                        iterations += 1
                        if test_fn(candidate):
                            best = candidate
                            removed.append(f"{key}[{i}].{inner_key}")

    minimized_size = _count_leaves(best)
    ratio = 1.0 - (minimized_size / original_size) if original_size > 0 else 0.0

    return MinimizeResult(
        original_size=original_size,
        minimized_size=minimized_size,
        reduction_ratio=ratio,
        original=scenario,
        minimized=best,
        iterations=iterations,
        fields_removed=removed,
    )


def minimize_from_jsonl(
    jsonl_path: str,
    scenario_id: str,
    test_fn: TestFunc,
    *,
    preserve_keys: set[str] | None = None,
) -> MinimizeResult | None:
    """Load a scenario from JSONL by id and minimize it."""
    from pathlib import Path

    path = Path(jsonl_path)
    if not path.exists():
        return None

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if obj.get("scenario_id") == scenario_id:
            return minimize_scenario(obj, test_fn, preserve_keys=preserve_keys)

    return None


__all__ = [
    "MinimizeResult",
    "TestFunc",
    "minimize_scenario",
    "minimize_from_jsonl",
]
