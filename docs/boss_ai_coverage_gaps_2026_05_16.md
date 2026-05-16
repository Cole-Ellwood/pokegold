# Boss AI Coverage Gaps — 2026-05-16

Status: surfaced at the end of the 2026-05-16 session's boss-ai-loop work.
The Python scorer + canonical labels reached high alignment on what's
covered (trajectory 47/48 = 97.9%, canonical 5/5 = 100%, pairwise 47/47 =
100%, other_better 4/4 = 100%, label health 48/48 = 100%), but the
**covered surface is a slice**, not the full decision space. This doc
is the actionable to-do for a future session that wants to close the
gaps. Pair it with [boss_ai_loop_runbook.md](boss_ai_loop_runbook.md)
(iteration pattern) and [boss_ai_python_to_rom_mapping.md](boss_ai_python_to_rom_mapping.md)
(when/how to propagate to ROM).

Per-gap: what's missing, where to look, what kind of work it needs.
Each gap is its own boss-ai-loop iter or small batch.

## A. Partially covered

### A1. Rapid Spin — boss-side offensive use

- **Status**: base AI (`engine/battle/ai/scoring.asm:2251`
  `AI_Smart_RapidSpin`) DOES encourage spin when boss is trapped /
  Leech Seeded / has Spikes on its side, scaling with layer depth.
  Boss AI overlay (`engine/battle/ai/boss_policy_move.asm` 6
  EFFECT_RAPID_SPIN refs) handles PLAYER-side spinners (iter 6-9
  work) but not boss-side use.
- **Python mirror**: none for boss-side spin (the existing
  `_active_player_revealed_rapid_spin` reads player only).
- **Fixture gap**: zero fixtures exercise "boss Tentacruel with 2-3
  Spikes on its side facing player active" → can the AI prioritise
  Rapid Spin over direct damage?
- **Work**: 1 fixture (Janine Tentacruel or Brock Forretress with
  boss-side Spikes) + 1 Python scorer rule mirroring `AI_Smart_RapidSpin`'s
  triggers. Audit floor doesn't change.

### A2. Recovery timing

- **Status**: only generic `preserve_value` (+4) applies. No
  recovery-specific rule for "Recover near KO threshold" vs "Recover
  full HP wastes turn."
- **Where to look**: `tools/boss_ai_debugger/scorer.py` — search
  `RECOVERY_NAMES`. Existing logic: +4 preserve, taste_risk if text
  marks recovery as "robotic"/"spam", + `full_hp_rest_fails` for Rest
  specifically.
- **Work**: 2-3 fixtures (e.g. Whitney Milk Drink at high HP vs low
  HP) + recovery_timing rule that reads boss active HP%: discourage
  recovery >= 80% HP; encourage 30-60% HP; penalty when "outdamaging"
  is the public read.

### A3. Lock-in moves / Choice items

- **Status**: ROM-side handled in `engine/battle/ai/late_gen_held_items.asm`
  (Choice Band / Specs / Scarf lock detection + scoring). Python scorer
  has only generic `lock_risk` (-8) on Rollout / Outrage.
- **Where to look**: `late_gen_held_items.asm` for the existing
  ROM logic. `tools/boss_ai_debugger/scorer.py` for the Python side
  (no Choice handling currently).
- **Work**: fixture set where boss is Choice-locked into an awkward
  move (e.g. Choice Band Snorlax locked into Earthquake vs a Flying
  player) + Python mirror rule for "current move is wrong but Choice
  forces it" — discourage switching (it's locked) but encourage
  switching when the locked move is publicly useless.

## B. Uncovered / weak

### B1. Multi-turn pattern memory

- **Status**: NOT implemented. Was the rebuild design doc's
  "Option B" pattern detector (4-8 byte WRAM struct tracking
  player_action × my_active_class). Shelved 2026-05-05.
- **Where to look**: `docs/boss_ai_design_conversation_2026-05-05.md`
  Option B section. `docs/boss_ai_rebuild_plan.md` for prior plan.
- **Work**: substantial. Read the design doc first. Likely a 4-byte
  WRAM ring buffer + a recall rule. Boss AI WRAM trace reserve has
  only 9 bytes free — TIGHT. Plan budget impact before any ASM.

### B2. Per-leader personality weights

- **Status**: implicit via fixture tags (Whitney `setup_lock`,
  Janine `hazards`, etc.). No explicit per-leader scoring biases in
  Python; ROM has role-bias tables (`engine/battle/ai/boss_policy_move.asm`
  `.ApplyRoleBias`).
- **Where to look**: `boss_policy_move.asm` role-bias code. The
  design doc Per-leader-feel-sketch table for taste guidance (Falkner
  newbie aggression vs Lance max risk-aversion).
- **Work**: per-leader scoring weights in Python (multiplier on
  preserve_value, sacrifice_pressure, etc. keyed by leader). Taste
  calls per leader escalate to user.

### B3. Phazing (Roar / Whirlwind)

- **Status**: `denial` rule (+6) fires on phazing text. No dedicated
  rule for "use Roar to clear hazards on player's side that boss
  set up but a setup mon trapped you with."
- **Where to look**: `tools/boss_ai_debugger/scorer.py` `denial`
  rule. ROM-side: search `boss_policy_move.asm` for `EFFECT_ROAR`,
  `EFFECT_WHIRLWIND`.
- **Work**: 2 fixtures (boss setup mon facing setup-stacking player;
  boss with hazards facing dangerous setup) + phazing rule that
  recognises "phazing erases public setup AND triggers player's
  hazard chip."

### B4. Trap moves (Mean Look / Spider Web / Wrap / Fire Spin / Bind)

- **Status**: no scorer rule, no fixture. The user-facing impact:
  Crobat / Ariados / etc. don't get extra credit for Mean Look
  setups, even though that's a clean ace-trap line.
- **Where to look**: `tools/boss_ai_preference/fixtures/`
  for any existing trap-move fixture; expected none.
- **Work**: 1-2 fixtures (Koga Crobat Mean Look on player ace;
  Whitney Clefairy Wrap chip) + trap_setup rule keyed on EFFECT_MEAN_LOOK
  / EFFECT_TRAP move family.

### B5. Status beyond sleep (paralysis / burn / toxic)

- **Status**: only generic `status_identity` (+5). No per-status
  rule for "Toxic clock wins endgame" or "paralysis cripples sweeper."
- **Where to look**: scorer.py `STATUS_NAMES`. The existing
  `sleep_clause_free_window` rule (iter 16) is the template.
- **Work**: toxic_clock_window (+X when player can't recover and
  endgame tag) + paralysis_speed_control (+X on Thunder Wave/Body
  Slam vs sweepers) + burn_phys_atk_chip (+X on Will-O-Wisp vs
  physical-only attackers). 3 small rules + 3 fixtures.

## How to consume this doc

Each section is one boss-ai-loop iter (or small batch when fixtures
+ rule + test land together). The runbook covers the template:
identify → diagnose → fix tier → audit → commit (`boss-ai-loop: iter
N <action>`) → push. The mapping doc covers when/how to propagate
to ROM.

Priority order (highest impact first): **A1, B3, A2, B5, B4, A3,
B2, B1**. B1 (multi-turn pattern memory) is intentionally last —
it's the largest scope and the design lead has shelved it once
already; revisit only after the simpler gaps close.
