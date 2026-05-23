"""Haki coverage tool — the Cole-approved 2026-05-23 gate-rule shape.

Haki eligibility: `wBossAITier != AI_TIER_EARLY` AND `wTrainerClass NOT IN
BossAIHakiExcludedClasses`.

This tool surfaces, for audit + balance review:
  - The eligibility gate as documented in docs/boss_ai_spec.md.
  - The expected included trainer classes (Johto post-Whitney + Silver
    MID/LATE stages + Rocket executives + E4 + Champion + Blue + Red).
  - The expected excluded trainer classes (Kanto gyms minus Blue).
  - A cross-check that data/trainers/ai_tiers.asm BossAITierMap actually
    assigns each included class a tier >= MID and each excluded class is
    still listed (so we know the gate WOULD apply if Haki tried to fire).

P0.5c original v1 was the spec-table parser. This version (post-pivot) is
the gate-rule cross-checker; both shapes co-existed during the transition
but the Uniform Haki Oracle design drops the per-leader table format.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


SPEC_PATH = Path("docs/boss_ai_spec.md")
TIER_MAP_PATH = Path("data/trainers/ai_tiers.asm")

# Trainer classes that should be Haki-eligible under the gate rule.
# RIVAL1/RIVAL2 entries are tier-gated per-stage (some EARLY, some MID/LATE);
# we list the classes themselves and let the audit verify ai_tiers.asm has
# at least one MID-or-LATE row for each.
EXPECTED_INCLUDED_CLASSES = (
    "MORTY", "CHUCK", "JASMINE", "PRYCE", "CLAIR",   # Johto post-Whitney
    "RIVAL1", "RIVAL2",                              # Silver
    "EXECUTIVEM", "EXECUTIVEF",                      # Rocket
    "WILL", "BRUNO", "KOGA", "KAREN",                # Elite Four
    "CHAMPION",                                      # Lance
    "BLUE", "RED",                                   # Kanto carve-out + final
)

EXPECTED_EXCLUDED_CLASSES = (
    "BROCK", "MISTY", "LT_SURGE", "ERIKA", "JANINE", "SABRINA", "BLAINE",
)

TIER_ROW_RE = re.compile(r"^\s*db\s+(\w+)\s*,\s*\w+\s*,\s*AI_TIER_(EARLY|MID|LATE)\s*(?:;|$)")


@dataclass(frozen=True)
class TierMapRow:
    trainer_class: str
    tier: str  # EARLY / MID / LATE


def parse_tier_map(text: str) -> list[TierMapRow]:
    rows: list[TierMapRow] = []
    in_map = False
    for line in text.splitlines():
        if "BossAITierMap" in line and ":" in line:
            in_map = True
            continue
        if "BossAITierRampMap" in line and ":" in line:
            in_map = False
            break
        if not in_map:
            continue
        m = TIER_ROW_RE.match(line)
        if m:
            rows.append(TierMapRow(trainer_class=m.group(1), tier=m.group(2)))
    return rows


def run_haki_coverage() -> dict:
    if not TIER_MAP_PATH.exists():
        return {"ok": False, "error": f"{TIER_MAP_PATH} not found"}
    tier_rows = parse_tier_map(TIER_MAP_PATH.read_text(encoding="utf-8"))
    if not tier_rows:
        return {"ok": False, "error": f"{TIER_MAP_PATH}: BossAITierMap parsed empty"}

    classes_with_mid_or_late = {r.trainer_class for r in tier_rows if r.tier in ("MID", "LATE")}
    classes_with_any_tier = {r.trainer_class for r in tier_rows}

    missing_eligible = [c for c in EXPECTED_INCLUDED_CLASSES if c not in classes_with_mid_or_late]
    missing_excluded = [c for c in EXPECTED_EXCLUDED_CLASSES if c not in classes_with_any_tier]

    # Sanity: excluded classes should NOT be missing from the tier map either
    # (they need to be listed so the gate sees them and rejects them; if they
    # have no tier row they fall through to non-boss handling instead).
    return {
        "ok": not missing_eligible and not missing_excluded,
        "tier_map_path": str(TIER_MAP_PATH),
        "spec_path": str(SPEC_PATH),
        "total_tier_rows": len(tier_rows),
        "expected_included_count": len(EXPECTED_INCLUDED_CLASSES),
        "expected_excluded_count": len(EXPECTED_EXCLUDED_CLASSES),
        "missing_eligible": missing_eligible,
        "missing_excluded": missing_excluded,
        "included_classes_seen_with_mid_or_late": sorted(
            c for c in EXPECTED_INCLUDED_CLASSES if c in classes_with_mid_or_late
        ),
        "excluded_classes_seen": sorted(
            c for c in EXPECTED_EXCLUDED_CLASSES if c in classes_with_any_tier
        ),
    }


def format_haki_coverage(report: dict) -> str:
    lines = [f"Haki gate-rule coverage from {report.get('tier_map_path', TIER_MAP_PATH)}:"]
    if not report.get("ok") and report.get("error"):
        lines.append(f"  FAIL: {report['error']}")
        return "\n".join(lines)
    lines.append(
        f"  expected included: {report['expected_included_count']} classes; "
        f"found with tier >= MID: {len(report['included_classes_seen_with_mid_or_late'])}"
    )
    lines.append(
        f"  expected excluded: {report['expected_excluded_count']} classes; "
        f"found in tier map: {len(report['excluded_classes_seen'])}"
    )
    if report.get("missing_eligible"):
        lines.append(f"  MISSING_ELIGIBLE: {', '.join(report['missing_eligible'])}")
    if report.get("missing_excluded"):
        lines.append(f"  MISSING_EXCLUDED: {', '.join(report['missing_excluded'])}")
    lines.append("")
    lines.append("  Eligible trainer classes (gate=tier-MID-or-LATE-and-not-excluded):")
    for c in report["included_classes_seen_with_mid_or_late"]:
        lines.append(f"    + {c}")
    lines.append("")
    lines.append("  Excluded trainer classes (Kanto gyms sans Blue — gate rejects):")
    for c in report["excluded_classes_seen"]:
        lines.append(f"    - {c}")
    return "\n".join(lines)


def run_self_test() -> int:
    report = run_haki_coverage()
    print(format_haki_coverage(report))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    sys.exit(run_self_test())
