# Boss AI Bug Testing Implementation Plan

Purpose: turn the post-patch Boss AI validation plan into repeatable bug tests.
This is an implementation guide for future Codex/helper sessions. It does not
authorize new Boss AI features.

Status legend:

- `FINISHED`: implemented and verified in this workspace.
- `IN PROGRESS`: started, but not fully implemented or verified.
- `UNTOUCHED`: intentionally not started yet.

Current implementation status:

| Work item | Status | Evidence / next step |
| --- | --- | --- |
| Focused static invariant audit | `FINISHED` | `python tools\audit\check_boss_ai_trace_invariants.py` passes. |
| Linker and WRAM memory budget audit | `FINISHED` | `python tools\audit\check_boss_ai_memory_budget.py` passes. |
| Trace capture helper | `FINISHED` | `python tools\trace\boss_ai_trace_capture.py --symbols-only` and boot-state WRAM smoke pass. |
| Trace capture polling/watch mode | `FINISHED` | `python tools\trace\boss_ai_trace_capture.py --watch-frames 2 --include-zero-snapshots` passes. |
| Scenario docs and expected excerpts | `FINISHED` | Existing excerpts live under `audit/boss_ai_trace/`. |
| Full final audit sweep after adding new tests | `FINISHED` | Review Checklist commands passed after adding the new audits. |
| Live capture ledger | `FINISHED` | `audit/boss_ai_trace/live_capture_ledger.md` tracks boss-position capture status. |
| Live capture ledger audit | `FINISHED` | `python tools\audit\check_boss_ai_live_capture_ledger.py` passes. |
| Live capture manifest | `FINISHED` | `audit/boss_ai_trace/live_capture_manifest.json` defines boss capture commands. |
| Live capture batch runner | `FINISHED` | `python tools\trace\boss_ai_trace_batch.py` dry-run reports missing save-states. |
| Boss-position live emulator/debugger captures | `UNTOUCHED` | Requires save-states or manual debugger positions at boss AI decision points. |

Preserve these constraints while implementing tests:

- No hidden foresight implementation.
- No save-wide chaos or overprediction score.
- No probability simulator.
- No Battle Core bank `0f` hooks.
- No exact private `AIDamageCalc` or `AICompareSpeed` boss decision knowledge.
- No persistent state in the temporary boss AI block.

## Scope

Priority bosses:

- Morty
- Jasmine
- Clair
- Koga
- Champion Lance

Required behaviors:

- Revealed coverage does not transfer across player species.
- A->B->A switch-loop penalty applies unless a public emergency exception
  applies.
- First-turn Spikes gets lead bias only when not under immediate public pressure.
- Status moves are discouraged into visible fail states.
- Lance avoids non-KO Hyper Beam.
- Spikes plus Roar/Whirlwind responds to repeated switching or public setup.
- Public +2 setup is punished by denial moves when no immediate KO exists.
- Immunity pivots beat neutral pivots when the public threat type supports it.

## Deliverables

Implement testing in this order:

1. `FINISHED`: Add a focused static invariant audit:
   `tools/audit/check_boss_ai_trace_invariants.py`
2. `FINISHED`: Add linker/memory assertions to that audit or a companion audit:
   `tools/audit/check_boss_ai_memory_budget.py`
3. `FINISHED`: Add a trace capture helper:
   `tools/trace/boss_ai_trace_capture.py`
4. `FINISHED`: Add scenario documentation and expected results under
   `audit/boss_ai_trace/`
5. `FINISHED`: Run existing release audits and update helper docs if paths or commands
   change.
6. `FINISHED`: Add a live-capture ledger audit:
   `tools/audit/check_boss_ai_live_capture_ledger.py`
7. `FINISHED`: Add a live-capture manifest and batch runner:
   `audit/boss_ai_trace/live_capture_manifest.json`,
   `tools/trace/boss_ai_trace_batch.py`

Prefer static audits first. They are cheaper, deterministic, and catch the class
of regressions this patch is most likely to suffer: wrong carry sense, stale
state, threshold drift, and accidental hidden-information reads.

## Static Invariant Audit

Status: `FINISHED`.

Implemented as `tools/audit/check_boss_ai_trace_invariants.py`.

Inputs:

- `engine/battle/ai/boss.asm`
- `ram/wram.asm`
- `data/trainers/parties.asm`
- `data/trainers/ai_tiers.asm`
- `constants/battle_constants.asm`

Assertions to implement:

- `BossAI_RecordRevealedPlayerMove` calls
  `BossAI_GetActiveSpeciesRevealedMaskPointer` before setting revealed move
  bits.
- `BossAI_HasRevealedSuperEffectiveMove` calls
  `BossAI_GetActiveSpeciesRevealedMaskPointer` before testing revealed move
  bits.
- `BossAI_AddRevealedDamagingTypesToMask` copies only the active species mask
  into `wBossAIPlausibleTypeMaskCache`.
- `wBossAIRevealedMovesBitmap` remains a six-species mask area, not a global
  move table.
- `BossAI_NeedsLoopPenalty` checks the proposed target in
  `wEnemySwitchMonParam` before or alongside the current-mon loop check.
- `BossAI_NeedsLoopPenalty` still has exception calls for imminent KO
  prevention, immunity pivot opportunity, and ace timing.
- `.spikes_layer1` compares `wBossAITurnsElapsed` with `2`, not `0` or `1`.
- `.spikes_layer1` checks `.EnemyUnderPressure` before taking the high lead
  bias.
- `.StatusMoveWouldFailPublicly` covers `EFFECT_SLEEP`, `EFFECT_PARALYZE`,
  `EFFECT_CONFUSE`, `EFFECT_POISON`, `EFFECT_TOXIC`, and
  `EFFECT_LEECH_SEED`.
- Paralysis status fail checks use real type-chart immunity, such as Thunder
  Wave into Ground or Glare into Ghost, instead of treating Electric targets as
  paralysis-immune.
- Substitute on the player is treated as a public fail state for primary
  status and Leech Seed, and an already-seeded player is treated as a Leech Seed
  fail state.
- Confusion status moves treat Safeguard, Substitute, and already-confused as
  public fail states.
- `.UtilityMoveWouldFailPublicly` heavily discourages already-active Reflect or
  Light Screen, Substitute while already behind a Substitute or too low on HP,
  Protect while already behind a Substitute, and healing moves while already at
  full HP.
- The status fail path discourages before generic status encouragement can
  dominate.
- `.ApplySetupPunishBias` checks public `BASE_STAT_LEVEL + 2` for Attack,
  Special Attack, Speed, and Evasion.
- `.ApplySetupPunishBias` rewards `EFFECT_FORCE_SWITCH`, `EFFECT_RESET_STATS`,
  and `EFFECT_ENCORE` only when no KO line exists.
- `.ApplyPhazingPlanBias` requires Spikes on the player side and then public
  setup or repeated-switch pressure.
- `BossAI_CurrentEnemyMovePressureScore` discounts non-super-effective pressure
  into visible Dragon defenders to mirror Imperial Scales.
- The Champion role branch discourages `EFFECT_HYPER_BEAM` after `.HasKOLine`
  fails.
- `.ApplyPrimaryThreatImmunityTieBreak` exists and the non-immune adjustment is
  greater than the replacement margin in
  `BossAI_RefineSwitchCandidateForPlausibleRisk`.
- Boss AI code does not add or call Battle Core bank `0f` hooks.

Implementation pattern:

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOSS = ROOT / "engine/battle/ai/boss.asm"

def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)

def block(text: str, label: str, next_labels: tuple[str, ...]) -> str:
    start = text.find(label)
    if start < 0:
        fail(f"missing {label}")
    ends = [text.find(next_label, start + len(label)) for next_label in next_labels]
    ends = [end for end in ends if end >= 0]
    return text[start:min(ends)] if ends else text[start:]
```

Keep checks semantic enough to survive comments and small label movement, but
strict enough to catch meaningful behavior drift. Do not parse full RGBDS unless
the text checks become too fragile.

Expected command:

```powershell
python tools\audit\check_boss_ai_trace_invariants.py
```

Expected output:

```text
Boss AI trace invariant audit passed.
```

## Memory Budget Audit

Status: `FINISHED`.

Implemented as `tools/audit/check_boss_ai_memory_budget.py`.

Inputs:

- `pokegold.map`
- `pokegold.sym`
- `pokegold_trace.map`
- `pokegold_trace.sym`
- `docs/generated/dev_index.md`

Assertions:

- Normal `Enemy Trainers` section ends below `$8000`.
- Trace `Enemy Trainers` section ends below `$8000`.
- `Battle Core` remains `$4000-$7fff` with no new Boss AI labels introduced
  there.
- Normal `wBossAIStateEnd` is before `wEventFlags`.
- Trace `wBossAIStateEnd` is before `wEventFlags`.
- Normal Boss AI state uses no more than the documented reserve:
  `wEventFlags - wBossAITier <= 140`.
- Trace Boss AI state also fits inside the same reserved block.
- `docs/generated/dev_index.md` agrees with current linker outputs. If it does
  not, regenerate it with:

```powershell
python scripts\generate_dev_index.py --rom pokegold --out docs\generated\dev_index.md
```

Expected command:

```powershell
python tools\audit\check_boss_ai_memory_budget.py
```

Expected output:

```text
Boss AI memory budget audit passed.
```

## Trace Capture Helper

Status: `FINISHED`.

Implemented as `tools/trace/boss_ai_trace_capture.py`.

Goal: read trace WRAM fields from `pokegold_trace.gbc` during manual or
scripted boss decisions. The helper should not implement battle logic. It should
only load symbols and format WRAM values.

Required symbol reads:

- `wBossAITraceTopMoves`
- `wBossAITraceTopScores`
- `wBossAITraceChosenMove`
- `wBossAITraceSwitchConfidence`
- `wBossAITracePlanId`
- `wBossAITracePlanPhase`
- `wBossAITracePlanConfidence`
- `wBossAITracePlausibleMask`
- `wBossAITraceRiskFlags`
- `wBossAITraceLookaheadBonusTop`
- `wBossAIRevealedMovesBitmap`

Recommended interface:

```powershell
python tools\trace\boss_ai_trace_capture.py `
  --rom pokegold_trace.gbc `
  --symbols pokegold_trace.sym `
  --save-state path\to\before_lance.state `
  --out audit\boss_ai_trace\champion_lance_live.txt
```

If PyBoy or another emulator backend is used, keep it isolated to this helper.
Do not add runtime code to the ROM to support the helper unless the user
explicitly approves a test-only build path.

Output format:

```text
boss=Champion Lance
turn=3
enemy=Gyarados
player=Raichu
top_moves=OUTRAGE:72,SURF:61,HYPER_BEAM:35
chosen=OUTRAGE
switch_confidence=18
plan=...
plausible_mask=...
risk_flags=...
notes=Hyper Beam was non-KO and was discouraged.
```

If full automation is not available, support a `--symbols-only` mode that prints
addresses for emulator debugger entry.

Verification commands:

```powershell
python tools\trace\boss_ai_trace_capture.py --symbols-only
python tools\trace\boss_ai_trace_capture.py --boss smoke --notes "boot-state reader smoke"
python tools\trace\boss_ai_trace_capture.py --watch-frames 2 --include-zero-snapshots
```

Smoke artifact:

- `audit/boss_ai_trace/trace_helper_smoke.txt`
- `audit/boss_ai_trace/trace_watch_smoke.txt`

## Manual Playtest Matrix

Status: `UNTOUCHED` for boss-position live emulator/debugger captures.
Capture tooling and the live-capture ledger are `FINISHED`.

Use `pokegold_trace.gbc` for all scenarios. Save excerpts under
`audit/boss_ai_trace/`.

Track live capture status in:

- `audit/boss_ai_trace/live_capture_ledger.md`
- `audit/boss_ai_trace/live_capture_manifest.json`

Dry-run all configured live captures:

```powershell
python tools\trace\boss_ai_trace_batch.py
```

Run captures with available save-states:

```powershell
python tools\trace\boss_ai_trace_batch.py --execute
```

Morty:

- Reveal Ice Punch or equivalent coverage on one player species, then switch to
  another species. Confirm Morty does not treat the second species as having the
  first species' revealed coverage.
- Present an already-statused target or Safeguard against Hypnosis/Toxic.
  Confirm status moves are discouraged.
- Reach +2 public setup against final Haunter. Confirm Haze receives denial
  priority when no KO line exists.

Jasmine:

- Lead against Magneton without immediate public pressure. Confirm first-turn
  Spikes receives high lead bias.
- Repeat under immediate public pressure. Confirm Spikes drops to baseline.
- Use Substitute, Ground, Ghost/Foresight, Poison, Steel, already-statused,
  already-confused, already-seeded, and Safeguard states against Thunder
  Wave/Glare/Toxic/Confuse Ray/Leech Seed.
- Set enemy Reflect, Light Screen, Substitute, low HP, and Substitute+Protect
  states, plus full HP with a healing move. Confirm the corresponding utility
  moves are heavily discouraged.
- Set Spikes, then repeatedly switch or set up to +2. Confirm Steelix Roar is
  encouraged.

Clair:

- Test Gligar first-turn Spikes with and without public pressure.
- Set player +2 Attack, Special Attack, Speed, or Evasion. Confirm Donphan or
  Steelix Roar is encouraged when no KO line exists.
- Test Dragonair Thunder Wave into Ground, Ampharos, already-statused, and
  Safeguard states.

Koga:

- Test Ariados first-turn Spikes with and without public pressure.
- Test Toxic into Poison, Steel, already-statused, and Safeguard states.
- Set public +2 setup. Confirm Tentacruel Haze is encouraged when no KO line
  exists.

Champion Lance:

- Bait Gyarados Hyper Beam while the player is outside KO range. Confirm Hyper
  Beam is discouraged and not selected over reasonable non-recharge lines.
- Establish Spikes, then repeatedly switch or set up to +2. Confirm Steelix Roar
  is encouraged.
- Present a public Electric threat with an immune Ground candidate and a merely
  neutral candidate available. Confirm the immunity pivot wins the refinement.

Shared switch-loop scenario:

- Force boss switch A->B, then create conditions where the boss considers
  switching back B->A.
- Confirm `BossAI_NeedsLoopPenalty` applies unless a public emergency exception
  is active.
- Repeat with an imminent KO or public immunity pivot opportunity and confirm
  the exception can waive the penalty.

## Review Checklist

Status: `FINISHED` for the static/release audit sweep. Live emulator/debugger
captures remain `UNTOUCHED`.

Before accepting the tests:

- Rebuild normal and trace ROMs.
- Regenerate `docs/generated/dev_index.md` after linker output changes.
- Run:

```powershell
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_ai_tiers.py
python tools\audit\check_boss_items_present.py
python tools\audit\check_boss_moves_complete.py
python tools\audit\check_battle_math_safety.py
python tools\audit\check_release_smoke.py
python tools\audit\check_docs_navigation.py
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_boss_ai_live_capture_ledger.py
python tools\trace\boss_ai_trace_capture.py --symbols-only
python tools\trace\boss_ai_trace_capture.py --watch-frames 2 --include-zero-snapshots
python tools\trace\boss_ai_trace_batch.py
git diff --check
```

Acceptance criteria:

- All audits pass.
- Normal and trace ROMs link without overflow.
- `wBossAIStateEnd` remains before `wEventFlags`.
- Trace excerpts exist for Morty, Jasmine, Clair, Koga, and Lance.
- Any failed scenario is recorded with the exact boss, turn, public state, trace
  fields, and candidate fix.

## Bug Triage Rules

Fix only concrete bugs found by these tests.

Preferred fixes:

- Tiny score or threshold changes in `engine/battle/ai/boss.asm`.
- Documentation updates when source is correct and docs are stale.
- Audit-script updates when the invariant is right but the check is too brittle.

Avoid:

- New predictive systems.
- New save or temp persistent state.
- Private exact damage/speed knowledge in Boss AI decisions.
- Battle Core bank `0f` hooks.
- Rewriting the release-safety patch without a concrete failing case.
