# Boss AI Bug Testing Implementation Plan

## Boss AI Cognition Mode

Use wild hypotheses to design sharp tests. If a boss line seems terrifying, ask
what trace, invariant, or save-state would prove it is legal instead of lucky or
clairvoyant. The tests are the fence around the crazy thinking, not a reason to
stop thinking crazy.

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
| Live capture batch runner | `FINISHED` | `python tools\trace\boss_ai_trace_batch.py` dry-run reports missing save-states and uses manifest preflights before capture. |
| Boss-position live emulator/debugger captures | `FINISHED` for current manifest floor | All 16 gym leaders plus Koga and Champion Lance have current trace-ROM first-decision chosen-move proof under `audit/boss_ai_trace/*_live.txt`; `shared_switch_loop` has a dedicated switch-confidence fixture at `audit/boss_ai_trace/shared_switch_loop_live.txt`. |

Preserve these constraints while implementing tests:

- No broad hidden foresight implementation outside Haki. The only allowed
  exception is a future once-per-battle Haki branch that follows
  `docs/boss_ai_spec.md`: deliberately unfair hidden/current-turn reading,
  traced, spent once, and quarantined from normal Boss AI memory.
- Haki must be invisible to the player. Developer trace may prove it fired, but
  battle text, animations, icons, field markers, and special visible states may
  not reveal it.
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
- Public Perish Song escape can override KO-stay and switch-loop reluctance only
  from the boss's own perish substatus/count.
- First-turn Spikes gets lead bias only when not under immediate public pressure.
- Status moves are discouraged into visible fail states.
- Full-Dark active players with an unconsumed Dark shield make shield-eligible
  status and utility effects visible fail states; consumed shields and half-Dark
  odds are not hard-failed.
- Non-KO contact moves into visible Poison defenders are soft-discouraged when
  Poison retaliation can actually status the enemy.
- Lance avoids non-KO Hyper Beam.
- Spikes plus Roar/Whirlwind responds to repeated switching or public setup.
- Public +2 setup is punished by denial moves when no immediate KO exists.
- Immunity pivots beat neutral pivots when the public threat type supports it.
- Exact revealed player priority moves count as public speed-breaking pressure
  only after the active player has shown them.

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
  prevention, public Perish Song escape, immunity pivot opportunity, and ace
  timing.
- `BossAI_SwitchOrTryItem` checks `BossAI_EnemyPerishEscapeUrgent` before
  `BossAI_HasAnyKOMove`, so a ticking Perish count can bypass the KO-stay gate.
- `BossAI_EnemyPerishEscapeUrgent` reads `wEnemySubStatus1` /
  `wEnemyPerishCount`, treats counts `1` and `2` as urgent, and never reads
  player hidden state.
- `.spikes_layer1` compares `wBossAITurnsElapsed` with `2`, not `0` or `1`.
- `.spikes_layer1` checks `.EnemyUnderPressure` before taking the high lead
  bias.
- `.StatusMoveWouldFailPublicly` covers `EFFECT_SLEEP`, `EFFECT_PARALYZE`,
  `EFFECT_CONFUSE`, `EFFECT_POISON`, `EFFECT_TOXIC`, and
  `EFFECT_LEECH_SEED`.
- `.StatusMoveWouldFailPublicly` calls the Dark shield helper before generic
  status encouragement, and that helper only hard-fails full-Dark active
  players with `wPlayerDarkShieldConsumed == 0`.
- `.UtilityMoveWouldFailPublicly` calls the Dark shield helper for public
  shield-eligible utility effects such as Disable, Encore, Spite, Attract, Mean
  Look, Nightmare, force-switch effects, and stat-down ranges.
- `.ApplyPoisonContactRiskBias` uses candidate move contact flags, player
  active Poison typing, current type matchup, enemy status/types/Safeguard, and
  a KO-line exception. It must not read hidden player items, bench moves, or
  current-turn player intent.
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
  Protect while already behind a Substitute, Disable with no public last counter
  move or an already-disabled player, Encore with no public last move or an
  already-encored player, Mean Look / Spider Web into a publicly already-trapped
  player, Dream Eater into visible player Substitute or a non-sleeping player,
  Nightmare into visible player Substitute, a non-sleeping player, or an
  already-nightmared player, and healing moves while already at full HP.
- Disable/Encore public fail gates must not inspect hidden player move slots or
  hidden PP. Those exact legality checks are Haki-only if they are ever used for
  boss decisions.
- Mean Look / Spider Web public fail gates must not inspect hidden reserve
  availability or last-mon legality. Damaging partial-trap effects are not
  equivalent because their damage can still be useful.
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
- `BossAI_PlayerHasRevealedPriorityThreat` scans only `wPlayerUsedMoves`,
  checks `EFFECT_PRIORITY_HIT`, type matchup, known defensive item nullification,
  and coarse enemy HP bands, and feeds both immediate pressure and lookahead
  pressure. `BossAI_ComputeSwitchCandidateRisk` separately checks
  half-HP-or-lower switch candidates against exact revealed priority using the
  candidate's base typing and own HP.
- `.ApplyRevealedProtectCommitmentRisk` scans only exact visible
  `wPlayerUsedMoves` for `EFFECT_PROTECT` and discourages Selfdestruct / Hyper
  Beam commitment lines without using current-turn input.
- `.ApplyRevealedRecoveryDenialBias` scans only exact visible
  `wPlayerUsedMoves` for recovery effects, requires the active player to be
  below full HP, refuses to override KO lines, and only rewards Toxic, Leech
  Seed, or force-switch moves after public fail gates pass.
- `.ApplyRevealedFastEncoreAvoidance` scans only exact visible
  `wPlayerUsedMoves` for `EFFECT_ENCORE`, refuses to run while the player is
  already encored, targets only recovery / Protect / Substitute / setup-style
  boss moves, and discourages them only when `BossAI_PublicEnemyFaster` says the
  boss does not move first. It must not read current-turn input, hidden move
  slots, or hidden PP.
- `.ApplyRevealedDestinyBondAvoidance` scans only exact visible
  `wPlayerUsedMoves` for `EFFECT_DESTINY_BOND`, requires a KO-pressure boss
  candidate, requires the active player to be visibly at quarter HP or lower,
  and discourages the KO only when `BossAI_PublicEnemyFaster` says the boss does
  not move first. It must not read current-turn input, hidden move slots, hidden
  PP, or hidden reserves.
- `.ApplyLastMoveEncoreTrapBias` reads only `wLastPlayerMove`, rejects empty /
  Struggle / Encore / Mirror Move cases, resolves that previous move's public
  effect, and rewards Encore only for Protect/Detect or recovery when public
  fail gates pass and `BossAI_PublicEnemyFaster` says the boss should move
  first. It must not read current-turn input, hidden move slots, or hidden PP.
- `.ApplyRevealedCounterCoatAvoidance` scans only exact visible
  `wPlayerUsedMoves` for Counter or Mirror Coat effects, checks the boss
  candidate's effective physical/special category, refuses to override KO lines,
  requires public matchup to be nonzero, and discourages only matching non-KO
  damaging moves. It must not read current-turn input or hidden player moves.
- `.ApplyRevealedAntiSetupAvoidance` scans only exact visible
  `wPlayerUsedMoves` for `EFFECT_RESET_STATS` or `EFFECT_FORCE_SWITCH`, checks a
  boost-only setup classifier, refuses to override KO lines, and discourages
  only non-KO boost setup. The boost classifier must not include Rain Dance or
  Sunny Day.
- `.ApplyRevealedSelfdestructProtectBias` scans only exact visible
  `wPlayerUsedMoves` for `EFFECT_SELFDESTRUCT`, requires Protect/Detect as the
  boss candidate, checks public utility fail gates, requires the active player to
  be half HP or lower, and refuses the scout line if the boss has any public KO
  move. It must not read current-turn input, hidden player moves, or hidden PP.
- Shared single-effect revealed scans should route through
  `.PlayerHasRevealedEffectA`. The invariant audit must keep proving that helper
  uses only `wPlayerUsedMoves`, `Moves + MOVE_EFFECT`, existing scratch bytes,
  and score-pointer-preserving calls.
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

Status: `FINISHED` for the current manifest's boss-position live
emulator/debugger floor. All 16 gym leaders plus Koga and Champion Lance have
current trace-ROM first-decision chosen-move proof under
`audit/boss_ai_trace/*_live.txt`. `shared_switch_loop` has a dedicated
repeated-switch fixture under `audit/boss_ai_trace/shared_switch_loop_live.txt`.
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

Generate or refresh real trainer decision states:

```powershell
python tools\trace\boss_ai_state_factory.py --all --update-manifest
```

Probe a Morty candidate state before adding it to the manifest:

```powershell
python tools\trace\boss_ai_trace_state_probe.py --save-state path\to\before_morty_decision.state --expect-morty --strict
```

Keep the `morty` manifest entry's `preflight.expect = morty` field. The batch
runner uses that field to reject stale Morty/Ecruteak states before capture.
The probe must reject both missing Morty object context and impossible active
player data such as copied SRAM showing `hp=64000/64000`.

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
  states, plus full HP with a healing move. Set the player behind Substitute
  against Dream Eater and Nightmare, including a sleeping target behind
  Substitute. Set already-active Nightmare too. Confirm the corresponding
  utility moves are heavily discouraged.
- Test Disable when the player is already disabled, when no public last counter
  move exists, and when the public last counter move is Struggle. Test Encore
  when the player is already encored, when no public last move exists, and when
  the public last move is Struggle, Encore, or Mirror Move. Test Mean Look /
  Spider Web when the player already has public `SUBSTATUS_CANT_RUN`, and keep
  Wrap-style damaging trap moves out of that full-fail expectation.
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
- Test contact moves into half-Poison and full-Poison active defenders. Confirm
  non-KO contact is penalized, KO pressure remains allowed, and already-statused
  or Poison/Steel enemy attackers are not penalized.
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

Shared Perish Song scenario:

- Put the boss active under public Perish Song with `wEnemyPerishCount` at `2`
  or `1` and a legal switch target available.
- Confirm the boss can consider switching even if the active mon has KO pressure.
- Confirm count `3` does not trigger the urgent escape bonus, and count `0` does
  not produce a bogus late switch request.

## Review Checklist

Status: `FINISHED` for the static/release audit sweep and current manifest live
emulator/debugger floor: all real trainer rows currently in the manifest have
first-decision chosen-move captures, and the shared switch-loop fixture has
switch-confidence proof.

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
- Trace excerpts exist for all tracked gym leaders plus Koga and Lance.
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
