# Boss AI Lessons Full Roadmap Plan - 2026-05-14

Status: implementation roadmap. The current worktree now implements the
zero-WRAM public-info patches from this roadmap plus a quarantined
Morty/Gengar Haki prototype; the document remains the design ledger rather
than the source of truth for ROM behavior.

This document answers the broader "all of it" request. The existing
`docs/boss_ai_lessons_implementation_plan_2026-05-14.md` was implementation
quality for the revealed Rapid Spin / Spikes patch only. That patch is now
treated as shipped and guarded by regression tests. The rest of the source
brief needed a real implementation plan before a goal for full implementation
would be honest.

Source brief:
`docs/pokemon_mastery/external_research_returns/codex_pokemon_gold_boss_ai_prompt.md`

Primary design rule:
ordinary boss AI must not cheat. It may use public or boss-owned information.
The only approved exceptions are the existing speed-comparison exception and a
future explicitly quarantined Haki/oracle branch.

## Current Objective

Create an implementation-ready roadmap for all remaining boss-AI lessons after
the shipped revealed-spinner Spikes patch. Success means every remaining item
has:

- scope and ordering;
- source targets;
- public-information legality;
- estimated memory/code risk;
- fixture and validation requirements;
- rollback notes;
- explicit handling of `AICompareSpeed` and Haki/oracle exceptions.

This plan does not authorize implementing all items in one patch. The safe
implementation model is one small heuristic per coding pass, with fixtures and
audits proving each change before moving on.

Current implementation note:
Patches 1-6 are implemented in source. Patch 7 is implemented as a conservative
near-tie selector tune, not a broad top-three bucket. Patch 8 is implemented
through expanded existing role-bias personality tables. Patch 9 is satisfied by
the existing public switch-count tendency signal rather than a new WRAM
counter. Patch 10 is implemented only for Morty's Gengar, with Haki flags packed
into `wBossAIRevealedMovesBitmapSpare` byte 1 and trace risk bit 3 marking the
oracle fire. Full all-leader Haki remains intentionally gated because the
current post-input hook is after move-order calculation.

## Files Inspected

Core plan and strategy brief:

- `docs/boss_ai_lessons_implementation_plan_2026-05-14.md`
- `docs/pokemon_mastery/external_research_returns/codex_pokemon_gold_boss_ai_prompt.md`
- `docs/boss_ai_post_patch_notes.md`
- `docs/agent_navigation/subsystems/boss_ai_logic.md`
- `engine/battle/ai/POLICY_DESIGN.md`
- `engine/battle/ai/PLATFORM_API.md`

Core ROM source:

- `engine/battle/ai/boss_policy_move.asm`
- `engine/battle/ai/boss_policy_switch.asm`
- `engine/battle/ai/boss_platform.asm`
- `engine/battle/ai/boss_trace_topmoves.asm`
- `engine/battle/ai/move.asm`
- `engine/battle/ai/scoring.asm`
- `data/trainers/ai_tiers.asm`
- `ram/wram.asm`

Validation and labels:

- `tools/audit/check_boss_ai_no_cheat.py`
- `tools/audit/check_boss_ai_gating.py`
- `tools/audit/check_boss_ai_trace_invariants.py`
- `tools/audit/check_boss_ai_memory_budget.py`
- `tools/audit/check_boss_ai_index_lines.py`
- `tools/audit/check_boss_ai_policy_contract.py`
- `tools/audit/check_boss_ai_selector_replay.py`
- `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`
- `tools/boss_ai_preference/labels/boss_ai_pairwise_preferences.jsonl`
- `tools/boss_ai_preference/labels/boss_ai_trajectory_preferences.jsonl`
- `tools/boss_ai_debugger/*`

Independent subagent reviews were used for:

- source-hook and byte-risk mapping;
- fixture, no-cheat, and trace-proof requirements.

## Relevant Existing AI Flow

The repo is a Pokemon Gold-based hack with custom Gym Leader Lab boss AI.
`engine/battle/ai/move.asm` dispatches boss move scoring through
`BossAI_ApplyMoveModel` and selection through `BossAI_SelectMove` when
`wBossAITier` is nonzero.

Lower move score is better. Illegal or unusable moves are excluded through high
scores before the boss selector scans candidates.

`BossAI_ApplyMoveModel` in `engine/battle/ai/boss_policy_move.asm` already
does the main scoring pass. It computes the public plausible player threat
mask, scores each enemy move, then applies local biases for KO pressure,
deny-KO, tempo, setup pressure, public utility/status failures, Spikes, phaze,
Rapid Spin, Baton Pass, role bias, plan bias, contact/recoil risks, Destiny
Bond, Counter/Mirror Coat, Protect, recovery denial, Encore, selfdestruct,
sleep preemption, scout/repeat, and risky effects.

`BossAI_SelectMove` applies lookahead, traces top moves under `BOSS_AI_TRACE`,
then chooses between the best and second-best legal moves with weighted odds
based on score gap. This means broad good-bucket logic already exists in a
limited form; top-three expansion should wait until hard gates are clean.

Switching lives in `engine/battle/ai/boss_policy_switch.asm`. It computes
switch confidence, candidate risk, public revenge risk, loop/cooldown pressure,
plan switch bias, and sack-vs-switch decisions. It must not read current-turn
player input.

Public player move memory exists in two forms:

- `wPlayerUsedMoves` for the active player Pokemon;
- `wBossAISpeciesUsedMoves` as a per-seen-species mirror.

Plausible threat masks live in:

- `wBossAIPlausibleTypeMaskCache`;
- `wBossAILikelyTypeMaskCache`.

Trace state already records top moves/scores, chosen move, switch confidence,
plan state, plausible masks, risk flags, and lookahead bonuses.

## Memory / Bank / Space Notes

Prefer zero new WRAM for the next several patches.

Known constraints from current docs and map audits:

- WRAMX is globally tight.
- The boss AI reserve is 140 bytes.
- Existing normal boss state uses most of that reserve.
- Trace builds have less headroom than normal builds.
- `wBossAITraceRiskFlags` exists and can carry extra trace bits if unused bits
  remain, but adding new trace bytes should be avoided.

Implementation planning must record before/after map deltas for every behavior
patch. Any item that wants persistent state must first prove the exact byte
allocation, clear path, trace path, and memory-budget audit result.

## Global No-Cheat Boundary

Ordinary scoring and switching may read:

- boss-owned team, moves, items, HP, status, boosts, and plan fields;
- active player species, visible HP/status/boosts, type, and public volatile
  state;
- revealed player moves;
- seen player species;
- public faint/send-out and switch history;
- public hazard state;
- public learnset priors only through the existing plausible/likely mask
  design.

Ordinary scoring and switching may not read:

- unrevealed player reserves;
- unrevealed player moves;
- hidden PP;
- hidden held items;
- private reserve HP/status;
- current-turn player input;
- exact private damage, speed, or item helpers unless explicitly documented.

Approved exact-speed exception:
`BossAI_SetupBoostHasFurtherValue` may continue to `farcall AICompareSpeed`
when deciding whether additional Speed setup still has value. This exception
must not be expanded into general exact-speed or exact-damage reasoning.

Approved Haki/oracle exception:
Haki/oracle is not ordinary AI. If implemented later, it must live in a
quarantined post-input branch, be limited to named late/major bosses, fire at
most once per battle, fire only on the ace's first active turn, be traceable,
and never expose a helper callable from normal move scoring or switching.

## Shipped Baseline To Preserve

The revealed Rapid Spin / Spikes patch is shipped. Permanent regression guards:

- `janine_qwilfish_finish_third_spikes_layer`:
  no Rapid Spin revealed, third layer remains favored.
- `janine_qwilfish_revealed_spinner_hazard_retention`:
  active revealed spinner suppresses extra stacking.
- `janine_qwilfish_unrevealed_spinner_no_suppression`:
  spinner-capable species without revealed Spin does not suppress Spikes.
- `janine_qwilfish_spikes_already_maxed`:
  fourth Spikes click remains bad.

Do not reopen this as the whole roadmap. It is one completed patch.

## Implementation Order

0. Validation floor repair and baseline snapshot.
1. Four-move saturation of plausible threats.
2. Anti-dead-setup tightening.
3. Status hard-answer discipline.
4. Recovery timing discipline.
5. Cash-out / Explosion route discipline.
6. Preservation switch refinement.
7. Good-bucket selector tuning.
8. Boss personality weighting.
9. Tiny public tendency counter.
10. Haki/oracle quarantine.

Reasoning:

- Items 1-6 improve bad action filtering and route quality.
- Selector/personality work should come after bad actions are filtered out.
- Persistent tendency state is later because memory and trace risk are higher.
- Haki/oracle is last and separate because it is intentionally unfair.

## Phase 0 - Validation Floor

Before any remaining behavior patch, create a fresh baseline:

```powershell
git status --short --branch
wsl -e bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'
python -m tools.boss_ai_preference validate
python tools\audit\check_boss_ai_preference_regression.py
python -m tools.boss_ai_debugger regress
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_boss_ai_policy_contract.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_boss_ai_index_lines.py
python tools\audit\check_boss_ai_selector_replay.py
python tools\audit\check_release_smoke.py
python tools\audit\check_docs_navigation.py
```

If map/symbol outputs changed, regenerate navigation indexes before trusting
memory and index checks:

```powershell
python scripts\generate_dev_index.py
python scripts\generate_boss_ai_index.py
python tools\audit\check_boss_ai_index_lines.py
python tools\audit\check_boss_ai_memory_budget.py
```

Trace ledger validation is required only when trace artifacts are refreshed:

```powershell
python tools\trace\boss_ai_trace_batch.py
python tools\audit\check_boss_ai_live_capture_ledger.py
```

## Patch 1 - Four-Move Saturation Of Plausible Threats

Name:
Four-revealed-move plausible mask saturation.

One-sentence purpose:
Once the active player species has publicly revealed four real moves, stop
pricing hidden fifth-move learnset coverage for that active species.

Human battle behavior:
A competent player stops respecting "maybe it has a fifth coverage move" after
the opponent has shown a complete four-move set, while still respecting the
four moves that were actually revealed.

Trigger:
The current active player species has a seen-species slot, its mirrored
`wBossAISpeciesUsedMoves` entry contains four nonzero real moves, and none of
those moves are copied/temporary reveal edge cases from the pre-audit list.

Default:
In `BossAI_ComputePlayerPlausibleTypeMask`, add public STAB and revealed move
types as today, then skip `BossAI_AddSpeciesAndPreEvolutionMovesToMask` for the
active species when the four-move-saturated gate is true. The likely mask keeps
revealed moves and public STAB only.

Exception:
Do not fire if any revealed move can be temporary or copied in the local engine:
Transform, Mimic, Metronome, Sleep Talk, Mirror Move, or any custom move found
by the audit to write a move animation that is not a permanent party move. Do
not fire for fewer than four revealed moves. Do not fire for a previously seen
bench species unless it is now active and its active used-move mirror has been
loaded.

Information legality:
The gate reads only public moves that the active species used earlier in this
battle and the existing public plausible-threat cache. It does not inspect the
player's hidden party moves or reserves.

Memory/code budget:
Estimated ROM: medium, likely one helper plus one branch in
`engine/battle/ai/boss_policy_move.asm` and possibly a tiny public move-effect
deny table. Estimated WRAM/HRAM/SRAM: 0 bytes. Target section: boss move policy
near `BossAI_ComputePlayerPlausibleTypeMask` and revealed-move helpers in
`boss_platform.asm`. Actual bytes: TBD after implementation.

Trace hook:
Use existing `wBossAITracePlausibleMask` to prove the speculative learnset bits
disappear only after four public real moves. If a trace-risk bit remains free,
optionally mark "saturated plausible mask" in `wBossAITraceRiskFlags`.

Failure mode:
The AI may under-respect a legal threat if copied or temporary move mechanics
pollute `wPlayerUsedMoves`. The pre-audit is mandatory.

Tests:
1. Should trigger: fixture where a player active has revealed four permanent
   moves and a learnset-only coverage type would otherwise make the boss avoid a
   good switch or setup line.
2. Should not trigger: same species with only three revealed moves still keeps
   learnset coverage in the plausible mask.
3. Edge/adversarial case: a four-slot reveal containing a copied/temporary move
   does not saturate the mask.

Rollback:
Remove the saturation helper/branch and saturation fixtures. No state migration
is needed because the patch adds no WRAM.

Source targets:
`engine/battle/ai/boss_policy_move.asm`, `engine/battle/ai/boss_platform.asm`,
`tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`,
`tools/boss_ai_preference/labels/boss_ai_pairwise_preferences.jsonl`,
`docs/boss_ai_trace_capture.md` if a trace bit is added.

Implementation gate:
Complete the copied/temporary move audit before coding the branch.

## Patch 2 - Anti-Dead-Setup Tightening

Name:
Public lethal-pressure setup clamp.

One-sentence purpose:
Discourage setup when public state says the boss is likely spending its last
turn boosting instead of converting, unless setup immediately wins or preserves
the route.

Human battle behavior:
A 1300-1500-ish player does not Swords Dance while dying to an obvious active
attack unless the boost immediately flips the position.

Trigger:
The current enemy move is a setup move by `BossAI_IsCurrentEnemySetupMove`; the
boss is at a visible low HP band or already under `EnemyUnderPressure`; and the
active player has public KO or strong deny-KO pressure through revealed moves,
public type pressure, or the existing plausible threat mask.

Default:
Apply a tier-weighted setup discouragement after the existing setup branch and
before later role/plan bias. The clamp should be small enough that explicit
route-conversion logic can override it.

Exception:
Do not fire if `HasKOLine` is true for a non-setup attack but setup is already
part of an active setup-sweep plan with immediate value; if
`BossAI_SetupBoostHasFurtherValue` says the boost still matters and
`BossAI_SetupTurnIsAffordable` says the turn is affordable; or if fixture
evidence shows setup survives the public punish and creates a better next turn.

Information legality:
Uses own HP/status/boosts, active player public threat evidence, and the
existing approved `AICompareSpeed` exception only inside
`BossAI_SetupBoostHasFurtherValue`. It must not call exact private damage
helpers or inspect hidden player moves.

Memory/code budget:
Estimated ROM: low-medium, one local helper under `BossAI_ApplyMoveModel` plus
branches near the setup scoring and lookahead setup projection. Estimated
WRAM/HRAM/SRAM: 0 bytes. Target section: `boss_policy_move.asm`. Actual bytes:
TBD after implementation.

Trace hook:
Existing top-move trace should show setup falling below attack/switch in unsafe
positions. If using `wBossAITraceRiskFlags`, define one bit for public
lethal-pressure setup clamp.

Failure mode:
Over-suppression can remove legitimate last-chance setup lines. The safe setup
mirror fixture must remain green.

Tests:
1. Should trigger: unsafe Bugsy/Scyther-style setup into public Fire or KO
   pressure drops below immediate attack or switch.
2. Should not trigger: `bugsy_scyther_vs_geodude_safe_swords_dance` remains
   setup-favored when public punish is survivable.
3. Edge/adversarial case: low-HP setup that immediately creates a KO or survival
   route is not clamped into a worse move.

Rollback:
Remove the setup clamp helper/branch and its fixtures/labels. No runtime state
is added.

Source targets:
`engine/battle/ai/boss_policy_move.asm`,
`tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`,
`tools/boss_ai_preference/labels/boss_ai_pairwise_preferences.jsonl`,
`tools/boss_ai_preference/labels/boss_ai_trajectory_preferences.jsonl`,
`tools/boss_ai_debugger/tests/*`.

Implementation gate:
Add one unsafe and one safe mirror before source edits so behavior is measured
instead of guessed.

## Patch 3 - Status Hard-Answer Discipline

Name:
Status loses to public hard answer.

One-sentence purpose:
When the boss has a public KO or deny-KO line, discourage slower status that
lets the active player keep its route.

Human battle behavior:
Good players click the concrete answer first when the target is already in
range or must be denied now; they do not throw Toxic or sleep into a position
where immediate damage or phaze wins.

Trigger:
The current enemy move effect is in `BossAIStatusEffects`, it does not fail
publicly, and another legal boss move has public KO pressure or an immediate
deny-KO effect against the active player.

Default:
Apply a small tier-weighted penalty to status after `.StatusMoveWouldFailPublicly`
has passed, unless the status move itself is the public hard answer.

Exception:
Do not fire when status is the best route: faster sleep stopping a sweeper,
Thunder Wave enabling survival, Toxic/Leech Seed beating revealed recovery, or
status pressure that is already encoded as a role or plan bias. Do not infer
absorbers or Sleep Talk from hidden reserves or unrevealed moves.

Information legality:
Reads only visible active state, current enemy moves, known effects, public
fail gates, and existing public KO/deny-KO checks.

Memory/code budget:
Estimated ROM: low, one helper under `BossAI_ApplyMoveModel`. Estimated
WRAM/HRAM/SRAM: 0 bytes. Target section: `boss_policy_move.asm`. Actual bytes:
TBD after implementation.

Trace hook:
Top-move trace should show status dropping below the concrete answer only in
hard-answer fixtures. Optional trace-risk bit: "status hard answer penalty".

Failure mode:
The AI can become too damage-happy and stop using status as a route tool.

Tests:
1. Should trigger: `koga_crobat_vs_alakazam_toxic_or_attack` keeps Wing Attack
   over Toxic while public KO exists.
2. Should not trigger: `jasmine_magneton_vs_quilava_thunder_wave_or_bolt`
   keeps Thunder Wave favored when speed control is the route and Thunderbolt
   does not solve the position.
3. Edge/adversarial case: `chuck_poliwrath_vs_alakazam_hypnosis_or_ice_punch`
   does not status if a clean public Dark pivot exists and status gambles the
   ace into faster Psychic pressure.

Rollback:
Remove the hard-answer penalty helper and fixtures/labels. No state migration.

Source targets:
`engine/battle/ai/boss_policy_move.asm`,
`tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`,
`tools/boss_ai_preference/labels/boss_ai_pairwise_preferences.jsonl`,
`tools/boss_ai_preference/labels/boss_ai_trajectory_preferences.jsonl`.

Implementation gate:
Confirm existing status-fail gates still handle public immunity/status cases;
this patch must cover only "status is legal but strategically slower."

## Patch 4 - Recovery Timing Discipline

Name:
Recovery route-window gate.

One-sentence purpose:
Encourage recovery only when it preserves a real public route piece, and
discourage recovery when attacking or switching is the actual answer.

Human battle behavior:
Competent players recover when the extra HP changes future turns; they do not
heal at full/near-full HP, heal into free setup, or heal when damage wins now.

Trigger:
The current enemy move is a recovery effect in the local recovery set, the boss
is not already at max HP, and public pressure/route state says the extra HP
changes survival, setup, hazard, ace, or cleanup value.

Default:
Keep existing fail gates. Add a small positive bias only inside public recovery
windows, and a small penalty when `HasKOLine` or concrete deny-KO exists and
recovery does not change the immediate route.

Exception:
Do not fire positive recovery at full HP, into obvious public setup/KO pressure,
or when the boss has a direct KO. Do not penalize Rest/recovery that is the only
public way to preserve a wincon under plan logic.

Information legality:
Uses boss HP/status, active player public pressure, revealed recovery denial
state, and plan fields. It must not read hidden player damage rolls, hidden
reserves, or hidden items.

Memory/code budget:
Estimated ROM: low-medium, likely local helper reuse near
`.ApplyRevealedRecoveryDenialBias` and deny-KO scoring. Estimated WRAM/HRAM/SRAM:
0 bytes. Target section: `boss_policy_move.asm`. Actual bytes: TBD after
implementation.

Trace hook:
Top-move trace across HP-band fixtures should show recovery encouraged only in
route-window cases and discouraged when attack wins now.

Failure mode:
Too broad a recovery bonus creates passive boss loops and makes leaders easier
to exploit.

Tests:
1. Should trigger: a recovery-capable boss at a public survival threshold keeps
   a route alive by healing.
2. Should not trigger: `misty_starmie_vs_meganium_recover_or_attack` keeps
   Psychic over Recover when chip/attack enables cleanup and recovery lacks a
   real window.
3. Edge/adversarial case: full-HP Rest/recovery status-fail fixtures remain
   rejected.

Rollback:
Remove recovery timing helper and its fixtures/labels. No runtime state.

Source targets:
`engine/battle/ai/boss_policy_move.asm`,
`tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`,
`tools/boss_ai_preference/labels/boss_ai_pairwise_preferences.jsonl`,
`tools/boss_ai_debugger/tests/*`.

Implementation gate:
Identify local recovery effects from source, not memory, before writing the
helper.

## Patch 5 - Cash-Out / Explosion Route Discipline

Name:
Public route-value self-KO discipline.

One-sentence purpose:
Encourage Explosion/Selfdestruct only when the public trade removes a route
piece or opens a boss route, and discourage low-value chip explosions.

Human battle behavior:
Good GSC players cash out with Explosion when the trade wins position, not
merely because it does damage.

Trigger:
The current enemy move has `EFFECT_SELFDESTRUCT`, the active player is a public
route piece by visible state, seen-species context, setup threat, recovery
threat, or immediate KO pressure, and the boss mon has low future value or the
trade opens a clear next boss action.

Default:
Use existing selfdestruct/protect logic as the floor. Add positive bias for
publicly valuable trades and negative bias for self-KO that only produces
non-decisive chip while the boss mon still has route value.

Exception:
Do not explode into revealed Protect/Detect risk unless a scout/protect plan
explicitly supports it. Do not treat unseen player reserves as "key threats."
Do not punish Explosion when the boss mon is already a low-value sack and the
trade creates a clean next entry.

Information legality:
Reads the active player's visible state, revealed moves, public seen-species
history, boss-owned team state, and existing route/plan fields. It must not
inspect unrevealed reserves or current input.

Memory/code budget:
Estimated ROM: medium, likely helper near `.ApplyRevealedProtectCommitmentRisk`
and `.ApplyRevealedSelfdestructProtectBias`. Estimated WRAM/HRAM/SRAM: 0 bytes.
Target section: `boss_policy_move.asm`. Actual bytes: TBD after implementation.

Trace hook:
Top-move trace should show self-KO score and selected probability moving in
both "boom is correct" and "preserve/pivot is correct" cases. Optional
trace-risk flag: "self-KO route value".

Failure mode:
Bad route-value definitions can make the boss throw important Pokemon away or
refuse correct trades.

Tests:
1. Should trigger: `brock_golem_vs_vaporeon_explosion_question` or
   `pryce_cloyster_vs_quilava_explosion_line` keeps Explosion favored when the
   public trade opens the route.
2. Should not trigger: bad boom into low-value chip falls behind attack or
   switch.
3. Edge/adversarial case: revealed Protect punishes self-KO unless the boss has
   a public reason to scout or punish Protect instead.

Rollback:
Remove self-KO route-value helper and fixtures/labels. No runtime state.

Source targets:
`engine/battle/ai/boss_policy_move.asm`,
`tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`,
`tools/boss_ai_preference/labels/boss_ai_pairwise_preferences.jsonl`,
`tools/boss_ai_preference/labels/boss_ai_trajectory_preferences.jsonl`.

Implementation gate:
Define "public route piece" narrowly before coding: active visible threat,
already seen species, revealed setup/recovery/status route, or immediate active
KO pressure only.

## Patch 6 - Preservation Switch Refinement

Name:
Public preservation switch confidence.

One-sentence purpose:
Improve cases where a useful boss piece should pivot out of public lethal
pressure instead of spending a dead turn.

Human battle behavior:
Competent players preserve a hazard/status/ace piece when a clean public pivot
exists and staying in does not convert.

Trigger:
Switch logic is active; the current boss mon has public future value through
role, plan, hazard/status access, wincon status, or a unique answer; active
player pressure is public and strong; and at least one legal switch candidate
has meaningfully lower public risk.

Default:
Adjust `BossAI_ComputeSwitchConfidence`,
`BossAI_ApplyPlausibleRiskToSwitchConfidence`, or candidate refinement by a
small amount. Prefer confidence/candidate-risk deltas over new state.

Exception:
Do not switch when the current mon has a KO or route-cashout line, when the
candidate creates higher plausible risk, or when cooldown/loop logic indicates
the boss is being farmed. Do not force a pivot that sacrifices tempo for no
public route gain.

Information legality:
Uses boss-owned party state, current active visible threat, revealed moves,
seen species, switch cooldown/loop state, and existing plausible/likely masks.
It must not read hidden player reserves or current input.

Memory/code budget:
Estimated ROM: medium-high because switch policy is dense. Estimated
WRAM/HRAM/SRAM: 0 bytes if implemented as score/confidence deltas. Target
section: `boss_policy_switch.asm`. Actual bytes: TBD after implementation.

Trace hook:
Existing `wBossAITraceSwitchConfidence` and top-move trace must show confidence,
candidate risk, and chosen switch/stay. If trace bits remain, mark
"preservation switch bias."

Failure mode:
Over-preservation creates passive loops and makes bosses waste turns switching.

Tests:
1. Should trigger: `chuck_poliwrath_vs_alakazam_hypnosis_or_ice_punch` keeps
   a clean Umbreon-style public pivot over gambling the ace.
2. Should not trigger: a current mon with public KO/cashout line stays in.
3. Edge/adversarial case: repeated A-B-A switch loops remain penalized by
   cooldown/loop logic.

Rollback:
Remove switch confidence/candidate-risk deltas and fixtures/labels. No runtime
state if the zero-WRAM plan is followed.

Source targets:
`engine/battle/ai/boss_policy_switch.asm`,
`engine/battle/ai/boss_policy_move.asm` only if a shared route-value helper is
needed,
`tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`,
`tools/boss_ai_preference/labels/boss_ai_trajectory_preferences.jsonl`.

Implementation gate:
Patch 5 should land first if preservation depends on the same route-value
vocabulary.

## Patch 7 - Good-Bucket Selector Tuning

Name:
Top-candidate good-bucket selector tuning.

One-sentence purpose:
Improve unpredictability among genuinely good actions without letting bad moves
enter the selector.

Human battle behavior:
Players mix close, defensible lines; they do not randomize into moves that
already failed the position.

Trigger:
After all scoring and lookahead, at least two legal moves are within a tiny
score margin of best and no hard-reject reason applies. Top-three expansion may
be considered only if traces prove third-best moves are often genuinely good.

Default:
First tune the existing best-vs-second odds/margins. Only if measurement shows
the current selector is the bottleneck, expand to a top-three bucket using
existing `BossAI_TraceTopMoves` evidence.

Exception:
Do not widen the bucket if a bad move survives scoring. Do not use personality
or tendency weights to override hard gates. Do not change legal move exclusion.

Information legality:
Reads only already-computed public move scores and boss-owned tier/personality
state. It does not add hidden player reads.

Memory/code budget:
Estimated ROM: low-medium for threshold/odds tuning; medium for top-three
selection. Estimated WRAM/HRAM/SRAM: 0 bytes; use existing trace top-three
state. Target section: `boss_policy_move.asm` and possibly
`boss_trace_topmoves.asm`. Actual bytes: TBD after implementation.

Trace hook:
`BossAI_TraceTopMoves`, `wBossAITraceTopScores`,
`wBossAITraceChosenMove`, and `check_boss_ai_selector_replay.py` are mandatory
proof. Selector replay must remain exact.

Failure mode:
Wider buckets make the AI worse if prior patches did not filter bad status,
setup, recovery, or self-KO actions.

Tests:
1. Should trigger: `third_best_never_selected` or a real fixture where three
   moves are all defensible and close.
2. Should not trigger: a clear best move with score gap remains highly favored.
3. Edge/adversarial case: a move that is close numerically but hard-rejected by
   status/setup/self-KO logic never enters the good bucket.

Rollback:
Restore previous `BossAI_SelectMove` thresholds/branching and remove selector
fixtures. No state migration.

Source targets:
`engine/battle/ai/boss_policy_move.asm`,
`engine/battle/ai/boss_trace_topmoves.asm`,
`tools/audit/check_boss_ai_selector_replay.py`,
`tools/boss_ai_debugger/tests/test_rom_scenarios.py`.

Implementation gate:
Do not implement broad top-three selection until Patches 2-6 are green and a
trace proves the current best-vs-second selector is the actual limitation.

## Patch 8 - Boss Personality Weighting

Name:
Existing-row boss personality weighting.

One-sentence purpose:
Make leaders feel distinct by nudging close decisions through existing tier,
role, and switch-weight hooks.

Human battle behavior:
Different bosses should prefer different good lines: hazards, status/control,
preservation, sacrifice, anti-setup, or ace pressure.

Trigger:
The boss trainer class or tier row has a documented personality, and the move
or switch decision is already close after hard gates.

Default:
Prefer tuning existing `BossAITierWeights`, role-effect tables, class switch
threshold modifiers, and `.ApplyRoleBias` branches. Add new tables only if
existing rows cannot express the behavior.

Exception:
Personality must not override hard gates, no-cheat rules, or public fail
checks. Avoid bespoke per-leader mini-AI unless a leader has a unique mechanic
that already exists in source and fixtures.

Information legality:
Uses boss-owned trainer class, tier, role, and public score context only.

Memory/code budget:
Estimated ROM: low if reusing existing rows and role branches; medium-high if
new tables are added. Estimated WRAM/HRAM/SRAM: 0 bytes. Target sections:
`boss_policy_move.asm`, `boss_policy_switch.asm`, `data/trainers/ai_tiers.asm`.
Actual bytes: TBD after implementation.

Trace hook:
Run the same fixture under two personality rows when possible. Trace should show
small score nudges, not legality changes.

Failure mode:
Over-weighted personality makes bosses ignore the board and click theme moves.

Tests:
1. Should trigger: a hazard/control leader gets a small close-score nudge toward
   hazard/status when both are legal and live.
2. Should not trigger: immediate KO still beats personality preference.
3. Edge/adversarial case: personality cannot resurrect public-failing status,
   dead setup, or bad self-KO.

Rollback:
Revert row/table changes and role-bias branch edits. No state migration.

Source targets:
`engine/battle/ai/boss_policy_move.asm`,
`engine/battle/ai/boss_policy_switch.asm`,
`data/trainers/ai_tiers.asm`,
`tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`.

Implementation gate:
Do after selector and hard-gate behavior is stable enough that personality only
modulates good choices.

## Patch 9 - Tiny Public Tendency Counter

Name:
One-byte public tendency counter.

One-sentence purpose:
Let bosses adapt slightly to one observed public player pattern without reading
hidden intent.

Human battle behavior:
A competent player notices repeated public behavior, such as repeated switches
to the same absorber or repeated low-HP healing, and biases the next close
choice accordingly.

Trigger:
A single selected public behavior has happened enough times in the current
battle to set a 1-bit or 2-bit tendency. Candidate behaviors: repeated switch
to the same seen species, repeated low-HP recovery, or repeated setup on free
turns.

Default:
Pack at most one byte, or reuse documented spare bits only after memory audit.
Update the counter only after public events resolve. Apply only a small
close-score bias or switch-confidence nudge.

Exception:
Do not track inferred intent. Do not update from hidden reserves, current input,
or private menu actions. Do not add a broad history buffer.

Information legality:
Reads only observed public actions after they happen. It predicts no hidden
move, item, reserve state, or current-turn input.

Memory/code budget:
Estimated ROM: medium. Estimated WRAM: high-risk unless packed into documented
reserve. Target state: at most 1 byte or 2-4 bits in the boss AI reserve, with
clear/reset in `ClearBossAIState`. Actual bytes: TBD after memory proof.

Trace hook:
Trace must expose the counter value, update event, and decay/reset behavior.
If no trace byte is available, delay implementation.

Failure mode:
The AI can look like it is reading minds if the counter updates before public
events or if it tracks inferred plans instead of observed actions.

Tests:
1. Should trigger: multi-turn fixture where the player repeatedly uses the same
   public absorber and the boss biases a close punish line.
2. Should not trigger: same board without the repeated public pattern keeps the
   baseline choice.
3. Edge/adversarial case: player hovers or selects a switch but does not execute
   it; no counter update is possible because ordinary AI cannot read input.

Rollback:
Remove the counter field/bits, clear code, update code, trace docs, fixtures,
and memory docs. Rerun memory budget and no-cheat audits.

Source targets:
`ram/wram.asm`, `engine/battle/ai/boss_platform.asm`,
`engine/battle/ai/boss_policy_move.asm`,
`engine/battle/ai/boss_policy_switch.asm`,
`docs/agent_navigation/subsystems/boss_ai_logic.md`,
`tools/audit/check_boss_ai_memory_budget.py`,
multi-turn fixture and trace tooling.

Implementation gate:
Do not implement until zero-WRAM heuristics above are complete and a fresh
memory-budget audit proves exact room.

## Patch 10 - Haki / Oracle Quarantine

Name:
Quarantined one-shot Haki/oracle branch.

One-sentence purpose:
Allow the user-approved unfair read only inside an isolated, traceable,
one-shot mechanic that cannot leak into ordinary boss AI.

Human battle behavior:
This is not human public-information behavior. It is a deliberate boss gimmick:
a named major boss gets one dramatic read after the player action is already
locked.

Trigger:
Named boss is eligible; active boss mon is the ace; this is the ace's first
active turn; Haki has not been spent this battle; execution is in the approved
post-input window; and trace/audit flags are available.

Default:
Inside the quarantined branch only, inspect the already-locked player action
and choose from a tiny set of allowed responses. Set spent state immediately and
write trace fields. Ordinary scoring helpers must remain unable to call this.

Exception:
Do not fire for ordinary leaders, non-ace mons, later ace turns, pre-input
scoring, switch policy, or any path that cannot trace the activation. Do not use
Haki to justify ordinary exact damage/speed/item reads.

Information legality:
This intentionally violates ordinary public-information rules, but only within
the user-approved exception. The implementation must make that boundary
auditable in source and tooling.

Memory/code budget:
Estimated ROM: high. Estimated WRAM: likely at least one spent flag unless a
documented spare bit is allocated. Target source is not selected yet because
the correct hook must be a post-input action-resolution point, not
`BossAI_ApplyMoveModel`. Actual bytes: TBD after hook audit.

Trace hook:
Dedicated trace evidence is mandatory: eligible, fired, selected response,
spent flag, boss/mon id, and turn. If that cannot be traced, do not implement.

Failure mode:
The feature can silently become a cheating helper for normal scoring. That is
the main failure to prevent.

Tests:
1. Should trigger: named eligible late/major boss ace first active turn fires
   once and writes trace.
2. Should not trigger: same boss on non-ace or second ace turn does not fire.
3. Edge/adversarial case: ordinary scoring path cannot call Haki helper and
   no-cheat audit fails if private reads appear outside the spent branch.

Rollback:
Remove hook, eligibility table, spent state, trace fields, fixtures, and docs.
Rerun no-cheat, gating, trace, memory, and live-capture audits.

Source targets:
TBD after a post-input hook audit. Candidate files to inspect:
`engine/battle/core.asm`, `engine/battle/ai/move.asm`,
`engine/battle/ai/boss_thunks.asm`, `ram/wram.asm`, trace tooling, and no-cheat
audit allowlist. Do not hook this into `BossAI_ApplyMoveModel`.

Implementation gate:
Requires a separate Haki spec naming the first boss, exact hook, exact state
bit, exact trace fields, and explicit no-cheat audit rule before coding.

## Before / After Examples

Four-move saturation:
Before, a boss may keep avoiding a switch because the active player species can
learn a dangerous hidden coverage move even after revealing four ordinary
moves. After, the boss respects the revealed four and stops inventing a fifth
move.

Anti-dead-setup:
Before, a low-HP Scyther can boost into obvious public fire pressure. After, it
attacks, switches, or cashes out unless the boost immediately changes the route.

Status hard-answer:
Before, a Crobat may Toxic an Alakazam that can simply be removed now. After,
the KO takes priority while Thunder Wave or sleep still wins in fixtures where
status is the actual answer.

Recovery timing:
Before, a recovery mon can heal because it is damaged, even when damage wins
now. After, recovery is for route windows, not passive stalling.

Cash-out / Explosion:
Before, Explosion can be treated as generic high damage. After, it is priced as
a route trade: good into a key visible threat, bad as low-value chip.

Preservation switching:
Before, a valuable hazard/status piece may stay in and spend a dead turn under
public lethal pressure. After, it pivots when a clean public candidate exists
and loop logic says switching is not being abused.

Good-bucket tuning:
Before, close positions may be too deterministic or restricted to second-best.
After, only proven good candidates get mixed, and bad actions remain filtered.

Boss personality:
Before, leaders mostly share the same close-score personality. After, leaders
can bias close decisions toward their style without overriding board reality.

Tiny tendency counter:
Before, repeated public player patterns have little persistent effect. After,
one observed pattern can nudge a close future choice if memory budget permits.

Haki/oracle:
Before, ordinary boss AI stays public-only. After, one named boss may use one
traceable unfair read in a quarantined branch, without changing ordinary AI.

## Global Validation Per Patch

Every behavior patch must run:

```powershell
git status --short --branch
wsl -e bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'
python -m tools.boss_ai_preference validate
python tools\audit\check_boss_ai_preference_regression.py
python -m tools.boss_ai_debugger regress
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_boss_ai_policy_contract.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_boss_ai_index_lines.py
python tools\audit\check_release_smoke.py
git diff --check
```

Selector changes must also run:

```powershell
python tools\audit\check_boss_ai_selector_replay.py
```

Docs or generated-index changes must also run:

```powershell
python tools\audit\check_docs_navigation.py
```

Trace-affecting changes must also run:

```powershell
python tools\audit\check_boss_ai_live_capture_ledger.py
```

Known caveat:
trace ledger checks are meaningful only after trace ROM artifacts and
manifest/ledger hashes are refreshed together.

## Rollback Policy

Rollback one patch at a time. Each patch must keep source edits, fixture
labels, trace docs, and generated docs separable enough to revert without
touching unrelated long-running work.

If a patch adds no runtime state, rollback is source plus tests only.

If a patch adds WRAM or trace fields, rollback must also remove clear/reset
code, docs, audit allowlists, and memory-budget references.

No patch may use `git reset --hard` or revert unrelated dirty tree work.

## Completion Checklist

This plan is complete when the following are true:

- Every remaining source-brief candidate after shipped Spikes is represented:
  four-move saturation, anti-dead-setup, status hard-answer, recovery timing,
  cash-out/Explosion, preservation switch, good-bucket tuning, boss
  personality, public tendency counter, and Haki/oracle.
- Each item has the micro-heuristic contract fields requested by the source
  brief.
- Each item names source targets and fixture surfaces.
- Each item states no-cheat legality.
- Each item states memory/code risk and trace proof.
- Each item has trigger, non-trigger, and edge/adversarial tests.
- Each item has rollback notes.
- The allowed `AICompareSpeed` exception is constrained to the existing setup
  helper.
- Haki/oracle is explicitly separate from ordinary scoring and switching.
- Global validation commands are listed.
