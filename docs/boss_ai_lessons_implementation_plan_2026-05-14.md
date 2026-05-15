# Boss AI Lessons Implementation Plan - 2026-05-14

Status: planning only. No ROM behavior is implemented by this document.

Full-roadmap note:
this file became implementation-quality for the first revealed Rapid Spin /
Spikes patch only. Use
`docs/boss_ai_lessons_full_roadmap_plan_2026-05-14.md` for the properly planned
remaining roadmap.

Source brief:
`docs/pokemon_mastery/external_research_returns/codex_pokemon_gold_boss_ai_prompt.md`

User constraint:
ordinary boss AI must not cheat. The only allowed exceptions are the existing
speed-comparison exception and the explicitly quarantined Haki/oracle design.
This plan treats both as exceptions, not general permission to read private
state.

## 1. Current Objective

Create a full implementation plan for translating the source brief into
Gym Leader Lab ROM changes. The plan should make bosses stronger and more
human-like through small, traceable, public-information heuristics, without
implementing any ROM behavior yet.

The target behavior is not a perfect bot. The target is a 1300-1500-ish
human-feeling boss that:

- recognizes obvious KOs and deny-KOs;
- avoids dead setup, failed utility, and pointless status;
- protects route-critical pieces when public state says sacrifice is wasteful;
- cashes out with sacrifice moves when the public route value is high;
- understands local three-layer Spikes and Rapid Spin pressure;
- mixes close good moves without opening garbage randomness;
- stays inside the public-information model except for documented Haki.

## 2. Files Inspected

Core brief and design docs:

- `docs/pokemon_mastery/external_research_returns/codex_pokemon_gold_boss_ai_prompt.md`
- `docs/boss_ai_spec.md`
- `docs/boss_ai_post_patch_notes.md`
- `docs/boss_ai_trace_capture.md`
- `docs/agent_navigation/subsystems/boss_ai_logic.md`
- `engine/battle/ai/PLATFORM_API.md`
- `engine/battle/ai/POLICY_DESIGN.md`
- `docs/pokemon_mastery/romhack_deltas/spikes_and_rapid_spin.md`

Core source:

- `Makefile`
- `engine/battle/ai/move.asm`
- `engine/battle/ai/scoring.asm`
- `engine/battle/ai/boss_policy_move.asm`
- `engine/battle/ai/boss_policy_switch.asm`
- `engine/battle/ai/boss_platform.asm`
- `engine/battle/ai/boss_thunks.asm`
- `engine/battle/ai/boss_trace_topmoves.asm`
- `data/trainers/attributes.asm`
- `data/trainers/ai_tiers.asm`
- `constants/battle_constants.asm`
- `constants/move_effect_constants.asm`
- `ram/wram.asm`

Validation and fixture surfaces:

- `tools/audit/check_boss_ai_no_cheat.py`
- `tools/audit/check_boss_ai_gating.py`
- `tools/audit/check_boss_ai_trace_invariants.py`
- `tools/audit/check_boss_ai_memory_budget.py`
- `tools/audit/check_boss_ai_index_lines.py`
- `tools/audit/check_boss_ai_policy_contract.py`
- `tools/audit/check_boss_ai_live_capture_ledger.py`
- `tools/audit/check_release_smoke.py`
- `tools/boss_ai_debugger/*`
- `tools/boss_ai_preference/*`
- `audit/boss_ai_trace/live_capture_ledger.md`
- `audit/boss_ai_trace/live_capture_manifest.json`

Subagent reviews were also used for independent critique:

- code and ROM constraints;
- strategy priority;
- no-cheat boundary;
- validation and measurement.

## 3. Relevant Existing AI Flow

### ROM AI Hackability Audit

1. Base:
   This repo resembles a custom Pokemon Gold / `pokegold` disassembly hack,
   not `pokecrystal`. Boss AI is a Gym Leader Lab-specific overlay on top of
   the Gen 2 battle engine.

2. Build commands:
   Normal Gold/Silver build from PowerShell through WSL:

   ```powershell
   wsl -e bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'
   ```

   Canonical trace rebuild:

   ```powershell
   bash -lc 'rgbds-1.0.1/rgbasm.exe -Weverything -Wtruncation=1 -Q8 -P includes.asm -D _GOLD -D BOSS_AI_TRACE -o main_gold_trace.o main.asm && rgbds-1.0.1/rgbasm.exe -Weverything -Wtruncation=1 -Q8 -P includes.asm -D _GOLD -D BOSS_AI_TRACE -o ram_gold_trace.o ram.asm && rgbds-1.0.1/rgblink.exe -Weverything -Wtruncation=1 -l layout.link -n pokegold_trace.sym -m pokegold_trace.map -o pokegold_trace.gbc audio_gold.o home_gold.o main_gold_trace.o ram_gold_trace.o data/text/common_gold.o data/maps/map_data_gold.o data/pokemon/egg_moves_gold.o data/pokemon/evos_attacks_gold.o engine/movie/credits_gold.o engine/overworld/events_gold.o gfx/misc_gold.o gfx/sprites_gold.o gfx/tilesets_gold.o data/pokemon/dex_entries_gold.o gfx/pics_gold.o && rgbds-1.0.1/rgbfix.exe -Weverything -cjsv -k 01 -l 0x33 -m MBC3+TIMER+RAM+BATTERY -r 3 -p 0 -t POKEMON_GLD -i AAUE pokegold_trace.gbc && tools/stadium pokegold_trace.gbc'
   ```

   The build produces `.map`, `.sym`, and `.noi` through the normal linker
   outputs.

3. Battle AI files:
   `engine/battle/ai/move.asm` owns `AIChooseMove`; `scoring.asm` holds legacy
   scoring; `boss_policy_move.asm`, `boss_policy_switch.asm`,
   `boss_platform.asm`, `boss_thunks.asm`, and `boss_trace_topmoves.asm` hold
   the split boss AI. Trainer AI tier wiring lives in
   `data/trainers/ai_tiers.asm` and trainer attributes in
   `data/trainers/attributes.asm`.

4. Current move flow:
   `AIChooseMove` initializes move scores where lower is better. Unusable,
   disabled, or zero-PP moves are assigned high scores. If `wBossAITier != 0`,
   the boss path calls `BossAI_ApplyMoveModel`, then `BossAI_SelectMove`, and
   returns when `wBossAIMoveChoiceReady` is set. Tier 0 trainers keep vanilla
   behavior.

5. Current scoring:
   `BossAI_ApplyMoveModel` calls `BossAI_ResetTurnCaches`,
   `BossAI_SelectPlanIfNeeded`, and `BossAI_ComputePlayerPlausibleTypeMask`.
   It then scores each legal enemy move. Existing scoring already includes KO
   pressure, deny-KO, tempo, setup under pressure, public utility/status fail
   gates, setup punish, Spikes layers, phazing, Rapid Spin, Baton Pass, role
   bias, plan bias, poison contact, Destiny Bond, Counter/Mirror Coat,
   Protect, recovery, Encore, selfdestruct, sleep preemption, scout/repeat, and
   risky-effect handling.

6. Current selection:
   `BossAI_SelectMove` applies lookahead to near-top candidates, traces top
   moves under `BOSS_AI_TRACE`, then chooses between the best and second-best
   legal scores. A gap of at least 6 gives the best move 90 percent odds; a gap
   of at least 3 gives 75 percent; a smaller gap gives 60 percent. This means
   good-bucket behavior is already partially implemented. A new broad bucket is
   not the first patch unless measurement proves the current best-vs-second
   selector is the bottleneck.

7. Current switching:
   Boss switching lives in `boss_policy_switch.asm`. It uses public threat
   checks, switch confidence, candidate risk, seen-species revenge warnings,
   loop penalties, and public Perish Song escape. `BossAI_PredictPlayerSwitch`
   uses observed switch count, turn count, active HP band, public threat, and
   revealed super-effective moves. It does not read current-turn input.

8. Public-info state:
   The boss tracks seen player species, public faint/send-out state, active
   revealed moves, per-species revealed move masks, plausible and likely type
   masks, visible HP/status/boosts, Spikes layers, turn count, player switch
   count, and tier/personality rows. Exact active revealed moves are mirrored in
   `wBossAISpeciesUsedMoves`.

9. Trace/debug infrastructure:
   `BOSS_AI_TRACE` writes top moves, scores, chosen move, switch confidence,
   plan fields, plausible masks, risk flags, and lookahead bonus fields into
   WRAM symbols. The debugger and preference tools provide fixtures,
   pairwise/trajectory labels, regression checks, and scenario reports.

10. Custom mechanics relevant to AI:
   The hack has three-layer Spikes. `SCREENS_SPIKES` and `SCREENS_SPIKES_2`
   encode 0-3 layers through `SCREENS_SPIKES_MASK`; switch-in damage is
   1/8, 1/6, then 1/4 max HP. Rapid Spin clears both Spikes bits, so it removes
   all layers. Flying type ignores Spikes. Haki/oracle is documented as the
   only intentional unfair exception, but no source implementation was found in
   this audit.

### No-Cheat Boundary

Ordinary boss AI may use only public or boss-owned information. It must not
read hidden party slots, hidden moves, hidden PP, hidden held items, private
stats, private menu state, current-turn player input, or player reserve state.

Approved exceptions:

- Existing speed comparison exception:
  `BossAI_SetupBoostHasFurtherValue` may call `AICompareSpeed` to stop valuing
  additional Speed setup after exact active battle speed already says the boss
  outspeeds the active player. Do not expand this exception without a new
  explicit design note.
- Haki/oracle:
  if implemented later, it is one activation per battle, only named late/major
  bosses, only on the ace's first active turn, only in the approved post-input
  window, and traceable. It must not become a helper for ordinary boss scoring.

## 4. Memory / Bank / Space Notes

Normal build was successfully run for `pokegold.gbc` and `pokesilver.gbc`.
Current map summary after that build:

- ROM0: 15650 used, 734 free.
- ROMX total: 1136267 used, 944501 free.
- SRAM: 31699 used, 1069 free.
- WRAM0: 4049 used, 47 free.
- WRAMX: 4096 used, 0 free.
- HRAM: 127 used, 0 free.

Important sections:

- `Enemy Trainers`: currently `0e:4000-6fe7`.
- `AI Scoring`: currently `0b:6c35-7bc5`.
- `Boss AI Trace`: exists at bank 1 start and is size 0 in a normal build.

Boss WRAM budget:

- The reserved boss AI block starts at `wBossAITier`.
- Normal logical end is `wBossAIStateEnd`.
- The reserve is `140` bytes.
- Existing docs report normal boss state using `104` bytes with `36` reserved
  bytes free, and trace state using `123` bytes with `17` reserved bytes free.
- WRAMX overall has no unreserved free space. Future patches should strongly
  prefer zero new WRAM.

Current validation hygiene blockers:

- After the fresh normal build, `tools/audit/check_boss_ai_memory_budget.py`
  fails because `docs/generated/dev_index.md` is stale and expects the old
  `Enemy Trainers` range. Regenerate the dev index before treating the memory
  budget gate as green.
- `tools/audit/check_boss_ai_live_capture_ledger.py` fails because the trace
  ROM hash in the manifest/ledger does not match the rebuilt trace artifacts.
  Rebuild the trace ROM and update the manifest/ledger hashes before treating
  live trace proof as green.
- `tools/audit/verify_sha1.py roms.sha1` is not a clean gate in this worktree
  because normal Gold/Silver hashes are already divergent from baseline.

## 5. Proposed Patch Contract

First implementation patch to plan, not implement now:

Name:
Public revealed-spinner hazard retention.

One-sentence purpose:
Discourage additional Spikes layers when the active player has already revealed
Rapid Spin and can publicly erase the whole stack.

Human battle behavior:
A competent GSC player does not spend a free turn stacking more hazards into an
active spinner that has already shown the spin button unless the hazard turn is
still converting immediately or the spinner is being forced out/punished.

Trigger:

- Current enemy move being scored has `EFFECT_SPIKES`.
- Player side already has one or two Spikes layers:
  `wPlayerScreens & SCREENS_SPIKES_MASK` is `1` or `2`.
- The active player Pokemon has publicly revealed `EFFECT_RAPID_SPIN`, checked
  through `.PlayerHasRevealedEffectA`, which scans only `wPlayerUsedMoves`.
- No hidden player species, hidden move slot, hidden PP, hidden item, or
  current input is read.

Default:

- Apply a tier-weighted Spikes discouragement before the current layer-2 or
  layer-3 positive branch returns.
- Preserve the existing no-spin behavior:
  - no layers: keep first-layer logic unchanged;
  - one layer and no revealed spin: keep the existing second-layer boundary;
  - two layers and no revealed spin: keep the existing strong third-layer push;
  - three layers: keep the existing fourth-click discouragement.

Exception:

- Do not fire for unrevealed Rapid Spin, even if the active species can learn
  it.
- Do not fire for previously seen bench species that revealed Rapid Spin unless
  they are the active Pokemon and their revealed used-move list is loaded.
- Do not fire at zero layers in the first patch; first-layer Spikes is a
  separate tempo question, not stack-retention.
- If fixture evidence shows this suppresses a forced-switch third-layer line,
  narrow the trigger with the existing `BossAI_PredictPlayerSwitch` threshold
  rather than broadening hidden-info reads.

Information legality:
The patch reads only the move being scored, public target-side Spikes bits, and
the active player's revealed used-move list. It does not infer the player's
unrevealed moveset, reserves, held item, PP, or selected action.

Memory/code budget:

- Estimated code: 20-45 ROM bytes in `engine/battle/ai/boss_policy_move.asm`.
- Estimated tables: none.
- Estimated WRAM/HRAM/SRAM: 0 bytes.
- Target bank/section: existing boss move policy section, same local helper
  cluster as `.ApplySpikesLayerBias`.
- Actual bytes: TBD after implementation and map comparison.

Trace hook:

- Minimum: prove through preference fixture score/rank changes and
  `BOSS_AI_TRACE` top-move/top-score fields.
- Optional if byte budget allows: set an unused `wBossAITraceRiskFlags` bit
  under `BOSS_AI_TRACE` when the revealed-spinner Spikes penalty fires, then
  document the bit in `docs/boss_ai_trace_capture.md`.
- Do not add a new trace WRAM byte for this first patch.

Failure mode:

- Over-penalizing Spikes may make Janine/Koga stop converting strong hazard
  routes merely because the spinner has revealed Spin.
- If the trigger includes legal-learnset priors instead of exact revealed Spin,
  it becomes too predictive and feels like hidden moveset reading.
- If the trigger looks at seen bench spinners, it may punish a current active
  Pokemon for a move it does not have.

Tests:

1. Should trigger:
   Use or extend the existing public-spinner holdout benchmark so Janine's
   Qwilfish at one or two layers faces an active player Pokemon with Rapid Spin
   in `wPlayerUsedMoves`. Spikes should fall behind a live damage/cash-out line.
2. Should not trigger:
   `janine_qwilfish_finish_third_spikes_layer` remains Spikes-favored when
   there are two layers, the player is grounded, no Spin is revealed, and no
   immediate public KO threat is present.
3. Edge/adversarial:
   A species that can legally learn Rapid Spin but has not revealed it must not
   suppress Spikes. This guards the no-cheat boundary around hidden moves.

Rollback:

- Revert only the small branch added inside `.ApplySpikesLayerBias`.
- Remove any added fixture labels and trace-risk-flag docs for this patch.
- No runtime state migration is needed because the patch uses no new WRAM.

## 6. Implementation Summary

No ROM implementation was performed. The user explicitly requested a plan only.

Implementation order for the next coding turn:

1. Clean validation prerequisites:
   regenerate `docs/generated/dev_index.md` after the current build outputs,
   then rerun `check_boss_ai_memory_budget.py`.
2. Add or tighten the three preference/debugger fixtures for the first patch.
3. Implement the narrow `.ApplySpikesLayerBias` revealed-Rapid-Spin branch.
4. Build Gold and Silver.
5. Compare map/WRAM deltas.
6. Run the static audit floor and preference regression.
7. If trace artifacts are refreshed, capture or at least dry-run a targeted
   trace for a Janine/Koga Spikes position.

## 7. Changed Files

Changed by this planning task:

- `docs/boss_ai_lessons_implementation_plan_2026-05-14.md`

Planned future first patch write set:

- `engine/battle/ai/boss_policy_move.asm`
- `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`
- `tools/boss_ai_preference/labels/boss_ai_pairwise_preferences.jsonl`
- possibly `tools/boss_ai_debugger/tests/*` if the fixture needs a debugger
  regression wrapper
- optionally `docs/boss_ai_trace_capture.md` only if a trace risk bit is added

## 8. Build/Test Commands Run

Planning audit commands already run:

```powershell
git status --short --branch
git rev-parse --short HEAD
python tools\audit\check_boss_ai_policy_contract.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_boss_ai_index_lines.py
python -m tools.boss_ai_preference validate
python -m tools.boss_ai_debugger list
python -m tools.boss_ai_debugger regress
python tools\audit\check_release_smoke.py
python tools\audit\check_ai_tiers.py
python tools\audit\check_boss_items_present.py
python tools\audit\check_boss_moves_complete.py
python tools\audit\check_gym_leader_wiring.py
python tools\audit\check_boss_ai_live_capture_ledger.py
python -m tools.boss_ai_debugger report
python tools\audit\check_boss_ai_preference_regression.py
python tools\audit\check_mechanics_docs_and_fixtures.py
python tools\audit\check_pokemon_mastery_measurement.py
python tools\audit\check_boss_ai_preference.py
```

Normal build command run:

```powershell
wsl -e bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'
```

Commands to run after the first future patch:

```powershell
wsl -e bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_boss_ai_index_lines.py
python -m tools.boss_ai_preference validate
python tools\audit\check_boss_ai_preference_regression.py
python -m tools.boss_ai_debugger regress
python tools\audit\check_release_smoke.py
```

Trace commands to run only after refreshing trace hashes:

```powershell
python tools\trace\boss_ai_state_factory.py --boss janine --update-manifest
python tools\trace\boss_ai_trace_batch.py
python tools\trace\boss_ai_trace_batch.py --execute --only janine
python tools\audit\check_boss_ai_live_capture_ledger.py
```

## 9. Test Results

Passing audit/test results from the planning pass:

- `check_boss_ai_policy_contract.py`: PASS.
- `check_boss_ai_no_cheat.py`: PASS.
- `check_boss_ai_gating.py`: PASS.
- `check_boss_ai_trace_invariants.py`: PASS.
- `check_boss_ai_index_lines.py`: PASS before the fresh build changed map
  addresses.
- `python -m tools.boss_ai_preference validate`: PASS.
- `python -m tools.boss_ai_debugger regress`: PASS, 43/43 strict pairwise
  labels agree.
- `check_release_smoke.py`: PASS, with stale-shipped-claim warnings only in
  handoff docs.
- `check_ai_tiers.py`: PASS.
- `check_boss_items_present.py`: PASS.
- `check_boss_moves_complete.py`: PASS.
- `check_gym_leader_wiring.py`: PASS.
- `check_boss_ai_preference_regression.py`: PASS.
- `check_mechanics_docs_and_fixtures.py`: PASS.
- `check_pokemon_mastery_measurement.py`: PASS.
- `check_boss_ai_preference.py`: PASS.
- Gold/Silver normal build: PASS.

Known non-green gates:

- `check_boss_ai_memory_budget.py`: passed before the fresh build, then failed
  after the fresh build because `docs/generated/dev_index.md` is stale.
- `check_boss_ai_live_capture_ledger.py`: FAIL due trace ROM hash mismatch.
- `python -m tools.boss_ai_debugger report`: currently reports 0 labels across
  0/57 fixtures; use `validate` and `regress` as the meaningful preference
  gates unless this report command is repaired.

## 10. Trace/Audit Evidence

Evidence that supports the first patch choice:

- Local mechanics docs confirm Rapid Spin clears all local Spikes layers.
- `.ApplySpikesLayerBias` already contains layer-aware scoring for 0, 1, 2, and
  3 layers.
- `.PlayerHasRevealedEffectA` already provides a public active revealed-effect
  scanner over `wPlayerUsedMoves`.
- Existing labels already separate "third layer with no Spin revealed" from
  "public spinner holdout" style positions.
- `check_boss_ai_no_cheat.py` passes in the current source and should remain
  the hard floor for any new heuristic.

Evidence that argues against starting with a broad good-bucket rewrite:

- `BossAI_SelectMove` already selects best versus second-best with weighted
  randomness based on score gap.
- `BossAI_ApplyLookaheadToTopMoveCandidates` already adjusts near-top moves
  before selection for mid/late tiers.
- The current failure risk is more likely bad action admission or missing
  narrow tactical penalties than lack of randomization infrastructure.

Evidence that argues against adding new tendency counters first:

- WRAMX has no unreserved free space.
- The boss AI reserve has limited free bytes and trace builds are tighter.
- The first useful hazard patch needs no new state.

## 11. Strategic Effect

The first patch makes the AI less autopilot around local hazards:

- It preserves the strong existing lesson that a safe third Spikes layer is
  scary in this hack.
- It adds the missing route-retention lesson that a revealed active spinner can
  erase the entire stack, so stacking into it is not automatically progress.
- It is visible to the player as fair adaptation because the spinner must have
  revealed Rapid Spin first.
- It should make Janine/Koga-style hazard turns feel less scripted while
  avoiding hidden team prediction.

Longer roadmap, ranked by byte cost, risk, and strategic value:

1. Public revealed-spinner hazard retention:
   implement the first patch above.
2. Four-move saturation of plausible threats:
   when the active species has publicly revealed all four real moves, stop
   treating unrevealed legal-learnset coverage as still possible for that
   active species. Before coding, audit `wPlayerUsedMoves` for Transform,
   Mimic, Metronome, Sleep Talk, and any copied-move edge cases.
3. Anti-dead-setup tightening:
   narrow setup encouragement when the boss is low HP and the active player has
   public KO pressure, unless setup immediately produces a KO, survival, or
   route-preserving effect.
4. Status hard-answer discipline:
   extend existing status fail gates into a small "take the hard answer first"
   bias when a public KO/deny-KO is available and status is slower.
5. Cash-out / Explosion route discipline:
   refine sacrifice moves so they are encouraged when they remove a public route
   piece or deny setup, and discouraged when they trade a useful boss mon for
   low-value chip.
6. Preservation switch refinement:
   improve the Koga/Ariados-style case where a hazard/status piece should pivot
   out from revealed lethal pressure instead of spending a dead turn.
7. Good-bucket tuning:
   only after hard rejects and tactical penalties are reliable, tune the current
   best-vs-second selector or extend it to top-three if traces prove the second
   best restriction is too narrow.
8. Tiny tendency counter:
   add at most one 1-bit or 2-bit public tendency counter after the zero-WRAM
   heuristics have shipped and the reserve budget is freshly proven.
9. Boss personality weighting:
   tune existing tier/role rows before adding new tables. Personality should
   modulate score bias, not create bespoke per-leader mini-AIs.
10. Haki/oracle:
   implement only as its own explicitly quarantined feature, one leader at a
   time, after ordinary public-info behavior is stable. It should never be
   smuggled into the ordinary move scorer.

Candidate ranking from the source brief:

| Candidate | Rank | Reason |
| --- | ---: | --- |
| F: hazard retention / spin awareness | 1 | clear hook, local mechanic verified, no WRAM, existing fixtures |
| B: anti-dead-setup gate | 2 | high visible value, but needs KO-pressure edge review |
| C: status target discipline | 3 | already partly implemented; next work should be narrow |
| E: cash-out / Explosion discipline | 4 | high value, more route-context risk |
| D: recovery timing | 5 | valuable but easy to make passive |
| A: good-bucket mixing | 6 | partially implemented already |
| H: boss personality weighting | 7 | useful after underlying scores are cleaner |
| G: player tendency counter | 8 | delayed by WRAM budget and timing complexity |

## 12. Known Risks / Exploit Cases

- A broad "spinners exist" rule would cheat by inferring hidden moves. The first
  patch must require exact active revealed Rapid Spin.
- A broad "do not stack into revealed Spin" rule can become too passive if the
  spinner is being forced out. Start narrow and let the fixture decide whether
  `BossAI_PredictPlayerSwitch` should create an exception.
- Four-move saturation is attractive but risky until copied or temporary move
  mechanics are audited. Do not assume `wPlayerUsedMoves` always means the
  original four party moves.
- Anti-dead-setup can suppress legitimate last-chance setup. It needs an
  exception for immediate route conversion and should avoid exact private damage
  helpers.
- Explosion discipline can become overfit if "key threat" is inferred from
  unseen reserves. It must stay tied to active visible pressure or already seen
  species.
- Good-bucket expansion can make the AI worse if bad moves survive hard gates.
  It should be a tuning patch after action quality is cleaner.
- Haki is intentionally unfair, but only inside its contract. User approval of
  Haki does not permit ordinary scoring to read current input.

## 13. Rollback Instructions

For this planning artifact:

- Delete `docs/boss_ai_lessons_implementation_plan_2026-05-14.md`.

For the first future behavior patch:

- Revert the small `.ApplySpikesLayerBias` branch.
- Revert the related fixture/label additions.
- If a trace risk flag was added, revert the bit write and docs update.
- Rerun the same audit floor to confirm the previous behavior is restored.

For any future patch in the roadmap:

- Keep each heuristic in one local branch/helper when possible.
- Add one fixture id per trigger family so rollback can remove source and
  evidence together.
- Avoid new WRAM unless the field is clearly named, cleared by
  `ClearBossAIState`, indexed in docs, and covered by memory-budget audits.

## 14. Next Smallest Useful Patch

Before coding, repair the validation floor:

1. Regenerate `docs/generated/dev_index.md` from the current map/symbol outputs.
2. Rerun `python tools\audit\check_boss_ai_memory_budget.py`.
3. Decide whether to refresh trace ROM hashes now or defer live trace proof
   until after the small patch builds.

Then implement exactly one behavior patch:
Public revealed-spinner hazard retention in `.ApplySpikesLayerBias`.

The intended implementation shape is:

```asm
; Inside the layer-2 and layer-3 Spikes branches only.
ld a, EFFECT_RAPID_SPIN
call .PlayerHasRevealedEffectA
jr c, .spikes_revealed_spinner_active
```

`spikes_revealed_spinner_active` should apply a tier-weighted discouragement
and return, with no hidden party/move reads and no new WRAM.

Success criteria for the first future patch:

- Gold/Silver build passes.
- No-cheat/gating/trace/index/memory audits pass after dev-index refresh.
- Preference regression remains green.
- The trigger fixture changes in the intended direction.
- The no-spin third-layer fixture remains Spikes-favored.
- The unrevealed-spinner edge fixture does not fire.
- Map delta records exact ROM byte impact and confirms no WRAM/HRAM use.
