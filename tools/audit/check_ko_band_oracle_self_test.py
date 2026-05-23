#!/usr/bin/env python3
"""Audit P2a — KO-band oracle matchup tables self-test.

Verifies the contract from scripts/generate_boss_matchup_tables.py and the
P2 section of docs/boss_ai_rom_expansion_2026-05-23_codex_task.md:

  (a) `data/boss_ai/matchup_tables.asm` is up to date — regenerate and
      diff against the committed file. If the generator produces different
      output, the committed table is stale and a `python
      scripts/generate_boss_matchup_tables.py` rerun is owed.

  (b) Per-leader coverage: all 16 Haki-eligible trainer classes appear in
      the table. Missing classes would make Codex's KO-band oracle fall
      back to the runtime matchup loop for that leader, defeating P2's
      "no runtime type-chart loops" goal.

  (c) Byte-layout invariants per row: each leader row has a 2-byte
      (class, id) header + 1-byte party count + N slot blocks, where N
      matches party_count. Each slot block is 1 (species) + 17 (defensive
      vector) + 17 (offensive vector) = 35 bytes. Total per leader =
      2 + 1 + 35 * party_count bytes (plus the table sentinel `db 0` at
      end of file).

  (d) Multiplier byte values are in the allowed set {0, 5, 10, 20}
      — no garbage encoding from a generator regression. (The runtime
      asm matchup loop interprets these as ×0/×0.5/×1/×2 — any other
      value would multiply through wrong.)

  (e) Defensive immunity sanity-check: at least one row in the table has
      a 0-multiplier somewhere, and at least one has a 20-multiplier
      somewhere. Catches a "generator emitted all 10s" regression.

This audit is intentionally simple — it doesn't try to re-derive the
type chart math, just verifies the generator's output is consistent
with itself and well-formed. Codex's P2b implementation will add the
oracle math layer; promotion of this audit to release-smoke happens
after P2b lands.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GENERATOR = REPO / "scripts" / "generate_boss_matchup_tables.py"
TABLE = REPO / "data" / "boss_ai" / "matchup_tables.asm"
ORACLE = REPO / "engine" / "battle" / "ai" / "ko_band_oracle.asm"

EXPECTED_CLASSES = (
    "MORTY", "CHUCK", "JASMINE", "PRYCE", "CLAIR",
    "RIVAL1", "RIVAL2",
    "EXECUTIVEM", "EXECUTIVEF",
    "WILL", "BRUNO", "KOGA", "KAREN",
    "CHAMPION",
    "BLUE", "RED",
)
NUM_TYPES = 17
SLOT_DATA_BYTES = 1 + NUM_TYPES + NUM_TYPES  # species + def + off
HEADER_BYTES = 2 + 1  # class + id + party_count
VALID_MULTIPLIERS = {0, 5, 10, 20}


def check_no_drift() -> tuple[bool, str]:
    """(a) Regenerate, diff against committed."""
    if not GENERATOR.exists():
        return False, f"(a) FAIL: generator not found at {GENERATOR}"
    if not TABLE.exists():
        return False, f"(a) FAIL: committed table not found at {TABLE}"
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--dry-run"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False, f"(a) FAIL: generator dry-run exited {result.returncode}: {result.stderr.strip()[:500]}"
    committed = TABLE.read_text(encoding="utf-8")
    if result.stdout != committed:
        # Diff the first few diverging lines for a useful failure message.
        committed_lines = committed.splitlines()
        regen_lines = result.stdout.splitlines()
        first_diff = None
        for i, (c, r) in enumerate(zip(committed_lines, regen_lines)):
            if c != r:
                first_diff = (i + 1, c, r)
                break
        if first_diff is None:
            if len(committed_lines) != len(regen_lines):
                first_diff = (
                    min(len(committed_lines), len(regen_lines)) + 1,
                    f"<file ends at line {len(committed_lines)}>",
                    f"<file ends at line {len(regen_lines)}>",
                )
        msg = (
            f"(a) FAIL: data/boss_ai/matchup_tables.asm is stale. "
            f"Rerun: python {GENERATOR.relative_to(REPO)}"
        )
        if first_diff:
            line_no, c_line, r_line = first_diff
            msg += f"\n      first divergence at line {line_no}:\n      committed: {c_line[:120]}\n      regen:     {r_line[:120]}"
        return False, msg
    return True, "(a) PASS: data/boss_ai/matchup_tables.asm matches generator output."


def parse_table_rows() -> list[dict]:
    """Parse the committed table into per-leader dicts.

    Returns: [{class, id, party_count, slots: [{species, def: [17], off: [17]}]}]
    """
    text = TABLE.read_text(encoding="utf-8")
    rows: list[dict] = []
    in_table = False
    pending_header: tuple[str, str] | None = None
    pending_party: int | None = None
    pending_slots: list[dict] = []
    current_slot_species: str | None = None
    current_def: list[int] | None = None
    # Pattern matchers.
    label_re = re.compile(r"^BossAIMatchupTables::")
    header_db_re = re.compile(r"^\s*db\s+(\w+)\s*,\s*(\w+)\s*$")
    party_count_re = re.compile(r"^\s*db\s+(\d+)\s*$")
    species_re = re.compile(r"^\s*db\s+(\w+)\s*$")
    vec_re = re.compile(r"^\s*db\s+([\d,\s]+)\s*;\s*(defensive|offensive)\s+vector\s*$")
    sentinel_re = re.compile(r"^\s*db\s+0\s*;\s*end-of-table\s+sentinel\s*$")
    for raw in text.splitlines():
        line = raw.split(";")[0].rstrip() if ("; defensive" not in raw and "; offensive" not in raw) else raw
        if label_re.search(raw):
            in_table = True
            continue
        if not in_table:
            continue
        if sentinel_re.match(raw):
            # flush trailing leader
            if pending_header and pending_party is not None and pending_slots:
                rows.append({
                    "class": pending_header[0],
                    "id": pending_header[1],
                    "party_count": pending_party,
                    "slots": pending_slots,
                })
            break
        v = vec_re.match(raw)
        if v:
            mults = [int(x.strip()) for x in v.group(1).strip().rstrip(",").split(",") if x.strip()]
            if v.group(2) == "defensive":
                current_def = mults
            else:
                if current_slot_species and current_def is not None:
                    pending_slots.append({
                        "species": current_slot_species,
                        "def": current_def,
                        "off": mults,
                    })
                current_slot_species = None
                current_def = None
            continue
        h = header_db_re.match(line)
        if h:
            # Either a leader header (class, id) or a single-token line we'll filter.
            tok_a, tok_b = h.group(1), h.group(2)
            # Heuristic: leader headers have class names from EXPECTED_CLASSES.
            if tok_a in EXPECTED_CLASSES:
                # New leader begins — flush previous if pending
                if pending_header and pending_party is not None and pending_slots:
                    rows.append({
                        "class": pending_header[0],
                        "id": pending_header[1],
                        "party_count": pending_party,
                        "slots": pending_slots,
                    })
                pending_header = (tok_a, tok_b)
                pending_party = None
                pending_slots = []
                current_slot_species = None
                current_def = None
                continue
        pc = party_count_re.match(line)
        if pc and pending_header is not None and pending_party is None:
            pending_party = int(pc.group(1))
            continue
        sp = species_re.match(line)
        if sp and pending_header is not None and pending_party is not None and current_slot_species is None:
            current_slot_species = sp.group(1)
            continue
    return rows


def check_class_coverage(rows: list[dict]) -> tuple[bool, str]:
    """(b) All 16 Haki-eligible classes appear at least once."""
    classes_present = {r["class"] for r in rows}
    missing = [c for c in EXPECTED_CLASSES if c not in classes_present]
    if missing:
        return False, f"(b) FAIL: matchup_tables.asm missing classes {missing}"
    return True, f"(b) PASS: all 16 Haki-eligible classes present ({len(rows)} total leader rows)."


def check_byte_layout(rows: list[dict]) -> tuple[bool, str]:
    """(c) Each row has party_count matching len(slots), each slot has 17+17 mults."""
    errors: list[str] = []
    for r in rows:
        if r["party_count"] != len(r["slots"]):
            errors.append(
                f"{r['class']}:{r['id']} party_count={r['party_count']} but {len(r['slots'])} slot blocks"
            )
        for i, s in enumerate(r["slots"]):
            if len(s["def"]) != NUM_TYPES:
                errors.append(f"{r['class']}:{r['id']} slot {i} ({s['species']}) defensive vector has {len(s['def'])} bytes, expected {NUM_TYPES}")
            if len(s["off"]) != NUM_TYPES:
                errors.append(f"{r['class']}:{r['id']} slot {i} ({s['species']}) offensive vector has {len(s['off'])} bytes, expected {NUM_TYPES}")
    if errors:
        return False, "(c) FAIL byte layout:\n      " + "\n      ".join(errors[:10])
    total_slots = sum(r["party_count"] for r in rows)
    return True, f"(c) PASS: byte layout consistent across {len(rows)} leaders / {total_slots} slots."


def check_multiplier_values(rows: list[dict]) -> tuple[bool, str]:
    """(d) All multiplier bytes are in {0, 5, 10, 20}."""
    bad: list[str] = []
    for r in rows:
        for i, s in enumerate(r["slots"]):
            for j, m in enumerate(s["def"]):
                if m not in VALID_MULTIPLIERS:
                    bad.append(f"{r['class']}:{r['id']} slot {i} ({s['species']}) def[{j}]={m}")
            for j, m in enumerate(s["off"]):
                if m not in VALID_MULTIPLIERS:
                    bad.append(f"{r['class']}:{r['id']} slot {i} ({s['species']}) off[{j}]={m}")
    if bad:
        return False, "(d) FAIL: multiplier bytes outside {0, 5, 10, 20}:\n      " + "\n      ".join(bad[:10])
    return True, "(d) PASS: all multiplier bytes in {0, 5, 10, 20}."


def _load_trainer_constants() -> set[str]:
    """Parse constants/trainer_constants.asm and return the full set of
    declared trainer-id constants (every `const <NAME>` line under a
    trainerclass block).
    """
    path = REPO / "constants" / "trainer_constants.asm"
    if not path.exists():
        return set()
    ids: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*const\s+(\w+)\s*$", raw)
        if m:
            ids.add(m.group(1))
    return ids


CHAMPION_SINGLETON_ID = "LANCE"  # CHAMPION has no `const` line; ai_tiers.asm uses LANCE.


def check_trainer_id_validity(rows: list[dict]) -> tuple[bool, str]:
    """(f) Every emitted (class, id) pair has a matching constant.

    Codex's 2026-05-23 slice_revisions_requested catch: the generator
    can synthesize bogus IDs (EXECUTIVEM4 vs EXECUTIVEM_4, off-by-one
    rival stage numbering) that would fail assembly when Codex's P2b
    INCLUDEs this file. Cross-check each ID against the
    trainer_constants.asm declared set (plus the CHAMPION:LANCE
    singleton special case).
    """
    declared = _load_trainer_constants()
    declared.add(CHAMPION_SINGLETON_ID)
    if not declared:
        return False, "(f) FAIL: couldn't parse constants/trainer_constants.asm"
    bad = [(r["class"], r["id"]) for r in rows if r["id"] not in declared]
    if bad:
        sample = ", ".join(f"{cls}:{tid}" for cls, tid in bad[:6])
        more = f" (+ {len(bad) - 6} more)" if len(bad) > 6 else ""
        return False, (
            f"(f) FAIL: emitted trainer IDs not declared in "
            f"constants/trainer_constants.asm: {sample}{more}. "
            f"The generator's ID-synthesis rule is out of sync with the constants."
        )
    return True, f"(f) PASS: all {len(rows)} emitted (class, id) pairs match declared constants."


def check_immunity_and_super_present(rows: list[dict]) -> tuple[bool, str]:
    """(e) Sanity: table has at least one 0 (immunity) and one 20 (super)."""
    has_zero = False
    has_super = False
    for r in rows:
        for s in r["slots"]:
            if any(m == 0 for m in s["def"]) or any(m == 0 for m in s["off"]):
                has_zero = True
            if any(m == 20 for m in s["def"]) or any(m == 20 for m in s["off"]):
                has_super = True
            if has_zero and has_super:
                break
        if has_zero and has_super:
            break
    if not has_zero:
        return False, "(e) FAIL: no immunity (mult=0) anywhere in matchup_tables.asm — generator regression?"
    if not has_super:
        return False, "(e) FAIL: no super-effective (mult=20) anywhere in matchup_tables.asm — generator regression?"
    return True, "(e) PASS: both immunities and super-effective entries present (sanity)."


def check_runtime_tier_gate() -> tuple[bool, str]:
    """(g) EARLY tier must not consume the P2 structural oracle."""
    text = ORACLE.read_text(encoding="utf-8", errors="replace")
    match = re.search(
        r"BossAI_ApplyKOBandOraclePressure::(?P<body>.*?); ai-layer: POLICY\s+BossAI_CurrentSlotOffensiveCoverageVsPlayer:",
        text,
        flags=re.S,
    )
    if not match:
        return False, "(g) FAIL: couldn't locate BossAI_ApplyKOBandOraclePressure body"
    body = match.group("body")
    required = [
        "ld a, [wBossAITier]",
        "cp AI_TIER_MID",
        "ret c",
        "ld a, [wTypeMatchup]",
    ]
    pos = -1
    for needle in required:
        nxt = body.find(needle, pos + 1)
        if nxt < 0:
            return False, f"(g) FAIL: KO-band oracle missing tier-gate sequence `{needle}`"
        pos = nxt
    return True, "(g) PASS: runtime KO-band oracle is gated off for EARLY tier."


def main() -> int:
    ok_drift, msg_drift = check_no_drift()
    print(msg_drift)
    if not ok_drift:
        # Drift catastrophically blocks remaining checks (parser would
        # read potentially garbled committed file). Bail.
        return 1
    rows = parse_table_rows()
    if not rows:
        print("FAIL: parser couldn't extract any rows — table format may have regressed.")
        return 1
    checks = [
        check_class_coverage(rows),
        check_byte_layout(rows),
        check_multiplier_values(rows),
        check_trainer_id_validity(rows),
        check_immunity_and_super_present(rows),
        check_runtime_tier_gate(),
    ]
    all_ok = ok_drift and all(ok for ok, _ in checks)
    for _, m in checks:
        print(m)
    print()
    if all_ok:
        print("PASS: KO-band oracle matchup tables self-test green (drift + coverage + layout + values + sanity).")
        return 0
    print("FAIL: KO-band oracle matchup tables self-test had failures above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
