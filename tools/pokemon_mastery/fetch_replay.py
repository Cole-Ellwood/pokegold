#!/usr/bin/env python3
"""Showdown replay search + downloader for the Compounding Loop.

Pure-stdlib client. Picks one unseen gen2ou replay above the rating
threshold, assigns it to the study or validation tier following the
4:1 study:validation policy and the per-tier rating gates
(study>=1400, validation>=1600), downloads the raw .log, and appends
a row to case_library/replay_index.jsonl.

Tier policy is deterministic given partition state, so two sessions
calling pick() at the same time will assign the same way for any
given replay rating. The HTTP layer is isolated in _fetch_json / _fetch_text
so tests can patch it without network access.

CLI:
  python tools/pokemon_mastery/fetch_replay.py pick \\
    [--format gen2ou] [--min-rating 1400] \\
    [--download-dir tmp/pokemon_mastery_replays] \\
    [--for-tier auto|study|validation|sealed_exam]

The for-tier flag is normally `auto` (use the partition policy). Set
explicitly to `sealed_exam` only at final-exam time.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
LIB = HERE / "case_library"
DEFAULT_DOWNLOAD_DIR = HERE.parent.parent / "tmp" / "pokemon_mastery_replays"

STUDY_RATING_FLOOR = 1400
VALIDATION_RATING_FLOOR = 1600
STUDY_TO_VALIDATION_RATIO = 4

SEARCH_URL_TEMPLATE = "https://replay.pokemonshowdown.com/search.json?format={fmt}"
LOG_URL_TEMPLATE = "https://replay.pokemonshowdown.com/{replay_id}.log"


_USER_AGENT = "pokemon-mastery-compounding-loop/0.1 (+local)"


def _open(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    return urllib.request.urlopen(req, timeout=30)


def _fetch_json(url: str) -> list[dict]:
    with _open(url) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body)


def _fetch_text(url: str) -> str:
    with _open(url) as resp:
        return resp.read().decode("utf-8", errors="replace")


def read_replay_index(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise ValueError(f"{path.name}:{n}: bad json: {e}") from e
    return rows


def seen_replay_ids(index_rows: list[dict]) -> set[str]:
    return {row.get("replay_id") for row in index_rows if row.get("replay_id")}


def tier_counts(index_rows: list[dict]) -> dict[str, int]:
    counts = {"study": 0, "validation": 0, "sealed_exam": 0}
    for row in index_rows:
        tier = row.get("tier")
        if tier in counts:
            counts[tier] += 1
    return counts


def assign_tier(
    rating: int,
    index_rows: list[dict],
    for_tier: str = "auto",
    *,
    study_floor: int = STUDY_RATING_FLOOR,
    validation_floor: int = VALIDATION_RATING_FLOOR,
    ratio: int = STUDY_TO_VALIDATION_RATIO,
) -> str | None:
    """Return the tier for a new replay, or None to skip (rating too low).

    Policy:
    - rating < study_floor: skip.
    - for_tier = sealed_exam: explicit tier, used only at final-exam time.
    - for_tier = study or validation: explicit; skip if rating below that tier's floor.
    - for_tier = auto: maintain ratio:1 (study:validation) given counts so far.
      Validation only if rating >= validation_floor.
    """
    if rating < study_floor:
        return None
    if for_tier == "sealed_exam":
        if rating < validation_floor:
            return None
        return "sealed_exam"
    if for_tier == "study":
        return "study"
    if for_tier == "validation":
        if rating < validation_floor:
            return None
        return "validation"
    if for_tier != "auto":
        raise ValueError(f"unknown for_tier: {for_tier!r}")

    counts = tier_counts(index_rows)
    study = counts["study"]
    validation = counts["validation"]
    if rating >= validation_floor and validation * ratio < study:
        return "validation"
    if rating >= validation_floor and study == 0 and validation == 0:
        return "study"
    return "study"


def pick_candidate(candidates: list[dict], seen: set[str], min_rating: int) -> dict | None:
    """Return the highest-rated candidate not in seen with rating>=min_rating.

    Candidates are dicts from the Showdown search API:
      {id, format, players, rating, uploadtime, private, password}
    """
    best: dict | None = None
    for c in candidates:
        rid = c.get("id")
        rating = c.get("rating") or 0
        if not rid or rid in seen:
            continue
        if rating < min_rating:
            continue
        if c.get("private"):
            continue
        if best is None or rating > (best.get("rating") or 0):
            best = c
    return best


def make_index_row(candidate: dict, tier: str) -> dict:
    return {
        "replay_id": candidate["id"],
        "tier": tier,
        "rating": candidate.get("rating") or 0,
        "uploadtime": candidate.get("uploadtime") or 0,
        "fetched_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "players": list(candidate.get("players") or []),
    }


def append_index_row(row: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")


def pick_and_record(
    *,
    fmt: str = "gen2ou",
    min_rating: int = STUDY_RATING_FLOOR,
    for_tier: str = "auto",
    download_dir: Path = DEFAULT_DOWNLOAD_DIR,
    index_path: Path = LIB / "replay_index.jsonl",
    fetch_json: Callable[[str], list[dict]] = _fetch_json,
    fetch_text: Callable[[str], str] = _fetch_text,
) -> dict:
    """End-to-end: search, dedupe, assign tier, download, append index row.

    Returns the appended index row. Raises if no eligible candidate exists.
    """
    index_rows = read_replay_index(index_path)
    seen = seen_replay_ids(index_rows)

    search_url = SEARCH_URL_TEMPLATE.format(fmt=fmt)
    candidates = fetch_json(search_url)
    if not isinstance(candidates, list):
        raise RuntimeError(f"unexpected search response shape: {type(candidates).__name__}")

    candidate = pick_candidate(candidates, seen, min_rating)
    if candidate is None:
        raise RuntimeError(
            f"no eligible replay found (format={fmt}, min_rating={min_rating}, "
            f"seen={len(seen)}, candidates={len(candidates)})"
        )

    tier = assign_tier(candidate.get("rating") or 0, index_rows, for_tier=for_tier)
    if tier is None:
        raise RuntimeError(
            f"candidate {candidate.get('id')!r} did not qualify for any tier "
            f"(rating={candidate.get('rating')}, for_tier={for_tier})"
        )

    download_dir.mkdir(parents=True, exist_ok=True)
    log_path = download_dir / f"{candidate['id']}.log"
    if not log_path.exists():
        log_text = fetch_text(LOG_URL_TEMPLATE.format(replay_id=candidate["id"]))
        log_path.write_text(log_text, encoding="utf-8")

    row = make_index_row(candidate, tier)
    append_index_row(row, index_path)
    return row


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    subparsers = parser.add_subparsers(dest="command", required=True)

    pick = subparsers.add_parser("pick", help="pick one unseen replay + download + record")
    pick.add_argument("--format", default="gen2ou", dest="fmt")
    pick.add_argument("--min-rating", type=int, default=STUDY_RATING_FLOOR)
    pick.add_argument(
        "--for-tier",
        choices=["auto", "study", "validation", "sealed_exam"],
        default="auto",
    )
    pick.add_argument("--download-dir", type=Path, default=DEFAULT_DOWNLOAD_DIR)
    pick.add_argument("--index-path", type=Path, default=LIB / "replay_index.jsonl")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "pick":
        try:
            row = pick_and_record(
                fmt=args.fmt,
                min_rating=args.min_rating,
                for_tier=args.for_tier,
                download_dir=args.download_dir,
                index_path=args.index_path,
            )
        except (urllib.error.URLError, RuntimeError) as e:
            print(f"FAIL: {e}", file=sys.stderr)
            return 1
        print(json.dumps(row, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
