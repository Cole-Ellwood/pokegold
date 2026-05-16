#!/usr/bin/env python3
"""Public-state fingerprint extractor for the Compounding Loop.

Builds the fingerprint dict defined in case_library/schema.json from a
parsed replay_turn_pause.ReplayState, from the perspective of the side
being advised. Fingerprints are the retrieval key: at fresh prediction
time, the predictor queries the case library for past cases whose
fingerprints overlap with the current position.

The fingerprint hash defined here is the single source of truth used
by verify_case_breadth.py to count distinct strategic situations.

CLI usage is mainly for spot-checking:
  python tools/pokemon_mastery/fingerprint.py <log_path> --turn N --side p1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from tools.pokemon_mastery import replay_turn_pause as rtp

UNKNOWN_HP = "unknown"
HP_BUCKETS = ("0", "<=25%", "26-50%", "51-75%", "76-99%", "100%", UNKNOWN_HP)


def hp_bucket(hp_str: str | None) -> str:
    """Map a Showdown HP string to a fixed bucket.

    Accepts: "?", "84/100", "0 fnt", "84%", "0", "" — and "unknown" passthrough.
    """
    if hp_str is None or hp_str in ("", "?"):
        return UNKNOWN_HP
    s = hp_str.strip().lower()
    if s == UNKNOWN_HP:
        return UNKNOWN_HP
    if s.startswith("0 fnt") or s == "fnt" or s == "0":
        return "0"
    if "/" in s:
        cur, _, mx = s.partition("/")
        try:
            cur_i = int(cur)
            mx_i = int(mx.split()[0])
        except ValueError:
            return UNKNOWN_HP
        if mx_i <= 0:
            return UNKNOWN_HP
        pct = 100.0 * cur_i / mx_i
    elif s.endswith("%"):
        try:
            pct = float(s.rstrip("%"))
        except ValueError:
            return UNKNOWN_HP
    else:
        return UNKNOWN_HP
    if pct <= 0:
        return "0"
    if pct <= 25:
        return "<=25%"
    if pct <= 50:
        return "26-50%"
    if pct <= 75:
        return "51-75%"
    if pct < 100:
        return "76-99%"
    return "100%"


def turn_bucket(turn: int) -> str:
    if turn <= 1:
        return "t1"
    if turn <= 6:
        return "early"
    if turn <= 15:
        return "mid"
    if turn <= 25:
        return "late"
    return "endgame"


def mon_snapshot(side: rtp.SideState, mon_key: str) -> dict[str, Any]:
    mon = side.seen.get(mon_key, rtp.MonState())
    species = mon.species or mon_key
    snap: dict[str, Any] = {
        "species": species,
        "hp_bucket": hp_bucket(mon.hp),
    }
    if mon.status:
        snap["status"] = mon.status
    if mon.boosts:
        snap["boosts"] = {k: v for k, v in mon.boosts.items() if v}
    if mon.moves:
        snap["revealed_moves"] = sorted(mon.moves)
    return snap


def seen_summary(side: rtp.SideState, exclude_active: bool) -> list[dict[str, Any]]:
    out = []
    for mon_key in sorted(side.seen.keys()):
        if exclude_active and mon_key == side.active:
            continue
        snap = mon_snapshot(side, mon_key)
        out.append({"species": snap["species"], "hp_bucket": snap["hp_bucket"]})
    return out


def derive_features(
    active_user: dict[str, Any],
    active_opp: dict[str, Any],
    user_sides: list[str],
    opp_sides: list[str],
) -> list[str]:
    feats: list[str] = []
    if active_user.get("status") and active_user["status"] not in ("", "fnt"):
        feats.append("user_active_statused")
    if active_opp.get("status") and active_opp["status"] not in ("", "fnt"):
        feats.append("opp_active_statused")
    if active_user.get("boosts") and any(v > 0 for v in active_user["boosts"].values()):
        feats.append("user_active_positively_boosted")
    if active_opp.get("boosts") and any(v > 0 for v in active_opp["boosts"].values()):
        feats.append("opp_active_positively_boosted")
    if active_user.get("hp_bucket") in {"0", "<=25%"}:
        feats.append("user_active_low_hp")
    if active_opp.get("hp_bucket") in {"0", "<=25%"}:
        feats.append("opp_active_low_hp")
    if "Spikes" in user_sides:
        feats.append("opp_has_spikes_on_user")
    if "Spikes" in opp_sides:
        feats.append("user_has_spikes_on_opp")
    if "Reflect" in user_sides:
        feats.append("user_has_reflect")
    if "Reflect" in opp_sides:
        feats.append("opp_has_reflect")
    if "Light Screen" in user_sides:
        feats.append("user_has_lightscreen")
    if "Light Screen" in opp_sides:
        feats.append("opp_has_lightscreen")
    return feats


def fingerprint_from_state(state: rtp.ReplayState, turn: int, side: str) -> dict[str, Any]:
    """Build a fingerprint dict matching case_library/schema.json#fingerprint.

    side is 'p1' or 'p2'; active_user is sides[side], active_opp is the other side.
    """
    if side not in ("p1", "p2"):
        raise ValueError(f"side must be p1 or p2, got {side!r}")
    other = "p2" if side == "p1" else "p1"
    user_side = state.sides[side]
    opp_side = state.sides[other]

    active_user = mon_snapshot(user_side, user_side.active)
    active_opp = mon_snapshot(opp_side, opp_side.active)

    user_conds = sorted(user_side.side_conditions)
    opp_conds = sorted(opp_side.side_conditions)

    fp: dict[str, Any] = {
        "active_user": active_user,
        "active_opp": active_opp,
        "seen_user": seen_summary(user_side, exclude_active=True),
        "seen_opp": seen_summary(opp_side, exclude_active=True),
        "side_conditions_user": user_conds,
        "side_conditions_opp": opp_conds,
        "turn_bucket": turn_bucket(turn),
        "speed_order_known": False,
        "decision_relevant_features": derive_features(
            active_user, active_opp, user_conds, opp_conds
        ),
    }
    return fp


def fingerprint_from_log(log_path: Path, turn: int, side: str) -> dict[str, Any]:
    lines = rtp.read_lines(log_path)
    state = rtp.state_before_turn(lines, turn)
    return fingerprint_from_state(state, turn, side)


def fingerprint_hash(fp: dict[str, Any]) -> str:
    """Stable hash over the breadth-counted fields.

    Must match verify_case_breadth.py's hash: tuple of
    (active_user.species, active_opp.species, turn_bucket,
     sorted(side_conditions_user), sorted(side_conditions_opp)).
    """
    parts = (
        (fp.get("active_user") or {}).get("species", ""),
        (fp.get("active_opp") or {}).get("species", ""),
        fp.get("turn_bucket", ""),
        ",".join(sorted(fp.get("side_conditions_user") or [])),
        ",".join(sorted(fp.get("side_conditions_opp") or [])),
    )
    blob = "|".join(parts)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("log", type=Path)
    parser.add_argument("--turn", type=int, required=True)
    parser.add_argument("--side", choices=("p1", "p2"), required=True)
    parser.add_argument("--hash-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        fp = fingerprint_from_log(args.log, args.turn, args.side)
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1
    if args.hash_only:
        print(fingerprint_hash(fp))
    else:
        print(json.dumps({"fingerprint": fp, "hash": fingerprint_hash(fp)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
