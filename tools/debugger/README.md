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
python -m tools.debugger capture-playtest --rom pokegold.gbc --symbols pokegold.sym --save-state .local\tmp\bug.state --input-log .local\tmp\bug.inputs --screenshot .local\tmp\bug.png --symptom "NPC freezes after sign text"
python -m tools.debugger investigate --playtest-packet .local\tmp\playtest_packet.json
python -m tools.debugger triage --changed-file engine\battle\late_gen_held_items.asm
python -m tools.debugger triage --symptom "boss selected the wrong switch"
python -m tools.debugger gate --changed-file engine\battle\late_gen_held_items.asm
python -m tools.debugger gate --changed-file engine\battle\late_gen_held_items.asm --execute --max-commands 2
python -m tools.debugger investigate --trace audit\boss_ai_debugger\rom_contribution_trace_smoke.json --symbol BossAI_ApplyMoveModel --address D0D3 --watch-size 1 --expect "event=score_delta,symbol=wEnemyAIMoveScores"
python -m tools.debugger investigate --patch wTypeMatchup=0 --watch-symbol wEnemyAIMoveScores --symptom "AI chose a Ground move into immunity"
python -m tools.debugger localize --symbol wCurDamage --address D141 --watch-size 2 --symptom "damage spike"
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
python -m tools.debugger minimize --report .local\tmp\debugger_state_space.json --expect "event=watch_change,address=D141" --execute-state-patches --out-state-report .local\tmp\debugger_state_space_minimized.json
python -m tools.debugger trace-instructions --report .local\tmp\debugger_watch_smoke.json --execute --require-hit --out-trace .local\tmp\watch_instruction_trace.jsonl
python -m tools.debugger trace-instructions --symbol BattleCommand_DamageCalc --watch-symbol wCurDamage --execute --require-hit --out-trace .local\tmp\damagecalc_instruction_trace.jsonl
python -m tools.debugger effect-trace --trace .local\tmp\damagecalc_instruction_trace.jsonl --watch-symbol wCurDamage --out-effects .local\tmp\damagecalc_effects.jsonl
python -m tools.debugger reverse-query --report .local\tmp\damagecalc_effect_trace.json --symbol wCurDamage
python -m tools.debugger dynamic-taint --report .local\tmp\damagecalc_effect_trace.json --source-reg a=move_power
python -m tools.debugger dynamic-taint --trace .local\tmp\instruction_trace.jsonl --source-reg a=move_power --sink-symbol wCurDamage
python -m tools.debugger dynamic-taint --report .local\tmp\damagecalc_instruction_trace.json
python -m tools.debugger setup --symbol wCurDamage --watch-symbol wCurDamage --watch-address D141 --watch-size 2 --out-scenarios .local\tmp\debugger_setup_scenarios.jsonl
python -m tools.debugger generate --symbol wCurDamage --out-scenarios .local\tmp\debugger_generation_seeds.jsonl
python -m tools.debugger generate --changed-file engine\battle\ai\boss_policy_move.asm --family all --max-cases 64 --seed 1
python -m tools.debugger provenance --symbol wCurDamage --symbol BattleCommand_DamageCalc
python -m tools.debugger provenance --source-file engine\battle\effect_commands.asm
python -m tools.debugger causal-graph --report .local\tmp\damagecalc_effect_trace.json --report .local\tmp\dynamic_taint.json
python -m tools.debugger slice --symbol wCurDamage
python -m tools.debugger slice --source-file engine\battle\effect_commands.asm --depth 3
python -m tools.debugger watch --watch-symbol wCurDamage
python -m tools.debugger watch --watch-address D141 --watch-size 2
python -m tools.debugger watch --rom pokegold_trace.gbc --symbols pokegold_trace.sym --save-state path\to\state --watch-symbol wEnemyAIMoveScores --execute --context-frames 24
python -m tools.debugger replay --rom pokegold.gbc --symbols pokegold.sym --save-state path\to\state --watch-symbol wCurDamage --execute-watch --context-frames 24
python -m tools.debugger replay --watch-address D141 --watch-size 2 --execute-watch
python -m tools.debugger replay --watch-address D141 --watch-size 2 --symbol BattleCommand_DamageCalc --execute-trace
python -m tools.debugger replay --report .local\tmp\debugger_watch_smoke.json --trace audit\boss_ai_debugger\rom_contribution_trace_smoke.json --symbol BossAI_SelectMove
python -m tools.debugger explain --report .local\tmp\debugger_replay_boss_ai.json --symbol BossAI_SelectMove
python -m tools.debugger explain --report .local\tmp\debugger_watch_smoke.json --watch-symbol wCurDamage --symptom "damage changed unexpectedly"
python -m tools.debugger suggest-tests --changed-file engine\battle\late_gen_held_items.asm
python -m tools.debugger suggest-tests --symbol BossAI_SelectMove --symptom "bad switch choice"
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
python -m tools.debugger selftest
python -m tools.debugger selftest --component capability_audit --json
python -m tools.debugger hypothesis add --symptom "physical damage 5x too high" --claim "AG-NN c-mirror suspected" --confidence judgment
python -m tools.debugger hypothesis list --refresh-citations
python -m tools.debugger hypothesis show <id>
python -m tools.debugger save-state-lab inspect <state>
python -m tools.debugger save-state-lab diff <a> <b>
python -m tools.debugger bisect --good <known-good-commit> --bad HEAD -- python tools/audit/check_release_smoke.py
python -m tools.debugger session-start
python -m tools.debugger session-start --json
python scripts\emit_bgb_sym.py --symbols pokegold.sym --out pokegold.bgb.sym
python scripts\emit_wram_map.py --symbols pokegold.sym --out pokegold.map.txt
python tools\audit\check_bgb_sym_parity.py --symbols pokegold.sym --bgb-symbols pokegold.bgb.sym
make bgb_sym
```

Omni-debugger v2 surfaces (`session-start`, `hypothesis`, `selftest`,
`save-state-lab`, `bisect`) are passthrough subcommands — the
top-level CLI strips the subcommand name and hands the remaining argv
to the module's own parser. So `python -m tools.debugger bisect --help`
shows the bisect module's help, and the module-level CLI
(`python -m tools.debugger.bisect ...`) keeps working unchanged. The
v2 surfaces are reported as a separate `v2_surfaces` section in
`python -m tools.debugger audit` output and do NOT count toward the
v1 readiness gate (see `docs/omni_debugger_v2.md`).

For a fresh session, `python -m tools.debugger session-start` is the
recommended first call — it composes the selftest health check,
open hypothesis tree, recent commits, and working-tree summary into
one bounded readout.

`make bgb_sym` exports `pokegold.bgb.sym` plus `pokegold.map.txt` from the
current RGBDS linker symbols. Load `pokegold.bgb.sym` as the matching ROM symbol
file in BGB or Emulicious, then use `pokegold.map.txt` as the compact SRAM,
WRAM, and HRAM label reference when comparing emulator debugger state to
`tools.debugger` reports. `python tools\audit\check_bgb_sym_parity.py` verifies
that the exported emulator symbols preserve every label from `pokegold.sym`.

Current mature subsystems:

- `tools.boss_ai_debugger`: Boss AI policy, traces, ROM materialization,
  generated scenarios, review queues, and changed-AI gates.
- `tools.damage_debugger`: damage-chain ROM-vs-oracle fuzzing, clobber smoke,
  replay, taint, coverage, and Tenet export.
- `tools.trace`: PyBoy runtime helpers, trace capture, symbol parsing, and
  save-state replay plumbing.
- `tools.audit`: static and release smoke gates.

`ingest` writes a generic manifest for ROMs, symbol files, trace text, save
states, input logs, generated scenario JSON/JSONL, and source-change paths. The manifest
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

`capture-playtest` creates a handoff packet for a playtest symptom. It records
ROM, symbol file, save state, input log, screenshot, traces, reports, scenarios,
changed files, suspect symbols, watch symbols, raw addresses, notes, hashes, and
the exact follow-up commands for `investigate`, `rank`, `impact`, `report`,
`effect-trace`, and `reverse-query`. The packet is intentionally `planned_only`
proof: it packages evidence and makes the next debugger step reproducible, but
runtime proof still comes from replay/watch/trace/effect/mirror reports.
`investigate --playtest-packet` consumes that packet directly: it carries over
the packet symptom, ROM/symbol/save-state/input-log paths, traces, reports, scenarios,
changed files, symbols, watch symbols, and raw addresses. Relative artifact
paths are resolved against the packet's recorded root, so packets captured in a
workspace with spaces in the path can be handed to another command without
turning the symbol file itself into a suspect symbol.

Text input logs can be replayed by the generic `watch`, `trace-instructions`,
and `replay --execute-*` paths. Supported lines are one step each: `A`,
`LEFT+START`, `WAIT 30`, or `A 8` for a held press. Playback is deterministic
PyBoy button input for this debugger format, not a full emulator movie format.

`investigate` is the one-command ROM debugging packet for this worktree. It
ingests the supplied ROM/symbol/trace/save-state/scenario/source-change inputs,
turns any explicit `--patch SYMBOL=VALUE` WRAM hypotheses into a generic
state-space report, then runs trace indexing, replay planning, localization,
coverage, causal explanation, mirror routing, optional expectation checks, counterexample
generation, minimization, ranking, impact scoring, static reporting, and
visualization into a single output directory. It is the command to start with
when a symptom has evidence but the next debugger step is unclear. A pass means
the packet was internally consistent and any supplied expectations passed; it is
only a bug proof when the included evidence is ROM-backed. Explicit `--address`
inputs are also threaded into the replay packet as raw watch addresses, using
`--watch-size` when a multi-byte watched value matters. Explicit or packet-derived
input logs are parsed into the replay packet and played before each frame tick
when runtime watch or instruction tracing is executed.
When `--execute-attribution` captures a fresh instruction trace, investigation
also executes the hook-order probe first so read-modify-write byte attribution
is tied to a runtime-observed pre-instruction hook timing check.

`localize` combines symptoms, source changes, symbols, and existing unified JSON
reports into a prioritized debugging plan. It scores likely symbol, source-file,
and raw-address suspects, folds in static slices, watch hits, trace-index
reverse attributions, expectation failures, raw address evidence, and
minimized-trace handoffs when available, then lays out reproduce, observe,
slice, compare, minimize, and verify phases with the commands that can prove or
reject each suspect. Explicit `--address` inputs become raw replay/watch
commands, report-derived raw address candidates preserve discovered watch width,
and addresses that resolve through `.sym` also seed symbol slicing.

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
instruction transfer model used by the damage debugger. It also consumes
`effect-trace` reports directly: observed source operands from CPU-visible
memory/stack/IO writes become dynamic write attributions, and supplied source
seeds turn those writes into taint paths without requiring the original JSONL
trace to be passed again. It accepts register, memory, or symbol seeds and
reports which dynamic writes to sink symbols or addresses are tainted, with
path evidence that downstream `rank`, `impact`, `localize`, `report`, and
`visualize` understand. `--report` can load an
instruction-trace or minimization report, discover written trace artifacts,
watched sink symbols, and optional `dynamic_taint_sources` metadata, then run the
same taint/write-attribution engine without manually copying trace paths and
sinks. Even without explicit source seeds, it emits `write_attributions` for
exact sink-writing instructions, including the source operands visible in the
trace, so impact/ranking can carry instruction-level reverse evidence before the
final source seed is known. Direct instruction-trace write attribution includes
ordinary memory writes plus stack writes from taken calls, `rst`, and `push`,
and carries the modeled byte value plus value source when the instruction frame
has enough pre-state evidence. Stack-corruption suspects can be localized
without first converting the trace to an effect report. This is the unified bridge for
emulator-trace-backed causality. When no trace artifact is available but a
report exposes watched sinks, raw sink addresses, or state patches,
`dynamic-taint` now emits a `trace_synthesis_plan` that routes through
content-state/state-space materialization when needed, captures an instruction
trace with `--require-hit`, and feeds the resulting trace report back into
`dynamic-taint`. With `--execute-synthesis`, those planned routes are run for
the supported content-state/state-space surfaces and the generated trace is
consumed in the same report. Report-discovered raw address sinks preserve their
declared watch size, so a two-byte sink such as `D141` keeps `--watch-size 2`
on the generated instruction trace and `--sink-size 2` on the follow-up taint
command. Ranked, impact, and other handoff reports can also supply
`related_addresses` or state-like `related_symbols`, with nested
`sink_size`/`watch_size` kept for raw addresses, letting a prioritized finding
route directly into trace capture and taint without manually restating the sink.
Raw addresses are parsed through a shared address helper that keeps CLI-safe
forms (`D141`, `01:D141`) separate from evidence forms (`$D141`, `01:$D141`)
and records `space`, `bank`, `address_hex`, and a bank-aware `key` in
`source_address_specs` and `sink_address_specs`; `$D141` and `01:$D141` no
longer collapse into the same debugger identity even when the current taint
engine still matches observed CPU writes by 16-bit bus address.
Generic reports can also name arbitrary output sinks through `outputs`,
`output_symbols`, or `output_addresses`; those outputs become dynamic-taint
sinks, preserve output size, and feed trace synthesis from any discovered save
state plus producer/source symbols in the same report.
When a supplied report already names an existing save state, the
synthesis route marks that state as ready and passes it explicitly to
`trace-instructions`; materialization-planned routes pass the newly generated
state to the trace step. It still needs a generated trace window before it can
claim byte-level taint paths.
Dynamic write paths and attributions for raw sinks keep address evidence as
addresses and emit `trace-index --address`, `localize --address`, and
`replay --watch-address` follow-ups instead of treating `D141`-style targets as
symbols. Multi-byte raw sinks include `--watch-size` on replay and localization
follow-ups.

`trace-instructions` creates that dense trace window. It disassembles selected
function symbols from the current ROM and `.sym`, or derives likely hook windows
from watch reports, trace reports, content-scenario runtime targets,
content-state materializations, changed source labels, and symptoms;
`--scenario-id` narrows content-scenario or content-state reports to a single
generated case. When a loaded content-state report was executed and its
`out_state` exists, or when a watch/replay-style report exposes an existing
save state, `trace-instructions` reuses that state automatically unless
`--save-state` was supplied. It plans a hook for every decoded SM83 instruction,
and with `--execute` records opcode, operand, PC label, registers, and watched
symbol or raw-address state before each executed instruction. Its
`execution_validation` block reports which selected hooks
actually fired, which planned routines were missed, and whether the captured
trace is ready to feed `dynamic-taint`; `--require-hit` turns an empty executed
window into a failing proof step. The output JSONL is designed to feed
`dynamic-taint`, `trace-index`, `expect`, and `minimize`. This gives the
unified debugger a capture path for instruction-level causal evidence without
requiring every subsystem to invent its own trace format.

`effect-trace` turns dense instruction traces into a bounded side-effect log.
It records opcode fetches, CPU-visible memory reads and writes, stack
push/pop/call/ret traffic, IO loads/stores, control-flow effects, watch hits,
common hardware side-effect triggers, pre-instruction register/watch snapshots,
value-source labels for observed-memory bytes versus modeled write results, and
a last-writer/read-history index per bus address. When the next captured
instruction frame observes the same written byte, the effect is annotated with
whether the modeled value matched that next pre-instruction snapshot. Adjacent
captured frames that show an observed watched byte changed without any modeled
write in the prior frame are reported as unattributed observed changes instead
of being indexed as known writers. Hardware trigger records cover
OAM DMA starts, MBC bank writes, WRAM/VRAM bank-select registers, and common
PPU/audio/timer/interrupt register writes, with source operands, trigger
addresses, and the sampled pre-state preserved for causal graph handoffs.
Observed OAM DMA starts are expanded into modeled `dma_read` and
`dma_write` effects for the 160-byte transfer, so reverse queries can answer
which instruction caused an OAM byte write; when the trace frame includes
runtime bank state, banked ROMX, WRAMX, and SRAM DMA source reads keep
bank-aware address keys and SRAM-enable evidence. Adjacent PC/SP trace frames
at interrupt vectors are expanded into trace-proven interrupt-entry stack
writes, so reverse queries can identify the pushed return address bytes. It can
write the event stream as JSONL with `--out-effects`. This is not full reverse
execution yet: PPU pixels, mixed audio, and timer ticks still require richer
emulator-backed capture unless those effects are present in the captured
instruction window. It is the first shared effect-store layer for reverse
queries such as "who last wrote D141?".

`reverse-query` consumes effect-trace reports or dense instruction traces and
answers direct state questions by symbol or address. It returns the matching
address index entry, read/write history, last writer sequence, last writer PC,
source operands when present, and follow-up trace-index/dynamic-taint commands.
It can synthesize an effect trace from `--trace` inputs, or reuse an existing
`--report <effect-trace.json>` packet when playtest triage has already captured
one.

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
With `--execute-state-patches`, content-state and explicit generic state-space
patch candidates are materialized through PyBoy before the minimizer accepts
them, so expectations such as `applied=true,verified=true` are checked against
an actual patched save state. If those executed candidates are gated by event or
value expectations, the minimizer now reruns watch replay from each candidate
save state and evaluates the expectation gate over that fresh runtime evidence
before accepting a removed patch. Every executed candidate also gets a replay
packet rebuilt from that candidate save state, so subsequent replay, trace,
impact, and compare work follows the minimized state instead of the original
unreduced report. Address-only expectations such as
`event=watch_change,address=D141` rerun raw `--watch-address` probes, so patch
reduction is not blocked on a `.sym` label for the affected byte.
Watch/replay reports keep only the relevant events and trim nested
dynamic-context frame windows to the smallest useful causal context, giving
every ROM surface a compact repro artifact before a surface-specific reducer
exists. With `--execute-semantic-reducers`, candidate state-patch removals that
still satisfy the expectation gate are written to bounded temporary reports and
run through the inferred semantic reducers under `--max-semantic-reducer-commands`;
the final minimized report uses any remaining command budget. It is the unified
coordinator; full semantic behavior reduction still depends on the depth of the
owning ROM surface's emulator-backed reducer.

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
Boss AI generated-policy scenarios, banking/ABI state-space probes,
content/static invariant checks, map content positioned-state materialization, and the
downstream minimization, mirror, materialization, impact, and report commands
needed to prove a bug. Ready instruction-trace reports are now routed directly
to `dynamic-taint --report ...` handoffs, so captured execution can feed
source-to-sink attribution without manually copying trace paths and watched
sinks. With `--out-scenarios`, it writes a deterministic JSONL seed manifest
for the unified debugger workflow. Map content seeds that carry state
preconditions now include `materialization_request` records that write a
`content-state` report/state and replay it; banking seeds include
`state_space_request` records that patch the real `hROMBank` and `wFarCallBC`
symbols, replay the patched state, trace `FarCall`/`FarCall_hl`/`Bankswitch`,
and hand the trace report to dynamic taint. UI/tilemap source changes now
generate output-sink scenarios for `wTilemap`, `wAttrmap`, `hBGMapMode`, and
`hBGMapAddress`, so replay, instruction tracing, and dynamic taint can follow
the drawing helper that changed visible screen state. Other surfaces remain handoff
records until their dedicated ROM materializers exist. With `--execute`,
`generate` and `fuzz` run a bounded prefix of their runnable proof commands and
record pass/fail/skipped status in the JSON; without it they remain planners.

`setup` is the bridge between “this symbol/file/report looks relevant” and
“here is how to reach it in the ROM.” It infers the affected surface, then emits
the scenario generation, `state_synthesis_recipes`, subsystem materialization,
save-state/replay, watch, and `trace-instructions --require-hit` validation
commands needed before a runtime claim should be treated as proof. Damage and
Boss AI setup can hand off to mature materializers; content setup creates
semantic scenario manifests, concrete trigger precondition records, and runtime
helper/watch replay routes for maps, scripts, graphics, and audio; banking
setup now includes both audit/watch probes and the same hROMBank/wFarCallBC
state-space plus FarCall/Bankswitch trace route used by generation and fuzzing.
UI output scenarios expose tilemap/attrmap output sinks that route through
content-state, replay, instruction tracing, and dynamic-taint synthesis.
General setup routes through audits, watches, and targeted replay.
Its `trigger_coverage` block grades each target as covered, planned, or blocked
and names the missing piece, such as a concrete scenario ID, supplied save
state, or validation expectation. If loaded scenarios or reports already name a
concrete `state`, `save_state`, `pre_choice_state`, or materialization-state
path, setup discovers it, prefers requested scenario IDs, and threads that state
into replay and instruction-trace commands. When no concrete state is available,
the recipe block shows the exact state factory, materializer, or watch/probe
commands to run next. It plans setup and trigger work; it does not yet synthesize
every arbitrary save state itself. Explicit `--watch-address` targets and
report-derived raw addresses are preserved through setup signals, replay
commands, watch commands, and instruction-trace validation commands.

`fuzz` turns inferred surfaces into concrete fuzz campaigns. Damage and Boss AI
campaigns route to the mature dynamic fuzzers/generators; banking campaigns add
dynamic `hROMBank`/`wFarCallBC` state-space mutations, replay/watch commands,
FarCall/FarCall_hl/Bankswitch instruction tracing, and dynamic-taint handoff
commands; content/static campaigns infer
source-expectation cases and runtime probe routes from labels and macros such
as `warp_event`, `object_event`, `hlcoord`/`decoord` UI drawing helpers, and
`INCBIN`. Ready instruction-trace reports
become `dynamic_trace` fuzz campaigns and `dynamic_taint_handoff` cases. With
`--out-cases`, it writes a deterministic JSONL fuzz-case manifest that can be
fed back into `expect`, `compare`, `suggest-tests`, `generate`, `localize`,
`rank`, `impact`, `report`, and `visualize`. Content fuzz cases preserve the
originating scenario's runtime targets, behavioral probes, state preconditions,
and related helper/watch symbols, so replay, setup, localization, coverage,
ranking, impact, reporting, expectation checks, and visualization can follow
script, map, movement, audio, and asset cases without losing the ROM proof
route. Audio, asset-loader, and UI/tilemap cases also carry `outputs` records
for watched engine/request/screen-state sinks, allowing
`dynamic-taint --report <content-state-or-fuzz-report>` to synthesize the
needed trace route. Static fuzz cases prove source invariants, not runtime behavior, until
paired with replay or dedicated materialization.

`provenance` joins the current `.sym` file with source labels and references.
It can show where a watch symbol or routine lives, which source files mention
it, and which subsystem debugger commands are most likely to be useful. This is
static provenance; dynamic proof still comes from replay, trace, taint, and
subsystem-specific materialization tools.

`causal-graph` normalizes watch, effect-trace, reverse-query, dynamic-taint,
causal-explanation, provenance, ranked, impact, and raw trace evidence into a
single typed node/edge graph. Nodes and edges keep source reports, related
symbols/files/addresses, evidence snippets, and explicit proof statuses, so
planned-only routes stay visibly separate from runtime, instruction, and taint
proof. The graph emits top causal paths plus follow-up `rank`, `visualize`,
`report`, `provenance`, `explain`, `reverse-query`, and `effect-trace`
commands.

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

`watch` is the generic runtime bridge. In plan mode it resolves watch symbols or
raw watch addresses, attaches static provenance for symbols, and reports the
debugger commands likely to help. In `--execute` mode it opens the ROM in PyBoy,
optionally loads a save state, polls the watched symbols or addresses for a
bounded number of frames, and records changes with watched bank/address, PC
bank/address, nearest symbol context, register snapshots, watch values, and the preceding
`--context-frames` frame-context window. Each hit also carries a bounded
source-cause slice when symbol context exists, so the watch output points at
likely static writers/readers and the follow-up `trace-index`, `slice`,
`explain`, `localize`, and `minimize` commands. It is frame-sampled forward
polling, not hardware watchpoints, instruction-by-instruction dynamic taint, or
reverse execution.

`replay` is the unified reproduction coordinator. It fingerprints the ROM,
symbols, traces, save states, scenarios, and changed files you give it; derives
watchable RAM targets, raw watch addresses, and suspect labels from traces and
existing debugger reports; then emits a repeatable workflow for setup/trigger
materialization, watch replay, localization, coverage proof, generic trace
minimization, subsystem minimization, mirror comparison, impact ranking, report
rendering, and final gates. Explicit `--watch-address` inputs and report-derived
`related_addresses`, `watch_addresses`, `sink_addresses`, watch fields, and
dynamic write addresses become replay `watch_addresses`, `watch --watch-address`
commands, trace-instruction watch-address handoffs when a hook source is
available, and minimized trace address expectations. It now runs the setup
planner internally, passes raw watch addresses into setup, reuses
scenario/report save-state discovery, and threads an existing discovered state
into watch and instruction-trace commands so ROM proof starts from the concrete
scenario state when one is available. Report-derived `watch_size`/`sink_size`
values keep multi-byte raw watches from being narrowed to one byte. With
`--execute-watch`, it runs the generic PyBoy watch bridge and embeds the enriched
watch report, including dynamic context windows, in the replay plan. With
`--execute-trace`, it also runs the selected instruction-trace handoff from the
same effective save state, requires at least one selected hook hit, writes
`.local\tmp\debugger_replay_instruction_trace.jsonl`, and embeds the trace
validation report for dynamic-taint follow-up.

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

`suggest-tests` maps changed files, symbols, and symptoms to this repo's
existing fuzzers, generators, metamorphic checks, coverage reports, and
counterexample/minimization commands. It is the lightweight registry layer used
by `generate`; surfaces without dedicated generators still report static
fallback gates and notes.

`compare` declares which mirrors/oracles can check a surface. It distinguishes
damage's ROM-vs-oracle checks, Boss AI's Python policy/differential plus ROM
materialization checks, static content/source expectation checks, and
content-state behavioral mirror reports. With `--report <content_state.json>`,
it turns WRAM map-position patches into `state-patch` expectation commands plus
replay/watch proof routes from the generated state report. Output-sink
content-state reports for UI, graphics, audio, and asset loaders are now
classified as `planned`, `partial`, or `passed`: supplied runtime evidence from
watch, replay, effect traces, instruction tracing, dynamic taint, or executed
content-state materialization can promote an output-sink mirror to
`mirror_passed` when every requested output sink is observed. It prints both
quick compare commands and the materialization/proof commands needed before
treating a result as ROM behavior. If an expectation report is supplied with
executed runtime evidence from watch, replay, instruction tracing, dynamic
taint, or content-state materialization, `compare` promotes it to a
`runtime_expectation_dynamic_mirror`, so any ROM surface can present a single
execution-backed expectation mirror instead of leaving runtime proof scattered
across separate reports.

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
materialization checks, audio channel headers, and audio note/command streams.
The JSONL output
feeds `generate`, `fuzz`, `replay`, `minimize`, `rank`, `impact`, `report`, and
`visualize`. Each scenario now carries `runtime_targets` for source labels,
script labels, event-engine or loader trace helpers, and map/script/movement/audio/asset
watch symbols, `state_preconditions` for the map/script/movement/audio/asset state that
must be loaded or synthesized before emulator proof, plus `behavioral_probes` that route
the case through content mirrors, concrete `expect` assertions, replay/setup,
coverage, comparison, provenance, runtime trace/watch planning, content-state
execution, positioned-state replay, positioned-state instruction tracing, and
minimization. These cases say exactly what map trigger, script entry, movement
stream, asset, audio header, or audio command stream to exercise; map, script command-stream, and
movement-data scenarios can now be converted into replayable WRAM-patched
states, while audio and asset cases emit explicit PlayMusic/graphics-loader
trace/watch and output-sink taint proof routes until they have dedicated state
builders.
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
(`wMusicID`, `wMusicBank`, channel flags, and 1bpp/2bpp request queues), audio
hardware register watch addresses (`rAUD*`), declared output sinks, helper trace
commands, and dynamic-taint followups, but they remain non-executable until an
owning caller or save state is supplied.
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
dynamic-taint handoffs instead of being buried as generic trace events; raw
address handoffs preserve sink width from trace validation, watch records, or
top-level `watch_size`/`sink_size` fields. Ranking
preserves related symbols, related files, and raw address-only evidence, so
reports that watch `D141` or attribute a write to an address do not have to
pretend that address is a symbol. Dynamic-taint paths and dynamic write
attributions both carry those raw addresses through ranking and impact scoring.
Content scenarios preserve runtime targets, state-precondition watches, and
behavioral probe routes as related evidence, so audio, movement, script, and
map scenarios stay tied to the symbols/files that can replay or observe them.
Every ranked finding carries an explicit `proof_status` such as
`planned_only`, `state_materialized`, `runtime_observed`,
`instruction_observed`, `taint_proven`, `mirror_passed`, or `mirror_failed`;
planned-only findings are intentionally demoted so routes to gather proof do not
look equivalent to observed ROM behavior.
It also applies a small ROM-surface
calibration for banking/ABI, battle damage, battle mechanics/items/hazards, Boss
AI, event scripts/maps, movement/text, graphics/audio/UI, and Pokemon/move-data
evidence so equally severe findings on riskier ROM surfaces sort predictably.

`impact` turns ranked findings, coverage gaps, localization candidates,
minimization routes, watch hits, gate failures, explicit changed files, suspect
symbols, symptom text, instruction-trace validation state, and content-state
ready/blocked/executed materialization reports into one ROM-aware priority
queue. It scores each item by failure severity, proof evidence, runnable next
commands, and the likely project surface affected: banking/ABI, battle damage,
Boss AI, battle core, Pokemon/move data, maps/scripts/text, graphics/audio/UI,
or debugger tooling. It also exposes a deterministic semantic risk profile for
ROM-backed runtime evidence, failed contracts, memory-safety/banked-call risks,
battle hazards/items/passives/status, progression content, and balance-data
surfaces, including replay/watch/trace/materialization routes and
script/movement/audio/UI runtime content. Evidence-backed calibration profiles
then make subsystem differences explicit for banking/ABI,
battle mechanics/items/hazards, maps/scripts/text, graphics/audio/UI, and
Pokemon/move data without promoting path-only guesses as proof. If a supplied
`unified_debugger_impact_feedback` report records confirmed playtest or
debugging outcomes, `impact` applies those learned priors only to matching
surface plus file, symbol, item type, or semantic-factor evidence. This is the command to use when
several debugger reports exist and the next question is which suspected bug can
hurt the romhack most and how to prove it.
Address-only watches and dynamic write attributions keep their watched/written
addresses as first-class `related_addresses` fields for later workflow handoff.
Impact reports also summarize `proof_status_counts` so a triage packet shows how
much of the queue is planned, materialized, observed, tainted, or mirror-backed.

`report` renders one or more unified JSON reports into a static Markdown or HTML
summary for a debugging run. It keeps the raw JSON as the source of truth, then
extracts the highest-priority findings, input report status, gaps, issues, and
follow-up commands so a romhack debugging session can be scanned without reading
every JSON file by hand. Findings and candidates now print raw
`related_addresses` and semantic impact factors beside symbol/file evidence, so
address-only watch, dynamic-write proof, and playtesting risk rationale remain
visible in handoff reports. Static reports include a Proof column and a
proof-status count summary for the normalized findings.

`visualize` renders one or more unified reports and traces into a visualization
packet. It builds a timeline of runtime/watch/trace/coverage/content/
content-state patch/instruction-trace validation/impact events, a workflow
waterfall from replay/localization/minimization/gate/materialization/
instruction-trace steps, a causal graph from explanation/slice/coverage/content/
content-state/instruction-trace artifacts, Mermaid timeline and graph blocks,
sampled emulator frame tables, and Markdown or HTML output. HTML output includes
a generic canvas inspector for emulator/watch/replay/instruction samples that
carry PC, register, watch-value, screenshot, framebuffer, or tilemap evidence.
Ranked findings, impact items, watch hits, trace
observations, and dynamic write attributions carry raw address evidence into
timeline `addresses`, graph address nodes/edges, semantic impact detail, and the interactive inspector.
HTML output includes a self-contained interactive evidence inspector with
search, lane/source filters, severity filtering, address columns, and graph-edge
tables. It is the unified view for scanning a debugging run; full
emulator-coupled canvas/TUI inspectors are still a future layer.

The whole-ROM goal means this romhack's ROM and source surfaces, not arbitrary
unrelated Game Boy games. `audit` should stay honest: until every relevant
project surface has generic ingest, replay, causal provenance, counterexample
generation, mirror comparison, impact ranking, reporting, and workflow
automation, it must report `ready=False`.
