# Cheap Difficulty Audit - 2026-04-26

Lane: cheap-difficulty evidence.

Purpose: catch static roster/item patterns that can make a hard fight feel
cheap before a human playtest notices them.

## New Audit

Added `tools/audit/check_cheap_difficulty.py`.

The script checks:

- early-tier late-item leakage;
- Choice item timing;
- Life Orb / Assault Vest tier timing;
- one-off Light Ball ownership;
- party-size pressure by AI tier;
- Rival starter-branch pressure parity;
- Johto Gym peak-level curve.

This is a static tripwire, not taste proof. It cannot say whether Whitney or
Clair feels good in play; it can say when a future edit violates obvious
fair-hard guardrails.

## Results

All commands were run from `C:\Users\lolno\Downloads\pokemon gold hack`.

| Command | Result |
| --- | --- |
| `python tools\audit\bug_hunt_triage.py --max-leads 10` | PASS: ranked leads none found across known high-yield bug shapes. |
| `python tools\audit\check_cheap_difficulty.py` | PASS: 43 target entries and 206 target mons checked; Johto Gym peak levels `11, 17, 21, 26, 32, 34, 33, 39`; 7 Rival branch sets checked. |
| `python tools\audit\check_ai_tiers.py` | PASS: 35 required boss entries covered; tier counts `EARLY=9`, `MID=9`, `LATE=17`; 17 adaptive lead entries covered. |
| `python tools\audit\check_boss_items_present.py` | PASS: 35 boss entries / 163 mons have items, with only documented early Rival1 no-item allowlist entries. |
| `python tools\audit\check_boss_moves_complete.py` | PASS: 35 boss entries / 163 mons have no `NO_MOVE` tokens. |

## Interpretation

No source defect was found in this pass.

The current static evidence supports:

- early boss rosters are not carrying late-game lock/swing items;
- Rival starter branches are pressure-matched by count, levels, and no-item
  shape;
- the Johto Gym level curve has no automated spike beyond the configured
  guardrail;
- boss item and move completeness still hold.

## Remaining Uncertainty

- This does not replace manual boss playtests.
- It does not judge actual feel, matchup coverage, or grinding pressure.
- It does not prove live Boss AI decision quality beyond existing trace
  evidence.
