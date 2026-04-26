# Labeled Bug Findings - 2026-04-26

Scope: broad bug-labeling pass on the current dirty checkout. Source/gameplay
fixes were initially out of scope; after the latest request, the labeled open
Boss AI bugs were fixed directly. Documentation drift discovered during the pass
was allowed to be corrected.

Current bug count:

- `OPEN`: 0
- `RESOLVED_THIS_SESSION`: 14
- `RESOLVED_IN_CURRENT_SOURCE`: 2
- New source/tooling/doc fix areas applied during this labeling pass: 20
  (8 source fixes, 9 invariant/smoke-audit/tooling coverage additions, 2
  follow-up navigation/evidence corrections, 1 generated-index refresh)

Investigation frame:

- Target route: broad bug hunt, then changed-source Boss AI/data/docs surfaces.
- Source truth: current source files and linker/generated mirrors.
- Generated files: `docs/generated/dev_index.md` was regenerated through
  `scripts/generate_dev_index.py` after a navigation check found stale Boss AI
  anchors. `docs/generated/balance_audit.md` was checked by temp generation
  only, not hand-edited.
- Manual proof gap: no emulator playtest was run in this pass.

## Resolved In Current Source

### BUG-2026-04-26-001 - P1 - Boss AI held-item reasoning compares item IDs to held-effect constants

Status: `RESOLVED_IN_CURRENT_SOURCE`

Surface: Boss AI move scoring, pressure scoring, speed estimation, and threat
severity adjustment.

Original evidence:

`wEnemyMonItem` stores the held item ID, not the held-effect enum. Comparing it
directly to `HELD_*` constants makes the new Boss AI held-item reasoning miss
real held effects. The actual battle engine can still enforce item behavior, but
the Boss AI scoring model can reason as if Life Orb, Choice items, Assault Vest,
Eviolite, Air Balloon, Shell Bell, and similar custom effects are absent.

Current source recheck:

- `engine/battle/ai/boss.asm:3131` defines `BossAI_GetEnemyHeldEffect`.
- `engine/battle/ai/boss.asm:3133` reads raw `wEnemyMonItem`, then calls
  `GetItemHeldEffect` and returns the held-effect value in `a`.
- The old held-item reasoning sites now call `BossAI_GetEnemyHeldEffect`
  before comparing against `HELD_*`, including Assault Vest legality,
  Life Orb/Shell Bell move bias, offensive item pressure, Choice Scarf speed,
  Assault Vest/Eviolite threat adjustment, and Air Balloon nullification.
- `rg -n "ld a, \[wEnemyMonItem\]|cp HELD_" engine\battle\ai\boss.asm`
  now shows the only raw `wEnemyMonItem` read inside `BossAI_GetEnemyHeldEffect`.

Source fix ownership:

No source fix was applied during this labeling pass. The current dirty checkout
already contains the helper-based fix, so the documentation label was corrected
to match current source truth.

Remaining related issue:

The current checkout also resolves the audit coverage gap tracked as
`BUG-2026-04-26-002`.

### BUG-2026-04-26-002 - P2 - Boss AI invariant audit accepts the broken held-item pattern

Status: `RESOLVED_IN_CURRENT_SOURCE`

Surface: `tools/audit/check_boss_ai_trace_invariants.py`

Original evidence:

The audit previously checked for held-item reasoning strings such as
`HELD_ASSAULT_VEST`, `HELD_LIFE_ORB`, `HELD_CHOICE_BAND`, `HELD_EVOLITE`, and
`HELD_AIR_BALLOON`, but did not require Boss AI source to call
`GetItemHeldEffect` or an equivalent helper.

Current source recheck:

- `tools/audit/check_boss_ai_trace_invariants.py:597` now requires
  `BossAI_GetEnemyHeldEffect` to call `GetItemHeldEffect`.
- The same audit now requires `call BossAI_GetEnemyHeldEffect` in the choice
  lock helper, offensive item pressure, Choice Scarf speed model, defensive
  threat adjustment, and Air Balloon nullifier.
- `python tools\audit\check_boss_ai_trace_invariants.py` passes on the current
  checkout.

Source fix ownership:

No tooling fix was applied during this labeling pass. The current dirty
checkout already contains the helper-aware audit checks, so the documentation
label was corrected to match current source truth.

## Resolved This Session

### BUG-2026-04-26-004 - P3 - Switch-risk helpers leak candidate base-data state

Status: `RESOLVED_THIS_SESSION`

Surface: Boss AI switch-loop exceptions and plausible-risk switch refinement.

Original evidence:

- `engine/battle/ai/boss.asm:2890` defines
  `BossAI_IsImmunityPivotOpportunity`.
- `engine/battle/ai/boss.asm:2916` writes a candidate party species into
  `wCurSpecies`.
- `engine/battle/ai/boss.asm:2917` calls `GetBaseData`.
- Before this fix, success and no-immunity paths returned without restoring the
  previous `wCurSpecies` or active-mon base-data mirror.
- `engine/battle/ai/boss.asm:5239` defines `BossAI_ComputeSwitchCandidateRisk`.
- `engine/battle/ai/boss.asm:5252` writes the candidate species into
  `wCurSpecies`.
- `engine/battle/ai/boss.asm:5253` calls `GetBaseData`.
- Before this fix, normal and hard-risk exits returned without restoring prior
  species/base data.
- The local safe pattern exists nearby:
  `engine/battle/ai/boss.asm:2621` to `engine/battle/ai/boss.asm:2684`
  saves and restores `wCurSpecies` around `GetBaseData` in
  `BossAI_PublicEnemyFaster`.
- `docs/bug_hunt_master_playbook.md` calls out this exact bug class: helpers
  that write `wCurSpecies`, `wCurPartySpecies`, `wBaseType1`, `wBaseType2`, or
  base-data fields through `GetBaseData` need proven restore behavior or a
  documented downstream contract.

Why this is a bug:

`wCurSpecies` and the `wBase*` mirror are global scratch state. These helpers
temporarily load candidate switch-in base data, but their names and callers read
like pure risk predicates. After a loop-penalty exception or switch-risk scan,
later Boss AI logic can inherit base data for the proposed switch target rather
than the active enemy unless every downstream consumer happens not to care.

Current observed consequence:

No audit failure or crash was observed in this pass. The current nearby callers
mostly use active battle structs after these helpers, which makes the bug
latent rather than immediately proven in a live trace. It is still labeled
because the state mutation violates the repo's own assembly audit rule and
creates a fragile hidden contract in the highest-churn Boss AI path.

Fix applied:

- `BossAI_IsImmunityPivotOpportunity` now saves `wCurSpecies` before loading the
  candidate, restores it on immune, not-immune, and early-no paths, and reloads
  base data for the saved species when nonzero.
- `BossAI_ComputeSwitchCandidateRisk` now saves `wCurSpecies` before candidate
  risk scoring and funnels both normal and hard-risk exits through
  `.restore_return`, preserving the computed risk in `b` while reloading the
  saved species base data.
- `tools/audit/check_boss_ai_trace_invariants.py` now checks the restoration
  shape for both helpers.

Residual proof gap:

No emulator/debugger trace was captured. The static invariant audit now covers
the restore contract, and a ROM rebuild was run after the fix.

### BUG-2026-04-26-005 - P3 - Boss AI Baton Pass bias ignores the no-bench failure path

Status: `RESOLVED_THIS_SESSION`

Surface: Boss AI move scoring for Baton Pass users.

Original evidence:

- `engine/battle/ai/boss.asm:903` defines `.ApplyBatonPassBias`.
- Before this fix, the helper checked only `.EnemyHasBoostToPass` before
  treating Baton Pass as good.
- `engine/battle/ai/boss.asm:1216` to `engine/battle/ai/boss.asm:1228`
  shows `.EnemyHasBoostToPass` only scans current enemy stat stages.
- `engine/battle/move_effects/baton_pass.asm:47` to
  `engine/battle/move_effects/baton_pass.asm:48` shows the actual enemy Baton
  Pass command fails when `CheckAnyOtherAliveEnemyMons` finds no living bench.
- `engine/battle/ai/boss.asm:1935` defines
  `BossAI_FindFirstAliveSwitchCandidate`, so Boss AI already has a nearby
  bench-alive predicate.
- Current boss parties include Baton Pass users: Whitney's Girafarig
  (`data/trainers/parties.asm:25`), Bugsy's Ledian
  (`data/trainers/parties.asm:33`), and Sabrina's Espeon
  (`data/trainers/parties.asm:1424`).

Why this is a bug:

When a Baton Pass user has any boosted stat, Boss AI can encourage Baton Pass
even if that mon is the last living enemy. The battle command will then fail,
so the AI can spend a turn choosing a move that cannot execute.

User-visible consequence:

A boosted last-mon Ledian, Girafarig, Espeon, or future Baton Pass boss mon can
waste a turn on failed Baton Pass instead of attacking, healing, setting a
screen, or making another legal play.

Fix applied:

- `.ApplyBatonPassBias` now calls `BossAI_FindFirstAliveSwitchCandidate` before
  considering boosts.
- If no living non-current enemy party member exists, the AI takes the same bad
  path used for unboosted Baton Pass and discourages the move.
- The helper call is wrapped in `push hl` / `pop hl` so the current move-score
  pointer survives before `BossAI_DiscourageScoreHL` or
  `.EncourageByTierWeight`.
- `tools/audit/check_boss_ai_trace_invariants.py` now checks that Baton Pass
  bias requires a living bench and preserves `hl`.

Residual proof gap:

No live trace was captured for a boosted last-mon Baton Pass scenario. The static
invariant audit now covers the scoring gate, and a ROM rebuild was run after the
fix.

### BUG-2026-04-26-006 - P2 - Plausible-threat species scan restores base data to the wrong species

Status: `RESOLVED_THIS_SESSION`

Surface: Boss AI public move-inference cache and any later helper that expects
`wCurSpecies` / base data to still describe the active species.

Original evidence:

- `docs/boss_ai_spec.md` says `BossAI_AddSpeciesAndPreEvolutionMovesToMask`
  temporarily mutates `wCurPartySpecies`, `wCurSpecies`, and base data while
  walking pre-evolutions, then must restore the active species and call
  `GetBaseData` before returning.
- `engine/battle/ai/boss.asm:3799` calls that helper while recomputing the
  public plausible-threat mask.
- Before this fix, `BossAI_AddSpeciesAndPreEvolutionMovesToMask` saved the
  original `wCurPartySpecies`, but did not save the original `wCurSpecies`.
- Its `.restore` path wrote `wBossAITemp4` back to `wCurSpecies`; that temp is
  the public player species being scanned, not the pre-call species.
- A nearby dormant helper, `BossAI_SeenSpeciesThreatScore`, had the same state
  hazard: it loaded seen player species through `GetBaseData` and returned a
  score without restoring `wCurSpecies` / base data.

Why this is a bug:

`BossAI_ComputePlayerPlausibleTypeMask` is called before move scoring,
lookahead, and switch decisions. A cache recompute can therefore leave the global
base-data mirror pointed at the public player species rather than whatever
species was active before the cache walk. Most nearby logic reads explicit battle
structs, which makes the failure mode selective, but the helper violated its own
documented state contract in a hot Boss AI entry path.

Fix applied:

- `BossAI_AddSpeciesAndPreEvolutionMovesToMask` now saves the incoming
  `wCurSpecies` on the stack before mutating `wCurPartySpecies`, restores both
  `wCurPartySpecies` and `wCurSpecies`, and reloads base data for the restored
  species when nonzero.
- `BossAI_SeenSpeciesThreatScore` now saves and restores `wCurSpecies`, reloads
  base data after restoration, and preserves its computed score across that
  reload.
- `tools/audit/check_boss_ai_trace_invariants.py` now checks both restore
  shapes as part of the plausible-threat source invariants.

Residual proof gap:

No live trace was captured for a downstream wrong decision from the stale
base-data mirror. The static invariant audit now covers the contract, and a ROM
rebuild was run after the fix.

### BUG-2026-04-26-007 - P2 - Legacy switch scoring leaks candidate base data and scans a fake species

Status: `RESOLVED_THIS_SESSION`

Surface: Non-boss trainer switch scoring through `CheckAbleToSwitch`.

Original evidence:

- `engine/battle/ai/items.asm:56`, `engine/battle/ai/items.asm:91`, and
  `engine/battle/ai/items.asm:125` call the switchability check for ordinary
  trainer switch decisions.
- `engine/battle/ai/switch.asm:230` calls
  `FindEnemyMonsImmuneToLastCounterMove`.
- `engine/battle/ai/switch.asm:339` defines that helper, which loads candidate
  party species into `wCurSpecies`, called `GetBaseData`, and originally
  returned to the caller without any entrypoint-level restore of the pre-call
  species/base-data mirror.
- `engine/battle/ai/switch.asm:194` and `engine/battle/ai/switch.asm:276` call
  `FindEnemyMonsThatResistPlayer`.
- `engine/battle/ai/switch.asm:543` defines that helper, which has the same
  candidate-species `GetBaseData` scan.
- Before this fix, `FindEnemyMonsThatResistPlayer` started its species scan at
  `wOTPartyCount`. That made the first scanned "species" the party-count byte
  rather than `wOTPartySpecies[0]`.

Why this is a bug:

The legacy switch scorer can decide not to switch and fall back to item/move
flow. If a candidate scan leaves `wCurSpecies` and base data pointed at a party
candidate rather than the pre-call species, later battle AI or move code inherits
hidden global state from a failed switch consideration. This is the same
base-data leak class as the Boss AI switch-risk bugs, but on the non-boss
trainer path.

Fix applied:

- The ordinary-trainer callers now go through
  `AI_CheckAbleToSwitchPreserveCurSpecies`, which saves `wCurSpecies`, calls
  `CheckAbleToSwitch`, then restores/reloads the pre-call species/base data
  before returning to item/switch decision flow. This keeps the restore code out
  of the already-full `Effect Commands` bank.
- `FindEnemyMonsThatResistPlayer` now starts at `wOTPartySpecies`, so the first
  candidate is the actual first party species rather than `wOTPartyCount`.
- `tools/audit/check_boss_ai_trace_invariants.py` now includes a legacy switch
  base-data restoration check and a guard for the party-species scan start.

Residual proof gap:

No live trace was captured for an ordinary trainer choosing not to switch after
one of these candidate scans. The static invariant audit now covers the restore
contract, and a forced ROM rebuild was run after the fix.

### BUG-2026-04-26-008 - P2 - Script XY compare uses a constant Y coordinate

Status: `RESOLVED_THIS_SESSION`

Surface: overworld `xycompare` script support in `SetXYCompareFlags`.

Original evidence:

- `home/region.asm:51` loads `wPlayerMapX`, adds the map-script coordinate
  offset `$4`, and stores the result in `d`.
- Before this fix, the matching Y path loaded `wPlayerMapY`, then immediately
  replaced it with the literal `$4` before storing `e`.
- The stale inline comment already stated the intended operation:
  `should be "add $4"`.
- `Script_xycompare` stores a pointer in `wXYComparePointer`, and
  `SetXYCompareFlags` compares that table against the adjusted player X/Y
  coordinates.

Why this is a bug:

The helper compared every XY table row against `player_x + 4` and a constant
Y value of `4`. Any script that enables `xycompare` for rows other than the
top offset row would fail to set the intended compare flag, while row-4 entries
could be reported at the wrong player Y position.

Fix applied:

- `SetXYCompareFlags` now mirrors the X path: load `wPlayerMapY`, add `$4`,
  and store the adjusted coordinate in `e`.
- `tools/audit/check_release_smoke.py` now checks this exact coordinate-offset
  shape so the old literal-load bug cannot return silently.

Residual proof gap:

No emulator/script fixture was run against a live `xycompare` table. The static
release smoke guard checks the corrected instruction sequence, and a ROM rebuild
was run after the fix.

### BUG-2026-04-26-009 - P2 - NPC trade stat recompute writes level to a struct offset

Status: `RESOLVED_THIS_SESSION`

Surface: NPC trade received-mon stat recalculation.

Original evidence:

- `engine/events/npc_trade.asm` calls `ComputeNPCTrademonStats` after replacing
  the player's traded mon with the received NPC trade mon.
- `ComputeNPCTrademonStats` reads the received mon's `MON_LEVEL` byte through
  `GetPartyParamLocation`.
- Before this fix, it wrote that level to `[MON_LEVEL]`, treating a party-struct
  offset constant as an absolute RAM address.
- `CalcMonStats`, which is called immediately afterward, reads the active level
  from `wCurPartyLevel`.
- The stale inline comment already stated the intended target:
  `should be "ld [wCurPartyLevel], a"`.

Why this is a bug:

The helper was supposed to recompute the received NPC trade mon's stats using
its actual party level. Instead, the level byte was not copied into the scratch
state that `CalcMonStats` consumes. In the best case, this relied on stale
`wCurPartyLevel` still being correct from earlier trade setup; in the worst
case, it wrote to the low absolute address represented by the struct offset.

Fix applied:

- `ComputeNPCTrademonStats` now stores the received mon's level in
  `wCurPartyLevel` before calling `CalcMonStats`.
- `tools/audit/check_release_smoke.py` now checks this exact level-load/store
  shape in the NPC trade stat recompute path.

Residual proof gap:

No emulator NPC-trade flow was run. The static release smoke guard checks the
corrected stat-recompute shape, and a ROM rebuild was run after the fix.

### BUG-2026-04-26-010 - P3 - Trade mail receive compaction copies past the mail buffer

Status: `RESOLVED_THIS_SESSION`

Surface: link trade mail receive/patch handling.

Original evidence:

- `engine/link/link.asm` receives trade mail into `wLinkOTMail`, then scans for
  the mail preamble and compacts the received payload down to the start of
  `wLinkOTMail`.
- Before this fix, the compaction copy used
  `wLinkDataEnd - wLinkOTMail` as its byte count.
- `ram/wram.asm` defines the mail receive buffer as `wLinkOTMail` through
  `wLinkOTMailEnd`, with `wLinkDataEnd` belonging to the larger raw-link union
  member.
- Current linker symbols put `wLinkDataEnd` ten bytes after `wLinkOTMailEnd`,
  so the old copy length crossed the declared mail-buffer boundary.
- The stale inline comment already stated the intended count:
  `should be wLinkOTMailEnd - wLinkOTMail`.

Why this is a bug:

The routine is a mail-buffer compaction pass, not a raw-link-data copy. Using
the larger union member's end label makes the copy read and write beyond the
declared mail receive buffer. Today those extra bytes are padding, which lowers
the observed damage, but the code violates the buffer contract and would become
fragile if the overlaid WRAM layout changes.

Fix applied:

- The compaction copy now uses `wLinkOTMailEnd - wLinkOTMail`.
- `tools/audit/check_release_smoke.py` now checks the receive-side trade-mail
  copy length.

Residual proof gap:

No real link trade/mail exchange was run. The static release smoke guard checks
the corrected copy bound, and a ROM rebuild was run after the fix.

### BUG-2026-04-26-011 - P3 - Wild Magikarp size filters compare feet/inches as millimeters

Status: `RESOLVED_THIS_SESSION`

Surface: wild Magikarp length generation in `LoadEnemyMon`.

Original evidence:

- `engine/events/magikarp.asm` says `CalcMagikarpLength` returns the length in
  feet and inches at `wMagikarpLength`.
- `engine/battle/core.asm` then filters wild Magikarp size after calling
  `CalcMagikarpLength`.
- Before this fix, the very-large filters compared the feet byte to
  `HIGH(1536)` and the inches byte to `LOW(1616)` / `LOW(1600)`. Those are
  byte splits of old millimeter thresholds, not feet/inches thresholds.
- The same routine skipped the Lake of Rage minimum-size floor when the player
  was actually on the Lake of Rage map, because the map-group and map-number
  tests branched on equality instead of inequality.

Why this is a bug:

The comments and helper contract agree that `wMagikarpLength` is no longer a
two-byte millimeter value. The old byte comparisons made the rare large-size
filters miss the intended 5-foot Magikarp range, and the inverted Lake of Rage
tests prevented the intended local minimum-size behavior on the actual Lake of
Rage map.

Fix applied:

- The large-size filters now operate on feet/inches directly: only 5-foot
  Magikarp enter the rare-size checks, with retry thresholds at 5'4" and 5'3".
- The Lake of Rage map gate now skips the minimum-size floor outside Lake of
  Rage and applies it on Lake of Rage.
- The minimum-size floor now retries Magikarp below about 3'4" by checking
  `feet < 3` or `feet == 3 && inches < 4`.
- The stale explanatory comments in `engine/battle/core.asm` were replaced with
  current feet/inches comments.
- `tools/audit/check_release_smoke.py` now checks the corrected Magikarp gate
  shapes.

Residual proof gap:

No emulator encounter-distribution test was run. The static release smoke guard
checks the corrected thresholds and Lake of Rage branch direction, and a ROM
rebuild was run after the fix.

## Resolved Documentation Drift

### BUG-2026-04-26-003 - P3 - Read docs still described Morty live proof as blocked or untouched

Status: `RESOLVED_THIS_SESSION`

Surface:

- `docs/boss_ai_bug_testing_plan.md`
- `docs/project_roadmap.md`
- `docs/agent_navigation/subsystems/boss_ai_trace.md`
- `audit/boss_ai_trace/live_capture_ledger.md`

Evidence:

At the time this doc-drift bug was labeled, the live-capture ledger and
manifest accepted Morty as `FINISHED` with `audit/boss_ai_trace/morty_live.txt`,
but several read docs still said boss-position captures were `UNTOUCHED` or
that the Morty proof capsule was blocked.

Doc fix applied:

Those docs were corrected at the time, but the later trace ROM rebuild exposed
that the accepted Morty proof was stale. `BUG-2026-04-26-012` is the current
truth-preserving fix for that follow-up drift.

### BUG-2026-04-26-012 - P2 - Live-capture tooling and docs accepted stale Morty proof

Status: `RESOLVED_THIS_SESSION`

Surface:

- `tools/trace/boss_ai_trace_capture.py`
- `audit/boss_ai_trace/live_capture_manifest.json`
- `audit/boss_ai_trace/live_capture_ledger.md`
- `audit/boss_ai_trace/morty_live.txt`
- `audit/boss_ai_trace/morty_state_needed_2026-04-26.md`
- `docs/project_roadmap.md`
- `docs/boss_ai_bug_testing_plan.md`
- `docs/boss_ai_trace_capture.md`
- `docs/agent_navigation/subsystems/boss_ai_trace.md`

Evidence:

- `python tools\audit\check_boss_ai_live_capture_ledger.py` failed because
  `audit/boss_ai_trace/live_capture_manifest.json` pinned old trace ROM and
  symbol hashes while the current `pokegold_trace.gbc` and
  `pokegold_trace.sym` hashes had changed.
- A regeneration attempt against the current trace ROM wrote
  `no_captures=true` to `audit/boss_ai_trace/morty_live.txt` even with
  `--require-chosen-move`, and still exited successfully.
- The strict Morty state preflight still passed, so the state is useful, but
  it is not current completed move-decision proof.

Fix applied:

- The capture helper now exits nonzero when `--require-chosen-move` watches
  zero completed move-decision captures.
- The manifest now pins the current trace ROM/symbol hashes and marks Morty
  `IN PROGRESS` instead of `FINISHED`.
- The live ledger, Morty state note, roadmap, Boss AI trace docs, and trace
  micro-index now say Morty needs a fresh current-ROM completed chosen-move
  capture before it can be promoted back to `FINISHED`.

Residual proof gap:

No new completed Morty move-decision trace was captured in this fix. Current
proof is limited to strict state preflight and the audit-confirmed ledger
status.

### BUG-2026-04-26-013 - P3 - Morty proof navigation still named the old blocker

Status: `RESOLVED_THIS_SESSION`

Surface:

- `docs/agent_navigation/navigation_health_check.md`
- `audit/boss_ai_trace/morty_state_needed_2026-04-26.md`

Evidence:

- The navigation smoke route for "is Morty boss AI proven?" still used the
  older blocker framing: no current boss-position state.
- The current manifest now has a Morty candidate state that passes strict
  preflight, so the blocker is narrower: no current trace-ROM completed
  chosen-move capture.
- The Morty state note still used "accepted" language for the frame-161
  plan-only breadcrumb and for the current candidate state.

Fix applied:

- The navigation route now points to the live ledger, manifest, and Morty state
  note, and answers that strict preflight passes but current proof still needs
  a completed chosen-move capture.
- The Morty state note now calls the frame-161 state a plan-only first nonzero
  trace and the completed-state path a current candidate artifact, not accepted
  proof.

Residual proof gap:

Same as `BUG-2026-04-26-012`: no completed current-ROM chosen-move capture has
been produced yet.

### BUG-2026-04-26-014 - P3 - Generated dev index carried stale Boss AI anchors

Status: `RESOLVED_THIS_SESSION`

Surface:

- `docs/generated/dev_index.md`

Evidence:

- `python tools\audit\check_docs_navigation.py` failed because
  `docs/generated/dev_index.md` did not match current linker/source anchors.
- The mismatch was concentrated in Boss AI label source-line anchors, so a
  helper following the generated index could land on stale line references.

Fix applied:

- Regenerated `docs/generated/dev_index.md` through
  `python scripts\generate_dev_index.py --rom pokegold`.

Residual proof gap:

None for the generated index. `check_docs_navigation.py` passes after the
refresh.

### BUG-2026-04-26-015 - P2 - Live-capture manifest pinned stale trace ROM hashes

Status: `RESOLVED_THIS_SESSION`

Surface:

- `audit/boss_ai_trace/live_capture_manifest.json`
- `audit/boss_ai_trace/morty_live.txt`

Evidence:

- `python tools\audit\check_boss_ai_live_capture_ledger.py` failed because the
  manifest expected trace ROM hash
  `2FFE741FEA716E7B5DB816CDCA2BE851BE4B9F372E55D158014DF8AD470027C1`, but the
  current `pokegold_trace.gbc` hash is
  `895E79859D78293343F028D2DDB5858DC127C01BB7D55D439B219FF6CF45C8E3`.
- `pokegold_trace.sym` likewise changed from the manifest's
  `A7EA5F02F237EBC68AC400E7EDBF68E7F7EC650B88AE2CE70BB1357F9EBE3509` to
  `72A3E42C7E15980B278966E3C08922E5E60FA088FB13FFBD536F94CE43BCE8ED`.

Fix applied:

- Refreshed the manifest trace ROM and symbol hashes to match the current files
  on disk.
- Later Morty proof work refreshed them again to the current accepted trace
  basis:
  `trace_rom_sha256=639680604270248FEC0FF9DDD92205C75FC2B01858FD1A365FBF51623DC66C29`
  and
  `trace_symbols_sha256=73A70E9C9ADB65840DBD05C9B9049BFF288AF0D2C1EFA22DE375CA773CCE777B`.

Residual proof gap:

None for Morty's first proof capsule. `audit/boss_ai_trace/morty_live.txt` now
has current matching hashes and nonzero `chosen_id=95`. Other boss-position
live captures remain open.

### BUG-2026-04-26-016 - P3 - Docs navigation audit can crash during Windows temp directory cleanup

Status: `RESOLVED_THIS_SESSION`

Surface:

- `tools/audit/check_docs_navigation.py`

Evidence:

- `python tools\audit\check_docs_navigation.py` completed its early checks, then
  crashed while deleting `.local\tmp\tmp9y0nijub` with
  `PermissionError: [WinError 5] Access is denied`.
- The generated-file freshness check only needs one disposable markdown output,
  but it used `tempfile.TemporaryDirectory`, so a cleanup failure could turn a
  successful comparison path into an audit crash.

Fix applied:

- Changed generated-file comparisons to use a single temporary output file in
  `.local\tmp`.
- Cleanup now unlinks that file and ignores cleanup-only `OSError`, so stale
  source/generated diffs still fail the audit while Windows temp cleanup does
  not mask the real result.

Residual proof gap:

None for the audit crash once `check_docs_navigation.py` passes.

## Verification Performed

Earlier full recheck recorded before the current held-item helper/audit drift
was noticed:

```powershell
python tools\audit\check_release_smoke.py
python tools\audit\check_ai_tiers.py
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_battle_math_safety.py
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_docs_navigation.py
python tools\audit\check_boss_items_present.py
python tools\audit\check_boss_moves_complete.py
python tools\audit\check_boss_ai_live_capture_ledger.py
git diff --check
bash -lc 'make -q RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'
```

Result:

- All listed audits passed.
- `make -q` reported `pokegold.gbc` and `pokesilver.gbc` up to date without
  rebuilding.
- `git diff --check` reported only the existing CRLF warning for
  `docs/generated/balance_audit.md`.
- This earlier green `check_boss_ai_trace_invariants.py` result was part of
  `BUG-2026-04-26-002`'s original evidence. Later current-source recheck below
  shows the audit now has helper-aware held-item checks.

Additional focused recheck after adding `BUG-2026-04-26-005`:

```powershell
python tools\audit\check_docs_navigation.py
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_boss_items_present.py
python tools\audit\check_boss_moves_complete.py
git diff --check
```

Result:

- The four Python audits passed.
- `git diff --check` again reported only the existing CRLF warning for
  `docs/generated/balance_audit.md`.

Latest focused recheck after marking `BUG-2026-04-26-001` and
`BUG-2026-04-26-002` resolved in current source:

```powershell
rg -n "ld a, \[wEnemyMonItem\]|cp HELD_" engine\battle\ai\boss.asm
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_docs_navigation.py
python scripts\generate_dev_index.py --rom pokegold
python tools\audit\check_docs_navigation.py
python tools\audit\check_boss_items_present.py
python tools\audit\check_boss_moves_complete.py
git diff --check
```

Result:

- The raw `wEnemyMonItem` read now appears only inside
  `BossAI_GetEnemyHeldEffect`; held-effect comparisons happen after helper
  calls.
- The first docs-navigation recheck found stale Boss AI line anchors in
  `docs/generated/dev_index.md`; regenerating with
  `python scripts\generate_dev_index.py --rom pokegold` updated the generated
  doc, and the rerun passed.
- The Boss AI trace invariant, boss item, and boss move audits passed.
- `git diff --check` again reported only the existing CRLF warning for
  `docs/generated/balance_audit.md`.

Latest fix verification after resolving `BUG-2026-04-26-004` and
`BUG-2026-04-26-005`, then extending the same state-restore fix family for
`BUG-2026-04-26-006` and `BUG-2026-04-26-007`:

```powershell
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_docs_navigation.py
python tools\audit\check_boss_items_present.py
python tools\audit\check_boss_moves_complete.py
git diff --check
bash -lc 'make -B -j4 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'
python scripts\generate_dev_index.py --rom pokegold
python tools\audit\check_docs_navigation.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_boss_ai_trace_invariants.py
git diff --check
```

Result:

- Boss AI trace invariants passed, including the new plausible-threat
  base-data restoration check, switch-candidate base-data restoration check,
  legacy switch base-data restoration check, and Baton Pass living-bench gate.
- Boss AI no-cheat, gating, memory-budget, docs-navigation, boss-item, and
  boss-move audits passed.
- `pokegold.gbc` and `pokesilver.gbc` rebuilt successfully through the repo-local
  RGBDS tools. `make -B` was used because a normal `make` reported both ROMs
  up to date after source edits, which was not strong enough proof.
- The rebuild shifted Boss AI linker anchors, so `docs/generated/dev_index.md`
  was regenerated and docs-navigation passed after regeneration.
- `git diff --check` reported only the existing CRLF warning for
  `docs/generated/balance_audit.md`.

Latest focused recheck after resolving `BUG-2026-04-26-008` and
`BUG-2026-04-26-009`, then the same verification lane after
`BUG-2026-04-26-010` and `BUG-2026-04-26-011`:

```powershell
python tools\audit\check_release_smoke.py
python tools\audit\check_docs_navigation.py
git diff --check
bash -lc 'make -B -j4 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'
python scripts\generate_dev_index.py --rom pokegold
python tools\audit\check_docs_navigation.py
python tools\audit\check_release_smoke.py
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_battle_math_safety.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_boss_items_present.py
python tools\audit\check_boss_moves_complete.py
git diff --check
```

Result:

- Release smoke passed, including the new overworld XY compare offset check,
  NPC trade stat recompute level check, and link trade mail receive bounds
  check, and wild Magikarp size gate checks.
- Docs navigation passed before and after regenerating `docs/generated/dev_index.md`.
- Boss AI trace invariants, battle math safety, Boss AI memory budget, boss
  item, and boss move audits passed after the rebuild.
- `pokegold.gbc` and `pokesilver.gbc` rebuilt successfully through the
  repo-local RGBDS tools.
- `git diff --check` reported only the existing CRLF warning for
  `docs/generated/balance_audit.md`.

Latest focused recheck after resolving `BUG-2026-04-26-012`,
`BUG-2026-04-26-013`, and `BUG-2026-04-26-014`:

```powershell
python tools\audit\check_boss_ai_live_capture_ledger.py
python tools\audit\check_docs_navigation.py
python tools\trace\boss_ai_trace_batch.py --only morty
python tools\trace\boss_ai_trace_capture.py --save-state .local\tmp\morty_issue_cycle4\a_taps_completed_trace_delta_263.state --watch-frames 5 --poll-every 1 --require-chosen-move --boss Morty --notes "expected failure check" --out .local\tmp\morty_require_chosen_should_not_write.txt
python -m py_compile tools\trace\boss_ai_trace_capture.py tools\trace\boss_ai_trace_batch.py tools\audit\check_boss_ai_live_capture_ledger.py
python tools\audit\check_release_smoke.py
python scripts\generate_dev_index.py --rom pokegold
python tools\audit\check_docs_navigation.py
python tools\audit\check_ai_tiers.py
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_boss_items_present.py
python tools\audit\check_boss_moves_complete.py
python tools\audit\check_battle_math_safety.py
python tools\audit\check_release_smoke.py
git diff --check
```

Result:

- This focused recheck is superseded by the later cycle8 Morty proof. The final
  live-capture ledger audit passes with Morty `FINISHED`.
- Docs navigation passed against the current manifest hash and revised trace
  status docs.
- Batch dry-run reports Morty `READY` from the preflighted state, but does not
  execute the capture without `--execute`.
- The direct `--require-chosen-move` capture test exited nonzero and did not
  write the requested output file, proving the tool no longer records this
  failure as success.
- `docs/generated/dev_index.md` was regenerated after docs navigation caught
  stale Boss AI source-line anchors, and docs navigation passed after the
  refresh.
- Python syntax compilation, AI tiers, Boss AI no-cheat, Boss AI gating, Boss
  AI trace invariants, Boss AI memory budget, boss item, boss move, battle math,
  and release smoke audits passed.
- `git diff --check` reported only the existing CRLF warning for
  `docs/generated/balance_audit.md`.

Latest focused recheck after resolving `BUG-2026-04-26-015` and
`BUG-2026-04-26-016`:

```powershell
python -m py_compile tools\audit\check_docs_navigation.py tools\audit\check_boss_ai_live_capture_ledger.py
python tools\audit\check_docs_navigation.py
python tools\audit\check_boss_ai_live_capture_ledger.py
python tools\trace\boss_ai_trace_batch.py --only morty
python tools\audit\check_release_smoke.py
python tools\audit\check_ai_tiers.py
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_boss_items_present.py
python tools\audit\check_boss_moves_complete.py
python tools\audit\check_battle_math_safety.py
git diff --check
bash -lc 'make -q RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'
```

Result:

- Python syntax compilation passed for the edited docs-navigation audit and live
  ledger audit.
- Docs navigation passed, including generated-index freshness, generated
  balance-audit freshness, and trace-manifest doc sync against the refreshed
  trace ROM hash.
- Live-capture ledger audit passed with Morty still `IN PROGRESS`.
- Morty batch dry-run reported `READY` when allowed to read the local PyBoy
  dependency folders outside the sandbox; it did not execute or write a live
  capture.
- Release smoke, AI tiers, Boss AI no-cheat, Boss AI gating, Boss AI trace
  invariants, Boss AI memory budget, boss item, boss move, and battle math
  audits passed.
- `git diff --check` reported only the existing CRLF warning for
  `docs/generated/balance_audit.md`.
- WSL `make -q` reported `pokegold.gbc` and `pokesilver.gbc` up to date.

Passed in earlier verification bundle:

```powershell
python tools\audit\check_release_smoke.py
python tools\audit\check_ai_tiers.py
python tools\audit\check_boss_items_present.py
python tools\audit\check_boss_moves_complete.py
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_boss_ai_live_capture_ledger.py
python tools\audit\check_battle_math_safety.py
python tools\trace\boss_ai_trace_batch.py --only morty
python tools\trace\boss_ai_trace_capture.py --symbols-only
```

Generated mirror checks:

```powershell
python scripts\generate_balance_audit.py --out .local\out\balance_audit_check.md
python scripts\generate_dev_index.py --rom pokegold --out .local\out\dev_index_check.md
git diff --no-index -- docs\generated\balance_audit.md .local\out\balance_audit_check.md
git diff --no-index -- docs\generated\dev_index.md .local\out\dev_index_check.md
```

Result:

- `docs/generated/dev_index.md` matched the temp generated copy.
- `docs/generated/balance_audit.md` differed only in the `Generated:` timestamp.

## Checks Not Run

- No emulator/manual gameplay validation was run.
- `python scripts\generate_balance_audit.py` was not run against the tracked
  output path.

## Rejected Leads

### Boss AI `cp SPECIAL` checks against move type bytes

Status: `NOT_A_BUG`

Evidence:

- `constants/type_constants.asm` defines `SPECIAL` as the boundary before
  `FIRE`, `WATER`, `GRASS`, `ELECTRIC`, `PSYCHIC_TYPE`, `ICE`, `DRAGON`, and
  `DARK`.
- Battle code already uses this pattern when deriving physical/special category
  from move type, for example in `engine/battle/late_gen_held_items.asm` and
  `engine/battle/type_passive_damage_mods.asm`.

Why it was rejected:

The suspicious Boss AI comparison around
`engine/battle/ai/boss.asm:4839` looks like a type/category mix-up at first
glance, but in this codebase type constants encode the Gen 2 physical/special
split. The surrounding held-item enum conversion problem is still real; this
specific `cp SPECIAL` idiom is not.

### Poison retaliation AI missing `HELD_PREVENT_POISON`

Status: `NOT_LABELED_CURRENTLY`

Evidence:

- The actual poison retaliation mechanic checks the attacking user's held
  effect against `HELD_PREVENT_POISON` in
  `engine/battle/type_passive_damage_mods.asm:1158` to
  `engine/battle/type_passive_damage_mods.asm:1161`.
- The Boss AI poison-contact risk helper at
  `engine/battle/ai/boss.asm:1068` to `engine/battle/ai/boss.asm:1089` checks
  enemy status, Poison/Steel typing, and Safeguard, but not
  `HELD_PREVENT_POISON`.
- Current item data did not show any `item_attribute` row assigning
  `HELD_PREVENT_POISON`; `PSNCUREBERRY` uses `HELD_HEAL_POISON`, and
  `POISON_BARB` uses `HELD_POISON_BOOST`.

Why it was not labeled:

This is a real model/mechanic mismatch only if an actual held item can produce
`HELD_PREVENT_POISON`. In the current item table, the held effect appears to be
available in the enum and battle command support, but not assigned to an item.
If a future rebalance assigns that held effect, the Boss AI poison-contact risk
helper should be updated at the same time.

### Weather and Curse setup classifiers are split across local and global helpers

Status: `NEEDS_DESIGN_DECISION_NOT_LABELED`

Evidence:

- The local move-scoring helper `.IsSetupMove` treats `EFFECT_RAIN_DANCE`,
  `EFFECT_SUNNY_DAY`, and non-Ghost `EFFECT_CURSE` as setup moves at
  `engine/battle/ai/boss.asm:1476` to `engine/battle/ai/boss.asm:1507`.
- The global `BossAI_IsSetupEffect` helper at
  `engine/battle/ai/boss.asm:3500` to `engine/battle/ai/boss.asm:3520` only
  treats Dragon Dance, Calm Mind, Quiver Dance, and stat-up effects as setup.
- The global helper feeds role selection and projection/plan scoring at
  `engine/battle/ai/boss.asm:3456`, `engine/battle/ai/boss.asm:4094`,
  `engine/battle/ai/boss.asm:4409`, `engine/battle/ai/boss.asm:4490`, and
  `engine/battle/ai/boss.asm:4554`.

Why it was not labeled:

The split is suspicious, but it may be intentional: weather has dedicated move
checks and role-effect entries, and Curse is type-dependent. Labeling this as a
bug needs a design decision about whether weather/Curse should participate in
the same setup-sweep planning as stat boosters.

### Boss AI trace invariant audit still requires the old direct choice-lock shape

Status: `NOT_A_CURRENT_BUG`

Evidence:

- Current `.HeldItemMoveBlocked` calls `BossAI_EnemyChoiceLockedMove`.
- Current `tools/audit/check_boss_ai_trace_invariants.py` requires that helper
  call in the local held-item legality block, then checks
  `wEnemyChoiceLockedMove`, `BossAI_GetEnemyHeldEffect`, and
  `BossAI_IsChoiceHeldEffect` inside `BossAI_EnemyChoiceLockedMove`.
- `python tools\audit\check_boss_ai_trace_invariants.py` passes on the current
  checkout.

Why it was rejected:

The stale-audit-shape concern is already resolved in the current dirty
checkout. There is no current open audit bug in this lane; the history is
covered by now-resolved `BUG-2026-04-26-002` and should stay closed unless the
helper-aware checks regress.

### `MOVE_DESC_NAME_BROKEN` wrong-bank name-table entry

Status: `DEAD_FENCED_OFF_NOT_FIXED`

Evidence:

- `constants/text_constants.asm` deliberately names the enum
  `MOVE_DESC_NAME_BROKEN`.
- `home/names.asm` keeps the matching `NamesPointers` row with the inline
  `wrong bank` warning.
- Current source has no live caller that sets `wNamedObjectType` to
  `MOVE_DESC_NAME_BROKEN`.
- Current move-description printing uses
  `engine/pokemon/print_move_description.asm`, which directly reads
  `MoveDescriptions` with `BANK(MoveDescriptions)` and calls
  `PlaceFarString`.

Why it was not fixed:

This is a quarantined broken generic-name-table route, not a current caller
bug. Fixing it would mean changing dead compatibility scaffolding in the home
name system without a live behavior win. If a future feature wants to fetch move
descriptions through `GetName`, it should replace the deliberately broken enum
with a real, tested API instead of reviving this table row casually.

### Original Gold/Silver bug list

Status: `RECHECKED_ALL_FIXED_CURRENT_SOURCE`

Evidence:

- `docs/bugs_and_glitches.md` lists seven original Gold/Silver bugs with
  Crystal-style fixes.
- Current source already uses `text_end` in `_CoinCaseCountText`.
- `engine/events/halloffame.asm` already erases previous save data before Hall
  of Fame writes when `wSavedAtLeastOnce` is false.
- `engine/events/lucky_number.asm` already scans through `NUM_BOXES`, not
  `NUM_BOXES_JP`.
- `data/text/battle.asm` already uses the shorter Present failure text.
- `engine/overworld/events.asm` already blocks Surf when
  `CheckFacingObject` finds a facing object.
- `data/maps/maps.asm` already sets `CeruleanGym` to `FISHGROUP_NONE`.
- `maps/Route15.asm` already capitalizes the sign text as `ROUTE 15`.

Why it was not labeled:

These are real bugs in the original game, but they are not open bugs in this
checkout. Keep `docs/bugs_and_glitches.md` as historical fix documentation, not
as an implied current bug list.
