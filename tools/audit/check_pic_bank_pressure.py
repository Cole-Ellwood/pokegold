#!/usr/bin/env python3
"""Pic-bank pressure guard: flag if any pic bank loses free bytes vs baseline.

Pic banks ($12, $15, $17, $1a, $1b, $1c, $1e, $1f) hold Pokemon and trainer
pic data. They sit with 0-4 bytes of slack in the current build; a single
sprite-size change can silently overflow one of them. The link error that
results does name the bank, but by then the work is done and an unrelated
agent's session is on fire.

This audit reads the "Tight Banks And Regions" table from
`docs/generated/dev_index.md` and compares each pic bank's free-byte count
against a baseline recorded in `tools/audit/data/pic_bank_baseline.json`.
FAIL if a pic bank's free-byte count drops below the baseline (a sprite
grew and ate into the cushion). Update the baseline only when the change
is intentional and reviewed.

Relies on `dev_index.md` being current. Per CLAUDE.md, regenerate it after
every successful build:
    python3 scripts/generate_dev_index.py --rom pokegold

The audit is a *cushion* check, not a *fit* check. Bank overflow itself is
caught by the linker; this script catches encroachment before that point.

Usage:
    check_pic_bank_pressure.py            # validate, exit 1 on regression
    check_pic_bank_pressure.py --update   # record current free-byte counts
                                          # as the new baseline (after a
                                          # reviewed sprite-size change)
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEV_INDEX = ROOT / "docs" / "generated" / "dev_index.md"
DATA_FILE = ROOT / "tools" / "audit" / "data" / "pic_bank_baseline.json"

PIC_BANKS = ("12", "15", "17", "1a", "1b", "1c", "1e", "1f")

TIGHT_HEADER_RE = re.compile(r"^###\s+Tight Banks And Regions\s*$")
ROW_RE = re.compile(
    r"^\|\s*(?P<region>[A-Za-z0-9]+)\s*\|\s*(?P<bank>[0-9a-fA-F]+)\s*\|\s*(?P<free>-?\d+)\s*\|"
)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def parse_tight_banks() -> dict[str, int]:
    if not DEV_INDEX.exists():
        fail(
            f"missing {DEV_INDEX.relative_to(ROOT)}. "
            "Regenerate with `python3 scripts/generate_dev_index.py --rom pokegold`."
        )
    in_section = False
    out: dict[str, int] = {}
    for line in DEV_INDEX.read_text(encoding="utf-8").splitlines():
        if TIGHT_HEADER_RE.match(line):
            in_section = True
            continue
        if in_section and line.startswith("### "):
            break
        if not in_section:
            continue
        match = ROW_RE.match(line)
        if not match:
            continue
        if match.group("region") != "ROMX":
            continue
        out[match.group("bank").lower()] = int(match.group("free"))
    if not out:
        fail(
            "could not parse any ROMX rows from the Tight Banks And Regions table. "
            f"Check {DEV_INDEX.relative_to(ROOT)} layout."
        )
    return out


def load_baseline() -> dict[str, int]:
    if not DATA_FILE.exists():
        return {}
    raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {bank.lower(): int(free) for bank, free in raw.items()}


def save_baseline(data: dict[str, int]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(
        json.dumps({bank: data[bank] for bank in sorted(data)}, indent=2) + "\n",
        encoding="utf-8",
    )


def collect_pic_state(tight: dict[str, int]) -> dict[str, int]:
    state: dict[str, int] = {}
    for bank in PIC_BANKS:
        if bank not in tight:
            # Bank dropped out of the tight-banks list; treat as plenty-of-room.
            # Anything not tight has at least the dev_index threshold of free bytes.
            # Record as "not tight" sentinel: -1 means "no longer in scope".
            state[bank] = -1
            continue
        state[bank] = tight[bank]
    return state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--update",
        action="store_true",
        help=(
            "record current pic-bank free-byte counts as the new baseline. "
            "Use only after a reviewed/intentional sprite-size change."
        ),
    )
    args = parser.parse_args(argv)

    tight = parse_tight_banks()
    current = collect_pic_state(tight)

    if args.update:
        save_baseline(current)
        print(
            "Recorded pic-bank baseline: "
            + ", ".join(f"${b}={current[b]}" for b in sorted(current))
        )
        return 0

    baseline = load_baseline()
    if not baseline:
        fail(
            f"no baseline at {DATA_FILE.relative_to(ROOT)}. "
            "Run with --update to record the current free-byte counts."
        )

    regressions: list[str] = []
    for bank in PIC_BANKS:
        if bank not in baseline:
            # New bank under monitoring; record once via --update.
            regressions.append(
                f"  ${bank}: no baseline recorded yet (re-run with --update)"
            )
            continue
        cur = current[bank]
        base = baseline[bank]
        # Sentinel -1 = bank dropped out of tight list (got *more* free space).
        # That's not a regression; it's good news. Skip.
        if cur == -1:
            continue
        if cur < base:
            regressions.append(
                f"  ${bank}: {base} free baseline -> {cur} free now ({cur - base:+d})"
            )

    if regressions:
        print(
            "Pic bank free-byte count dropped below baseline. "
            "A sprite likely grew; review the change before bumping the baseline."
        )
        for line in regressions:
            print(line)
        fail(
            "If the change is intentional, run "
            "`python3 tools/audit/check_pic_bank_pressure.py --update`."
        )

    print(
        "Pic-bank pressure OK: "
        + ", ".join(
            f"${b}={current[b]}" if current[b] != -1 else f"${b}=loose"
            for b in PIC_BANKS
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
