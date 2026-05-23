# Debugger Bug-Class Catalog

Status: drafted by Claude (Opus 4.7, 1M context) on 2026-05-22 as the P20
first-slice deliverable per
[docs/debugger_masterpiece_roadmap_codex_task.md](debugger_masterpiece_roadmap_codex_task.md)
§3 P20. Audit-enforced by
[tools/audit/check_debugger_bug_class_catalog.py](../tools/audit/check_debugger_bug_class_catalog.py).

## Purpose

Honest, audit-enforced inventory of the failure classes this codebase has
hit (or instrumented synthetically) and what the unified debugger can and
cannot do about each. Three tiers:

- **AUTO** — the P19 auto-watcher catches this class without prompting.
  The detector module + lived-smoke test + audit are named.
- **QUERY** — locatable in ≤2 commands by an LLM driving the masterpiece
  debugger primitives. The canonical command pair is named.
- **JUDGMENT** — requires human (Cole's) gameplay-design call. The
  escalation path is named.

Schema (audit-enforced): each entry is a `## NAME` section with required
fields `**Tier:** AUTO|QUERY|JUDGMENT`, `**Lived history:**`, and one of
(`**Detector:**` | `**Locate:**` | `**Escalation:**`) depending on tier.

## AUTO classes

### ag_nn_register_clobber

**Tier:** AUTO
**Lived history:** Shipped twice as ~5x physical damage on wild encounters.
First instance: `44ca3b29`-era `_GetSidedHL` extraction broke
`GetUserItem`'s `de` preservation. Second instance: May 2026 AG-08
`TypePassive_GetEffectiveMoveCategory_Far` `ld c, a` mirror clobbered
defender def low byte at same-bank callers in
[engine/battle/late_gen_held_items.asm](../engine/battle/late_gen_held_items.asm).
Full description in
[docs/asm_authoring_guide.md](asm_authoring_guide.md) §3.13, §3.14.
**Detector:** [tools/debugger/auto_watch.py](../tools/debugger/auto_watch.py)
`run_register_flow_detector` (wraps
[tools/debugger/register_flow.py](../tools/debugger/register_flow.py)).
Flags any function whose static clobber set contains `c`. First-slice
detector intentionally over-fires (no call-site correlation yet); the
selftest component `auto_watch` exercises broken-vs-fixed synth.
**Lived smoke:** `auto_watch` selftest component (synth AG-NN regression
in tmp asm tree).
**Audit:** `python -m tools.debugger auto-watch --self-test`.

### farcall_hl_clobber

**Tier:** AUTO
**Lived history:** Shipped twice. April 2026 one-shot damage bug. May 2026
rival 1 softlock. The `farcall` macro expands to
`ld hl, target; ld a, BANK(target); rst FarCall`, so target functions that
read `hl` as input see the macro's value, not the caller's. Three valid
patterns documented in
[docs/asm_authoring_guide.md](asm_authoring_guide.md) §3.2.
**Detector:** [tools/audit/check_farcall_hl_clobber.py](../tools/audit/check_farcall_hl_clobber.py)
auto-discovers hl-input functions via a
`; Reach via ROM0 thunk ...` marker comment and flags any `farcall` to
them.
**Audit:** `python tools/audit/check_farcall_hl_clobber.py` (in the
release-smoke floor).

### farcall_a_clobber

**Tier:** AUTO
**Lived history:** Shipped May 2026 as the wild-encounter-level-floor
no-op. `farcall` does not preserve target's `a` — caller's `a` after
`farcall` equals target's exit `c`, not target's `a`
([home/farcall.asm:13-28](../home/farcall.asm)). Five latent live bugs
surfaced in commit `13a6e3a3` when the audit first ran.
**Detector:** [tools/audit/check_farcall_a_clobber.py](../tools/audit/check_farcall_a_clobber.py).
Walks back from each `ret` through c-untouching instructions for an
`ld c, a` mirror; flags farcall sites where target is UNSAFE and the
caller consumes `a` post-farcall.
**Audit:** `python tools/audit/check_farcall_a_clobber.py` (in the
release-smoke floor).

### cross_bank_call

**Tier:** AUTO
**Lived history:** Shipped May 2026 as a type-immunity softlock. Plain
`call` only reaches the current bank or ROM0 — calling a `::` label in
another ROMX bank assembles but jumps to garbage. Commit `f2e18554` fixed
39 hits in `engine/battle/ai/boss.asm` by thunking through 7
hl-preserving wrappers (`AIxxx_HL`) that route via `farcall` to the
bank-0x0b scoring helpers.
**Detector:** [tools/audit/check_cross_bank_call.py](../tools/audit/check_cross_bank_call.py).
**Audit:** `python tools/audit/check_cross_bank_call.py` (currently PASS;
promotion to release-smoke floor gated on the trace-ROM verification
described in [CLAUDE.md](../CLAUDE.md)).

### save_format_drift

**Tier:** AUTO
**Lived history:** WRAM/SRAM offsets are part of the save format. There
is no migration code anywhere in this repo. Any field reorder/resize in
`ram/` silently misaligns old saves. Save-format changes shipping to
public release are an escalation item per
[CLAUDE.md](../CLAUDE.md).
**Detector:** [tools/audit/check_save_format_version.py](../tools/audit/check_save_format_version.py)
enforces `SAVE_FORMAT_VERSION` bump on any `ram/` change.
**Audit:** `python tools/audit/check_save_format_version.py` (in the
release-smoke floor; the rom-edit P12 gate refuses auto-apply when this
audit is red).

### typepassive_c_mirror

**Tier:** AUTO
**Lived history:** Specific instance of `ag_nn_register_clobber` that
recurs in
[engine/battle/late_gen_held_items.asm](../engine/battle/late_gen_held_items.asm).
Named separately because it has its own dedicated audit gate independent
of the more general register_flow heuristic.
**Detector:** [tools/audit/check_typepassive_c_mirror.py](../tools/audit/check_typepassive_c_mirror.py).
**Audit:** `python tools/audit/check_typepassive_c_mirror.py`.

### clobber_smoke_regression

**Tier:** AUTO
**Lived history:** The damage-chain ABI floor. Catches any clobber-class
bug that manifests as a 5-10x damage spike when a register carrying
defender def / move BP / attacker atk gets overwritten mid-chain. The
c-clobber that shipped May 2026 turned `wCurDamage` from 4 into 16 —
exactly the kind of jump this catches.
**Detector:** [tools/damage_debugger/clobber_smoke.py](../tools/damage_debugger/clobber_smoke.py).
**Audit:** `python -m tools.damage_debugger.clobber_smoke` (required by
[CLAUDE.md](../CLAUDE.md) Build & verification floor for battle-code
register-ABI changes).

### release_smoke_regression

**Tier:** AUTO
**Lived history:** The release-floor audit aggregator. Flags broad
release-quality regressions across audits (cross-bank, farcall hl/a,
save-format, others) plus repo invariants.
**Detector:** [tools/audit/check_release_smoke.py](../tools/audit/check_release_smoke.py).
**Audit:** `python tools/audit/check_release_smoke.py` (always required
per [CLAUDE.md](../CLAUDE.md) Build & verification).

### selftest_regression

**Tier:** AUTO
**Lived history:** Any v2 surface (hypothesis_tracker, save_state_lab,
when_wrote, dap_server, auto_watch, register_flow, …) silently breaks if
the underlying primitive regresses. The selftest is the daily health
gauge for all v2 surfaces.
**Detector:** [tools/debugger/selftest.py](../tools/debugger/selftest.py)
30 components.
**Audit:** `python -m tools.debugger selftest`.

### boss_ai_invariant_break

**Tier:** AUTO
**Lived history:** Boss AI overlay invariants (no hidden-info reads,
scoring-bias gate semantics, route projection consistency). Breaks here
are gameplay-correctness regressions Cole can't see in a single playtest.
**Detector:** [tools/audit/check_boss_ai_debugger_done.py](../tools/audit/check_boss_ai_debugger_done.py)
plus the `check_boss_ai_*` family in `tools/audit/`.
**Audit:** `python tools/audit/check_boss_ai_debugger_done.py` plus
audits referenced in [CLAUDE.md](../CLAUDE.md) Build & verification.

### watcher_unavailable

**Tier:** AUTO (self-reported)
**Lived history:** The autonomous watcher itself can fail (module import
error, runtime exception). The post-commit hook in
[scripts/install_debugger_hooks.py](../scripts/install_debugger_hooks.py)
appends `status=watcher_unavailable` rows to
`audit/auto_watch_findings.jsonl` when the watcher can't run, and the
hook still succeeds (per the §3 P19 fail-open contract).
**Detector:** [scripts/install_debugger_hooks.py](../scripts/install_debugger_hooks.py)
heredoc fallback (lines 36-81) writes the both-shapes
watcher_unavailable row.
**Audit:** covered by
[tools/debugger/tests/test_install_debugger_hooks.py](../tools/debugger/tests/test_install_debugger_hooks.py)
`test_install_debugger_hooks_hook_exits_zero_when_auto_watch_missing`.

## QUERY classes

### vram_pyboy_vba_divergence

**Tier:** QUERY
**Lived history:** May 2026 tile-jumble class. Cole plays in VBA-M; the
debugger runs on PyBoy. Pixel-accurate divergence between the two on a
save-state load surfaced a real bug that pixel diffs couldn't triage —
structured tile/OAM/palette diff was the readable evidence.
**Locate:** two commands.
`python -m tools.debugger vram-snapshot --decode --save-state bug.state`
returns the structured layout (BG tilemaps, OBJ palette, OAM entries).
`python -m tools.debugger vram-diff bug.state good.state` shows the
structural shift (which tiles moved, which OAM entries appeared).
Cross-emulator differential is the next escalation: `python -m
tools.debugger crossemu preflight` then `crossemu run --backends
pyboy,sameboy --save-state X --frames N`.

### boss_ai_picked_stupid_move

**Tier:** QUERY
**Lived history:** Boss AI scoring waterfall is opaque from a playtest
log — you see the picked move, not the runners-up or the gate it passed.
**Locate:** two commands.
`python -m tools.debugger triage --symptom "boss ai picked stupid move"`
routes to the boss_ai_debugger surface.
`python -m tools.boss_ai_debugger ...` (consult
[tools/boss_ai_debugger](../tools/boss_ai_debugger) for the per-route
sub-commands; the rule-waterfall trace + score-write
correlation lives there). Cross-references P20-pending
`debugger ai-trace --boss-route X --turn N --decode-rules` per the §0
north-star scenario 3.

### damage_too_high_or_low

**Tier:** QUERY
**Lived history:** Recurring debugging request when a balance change
ships and the player sees damage diverge from expected. Hand-rolling the
Gen-2 damage formula has shipped wrong numbers twice in one session per
`feedback_use_damage_debugger_dont_hand_calc.md`.
**Locate:** two commands.
`python -m tools.damage_debugger.clobber_smoke` runs the curated
regression set against the real ROM and reports observed-vs-expected
wCurDamage per scenario; deterministic via WRAM seed + PC injection.
Plus `python -m tools.debugger when-wrote --address D141 --since-symbol
BattleCommand_DamageCalc` for the specific clobber-or-input question
when a single damage value is anomalous.

### did_this_commit_break_x

**Tier:** QUERY
**Lived history:** Whenever a regression surfaces in playtest with no
obvious source commit. Pre-masterpiece the loop was
`git bisect` + hand-checking each commit.
**Locate:** one command.
`python -m tools.debugger bisect --good <commit> --bad HEAD -- python
tools/audit/check_release_smoke.py` (or any other reproducer command).
Chaos mode (`--chaos`) hardens against flaky interrupt-timing races.

### value_came_from_where

**Tier:** QUERY
**Lived history:** Recurring "why is this wCurDamage = 16 not 4?" class.
Hand-rolling watch + re-run + grep used to be a 4-iteration loop.
**Locate:** one command.
`python -m tools.debugger when-wrote --address D141 --since-symbol
BattleCommand_DamageCalc --trace .local/tmp/...` returns the writer PC,
symbol, bank, frame, register state, instruction bytes, plus a proof
vector. The `tdb` query language is the next escalation for bounded-span
queries:
`python -m tools.debugger tdb 'writes(addr=$D141) and
caller=BattleCommand_DamageCalc'`.

## JUDGMENT classes

### gameplay_feel_balance

**Tier:** JUDGMENT
**Lived history:** "Pokémon X feels overtuned vs role." "The new movepool
for Y kills the surprise factor." "This trainer's level curve drops too
fast." None of these are decidable from source. The debugger can report
stats / matchup tables / route projections, but the verdict is taste.
**Escalation:** chat with Cole. Per the rebalanced-base-stats /
movesets / trainer-rosters scope in [CLAUDE.md](../CLAUDE.md), gameplay-
taste calls escalate to him explicitly. Memory pointer:
`feedback_no_flat_distributions.md`,
`feedback_show_player_facing_ranges.md`.

### north_star_alignment

**Tier:** JUDGMENT
**Lived history:** The First-Playthrough Promise from
[CLAUDE.md](../CLAUDE.md): does this change help a knowledgeable player
feel discovery, danger, and respect for the world again? Or does it just
make the ROM harder/cleaner without serving that feeling? Not decidable
by audit.
**Escalation:** chat with Cole. Cole is the playtest seat; he reports
felt-feel and the LLM-pair adjusts.

### trainer_difficulty_curve

**Tier:** JUDGMENT
**Lived history:** Gym 1 should feel teach-by-doing; Gym 4 should feel
"do I have the right counter?"; Champion should feel "are my preparation
choices paying off?". The masterpiece debugger can replay battles and
report win-rates, but the verdict on "is this the right difficulty
shape?" is Cole's.
**Escalation:** chat with Cole. The boss-AI roadmap explicitly carves
out per-route taste calls.

---

## Catalog audit (P20 first-slice scope)

The audit at
[tools/audit/check_debugger_bug_class_catalog.py](../tools/audit/check_debugger_bug_class_catalog.py)
enforces:

1. This file exists at `docs/debugger_bug_class_catalog.md`.
2. At least 12 entries (`## <name>` headers under AUTO/QUERY/JUDGMENT
   sections, excluding section headers themselves).
3. Every entry has a `**Tier:**` line and a `**Lived history:**` line.
4. Every AUTO entry has a `**Detector:**` line.
5. Every QUERY entry has a `**Locate:**` line.
6. Every JUDGMENT entry has an `**Escalation:**` line.

Out of scope for slice-1 (slice-2 work):
- Auto-executing every AUTO entry's `**Audit:**` line and verifying exit 0.
- Cross-referencing every selftest lived-smoke component to a catalog
  entry (mechanical: walk `NAMED_CHECKS` in
  [tools/debugger/selftest.py](../tools/debugger/selftest.py); for each
  component name, find a catalog entry that references it; fail closed
  if any are missing).
- Adding the audit to `tools/audit/check_release_smoke.py`.
