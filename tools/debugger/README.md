# Unified Pokemon Gold Romhack Debugger

`tools.debugger` is the project-wide front door for debugger discovery and
triage in this Pokemon Gold romhack worktree. It does not replace the focused
subsystem debuggers. It records what exists, routes symptoms or changed files to
the strongest available tools, and keeps the remaining whole-ROM gaps visible.

```powershell
python -m tools.debugger inventory
python -m tools.debugger audit
python -m tools.debugger audit --strict
python -m tools.debugger ingest --rom pokegold.gbc --symbols pokegold.sym --trace audit\boss_ai_trace\clair_live.txt
python -m tools.debugger ingest --scenario audit\boss_ai_debugger\runs\expanded_policy_smoke\scenarios.jsonl
python -m tools.debugger triage --changed-file engine\battle\late_gen_held_items.asm
python -m tools.debugger triage --symptom "boss selected the wrong switch"
python -m tools.debugger gate --changed-file engine\battle\late_gen_held_items.asm
python -m tools.debugger gate --changed-file engine\battle\late_gen_held_items.asm --execute --max-commands 2
python -m tools.debugger investigate --trace audit\boss_ai_debugger\rom_contribution_trace_smoke.json --symbol BossAI_ApplyMoveModel --address D0D3 --expect "event=score_delta,symbol=wEnemyAIMoveScores"
python -m tools.debugger investigate --patch wTypeMatchup=0 --watch-symbol wEnemyAIMoveScores --symptom "AI chose a Ground move into immunity"
python -m tools.debugger localize --symbol wCurDamage --symptom "damage spike"
python -m tools.debugger localize --report .local\tmp\debugger_watch_smoke.json --report .local\tmp\debugger_slice_smoke.json
python -m tools.debugger coverage --symbol BattleCommand_DamageCalc --report audit\boss_ai_debugger\runs\20260515_121426_changed_ai\rom_contribution_trace_summary.json
python -m tools.debugger coverage --changed-file engine\battle\ai\boss_policy_move.asm --trace audit\boss_ai_debugger\rom_contribution_trace_smoke.json
python -m tools.debugger coverage --rule move.apply_move_model.apply_role_bias --report audit\boss_ai_debugger\runs\20260515_121426_changed_ai\rom_contribution_trace_summary.json
python -m tools.debugger trace-index --trace audit\boss_ai_debugger\rom_contribution_trace_smoke.json --symbol BossAI_ApplyMoveModel
python -m tools.debugger trace-index --report .local\tmp\debugger_watch_smoke.json --watch-symbol wCurDamage --address D141
python -m tools.debugger minimize --scenario audit\boss_ai_debugger\runs\expanded_policy_smoke\scenarios.jsonl --scenario-id generated_policy_00000 --out-scenarios .local\tmp\debugger_minimized_candidates.jsonl
python -m tools.debugger minimize --symbol wCurDamage --bug-id hp_d_clobber
python -m tools.debugger minimize --trace .local\tmp\debugger_reverse_trace_smoke.json --expect "event=memory_write,symbol=wCurDamage" --out-trace .local\tmp\debugger_minimized_trace.json
python -m tools.debugger minimize --report .local\tmp\debugger_watch_smoke.json --expect "event=watch_change,symbol=wCurDamage" --expect "event=control_flow,symbol=BattleCommand_DamageCalc" --out-trace .local\tmp\debugger_minimized_watch.json
python -m tools.debugger minimize --report .local\tmp\debugger_state_space.json --expect "state-patch=wTypeMatchup,value=0x00,applied=true,verified=true" --execute-state-patches --out-state-report .local\tmp\debugger_state_space_minimized.json
python -m tools.debugger trace-instructions --report .local\tmp\debugger_watch_smoke.json --execute --require-hit --out-trace .local\tmp\watch_instruction_trace.jsonl
python -m tools.debugger trace-instructions --symbol BattleCommand_DamageCalc --watch-symbol wCurDamage --execute --require-hit --out-trace .local\tmp\damagecalc_instruction_trace.jsonl
python -m tools.debugger dynamic-taint --trace .local\tmp\instruction_trace.jsonl --source-reg a=move_power --sink-symbol wCurDamage
python -m tools.debugger dynamic-taint --report .local\tmp\damagecalc_instruction_trace.json
python -m tools.debugger watch --reset-sentinel --rom pokegold.gbc --symbols pokegold.sym --save-state path\to\state --frames 1200 --context-frames 20
python -m tools.debugger watch --reset-sentinel --rom pokegold.gbc --symbols pokegold.sym --battery-save pokegold.sav --out-initial-state .local\tmp\continue.state --input 0:a:8 --watch-symbol wScriptBank --watch-symbol wScriptPos --execute
python -m tools.debugger state-inspect --save-state for_codex1.sgm --rom pokegold.gbc --symbols pokegold.sym --json-out .local\tmp\for_codex1_runtime_state.json
python -m tools.debugger script-resume-gate --report .local\tmp\for_codex1_runtime_state.json
python -m tools.debugger learnset-inspect --species GASTLY --level 14
python -m tools.debugger party-inspect --save pokegold.sav --slot 1
python -m tools.debugger grass-regrowth --max-total-hp 300
python -m tools.debugger wram-ownership --symbol wSeenTrainerBank --symbol wScriptAfterPointer --symbol wRunningTrainerBattleScript
python -m tools.debugger wram-lifetime --symbol wSeenTrainerBank --symbol wScriptAfterPointer --symbol wRunningTrainerBattleScript --through Script_startbattle
python -m tools.debugger wram-bank-hazards --source-file engine\battle\ai\observation_log.asm
python -m tools.debugger repro-recipe --id first-wild-route29
python -m tools.debugger repro-recipe --id trainer-battle-evolution-resume
python -m tools.debugger setup --symbol wCurDamage --watch-symbol wCurDamage --out-scenarios .local\tmp\debugger_setup_scenarios.jsonl
python -m tools.debugger setup --report .local\tmp\debugger_investigate_wrong_switch.json
python -m tools.debugger generate --symbol wCurDamage --out-scenarios .local\tmp\debugger_generation_seeds.jsonl
python -m tools.debugger generate --changed-file engine\battle\ai\boss_policy_move.asm --family all --max-cases 64 --seed 1
python -m tools.debugger provenance --symbol wCurDamage --symbol BattleCommand_DamageCalc
python -m tools.debugger provenance --source-file engine\battle\effect_commands.asm
python -m tools.debugger slice --symbol wCurDamage
python -m tools.debugger slice --source-file engine\battle\effect_commands.asm --depth 3
python -m tools.debugger watch --watch-symbol wCurDamage
python -m tools.debugger watch --rom pokegold_trace.gbc --symbols pokegold_trace.sym --save-state path\to\state --watch-symbol wEnemyAIMoveScores --execute --context-frames 24
python -m tools.debugger replay --rom pokegold.gbc --symbols pokegold.sym --save-state path\to\state --watch-symbol wCurDamage --execute-watch --context-frames 24
python -m tools.debugger replay --report .local\tmp\debugger_watch_smoke.json --trace audit\boss_ai_debugger\rom_contribution_trace_smoke.json --symbol BossAI_SelectMove
python -m tools.debugger explain --report .local\tmp\debugger_replay_boss_ai.json --symbol BossAI_SelectMove
python -m tools.debugger explain --report .local\tmp\debugger_watch_smoke.json --watch-symbol wCurDamage --symptom "damage changed unexpectedly"
python -m tools.debugger suggest-tests --changed-file engine\battle\late_gen_held_items.asm
python -m tools.debugger suggest-tests --symbol BossAI_SelectMove --symptom "bad switch choice"
python -m tools.debugger suggest-tests --report .local\tmp\debugger_investigate_wrong_switch.json
python -m tools.debugger compare --symbol wCurDamage
python -m tools.debugger compare --changed-file engine\battle\ai\boss_policy_move.asm
python -m tools.debugger content-mirror --source-file maps\NewBarkTown.asm
python -m tools.debugger content-scenarios --source-file maps\NewBarkTown.asm --out-scenarios .local\tmp\debugger_content_scenarios.jsonl
python -m tools.debugger state-space --patch wMapGroup=1 --patch wMapNumber=2 --patch wXCoord=6 --patch wYCoord=3 --json-out .local\tmp\debugger_state_space.json
python -m tools.debugger state-space --patch wScriptBank=2 --patch wScriptPos=0x50,0x40 --base-save-state path\to\base.state --out-state .local\tmp\patched.state --execute --json-out .local\tmp\debugger_state_space.json
python -m tools.debugger expect --report .local\tmp\debugger_trace_index_boss_ai.json --expect event=score_delta,symbol=wEnemyAIMoveScores
python -m tools.debugger expect --trace audit\boss_ai_debugger\rom_contribution_trace_smoke.json --rule move.apply_move_model.apply_role_bias
python -m tools.debugger expect --source-file maps\NewBarkTown.asm --expect contains=warp_event --expect not-contains=TODO
python -m tools.debugger rank --report .local\tmp\debugger_watch_smoke.json --report .local\tmp\debugger_diff.json
python -m tools.debugger impact --report .local\tmp\debugger_watch_smoke.json --changed-file engine\battle\effect_commands.asm --symbol wCurDamage
python -m tools.debugger report --report .local\tmp\debugger_watch_smoke.json --report .local\tmp\debugger_diff.json --out .local\tmp\debugger_report.md
python -m tools.debugger report --report .local\tmp\debugger_watch_smoke.json --format html --out .local\tmp\debugger_report.html
python -m tools.debugger visualize --report .local\tmp\debugger_replay_boss_ai.json --report .local\tmp\debugger_explain_boss_ai.json --out .local\tmp\debugger_visualization.md
python -m tools.debugger visualize --report .local\tmp\debugger_explain_damage.json --format html --out .local\tmp\debugger_visualization.html
```

Current mature subsystems:

- `tools.boss_ai_debugger`: Boss AI policy, traces, ROM materialization,
  generated scenarios, review queues, and changed-AI gates.
- `tools.damage_debugger`: damage-chain ROM-vs-oracle fuzzing, clobber smoke,
  replay, taint, coverage, and Tenet export.
- `tools.trace`: PyBoy runtime helpers, trace capture, symbol parsing, and
  save-state replay plumbing.
- `tools.audit`: static and release smoke gates.

`ingest` writes a generic manifest for ROMs, symbol files, trace text, save
states, generated scenario JSON/JSONL, and source-change paths. The manifest
records artifact type, normalized path, size, SHA-256, lightweight structural
metadata, parse warnings, and parse errors. This gives later replay,
localization, differential, and provenance tools stable inputs without forcing
Boss-AI-specific or damage-specific schemas onto every ROM surface.

`triage` routes changed files and symptom text to the strongest available
subsystem debugger. Symptom keywords are tokenized instead of substring-matched,
so short routing words such as `ai` only match as standalone words while
battle-mechanics phrases such as `Air Balloon Ground immunity` route to the
damage/type-matchup tooling. JSON output includes `matched_symptom_keywords`
when text caused a route.

`gate` turns triage into an ordered workflow. By default it only prints the
selected commands. With `--execute`, it runs known commands whose arguments are
fully concrete and skips placeholder commands that need a specific scenario or
artifact.

`investigate` is the one-command ROM debugging packet for this worktree. It
ingests the supplied ROM/symbol/trace/save-state/scenario/source-change inputs,
turns any explicit `--patch SYMBOL=VALUE` WRAM hypotheses into a generic
state-space report, then runs trace indexing, replay planning, localization,
coverage, causal explanation, mirror routing, optional expectation checks, counterexample
generation, minimization, ranking, impact scoring, static reporting, and
visualization into a single output directory. It is the command to start with
when a symptom has evidence but the next debugger step is unclear. A pass means
the packet was internally consistent and any supplied expectations passed; it is
only a bug proof when the included evidence is ROM-backed.
When it is invoked with only `--symptom`, the output is explicitly a planning
packet, not a repro; the JSON embeds the same `unified_debugger_next_step`
proof path used by `next`, including required inputs, source/data anchors,
evidence and disproof standards, and the regression gate so `rank`, `report`,
and `visualize` keep that routing intact.

`localize` combines symptoms, source changes, symbols, and existing unified JSON
reports into a prioritized debugging plan. It scores likely symbol and source
file suspects, folds in static slices, watch hits, trace-index reverse
attributions, expectation failures, and minimized-trace handoffs when available,
then lays out reproduce, observe, slice, compare, minimize, and verify phases
with the commands that can prove or reject each suspect.
When a report contains an embedded `unified_debugger_next_step` route, such as a
symptom-only `investigate` packet, `localize` treats its source/data anchors as
localization signals and places the routed first proof command, escalation, and
regression gate into the workflow phases.

`coverage` normalizes coverage-like evidence from unified JSON reports, Boss AI
contribution traces, coverage target reports, watch output, and key/value trace
text. Given explicit symbols or changed files, it marks targets as directly
covered, indirectly covered through related labels/files, or still uncovered,
then prints proof commands for the gaps.

`trace-index` turns arbitrary trace JSON/JSONL/text and unified reports into a
ROM-oriented event index. It recognizes watch changes, score deltas, memory
reads/writes, public-read hints, rule hits, PC context, addresses, source
labels, and source files; annotates what it can through the current `.sym` file
and static slice data; then emits address/symbol/rule indexes plus causal links
from writers to later readers or overwrites. It also emits bounded reverse
attribution windows for matched writes, linking them to prior reads, values, and
rule/source context when the trace exposes enough evidence. This is the generic
trace evidence bridge for `explain`, `rank`, `impact`, and `report`. It is
still not a full instruction-level SM83 taint engine.

`dynamic-taint` consumes dense SM83 instruction traces with opcode, operand,
register, PC, and label fields, then runs byte-level taint through the same
instruction transfer model used by the damage debugger. It accepts register,
memory, or symbol seeds and reports which dynamic writes to sink symbols or
addresses are tainted, with path evidence that downstream `rank`, `impact`,
`localize`, `report`, and `visualize` understand. `--report` can load an
instruction-trace or minimization report, discover written trace artifacts,
watched sink symbols, and optional `dynamic_taint_sources` metadata, then run the
same taint/write-attribution engine without manually copying trace paths and
sinks. Even without explicit source seeds, it emits `write_attributions` for
exact sink-writing instructions, including the source operands visible in the
trace, so impact/ranking can carry instruction-level reverse evidence before the
final source seed is known. This is the unified bridge for
emulator-trace-backed causality; it still requires a trace window that actually
covers the relevant instructions.

`trace-instructions` creates that dense trace window. It disassembles selected
function symbols from the current ROM and `.sym`, or derives likely hook windows
from watch reports, trace reports, content-scenario runtime targets,
content-state materializations, changed source labels, and symptoms;
`--scenario-id` narrows content-scenario or content-state reports to a single
generated case. When a loaded content-state report was executed and its
`out_state` exists, `trace-instructions` reuses that state automatically unless
`--save-state` was supplied. It plans a hook for every decoded SM83 instruction,
and with `--execute` records opcode, operand, PC label, registers, and watched
state before each executed instruction. Its `execution_validation` block reports which selected hooks
actually fired, which planned routines were missed, and whether the captured
trace is ready to feed `dynamic-taint`; `--require-hit` turns an empty executed
window into a failing proof step. The output JSONL is designed to feed
`dynamic-taint`, `trace-index`, `expect`, and `minimize`. This gives the
unified debugger a capture path for instruction-level causal evidence without
requiring every subsystem to invent its own trace format.

`state-inspect` is the read-only crash-state inspector for emulator snapshots.
For VBA-M `.sgm` files it decompresses the state, parses CPU registers, locates
the live WRAM window from party/map/script anchors, resolves the current map
script bank/range, and flags impossible script VM states such as
`wScriptBank:wScriptPos=$B4:$0002` after a trainer battle and evolution. For
PyBoy `.state` files it loads the state through PyBoy and reads the same
symbols. For `.sav` files it copies the ROM to a temporary path, attaches the
save as a `.ram` sidecar, presses through Continue, and inspects that live
state. This is diagnosis for an already-captured or booted state; fix proof
still needs a before-trigger replay/watch.

`watch` can replay from an existing PyBoy `.state`, or from a `.sav` by copying
the ROM to a temporary work path, attaching the battery save as a `.ram` sidecar,
pressing through Continue, and then polling the requested symbols. Scheduled
inputs use `--input FRAME:BUTTON[:DELAY]` and are recorded in the report with
initial/final PC/SP snapshots. This is still a faithful forward watch only for
the supplied state/input route; it does not auto-navigate arbitrary saves to a
trainer.

`script-resume-gate` evaluates `state-inspect` and watch reports for the
post-battle/evolution freeze class. It fails on reset sentinels, invalid script
PCs, script-bank/current-map mismatches, echo-RAM returns, or watch-emitted
`invalid_script_state` events. For watch reports it also requires actual
execution, the trainer resume watch symbols, reset sentinels, and PC/SP
snapshots. Use it with `repro-recipe
trainer-battle-evolution-resume` to keep the distinction between a corrupted
crash-state diagnosis and a before-trigger proof. A watch with only idle frames
or trainer-bank-only union churn is rejected rather than treated as proof.

`wram-ownership` explains static WRAM overlap risk for named symbols. It
identifies `UNION` co-tenants and source references, which is the quick way to
see that trainer resume bytes such as `wSeenTrainerBank`,
`wScriptAfterPointer`, and `wRunningTrainerBattleScript` share volatile WRAM
with other temporary contexts. It does not prove dynamic overwrite order; pair it
with watch or instruction tracing for that.

`minimize` plans the shortest path from a suspect or failing report to a
minimal proof case. It extracts scenario IDs and bug IDs from reports and
scenario JSON/JSONL, can write a smaller scenario subset, and routes the result
to the right semantic reducer: Boss AI scenario minimization/counterfactuals or
damage-debugger ddmin/replay. Given arbitrary trace evidence or a unified JSON
report plus explicit expectations, it can also write a reduced evidence
artifact that still satisfies the expectation gate. For content-state reports
and explicit generic state-space reports with `state_patches` or
`state_space.patches`, `--out-state-report` can write a minimized WRAM patch
evidence view that preserves explicit `state-patch` expectations, then routes
that reduced state evidence back through `expect`, `replay`, and `compare`.
With `--execute-state-patches`, explicit generic state-space patch candidates
are materialized through PyBoy before the minimizer accepts them, so expectations
such as `applied=true,verified=true` are checked against an actual patched save
state.
Watch/replay reports keep only the relevant events and trim nested
dynamic-context frame windows to the smallest useful causal context, giving
every ROM surface a compact repro artifact before a surface-specific reducer
exists. It is the unified coordinator; full semantic behavior reduction still
requires replaying the owning ROM surface after the minimized state is built.

`state-space` turns explicit WRAM hypotheses into a generic patch report that
the rest of the debugger can consume. A patch such as `wScriptPos=0x50,0x40`
resolves through the current `.sym`, records exact bank/address/value evidence,
and emits expectation, replay, watch, instruction-trace, minimization, compare,
impact, and visualization commands. With `--execute`, it loads an existing save
state through PyBoy, writes the requested bytes, verifies them, and saves a
patched state. This is the escape hatch for arbitrary ROM states that are not
yet covered by a content-specific materializer.

`generate` coordinates focused test generation and counterexample search. It
combines reports, scenarios, changed files, symbols, symptoms, and optional
families; infers the affected ROM surfaces; then routes to damage fuzzing,
Boss AI generated-policy scenarios, banking/ABI hazard checks, content/static
invariant checks, map content positioned-state materialization, and the
downstream minimization, mirror, materialization, impact, and report commands
needed to prove a bug. Ready instruction-trace reports are now routed directly
to `dynamic-taint --report ...` handoffs, so captured execution can feed
source-to-sink attribution without manually copying trace paths and watched
sinks. With `--out-scenarios`, it writes a deterministic JSONL seed manifest
for the unified debugger workflow. Map content seeds that carry state
preconditions now include `materialization_request` records that write a
`content-state` report/state and replay it; other surfaces remain handoff
records until their dedicated ROM materializers exist.

`setup` is the bridge between “this symbol/file/report looks relevant” and
“here is how to reach it in the ROM.” It infers the affected surface, then emits
the scenario generation, `state_synthesis_recipes`, subsystem materialization,
save-state/replay, watch, and `trace-instructions --require-hit` validation
commands needed before a runtime claim should be treated as proof. Damage and
Boss AI setup can hand off to mature materializers; content setup creates
semantic scenario manifests, concrete trigger precondition records, and runtime
helper/watch replay routes for maps, scripts, graphics, and audio; banking and
general setup route through audits, watches, and targeted replay.
Its `trigger_coverage` block grades each target as covered, planned, or blocked
and names the missing piece, such as a concrete scenario ID, supplied save
state, or validation expectation. If loaded scenarios or reports already name a
concrete `state`, `save_state`, `pre_choice_state`, or materialization-state
path, setup discovers it, prefers requested scenario IDs, and threads that state
into replay and instruction-trace commands. When no concrete state is available,
the recipe block shows the exact state factory, materializer, or watch/probe
commands to run next. When a report contains an embedded
`unified_debugger_next_step` route, `setup --report` treats that route as the
setup surface and target source of truth; for the wrong-switch route this keeps
setup on Boss AI and targets `BossAI_SwitchOrTryItem`,
`wEnemySwitchMonIndex`, `wEnemySwitchMonParam`, and `wEnemyAIMoveScores`
instead of inheriting unrelated nested damage or banking setup lanes. It plans
setup and trigger work; it does not yet synthesize every arbitrary save state
itself.

`fuzz` turns inferred surfaces into concrete fuzz campaigns. Damage and Boss AI
campaigns route to the mature dynamic fuzzers/generators; banking campaigns add
bank/register watch and taint probes; content/static campaigns infer
source-expectation cases and runtime probe routes from labels and macros such
as `warp_event`, `object_event`, and `INCBIN`. Ready instruction-trace reports
become `dynamic_trace` fuzz campaigns and `dynamic_taint_handoff` cases. With
`--out-cases`, it writes a deterministic JSONL fuzz-case manifest that can be
fed back into `expect`, `compare`, `localize`, `rank`, `impact`, `report`, and
`visualize`. Static fuzz cases prove source invariants, not runtime behavior,
until paired with replay or dedicated materialization.

`provenance` joins the current `.sym` file with source labels and references.
It can show where a watch symbol or routine lives, which source files mention
it, and which subsystem debugger commands are most likely to be useful. This is
static provenance; dynamic proof still comes from replay, trace, taint, and
subsystem-specific materialization tools.

`slice` builds a static RGBDS assembly dependency slice for symbols or source
files. For a watched WRAM symbol it shows plausible readers/writers/callers and
the files affected by the slice; for a routine or data label it also shows the
labels it touches. This is a source graph, not a CPU trace, so it is best used
to choose the next replay, watch, taint, differential, or audit command.

`taint` performs a bounded source-level SM83-style backward dataflow pass over
RGBDS assembly. Given a target symbol, it finds direct and same-routine indirect
writes, walks register loads and simple value transforms backward, and reports
which source symbols may have contributed to the written value. It is the bridge
between a coarse static `slice` and emulator-backed trace evidence: stronger
than a reference graph, but still not a full dynamic CPU taint engine.

`watch` is the generic runtime bridge. In plan mode it resolves watch symbols,
attaches static provenance, and reports the debugger commands likely to help. In
reset-sentinel mode it can run without a watched symbol, hook the reset/start
vectors, and dump recent PC/register context plus `hROMBank`, `hWRAMBank`,
`wBattleMode`, and `wTempWildMonSpecies` when a replay jumps back through boot.
Use that first for reports like "reset to intro then black screen"; it keeps
crash handling ahead of static policy-matrix checks.
In `--execute` mode it opens the ROM in PyBoy, optionally loads a save state, polls
the watched symbols for a bounded number of frames, and records changes with PC
bank/address, nearest symbol context, register snapshots, watch values, and the
preceding `--context-frames` frame-context window. Each hit also carries a
bounded source-cause slice, so the watch output points at likely static
writers/readers and the follow-up `trace-index`, `slice`, `explain`, `localize`,
and `minimize` commands. It is frame-sampled forward polling, not hardware
watchpoints, instruction-by-instruction dynamic taint, or reverse execution.

`wram-bank-hazards` is a static guard for WRAMX stack/bank bugs. It flags
`call SetWRAMBank` sites that could return through the newly selected WRAMX
bank, explicit push/pop pairs that cross an inline WRAM bank switch, and
routines that return before restoring WRAMX bank 1. Pair it with
`watch --reset-sentinel` when a symptom smells like a jump to the intro or a
black-screen reset.

`repro-recipe` prints named, scenario-specific capture recipes. The first
checked-in recipe is `first-wild-route29`, which routes new-save Route 29 wild
encounter resets through the reset sentinel, instruction trace, and WRAM
bank/stack hazard scan before broader static audits.

`replay` is the unified reproduction coordinator. It fingerprints the ROM,
symbols, traces, save states, scenarios, and changed files you give it; derives
watchable RAM targets and suspect labels from traces and existing debugger
reports; then emits a repeatable workflow for setup/trigger materialization,
watch replay, localization, coverage proof, generic trace minimization,
subsystem minimization, mirror comparison, impact ranking, report rendering,
and final gates. It now runs the setup planner internally, reuses scenario/report
save-state discovery, and threads an existing discovered state into watch and
instruction-trace commands so ROM proof starts from the concrete scenario state
when one is available. When a report contains an embedded
`unified_debugger_next_step` route, `replay --report` turns that route into
concrete trace/watch targets and source refs; for the wrong-switch route this
means `BossAI_SwitchOrTryItem`, `wEnemySwitchMonIndex`,
`wEnemySwitchMonParam`, and `wEnemyAIMoveScores`, not impact-report tag words
from prose. With `--execute-watch`, it runs the generic PyBoy watch bridge and
embeds the enriched watch report, including dynamic context windows, in the
replay plan.

`explain` turns watch/replay reports, trace-index reports, traces, symptoms,
symbols, and changed files into ranked causal paths. For a dynamic watch hit or
trace-index event it connects the changed state, PC/source label, source
definition, and static readers/writers/callers into a single evidence path with
proof commands and a Mermaid graph. For content scenario reports it now also
builds paths from the map/audio/asset trigger to source labels, script labels,
runtime helper routines, watch symbols, and the setup/replay/coverage/provenance
commands needed to prove the behavior. This is stronger than a raw static slice
because runtime evidence or runtime probe targets anchor the path, but it is
still not a full instruction-level SM83 taint graph for every memory byte.
When a report contains an embedded `unified_debugger_next_step` route,
`explain` emits a causal proof-path node chain with the routed first command,
source/data anchors, evidence standard, disproof standard, proof limit, and
regression gate, keeping symptom-only planning packets explainable without
pretending they are ROM-backed repros.

`suggest-tests` maps changed files, symbols, symptoms, and prior debugger
reports to this repo's existing fuzzers, generators, metamorphic checks,
coverage reports, and counterexample/minimization commands. When a report
contains an embedded `unified_debugger_next_step` route, `suggest-tests --report`
promotes the routed first proof command and regression gate into the
check-command list, preserves escalation as the counterexample command, and
keeps required inputs, source/data anchors, evidence/disproof standards, and
proof limits in notes. It is the lightweight registry layer used by `generate`;
surfaces without dedicated generators still report static fallback gates and
notes.

`compare` declares which mirrors/oracles can check a surface. It distinguishes
damage's ROM-vs-oracle checks, Boss AI's Python policy/differential plus ROM
materialization checks, static content/source expectation checks, and
content-state behavioral mirror reports. With `--report <content_state.json>`,
it turns WRAM map-position patches into `state-patch` expectation commands plus
replay/watch proof routes from the generated state report. It prints both quick
compare commands and the materialization/proof commands needed before treating a
result as ROM behavior.

`content-mirror` is the romhack-aware static mirror for maps, scripts, graphics,
audio, text, and data. It parses RGBDS labels and macros, checks map event
sections such as `def_warp_events`/`warp_event`, verifies `INCBIN` asset targets,
checks audio `channel_count` blocks, and reports object-constant mismatches as
warnings. When `pokegold.gbc` and `pokegold.sym` are available, it also encodes
each `_MapEvents` table from source and byte-compares it against the built ROM,
so map warps, coordinate events, background events, and object events now have a
ROM materialization check. Common script commands such as text jumps, local
branches, event flag checks, standard-script jumps, movement pointers, and item
commands are encoded from their RGBDS macros and byte-compared against script
labels in the built ROM. Common map-action and battle setup macros such as
`special`, `pause`, `appear`, `disappear`, `moveobject`, `setmapscene`,
`winlosstext`, `loadtrainer`, `startbattle`, mart/shop commands, trainer
records, random branches, command queues, and map music commands are encoded
too, including banked `callasm`/`autoinput`, `musicfadeout`,
`catchtutorial`, command-queue stone tables, and the local Underground
`doorstate` macro expansion, so many map-script edits now have a direct
compiled bytecode proof. Local script and text labels resolve against their
parent labels, including colonless local labels, so embedded branch targets and
inline dialogue are compared at the correct ROM address.
Standard text macro blocks are encoded through
`constants/charmap.asm`, including RGBDS decimal string interpolation such as
`{d:NUM_UNOWN}`, and byte-compared against text labels, so dialogue and sign
text edits get the same source-to-ROM proof. Movement data blocks such as
`step`, `turn_head`, `step_sleep`, and `step_end` are encoded from movement
macros and byte-compared against movement labels, proving NPC path edits landed
in the ROM before an emulator replay. Audio `channel_count`/`channel` headers are encoded
from source and byte-compared against the built ROM too, proving the compiled
channel count, channel ids, and channel pointers before full playback replay
exists. Labeled `INCBIN` assets and aggregate `INCBIN` tables are byte-compared
against the ROM as well, which covers many graphics, tilemaps, compressed blobs,
footprint sheets, and data payloads. Labeled RGBDS `db`/`dw`/`dn` data blocks,
quoted charmap strings, and text-style string continuations are also encoded
from source and byte-compared against ROM labels, giving plain tables, names,
mail text, and pointer lists a source-to-ROM proof route without a custom
semantic mirror. Its JSON output
feeds `rank`, `impact`, `report`, and `visualize`.
This is stronger than raw `contains=` expectations because it understands the
Pokemon Gold source conventions and can prove source bytes landed in the ROM,
but it is still not an emulator-backed interaction replay.

`content-scenarios` converts those same ROM source conventions into deterministic
semantic scenario records: map warps, coordinate/background/object events,
script command streams, text blocks, movement data paths, `INCBIN` asset
materialization checks, and audio channel blocks. The JSONL output
feeds `generate`, `fuzz`, `replay`, `minimize`, `rank`, `impact`, `report`, and
`visualize`. Each scenario now carries `runtime_targets` for source labels,
script labels, event-engine or loader trace helpers, and map/script/movement/audio/asset
watch symbols, `state_preconditions` for the map/script/movement/audio/asset state that
must be loaded or synthesized before emulator proof, plus `behavioral_probes` that route
the case through content mirrors, concrete `expect` assertions, replay/setup,
coverage, comparison, provenance, runtime trace/watch planning, content-state
execution, positioned-state replay, positioned-state instruction tracing, and
minimization. These cases say exactly what map trigger, script entry, movement
stream, asset, or audio block to exercise; map, script command-stream, and
movement-data scenarios can now be converted into replayable WRAM-patched
states, while audio and asset cases emit explicit PlayMusic/graphics-loader
trace/watch proof routes until they have dedicated state builders.
`minimize --report <content-scenarios.json>` can now extract a reduced scenario
JSONL subset directly from the report while preserving those state preconditions.
`setup --report <content-scenarios.json>` treats those preconditions as real
positioned-state requirements: without a matching save state the trigger
coverage stays planned and reports `state:partially-synthesizable`, while a
scenario/report-provided state can promote the same content runtime proof route
to covered.
`content-state` closes the next step in that path by resolving map labels
through `data/maps/maps.asm` and `pokegold.sym`, resolving script and movement
labels through `pokegold.sym`, then producing concrete
`wMapGroup`/`wMapNumber`/`wXCoord`/`wYCoord` map-position patches or
`wScriptBank`/`wScriptPos`/`wScriptRunning`/`wScriptMode` script-entry patches,
or `wMovementObject`/`wMovementDataBank`/`wMovementDataAddress`/
`wMovementPointer` movement-entry patches. Audio and asset-loader preconditions
now become planned runtime proof records with concrete watch symbols
(`wMusicID`, `wMusicBank`, channel flags, and 1bpp/2bpp request queues) and
helper trace commands, but they remain non-executable until an owning caller or
save state is supplied.
With
`--base-save-state`, `--out-state`, and `--execute`, it applies those patches to
a PyBoy state file so replay/watch/trace-instructions can start from the
requested content position, script entry, or movement entry. The resulting JSON report feeds
`trace-instructions`, `expect`, `replay`, `compare`, `rank`, `impact`,
`report`, and `visualize`, so a positioned map scenario or script command stream
can now be checked, prioritized, and inspected as a ROM-backed state mirror
before running the final trigger replay.

`expect` evaluates high-level behavior claims against captured evidence from
traces and unified reports. It supports CLI assertions such as
`--expect no-errors`, `--expect symbol=wEnemyAIMoveScores`,
`--expect event=score_delta,symbol=wEnemyAIMoveScores`,
`--expect scenario=content_scenario_1_0000`, and
`--expect precondition=map_position,scenario=content_scenario_1_0000,symbol=wMapGroup`.
JSON/JSONL expectation files can use fields like `event_type`, `symbol`,
`rule_id`, `address`, `source_file`, `scenario_id`, `precondition_kind`,
`min_count`, and `max_count`. It gives every ROM
surface a common ROM-vs-expectation gate even before that surface has a bespoke
semantic oracle. With `--source-file`, it also loads source files directly, so
maps, scripts, graphics, audio, text, and UI changes can be checked with static
expectations such as `contains=warp_event` or `not-contains=TODO` before a
dynamic mirror exists. A pass means the supplied evidence or source satisfied
the claim; replay or subsystem materialization is still required when the
evidence itself is not yet ROM-backed.

`rank` normalizes findings from unified JSON reports into one severity-ordered
queue. It currently understands ingest manifests, watch reports, gate plans,
compare plans, content mirrors, content scenarios, content-state
materializations, test suggestions, generation plans, trace indexes, taint
reports, instruction-trace validation, and expectation reports. Ranking is
intentionally conservative: hard failures, invalid artifacts, instruction traces
whose selected hooks did not fire, blocked content-state patches, failed content
invariants, and failed expectations outrank ready state materializations, watch
hits, taint paths, trace events, generator gaps, mirror gaps, and documentation
warnings. Instruction traces that did hit watched sinks are promoted as
dynamic-taint handoffs instead of being buried as generic trace events. Ranking
also applies a small ROM-surface calibration for banking/ABI, battle damage,
Boss AI, event scripts/maps, movement/text, graphics/audio/UI, and
Pokemon/move-data evidence so equally severe findings on riskier ROM surfaces
sort predictably.

`impact` turns ranked findings, coverage gaps, localization candidates,
minimization routes, watch hits, gate failures, explicit changed files, suspect
symbols, symptom text, instruction-trace validation state, and content-state
ready/blocked/executed materialization reports into one ROM-aware priority
queue. It scores each item by failure
severity, proof evidence, runnable next commands, and the likely project surface
affected: banking/ABI, battle damage, Boss AI, battle core, Pokemon/move data,
maps/scripts/text, graphics/audio/UI, or debugger tooling. This is the command
to use when several debugger reports exist and the next question is which
suspected bug can hurt the romhack most and how to prove it.

`report` renders one or more unified JSON reports into a static Markdown or HTML
summary for a debugging run. It keeps the raw JSON as the source of truth, then
extracts the highest-priority findings, input report status, gaps, issues, and
follow-up commands so a romhack debugging session can be scanned without reading
every JSON file by hand. `next` JSON reports are treated as first-class proof
path inputs: the rendered report preserves the recommended first command,
required inputs, source/data anchors, evidence/disproof standards, proof limit, regression gate, escalation command, and repro
recipe links instead of collapsing them into an unsupported-report warning. `audit` JSON reports are
also first-class inputs: partial or missing capabilities become ranked findings
with readiness counts, blocker context, and the next proof commands from the
capability audit.

`visualize` renders one or more unified reports and traces into a visualization
packet. It builds a timeline of runtime/watch/trace/coverage/content/
content-state patch/instruction-trace validation/impact events, a workflow
waterfall from replay/localization/minimization/gate/materialization/
instruction-trace steps, a causal graph from explanation/slice/coverage/content/
content-state/instruction-trace artifacts, Mermaid timeline and graph blocks,
and Markdown or HTML output. It also treats `next` and `audit` JSON as proof
surface inputs: next-step reports become proof-route, source-ref, evidence-standard, disproof-standard, regression-gate,
timeline/waterfall/graph items, and capability audits become readiness lanes
with blocker capabilities and their next proof commands. HTML output includes a self-contained interactive
evidence inspector with search, lane/source filters, severity filtering, and
graph-edge tables. It is the unified view for scanning a debugging run; full
emulator-coupled canvas/TUI inspectors are still a future layer.

The whole-ROM goal means this romhack's ROM and source surfaces, not arbitrary
unrelated Game Boy games. `audit` should stay honest: until every relevant
project surface has generic ingest, replay, causal provenance, counterexample
generation, mirror comparison, impact ranking, reporting, and workflow
automation, it must report `ready=False`.
