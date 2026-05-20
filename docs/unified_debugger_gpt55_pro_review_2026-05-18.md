# Unified Debugger GPT-5.5 Pro Review Return - 2026-05-18

Source: GPT-5.5 Pro review requested by the user on May 18, 2026.

Packet reviewed:

- `C:\Users\lolno\Downloads\debugger_gpt55_pro_packet_2026-05-18`
- `tools/debugger/address.py`
- `tools/debugger/workflow.py`
- `tools/debugger/instruction_trace.py`
- `tools/debugger/hook_order.py`
- `tools/debugger/effect_trace.py`
- `tools/debugger/dynamic_taint.py`
- `tools/debugger/reverse_query.py`
- `tools/debugger/causal_graph.py`
- `tools/debugger/playtest_packet.py`
- `tools/debugger/tests/test_catalog.py`

Local status at time of review request:

- `python -B -m unittest discover tools\debugger\tests` passed 356 tests.
- `python -m tools.debugger audit` reported `ready=False`, with 7 complete, 4 partial, 0 missing, and 4 blocking gaps.
- The active debugger goal remains incomplete.

Important interpretation rule: this file preserves external review guidance. Treat each item as a hypothesis or recommendation until local source, tests, traces, or audits confirm it.

## Bottom Line

Keep `ready=False`.

The debugger is much stronger than a generic trace/search workflow, but the remaining high-risk area is proof promotion at subsystem boundaries. Reverse query, dynamic taint, effect trace, and causal graph can look authoritative, so the dangerous failures are silent promotions from "same 16-bit bus address in a bounded trace window" to "exact banked causal writer."

The key next correction is to make bank/address precision and proof status first-class in every report, result, path, and graph edge. Existing `known_limits` are honest, but some structures can still collapse caveats when producing reverse-query results, dynamic-taint paths, graph nodes, or ranked findings.

## Highest-Priority Findings

1. Banked symbol reverse-query fallback can identify the wrong last writer.

Files/functions to inspect:

- `tools/debugger/reverse_query.py`
- `matching_write_index_entries()`
- `target_requires_exact_key()`

Risk: a banked symbol such as `02:D141 wBank2Damage` may fall back to a wrong unbanked or wrong-bank `D141` writer if exact `address_key` matching fails. Banked symbols should require exact key matching just like raw banked addresses.

Suggested test: `test_reverse_query_banked_symbol_does_not_fallback_to_unbanked_bus_key`.

Expected behavior: no exact result, or an explicitly downgraded `match_precision="bus_address_unverified_bank"` result. Do not mark as `instruction_observed`.

2. Reverse query can claim `instruction_observed` from `write_count` alone.

Files/functions to inspect:

- `tools/debugger/reverse_query.py`
- `reverse_query_proof_status()`
- `result_has_observed_write()`
- `result_proof_status()`

Risk: `write_count > 0` can promote proof even when there is no concrete `last_write` history/event object. This can conflict with validation that says `no_observed_write`.

Suggested test: `test_reverse_query_write_count_without_history_is_not_instruction_observed`.

Expected behavior: compact index counts without concrete write evidence should be invalid, `planned_only`, or `index_incomplete`; they should not become `instruction_observed`.

3. `bounded_replay_validation()` is named too strongly.

File/function:

- `tools/debugger/reverse_query.py`
- `bounded_replay_validation()`

Risk: current logic appears to validate consistency across the modeled effect stream, not restore an emulator checkpoint and replay CPU semantics. The term "replay" can overstate proof.

Suggested patch: rename or split into:

- `bounded_effect_span_validation` for current modeled-effect consistency.
- `checkpoint_emulator_replay_validation` only for actual emulator-backed replay.

Suggested test: `test_reverse_query_bounded_replay_does_not_claim_emulator_replay`.

4. Dynamic taint likely has the same banked-symbol looseness as reverse query.

Files/functions to inspect:

- `tools/debugger/dynamic_taint.py`
- `annotate_sink_address_specs()`
- sink/source matching and path proof promotion

Risk: a single banked sink symbol may be treated as a bus-address sink if no duplicate banked symbol exists. A taint path to a banked symbol should not become `taint_proven` from unbanked bus evidence.

Suggested test: `test_dynamic_taint_banked_symbol_sink_unverified_bus_match_not_taint_proven`.

Expected behavior: bank-unverified bus matches should carry `match_precision="bus_address_unverified_bank"` and proof no stronger than unverified observation.

5. Stack effects may lose WRAMX bank precision.

File/functions:

- `tools/debugger/effect_trace.py`
- stack effects for push/pop/call/ret/rst/interrupt entry
- any bank-state attachment helper

Risk: stack addresses in `D000-DFFF` are WRAMX and need runtime WRAM bank qualification. If only normal memory effects get bank keys, stack effects can collapse to bus-address-only evidence.

Suggested test: `test_effect_trace_banks_stack_writes_when_sp_in_wramx`.

Expected behavior: stack writes with `SP` in WRAMX and `bank_state={"wram": 3}` should carry exact banked keys such as `wramx:03:DFEE` and an explicit bank source.

6. SM83 effect/register modeling still misses important write classes.

Risk areas:

- `ld a,[hli]`, `ld a,[hld]`, `ld [hli],a`, `ld [hld],a` should write back `HL`.
- 16-bit `inc/dec bc,de,hl,sp` should write register pairs.
- `add hl,rr`, `add sp,e8`, `ld hl,sp+e8`, `ld sp,hl`.
- CB register operations should produce register writes, not only CB `[hl]`.
- `DAA`, `CPL`, `SCF`, `CCF`, accumulator rotates, and flag writes matter for branches and carry-dependent operations.
- Stack pointer changes from push/pop/call/ret/rst/interrupt should be explicit `SP` register-write effects.

Suggested tests:

- `test_effect_trace_models_hli_hld_hl_register_update`
- `test_effect_trace_models_16bit_inc_dec_pair_update`
- `test_effect_trace_models_cb_register_write`
- `test_effect_trace_models_sp_update_for_call_ret_push_pop_rst_interrupt`

7. Causal graph node merging can make weak evidence look strong.

File/functions:

- `tools/debugger/causal_graph.py`
- node merging and path proof selection

Risk: nodes can be promoted to the strongest proof status seen for that label, even if another source only planned the same target. Edges may preserve truth, but UI/report consumers can overread the node proof.

Suggested tests:

- `test_causal_graph_node_keeps_proof_status_by_source`
- `test_causal_graph_path_proof_does_not_exceed_weakest_required_edge`

Suggested patch: add `proof_status_by_source` and proof summaries on nodes; score causal paths from edges, not node-level max proof.

8. RMW old-byte attribution should carry per-effect hook-order proof.

Files:

- `tools/debugger/hook_order.py`
- `tools/debugger/effect_trace.py`

Risk: hook-order proof is top-level, while individual RMW effects that depend on pre-instruction old-byte sampling should show whether hook-order validation was supplied and passed.

Suggested test: `test_effect_trace_rmw_old_byte_marks_hook_order_unvalidated_without_probe`.

Expected behavior: RMW effects can still be emitted without a hook-order report, but they should carry a downgraded `pre_state_proof_status` or equivalent until validated.

9. Playtest packet route readiness is syntactic, not evidentiary.

File:

- `tools/debugger/playtest_packet.py`

Risk: a route can become `status="ready"` because the command string has no placeholder, even when required artifacts are missing or untrusted.

Suggested test: `test_playtest_route_ready_requires_artifact_existence_and_trust`.

Suggested patch: derive route readiness from command parseability plus required input existence/trust/consistency.

10. Address parsing is shell-safe but not semantically strict enough.

Files:

- `tools/debugger/address.py`
- `tools/debugger/workflow.py`

Risk: shell handling for `$D141` is improved, but semantically impossible or ambiguous banks can still pass as ordinary exact addresses.

Suggested test: `test_address_spec_rejects_impossible_bank_for_space`.

Suggested direction: split user intent from observed evidence with typed `AddressSpec`, `ObservedAddressKey`, `BankState`, exactness, bank validity, and source.

## Missing Tests To Prioritize

- `test_reverse_query_banked_symbol_does_not_fallback_to_unbanked_bus_key`
- `test_reverse_query_write_count_without_history_is_not_instruction_observed`
- `test_reverse_query_bounded_replay_is_effect_span_consistency_not_replay`
- `test_dynamic_taint_banked_symbol_sink_unverified_bus_match_not_taint_proven`
- `test_dynamic_taint_banked_source_collision_is_reported_not_silent`
- `test_effect_trace_banks_stack_writes_when_sp_in_wramx`
- `test_effect_trace_models_hli_hld_register_writeback`
- `test_effect_trace_models_cb_register_ops`
- `test_dynamic_taint_clears_stale_register_on_unmodeled_overwrite`
- `test_causal_graph_shared_node_exposes_proof_by_source`
- `test_causal_graph_path_proof_does_not_exceed_weakest_required_edge`
- `test_playtest_route_ready_requires_artifact_existence_and_trust`
- `test_command_spec_round_trips_powershell_embedded_quote`

## Recommended Next Patch Queue

Must-fix correctness:

1. Make reverse query require exact keys for any bank-qualified target, including symbols.
2. Make reverse-query proof require a concrete write object; do not promote from `write_count` alone.
3. Rename/split bounded replay into modeled effect-span consistency vs real emulator replay.
4. Make dynamic-taint source/sink matching carry `match_precision` and block `taint_proven` on bank-unverified bus matches.
5. Bank-qualify all stack effects in effect traces.

Proof-honesty/reporting:

1. Add `match_precision`, `bank_match`, `bank_source`, and `proof_downgrade_reason` to reverse-query results, dynamic-taint attributions, effect watch hits, causal graph edges, and ranked findings.
2. Add per-target proof status to instruction trace reports.
3. Add per-effect pre-state proof for RMW old-byte attribution.
4. Add `proof_status_by_source` to causal graph nodes.
5. Keep mirror evidence separate from causal proof: `mirror_passed` is expectation consistency, not writer causation.

Architecture:

1. Introduce typed `AddressSpec` for requested addresses and `ObservedAddressKey` for trace-proven addresses.
2. Replace command-string parsing with typed `CommandSpec` that stores argv, rendered command, shell, placeholders, required inputs, expected outputs, and expected proof status.
3. Add a shared `EvidenceAtom` schema for effect trace, reverse query, dynamic taint, causal graph, ranking, and playtest packets.
4. Move SM83 effect modeling toward a table-driven opcode model for reads, writes, register defs, flag defs, SP/PC/IME effects, and hardware triggers.
5. Add a real `BankState` object that distinguishes runtime-observed, inferred-from-IO-write, default, unknown, and mapper-dependent state.

Feature work after correctness/proof fixes:

1. Complete SM83 CPU/effect coverage.
2. Add emulator-backed memory/IO event capture where PyBoy exposes it, especially DMA, interrupts, timer, PPU/audio registers, MBC writes, SRAM enable/bank, WRAM/VRAM bank switches.
3. Build mirror runner statuses: `mirror_passed`, `mirror_failed`, `mirror_inconclusive`, `mirror_not_run`.
4. Add playtest packet minimization for input logs, save-state patches, and trace windows.
5. Generate counterexamples for causal claims, especially last-writer claims that could be falsified by writers outside the observed window.

## Architecture Direction

Do not treat proof status as a single scalar property of a report or graph node. Treat it as a claim-specific proof vector.

Useful proof axes:

- `origin`: planned route, static source, runtime watch, instruction trace, effect model, mirror.
- `observation`: none, runtime state, instruction frame, modeled effect, hardware event, emulator replay.
- `precision`: exact bank key, inferred bank key, unbanked bus address, symbolic only.
- `validation`: none, post-register match, post-memory match, effect-span consistency, emulator replay, mirror pass/fail.
- `scope`: trace source, frame range, instruction sequence range, save-state hash, ROM hash, symbol hash.
- `claim`: written-by, value-came-from, expectation-passed, route-would-produce-evidence, planned target.

Desired future answer shape:

> This symbol is a planned target from the playtest packet, was observed at runtime in a watch report, was written by this instruction in this bounded effect window, has an exact WRAMX bank key from runtime bank state, has a taint path from this source register, and then the visual mirror failed. The script VM mirror was not run.

This is stronger than setting a shared graph node to `proof_status="taint_proven"`.

## Additional Files Requested For Deeper Review

GPT-5.5 Pro requested these additional files for a fully certain review:

- `tools/debugger/provenance.py`, especially `parse_symbol_table()`.
- `tools.damage_debugger.taint`, especially `Sink` and `TaintEngine`.
- `tools/trace/runtime.py`, for PyBoy hook semantics and exposed bank/runtime state.

## Supplemental Review After Extra Files

Source: GPT-5.5 Pro follow-up after reviewing the three additional files above.

Bottom line: the extra files do not weaken the previous review. They make the bank-exactness issue more certain.

### Refined Findings

1. `parse_symbol_table()` is not the problem.

`tools/debugger/provenance.py` preserves symbol-table bank and address fields well enough for downstream debugger tools: `bank`, `address`, `bank_hex`, `address_hex`, and `bank_address` are emitted. A symbol such as `01:D141 wCurDamage` becomes `bank_address="01:D141"` downstream.

The parser is providing static symbol provenance, not runtime bank proof, but it is not dropping the bank. The problem is downstream fallback and proof promotion.

2. Banked symbol reverse-query fallback is now confirmed, not speculative.

`tools/debugger/reverse_query.py` uses a symbol's `bank_address`, parses it into an `AddressSpec`, and labels the target as `type="symbol"`. The reported issue is that `target_requires_exact_key()` only requires exact matching for raw address targets with a bank, not banked symbol targets. Then `matching_write_index_entries()` can fall back to `entry["address"] == target["address_hex"]`, which is only 16-bit bus-address matching.

Expected fix: banked symbols must require exact `address_key` matching just like raw banked addresses.

3. Dynamic-taint bank exactness affects both banked symbol sinks and banked symbol sources.

`tools.damage_debugger.taint.Sink` is only `name`, `address`, and `size`, and `Sink.contains()` is a 16-bit range check. `TaintState.memory` is also keyed by `addr & 0xFFFF`. That may be fine for the older damage-path helper, but it is not sufficient for unified bank-exact provenance.

`tools/debugger/dynamic_taint.py` preserves `AddressSpec` records, but enforcement is incomplete:

- `parse_memory_sources()` collapses source symbols/memory specs to 16-bit addresses.
- `parse_sinks()` collapses sinks to 16-bit `Sink` objects.
- `annotate_sink_address_specs()` only sets `bank_exact_required` for raw banked non-symbol sinks or duplicate banked symbols at the same bus address.
- `sink_matches_effect()` only requires exact key matching when `bank_exact_required` is true.
- `source_origin_for_operand()` avoids fallback for raw banked non-symbol records, but not for banked symbol records.

Risk: a bank-unverified bus match can become `taint_proven` if a banked source or sink symbol is matched by address only.

4. New concrete runtime bug: `tools.trace.runtime.read_word()` appears endian-reversed.

SM83/Game Boy memory words are little-endian. The reviewed helper reportedly computes high-byte-first. It should read low at `address`, high at `address + 1`, and return:

```python
low | (high << 8)
```

This was classified as latent unless current repo callers use `read_word()`, but it is still wrong for a Game Boy runtime helper.

5. Refined HLI/HLD effect-model issue.

The prior broad comment was narrowed: `effect_trace.py` already models memory reads for `ld a,[hli/hld]`, register loads into `A`, and memory writes for `ld [hli/hld],a`.

The remaining missing/risky side effect is the `HL` increment/decrement register write for opcodes `0x22`, `0x2A`, `0x32`, and `0x3A`. That matters for later `[hl]` attribution and taint.

6. New direct-taint correctness issue in the older damage taint engine.

`tools.damage_debugger.taint` reportedly says unsupported opcodes are conservative and clear identifiable destinations, but `TaintEngine.step()` only increments an unsupported counter. It does not clear anything.

Also, `_alu_a()` clears `xor a`, but not `sub a` (`0x97`), even though `sub a` deterministically clears `A`. The newer effect-trace path appears to handle `sub a`; the older direct `TaintEngine` path can falsely retain taint through `sub a`.

### Prior Findings That Still Stand

- Reverse-query proof promotion from summary/index evidence still stands.
- `bounded_replay_validation()` naming still overstates modeled effect-span consistency as replay.
- Causal graph node proof merging can amplify upstream overclaims.

### First Three Patches Recommended By GPT-5.5 Pro

1. Make bank-exact matching mandatory for banked symbols.

Add a shared helper along these lines:

```python
def address_spec_requires_exact_key(record_or_target: dict[str, Any]) -> bool:
    return (
        record_or_target.get("bank") is not None
        and record_or_target.get("space") in {"romx", "vram", "sram", "wramx"}
    )
```

Use it in both reverse query and dynamic taint:

- In `reverse_query.target_requires_exact_key()`, stop checking only `type == "address"`; banked symbols need exact keys too.
- In `dynamic_taint.annotate_sink_address_specs()`, set `bank_exact_required` for all banked specs, including symbols.
- In `source_origin_for_operand()`, do not fall back to bus-address origin for banked symbols. Either exact `address_key` matches or the banked symbol is not a contributor.

Immediate tests:

- `test_reverse_query_banked_symbol_requires_exact_key`
- `test_dynamic_taint_banked_symbol_sink_requires_exact_effect_key`
- `test_dynamic_taint_banked_symbol_source_requires_exact_effect_key`

2. Stop proof promotion from summary/index evidence.

In `reverse_query.py`, make `result_has_observed_write()` true only when there is a concrete `last_writer` or `last_write` item with `access="write"` and PC/seq/address evidence. Do not let `write_count > 0` alone become `instruction_observed`.

Rename or split `bounded_replay_validation()` into modeled effect-span consistency. Suggested statuses: `effect_span_matched` and `effect_span_mismatch`, not `replay_matched` and `replay_mismatch`.

Immediate tests:

- `test_reverse_query_write_count_without_history_is_not_instruction_observed`
- `test_reverse_query_effect_span_validation_not_named_emulator_replay`

3. Fix direct taint and runtime helper correctness bugs.

Fix `tools.damage_debugger.taint.TaintEngine` so `sub a` clears `A` taint just like `xor a`.

More broadly, unsupported known register writers should clear their destination or emit explicit unknown-write evidence; the current docstring promise and behavior should be reconciled.

Fix `tools.trace.runtime.read_word()` to little-endian.

Immediate tests:

- `test_dynamic_taint_direct_sub_a_clears_a_taint`
- `test_trace_runtime_read_word_is_little_endian`
- `test_trace_runtime_wramx_read_restores_ff70`

### Hard Line

The next hard line is bank exactness and proof promotion. Do those before adding more whole-ROM features, because they are the most likely path to the debugger looking like it proved a causal chain when it only matched a 16-bit bus address inside a bounded trace.

## Implementation Note - 2026-05-18

The first hard-line patch set from the supplemental review has been implemented and validated.

Implemented:

- Bank-qualified symbols now require exact bank-aware keys in reverse query and dynamic taint, instead of falling back to 16-bit bus-address matching.
- Dynamic taint now rejects banked symbol source/sink matches unless the instruction frame or effect evidence carries matching runtime bank state.
- Reverse query no longer promotes `write_count > 0` summary/index evidence to `instruction_observed`; it requires a concrete last-write event/history item.
- The former `bounded_replay_validation` report path was renamed to `bounded_effect_span_validation`; matching modeled effects now report `effect_span_consistent`, `consistent=True`, `validated=False`, and `validation_kind=modeled_effect_span`.
- Stack read/write effects are now bank-qualified when `SP` is in banked WRAM and frame bank state is present.
- `tools.trace.runtime.read_word()` now reads SM83 little-endian words.
- `tools.damage_debugger.taint.TaintEngine` now clears `A` taint for `sub a` as well as `xor a`.
- Causal graph nodes now carry `proof_status_by_source` and `proof_summary` so a shared node can show both planned and proven sources instead of only the strongest merged proof status. Visualization preserves that metadata.
- Multi-edge causal paths now carry `proof_vector` and `proof_summary`; their top-level `proof_status` is bounded by the weakest required edge. For example, a register-provenance chain with one `taint_proven` source edge and `instruction_observed` write edges reports the chain as `instruction_observed`, with `proof_summary.max=taint_proven`.
- Playtest packet evidence routes now require inspected artifact availability in addition to shell-runnable command syntax. A route with a real but missing save state path is `blocked` with `missing_required_inputs=["save_state"]`, not `ready`; route availability metadata is ignored by recursive investigation target extraction so booleans like `symbols=True` cannot become fake targets.

Validation run:

- `python -B -m unittest discover tools\debugger\tests` -> 365 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m tools.damage_debugger.taint --self-test` -> PASS.
- `python -m py_compile` on the touched debugger/runtime/taint files -> PASS.
- `git diff --check` on the touched files -> PASS.

Important remaining caveat: the audit still correctly stays `ready=False`. These patches make the current evidence chain harder to overclaim, but they do not implement full reverse execution, arbitrary event-engine materialization, full behavioral mirrors, or a complete proof graph.

## Implementation Note - RMW Pre-State Proof - 2026-05-18

Follow-up from Pro's hook-order review has been implemented.

Implemented:

- Effect traces now annotate each modeled read-modify-write memory write that uses a watched pre-instruction byte for `inc [hl]`, `dec [hl]`, or writable `CB [hl]` operations.
- Each such effect carries `pre_state_sample=hook_pre_instruction`, `pre_state_value_hex`, `pre_state_proof_status`, `pre_state_validation`, and optional `pre_state_validation_source`.
- Without a supplied passing hook-order probe, RMW old-byte attribution remains available but is explicitly marked `pre_state_proof_status=planned_only` and `pre_state_validation=missing_hook_order_probe` or `hook_order_probe_not_validated`.
- With a passing runtime hook-order report, only the affected RMW effects upgrade their pre-state proof to `runtime_observed` with `pre_state_validation=hook_order_probe_passed`.
- The write index, reverse-query last-writer results, ranking evidence, and causal graph evidence now preserve this per-effect pre-state proof instead of relying only on the top-level effect-trace hook-order status.
- Ranking now keeps CPU pre-register evidence such as `pre_HL=C200` separate from `pre_state_*` evidence so the added proof metadata does not hide the register state needed for triage.

Validation run:

- Focused RMW/hook-order tests -> 5 passed.
- Runtime attribution hook-order integration tests -> 4 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 367 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: this makes RMW old-byte attribution proof-honest, but it is still bounded by the captured trace window and the hook-order probe scope. It does not make the effect trace a complete CPU/hardware reverse execution engine.

## Implementation Note - HLI/HLD HL Writeback - 2026-05-18

Follow-up from Pro's SM83 effect-modeling review has been implemented.

Implemented:

- `tools.debugger.effect_trace` now emits modeled `HL` register-write effects for all four HLI/HLD opcodes:
  - `ld [hli], a`
  - `ld a, [hli]`
  - `ld [hld], a`
  - `ld a, [hld]`
- The load variants still emit their `A` register-write effects from observed watched memory bytes, but now also emit the `HL` increment/decrement side effect instead of returning early.
- Adjacent-frame register validation can now confirm those `HL` writebacks and carry the evidence into the causal graph.

Validation run:

- Focused HLI/HLD and register-write tests -> 3 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 368 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: this closes the concrete HLI/HLD stale-HL modeling hole, but broader SM83 register/flag/IME/timer/PPU/audio side-effect coverage is still not complete.

## Implementation Note - CB Register Write Effects - 2026-05-18

Follow-up from Pro's SM83 effect-modeling review has been implemented.

Implemented:

- `tools.debugger.effect_trace` now emits register-write effects for writable `CB` register operations:
  - rotate/shift/swap register targets
  - `res bit, r`
  - `set bit, r`
- `CB [hl]` memory-write behavior remains covered by the existing memory RMW path.
- Modeled register values use the same SM83 byte transform helper as the `[hl]` path, including pre-instruction carry for `rl r` and `rr r`.
- Adjacent-frame register validation now confirms these CB register writes and carries the evidence into the causal graph.

Validation run:

- Focused CB register and CB `[hl]` tests -> 4 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 369 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: CB register writes are now modeled, but full flag-output modeling and complete SM83 side-effect coverage are still not finished.

## Implementation Note - Stack Pointer Side Effects - 2026-05-18

Follow-up from Pro's stack/control-flow effect-modeling review has been implemented.

Implemented:

- `tools.debugger.effect_trace` now emits `SP` register-write effects for stack-changing CPU operations:
  - `push rr`
  - taken `call`
  - `rst`
  - taken `ret` / `reti`
  - `pop rr`
- Interrupt-entry transitions now emit an `SP` register-write effect alongside the already-modeled interrupt-entry stack writes.
- Adjacent-frame register validation now confirms SP updates for straight-line stack operations such as `push` and `pop`.
- Dynamic-taint effect-report tests now explicitly account for the new `SP` effects while preserving the original stale-pair provenance checks.

Validation run:

- Focused stack/interrupt tests -> 5 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 370 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: stack pointer side effects are now visible in bounded effect traces, but the debugger still does not provide full reverse execution across every CPU/hardware side effect.

## Implementation Note - 16-Bit Inc/Dec Register-Pair Effects - 2026-05-18

Follow-up from Pro's SM83 register-effect coverage review has been implemented.

Implemented:

- `tools.debugger.effect_trace` now emits register-write effects for 16-bit register-pair increment/decrement instructions:
  - `inc bc` / `dec bc`
  - `inc de` / `dec de`
  - `inc hl` / `dec hl`
  - `inc sp` / `dec sp`
- Adjacent-frame register validation can now confirm the modeled `BC`, `DE`, `HL`, and `SP` values.
- Causal graph evidence now sees these pair writes through the existing register-write path.

Validation run:

- Focused pair-writeback, HLI/HLD, and SP tests -> 3 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 371 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: 16-bit inc/dec pair effects are now visible, but `add hl,rr`, `add sp,e8`, flag outputs, and full hardware side-effect capture still need broader modeling before this can be treated as complete SM83 reverse provenance.

## Implementation Note - 16-Bit Add Register Effects - 2026-05-18

Follow-up from Pro's SM83 16-bit arithmetic review has been implemented.

Implemented:

- `tools.debugger.effect_trace` now emits register-write effects for:
  - `add hl,bc`
  - `add hl,de`
  - `add hl,hl`
  - `add hl,sp`
  - `add sp,e8`
- Signed immediate handling for `add sp,e8` is modeled from the pre-instruction `SP` value and the instruction operand.
- Adjacent-frame register validation can now confirm the modeled `HL` and `SP` results.
- Causal graph evidence receives these writes through the existing register-write path.

Validation run:

- Focused 16-bit add, pair inc/dec, and stack-SP tests -> 3 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 372 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: these 16-bit arithmetic writes are now visible in bounded traces, but exact flag-output modeling, timer/PPU/audio side effects, and complete reverse execution remain incomplete.

## Implementation Note - Deterministic Accumulator and Flag Effects - 2026-05-18

Follow-up from Pro's flag-output modeling review has been partially implemented for deterministic, low-risk instructions.

Implemented:

- `tools.debugger.effect_trace` now emits modeled register-write effects for accumulator rotates:
  - `rlca`
  - `rrca`
  - `rla`
  - `rra`
- Those rotate effects now include both the resulting `A` value and the resulting `F` flags when the needed pre-instruction inputs are present.
- `cpl` now emits both the complemented `A` value and the deterministic `F` update preserving `Z`/`C` and setting `N`/`H`.
- `scf` and `ccf` now emit deterministic `F` updates preserving `Z`, clearing `N`/`H`, and setting/toggling `C`.
- Adjacent-frame register validation can now confirm these `A`/`F` effects, and causal graph evidence receives them through the existing register-write path.

Validation run:

- Focused accumulator/flag, 16-bit add, pair inc/dec, and stack-SP tests -> 4 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 373 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: this is intentionally not a complete flag model. `daa`, full ALU flag outputs, timer/PPU/audio effects, and full reverse execution remain incomplete.

## Implementation Note - ALU and CP Flag Effects - 2026-05-18

Follow-up from Pro's ALU flag-output review has been implemented for the standard 8-bit ALU family.

Implemented:

- `tools.debugger.effect_trace` now emits modeled `F` register-write effects for:
  - `add a,r/[hl]/n`
  - `adc a,r/[hl]/n`
  - `sub a,r/[hl]/n`
  - `sbc a,r/[hl]/n`
  - `and a,r/[hl]/n`
  - `xor a,r/[hl]/n`
  - `or a,r/[hl]/n`
  - `cp a,r/[hl]/n`
- `CP` is modeled as a flag-only write and does not emit an `A` write.
- `Z`, `N`, `H`, and `C` flags are computed from pre-instruction operands and pre-instruction carry where required.
- Adjacent-frame register validation can now confirm ALU `A` and `F` outputs, and dynamic-taint effect-report provenance continues to use the `A` write while seeing the additional `F` write.

Validation run:

- Focused ALU flag, accumulator/flag, 16-bit add, and dynamic-taint ALU provenance tests -> 4 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 374 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: ALU flags are now modeled, but `DAA`, full timer/PPU/audio side effects, arbitrary event-engine state, and full reverse execution remain incomplete.

## Implementation Note - DAA Register and Flag Effects - 2026-05-18

Follow-up from Pro's remaining deterministic SM83 flag-output review has been implemented for `DAA`.

Implemented:

- `tools.debugger.effect_trace` now emits modeled register-write effects for `DAA`:
  - resulting `A`
  - resulting `F`
- The DAA model handles add-mode and subtract-mode adjustment from pre-instruction `A` and `F`, including half-carry, carry, zero, and preserved subtract/carry behavior.
- Adjacent-frame register validation can now confirm DAA output for both add and subtract cases.
- Causal graph evidence receives these writes through the existing register-write path.

Validation run:

- Focused DAA, accumulator/flag, and ALU flag tests -> 3 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 375 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: deterministic CPU effect coverage is stronger, but full reverse execution and full timer/PPU/audio/event-engine behavior remain incomplete.

## Implementation Note - 16-Bit Arithmetic Flag Effects - 2026-05-18

Follow-up from Pro's 16-bit flag-output review has been implemented.

Implemented:

- `tools.debugger.effect_trace` now emits modeled `F` register-write effects for:
  - `add hl,bc`
  - `add hl,de`
  - `add hl,hl`
  - `add hl,sp`
  - `add sp,e8`
  - `ld hl,sp+e8`
- `add hl,rr` now preserves old `Z`, clears `N`, and computes `H`/`C` from the 12-bit and 16-bit add.
- `add sp,e8` and `ld hl,sp+e8` now compute the Game Boy low-byte `H`/`C` flags and clear `Z`/`N`.
- Adjacent-frame register validation can now confirm these `F` effects, and causal graph evidence receives them through the existing register-write path.

Validation run:

- Focused 16-bit flag, 16-bit value, ALU flag, and pair inc/dec tests -> 4 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 376 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: 16-bit arithmetic flags are now visible, but full reverse execution, hardware timing effects, and arbitrary event-engine behavior remain incomplete.

## Implementation Note - INC/DEC Flag Effects - 2026-05-18

Follow-up from Pro's branch-relevant CPU provenance review has been implemented for 8-bit `inc/dec`.

Implemented:

- `tools.debugger.effect_trace` now emits modeled `F` register-write effects for:
  - `inc r`
  - `dec r`
  - `inc [hl]`
  - `dec [hl]`
- Register `inc/dec` flag outputs preserve old carry and compute `Z`, `N`, and `H` from the pre-instruction register value.
- `[hl]` `inc/dec` flag outputs use the same observed pre-memory snapshot path as the byte write itself, so the flag model inherits the existing RMW pre-state proof boundary.
- Adjacent-frame register validation can now confirm these `F` writes, and dynamic-taint effect-report provenance still follows the data register write while seeing the extra flag effect.

Validation run:

- Focused inc/dec flag, raw-watch inc/dec, ALU flag, and 16-bit flag tests -> 4 passed.
- Focused dynamic-taint stale-register, inc-register provenance, and inc/dec flag tests -> 3 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 377 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.

Important remaining caveat: these are modeled effects inside bounded instruction traces. This still does not implement full reverse execution, complete hardware side-effect capture, or arbitrary event-engine behavioral mirrors.

## Implementation Note - CB Flag Effects - 2026-05-18

Follow-up from Pro's CB-prefixed CPU effect review has been implemented for branch-relevant flag outputs.

Implemented:

- `tools.debugger.effect_trace` now emits modeled `F` register-write effects for CB group 0 rotate/shift/swap operations on registers and `[hl]`.
- `tools.debugger.effect_trace` now emits modeled `F` register-write effects for CB group 1 `BIT` operations on registers and `[hl]`.
- CB group 2/3 `RES`/`SET` still emit only the data write because SM83 leaves flags unchanged for those operations.
- `[hl]` CB flag outputs use observed pre-memory snapshots when available, matching the same bounded RMW proof boundary used by CB `[hl]` byte writes.
- Adjacent-frame register validation can now confirm these CB `F` effects, including carry-through `RL`/`RR` and carry-preserving `BIT`.

Validation run:

- Focused CB register-write, CB flag, CB `[hl]` dynamic-taint, and raw-watch CB `[hl]` tests -> 4 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 378 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.

Important remaining caveat: CB flag outputs are still modeled effects inside the captured instruction window. They do not replace hook-order proof for `[hl]` old-byte samples or full reverse execution for code outside the trace window.

## Implementation Note - Direct Dynamic-Taint INC/DEC Flag Provenance - 2026-05-18

Follow-up from the duplicate direct-trace dynamic-taint review has been implemented for `inc/dec r` flag provenance.

Implemented:

- `tools.debugger.dynamic_taint` direct trace attribution now models `F` register writes for `inc r` and `dec r`.
- The direct model computes the same `Z`, `N`, `H`, and carry-preservation behavior used by `tools.debugger.effect_trace`.
- This closes a concrete causal-path gap where a source byte could feed `A`, `inc a` could produce flags, and `push af` could write the derived `F` byte to a sink without direct dynamic-taint attributing that low stack byte back to the source.
- A regression now proves `source memory -> A -> inc a flags -> F -> push af low` and separately keeps `A -> push af high` provenance intact.

Validation run:

- Focused direct dynamic-taint inc-register, inc-flags-through-`push af`, and pair-push provenance tests -> 3 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 379 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: this narrows one direct dynamic-taint/effect-trace divergence, but the duplicate direct-trace model is still not fully unified with `effect_trace.py`. Longer term, direct dynamic-taint should consume the same authoritative effect model or an effect-report handoff to avoid future drift.

## Implementation Note - Direct Dynamic-Taint ALU/CP Flag Provenance - 2026-05-18

Follow-up from the direct dynamic-taint/effect-trace divergence review has been implemented for ALU and compare flag provenance.

Implemented:

- `tools.debugger.dynamic_taint` direct trace attribution now models `F` register writes for:
  - `add a,r/[hl]/n`
  - `adc a,r/[hl]/n`
  - `sub a,r/[hl]/n`
  - `sbc a,r/[hl]/n`
  - `and a,r/[hl]/n`
  - `xor a,r/[hl]/n`
  - `or a,r/[hl]/n`
  - `cp a,r/[hl]/n`
- The direct model now keeps `CP` as a flag-only write, matching SM83 behavior and the effect-trace model.
- A regression proves `source memory -> B -> cp a,b flags -> F -> push af low` while `A -> push af high` remains untainted when `A` was not source-derived.
- Existing direct ALU register provenance remains intact for `source memory -> B -> add a,b -> A -> sink`.

Validation run:

- Focused direct dynamic-taint ALU-register, CP-flags-through-`push af`, inc-flags-through-`push af`, and pair-push provenance tests -> 4 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 380 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: direct dynamic-taint is now stronger for flag-carrying stack snapshots and compare-driven provenance, but the broader duplicate-model risk remains until direct dynamic-taint and effect tracing share one authoritative opcode/effect table.

## Implementation Note - Direct Dynamic-Taint CB Register and Flag Provenance - 2026-05-18

Follow-up from the direct dynamic-taint/effect-trace divergence review has been implemented for CB-prefixed register and flag provenance.

Implemented:

- `tools.debugger.dynamic_taint` direct trace attribution now models writable CB register operations:
  - rotate/shift/swap group 0
  - `RES` group 2
  - `SET` group 3
- Direct dynamic-taint now models CB group 0 flag writes and CB group 1 `BIT` flag writes for register targets.
- Direct dynamic-taint also emits CB `[hl]` flag writes when the instruction has a watched pre-memory byte, matching the same bounded pre-state evidence rule used for CB `[hl]` data writes.
- A regression proves `source memory -> B -> rl b -> B -> sink`.
- A regression proves `source memory -> B -> bit 7,b flags -> F -> push af low`, while `A -> push af high` remains untainted.

Validation run:

- Focused direct dynamic-taint CB-register, CB-bit-flags-through-`push af`, CB-`[hl]`, and CP-flags-through-`push af` tests -> 4 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 382 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: direct dynamic-taint and effect tracing are closer, but still duplicated. A shared opcode/effect table remains the cleaner architecture for complete SM83 coverage and lower future drift risk.

## Implementation Note - Direct Dynamic-Taint Accumulator and DAA Provenance - 2026-05-18

Follow-up from the direct dynamic-taint/effect-trace divergence review has been implemented for accumulator and flag-only operations.

Implemented:

- `tools.debugger.dynamic_taint` direct trace attribution now models accumulator rotate writes for:
  - `rlca`
  - `rrca`
  - `rla`
  - `rra`
- Direct dynamic-taint now models `DAA`, including both adjusted `A` and resulting `F`.
- Direct dynamic-taint now models `CPL`, including complemented `A` and resulting `F`.
- Direct dynamic-taint now models `SCF`/`CCF` flag writes.
- A regression proves `source memory -> A -> rlca -> A -> sink` with the transformed `A` value and provenance preserved.
- A regression proves `source memory -> A -> daa -> A/F -> push af` so both the high byte and low flag byte are attributed to the source when appropriate.

Validation run:

- Focused direct dynamic-taint accumulator-rotate, DAA-flags-through-`push af`, CP-flags-through-`push af`, and inc-flags-through-`push af` tests -> 4 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 384 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: direct dynamic-taint now follows more SM83 accumulator/flag provenance, but direct and effect-trace opcode semantics are still implemented in parallel. Full state-of-the-art CPU provenance still needs a shared opcode/effect table and broader hardware-side effect coverage.

## Implementation Note - Direct Dynamic-Taint 16-Bit Register Provenance - 2026-05-18

Follow-up from the direct dynamic-taint/effect-trace divergence review has been implemented for 16-bit register and pointer provenance.

Implemented:

- `tools.debugger.dynamic_taint` now accepts pair registers in `--source-reg`/`source_regs`:
  - `af`
  - `bc`
  - `de`
  - `hl`
  - `sp`
- Direct trace attribution now models 16-bit pair increment/decrement register writes for `BC`, `DE`, `HL`, and `SP`.
- Direct trace attribution now models:
  - `ld sp,hl`
  - `ld hl,sp+e8`
  - `add hl,bc/de/hl/sp`
  - `add sp,e8`
  - HLI/HLD `HL` writeback for `ld [hli],a`, `ld a,[hli]`, `ld [hld],a`, and `ld a,[hld]`
- Direct `add hl,rr`, `add sp,e8`, and `ld hl,sp+e8` now emit modeled `F` writes matching the effect-trace flag model.
- Direct write attribution now derives the top-level `taint` field from recovered register-provenance contributors when the older direct taint engine has no separate finding. This fixes a proof-reporting gap where contributor evidence existed but `taint=[]`.
- A regression proves `source BC -> add hl,bc -> HL -> push hl`, with both pushed bytes attributed to the source pair.

Validation run:

- Focused direct dynamic-taint add-HL-through-`push hl`, pair-push, accumulator-rotate, and ALU-register tests -> 4 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 385 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: direct dynamic-taint now tracks more 16-bit CPU provenance, but this is still duplicate opcode semantics rather than a shared table. Whole-ROM state-of-the-art proof still requires shared effect modeling, full reverse execution, and emulator-backed behavioral mirrors.

## Implementation Note - Direct Dynamic-Taint Stack/Control SP Provenance - 2026-05-18

Follow-up from the direct dynamic-taint/effect-trace divergence review has been implemented for stack-pointer updates caused by stack and control-flow instructions.

Confirmed bug before the patch:

- A direct trace sequence `ld sp,hl -> push bc -> ld hl,sp+n -> push hl` still attributed the later `SP` source to the earlier `ld sp,hl`, not the intervening `push bc` stack-pointer update.
- A direct trace sequence `ld sp,hl -> call nn -> ld hl,sp+n -> push hl` had the same stale attribution, naming `ld sp,hl` instead of the taken call's `SP` update.

Implemented:

- `tools.debugger.dynamic_taint` direct trace attribution now models `SP` register writes for:
  - `push bc/de/hl/af`
  - taken `call nn` and taken conditional calls
  - `rst`
  - `ret`, `reti`, and taken conditional returns
  - `pop bc/de/hl/af`
- `pop` direct attribution now records both the loaded register pair and the post-pop `SP` update.
- New regressions prove that later `ld hl,sp+n -> push hl` provenance names the intervening `push bc updates sp` or `call updates sp` record, with the adjusted `SP` value.

Validation run:

- Focused direct dynamic-taint stack/control `SP` tests plus the existing add-HL-through-`push hl` regression -> 3 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 387 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: this closes another direct dynamic-taint/effect-trace drift point, but both paths still duplicate SM83 opcode semantics. The next architectural improvement remains a shared opcode/effect model, plus broader hardware-side effect capture and emulator-backed replay/mirrors before the debugger should be marked ready.

## Implementation Note - Direct Attribution Findings for Dynamic-Taint Paths - 2026-05-18

Follow-up from the proof-promotion/subsystem-boundary review has been implemented for instruction-trace dynamic-taint paths.

Confirmed bug before the patch:

- Direct write attribution could prove a contributor-backed path that the older direct `TaintEngine` did not emit as a finding.
- Example: `source BC -> add hl,bc -> push hl` produced correct write attributions for both pushed bytes, but `path_count` stayed `0`, so the causal path layer lost that proof.

Implemented:

- `tools.debugger.dynamic_taint` now reconciles instruction-trace findings from two sources:
  - legacy direct `TaintEngine` sink findings
  - contributor-backed direct write attributions
- Direct write attributions with non-empty `contributors` and `taint` now become `instruction_trace_write_attribution` findings.
- Duplicate findings for the same `(seq, address, sink)` prefer the richer direct attribution finding.
- The direct pair-source regression now proves both pushed bytes become dynamic-taint paths:
  - `$C1FE` with `seed_pair`
  - `$C1FF` with `seed_pair`

Validation run:

- Focused direct dynamic-taint pair-path, stack `SP`, and call `SP` regressions -> 3 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 387 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: this improves path visibility for direct instruction evidence, but it still depends on the direct attribution model being correct. It does not replace the planned shared opcode/effect table or full side-effect-complete reverse execution.

## Implementation Note - Dynamic-Taint Path Evidence Preservation - 2026-05-18

Follow-up from the proof-promotion/subsystem-boundary review has been implemented for dynamic-taint path evidence.

Confirmed bug before the patch:

- Rich direct attribution evidence could become a dynamic-taint path, but the path itself kept only generic evidence:
  - `seq=...`
  - mnemonic
  - `taint=...`
- The source finding's proof status, source kind, and detailed register-provenance evidence were dropped at the path boundary.
- Because the causal graph uses path evidence for `proves_taint_to` and contributor edges, those graph edges also lost the detailed provenance line.

Implemented:

- Dynamic-taint paths now preserve:
  - `source_kind`
  - `evidence_source_proof_status`
  - source finding evidence, including register-provenance lines
- Dynamic-taint path steps now use the source-kind role instead of a generic `dynamic_instruction` role and carry the evidence-source proof status.
- The direct pair-source regression now proves that `register_provenance=l@01:4000` survives:
  - in the `$C1FE` dynamic-taint path evidence
  - in causal-graph edge evidence derived from that path

Validation run:

- Focused dynamic-taint path evidence, stack `SP`, call `SP`, and effect-report register provenance regressions -> 4 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 387 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: this preserves proof detail across one more subsystem boundary, but it still does not create new runtime observations. The larger remaining gaps are still full side-effect-complete reverse execution, shared CPU/effect semantics, and emulator-backed whole-ROM behavior mirrors.

## Implementation Note - Dynamic-Taint Path Proof Gate - 2026-05-18

Follow-up from the proof-promotion/subsystem-boundary review has been implemented for dynamic-taint path proof status.

Confirmed bug before the patch:

- `build_paths()` promoted any finding with a non-empty `taint` list to `proof_status="taint_proven"`.
- That was acceptable for the current instruction/effect findings, but unsafe as a subsystem boundary: a planned route or synthetic finding with a taint label could be promoted to proven taint without observed evidence.

Implemented:

- Dynamic-taint path proof status now depends on both:
  - the presence of taint
  - the source finding's proof status
- Taint paths promote to `taint_proven` only when the source finding is at least observed through:
  - `instruction_observed`
  - `runtime_observed`
  - already `taint_proven`
- Planned/source-only taint labels stay at the source proof level instead of being promoted.
- A regression proves a `planned_only` finding with `taint=["move_power"]` remains `planned_only` while preserving the taint label and evidence.

Validation run:

- Focused planned-evidence proof-gate and observed direct-attribution path regressions -> 2 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 388 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: this prevents one proof-promotion class at the dynamic-taint path boundary. It does not solve deeper source-of-truth issues such as shared CPU/effect semantics, complete hardware side-effect capture, or full reverse execution.

## Implementation Note - Direct Dynamic-Taint Pop SP Regression - 2026-05-18

Follow-up coverage has been added for direct dynamic-taint `pop` stack-pointer provenance.

Confirmed before adding the test:

- Effect trace already had `pop ... updates sp` coverage.
- Direct dynamic-taint already had data provenance for `pop bc low/high`.
- Direct dynamic-taint did not have a focused regression proving the post-pop `SP` update feeds later attribution.

Added regression:

- `ld sp,hl -> pop bc -> ld hl,sp+n -> push hl`
- The pushed low byte now proves it came through the intervening `pop bc updates sp` register-provenance record.
- The assertion checks:
  - pushed value `02`
  - `register_provenance.operation == "pop bc updates sp"`
  - adjusted `SP` value `C102`
  - taint remains `stack_base`

Validation run:

- Focused direct dynamic-taint pop/push/call `SP` regressions -> 3 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 389 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: this is coverage hardening for an implemented behavior. It does not close the larger reverse-execution or whole-ROM mirror gaps.

## Implementation Note - Causal Path Proof Summary in Ranking/Impact - 2026-05-18

Follow-up from the proof-promotion/subsystem-boundary review has been implemented for ranked and impact views of causal-graph paths.

Confirmed bug before the patch:

- `tools.debugger.causal_graph` already emitted `proof_vector` and `proof_summary` for causal paths.
- `tools.debugger.ranking` reduced causal paths to ordinary findings and kept only the path's generic evidence.
- `tools.debugger.impact` consumes ranked findings, so impact output also lost the weak-edge proof details.
- A mixed path with `proof_status="planned_only"` but `proof_summary.max="taint_proven"` could be displayed without showing that the path's minimum proof was still planned.

Implemented:

- Ranked causal-path findings now include:
  - `proof_min=...`
  - `proof_max=...`
  - `proof_edge_count=...`
  - `proof_edge=<relation>:<proof_status> source=<source>`
- Impact output inherits the same proof summary/vector evidence through ranked findings.
- A regression proves ranking and impact preserve `proof_min=planned_only`, `proof_max=taint_proven`, and the weak `plans_evidence_route:planned_only` edge.

Validation run:

- Focused causal proof-summary/ranking/impact regressions -> 3 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 390 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: this is a presentation/proof-honesty fix for existing graph evidence. It does not create new runtime observations or close the full reverse-execution and whole-ROM mirror gaps.

## Implementation Note - Dynamic-Taint Path Proof Status in Ranking/Impact - 2026-05-18

Follow-up from the proof-promotion/subsystem-boundary review has been implemented for ranked and impact views of dynamic-taint paths.

Confirmed bug before the patch:

- `tools.debugger.dynamic_taint` paths can now remain `planned_only` when they carry a taint label from planned/source-only evidence.
- `tools.debugger.ranking` ignored `path.proof_status` for dynamic-taint paths, so `finding()` inferred `taint_proven` from `type="taint_path"`.
- `tools.debugger.impact` also ignored `path.proof_status` when directly consuming a dynamic-taint report, so planned taint paths could be promoted again in impact output.

Implemented:

- Ranked dynamic-taint findings now preserve `path.proof_status`.
- Impact dynamic-taint items now preserve `path.proof_status`.
- A regression proves a dynamic-taint path with:
  - `proof_status="planned_only"`
  - `taint=["move_power"]`
  remains `planned_only` in both ranked and impact output.
- The existing observed dynamic-taint path regression still proves true observed paths remain `taint_proven`.

Validation run:

- Focused planned/observed dynamic-taint consumer proof regressions -> 2 passed.
- `python -B -m unittest discover tools\debugger\tests` -> 391 tests passed.
- `python -m tools.debugger audit` -> `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile` on touched debugger files -> PASS.
- `git diff --check` on touched debugger files -> PASS.

Important remaining caveat: this fixes another downstream proof-promotion path. It does not reduce the remaining need for stronger runtime observation, side-effect-complete reverse execution, or emulator-backed mirrors.

## GPT-5.5 Pro Checkpoint - Expanded Packet Review - 2026-05-18

Source: user relayed GPT-5.5 Pro feedback after reviewing the expanded checkpoint packet from
`C:\Users\lolno\Downloads\debugger_gpt55_pro_packet_2026-05-18_next`.

Plain-language summary:

- The debugger is getting much better at not overstating evidence.
- Several previous hard-line proof-boundary bugs appear fixed in the current snapshot.
- `ready=False` is still correct.
- The suite being green is meaningful, but it is not readiness.
- The main remaining danger is no longer the most obvious proof-boundary holes; it is downstream consumers/UI making careful bounded evidence look final.

Confirmed improvements Pro called out:

- Bank-qualified symbols now require exact bank-aware keys in reverse query and dynamic taint.
- Reverse query no longer promotes `write_count > 0` without a concrete observed last-write object.
- Bounded "replay" has been renamed/reframed as modeled `bounded_effect_span_validation`.
- Stack read/write effects are bank-qualified when `SP` is in banked WRAM.
- `tools.trace.runtime.read_word()` is little-endian.
- `sub a` clears damage-taint `A`.
- Causal graph nodes carry `proof_status_by_source`.
- Multi-edge paths carry proof vectors.
- Playtest routes require artifact availability rather than command-string runnability alone.

Keep `ready=False` because:

- Reverse query is still bounded to supplied effect traces.
- Last-writer answers are exact only inside supplied instruction/effect windows.
- Checkpoint validation is modeled forward from retained trace checkpoints, not full emulator reverse execution.
- DMA, PPU, timer, audio mixer, interrupt-entry, and bank-switch side effects still need richer capture.
- Whole-ROM replay/localization remains partial, despite being much richer than before.
- The debugger still cannot honestly claim whole-ROM, side-effect-complete, arbitrary-context causal debugging.

Remaining high-severity proof-promotion risks:

1. Ranking fallback inference is still dangerous.
   - `ranking.infer_proof_status()` still defaults:
     - `taint_path` -> `taint_proven`
     - `reverse_attribution` / `write_attribution` / `reverse_query` -> `instruction_observed`
     - `causal_path` -> `taint_proven`
   - This can re-promote legacy or malformed proof-less findings by item type.

2. Impact dynamic write attribution proof is still risky.
   - `impact.taint_items()` preserves dynamic-taint path proof status now.
   - But dynamic write attributions are still converted to impact items without preserving `attribution["proof_status"]`.
   - A downgraded attribution can be reclassified downstream by type inference.

3. Causal graph reverse-query ingestion still has a risky default.
   - `add_reverse_query_report()` currently defaults missing result proof to `instruction_observed`.
   - Missing/malformed/legacy reverse-query results should default to `planned_only` unless validation or a concrete observed writer proves more.

4. Visualization can still mislead through max-proof display.
   - Nodes carry `proof_status_by_source` and `proof_summary`, which is good.
   - But a UI badge that only shows top-level strongest proof can hide mixed proof.
   - Mixed nodes need an obvious mixed-proof badge or min/max display.

Subsystem-boundary status:

- Dynamic taint is much better, especially path proof gating via source finding proof status.
- Effect trace is stronger and more honest, with banked memory/stack effects and modeled effect evidence.
- Reverse query is improved, especially concrete observed-write requirements and modeled effect-span naming.
- Causal graph is improved, but reverse-query default proof needs hardening.
- Ranking and impact are currently the weakest remaining proof-boundary consumers.
- Visualization preserves metadata but still needs visible mixed-proof presentation.

Bank/address exactness status:

- Main hard-line banked-symbol fallback cases look fixed.
- Reverse query exact-matches bank-qualified targets.
- Dynamic taint blocks banked source/sink matches unless runtime bank evidence can produce the same key.
- Effect trace attaches runtime bank state to memory and stack effects.

Remaining bank/address design risks:

- `tools.damage_debugger.taint.Sink` and `TaintState.memory` are still 16-bit structures.
- The unified wrapper compensates with bank-exact matching, but long term the unified proof substrate should use bank-aware sinks/state.
- `AddressSpec` still mixes user intent/static request with observed runtime evidence.
- Need a separate `ObservedAddressKey`.
- `address_spec_requires_exact_key()` may treat any present bank as exact; bank prefixes on unbanked spaces like WRAM0/HRAM/IO/OAM/IE should be invalid, ignored as inexact, or explicitly marked semantically meaningless.

Duplicated SM83 modeling risk:

- Direct dynamic-taint and effect-trace modeling are closer than before but still duplicated.
- This remains a major architecture risk.
- Divergence risks include:
  - unsupported-op handling,
  - flag semantics,
  - register-pair side effects,
  - `HL` writeback,
  - `SP` updates,
  - stack/control instructions,
  - RMW old-byte attribution,
  - hardware effects like OAM DMA, CGB VRAM DMA, DIV/timer, MBC, SRAM enable/bank, WRAM/VRAM bank writes, PPU/audio IO, interrupt entry, HALT/STOP, EI/DI/RETI.
- Recommended shared model: `tools/debugger/sm83_model.py` or `tools/debugger/cpu_effect_model.py`.
- The shared model should emit typed effects:
  - register reads/writes,
  - memory reads/writes,
  - stack reads/writes,
  - flag writes,
  - PC/SP/IME effects,
  - conditional control flow,
  - required pre-state fields,
  - hardware trigger declarations.
- Dynamic taint should consume the shared model and attach taint.
- Effect trace should consume the shared model and attach observed values/proof.

Recommended implementation order from Pro:

1. Patch ranking/impact proof preservation for write attributions and reverse/causal defaults.
2. Patch causal graph reverse-query default proof to `planned_only` unless validation/concrete writer proves more.
3. Add mixed-proof UI badges and proof min/max rendering in visualization.
4. Add semantic bank validity to address handling.
5. Introduce `EvidenceAtom` and `ObservedAddressKey` as compatibility wrappers first.
6. Build a shared SM83 effect model for loads, stack/control, ALU/flags, and CB ops.
7. Build checkpointed effect logs with pre/post validation and bank state.
8. Add playtest minimization over input logs and trace windows.
9. Add event-context materializer for scripts/maps/audio entry points.
10. Expand mirrors with explicit `passed`, `failed`, `inconclusive`, and `not_run` statuses.

Specific next tests Pro recommended:

- `test_ranking_dynamic_write_attribution_preserves_planned_proof_status`
- `test_impact_dynamic_write_attribution_preserves_planned_proof_status`
- `test_causal_graph_reverse_query_missing_result_proof_defaults_planned`
- `test_visualization_shared_node_requires_mixed_proof_badge`
- `test_address_spec_rejects_impossible_bank_for_unbanked_space`
- `test_reverse_query_unbanked_target_reports_bus_address_unverified_when_bank_collision_exists`
- `test_effect_trace_rmw_every_old_byte_has_pre_state_proof_status`
- `test_shared_sm83_model_dynamic_taint_and_effect_trace_parity_ld_hli`
- `test_hblank_dma_trigger_is_not_expanded_without_hblank_runtime_evidence`
- `test_mirror_passed_does_not_rank_as_causal_writer`

Specific next patches Pro recommended:

- `tools/debugger/ranking.py`: make `infer_proof_status()` conservative. Remove broad type-only promotion defaults or only use them when explicit validated evidence exists.
- `tools/debugger/impact.py`: preserve `attribution["proof_status"]` for dynamic write attributions and include match precision/bank/proof-downgrade evidence when present.
- `tools/debugger/causal_graph.py`: derive reverse-query proof from result validation/concrete observed writer; fallback `planned_only`.
- `tools/debugger/visualization.py`: make mixed proof impossible to miss with min/max and mixed-proof badges.
- `tools/debugger/address.py`: split requested/static `AddressSpec` from observed runtime `ObservedAddressKey`; add bank semantic validity.
- `tools/debugger/dynamic_taint.py`: replace/wrap the 16-bit `Sink` with a bank-aware unified sink object for unified debugger use.
- Start `tools/debugger/sm83_model.py` or `tools/debugger/cpu_effect_model.py` as the shared CPU/effect source of truth.

Design guidance to preserve:

- Use typed `EvidenceAtom` so every causal claim records claim type, origin, observation type, precision, validation, scope, hashes, source report, and proof status.
- Treat scalar `proof_status` as a summary, not the proof itself.
- Split requested/static address, static symbol address, bus address, and runtime bank-qualified address into distinct facts.
- Introduce a real `BankState` object that distinguishes runtime observed, inferred from IO write, default, unknown, mapper-derived, and SRAM-disabled states.
- Introduce `CommandSpec` for typed command readiness, required inputs, expected outputs, placeholders, trust checks, expected proof, and rendered argv.
- Make proof vectors mandatory for causal paths, ranking, impact, and visualization.

UI/reporting risks to keep checking:

- A shared node with planned and taint-proven sources is mixed proof, not simply `taint_proven`.
- Reverse-query UI should not say "last writer" without "within supplied effect window."
- Mirror UI should separate expectation consistency from causal proof.
- Playtest routes must distinguish `planned_only`, `ready_to_run`, `executed`, and `observed`.

Blunt takeaway:

- The checkpoint fixed the most embarrassing proof-boundary holes.
- The next danger is subtler: downstream consumers and UI can still make careful bounded evidence look final.
- Patch proof consumers and presentation before adding more breadth.

## Working Checkpoint - Read Before Continuing Long Debugger Work

This section is intentionally operational. Before another long implementation stretch, reread this checkpoint and the previous Pro review notes in this file.

Current status:

- Keep `ready=False`.
- Latest known full debugger validation before this checkpoint was green at 391 debugger tests, with `python -m tools.debugger audit` still reporting 7 complete buckets, 4 partial buckets, and 4 blocking gaps.
- Do not claim state-of-the-art whole-ROM causality yet. The debugger is stronger and more honest, but reverse query remains bounded to supplied effect windows, and full reverse execution / arbitrary event runtime generation / graphics-audio-script mirrors are still incomplete.

Highest-priority implementation reminders:

1. Patch proof consumers before adding more breadth.
   - `ranking.py`, `impact.py`, `causal_graph.py`, and visualization can still make bounded evidence look stronger than it is.
   - Type-based proof inference is risky unless explicit validated evidence is present.

2. Preserve dynamic write attribution proof status.
   - Planned or downgraded dynamic write attributions must remain planned/downgraded in ranking and impact.
   - Add regressions for planned dynamic write attributions before patching.

3. Harden causal graph reverse-query defaults.
   - Missing proof on a reverse-query result should not default to `instruction_observed`.
   - Derive proof from validation or a concrete observed last-write object; fallback should be `planned_only`.

4. Make mixed proof visible.
   - A shared node with one planned source and one taint-proven source is mixed, not simply proven.
   - Visualization should show proof min/max or a mixed-proof badge.

5. Keep bank/address exactness conservative.
   - Main banked-symbol fallback bugs are believed fixed, but address semantics are not finished.
   - Long term, split requested/static `AddressSpec` from runtime `ObservedAddressKey`, and add semantic bank validity for spaces where a bank is invalid or meaningless.

6. Converge SM83 modeling.
   - Direct dynamic-taint and effect-trace opcode modeling are still duplicated.
   - The next architecture win after proof-consumer patches is a shared `sm83_model.py` / `cpu_effect_model.py` consumed by both engines.

Immediate next tests to consider:

- `test_ranking_dynamic_write_attribution_preserves_planned_proof_status`
- `test_impact_dynamic_write_attribution_preserves_planned_proof_status`
- `test_causal_graph_reverse_query_missing_result_proof_defaults_planned`
- `test_visualization_shared_node_requires_mixed_proof_badge`

Validation rule:

- After each proof-boundary patch, run focused regressions first, then the full debugger test suite, `python -m tools.debugger audit`, `py_compile` on touched modules, and `git diff --check`.

## Implementation Note - Dynamic Write Attribution Proof in Ranking/Impact

Date: 2026-05-18.

Confirmed bug before patch:

- A dynamic-taint `write_attributions[]` entry with `proof_status="planned_only"` was emitted into ranking as `type="reverse_attribution"` without carrying the explicit proof status.
- The generic ranking fallback then inferred `instruction_observed`.
- Focused regression failed before the patch:
  - `test_rank_and_impact_do_not_promote_planned_dynamic_write_attribution`
  - observed failure: ranking returned `instruction_observed` instead of `planned_only`.

Implemented fix:

- `tools/debugger/ranking.py` now passes dynamic write attribution `proof_status` into the ranked `reverse_attribution` finding.
- `tools/debugger/impact.py` now passes dynamic write attribution `proof_status` into the impact `reverse_attribution` item.
- Both ranking and impact now preserve attribution proof details in evidence when present:
  - `proof_status`
  - `match_precision`
  - `bank_match`
  - `bank_source`
  - `proof_downgrade_reason`
  - `evidence_source_proof_status`
  - `effect_evidence_source`
  - `effect_proof_status`

Regression added:

- `test_rank_and_impact_do_not_promote_planned_dynamic_write_attribution`
- It verifies a planned dynamic write attribution remains `planned_only` in both ranking and impact.
- It also verifies proof downgrade and bank precision details remain visible in evidence.

Validation after patch:

- Focused dynamic-taint ranking/impact tests: 5 passed.
- Full debugger suite: 392 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile tools\debugger\ranking.py tools\debugger\impact.py tools\debugger\tests\test_catalog.py`: passed.
- `git diff --check` on touched debugger/doc files: passed before this note; rerun after this note before finalizing.

Remaining priority from Pro:

- Patch causal graph reverse-query default proof so missing/malformed result proof falls back to `planned_only`, not `instruction_observed`.
- Add mixed-proof visualization badge/min-max proof rendering.
- Then continue toward shared address/evidence schemas and the shared SM83 effect model.

## Implementation Note - Reverse Query Proof Derivation in Causal Graph

Date: 2026-05-18.

Finding while implementing:

- `tools/debugger/causal_graph.py` visually contained the risky fallback Pro called out: missing reverse-query result proof appeared to fall back to `instruction_observed`.
- The module's `normalize_proof_status()` currently defaults unknown values to `planned_only`, so the fallback was mostly dead in practice.
- That made missing-proof/no-writer results safe by accident, but also meant legacy results with a concrete last-writer object and missing scalar proof stayed `planned_only`.

Implemented fix:

- Added explicit reverse-query result proof derivation:
  - explicit `result["proof_status"]` wins;
  - then `result["validation"]["proof_status"]`;
  - then a concrete observed last-writer object promotes to `instruction_observed`;
  - otherwise fallback is `planned_only`.
- A concrete last writer requires:
  - non-empty `last_writer` dict,
  - sequence,
  - PC or PC label,
  - address or address key,
  - and no non-write access/kind contradiction.

Regressions added:

- `test_causal_graph_reverse_query_missing_result_proof_defaults_planned`
  - proof-less/no-writer reverse-query result stays `planned_only`.
- `test_causal_graph_reverse_query_concrete_writer_missing_proof_is_observed`
  - legacy result with a concrete last writer is treated as `instruction_observed`.

Validation after patch:

- Focused reverse/causal graph tests: 4 passed.
- Full debugger suite: 394 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile tools\debugger\causal_graph.py tools\debugger\ranking.py tools\debugger\impact.py tools\debugger\tests\test_catalog.py`: passed.
- `git diff --check` on touched debugger/doc files: passed before this note; rerun after this note before finalizing.

Remaining priority from Pro:

- Add mixed-proof visualization badge/min-max proof rendering.
- Then move to address semantic validity / `ObservedAddressKey` and shared SM83 effect modeling.

## Implementation Note - Mixed Proof Visualization

Date: 2026-05-18.

Problem:

- Causal graph nodes already preserved `proof_status_by_source` and `proof_summary`, but rendered visualization could still visually emphasize only the strongest node proof.
- That made a node with planned and proven sources easy to read as simply proven.

Implemented fix:

- `tools/debugger/visualization.py` now gives graph nodes:
  - `proof_badge`
  - `proof_min`
  - `proof_max`
- Nodes with different min/max proof statuses get `proof_badge="mixed"`.
- Mermaid graph labels now annotate mixed nodes as:
  - `proof:mixed planned_only->taint_proven`
- Markdown output now includes a `Mixed Proof Nodes` table with:
  - node label,
  - `proof_min=...`,
  - `proof_max=...`,
  - source-specific proof statuses.
- HTML inspector now includes a graph-node table showing proof badge/range/source proof status, in addition to graph edges.

Regression updated:

- `test_visualization_preserves_causal_graph_edge_proof_statuses`
- It now verifies:
  - `proof_badge="mixed"`,
  - `proof_min="planned_only"`,
  - `proof_max="taint_proven"`,
  - mixed proof appears in Mermaid output,
  - min/max proof appears in rendered Markdown content.

Validation after patch:

- Focused visualization/causal graph tests: 4 passed.
- Full debugger suite: 394 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile tools\debugger\visualization.py tools\debugger\causal_graph.py tools\debugger\ranking.py tools\debugger\impact.py tools\debugger\tests\test_catalog.py`: passed.
- `git diff --check` on touched debugger/doc files: passed before this note; rerun after this note before finalizing.

Remaining priority from Pro:

- Address semantic validity / `ObservedAddressKey`.
- Shared SM83 effect model for dynamic-taint and effect-trace parity.
- Checkpointed effect logs and then playtest minimization.

## Implementation Note - Address Semantic Validity and ObservedAddressKey

Date: 2026-05-18.

Problem:

- `AddressSpec` treated any present bank prefix as exact, even for spaces where a runtime bank is impossible or semantically meaningless.
- Reverse-query bus-address fallback could return multiple bank-qualified runtime keys for an unbanked target without explicitly marking the target match as bank-unverified.

Implemented fix:

- `tools/debugger/address.py` now distinguishes request/static `AddressSpec` from runtime `ObservedAddressKey`.
- `AddressSpec` now carries:
  - `bank_semantics`;
  - `bank_valid`;
  - `exact_key_required`.
- Exact-key requirements are limited to bank-qualified spaces:
  - `romx`;
  - `vram`;
  - `sram`;
  - `wramx`.
- Bank `00:` prefixes on fixed/unbanked symbol addresses are preserved as static metadata but are not exact runtime keys.
- Nonzero bank prefixes on unbanked spaces such as WRAM0, OAM, IO, HRAM, and IE are rejected.
- `tools/debugger/effect_trace.py` now uses `ObservedAddressKey` when building observed effect address keys.
- `tools/debugger/reverse_query.py` now annotates fallback bus-address matches with:
  - `match_precision`;
  - `bank_match`;
  - `proof_downgrade_reason`.
- When an unbanked reverse-query target matches multiple bank-qualified runtime keys at the same bus address, each result is downgraded to `planned_only` for the target claim and marked `match_precision="bus_address_unverified_bank"`.

Regressions added:

- `test_address_spec_rejects_impossible_bank_for_unbanked_space`
- `test_reverse_query_unbanked_target_reports_bus_address_unverified_when_bank_collision_exists`

Validation after patch:

- Focused address/reverse-query regressions: 2 passed.
- Adjacent bank-exactness regressions: 10 passed.
- Full debugger suite: 396 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority from Pro:

- Shared SM83 effect model for dynamic-taint and effect-trace parity.
- Checkpointed effect logs with pre/post validation and bank state.
- Playtest recorder/minimizer.

## Implementation Note - Shared SM83 HLI/HLD Model Slice

Date: 2026-05-18.

Problem:

- `effect_trace.py` and `dynamic_taint.py` both modeled HLI/HLD instruction semantics locally.
- The duplicated logic had already been corrected, but keeping separate operation names and HL writeback value math made future divergence likely.

Implemented fix:

- Added `tools/debugger/sm83_model.py` as the first shared SM83 CPU/effect model slice.
- The shared model currently owns HLI/HLD semantics for:
  - `ld [hli], a`;
  - `ld a, [hli]`;
  - `ld [hld], a`;
  - `ld a, [hld]`.
- The model exposes:
  - exact memory operation text;
  - exact HL writeback operation text;
  - signed HL delta;
  - updated-HL value calculation.
- `tools/debugger/effect_trace.py` now consumes the shared model for HLI/HLD memory effects and HL register writeback effects.
- `tools/debugger/dynamic_taint.py` now consumes the shared model for direct dynamic-taint HLI/HLD memory writes, register-load provenance, and HL writeback records.
- Both consumers now mark shared-model-derived HLI/HLD records with `model_source="tools.debugger.sm83_model"` so downstream evidence can distinguish shared CPU-model semantics from local ad hoc modeling.

Regression added:

- `test_shared_sm83_model_dynamic_taint_and_effect_trace_parity_ld_hli`
  - verifies the shared model's HLI operation and HL update;
  - verifies effect-trace HLI/HLD memory/register effects carry the shared model source;
  - verifies dynamic-taint HLI/HLD write attributions carry the shared model source;
  - verifies dynamic-taint register provenance through `ld a, [hli]` keeps the shared model source and taint.

Validation after patch:

- Focused shared-model parity regression: 1 passed.
- Adjacent HLI/HLD and dynamic/effect provenance regressions: 5 passed.
- Full debugger suite: 397 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority from Pro:

- Expand the shared SM83 model beyond HLI/HLD into loads, stack/control, ALU/flags, CB ops, SP/PC/IME, and hardware trigger declarations.
- Checkpointed effect logs with pre/post validation and bank state.
- Playtest recorder/minimizer.

## Implementation Note - Shared SM83 Stack/Control Model Slice

Date: 2026-05-18.

Problem:

- Stack/control semantics were still duplicated between effect tracing and dynamic-taint attribution.
- Push/call/rst stack writes, pop/ret stack reads, SP deltas, and call/rst/return control-flow labels are part of the same CPU semantic claim, but each consumer encoded those strings and deltas locally.

Implemented fix:

- Extended `tools/debugger/sm83_model.py` with `StackControlSemantics`.
- The shared model now owns stack/control semantics for:
  - `push bc/de/hl/af`;
  - `pop bc/de/hl/af`;
  - unconditional and conditional `call`;
  - unconditional and conditional `ret`;
  - `reti`;
  - all `rst` vectors.
- The model exposes:
  - stack write/read operation text;
  - register-write operation text for pop targets;
  - SP writeback operation text;
  - signed SP delta and updated-SP calculation;
  - control-flow operation text;
  - RST target when applicable.
- `tools/debugger/effect_trace.py` now consumes the shared model for stack reads/writes, SP register writebacks, and call/rst/return control-flow records.
- `tools/debugger/dynamic_taint.py` now consumes the shared model for direct stack write attribution, pop register provenance, and SP writeback records.
- Shared-model-derived stack/control records now carry `model_source="tools.debugger.sm83_model"` in both consumers while preserving the existing JSON fields.

Regression added:

- `test_shared_sm83_model_dynamic_taint_and_effect_trace_parity_stack_control`
  - verifies the shared model's call return/SP/control semantics;
  - verifies effect-trace stack read/write, SP writeback, and control-flow records carry the shared model source;
  - verifies dynamic-taint stack write attributions carry the shared model source.

Validation after patch:

- Focused stack/control shared-model parity regression: 1 passed.
- Adjacent stack/control and dynamic-taint regressions: 6 passed.
- Full debugger suite: 398 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority from Pro:

- Expand the shared SM83 model further into general loads, ALU/flags, CB ops, SP/PC/IME, and hardware trigger declarations.
- Checkpointed effect logs with pre/post validation and bank state.
- Playtest recorder/minimizer.

## Implementation Note - Shared SM83 ALU/Flag Model Slice

Date: 2026-05-18.

Problem:

- ALU result and flag semantics were still duplicated between `effect_trace.py` and `dynamic_taint.py`.
- These values feed branch/control causality and register provenance, so keeping two implementations risked future drift in carry, half-carry, zero, subtract, and CP/no-A-write behavior.

Implemented fix:

- Extended `tools/debugger/sm83_model.py` with `AluSemantics`.
- The shared model now owns ALU result and flag semantics for:
  - `add a,r/[hl]/n`;
  - `adc a,r/[hl]/n`;
  - `sub a,r/[hl]/n`;
  - `sbc a,r/[hl]/n`;
  - `and a,r/[hl]/n`;
  - `xor a,r/[hl]/n`;
  - `or a,r/[hl]/n`;
  - `cp a,r/[hl]/n`.
- The model exposes:
  - ALU group/name;
  - operation text from a source label;
  - modeled A result, with CP returning no A result;
  - modeled F result including zero/subtract/half-carry/carry.
- `tools/debugger/effect_trace.py` now consumes the shared model for ALU register-write effects and annotates those records with `model_source="tools.debugger.sm83_model"`.
- `tools/debugger/dynamic_taint.py` now consumes the shared model for direct ALU register provenance and annotates those records with `model_source="tools.debugger.sm83_model"`.
- Removed the duplicate local ALU result/flag helpers from both consumers.

Regression added:

- `test_shared_sm83_model_dynamic_taint_and_effect_trace_parity_alu_flags`
  - verifies shared-model ADD and CP result/flag behavior;
  - verifies effect-trace ALU writes carry the shared model source;
  - verifies dynamic-taint register provenance through `add a, b` carries the shared model source and taint.

Validation after patch:

- Focused ALU shared-model parity regression: 1 passed.
- Adjacent ALU/DAA/accumulator/CP/dynamic provenance regressions: 7 passed.
- Full debugger suite: 399 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority from Pro:

- Expand the shared SM83 model further into general loads, CB ops, SP/PC/IME, and hardware trigger declarations.
- Checkpointed effect logs with pre/post validation and bank state.
- Playtest recorder/minimizer.

## Implementation Note - Shared SM83 CB Model Slice

Date: 2026-05-18.

Problem:

- CB opcode result and flag semantics were still duplicated between `effect_trace.py` and `dynamic_taint.py`.
- CB operations feed both register provenance and read-modify-write memory attribution, so duplicated carry, bit-test, rotate/shift, `res`, and `set` handling could silently diverge.

Implemented fix:

- Extended `tools/debugger/sm83_model.py` with `CbSemantics`.
- The shared model now owns CB semantics for:
  - rotate/shift/swap operations;
  - `bit n,r/[hl]`;
  - `res n,r/[hl]`;
  - `set n,r/[hl]`.
- The model exposes:
  - target register or `[hl]`;
  - group/bit decoding;
  - operation text;
  - whether the opcode writes a value or flags;
  - carry dependency for result/flag source operands;
  - modeled result byte;
  - modeled F result.
- `tools/debugger/effect_trace.py` now consumes the shared model for CB memory reads, register writes, flag writes, and `[hl]` memory writes.
- `tools/debugger/dynamic_taint.py` now consumes the shared model for direct CB register provenance, flag provenance, and `[hl]` memory write attributions.
- Shared-model-derived CB records now carry `model_source="tools.debugger.sm83_model"` in both consumers while preserving existing JSON fields.

Regression added:

- `test_shared_sm83_model_dynamic_taint_and_effect_trace_parity_cb_ops`
  - verifies shared-model RL, BIT `[hl]`, and SET `[hl]` result/flag behavior;
  - verifies effect-trace CB register/flag/memory records carry the shared model source;
  - verifies dynamic-taint CB register provenance and direct `[hl]` write attribution carry the shared model source and preserve taint.

Validation after patch:

- Focused CB shared-model parity regression: 1 passed.
- Adjacent CB effect/dynamic regressions: 7 passed.
- Full debugger suite: 400 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority from Pro:

- Expand the shared SM83 model further into general loads, SP/PC/IME, interrupt entry, and hardware trigger declarations.
- Checkpointed effect logs with pre/post validation and bank state.
- Playtest recorder/minimizer.

## Implementation Note - Shared SM83 CPU-State and Interrupt-Entry Model Slice

Date: 2026-05-18.

Problem:

- HALT/STOP, EI/DI/RETI, and interrupt-entry transition semantics were still locally encoded in `effect_trace.py`.
- Interrupt-entry SP deltas, return-address bytes, operation names, and IME/CPU-state side effects are proof-bearing CPU semantics, so they should come from the same shared model as stack/control, ALU, HLI/HLD, and CB behavior.

Implemented fix:

- Extended `tools/debugger/sm83_model.py` with:
  - `CpuStateSemantics` for HALT, STOP, EI, DI, and RETI;
  - `InterruptEntrySemantics` for SM83 interrupt vectors.
- The shared interrupt model now owns:
  - vector names and operation text;
  - interrupt-entry SP delta and updated-SP calculation;
  - return-address calculation from the interrupted instruction;
  - low/high return-address stack byte extraction.
- `tools/debugger/effect_trace.py` now consumes the shared model for:
  - `cpu_state` HALT/STOP side effects;
  - `ime` EI/DI/RETI side effects;
  - trace-inferred interrupt-entry side effect records;
  - interrupt-entry SP writebacks;
  - interrupt-entry stack writes.
- Shared-model-derived CPU-state and interrupt-entry records now carry `model_source="tools.debugger.sm83_model"`.
- Side-effect index triggers now preserve `model_source` when the source effect carries it, without removing or renaming existing fields.

Regression added:

- `test_shared_sm83_model_effect_trace_cpu_state_and_interrupt_entry`
  - verifies shared-model interrupt vector naming, SP delta, return-address calculation, and HALT/STOP modes;
  - verifies effect-trace interrupt-entry, SP writeback, stack-write, IME, and CPU-state records carry the shared model source;
  - verifies side-effect index triggers preserve the shared model source.

Validation after patch:

- Focused CPU-state/interrupt-entry shared-model regression: 1 passed.
- Adjacent interrupt/IME/HALT/STOP regressions: 3 passed.
- Full debugger suite: 401 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority from Pro:

- Expand the shared SM83 model further into general loads and hardware trigger declarations.
- Checkpointed effect logs with pre/post validation and bank state.
- Playtest recorder/minimizer.

## Implementation Note - Shared SM83 Hardware Trigger Declaration Slice

Date: 2026-05-18.

Problem:

- Common hardware-trigger declarations were still local to `effect_trace.py`.
- OAM DMA, CGB VRAM DMA, DIV reset, IO register classes, MBC writes, and bank-select writes are proof-bearing hardware semantics. Keeping those declarations separate from the shared SM83 model left effect tracing as the only source of truth for trigger kind/category/operation text.

Implemented fix:

- Extended `tools/debugger/sm83_model.py` with `HardwareTriggerSemantics`.
- The shared model now declares hardware trigger semantics for:
  - OAM DMA start writes;
  - CGB VRAM DMA setup and length/mode/start writes;
  - DIV reset and timer register writes;
  - audio, PPU, timer, interrupt, serial, and joypad IO writes;
  - WRAM/VRAM bank-select writes;
  - MBC external RAM enable, ROM bank select, RAM/upper-ROM bank select, and mode/latch writes.
- Moved hardware memory-bank helpers into the shared model so DMA source/read bank attribution is no longer locally duplicated in `effect_trace.py`.
- `tools/debugger/effect_trace.py` now consumes the shared declarations when producing side-effect triggers and DMA/timer reset derived effects.
- Shared-model-derived hardware triggers, DMA transfer effects, and DIV reset writes now carry `model_source="tools.debugger.sm83_model"`.
- Side-effect index triggers preserve the shared model source through existing JSON fields plus the added `model_source` field.

Regression added:

- `test_shared_sm83_model_effect_trace_hardware_trigger_declarations`
  - verifies shared-model OAM DMA, DIV reset, and CGB VRAM DMA declarations;
  - verifies effect-trace side-effect index triggers carry the shared model source;
  - verifies representative DMA and timer reset derived effects carry the shared model source.

Validation after patch:

- Focused hardware-trigger shared-model regression: 1 passed.
- Adjacent OAM DMA, CGB VRAM DMA, and DIV reset regressions: 5 passed.
- Full debugger suite: 402 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority from Pro:

- Expand the shared SM83 model further into general loads.
- Checkpointed effect logs with pre/post validation and bank state.
- Playtest recorder/minimizer.

## Implementation Note - Shared SM83 General Load Model Slice

Date: 2026-05-18.

Problem:

- General `ld` operation declarations were still duplicated between `effect_trace.py` and `dynamic_taint.py`.
- Immediate register loads, register-to-register copies, direct memory loads, `[hl]` loads/stores, direct stores, high-memory loads/stores, and `ld sp, hl` all feed register provenance and write attribution. Keeping operation text, register targets, source kinds, and address-source metadata local to each consumer risked divergence.

Implemented fix:

- Extended `tools/debugger/sm83_model.py` with `LoadSemantics`.
- The shared model now declares general load semantics for:
  - `ld r,n`;
  - `ld rr,nn`;
  - `ld r,r`;
  - `ld r,[hl]` and `ld [hl],r`;
  - `ld a,[bc]`, `ld a,[de]`, `ld [bc],a`, and `ld [de],a`;
  - `ld [hl],n`;
  - `ld [nn],sp`, `ld [nn],a`, and `ld a,[nn]`;
  - `ldh [n],a`, `ldh [c],a`, `ldh a,[n]`, and `ldh a,[c]`;
  - `ld sp,hl`.
- `tools/debugger/effect_trace.py` now consumes the shared model for:
  - load memory-read effects;
  - load register-write effects;
  - load memory/io-write effects.
- `tools/debugger/dynamic_taint.py` now consumes the shared model for:
  - direct register provenance from load instructions;
  - direct memory/io write attribution from load stores.
- Shared-model-derived general load records now carry `model_source="tools.debugger.sm83_model"` while preserving existing JSON field names and operation strings.

Regression added:

- `test_shared_sm83_model_dynamic_taint_and_effect_trace_parity_general_loads`
  - verifies shared-model immediate, register-copy, `[hl]` store, direct memory load, and direct store declarations;
  - verifies effect-trace load register-write and memory-write records carry the shared model source;
  - verifies dynamic-taint direct write attribution and register provenance through `ld a,[nn]` / `ld [nn],a` carry the shared model source and preserve taint.

Validation after patch:

- Focused general-load shared-model regression: 1 passed.
- Adjacent LD/dynamic provenance regressions: 6 passed.
- Full debugger suite: 403 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority from Pro:

- Checkpointed effect logs with pre/post validation and bank state.
- Playtest recorder/minimizer.

## Implementation Note - Reverse-Query Bounded Span Bank/Post Evidence

Date: 2026-05-18.

Problem:

- Bounded checkpoint-to-writer reverse-query validation replayed effect spans, but the resulting reverse-query report did not expose the checkpoint context that made the replay bounded.
- Span writes also summarized the writer without carrying the already available bank-state attribution and adjacent post-write validation evidence through to the reverse-query result.
- That made banked reverse-query answers harder to audit when SRAM/VRAM/WRAM bank state and post-write observations were the proof boundary.

Implemented fix:

- `tools/debugger/reverse_query.py` now attaches bounded-span checkpoint context to reverse-query validation results:
  - checkpoint PC and label;
  - checkpoint bank state;
  - checkpoint registers;
  - checkpoint observed memory.
- Bounded-span writes now preserve existing JSON shape while adding proof-bearing fields from the source effect:
  - runtime observation and model source;
  - bank, bank source, address space, SRAM enable state, and SRAM enable source;
  - post-value hex/source/status plus the observed post-state sequence and PC;
  - per-effect bank-state snapshot.

Regression added:

- `test_reverse_query_bounded_effect_span_preserves_bank_and_post_validation_evidence`
  - verifies a bounded SRAM reverse query preserves checkpoint SRAM bank state;
  - verifies the span writer resolves to `sram:02:A100` with bank-source evidence from inferred SRAM state;
  - verifies adjacent next-instruction post-state validation remains visible on the reverse-query span write.

Validation after patch:

- Focused bounded-span reverse-query regression: 1 passed.
- Adjacent bank-state and post-validation regressions: 7 passed.
- Full debugger suite: 404 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority from Pro:

- Playtest recorder/minimizer.
- Full reverse execution/emulator replay across every CPU side effect remains incomplete.

## Implementation Note - Playtest Route Execution/Observation State

Date: 2026-05-18.

Problem:

- Playtest packet routes already distinguished command/input readiness from missing artifacts, but downstream reports still had to infer whether a route was merely ready to run, had produced an output, or had produced observed evidence.
- A route with `status="ready"` and `proof_status="planned_only"` was compatible, but too easy to read as proof-bearing without checking the declared output.

Implemented fix:

- `tools/debugger/playtest_packet.py` now inspects each route's declared `produces` output and adds compatible fields without removing or renaming existing route fields:
  - `execution_status`: `planned_only`, `ready_to_run`, `executed`, or `observed`;
  - output existence, size, kind, valid flag, execution flag, proof status, and output errors;
  - top-level `route_execution_status_counts`, `executed_evidence_routes`, and `observed_evidence_routes`.
- Route `proof_status` remains `planned_only` until the produced output exists, is valid, and carries the expected proof status. Ready commands are now explicitly `execution_status="ready_to_run"` rather than proof-bearing evidence.
- `tools/debugger/investigate.py` propagates the route execution/output fields into investigation reports and adds `playtest_route_execution_status_counts`.

Regression added:

- `test_playtest_packet_routes_distinguish_ready_executed_and_observed_evidence`
  - verifies a runnable runtime watch route starts as `ready_to_run` with `proof_status="planned_only"`;
  - verifies a produced watch report with `proof_status="runtime_observed"` promotes that route to `execution_status="observed"` and `proof_status="runtime_observed"`;
  - verifies a produced planned/ranking output is `execution_status="executed"` but still `proof_status="planned_only"`;
  - verifies investigation report collection preserves the execution status counts.

Validation after patch:

- Focused playtest route execution-status regression: 1 passed.
- Focused plus adjacent playtest packet/capture/readiness/consistency regressions: 7 passed.
- Full debugger suite: 405 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority from Pro:

- Playtest minimizer evidence should continue to converge toward executed minimized repro packets, not just planned route metadata.
- Full reverse execution/emulator replay across every CPU side effect remains incomplete.

## Implementation Note - Playtest Input-Log Minimizer Slice

Date: 2026-05-18.

Problem:

- The generic minimizer could trim trace/report evidence windows, but supported text input logs were not first-class minimization inputs.
- Playtest packets could point at an input log and replay routes could consume one, but there was no reduced input artifact that kept only the input events required by an explicit repro predicate.

Implemented fix:

- `tools/debugger/minimize.py` now accepts input logs through `input_logs`.
- `tools.debugger minimize` now exposes `--input-log` and `--out-input-log`.
- Added `input_log_minimization` to minimization reports with:
  - original/minimized/removed event counts;
  - written reduced input-log path and line count;
  - retained button sample;
  - expectation results and known limits;
  - follow-up commands for ingest, replay, and investigation using the reduced input log.
- The reducer preserves retained event timing by inserting explicit `WAIT n` lines for gaps before retained events. For example, retaining `A` at frame 1 and `B` at frame 4 emits `WAIT 1`, `A`, `WAIT 2`, `B`.
- The reduced input log remains a repro candidate, not proof by itself; the emitted replay/investigate commands must execute before treating it as observed ROM behavior.

Regressions added:

- `test_minimize_reduces_playtest_input_log_with_timing_preserved`
  - verifies a noisy playtest input log is reduced to the expected button events;
  - verifies generated waits preserve retained input frame timing;
  - verifies replay/investigation follow-up commands use the reduced input log.
- `test_cli_minimize_reduces_input_log`
  - verifies the CLI path writes the minimized text input log and JSON minimization report.

Validation after patch:

- Focused input-log minimizer regressions plus adjacent minimizer/replay regressions: 6 passed.
- Full debugger suite: 407 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority from Pro:

- Playtest minimization still needs execution-backed repro confirmation and minimization over emulator state/save-state deltas.
- Full reverse execution/emulator replay across every CPU side effect remains incomplete.

## Implementation Note - Minimized State-Patch Runtime Confirmation

Date: 2026-05-18.

Problem:

- `state_patch_minimization.out_report` was a useful handoff, but replay did not automatically load an existing minimized state report as part of the next replay plan.
- Downstream consumers also lacked a proof-gated distinction between "a minimized state patch report exists" and "that minimized state was actually exercised by runtime watch evidence."

Implemented fix:

- `tools/debugger/replay.py` now derives existing minimized state-patch reports from `state_patch_minimization.out_report` and includes them in `effective_reports`.
- Replay setup/save-state discovery can now select concrete save states from the minimized state report when the file exists.
- Replay reports now add `minimized_state_patch_confirmation` with:
  - source minimization reports;
  - minimized state reports, existing/missing report split, and effective save state;
  - watch execution state, hit count, evidence strings, and follow-up commands.
- The confirmation remains `proof_status="planned_only"` until a runtime watch executes against the derived replay context and observes at least one watch hit.
- `tools/debugger/ranking.py` now emits a `minimized_state_patch_confirmation` finding, so `tools.debugger impact` preserves the same proof status through ranked findings.

Regressions added:

- `test_replay_loads_minimized_state_patch_report_but_keeps_confirmation_planned`
  - verifies replay loads an existing minimized state report into `effective_reports`;
  - verifies setup selects the state from that minimized report;
  - verifies confirmation stays `planned_only` without runtime execution.
- `test_replay_confirms_minimized_state_patch_with_runtime_watch_execution`
  - verifies executed watch evidence promotes only the state-patch confirmation to `runtime_observed`;
  - verifies rank and impact carry that proof status.

Validation after patch:

- Focused minimized-state confirmation regressions: 2 passed.
- Adjacent replay/minimizer/input-log confirmation regressions: 9 passed.
- Full debugger suite: 414 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger files.
- `git diff --check` passed for touched tracked debugger files; the untracked review log passed a trailing-whitespace check.

Remaining priority from Pro:

- This closes another minimization proof boundary, but full reverse execution/emulator replay across every CPU side effect remains incomplete.
- Playtest minimization still needs deeper minimization over emulator state/save-state deltas, not just proof-gated minimized state-report handoff confirmation.

## Implementation Note - Save-State Delta Evidence for Materialized States

Date: 2026-05-18.

Problem:

- Executed content-state and generic state-space materialization wrote patched save states, but reports did not expose the actual before/after save-state byte delta.
- State-patch minimization could prove that a smaller patch list preserved expectations, but downstream users still had to inspect the `.state` artifact manually to know how small the resulting save-state mutation was.

Implemented fix:

- `tools/debugger/content_state.py` now builds a compact `save_state_delta` summary after execution:
  - base/out save-state paths;
  - byte sizes and SHA-256 hashes;
  - changed byte count;
  - bounded changed-offset list and before/after samples;
  - `proof_status="state_materialized"`.
- `tools/debugger/state_space.py` reuses the same delta summarizer for executed generic state-space reports and exposes it at both top-level and inside `execution`/`state_space`.
- `tools/debugger/minimize.py` now carries the minimized candidate's save-state delta into the written minimized state report and into `state_patch_minimization.minimized_save_state_delta`.

Regressions added:

- `test_state_space_execute_patches_and_writes_state`
  - verifies executed generic state-space reports expose exact changed offsets and counts.
- `test_content_state_execute_patches_and_writes_state`
  - verifies executed content-state materialization exposes the same delta evidence.
- `test_minimize_executes_generic_state_space_candidates`
  - verifies the minimized state-space report and minimization summary preserve the minimized save-state delta.

Validation after patch:

- Focused save-state delta regressions: 2 passed.
- Adjacent content-state/state-space execution and minimization regressions: 6 passed.
- Full debugger suite: 414 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger files.
- `git diff --check` passed for touched tracked debugger files and the untracked review log.

Remaining priority from Pro:

- Save-state byte deltas make materialized state mutation smaller and inspectable, but this still does not implement full reverse execution/emulator replay across every CPU side effect.
- Deeper semantic minimization over arbitrary event-engine context and save-state fields remains incomplete.

## Implementation Note - Shared SM83 Inc/Dec Model Slice

Date: 2026-05-18.

Problem:

- 8-bit `inc`/`dec` register and `[hl]` result/flag semantics were still duplicated in `effect_trace.py` and `dynamic_taint.py`.
- These instructions feed register provenance, memory write attribution, flag causality, and pushed-AF proof chains, so local drift could make two reports disagree while still looking modeled.

Implemented fix:

- `tools/debugger/sm83_model.py` now owns shared 8-bit `inc`/`dec` semantics for register targets and `[hl]`.
- `tools/debugger/effect_trace.py` now routes register writes, `[hl]` reads/writes, and `[hl]` flag writes through that shared model.
- `tools/debugger/dynamic_taint.py` now routes register provenance and `[hl]` memory write attribution through the same model.
- Emitted JSON keeps existing operation names and report shape while adding `model_source="tools.debugger.sm83_model"` where this model is now authoritative.

Regression added:

- `test_shared_sm83_model_dynamic_taint_and_effect_trace_parity_inc_dec`
  - verifies shared-model result and flag behavior for `inc b` and `inc [hl]`;
  - verifies effect-trace records for register and `[hl]` inc/dec operations carry the shared model source;
  - verifies dynamic-taint provenance through `inc b` and `[hl]` write attribution carries the shared model source and preserves taint.

Validation after patch:

- Focused shared inc/dec model regression: 1 passed.
- Adjacent effect-trace and dynamic-taint inc/dec regressions: 5 passed.
- Full debugger suite: 412 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger files.

Remaining priority from Pro:

- Address semantic validity / `ObservedAddressKey` compatibility remains the next proof-boundary slice.
- Full reverse execution/emulator replay across every CPU side effect remains incomplete.

## Implementation Note - Shared SM83 16-Bit Arithmetic and Accumulator Model Slice

Date: 2026-05-18.

Problem:

- After the general-load shared model work, 16-bit inc/dec, `add hl,rr`, `add sp,e8`, `ld hl,sp+e8`, accumulator rotates, `DAA`, `CPL`, `SCF`, and `CCF` were still locally modeled in both `effect_trace.py` and `dynamic_taint.py`.
- Those operations feed register provenance, flag provenance, branch causality, and stack-pushed AF/HL evidence, so duplicated semantics could drift while still looking proof-bearing downstream.

Implemented fix:

- `tools/debugger/sm83_model.py` now owns shared semantics for:
  - 16-bit register-pair inc/dec;
  - `add hl,bc/de/hl/sp`;
  - `add sp,e8`;
  - `ld hl,sp+e8`;
  - accumulator rotates;
  - `DAA`, `CPL`, `SCF`, and `CCF`.
- `tools/debugger/effect_trace.py` and `tools/debugger/dynamic_taint.py` now consume those shared semantics and annotate emitted records with `model_source="tools.debugger.sm83_model"`.
- The old duplicated result/flag helpers for these instruction families were removed from both consumers.

Regression added:

- `test_shared_sm83_model_dynamic_taint_and_effect_trace_parity_16bit_and_accumulator`
  - verifies shared-model result/flag behavior for inc-pair, `add hl`, `add sp,e8`, and `DAA`;
  - verifies effect-trace records for these operations carry the shared model source;
  - verifies dynamic-taint provenance through pushed AF/HL carries the shared model source and preserves taint.

Validation after patch:

- Focused 16-bit/accumulator shared-model regression: 1 passed.
- Adjacent arithmetic, accumulator, DAA, and dynamic-taint provenance regressions: 9 passed.
- Full debugger suite: 411 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger files.
- `git diff --check` passed for touched tracked debugger files.

Remaining priority from Pro:

- Full reverse execution/emulator replay across every CPU side effect remains incomplete.
- Playtest minimization still needs deeper minimization over emulator state/save-state deltas.

## Implementation Note - Minimized Input-Log Runtime Confirmation

Date: 2026-05-18.

Problem:

- Replay could now consume a minimized `.inputs` artifact from an `input_log_minimization` report, but the replay report did not explicitly distinguish "this reduced log is ready for replay" from "this reduced log was actually used in runtime watch evidence."
- Rank/impact consumers could therefore see the replay as a useful handoff without a first-class proof boundary for the minimized input itself.

Implemented fix:

- `tools/debugger/replay.py` now adds `minimized_input_log_confirmation` to replay reports.
- The confirmation records source reports, reduced input logs, parsed playback counts, retained button samples, watch targets, watch execution state, hit count, evidence strings, and follow-up commands.
- Confirmation remains `proof_status="planned_only"` with `status="runtime_confirmation_planned"` until a runtime watch run executes and observes at least one watch hit.
- When executed watch evidence is valid and hit-bearing, confirmation promotes only that field to `proof_status="runtime_observed"` with `status="runtime_watch_observed"`.
- `tools/debugger/ranking.py` now emits a `minimized_input_log_confirmation` finding from replay reports, preserving the confirmation proof status so `tools.debugger impact` inherits the same boundary through ranked findings.

Regressions added:

- `test_replay_keeps_minimized_input_log_confirmation_planned_without_runtime_execution`
  - verifies replay records the minimized input source but keeps proof planned without execution.
- `test_replay_confirms_minimized_input_log_with_runtime_watch_execution`
  - verifies executed watch evidence promotes the minimized input confirmation to `runtime_observed`;
  - verifies rank and impact carry that proof status.

Validation after patch:

- Focused minimized-input confirmation regressions: 2 passed.
- Focused plus adjacent replay/minimizer/rank/impact regressions: 5 passed.
- Full debugger suite: 410 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger files.
- `git diff --check` passed for touched tracked debugger files.

Remaining priority from Pro:

- The reduced input log is now explicitly proof-gated, but broad emulator-backed reverse execution across every CPU side effect remains incomplete.
- Playtest minimization still needs deeper minimization over emulator state/save-state deltas.

## Implementation Note - Minimized Input-Log Replay/Investigation Handoff

Date: 2026-05-18.

Problem:

- The input-log minimizer could write a reduced `.inputs` artifact, but replay and investigation still treated it as a standalone command output.
- That meant a minimization report with `input_log_minimization.out_input_log` did not automatically become the black-box replay input for the next debugger pass.

Implemented fix:

- `tools/debugger/replay.py` now derives effective input logs from preserved and written `input_log_minimization` reports.
- Replay reports now ingest and parse the minimized input log, include it in `input_logs`, and pass it into replay/watch/instruction-trace commands.
- Replay signals now include `input_log_minimized_artifact` and retained button samples so downstream reports can see that the replay input came from a reducer.
- `tools/debugger/investigate.py` now derives minimized input logs from input reports into `derived_inputs["input_logs"]`, includes them in `effective_input_logs`, and preserves the reducer's follow-up commands in the input-report step.

Regression added:

- `test_replay_and_investigate_consume_minimized_input_log_artifact`
  - verifies replay consumes `minimized.inputs` from a minimization report without requiring a repeated CLI `--input-log`;
  - verifies replay parses the reduced input log and emits replay commands with `--input-log minimized.inputs`;
  - verifies investigation derives the same minimized input log and carries it into `effective_input_logs`.

Validation after patch:

- Focused minimized-input handoff plus adjacent replay/investigation/minimizer regressions: 7 passed.
- Full debugger suite: 408 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority from Pro:

- Playtest minimization still needs execution-backed repro confirmation and minimization over emulator state/save-state deltas.
- Full reverse execution/emulator replay across every CPU side effect remains incomplete.

## Implementation Note - Save-State Delta Evidence in Consumers

Date: 2026-05-18.

Problem:

- Executed content-state/state-space reports and minimized state-patch reports now carried save-state byte deltas, but ranking, impact, and visualization did not surface those deltas in their human-facing evidence.
- Impact evidence is capped, so appending delta details after lower-value minimization metadata could still hide the changed-byte count and offsets from the selected impact item.

Implemented fix:

- `tools/debugger/ranking.py` now has shared save-state delta evidence helpers for materialized reports and minimized state-patch summaries.
- Ranking and impact findings/items for executed content-state and state-space materializations now include changed-byte count, changed offsets, and delta proof status.
- Ranking and impact minimization-route findings/items now include minimized save-state changed-byte count, changed offsets, and proof status before lower-value metadata, so impact truncation cannot hide the core delta evidence.
- `tools/debugger/visualization.py` now includes save-state delta evidence in runtime materialization timeline details and state-patch minimization timeline details.

Regressions updated:

- `test_rank_and_impact_consume_content_state_materializations`
  - verifies content-state executed findings/items expose save-state delta changed bytes and offsets.
- `test_rank_impact_and_visualization_consume_state_space_reports`
  - verifies state-space ranking, impact, and visualization preserve save-state delta evidence.
- `test_visualization_consumes_content_state_materializations`
  - verifies visualization runtime details expose content-state save-state delta evidence.
- `test_minimize_executes_generic_state_space_candidates`
  - verifies rank/impact/visualization preserve minimized save-state delta evidence.

Validation after patch:

- Focused save-state delta consumer regressions: 4 passed.
- Full debugger suite: 414 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger files.
- `git diff --check` passed for touched tracked debugger files and the untracked review log.

Remaining priority from Pro:

- Save-state delta evidence now survives downstream consumers, but full reverse execution/emulator replay across every CPU side effect remains incomplete.
- Deeper semantic minimization over arbitrary event-engine context and save-state fields remains incomplete.

## Implementation Note - EvidenceAtom Compatibility Wrappers

Date: 2026-05-18.

Problem:

- Several proof consumers still relied on free-form evidence strings plus subsystem-specific fields.
- That made it harder for downstream causal graph, ranking, impact, and UI layers to uniformly identify the claim type, origin subsystem, observation type, scope, subjects, precision, and validation status behind a proof claim.

Implemented fix:

- Added `tools/debugger/evidence.py` as a shared compatibility wrapper for typed evidence atoms.
- `tools/debugger/effect_trace.py` now emits EvidenceAtom records on instruction events, effect items, and write-index history entries while preserving existing JSON fields.
- `tools/debugger/reverse_query.py` now emits typed last-writer EvidenceAtom records and carries source effect atoms through result history.
- `tools/debugger/dynamic_taint.py` now emits typed path and write-attribution atoms for instruction traces and effect-trace-backed attribution.
- `tools/debugger/ranking.py` and `tools/debugger/impact.py` now preserve EvidenceAtom records on findings and impact items.
- `tools/debugger/causal_graph.py` now stores EvidenceAtom records on graph nodes and edges, including reverse-query answer edges and concrete writer nodes.
- `tools/debugger/playtest_packet.py` now tags route evidence with planned-route atoms so route proof metadata has the same typed carrier.

Regressions added:

- `test_evidence_atoms_wrap_effect_reverse_and_causal_graph_claims`
  - verifies effect-trace write claims, reverse-query last-writer claims, and causal-graph answer edges expose compatible typed atoms with scope, subjects, proof status, and validation details.
- `test_evidence_atoms_flow_from_dynamic_taint_to_rank_and_impact`
  - verifies dynamic-taint path and write-attribution atoms survive into ranking findings and impact items.

Validation after patch:

- Focused EvidenceAtom regressions: 2 passed.
- Adjacent effect-trace, reverse-query, dynamic-taint, causal-graph, and playtest-packet regressions passed.
- Full debugger suite: 416 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger files.
- `git diff --check` passed for touched tracked debugger files.

Remaining priority from Pro:

- EvidenceAtom compatibility now gives proof claims a typed, portable carrier across major consumers, but it does not close the full reverse-execution, hardware/event-engine, or behavioral mirror gaps.
- The debugger should keep treating `ready=False` as authoritative until those gaps are closed and audited.

## Implementation Note - Address-Key Semantic Compatibility

Date: 2026-05-18.

Problem:

- Requested `AddressSpec` records and runtime `ObservedAddressKey` records used different field shapes for the same semantic address key.
- `ObservedAddressKey` could also silently discard impossible bank qualifiers for unbanked spaces without retaining the semantic reason in the compatibility record.
- Reverse-query ambiguity for an unbanked target that matched multiple bank-qualified runtime keys was only visible through downgrade strings, not structured address-match metadata.

Implemented fix:

- `tools/debugger/address.py` now gives `AddressSpec.as_dict()` an additive `address_key` alias matching its existing `key`.
- `ObservedAddressKey` now exposes compatible `key`, `address_key`, `cli`, `evidence`, `bank_semantics`, `bank_valid`, `requested_bank`, and `requested_bank_source` fields while preserving the existing effective `bank` and `bank_source` fields.
- Invalid observed bank qualifiers for unbanked spaces now remain non-exact but carry `bank_semantics=invalid_for_unbanked_space` and `bank_valid=False`.
- `tools/debugger/reverse_query.py` now adds `ambiguous_address_keys` and an `address_match` summary to each result without removing existing top-level report fields.
- Reverse-query evidence and EvidenceAtom precision now include ambiguous bank-qualified keys when an unbanked target falls back to an ambiguous bus-address match.

Regressions added:

- `test_address_spec_and_observed_address_key_share_compatibility_fields`
  - verifies requested and observed address keys expose compatible field names and retain invalid observed bank semantics for unbanked spaces.
- `test_reverse_query_unbanked_target_reports_bus_address_unverified_when_bank_collision_exists`
  - verifies unbanked reverse queries over multiple banked runtime keys stay `planned_only` and expose structured ambiguous-address metadata.

Validation after patch:

- Focused address-key regressions: 2 passed.
- Adjacent address, effect-trace, reverse-query, and dynamic-taint bank/address regressions: 13 passed.
- Full debugger suite: 417 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger files.
- `git diff --check` passed for touched tracked debugger files.

Remaining priority from Pro:

- Address-key compatibility now makes invalid and ambiguous bank semantics explicit in additive JSON fields, but the full objective remains incomplete.
- Reverse execution across every CPU side effect, richer hardware/event-engine execution, and emulator-backed behavioral mirrors remain blocking gaps.

## Implementation Note - Dynamic-Taint Bank-Unverified Match Downgrade

Date: 2026-05-18.

Problem:

- Dynamic-taint could match an unbanked sink such as `$D141` against bank-qualified runtime evidence such as `wramx:02:D141`.
- That bus-address fallback did not carry structured `match_precision`, `bank_match`, `bank_source`, or downgrade metadata.
- Because the source evidence still looked `instruction_observed`, dynamic-taint paths could promote a bank-unverified bus match to `taint_proven`.

Implemented fix:

- `tools/debugger/dynamic_taint.py` now builds explicit sink-match records for instruction traces and effect-trace reports.
- Instruction-trace write attributions now carry observed `address_key`, `match_precision`, `bank_match`, `bank_source`, and `proof_downgrade_reason`.
- Effect-trace write attributions and taint findings carry the same metadata when an unbanked sink matches bank-qualified effect evidence.
- Bank-unverified bus matches now downgrade attribution/finding proof to `planned_only`, preventing dynamic paths from becoming `taint_proven`.
- Dynamic-taint paths and EvidenceAtom precision now preserve the match metadata for downstream ranking, impact, and graph consumers.

Regressions added:

- `test_dynamic_taint_instruction_trace_downgrades_unbanked_sink_with_banked_runtime_key`
  - verifies instruction-trace evidence with runtime WRAM bank state records the bank-qualified key and downgrades an unbanked sink match.
- `test_dynamic_taint_effect_report_downgrades_unbanked_sink_with_banked_effect_key`
  - verifies effect-trace-backed dynamic taint preserves bank source and downgrades unbanked-to-banked bus matches.

Validation after patch:

- Focused dynamic-taint bank-unverified regressions: 2 passed.
- Adjacent dynamic-taint bank/proof and ranking/impact EvidenceAtom regressions: 12 passed.
- Full debugger suite: 419 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger files.
- `git diff --check` passed for touched tracked debugger files.

Remaining priority from Pro:

- Dynamic-taint no longer promotes bank-unverified bus matches to proven taint, but full SM83 effect-model unification and emulator-backed reverse execution remain incomplete.
- The debugger should continue reporting `ready=False` until the remaining CPU-side-effect, event-engine, and behavioral mirror gaps are closed.

## Implementation Note - Proof-Consumer and Checkpoint Boundary Hardening

Date: 2026-05-18.

Problem:

- Reverse-query checkpoint lookup could fall back from a last writer with a concrete `trace_source` to any prior checkpoint from a different source.
- Checkpoint validation used replay-oriented fields and wording even though the current substrate only checks modeled effects through a retained trace-window checkpoint, not emulator replay.
- Trace-index reverse attributions and causal paths could enter ranking and impact without explicit proof metadata, allowing generic type inference to promote compact or planned evidence.
- Compact `write_index.history` items with concrete-looking `seq`/`pc`/address fields could become `instruction_observed` even when no event body, evidence atom, or trusted source marker was supplied.

Implemented fix:

- `tools/debugger/reverse_query.py` now refuses cross-source checkpoint fallback; when the writer has a `trace_source`, checkpoints must match that exact source.
- Checkpoint validation now adds `validation_kind=trace_window_checkpoint`, `trace_checkpointed`, `checkpoint_kind`, `emulator_replay=False`, `emulator_replay_status=not_run`, and `modeled_effect_span`.
- `replay_span` remains as a deprecated compatibility alias via `legacy_replay_span=True`, while bounded effect-span validation prefers `modeled_effect_span`.
- Checkpoint and bounded-span messages now describe modeled effect-span checking rather than emulator replay.
- Compact index history now carries `history_trusted`; only history with EvidenceAtom data or explicit trusted source/status markers can promote to `instruction_observed`.
- `tools/debugger/ranking.py` and `tools/debugger/impact.py` now preserve trace-index item/report proof status for reverse attributions and causal paths, defaulting missing compact proof to `planned_only`, and carry `evidence_atoms` through both consumers.

Regressions added:

- `test_reverse_query_checkpoint_does_not_cross_trace_sources`
  - verifies a writer from `trace_a.jsonl` is not bounded by a checkpoint from `trace_b.jsonl`.
- `test_reverse_query_checkpoint_validation_does_not_claim_emulator_replay`
  - verifies checkpoint validation exposes modeled-span, non-emulator fields while keeping the legacy replay-span alias.
- `test_rank_and_impact_preserve_trace_index_reverse_attribution_planned_proof`
  - verifies trace-index reverse attributions and causal paths remain `planned_only` in ranking and impact.
- `test_reverse_query_index_history_only_untrusted_compact_history_is_planned`
  - verifies untrusted compact history stays planned-only even with concrete sequence, PC, and address fields.

Validation after patch:

- Focused proof-consumer/checkpoint regressions: 4 passed.
- Adjacent reverse-query and trace-index regressions passed.
- Full debugger suite: 423 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger files.

Remaining priority from Pro:

- Proof consumers now preserve bounded/planned evidence more honestly, but the full objective remains incomplete.
- Actual emulator-backed checkpoint replay, arbitrary event/runtime generation, full behavioral mirrors, and broader SM83 adapter unification remain blocking work.

## Implementation Note - Shared SM83 POP AF Flag Masking

Date: 2026-05-18.

Problem:

- `POP AF` loads the low stack byte into the flag register, but on SM83 the low nibble of `F` is always masked to zero.
- `tools/debugger/effect_trace.py` and direct `tools/debugger/dynamic_taint.py` both reconstructed the popped `AF` value as `(high << 8) | low`.
- That could report impossible flag bits in effect-trace register writes and propagate those impossible bits through dynamic-taint register provenance.

Implemented fix:

- `tools/debugger/sm83_model.py` now owns shared stack-pop value derivation:
  - `stack_pop_register_value()` masks `POP AF` aggregate values to `0xFFF0`.
  - `stack_pop_component_value()` masks the `F` component to `0xF0`.
- `tools/debugger/effect_trace.py` now uses the shared helper for stack-to-register load effects.
- `tools/debugger/dynamic_taint.py` now uses the shared helper for direct POP register writes and for component provenance split from pair writes.

Regression added:

- `test_shared_sm83_pop_af_masks_flag_low_nibble_for_effect_and_dynamic_taint`
  - verifies effect-trace reports `AF=12F0` when stack bytes are low `FF`, high `12`;
  - verifies direct-trace and effect-report dynamic-taint register provenance carry `F0`, not `FF`, into a following `push af` sink write.

Validation after patch:

- Focused POP AF regression: 1 passed.
- Adjacent stack/control, SP, unmodeled-address, and shared-SM83 parity regressions: 5 passed.
- Full debugger suite: 424 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority from Pro:

- This closes a concrete SM83 semantic divergence, but the full objective remains incomplete.
- Actual emulator-backed checkpoint replay, arbitrary event/runtime generation, full behavioral mirrors, and broader SM83 adapter unification remain blocking work.

## Implementation Note - Trace Checkpoint Bank-State Sources

Date: 2026-05-18.

Problem:

- Trace-window checkpoints and bounded effect-span writes carried `bank_state` values, including inferred SRAM bank state, but did not carry a per-key source map.
- Consumers could see that `sram=2` was present without knowing whether it came from the instruction frame or from in-window MBC write inference.

Implemented fix:

- `tools/debugger/effect_trace.py` now emits additive `bank_state_sources` maps on effect events and trace-window checkpoints.
- Source maps use the existing source labels: direct frame values use `bank_state.<key>`, inferred values use `inferred_bank_state.<key>`.
- `tools/debugger/reverse_query.py` now preserves those source maps through compact checkpoint JSON, bounded-span checkpoint context, and bounded-span write records.

Regressions strengthened:

- `test_effect_trace_carries_sram_bank_from_observed_mbc_writes`
  - verifies inferred checkpoint `sram` and `sram_enabled` values carry `inferred_bank_state.*` sources.
- `test_reverse_query_bounded_effect_span_preserves_bank_and_post_validation_evidence`
  - verifies reverse-query checkpoint validation, bounded-span checkpoint context, and span write records preserve the same source map.

Validation after patch:

- Focused bank-state provenance regressions: 2 passed.
- Adjacent checkpoint and bank-state regressions: 5 passed.
- Full debugger suite: 424 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile`, `git diff --check`, and trailing-whitespace checks passed for touched debugger files.

Remaining priority from Pro:

- This makes retained trace checkpoints more explicit about bank-state provenance, but it is still modeled trace-window evidence, not emulator save-state replay.
- Actual emulator-backed checkpoint replay, arbitrary event/runtime generation, full behavioral mirrors, and broader SM83 adapter unification remain blocking work.

## Implementation Note - Typed Trace-Frame Checkpoints

Date: 2026-05-18.

Problem:

- Trace-window checkpoints were still anonymous snapshots in `tools/debugger/effect_trace.py`.
- Reverse-query validation had non-emulator fields, but the retained checkpoint objects themselves did not say they were pre-instruction trace frames from an instruction trace.
- The effect-trace known-limit text still used "replay modeled effects," which could be misread as emulator replay.

Implemented fix:

- `tools/debugger/effect_trace.py` now emits additive checkpoint identity fields:
  - `kind=trace_checkpoint`
  - `checkpoint_kind=pre_instruction_trace_frame`
  - `checkpoint_source=instruction_trace`
  - `emulator_replay=False`
  - `emulator_replay_status=not_run`
- The trace-window known limit now says reverse query can check modeled effects forward from the retained checkpoint, not replay them.
- `tools/debugger/reverse_query.py` now preserves checkpoint identity and non-emulator status through compact checkpoint JSON and bounded-span checkpoint context.

Regressions strengthened:

- `test_effect_trace_carries_sram_bank_from_observed_mbc_writes`
  - verifies effect-trace checkpoints expose typed pre-instruction trace-frame metadata and non-emulator status.
  - verifies trace-window known limits no longer say "replay modeled effects."
- `test_reverse_query_bounded_effect_span_preserves_bank_and_post_validation_evidence`
  - verifies reverse-query checkpoint validation and bounded-span context preserve the typed checkpoint metadata.

Validation after patch:

- Focused typed-checkpoint regressions: 2 passed.
- Adjacent checkpoint and bank-state regressions: 5 passed.
- Full debugger suite: 424 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile`, `git diff --check`, and trailing-whitespace checks passed for touched debugger files.

Remaining priority from Pro:

- The checkpoint evidence is now typed more honestly, but it is still bounded modeled effect evidence rather than emulator-backed replay.
- Actual emulator-backed checkpoint replay, arbitrary event/runtime generation, full behavioral mirrors, and broader SM83 adapter unification remain blocking work.

## Implementation Note - Audit Replay Wording Boundary

Date: 2026-05-18.

Problem:

- `tools/debugger/effect_trace.py` still said trace-window checkpoints support "bounded forward effect replay."
- `tools/debugger/catalog.py` still described the partial whole-ROM replay/localization capability as having "bounded checkpoint-to-writer forward effect replay validation."
- Both phrases were stronger than the current implementation, which performs modeled effect-span consistency checks through retained trace frames, not emulator replay.

Implemented fix:

- Effect-trace known limits now describe "modeled effect-span checks" from retained trace checkpoints.
- The capability audit gap now says "modeled checkpoint-to-writer effect-span consistency."
- Readiness accounting and commands are unchanged; the audit still reports the whole objective as incomplete.

Regressions strengthened:

- `test_capability_report_keeps_whole_rom_goal_incomplete`
  - verifies the audit gap uses modeled effect-span wording and no longer says "effect replay validation."
- `test_effect_trace_carries_sram_bank_from_observed_mbc_writes`
  - verifies top-level effect-trace known limits no longer say "bounded forward effect replay."

Validation after patch:

- Focused audit/effect-trace wording regressions: 2 passed.
- Adjacent audit, checkpoint, and bank-state regressions: 5 passed.
- Full debugger suite: 424 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile`, `git diff --check`, and trailing-whitespace checks passed for touched debugger files.

Remaining priority from Pro:

- This removes a remaining overclaim in public audit wording, but it does not implement emulator-backed replay.
- Actual emulator-backed checkpoint replay, arbitrary event/runtime generation, full behavioral mirrors, and broader SM83 adapter unification remain blocking work.

## Implementation Note - Effect-Trace Target-Match Proof Split

Date: 2026-05-18.

Problem:

- Effect-trace watch hits could say `bank_match=bus_address_unverified_bank`, but the aggregate ranked finding still reported `proof_status=instruction_observed`.
- That collapsed two different claims:
  - the instruction/effect was observed and modeled;
  - the watched bank-qualified target was actually the runtime banked address.
- For a bank-qualified watch matched only by 16-bit bus address with no runtime bank state, the target-match claim must stay planned-only.

Implemented fix:

- `tools/debugger/effect_trace.py` now emits additive per-watch-hit fields:
  - `match_precision`
  - `target_match_proof_status`
  - `effect_proof_status`
  - `proof_downgrade_reason`
- `tools/debugger/ranking.py` now calibrates effect-trace observed findings so all-unverified watched writes remain `planned_only`.
- Mixed traces with stronger exact/unbanked watched-write evidence can remain `instruction_observed`, but still carry the unverified-bank caveat in evidence.
- Impact reports inherit the calibrated proof status and proof-boundary evidence from ranking.

Regressions strengthened:

- `test_effect_trace_banked_symbol_watch_requires_runtime_bank_match`
  - verifies precise banked watches carry `exact_address_key` and `instruction_observed` target-match proof.
  - verifies bus-address-only banked watches carry `bus_address_unverified_bank`, `planned_only`, and a downgrade reason.
  - verifies ranking and impact keep the unverified-only target match `planned_only`.
- `test_effect_trace_indexes_stack_io_and_watched_writes`
  - guards the mixed/stronger evidence case so one unverified caveat does not erase the instruction-observed proof for other observed watched writes and side effects.

Validation after patch:

- Focused effect-trace target-match regression: 1 passed.
- Adjacent address/proof-consumer regressions: 6 passed.
- Full debugger suite: 424 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile`, `git diff --check`, and trailing-whitespace checks passed for touched debugger files.

Remaining priority from Pro:

- This closes another proof-consumer overclaim path, but does not implement full reverse execution, arbitrary event/runtime generation, full behavioral mirrors, or broader SM83 adapter unification.

## Implementation Note - Direct Dynamic-Taint Missing-Address Diagnostics

Date: 2026-05-18.

Problem:

- `tools/debugger/effect_trace.py` reported observed write-shaped instructions as `unmodeled_missing_register` when an address register such as `HL` was absent from the trace frame.
- Direct `tools/debugger/dynamic_taint.py` silently omitted the same instruction from write attribution, leaving consumers with no indication that an observed write could not be modeled.

Implemented fix:

- `tools/debugger/dynamic_taint.py` now emits additive `unmodeled_write_diagnostics` on trace runs and the top-level report.
- Diagnostics carry:
  - `kind=unmodeled_memory_write` or `unmodeled_io_write`
  - `missing_registers`
  - `evidence_status=unmodeled_missing_register`
  - `proof_status=instruction_observed`
  - `target_match_proof_status=planned_only`
  - `attribution_status=unresolved_missing_register`
  - typed EvidenceAtom metadata.
- `tools/debugger/ranking.py` now surfaces these diagnostics as `dynamic_taint_unmodeled_write` findings.
- Impact reports inherit the ranked diagnostic item and proof-boundary evidence.

Regression strengthened:

- `test_effect_trace_reports_unmodeled_missing_address_registers`
  - verifies effect trace still reports the unmodeled `ld [hl], a` write.
  - verifies direct dynamic taint now reports the same observed-but-unresolved write diagnostic.
  - verifies ranking and impact expose the diagnostic without claiming target attribution.

Validation after patch:

- Focused missing-address diagnostic regression: 1 passed.
- Adjacent dynamic-taint/effect-trace regressions: 6 passed.
- Full debugger suite: 424 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile`, `git diff --check`, and trailing-whitespace checks passed for touched debugger files.

Remaining priority from Pro:

- This closes a direct dynamic-taint silent-omission path, but full reverse execution, arbitrary event/runtime generation, full behavioral mirrors, and broader SM83 adapter unification remain blocking work.

## Implementation Note - Typed BankState Records

Date: 2026-05-18.

Problem:

- Effect traces and reverse queries had scalar `bank_state` values plus `bank_state_sources`, but no typed BankState carrier.
- Consumers could preserve a bank value and source string, but could not distinguish runtime-observed state from in-window inferred state without re-parsing source labels.
- The Pro review called out a real `BankState` object as the next schema step.

Implemented fix:

- `tools/debugger/effect_trace.py` now emits additive `bank_state_records` on effect events and trace-window checkpoints.
- Each record carries:
  - `name`
  - `value`
  - `value_hex`
  - `source`
  - `source_kind`
  - `state_kind`
  - `inferred`
  - `valid_for_space`
  - `valid_for_spaces`
- Existing scalar `bank_state` and `bank_state_sources` fields remain unchanged.
- `tools/debugger/reverse_query.py` now preserves these records through compact checkpoint JSON, bounded-span checkpoint context, and bounded-span write records.

Regressions strengthened:

- `test_effect_trace_carries_sram_bank_from_observed_mbc_writes`
  - verifies inferred SRAM checkpoint state has typed record fields including `state_kind=inferred_from_io_write` and `valid_for_space=sram`.
- `test_reverse_query_bounded_effect_span_preserves_bank_and_post_validation_evidence`
  - verifies checkpoint validation, bounded-span checkpoint context, and span write records preserve typed bank-state records.

Validation after patch:

- Focused typed BankState regressions: 2 passed.
- Adjacent checkpoint and bank-state regressions: 5 passed.
- Full debugger suite: 424 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile`, `git diff --check`, and trailing-whitespace checks passed for touched debugger files.

Remaining priority from Pro:

- This makes bank-state provenance more machine-readable, but it does not implement emulator-backed checkpoint replay, full reverse execution, arbitrary event/runtime generation, full behavioral mirrors, or broader SM83 adapter unification.

## Implementation Note - Explicit Emulator Replay Validation Slot

Date: 2026-05-18.

Problem:

- Reverse-query checkpoint and bounded-span validation exposed scalar `emulator_replay=False` / `emulator_replay_status=not_run`.
- There was no stable structured object where future emulator-backed replay can report attempted/passed/failed state.
- Consumers still had to infer "not emulator replay" from loose scalar fields.

Implemented fix:

- `tools/debugger/reverse_query.py` now emits additive `emulator_replay_validation` objects on:
  - `checkpoint_validation`
  - every `bounded_effect_span_validation` status path.
- Current reports explicitly say:
  - `attempted=False`
  - `status=not_run`
  - `engine=emulator`
  - `replay_kind=emulator_save_state`
  - `reason=no emulator save-state checkpoint was supplied`
- Existing scalar compatibility fields remain unchanged.

Regression strengthened:

- `test_reverse_query_checkpoint_validation_does_not_claim_emulator_replay`
  - verifies checkpoint validation exposes the structured non-emulator replay object.
  - verifies bounded-span validation exposes the same not-run replay status.

Validation after patch:

- Focused emulator-replay validation regression: 1 passed.
- Adjacent reverse-query checkpoint regressions: 5 passed.
- Full debugger suite: 424 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile`, `git diff --check`, and trailing-whitespace checks passed for touched debugger files.

Remaining priority from Pro:

- This creates the schema slot for real emulator replay, but it does not restore or rerun emulator save states yet.
- Actual emulator-backed checkpoint replay, full reverse execution, arbitrary event/runtime generation, full behavioral mirrors, and broader SM83 adapter unification remain blocking work.

## Implementation Note - Reverse-Query CommandSpec Validation Routes

Date: 2026-05-18.

Problem:

- Reverse-query validation routes exposed raw command strings plus scalar runnable/status/proof fields.
- Consumers had to infer placeholders, required inputs, expected outputs, and proof expectations from the command text.
- That left a proof-boundary risk where planned rerun routes could be mistaken for current evidence.

Implemented fix:

- `tools/debugger/reverse_query.py` now adds an additive `command_spec` object to every validation route.
- Existing route fields remain unchanged.
- Each command spec carries:
  - `kind=command_spec`
  - `rendered`
  - parsed `argv`
  - `runnable`
  - `status`
  - `has_placeholders`
  - `placeholders`
  - `required_inputs`
  - `expected_outputs`
  - `actual_proof_status`
  - `expected_proof_status`
  - `trust_checks`
- Placeholder routes now explicitly say placeholders must be replaced before execution.
- Runnable concrete routes now preserve parsed input paths and say the expected proof status is the rerun target, not current evidence.

Regressions strengthened:

- `test_reverse_query_preserves_compact_write_index_operand_history`
  - verifies a runnable rerun route exposes `command_spec`, required report/symbol inputs, expected output, actual proof, and expected proof.
- `test_reverse_query_validation_route_command_spec_marks_placeholder_inputs`
  - verifies the capture route exposes unresolved `<runtime-state>` and `<instruction-trace.jsonl>` placeholders and stays non-runnable/planned.
- `test_reverse_query_answers_last_writer_from_effect_trace`
  - verifies regenerated effect-trace validation routes expose typed command metadata without changing old route fields.

Validation after patch:

- Focused CommandSpec route regressions: 3 passed.
- Adjacent proof-boundary regressions: 4 passed.
- Full debugger suite: 425 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile`, `git diff --check`, and trailing-whitespace checks passed for touched debugger files.

Remaining priority from Pro:

- This makes validation-route command readiness and proof expectations machine-readable, but it does not implement emulator-backed checkpoint replay, full reverse execution, arbitrary event/runtime generation, full behavioral mirrors, or broader SM83 adapter unification.

## Implementation Note - Instruction Trace Watch-Value Coverage

Date: 2026-05-18.

Problem:

- Raw instruction traces with `watch_values` carried observed watched bytes, but coverage and trace-index consumers ignored those snapshots.
- A partial-use showcase trace proved `wCurDamage` through effect trace, reverse query, and dynamic taint, while `coverage --trace` still reported the watched symbol as uncovered.
- Trace-index should expose watch snapshots as observed memory reads, but not promote them into writes or reverse attribution.

Implemented fix:

- `tools/debugger/coverage.py` now recognizes `watch_values` keys as observed addresses or symbols.
- Coverage maps observed watch addresses back to symbols through the supplied symbol table when the address is unambiguous.
- `tools/debugger/trace_index.py` now normalizes raw instruction-frame `watch_values` entries into `memory_read` events with operation `watch_values_snapshot`.
- Trace-index suppresses these synthetic snapshot events inside records that already have an explicit watch-change event, avoiding duplicate watch-report entries.

Regressions strengthened:

- `test_coverage_maps_instruction_trace_watch_values_to_symbols`
  - verifies a raw instruction trace observing `$D141` marks `wCurDamage` covered through the symbol table.
- `test_trace_index_normalizes_instruction_trace_watch_values`
  - verifies trace-index emits read-only watch snapshot events with address, symbol, value, and evidence.
- Existing watch-report regression:
  - verifies explicit watch-change reports still index as one event, not duplicated snapshots.

Validation after patch:

- Focused watch-value coverage/trace-index regressions: 3 passed.
- Adjacent coverage/trace-index regressions: 5 passed.
- Showcase raw trace now reports `wCurDamage` covered and trace-indexed as two read snapshots, with zero writes and zero reverse attributions.
- Full debugger suite: 427 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile`, `git diff --check`, and trailing-whitespace checks passed for touched debugger files.

Remaining priority from Pro:

- This tightens runtime-evidence consumer honesty, but it does not implement emulator-backed checkpoint replay, full reverse execution, arbitrary event/runtime generation, full behavioral mirrors, or broader SM83 adapter unification.

## Implementation Note - Dynamic-Taint Banked Sink Warning Honesty

Date: 2026-05-18.

Problem:

- Instruction-trace dynamic taint warned that every bank-exact sink had been skipped before checking whether trace frames supplied a matching runtime address key.
- A banked symbol sink such as `wCurDamage` could produce an exact `wramx:01:D141` write attribution while the same report still said the sink was skipped and should use effect-trace evidence.
- That was a proof-consumer honesty issue: the attribution proof boundary was correct, but the warning stream overstated a missing-evidence condition.

Implemented fix:

- `tools/debugger/dynamic_taint.py` now emits the skipped banked-sink warning only for bank-exact sinks that are actually excluded from the instruction-trace run.
- Exact runtime-bank matches keep their `exact_address_key`, `bank_match=exact`, and `instruction_observed` attribution without the stale skipped-sink warning.
- Existing raw banked sinks without runtime bank evidence still get excluded and still emit the warning.

Regression strengthened:

- `test_dynamic_taint_instruction_trace_does_not_warn_for_exact_banked_symbol_sink`
  - verifies a banked symbol sink with matching `bank_state.wram` produces exact address-key attribution.
  - verifies the skipped banked-sink warning is absent.
- Existing raw banked sink regression:
  - verifies a raw bank-qualified sink with no exact runtime key is still skipped and still warns.

Validation after patch:

- Focused exact-bank warning regression: 1 passed.
- Adjacent dynamic-taint bank/address precision regressions: 9 passed.
- Full debugger suite: 428 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile`, `git diff --check`, and trailing-whitespace checks passed for touched debugger files.

Remaining priority from Pro:

- This removes a misleading report boundary, but it does not implement emulator-backed checkpoint replay, full reverse execution, arbitrary event/runtime generation, full behavioral mirrors, or broader SM83 adapter unification.

## Implementation Note - HBlank VRAM DMA Expansion Honesty

Date: 2026-05-18.

Problem:

- CGB VRAM DMA trigger handling already avoided expanding HBlank-mode DMA into concrete copied bytes.
- The trigger only exposed `mode=hblank` plus size fields, so downstream reports did not explicitly explain why no `dma_read` / `dma_write` effects were present.
- That left a proof-boundary ambiguity: general DMA is modeled from observed setup registers, but HBlank DMA needs PPU/HBlank timing evidence before it can be expanded honestly.

Implemented fix:

- `tools/debugger/effect_trace.py` now adds additive blocked-transfer fields to HBlank FF55 triggers:
  - `transfer_model=blocked_hblank_runtime_evidence_required`
  - `transfer_blocked_reason=hblank_dma_requires_ppu_mode_timing`
- The side-effect index preserves the blocked reason.
- `tools/debugger/ranking.py` and `tools/debugger/visualization.py` surface `transfer_blocked_reasons=...` in side-effect summaries.
- `tools/debugger/causal_graph.py` carries `transfer_blocked_reason=...` on side-effect evidence.
- General-mode CGB VRAM DMA expansion remains unchanged and still emits modeled source reads / VRAM writes only when setup registers are observed.

Regression strengthened:

- `test_effect_trace_classifies_cgb_vram_dma_register_writes`
  - verifies HBlank FF55 triggers are not expanded into DMA copy effects.
  - verifies the effect trace, ranking, visualization, and causal graph expose the blocked-transfer reason.
- Existing general DMA regression:
  - verifies observed general-mode CGB VRAM DMA still expands to modeled copy reads/writes and reverse/dynamic/graph/ranking/visualization consumers still see `modeled_general_dma_from_observed_registers`.

Validation after patch:

- Focused HBlank DMA proof-boundary regression: 1 passed.
- Adjacent hardware/DMA side-effect regressions: 8 passed.
- Full debugger suite: 428 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile`, `git diff --check`, and trailing-whitespace checks passed for touched debugger files.

Remaining priority from Pro:

- This closes one HBlank DMA overclaim ambiguity, but it does not implement PPU-mode-timed HBlank DMA execution, emulator-backed checkpoint replay, full reverse execution, arbitrary event/runtime generation, full behavioral mirrors, or broader SM83 adapter unification.

## Implementation Note - Proofless Consumer Defaults Stay Planned

Date: 2026-05-18.

Problem:

- `tools/debugger/ranking.py` still had generic type-based proof inference for high-risk claim types:
  - `taint_path` -> `taint_proven`
  - `reverse_attribution` / `write_attribution` / `reverse_query` -> `instruction_observed`
  - `causal_path` -> `taint_proven`
- `reverse_query_findings()` also defaulted a result with no result/report proof field to `instruction_observed`.
- Modern reports usually carry explicit proof fields, but legacy, compact, or malformed reports could still be promoted solely from their type.

Implemented fix:

- Removed the high-risk type-only promotions from `infer_proof_status()`.
- Proofless `taint_path`, `reverse_attribution`, `write_attribution`, `reverse_query`, and `causal_path` findings now fall through to `planned_only` unless explicit proof evidence says otherwise.
- `reverse_query_findings()` now defaults missing result/report proof to `planned_only`.
- Existing explicit proof paths still preserve `taint_proven` and `instruction_observed` when current reports actually supply those fields.

Regression strengthened:

- `test_rank_and_impact_default_proofless_dynamic_taint_claims_to_planned`
  - verifies proofless legacy dynamic-taint paths and write attributions stay `planned_only` in ranking and impact.
- `test_rank_and_impact_default_proofless_reverse_query_result_to_planned`
  - verifies proofless reverse-query results stay `planned_only` in ranking and impact even when they look concrete.
- Updated the legacy fake dynamic-taint fixture to treat missing proof as planned rather than proven.

Validation after patch:

- Focused proofless consumer regressions: 2 passed.
- Adjacent proof-consumer regressions: 8 passed.
- Full debugger suite: 430 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile`, `git diff --check`, and trailing-whitespace checks passed for touched debugger files.

Remaining priority from Pro:

- This removes another proof-promotion fallback, but it does not implement emulator-backed checkpoint replay, full reverse execution, arbitrary event/runtime generation, full behavioral mirrors, or broader SM83 adapter unification.

## Implementation Note - Compact History Trust Markers

Date: 2026-05-18.

Problem:

- `tools/debugger/reverse_query.py` treated compact `write_index.history` as trusted when it carried claim-shaped metadata such as `evidence_source`, `evidence_status`, `runtime_observation`, or `model_source`.
- That was too broad for arbitrary supplied compact reports: concrete `seq` / `pc` / address fields plus descriptive metadata can identify a bounded writer candidate, but should not become `instruction_observed` proof without typed evidence atoms or an explicit effect-trace write-index source marker.
- Entry-level compact-index source markers were also not inherited into normalized history items, so an explicit `history_source=effect_trace.write_index` marker on the write-index entry could be lost.

Implemented fix:

- `trusted_compact_history()` now promotes compact index history only when:
  - typed `evidence_atoms` are present, or
  - `history_source=effect_trace.write_index`, or
  - `effect_trace_schema_version` is present.
- `normalize_index_history()` now inherits `history_source` and `effect_trace_schema_version` from the write-index entry into each history item when the item did not carry its own marker.
- `result_validation()` exposes the inherited `history_source` and `effect_trace_schema_version` additively so consumers can see why compact history was or was not trusted.

Regression strengthened:

- `test_reverse_query_index_history_only_claim_metadata_without_source_marker_is_planned`
  - verifies concrete compact history with `evidence_source`, `evidence_status`, `runtime_observation`, and `model_source` but no trusted source marker remains `planned_only`.
- `test_reverse_query_index_history_only_trusts_explicit_effect_trace_write_index_source`
  - verifies entry-level `history_source=effect_trace.write_index` and `effect_trace_schema_version` are inherited and allow compact effect-trace write-index history to remain `instruction_observed`.
- Existing compact-history regressions still verify generated `effect_trace.write_index` operand history stays usable and untrusted compact history stays planned.

Validation after patch:

- Focused compact-history regressions: 5 passed.
- Full debugger suite: 432 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile`, `git diff --check`, and trailing-whitespace checks passed for touched debugger files.

Remaining priority from Pro:

- This closes another compact-report proof-promotion path, but it does not implement emulator-backed checkpoint replay, full reverse execution, arbitrary event/runtime generation, full behavioral mirrors, or broader SM83 adapter unification.

## Implementation Note - Dynamic-Taint Public Finding Proof Metadata

Date: 2026-05-18.

Problem:

- `tools/debugger/dynamic_taint.py` still let proofless public dynamic-taint findings promote inside `build_paths()` because missing `proof_status` defaulted to `instruction_observed`.
- Public instruction-trace engine findings also did not carry the sink match metadata that richer write attributions already expose, so downstream consumers could not distinguish exact sink matches from bus-address-unverified bank matches.
- That left a legacy/secondary consumer path where a tainted engine finding with no explicit proof metadata could become `taint_proven` by default.

Implemented fix:

- `build_paths()` now defaults missing dynamic-finding proof to `planned_only`.
- Instruction-trace engine findings now preserve additive public metadata:
  - `source_kind=instruction_trace_taint_engine`
  - `proof_status`
  - `address_key`
  - `match_precision`
  - `bank_match`
  - `bank_source`
  - `proof_downgrade_reason`
  - match evidence strings
- Engine findings derive their public proof status from the same sink-match classifier used by write attributions, so `bus_address_unverified_bank` remains `planned_only` instead of promoting through taint.

Regression strengthened:

- `test_dynamic_taint_path_defaults_proofless_finding_to_planned`
  - verifies legacy/proofless dynamic findings remain `planned_only` in `build_paths()`.
- `test_dynamic_taint_public_engine_finding_preserves_bank_unverified_match_proof`
  - verifies public engine findings carry bank-unverified match metadata and produce planned-only dynamic paths.
- Adjacent dynamic-taint attribution, bank-downgrade, evidence-atom, and proof-consumer regressions still pass.

Validation after patch:

- Focused public-finding proof regressions: 2 passed.
- Adjacent dynamic-taint/proof-consumer regressions: 6 passed.
- Full debugger suite: 434 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile`, `git diff --check`, and trailing-whitespace checks passed for touched debugger files.

Remaining priority from Pro:

- This closes the remaining dynamic-taint public-finding proof-promotion path found in this pass, but it does not implement emulator-backed checkpoint replay, full reverse execution, arbitrary event/runtime generation, full behavioral mirrors, or broader SM83 adapter unification.

## Implementation Note - Supplied Emulator Replay Validation Preservation

Date: 2026-05-18.

Problem:

- Reverse-query checkpoint validation had a structured `emulator_replay_validation` slot, but successful checkpoint validation always populated it with `not_run`.
- If a future or adjacent effect report supplied real emulator replay evidence on a retained checkpoint, `tools/debugger/reverse_query.py` would drop that evidence at the checkpoint-validation boundary.
- That made the schema ready for future replay only in shape, not in data flow.

Implemented fix:

- `checkpoint_validation()` now derives additive emulator replay fields from the selected checkpoint when present:
  - `emulator_replay`
  - `emulator_replay_status`
  - `emulator_replay_validation`
- `compact_checkpoint()` now preserves supplied replay validation objects on retained checkpoints.
- `bounded_span_checkpoint_context()` now carries checkpoint replay evidence separately as:
  - `checkpoint_emulator_replay`
  - `checkpoint_emulator_replay_status`
  - `checkpoint_emulator_replay_validation`
- Modeled effect-span validation still keeps its own `validation_kind=modeled_effect_span`, `emulator_replay=False`, and non-emulator replay slot unless an actual span-level emulator replay validator is implemented.

Regression strengthened:

- `test_reverse_query_preserves_supplied_emulator_replay_validation_from_checkpoint`
  - verifies a checkpoint carrying supplied `emulator_replay_validation={attempted: true, status: passed, ...}` survives checkpoint validation, compact checkpoint JSON, and bounded-span checkpoint context.
- Existing non-emulator checkpoint regressions still verify ordinary trace-frame checkpoints remain `not_run` and do not claim emulator replay.

Validation after patch:

- Focused supplied replay preservation regression: 1 passed.
- Adjacent checkpoint/reverse-query regressions: 6 passed.
- Full debugger suite: 435 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile`, `git diff --check`, and trailing-whitespace checks passed for touched debugger files.

Remaining priority from Pro:

- This preserves real replay evidence when a report supplies it, but it does not yet restore and rerun emulator save states itself. Actual emulator-backed checkpoint replay, full reverse execution, arbitrary event/runtime generation, full behavioral mirrors, and broader SM83 adapter unification remain blocking work.

## Implementation Note - Event Runtime Materialization Proof-State Integration

Date: 2026-05-18.

Context:

- Claude worked a parallel event-runtime materialization slice in an isolated worktree, but no patch file was present in the parent worktree.
- The parent worktree is authoritative, so the slice was reimplemented and validated against the current 435+ test debugger surface rather than Claude's older 189-test branch baseline.

Problem:

- Content scenarios and content-state materializations had runtime proof routes, but they did not carry a stable proof-state vocabulary from planned route through state materialization to observed runtime evidence.
- Compare/mirror consumers could not distinguish a ready state patch, an executed state patch, and a behavior actually observed through runtime sinks without relying on loose status strings.
- Generic expectation evidence collection could accidentally treat nested route metadata as additional scenario preconditions unless route internals were guarded.

Implemented fix:

- `tools/debugger/content_scenarios.py`
  - adds `PROOF_STATUS_PROGRESSION=(planned_only, ready_to_run, state_materialized, executed, observed)`.
  - adds `RUNTIME_ROUTE_PROFILES` and `event_runtime_materialization_route()`.
  - attaches `event_runtime_materialization_route` to generated state preconditions with required inputs, expected proof commands, expected/actual proof status, expected sinks, observed sinks, and route kind.
- `tools/debugger/content_state.py`
  - propagates route records onto every materialization.
  - emits materialization-level `actual_proof_status`, `expected_proof_status`, `expected_sinks`, and `observed_sinks`.
  - promotes patch-backed materializations to `state_materialized` only after executed patch verification.
- `tools/debugger/state_space.py`
  - emits patch-level and report-level `actual_proof_status`, `expected_proof_status`, `expected_sinks`, and `observed_sinks`.
  - promotes verified executed patches to `state_materialized`.
- `tools/debugger/mirrors.py`
  - accepts `runtime_observations` as a Python kwarg and harvests top-level `runtime_observations` from loaded reports.
  - adds `mirror_status`, `actual_proof_status`, `expected_proof_status`, `expected_sinks`, `observed_sinks`, and `runtime_evidence_gaps` to content-state behavioral mirror matches.
  - requires both state-materialized floor and full expected-sink observation before marking the mirror `passed`.
- `tools/debugger/expect.py`
  - ignores nested `event_runtime_materialization_route` internals as scenario-precondition evidence, keeping existing expectation counts stable.

Regression strengthened:

- New test module: `tools/debugger/tests/test_event_runtime_materialization.py`.
- The 13 new tests cover:
  - route attachment on map/script/output scenarios;
  - route expected/observed sink fields;
  - content-state ready, blocked, planned-output, and executed proof-state propagation;
  - generic state-space ready/executed proof fields;
  - compare mirror status for ready, state-materialized, observed, and loaded-report runtime-observation paths.
- Existing expectation, content-state, compare, and state-space regressions still pass.

Validation after patch:

- Focused event-runtime materialization tests: 13 passed.
- Adjacent compatibility regressions: 14 passed after the expectation-consumer guard.
- Full debugger suite: 448 tests passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile`, `git diff --check`, and trailing-whitespace checks passed for touched debugger files.

Remaining priority from Pro:

- This establishes the proof-state carrier for event runtime materialization and mirror gating, but it does not implement full arbitrary event-engine generation, full script VM behavior under arbitrary context, pixel/audio behavioral mirrors, or side-effect-complete reverse execution. The goal remains incomplete and `ready=False` remains correct.

## Implementation Note - Claude Event Runtime Contract Reconciliation

Date: 2026-05-18.

Context:

- Claude later delivered `C:\Users\lolno\Downloads\claude_event_runtime_materialization.patch`, scoped to `content_scenarios.py`, `content_state.py`, `mirrors.py`, `state_space.py`, and `tests/test_event_runtime_materialization.py`.
- The patch did not apply over the parent worktree because the same slice had already been integrated against the newer debugger surface, so the parent implementation was reconciled to Claude's public contract additively instead of applying the patch over local edits.

Implemented fix:

- `content_scenarios.py` now exposes the named proof constants and `EVENT_RUNTIME_ROUTE_KIND="event_runtime_materialization"`.
- Route records keep the existing compatibility key `event_runtime_materialization_route` and also expose Claude's `event_runtime_materialization` key.
- `event_runtime_materialization_route()` accepts the Claude-style keyword shape (`precondition_id`, `source_file`, `actual_proof_status`, `observed_sinks`) while preserving the existing parent callers.
- `content_state.py` accepts either route key on input, normalizes old route-kind values to `event_runtime_materialization`, and writes both route keys on output.
- `mirrors.py` reads expected sinks from either route key.
- `expect.py` ignores both the legacy route-kind name and the reconciled route kind when collecting structured precondition evidence.

Regression strengthened:

- Focused event-runtime materialization tests now include 15 cases, including Claude-key-only input and Claude-signature helper construction.

Validation after reconciliation:

- Focused event-runtime materialization tests: 15 passed.
- Adjacent `test_catalog` plus event-runtime tests: 450 passed.
- Full debugger suite: 450 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` and `git diff --check` passed for touched debugger files.

Remaining priority from Pro:

- This only reconciles the proof-state carrier contract. Full arbitrary event-engine generation, full script VM behavior under arbitrary context, pixel/audio behavioral mirrors, side-effect-complete reverse execution, and a genuinely green audit remain incomplete.

## Implementation Note - Output Mirror Runtime Evidence Proof Gating

Date: 2026-05-18.

Context:

- Output-sink behavioral mirrors accepted any loaded runtime evidence record mentioning a requested output symbol or address.
- That could promote weak evidence into `mirror_passed`, including `planned_only` dynamic-taint paths and executed content-state metadata that only proves a save-state materialization, not an output helper reaching the sink at runtime.

Implemented fix:

- `tools/debugger/mirrors.py`
  - classifies output-mirror coverage through explicit runtime evidence kinds only: watch, replay-watch, instruction trace, effect trace, dynamic taint, visual snapshot, and audio snapshot.
  - requires strong proof status for dynamic-taint output coverage; `planned_only` dynamic-taint evidence is kept as weak diagnostic evidence and does not cover a sink.
  - treats `content_state` evidence as weak for output-sink mirror coverage because state materialization is not output behavior observation.
  - adds `weak_runtime_reports`, `weak_runtime_kinds`, and `runtime_evidence_gaps` to output mirror matches without removing legacy fields.
  - emits proof status on runtime evidence records so downstream output mirror coverage can distinguish observed evidence from planned or state-materialized evidence.

Regression strengthened:

- `test_compare_output_sink_mirror_ignores_planned_dynamic_taint_evidence`
  - verifies a planned-only dynamic-taint path mentioning `wTilemap` does not pass an output mirror.
- `test_compare_output_sink_mirror_does_not_pass_from_content_state_metadata`
  - verifies executed content-state output metadata does not pass an output mirror by itself.
- Existing effect-trace output mirror pass coverage still verifies real modeled runtime writes can pass the mirror.

Validation after patch:

- Focused output-mirror regressions plus effect-trace pass case: 3 passed.
- Adjacent runtime expectation, content-fuzz, and output-mirror regressions: 5 passed.
- Full `test_catalog`: 437 passed.
- Focused event-runtime materialization tests: 15 passed.
- Full debugger suite: 452 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` and `git diff --check` passed for touched debugger files.

Remaining priority from Pro:

- This removes another mirror proof-promotion path, but it does not implement emulator-backed checkpoint replay, full reverse execution, arbitrary event/runtime generation, full behavioral mirrors, or broader SM83 adapter unification.

## Implementation Note - Real Runtime Reports Feed Content-State Mirror Observations

Date: 2026-05-18.

Context:

- Content-state behavioral mirrors could already pass from synthetic top-level `runtime_observations`.
- Real runtime report shapes, especially `unified_debugger_watch_report` and nested replay `watch_report`, were not converted into the same observation stream.
- That meant an executed content-state route plus an actual watch/replay-watch hit on every expected sink could still stop at `state_materialized` instead of becoming observed mirror evidence.

Implemented fix:

- `tools/debugger/mirrors.py`
  - derives runtime observations from strong runtime evidence records emitted by loaded reports.
  - includes watch, replay-watch, instruction trace, effect trace, strong dynamic taint, visual snapshot, and audio snapshot evidence.
  - keeps content-state metadata out of this derived observation stream, so state materialization alone still cannot pass a behavioral mirror.
  - normalizes both `scenario_id` and `scenario_ids`, including replay `input_scenario_ids` and replay target scenario IDs, before applying observations to content-state mirror scenarios.
  - preserves address observations alongside symbol observations so address-sink routes can be covered by real watch/replay evidence.

Regression strengthened:

- `test_compare_harvests_runtime_observations_from_watch_report_events`
  - verifies a content-state mirror with expected `wMapGroup`/`wMapNumber` sinks passes when a loaded watch report has real watch-change events for both sinks.
- `test_compare_harvests_runtime_observations_from_replay_watch_report`
  - verifies the same promotion works through a replay report's nested `watch_report`.
- Existing tests still verify content-state-only reports do not pass mirrors without runtime observations.

Validation after patch:

- Focused new watch/replay-watch observation regressions: 2 passed.
- Full event-runtime materialization tests: 17 passed.
- Adjacent content-state, runtime expectation, and output-mirror regressions: 6 passed.
- Full `test_catalog`: 437 passed.
- Full debugger suite: 454 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` and `git diff --check` passed for touched debugger files.

Remaining priority from Pro:

- This connects existing real runtime reports to content-state behavioral mirror gating, but it does not implement emulator-backed checkpoint replay, full reverse execution, arbitrary event/runtime generation, full behavioral mirrors, or broader SM83 adapter unification.

## Implementation Note - Content Fuzz Behavioral Mirror Runtime Gating

Date: 2026-05-18.

Context:

- `content_fuzz_behavioral_mirror` described generated content runtime routes, but it did not expose `status`, `proof_status`, `mirror_status`, expected sinks, observed sinks, or runtime evidence gaps.
- A generated script/map/movement/audio/UI fuzz route could be handed to replay/setup/trace tools, but compare could not distinguish "planned route" from "real watch/replay evidence observed every declared sink."

Implemented fix:

- `tools/debugger/mirrors.py`
  - passes the already normalized runtime observation stream into content-fuzz mirror construction.
  - derives expected fuzz sinks from runtime-target watch symbols/addresses, state-precondition watch symbols, and declared output sinks.
  - emits `status`, `proof_status`, `mirror_status`, `actual_proof_status`, `expected_proof_status`, `expected_sinks`, `observed_sinks`, and `runtime_evidence_gaps` on content-fuzz mirror matches.
  - keeps no-runtime content-fuzz mirrors at `status=planned`, `proof_status=planned_only`, and `mirror_status=planned_only`.
  - promotes content-fuzz mirrors to `passed` / `mirror_passed` only when real runtime observations cover every declared expected sink for the scenario set.

Regression strengthened:

- `test_compare_plan_consumes_content_fuzz_behavioral_mirror`
  - now verifies generated script fuzz mirrors expose planned proof state and expected runtime sinks when no runtime evidence is supplied.
- `test_compare_content_fuzz_mirror_passes_with_real_watch_observations`
  - verifies a generated script fuzz mirror promotes to `passed` only after a real watch report observes every declared script-entry sink.

Validation after patch:

- Focused content-fuzz mirror regressions: 2 passed.
- Adjacent content-fuzz compare/investigate/generate/suggest/dynamic-taint handoff regressions: 5 passed.
- Full `test_catalog`: 438 passed.
- Event-runtime materialization tests: 17 passed.
- Full debugger suite: 455 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` and `git diff --check` passed for touched debugger files.

Remaining priority from Pro:

- This gives generated content fuzz mirrors real runtime-observation gating, but it still does not implement arbitrary event-engine state generation, full script VM execution semantics, pixel/audio behavioral mirrors, emulator-backed checkpoint replay, full reverse execution, or broader SM83 adapter unification.

## Implementation Note - Content Fuzz Runtime Attempt Outcomes

Date: 2026-05-18.

Context:

- `content_fuzz_behavioral_mirror` could now pass from real runtime observations, but the no-evidence path still collapsed two different states:
  - no runtime watch/replay attempt was supplied.
  - a runtime watch/replay attempt ran against the expected sinks and observed no expected sink changes.
- That made an executed but empty watch report look like a planned route instead of a failed behavioral mirror attempt.

Implemented fix:

- `tools/debugger/mirrors.py`
  - adds a runtime-attempt stream alongside runtime observations.
  - extracts attempted sinks from executed watch reports, watch report `watches`, watch report events, and nested replay watch reports.
  - keeps observations as the only path to `mirror_passed`.
  - reports no-attempt content fuzz mirrors as `status=planned`, `proof_status=planned_only`, `mirror_status=not_run`, and `actual_proof_status=planned_only`.
  - reports an attempted full expected sink set with no observed expected sink changes as `status=failed`, `proof_status=mirror_failed`, `mirror_status=failed`, and `actual_proof_status=runtime_observed`.
  - adds `attempted_sinks`, `runtime_attempt_reports`, and `runtime_attempt_kinds` to the content-fuzz mirror match without removing existing fields.

Regression strengthened:

- `test_compare_plan_consumes_content_fuzz_behavioral_mirror`
  - now verifies no supplied runtime report is explicitly `mirror_status=not_run`.
- `test_compare_content_fuzz_mirror_fails_when_watch_attempt_observes_no_expected_sinks`
  - verifies an executed watch attempt over every expected script sink with zero events becomes a failed mirror attempt.
- `test_compare_content_fuzz_mirror_fails_when_replay_watch_attempt_observes_no_expected_sinks`
  - verifies a nested replay watch attempt inherits the replay target sinks and becomes a failed mirror attempt when no expected sink changes are observed.
- `test_compare_content_fuzz_mirror_passes_with_real_watch_observations`
  - continues to verify that full watch observations promote the same mirror to `passed`.

Validation after patch:

- Focused content-fuzz attempt regressions: 4 passed.
- Adjacent content-fuzz compare/investigate/generate/suggest/dynamic-taint handoff regressions: 6 passed.
- Event-runtime materialization tests: 17 passed.
- Full `test_catalog`: 440 passed.
- Full debugger suite: 457 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.

Remaining priority from Pro:

- This closes another behavioral mirror claim-calibration gap, but it still does not implement arbitrary event-engine state generation, full script VM execution semantics, pixel/audio behavioral mirrors, emulator-backed checkpoint replay, full reverse execution, or broader SM83 adapter unification.

## Implementation Note - Content-State Runtime Attempt Outcomes

Date: 2026-05-18.

Context:

- `content_state_behavioral_mirror` could pass from real runtime observations and correctly stopped at `state_materialized` without runtime evidence.
- It still did not distinguish "no runtime attempt was supplied" from "a replay/watch attempt ran over every expected sink and observed no expected sink changes."
- That left an executed but empty watch/replay-watch report looking like an unattempted materialized route.

Implemented fix:

- `tools/debugger/mirrors.py`
  - feeds the runtime-attempt stream into content-state mirror construction.
  - carries `attempted_sinks`, `runtime_attempt_reports`, and `runtime_attempt_kinds` on content-state mirror matches.
  - keeps no-attempt materialized routes at `mirror_status=state_materialized`, preserving the materialization proof floor.
  - keeps observations as the only path to `mirror_status=passed`.
  - reports a materialized route whose watch/replay-watch attempt covers every expected sink but observes no expected sink changes as `status=failed`, `proof_status=mirror_failed`, `mirror_status=failed`, and `actual_proof_status=runtime_observed`.
  - treats partial attempted sink coverage as inconclusive rather than a mirror failure.

Regression strengthened:

- `test_compare_fails_state_materialized_route_when_watch_attempt_observes_no_expected_sinks`
  - verifies an executed watch report with the expected map-position sinks and zero events fails the content-state behavioral mirror.
- `test_compare_fails_state_materialized_route_when_replay_watch_attempt_observes_no_expected_sinks`
  - verifies the same failure through a nested replay watch report that inherits replay target sinks.
- Existing content-state runtime observation tests still verify full watch/replay-watch observations promote the mirror to `passed`.

Validation after patch:

- Focused content-state runtime attempt regressions plus existing no-evidence/pass cases: 5 passed.
- Event-runtime materialization tests: 19 passed.
- Full `test_catalog`: 440 passed.
- Full debugger suite: 459 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.

Remaining priority from Pro:

- This closes the same attempted-but-empty runtime boundary for materialized content-state mirrors, but it still does not implement arbitrary event-engine state generation, full script VM execution semantics, pixel/audio behavioral mirrors, emulator-backed checkpoint replay, full reverse execution, or broader SM83 adapter unification.

## Implementation Note - Output-Sink Runtime Attempt Outcomes

Date: 2026-05-18.

Context:

- `content_output_behavioral_mirror` already required strong runtime evidence before promoting output sinks to `mirror_passed`.
- It still treated an executed watch/replay-watch attempt over every requested output sink with zero observed output changes as merely `planned`.
- That hid a real negative runtime attempt for UI/audio/asset output mirrors.

Implemented fix:

- `tools/debugger/mirrors.py`
  - feeds scenario-scoped runtime attempts into output-sink mirror status.
  - matches attempted output symbols and normalized attempted output addresses against requested output sinks.
  - keeps strong runtime evidence as the only path to `status=passed`, `proof_status=mirror_passed`.
  - reports full attempted output coverage with no observed output write as `status=failed`, `proof_status=mirror_failed`, `mirror_status=failed`, and `actual_proof_status=runtime_observed`.
  - adds `attempted_output_count`, `attempted_symbols`, `attempted_addresses`, `runtime_attempt_reports`, `runtime_attempt_kinds`, `mirror_status`, and `actual_proof_status` to output mirror matches without removing existing fields.
  - keeps partial attempts inconclusive rather than treating them as a mirror failure.

Regression strengthened:

- `test_compare_output_sink_mirror_fails_when_watch_attempt_observes_no_outputs`
  - verifies an executed watch over `wTilemap` and `wAttrmap` with zero events fails the output mirror.
- `test_compare_output_sink_mirror_fails_when_replay_watch_attempt_observes_no_address_output`
  - verifies a nested replay watch attempt over `$9800` with zero events fails the output mirror.
- Existing output mirror regressions still verify strong effect-trace evidence passes, planned dynamic taint stays weak, and content-state metadata alone cannot pass.

Validation after patch:

- Focused output attempt/pass/weak-evidence regressions: 5 passed.
- Event-runtime materialization tests: 19 passed.
- Full `test_catalog`: 442 passed.
- Full debugger suite: 461 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.

Remaining priority from Pro:

- This closes the attempted-but-empty runtime boundary across content-state, content-fuzz, and output-sink mirrors. The remaining full-goal blockers are still real: arbitrary event-engine state generation, full script VM execution semantics, pixel/audio behavioral mirrors, emulator-backed checkpoint replay, full reverse execution, and broader SM83 adapter unification.

## Implementation Note - Compact Effect-Index Output Mirror Boundary

Date: 2026-05-19.

Context:

- `content_output_behavioral_mirror` could promote an effect-trace report to `mirror_passed` from `write_index` alone.
- That meant a compact/index-only report with `write_count > 0` and no concrete effect events could pass an output-sink mirror.
- This violated the current proof rule: compact or proofless evidence must not become runtime, instruction, taint, causal, or mirror proof.

Implemented fix:

- `tools/debugger/mirrors.py`
  - requires concrete effect events or strong write watch hits before effect-trace output evidence can cover an output sink.
  - keeps compact `write_index` evidence as weak diagnostic evidence with `proof_status=planned_only`.
  - adds `proof_downgrade_reason` to weak runtime evidence records and includes that reason in output mirror evidence gaps.
  - requires every output runtime evidence record to carry an explicit strong proof status before it can cover an output sink.

Regression strengthened:

- `test_compare_output_sink_mirror_does_not_pass_from_compact_effect_index`
  - verifies a compact effect-trace `write_index` with no concrete `events` stays `planned_only`, appears as weak effect-trace evidence, and does not create ranked `mirror_passed` findings.
- Existing output mirror tests still verify real concrete effect traces can pass and planned dynamic-taint/content-state metadata cannot.

Validation after patch:

- Focused compact/effect/output mirror regression: passed.
- Adjacent output mirror regressions: 6 passed.
- Full debugger suite: 462 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.

Remaining priority from Pro:

- This closes another proof-promotion boundary at the mirror/report consumer layer. It does not implement arbitrary event-engine state generation, full script VM execution semantics, full pixel/audio behavioral mirrors, emulator-backed checkpoint replay, full reverse execution, or broader SM83 adapter unification. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Visualization Timeline Proof Preservation

Date: 2026-05-19.

Context:

- Visualization timeline events for dynamic-taint paths, dynamic writes, reverse queries, causal paths, compare matches, ranked findings, and impact items could omit explicit `proof_status`.
- A planned or downgraded path could still appear as a high-severity visualization event, and downstream ranked visualization findings had to infer proof from generic text.
- That was another UI/report boundary where proof vectors were easy to lose.

Implemented fix:

- `tools/debugger/visualization.py`
  - adds optional `proof_status` to timeline events.
  - appends `proof=<status>` to timeline details when a proof status is supplied and the detail does not already include one.
  - passes source proof status through major causal/report timeline paths: reverse query, causal explanation/graph, trace-index reverse attribution, dynamic-taint trace synthesis/path/write, impact items, ranked findings, and compare-plan matches.
- `tools/debugger/ranking.py`
  - ranked visualization findings now preserve timeline `proof_status` instead of relying on inference.
  - finding evidence now includes `proof_status=<status>` when present.

Regression strengthened:

- `test_visualization_timeline_preserves_planned_dynamic_taint_proof_status`
  - verifies a high-severity `planned_only` dynamic-taint path keeps `proof_status=planned_only` in the visualization timeline and in ranked visualization findings.

Validation after patch:

- Focused visualization proof regression: passed.
- Related proof-boundary cluster: 5 passed.
- Full debugger suite: 463 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.

Remaining priority from Pro:

- This closes a visualization/report proof-preservation leak. It does not implement arbitrary event-engine state generation, full script VM execution semantics, full pixel/audio behavioral mirrors, emulator-backed checkpoint replay, full reverse execution, or broader SM83 adapter unification. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Impact Merge Mixed-Proof Preservation

Date: 2026-05-19.

Context:

- Impact aggregation merged duplicate items by keeping only the strongest scalar `proof_status`.
- That preserved older JSON consumers, but it could hide that a single finding mixed `planned_only` evidence with `taint_proven`, `instruction_observed`, or other stronger proof.
- The proof-substrate rule requires report/UI/impact boundaries to preserve proof vectors, proof min/max, source-specific proof, and mixed-proof display rather than silently promoting the whole finding.

Implemented fix:

- `tools/debugger/impact.py`
  - keeps compatibility by leaving merged `proof_status` as the strongest observed status.
  - adds mixed-proof fields when duplicate items carry different proof statuses: `proof_statuses`, `proof_min`, `proof_max`, and `proof_badge=mixed`.
  - appends `proof_statuses=...`, `proof_min=...`, and `proof_max=...` to merged evidence text.
  - merges `proof_status_by_source` maps instead of dropping one duplicate item's source proof.
  - merges `proof_vector` entries from duplicate items when present.

Regression strengthened:

- `test_impact_merge_preserves_mixed_proof_status_vector`
  - failed before the patch because duplicate impact items had no `proof_statuses`.
  - now verifies the merged item keeps `proof_status=taint_proven` for compatibility while exposing `proof_statuses=["planned_only", "taint_proven"]`, `proof_min=planned_only`, `proof_max=taint_proven`, `proof_badge=mixed`, merged source proof, and mixed-proof evidence strings.

Validation after patch:

- Focused mixed-proof impact regression: passed.
- Related proof-boundary cluster: 4 passed.
- Full debugger suite: 464 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed.

Remaining priority from Pro:

- This closes another impact/report proof-promotion leak. It does not implement arbitrary event-engine state generation, full script VM execution semantics, full pixel/audio behavioral mirrors, emulator-backed checkpoint replay, full reverse execution, or broader SM83 adapter unification. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Proofless Register-Provenance Boundary

Date: 2026-05-19.

Context:

- Rank and impact reports already default proofless dynamic-taint paths and write attributions to `planned_only`.
- Causal graph and visualization still had a narrower register-provenance leak:
  - synthetic register provenance created from a `via_register` operand could default to `instruction_observed`;
  - graph edges such as `feeds_register` and `taints_register` could become `taint_proven` from a proofless attribution;
  - visualization register-provenance timeline events could omit the proof floor entirely.
- That allowed a report/UI boundary to make proofless or legacy attribution data look observed/proven.

Implemented fix:

- `tools/debugger/causal_graph.py`
  - defaults proofless dynamic write attributions and synthetic register provenance to `planned_only`.
  - only upgrades register-taint edges to `taint_proven` when the attribution proof is runtime/instruction/taint-backed.
  - keeps proofless/planned `feeds_register` and `taints_register` edges at `planned_only`.
- `tools/debugger/visualization.py`
  - gives dynamic write, operand, register-provenance, and register-taint graph nodes/edges an explicit planned proof floor when the source attribution has no proof.
  - adds `proof_status` to register-provenance timeline events, so markdown/HTML/ranking consumers see `proof=planned_only` rather than an unqualified causal event.

Regression strengthened:

- `test_graph_and_visualization_keep_proofless_register_provenance_planned`
  - failed before the patch because causal-graph register-provenance nodes could carry `instruction_observed`.
  - now verifies graph provenance nodes, `feeds_register`/`taints_register` edges, visualization provenance nodes, and timeline provenance events all stay `planned_only` for proofless dynamic-taint attribution input.
- Observed register-provenance tests still verify real direct/effect trace chains keep their observed and taint-proven edges.

Validation after patch:

- Focused proofless register-provenance regression: passed.
- Related observed/proofless register-provenance cluster: 4 passed.
- Full debugger suite: 465 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed.

Remaining priority from Pro:

- This closes another causal graph/visualization proof-promotion boundary. It does not implement arbitrary event-engine state generation, full script VM execution semantics, full pixel/audio behavioral mirrors, emulator-backed checkpoint replay, full reverse execution, or broader SM83 adapter unification. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Empty Snapshot Runtime-Proof Boundary

Date: 2026-05-19.

Context:

- Visual and audio snapshot consumers could preserve or infer `runtime_observed` from an `executed=True` report, even when the report carried no sampled visual surfaces, framebuffer, IO registers, audio registers, audio symbols, or wave RAM.
- That made report/UI boundaries trust an execution-looking envelope instead of runtime-visible evidence.
- This was especially risky for the remaining graphics/audio mirror work: empty or malformed snapshot reports must not become runtime proof.

Implemented fix:

- `tools/debugger/ranking.py`
  - visual/audio snapshot findings now require concrete runtime samples before using `runtime_observed`.
  - empty executed-looking reports are downgraded to `planned_only`.
  - evidence now includes `runtime_samples=<bool>` and `proof_downgrade_reason=no_visual_runtime_samples` or `proof_downgrade_reason=no_audio_runtime_samples` when downgraded.
- `tools/debugger/causal_graph.py`
  - visual/audio snapshot graph nodes and sampled-state edges now use the same runtime-sample gate.
  - empty executed-looking snapshot reports remain `planned_only` in graph proof.
- `tools/debugger/visualization.py`
  - visual/audio snapshot timeline events and graph nodes/edges now carry explicit proof status.
  - empty executed-looking reports show `proof=planned_only` plus the downgrade reason in timeline detail.

Regression strengthened:

- `test_snapshot_consumers_do_not_promote_empty_executed_reports_to_runtime`
  - failed before the patch because ranked visual snapshot proof was `runtime_observed`.
  - now verifies rank, impact, causal graph, visualization graph, and visualization timeline all keep empty executed-looking visual/audio snapshots at `planned_only`.
- Existing visual/audio snapshot tests still verify real sampled UI surfaces, framebuffer, audio registers, symbol state, and wave RAM promote to `runtime_observed`.

Validation after patch:

- Focused empty-snapshot runtime-proof regression: passed.
- Existing sampled visual/audio snapshot regressions: 4 passed.
- Full debugger suite: 466 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed.

Remaining priority from Pro:

- This closes another graphics/audio report-boundary proof leak. It does not implement arbitrary event-engine state generation, full script VM execution semantics, full pixel/audio behavioral mirrors, emulator-backed checkpoint replay, full reverse execution, or broader SM83 adapter unification. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Proofless Dynamic-Taint Visualization Boundary

Date: 2026-05-19.

Context:

- Rank and impact already default proofless dynamic-taint paths to `planned_only`.
- Causal graph also normalizes missing dynamic-taint path proof to `planned_only`.
- Visualization still omitted the proof floor for proofless dynamic-taint paths:
  - timeline `taint_path` events could appear without `proof_status`;
  - visualization graph taint source/target nodes and contributor edges could appear without proof status.
- That did not promote the data to `taint_proven`, but it still lost the required proof floor at a report/UI boundary.

Implemented fix:

- `tools/debugger/visualization.py`
  - dynamic-taint timeline path events now default missing proof to `planned_only`.
  - graph taint target/source nodes and contributor edges now carry the same explicit proof.
  - proofless dynamic-taint visualization details now include `proof=planned_only`.

Regression strengthened:

- `test_graph_and_visualization_default_proofless_dynamic_taint_path_to_planned`
  - failed before the patch because the visualization timeline event had no `proof_status`.
  - now verifies causal graph path proof remains planned and visualization timeline/graph proof is explicitly `planned_only` for legacy proofless dynamic-taint paths.
- Adjacent dynamic-taint proof-boundary tests still verify planned paths stay planned and real register-provenance paths keep their observed/proven proof.

Validation after patch:

- Focused proofless dynamic-taint visualization regression: passed.
- Adjacent dynamic-taint proof-boundary cluster: 5 passed.
- Full debugger suite: 467 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed.

Remaining priority from Pro:

- This closes another visualization proof-preservation leak. It does not implement arbitrary event-engine state generation, full script VM execution semantics, full pixel/audio behavioral mirrors, emulator-backed checkpoint replay, full reverse execution, or broader SM83 adapter unification. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Trace-Synthesis Visualization Graph Proof Floor

Date: 2026-05-19.

Context:

- Trace-synthesis routes are planned proof routes until the generated content-state, instruction-trace, and dynamic-taint commands are actually executed.
- Rank, impact, and visualization timeline output already carried `planned_only` for trace-synthesis routes.
- Visualization graph output still omitted proof status for trace-synthesis route nodes, planned trace outputs, save-state/source/sink nodes, workflow commands, and their edges.
- That lost the explicit proof floor at a UI/report boundary and made planned runtime routes visually indistinguishable from unqualified graph facts.

Implemented fix:

- `tools/debugger/visualization.py`
  - trace-synthesis graph route nodes now carry the route proof, defaulting to `planned_only`.
  - planned trace-output, save-state, source, sink, source-memory, and workflow-command nodes inherit the same route proof.
  - `plans_trace`, `loads_state`, `watches`, `watches_address`, `seeds_trace`, `seeds_memory`, `labels_memory`, and `runs` edges now preserve that proof.

Regression strengthened:

- `test_rank_impact_report_and_visualize_dynamic_taint_trace_synthesis`
  - now verifies the visualization timeline event and graph route/source/sink nodes and route edges all carry `planned_only`.
  - failed before the patch because the graph `trace_synthesis` node had no `proof_status`.

Validation after patch:

- Focused trace-synthesis visualization regression: passed.
- Adjacent trace-synthesis/dynamic-taint proof cluster: 4 passed.
- Full debugger suite: 467 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed.

Remaining priority from Pro:

- This closes another planned-runtime-route visualization proof leak. It does not implement arbitrary event-engine state generation, full script VM execution semantics, full pixel/audio behavioral mirrors, emulator-backed checkpoint replay, full reverse execution, or broader SM83 adapter unification. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Reverse-Query Visualization Proof Derivation

Date: 2026-05-19.

Context:

- Rank, impact, and causal graph already avoid promoting proofless legacy reverse-query results to observed proof.
- Visualization timeline and graph output only read explicit result/report proof fields.
- A proofless reverse-query result could therefore appear without a visible proof floor in visualization, even when rank/impact correctly treated it as `planned_only`.

Implemented fix:

- `tools/debugger/visualization.py`
  - now derives reverse-query result proof from explicit result proof, validation proof, report proof, or concrete last-writer evidence.
  - falls back to `planned_only` when the result has no concrete last-writer proof.
  - uses the derived proof for reverse-query timeline events and graph nodes.
  - keeps concrete last-writer legacy compatibility by promoting only when a last-writer object has seq, pc, address, and write-like access/kind evidence.

Regression strengthened:

- `test_rank_and_impact_default_proofless_reverse_query_result_to_planned`
  - now also checks visualization timeline and graph proof.
  - failed before the patch because the visualization timeline reverse-query event had no `proof_status`.
- Adjacent reverse-query proof tests still verify planned no-writer cases stay planned and concrete writer cases can be observed.

Validation after patch:

- Focused reverse-query visualization regression: passed.
- Adjacent reverse-query proof cluster: 4 passed.
- Full debugger suite: 467 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed.

Remaining priority from Pro:

- This closes another visualization proof-derivation leak. It does not implement arbitrary event-engine state generation, full script VM execution semantics, full pixel/audio behavioral mirrors, emulator-backed checkpoint replay, full reverse execution, or broader SM83 adapter unification. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Watch Report Visualization Runtime Proof Preservation

Date: 2026-05-19.

Context:

- `unified_debugger_watch_report` events are runtime evidence when the report or event explicitly carries `proof_status="runtime_observed"`.
- Visualization timeline and graph output still omitted that proof status for watch events, watch writer instructions, watched symbols, watched addresses, and their edges.
- That did not create new runtime evidence, but it dropped the explicit proof vector at a UI/report boundary and made runtime watch observations visually indistinguishable from unqualified facts.

Implemented fix:

- `tools/debugger/visualization.py`
  - watch timeline events now preserve event-level proof first, then report-level proof.
  - watch graph event/instruction/symbol/address nodes now carry the same proof.
  - watch graph `writes`, `observes`, and `observes_address` edges now carry the same proof.
  - proofless legacy watch events now receive an explicit conservative `planned_only` floor instead of being silently unqualified.

Regression strengthened:

- `test_visualization_preserves_watch_report_runtime_proof_status`
  - failed before the patch because the watch timeline event had no `proof_status`.
  - now verifies the watch timeline event includes `proof_status=runtime_observed` and `proof=runtime_observed`.
  - now verifies watch graph nodes and edges preserve `runtime_observed`.

Validation after patch:

- Focused watch visualization proof regression: passed.
- Adjacent visualization/watch regressions: 3 passed.
- Full debugger suite: 468 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed.

Remaining priority from Pro:

- This closes another runtime-proof visualization preservation leak. It does not implement arbitrary event-engine state generation, full script VM execution semantics, full pixel/audio behavioral mirrors, emulator-backed checkpoint replay, full reverse execution, or broader SM83 adapter unification. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Instruction-Trace Validation Visualization Proof Preservation

Date: 2026-05-19.

Context:

- `unified_debugger_instruction_trace` reports can carry explicit instruction-level proof on `execution_validation` or the report itself.
- Visualization timeline events for validation hit/ready/partial/miss/limit states did not preserve that proof.
- Visualization graph nodes and edges for validation status, trace output, save states, hit/missed functions, watched symbols, and trace writes also omitted proof status.
- That dropped instruction-observed proof at a UI/report boundary and made executed validation evidence visually indistinguishable from proofless validation records.

Implemented fix:

- `tools/debugger/visualization.py`
  - instruction-trace validation timeline events now preserve validation-level proof first, then report-level proof.
  - validation-limit timeline events use the same proof as the validation event.
  - validation graph nodes and `writes_trace`, `plans_trace`, `loads_state`, `hit`, `missed`, and `observes` edges now carry that proof.
  - proofless validation records now receive an explicit conservative `planned_only` floor.

Regression strengthened:

- `test_visualization_preserves_instruction_trace_validation_proof_status`
  - failed before the patch because validation timeline events had no `proof_status`.
  - now verifies validation timeline events include `proof_status=instruction_observed` and `proof=instruction_observed`.
  - now verifies validation graph nodes and edges preserve `instruction_observed`.

Validation after patch:

- Focused instruction-trace visualization proof regression: passed.
- Adjacent instruction-trace visualization consumer regression: passed.
- Full debugger suite: 469 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed, with unrelated CRLF warnings from the broader dirty worktree.

Remaining priority from Pro:

- This closes another instruction-proof visualization preservation leak. It does not implement arbitrary event-engine state generation, full script VM execution semantics, full pixel/audio behavioral mirrors, emulator-backed checkpoint replay, full reverse execution, or broader SM83 adapter unification. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Played-Input Visualization Proof Boundary

Date: 2026-05-19.

Context:

- Visualization collected top-level `played_inputs` from reports before dispatching by report kind.
- Timeline played-input events omitted proof status entirely.
- Graph played-input nodes and `played_input` edges were always marked `runtime_observed`, even if a malformed, synthetic, or planned report carried `played_inputs` without a valid executed run.
- That was a proof promotion risk at a UI/report boundary: requested/static or proofless played-input records could look like observed runtime input playback.

Implemented fix:

- `tools/debugger/visualization.py`
  - played-input timeline events now carry explicit per-input proof when provided.
  - absent explicit proof, valid executed reports mark played inputs as `runtime_observed`.
  - unexecuted, invalid, or proofless played-input records now stay `planned_only`.
  - played-input graph nodes and `played_input` edges use the same proof rule instead of always forcing `runtime_observed`.

Regression strengthened:

- `test_visualization_does_not_promote_unexecuted_played_inputs_to_runtime`
  - failed before the patch because timeline played-input events had no `proof_status`.
  - also guards the graph-side over-promotion by verifying unexecuted played-input nodes and edges stay `planned_only`.
  - verifies valid executed played-input evidence still displays as `runtime_observed`.

Validation after patch:

- Focused played-input visualization proof regression: passed.
- Adjacent replay/input visualization regressions: 3 passed.
- Full debugger suite: 470 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed, with unrelated CRLF warnings from the broader dirty worktree.

Remaining priority from Pro:

- This closes another runtime-proof promotion leak in visualization. It does not implement arbitrary event-engine state generation, full script VM execution semantics, full pixel/audio behavioral mirrors, emulator-backed checkpoint replay, full reverse execution, or broader SM83 adapter unification. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Observed TIMA Overflow Side-Effect Evidence

Date: 2026-05-20.

Context:

- The replay/localization audit bucket already covered bounded instruction effects, DIV reset writes, IO register writes, DMA expansion, interrupt entry, and observed post-write validation.
- It still had a real hardware side-effect gap around timer overflow behavior: TIMA can reload from TMA and request the timer interrupt between adjacent captured instructions without a CPU instruction write to `$FF05` or `$FF0F`.
- The patch intentionally uses primary Game Boy references and bounded runtime evidence instead of claiming cycle-accurate timer emulation.

Web references used:

- Pan Docs, Timer and Divider Registers: `https://gbdev.io/pandocs/Timer_and_Divider_Registers.html`
- Pan Docs, Interrupts: `https://gbdev.io/pandocs/Interrupts.html`
- Pan Docs, Timer Obscure Behaviour: `https://gbdev.io/pandocs/Timer_Obscure_Behaviour.html`

Implemented fix:

- `tools/debugger/sm83_model.py`
  - adds shared `TimerOverflowSemantics` for the TIMA reload and timer IF request model.
  - adds named constants for `$FF05` TIMA, `$FF06` TMA, `$FF07` TAC, and `$FF0F` IF.
- `tools/debugger/effect_trace.py`
  - detects a conservative adjacent-frame timer-overflow proof only when the current pre-instruction frame observes TIMA=`$FF`, TMA=`X`, IF bit 2 clear, and the next pre-instruction frame observes TIMA=`X` plus IF bit 2 set.
  - emits a `timer_tima_overflow` side effect, a `timer_tima_reload_write` to `$FF05`, and a `timer_interrupt_request_write` to `$FF0F`.
  - labels those effects as `observed_adjacent_timer_overflow` / `observed_hardware_side_effect`.
  - refreshes watch hits after late-attached hardware effects so reverse query and dynamic taint can see the runtime writes.
- `tools/debugger/catalog.py`
  - updates the replay/localization audit wording to name the newly observed TIMA overflow reload and IF timer-interrupt request evidence.

Regression strengthened:

- `test_effect_trace_models_observed_tima_overflow_reload_and_interrupt_request`
  - failed before the patch because no `timer_tima_reload_write` or `timer_interrupt_request_write` existed.
  - now verifies effect trace, write index, watch hits, reverse query, and dynamic taint all preserve the observed hardware side-effect evidence.
- `test_effect_trace_requires_observed_timer_if_transition_for_overflow_proof`
  - guards against over-promotion: a TIMA-looking reload without an observed IF bit-2 transition stays unmodeled/unattributed instead of being promoted to timer-overflow proof.

Validation after patch:

- Focused timer/hardware regression cluster: 5 passed.
- Full debugger suite: 472 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed, with unrelated CRLF warnings from the broader dirty worktree.

Remaining priority from Pro:

- This is a bounded observed hardware side-effect slice, not full reverse execution or full timer emulation. Unobserved timer ticks, cycle-accurate TIMA/TMA/TAC corner cases, arbitrary event-engine state generation, full script VM behavior, pixel-accurate graphics mirrors, and audio playback/mixer mirrors remain blockers. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Visual/Audio Snapshot Runtime Evidence Gate

Date: 2026-05-20.

Context:

- Visual and audio snapshots are useful runtime evidence only when they carry concrete runtime samples from an executed, runtime-proven capture.
- `expect` could still count framebuffer/audio fields from an unexecuted or planned snapshot envelope.
- `compare` could treat an empty executed-looking visual/audio snapshot report as runtime evidence for the dynamic expectation mirror.
- That was another report-boundary promotion risk: JSON fields that looked like samples could become expectation or mirror proof without executed runtime evidence.

Web references used:

- PyBoy screen API: `https://docs.pyboy.dk/api/screen.html`
- PyBoy sound API: `https://docs.pyboy.dk/api/sound.html`

Implemented fix:

- `tools/debugger/expect.py`
  - visual framebuffer expectations now only collect framebuffer evidence from valid, executed snapshots with strong runtime proof and a concrete framebuffer hash/sample field.
  - audio expectations now only collect audio evidence from valid, executed snapshots with strong runtime proof and concrete register, symbol, audio-state, or wave-RAM samples.
- `tools/debugger/mirrors.py`
  - visual/audio snapshot runtime mirror evidence now requires valid executed reports, strong runtime proof, and at least one concrete visual/audio sample.
  - empty executed-looking visual/audio snapshot envelopes no longer satisfy the dynamic expectation mirror's runtime evidence requirement.
  - existing JSON fields remain compatible; this only tightens consumer interpretation.

Regression strengthened:

- `test_expectation_ignores_unexecuted_visual_snapshot_framebuffer`
  - failed before the patch because an unexecuted planned visual snapshot with a `screen_frame` field passed `framebuffer=...`.
- `test_expectation_ignores_audio_snapshot_without_runtime_proof`
  - failed before the patch because an executed-looking but `planned_only` audio snapshot passed `audio-register=...`.
- `test_compare_does_not_promote_empty_snapshot_envelope_to_runtime_expectation_mirror`
  - failed before the patch because empty visual/audio snapshot envelopes were enough to create a passed runtime expectation mirror.

Validation after patch:

- Focused visual/audio snapshot proof-boundary cluster: 6 passed.
- Adjacent compare/expectation mirror cluster: 6 passed.
- Full debugger suite: 475 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed, with unrelated CRLF warnings from the broader dirty worktree.

Remaining priority from Pro:

- This closes a visual/audio expectation and mirror proof-promotion boundary. It does not implement pixel-accurate graphics playback, full audio playback/mixer mirrors, arbitrary event-engine state generation, full script VM behavior, emulator-backed reverse execution, or subsystem-complete causal proof. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Bounded PyBoy Sound-Buffer Snapshot Evidence

Date: 2026-05-20.

Context:

- The previous audio snapshot patch correctly prevented proof promotion from planned or empty audio snapshot envelopes.
- The audio snapshot itself still only exposed CPU-visible audio registers, Wave RAM, audio-state summaries, and music-engine WRAM state.
- Per the PyBoy sound API, executed emulator frames can also expose a bounded sound buffer and metadata such as sample rate, raw-buffer head, and buffer format. That is useful emulator-visible audio evidence, but it is not a full APU or playback-quality mirror.

Web references used:

- PyBoy sound API: `https://docs.pyboy.dk/api/sound.html`

Implemented fix:

- `tools/debugger/audio_snapshot.py`
  - captures `pyboy.sound.ndarray` when PyBoy exposes it, falling back to `pyboy.sound.raw_buffer` if needed.
  - records a bounded `sound_buffer` packet with source, sample rate, raw-buffer metadata, byte count, SHA-256 digest, sample hex, shape/dtype when available, and a `sound_buffer_count`.
  - keeps known limits explicit: the buffer digest/sample proves bounded emulator-visible samples at the capture point, not full song playback or mixer correctness.
- `tools/debugger/expect.py`
  - adds `audio-buffer-sha256=...` expectations.
  - collects sound-buffer evidence only from valid, executed, runtime-proven audio snapshots with concrete runtime samples.
  - keeps planned/proofless sound-buffer-shaped fields out of expectation evidence.
- `tools/debugger/mirrors.py`
  - carries sound-buffer source/digest artifacts into execution-backed expectation mirrors without treating them as sufficient unless the audio snapshot passes the runtime proof gate.
- `tools/debugger/ranking.py`, `tools/debugger/causal_graph.py`, `tools/debugger/visualization.py`, and `tools/debugger/__main__.py`
  - surface sound-buffer source/digest evidence in ranking, graph nodes/edges, visualization, and CLI report output.
- `tools/debugger/catalog.py`
  - updates the differential-mirror audit wording to include bounded PyBoy sound-buffer digest/sample evidence while retaining the full audio playback/mixer blocker.

Regression strengthened:

- `test_expectation_and_compare_use_audio_snapshot_evidence`
  - now verifies `audio-buffer-sha256` expectations, dynamic mirror artifacts, and sound-buffer evidence flow.
- `test_expectation_ignores_audio_snapshot_without_runtime_proof`
  - now verifies sound-buffer-shaped fields in a `planned_only` audio snapshot do not become expectation proof.
- `test_audio_snapshot_captures_registers_symbols_and_visualization`
  - now verifies executed audio snapshots capture PyBoy sound-buffer metadata/digest/sample and expose distinct `audio_sound_buffer` graph/visualization nodes and `samples_audio_sound_buffer` edges.

Validation after patch:

- Focused audio snapshot proof/evidence cluster: passed.
- Full debugger suite: 475 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed, with unrelated CRLF warnings from the broader dirty worktree.

Remaining priority from Pro:

- This upgrades audio snapshots from register/Wave-RAM/WRAM state to bounded emulator-visible sample evidence. It still does not implement full audio playback/mixer mirrors, arbitrary event-engine state generation, full script VM behavior, pixel-accurate graphics/UI behavior, emulator-backed reverse execution, or subsystem-complete causal proof. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Coord-Event Scene Variable Materialization

Date: 2026-05-20.

Context:

- Map coord events are not triggered by position alone; they also include a scene id in the `coord_event x, y, scene_id, script` record.
- The content-state materializer could patch `wMapGroup`, `wMapNumber`, `wXCoord`, and `wYCoord`, then mark the generated map-position state as ready even when the selected coord event required a map-specific scene variable value.
- That left an event-engine generation gap: a positioned state could be ready while still missing the scene gate needed to make `CheckCurrentMapCoordEvents` reach the intended script.

Web references used:

- pret pokecrystal map event script reference: `https://pret.github.io/pokecrystal/map_event_scripts.html`
- upstream pokegold `home/map.asm` reference for coord-event scene checks: `https://git.poke.blue/pokegold/tree/home/map.asm?id=dd73b278b585266922424e09cd99faeeba02a2f4`

Implemented fix:

- `tools/debugger/content_state.py`
  - parses `data/maps/scenes.asm` `scene_var MAP, wMapSceneID` rows into a normalized map-to-scene-variable index.
  - resolves coord-event `SCENE_*` ids from the selected map source's `scene_script` order, matching the local `scene_script` macro behavior.
  - adds a map-specific scene-variable patch to coord-event map-position materializations when the scene var and scene id can be resolved.
  - carries `event_context` with `scene_token`, `scene_symbol`, `scene_value`, `validation_kind=source_scene_var_and_scene_script_order`, and source line/file provenance.
  - adds the scene variable to `watch_symbols`, `expected_sinks`, and route commands so later replay/watch/trace proof has the exact missing state gate in view.
- `tools/debugger/catalog.py`
  - updates the generation/fuzzing audit wording to name coord-event scene-variable patch generation.

Regression strengthened:

- `test_content_state_materializes_coord_event_scene_variable`
  - failed before the patch because coord-event materialization never patched `wUnitMapSceneID`.
  - now verifies scene-variable resolution through `data/maps/scenes.asm`, scene id resolution through `scene_script` order, patch value/address/provenance, watch-symbol inclusion, expected-sink inclusion, and command routing.

Validation after patch:

- Focused content scenario/materialization cluster: passed.
- Full debugger suite: 476 passed.
- `python -m tools.debugger audit`: `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed, with unrelated CRLF warnings from the broader dirty worktree.

Remaining priority from Pro:

- This moves coord-event generation beyond position-only patches, but it still does not synthesize full object structs, full BG/object event facing and flag state, arbitrary event-engine contexts, full script VM behavior, pixel/audio behavioral mirrors, emulator-backed reverse execution, or subsystem-complete causal proof. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - BG-Event Player Facing Materialization

Date: 2026-05-20.

Context:

- BG events are not triggered by standing on the event tile. The event engine derives the tile the player is facing from `wPlayerDirection` and `wPlayerMapX/Y`, converts the buffered map coordinates back to event-table coordinates, then matches that tile against the map's BG-event table.
- The content-state materializer previously patched the target event tile into `wXCoord/wYCoord`, which is not enough for a facing BG event and can be the wrong player position.
- That left another event-engine generation gap: a generated BG-event case could look map-position-ready while missing the player-facing state needed for `CheckFacingBGEvent`.

Web references used:

- pret pokecrystal map event script reference for `bg_event x, y, type, script`: `https://pret.github.io/pokecrystal/map_event_scripts.html`
- upstream pokegold `home/map.asm` reference for `GetFacingTileCoord` and `CheckFacingBGEvent`: `https://git.poke.blue/pokegold/tree/home/map.asm?id=dd73b278b585266922424e09cd99faeeba02a2f4`

Implemented fix:

- `tools/debugger/content_state.py`
  - derives a planned player position and facing direction for BG events from the selected BG-event tile and `BGEVENT_UP/DOWN/LEFT/RIGHT` direction.
  - patches `wXCoord/wYCoord` to the player tile, not the event tile, for BG-event scenarios.
  - patches `wPlayerMapX`, `wPlayerMapY`, and `wPlayerDirection` when those symbols exist, including the +4 buffered-map coordinate offset used by the engine.
  - carries `event_context` / `player_context` with target coordinates, player coordinates, facing direction/value, `validation_kind=event_engine_player_position_and_facing`, and `proof_status=state_patch_planned`.
  - adds the player-map and facing symbols to watch symbols, expected sinks, and commands so later runtime proof has the exact state gate in view.
- `tools/debugger/catalog.py`
  - updates the generation/fuzzing audit wording to name BG-event player-coordinate/facing patch generation.

Regression strengthened:

- `test_content_state_materializes_bg_event_player_facing_state`
  - failed before the patch because BG-event materialization patched `wYCoord` to the event tile instead of the player tile and did not patch `wPlayerMapX/Y` or `wPlayerDirection`.
  - now verifies the player tile, buffered player-map coordinates, facing value, planned proof status, watch-symbol inclusion, expected-sink inclusion, and command routing.

Validation after patch:

- Focused BG-event + coord-event regression pair: passed.
- Focused content scenario/materialization cluster: 9 passed.
- Full debugger suite: 477 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed, with unrelated CRLF warnings from the broader dirty worktree.

Remaining priority from Pro:

- This moves BG-event generation beyond target-tile-only patches, but it still does not synthesize BG-event flag/item payloads, full object structs, arbitrary event-engine contexts, full script VM behavior, pixel/audio behavioral mirrors, emulator-backed reverse execution, or subsystem-complete causal proof. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Object-Event Ready-State Downgrade

Date: 2026-05-20.

Context:

- Object events are reached through `CheckFacingObject`, which uses `GetFacingTileCoord` and then requires `IsNPCAtCoord` to find a standing object struct at the facing coordinates.
- The content-state materializer previously treated object-event map-position patches as `ready` after installing only map/x/y state.
- That was a proof promotion bug: map position alone cannot prove or even fully prepare an object-event trigger, because the NPC/object struct and visibility state still matter.

Web references used:

- pret pokecrystal map event script reference for `object_event` records: `https://pret.github.io/pokecrystal/map_event_scripts.html`
- upstream pokegold `home/map.asm` / local `engine/overworld/npc_movement.asm` behavior for facing-tile and object checks: `https://git.poke.blue/pokegold/tree/home/map.asm?id=dd73b278b585266922424e09cd99faeeba02a2f4`

Implemented fix:

- `tools/debugger/content_scenarios.py`
  - preserves object-event `sprite` and `movement` fields in map-position precondition values for future object-struct materialization.
- `tools/debugger/content_state.py`
  - derives a planned adjacent player tile and `OW_UP` facing for object-event scenarios, including buffered `wPlayerMapX/Y` and `wPlayerDirection` patches when symbols exist.
  - keeps the proof explicit as `proof_status=state_patch_planned`.
  - adds `proof_blockers=["object_struct_not_materialized"]` and marks object-event materializations `blocked` instead of `ready` until object struct state is synthesized or observed.
  - carries known limits that map/player state is not enough for object-event execution proof.
- `tools/debugger/catalog.py`
  - updates the generation/fuzzing audit wording to preserve this blocker instead of implying object events are fully materialized.

Regression strengthened:

- `test_content_state_does_not_mark_object_event_ready_without_object_struct`
  - failed before the patch because object-event materialization was `ready`.
  - now verifies the materialization is blocked, carries the object-struct proof blocker, patches planned player-facing state, and exposes the right watch/expected sink symbols for later runtime proof.

Validation after patch:

- Focused object-event regression: passed.
- Focused content scenario/materialization cluster: 10 passed.
- Full debugger suite: 478 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed, with unrelated CRLF warnings from the broader dirty worktree.

Remaining priority from Pro:

- This prevents object-event proof promotion and preserves enough requested/static fields for the next generator step, but it does not synthesize object structs, object visibility, movement state, arbitrary event-engine contexts, full script VM behavior, pixel/audio behavioral mirrors, emulator-backed reverse execution, or subsystem-complete causal proof. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Object-Event Object Struct Materialization

Date: 2026-05-20.

Context:

- The previous object-event patch correctly stopped map-position-only evidence from becoming ready.
- The next runtime-generation blocker was concrete: `TryObjectEvent` calls `CheckFacingObject`, which requires `IsNPCAtCoord` to find a nonzero object struct whose `OBJECT_WALKING` is `STANDING`, then uses `OBJECT_MAP_OBJECT_INDEX` to load the corresponding `wMapObjects` row and script pointer.
- Source `object_event` coordinates are macro-expanded with a +4 map-buffer offset, so generated object structs and `wMap2Object` rows must use buffered coordinates while `wXCoord/wYCoord` stay player map coordinates.

Web references used:

- pret pokecrystal map event script reference for `object_event` fields: `https://pret.github.io/pokecrystal/map_event_scripts.html`
- upstream pokegold `home/map.asm` reference plus local `engine/overworld/player_object.asm`, `engine/overworld/npc_movement.asm`, and `constants/map_object_constants.asm` for object struct layout and facing-object behavior: `https://git.poke.blue/pokegold/tree/home/map.asm?id=dd73b278b585266922424e09cd99faeeba02a2f4`

Implemented fix:

- `tools/debugger/content_scenarios.py`
  - preserves object-event radius, time, palette, sight range, sprite, movement, object type, script, and event flag fields in precondition values.
- `tools/debugger/content_state.py`
  - resolves object-event constants from local constant files, with minimal test fallbacks for core object-event tokens.
  - patches a generated visible `wObject1Struct` object struct for the selected object event: sprite, map-object index, movement, standing state, direction, buffered current/last/init coordinates, radius, and range.
  - patches the matching first visible map-object row (`wMap2Object*`): struct id, sprite, buffered coordinates, movement, radius, time, type/palette, sight range, script pointer, and event flag.
  - marks the materialization `ready` only when object struct symbols, map-object symbols, script pointer, and constants all resolve.
  - keeps `proof_status=state_patch_planned`; replay/watch/trace still must prove `TryObjectEvent` consumes the patched state.
- `tools/debugger/catalog.py`
  - updates the generation/fuzzing audit wording from object-event blocker-only to bounded object-event object-struct generation, while retaining multi-object/counter-tile/large-object/arbitrary event-engine blockers.

Regression strengthened:

- `test_content_state_materializes_object_event_object_struct_state`
  - failed before the patch because object-event materialization had no `object_context` and stayed blocked even when all object struct and map-object symbols were available.
  - now verifies generated object struct patches, map-object row patches, script pointer word patches, event flag word patches, planned proof status, route expected sinks, and watch routing.
- `test_content_state_does_not_mark_object_event_ready_without_object_struct`
  - still verifies object-event materialization remains blocked when the object struct/map-object state cannot be generated.

Validation after patch:

- Focused object-event positive/negative regression pair: passed.
- Focused content scenario/materialization cluster: 11 passed.
- Full debugger suite: 479 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed, with unrelated CRLF warnings from the broader dirty worktree.

Remaining priority from Pro:

- This is bounded object-event state generation, not arbitrary event runtime generation. It still does not prove runtime execution without replay/watch/trace evidence, and it does not cover counter-tile interaction distance, large objects, multiple loaded objects, object visibility edge cases, full script VM behavior, pixel/audio behavioral mirrors, emulator-backed reverse execution, or subsystem-complete causal proof. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - BG-Event Flag State Materialization

Date: 2026-05-20.

Context:

- The BG-event facing patch handled player coordinates and direction, but `BGEVENT_ITEM`, `BGEVENT_COPY`, `BGEVENT_IFSET`, and `BGEVENT_IFNOTSET` also call `CheckBGEventFlag`.
- The engine reads an event flag id from the pointed `hiddenitem` or `conditional_event` payload, then checks the corresponding bit in `wEventFlags`.
- Without a generated event-flag bit patch, hidden items and conditional BG events could look positioned and facing-ready while the actual BG-event branch condition remained unsatisfied.

Web references used:

- pret pokecrystal map event script reference for BG event records and script payloads: `https://pret.github.io/pokecrystal/map_event_scripts.html`
- local/upstream pokegold event-engine references: `engine/overworld/events.asm`, `macros/scripts/maps.asm`, `home/flag.asm`, and upstream `home/map.asm` at `https://git.poke.blue/pokegold/tree/home/map.asm?id=dd73b278b585266922424e09cd99faeeba02a2f4`

Implemented fix:

- `tools/debugger/content_state.py`
  - resolves `hiddenitem ITEM, EVENT_*` and `conditional_event EVENT_*, script` payloads from the selected map source label.
  - resolves event flags and hidden-item constants from local constant files.
  - adds planned bit patches for `wEventFlags+N` with `patch_kind=bit`, `bit_operation=set/reset`, `bit_index`, `bit_mask`, and `preserves_other_bits=True`.
  - updates execution-time patching so bit patches preserve neighboring flags in the same byte when `content-state --execute` writes a save state.
  - carries `event_context` fields for flag token/value, byte offset, bit mask, required flag state, source payload macro, source line, and hidden-item token/value when present.
  - keeps `proof_status=state_patch_planned`; replay/watch/trace still must prove `CheckBGEventFlag` or the BG event branch executed.
- `tools/debugger/catalog.py`
  - updates the generation/fuzzing audit wording to include hidden-item/conditional BG-event flag bit generation while retaining arbitrary event-engine blockers.

Regression strengthened:

- `test_content_state_materializes_bg_event_hidden_item_flag_state`
  - failed before the patch because BG-event materialization only exposed player/facing context and did not patch `wEventFlags`.
  - now verifies hidden-item payload resolution, event flag value, byte offset, bit mask, reset operation, hidden item value, route expected sinks, and watch routing.
- `test_content_state_materializes_bg_event_conditional_flag_state`
  - verifies `BGEVENT_IFSET` requests a set-bit patch with the correct flag bit mask.

Validation after patch:

- Focused BG-event flag regression pair: passed.
- Focused content scenario/materialization cluster: 13 passed.
- Full debugger suite: 481 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed, with unrelated CRLF warnings from the broader dirty worktree.

Remaining priority from Pro:

- This closes another bounded event-engine state-generation slice, but it still does not provide runtime proof by itself. It does not cover counter-tile interaction distance, large-object BG/object geometry, full script VM behavior under arbitrary context, pixel/audio behavioral mirrors, emulator-backed reverse execution, or subsystem-complete causal proof. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Counter-Tile Object-Event State Materialization

Date: 2026-05-20.

Context:

- `CheckFacingObject` first calls `GetFacingTileCoord`; if that facing tile is a counter collision, `CheckCounterTile` reflects the facing coordinates across the player before `IsNPCAtCoord`.
- The object-event object-struct patch could generate adjacent object interactions, but counter interactions still needed a distinct two-tile-away player state plus the cached facing-tile collision byte.
- Treating the object struct alone as sufficient for counter interactions would be another planned-state overclaim, because the reflected path depends on `wTileDown`, `wTileUp`, `wTileLeft`, or `wTileRight`.

Web references used:

- pret pokecrystal map event script reference for `object_event` records: `https://pret.github.io/pokecrystal/map_event_scripts.html`
- upstream pokecrystal facing-object/counter-tile behavior: `https://github.com/pret/pokecrystal/blob/master/engine/overworld/npc_movement.asm`
- local/upstream pokegold references: `home/map.asm`, `home/map_objects.asm`, `engine/overworld/npc_movement.asm`, `constants/collision_constants.asm`

Implemented fix:

- `tools/debugger/content_scenarios.py`
  - adds four additional planned map-position preconditions for each `map_object_event`, one for each counter-tile facing direction.
  - preserves compatibility by adding fields (`counter_tile`, `counter_facing_direction`, `counter_tile_symbol`, `counter_tile_collision`) instead of changing existing object-event fields.
- `tools/debugger/content_state.py`
  - materializes counter-tile object-event candidates by positioning the player two tiles from the object and patching `wPlayerMapX/Y`, `wPlayerDirection`, the generated object struct/map-object row, and the selected cached facing-tile collision byte.
  - resolves `COLL_COUNTER` from `constants/collision_constants.asm` with the existing constant parser.
  - blocks counter-tile candidates, without invalidating the whole report, when the facing-tile symbol or collision constant cannot be resolved.
  - carries counter-tile event-context fields and keeps `proof_status=state_patch_planned`; replay/watch/trace must still prove `CheckCounterTile` and `TryObjectEvent` consumed the patched state.
- `tools/debugger/catalog.py`
  - updates the generation/fuzzing audit wording from counter-tile blocker to bounded four-direction counter-tile candidate generation, while retaining multi-object, large-object, arbitrary event-engine, script VM, graphics, audio, and mirror blockers.

Regression strengthened:

- `test_content_state_materializes_counter_tile_object_event_state`
  - failed before the patch because no counter-tile object-event materialization existed.
  - now verifies the added counter-tile preconditions, two-tile player placement, `wTileUp=COLL_COUNTER` patch, reflected target object struct coordinates, event-context fields, route expected sinks, and watch routing.

Validation after patch:

- Focused counter-tile object-event regression: passed.
- Focused map/content materialization cluster: 8 passed.
- Focused generic content-state materialization cluster: 3 passed.
- Full debugger suite: 482 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed for touched debugger Python files before this documentation update.

Remaining priority from Pro:

- This closes the bounded counter-tile state-generation slice, but it is still planned state evidence until replay/watch/trace observes the event engine consuming it. It does not implement multi-object or large-object event-state generation, arbitrary event-engine states, full script VM behavior under arbitrary context, pixel-accurate graphics/UI mirrors, full audio playback/mixer mirrors, emulator-backed reverse execution, or subsystem-complete causal proof. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Large-Object Object-Event State Materialization

Date: 2026-05-20.

Context:

- `IsNPCAtCoord` does not treat every object as 1x1. If `OBJECT_PALETTE` has the `BIG_OBJECT` bit, it calls `WillObjectIntersectBigObject`, which accepts any facing tile inside the object's 2x2 footprint.
- `SPRITEMOVEDATA_BIGDOLLSYM`, `SPRITEMOVEDATA_BIGDOLLASYM`, and `SPRITEMOVEDATA_BIGDOLL` set that bit through `data/sprites/map_objects.asm`.
- The previous object-event state patch could synthesize an object struct, but for big dolls it left `OBJECT_PALETTE=0` and used the ordinary one-tile-below player position, which can place the player inside the 2x2 footprint instead of outside it.

Web references used:

- upstream pokecrystal facing-object/big-object behavior: `https://github.com/pret/pokecrystal/blob/master/engine/overworld/npc_movement.asm`
- local/upstream pokegold references: `engine/overworld/npc_movement.asm`, `home/map_objects.asm`, `data/sprites/map_objects.asm`, `constants/map_object_constants.asm`

Implemented fix:

- `tools/debugger/content_scenarios.py`
  - marks known big-doll movement tokens as `large_object` and adds eight planned large-object map-position candidates around the 2x2 footprint.
  - preserves the original object-event precondition shape while adding `large_object_*` fields for the generated candidates.
- `tools/debugger/content_state.py`
  - parses sprite movement attributes from `data/sprites/map_objects.asm`.
  - patches object-struct `OBJECT_FLAGS1`, `OBJECT_FLAGS2`, and `OBJECT_PALETTE` from the sprite movement data instead of forcing them to zero.
  - detects large-object movement data and places the default object-event player outside the 2x2 footprint.
  - carries `large_object`, width/height, and sprite-movement flag evidence in the event/object context while keeping `proof_status=state_patch_planned`.
- `tools/debugger/catalog.py`
  - updates the generation/fuzzing audit wording from generic large-object blocker to bounded 2x2 large-object footprint candidate generation, while retaining multi-object, custom large-object, arbitrary event-engine, script VM, graphics, audio, and mirror blockers.

Regression strengthened:

- `test_content_state_materializes_large_object_event_state`
  - failed before the patch because only normal/counter preconditions existed and the object struct did not carry the big-object palette bit.
  - now verifies large-object candidate generation, outside-footprint player placement, movement-data-derived flags, `OBJECT_PALETTE=BIG_OBJECT|STRENGTH_BOULDER`, large-object event context, and expected-sink routing.

Validation after patch:

- Focused large-object object-event regression: passed.
- Focused map/content materialization cluster: 9 passed.
- Full debugger suite: 483 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed for touched debugger Python files before this documentation update.

Remaining priority from Pro:

- This closes the bounded known-2x2-large-object state-generation slice, but it remains planned state evidence until replay/watch/trace observes `IsNPCAtCoord` consuming the big-object intersection path. It does not implement multi-object map-object rows, custom non-2x2 large-object geometry, arbitrary event-engine states, full script VM behavior under arbitrary context, pixel-accurate graphics/UI mirrors, full audio playback/mixer mirrors, emulator-backed reverse execution, or subsystem-complete causal proof. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Selected Map-Object Row Materialization

Date: 2026-05-20.

Context:

- `ReadObjectEvents` copies source `object_event` records into `wMap2Object` onward. `wMapObjects` index 0 is the player object and visible object initialization starts at map object index 2.
- `TryObjectEvent` uses `OBJECT_MAP_OBJECT_INDEX` from the found object struct, then calls `GetMapObject`. A second source object therefore needs `OBJECT_MAP_OBJECT_INDEX=3` and a `wMap3Object*` row, not the hardcoded `wMap2Object*` row.
- The previous materializer was correct for the first source object only. On maps with several object events, it could prepare the selected script label but attach it to the wrong map-object row.

Web references used:

- pret/pokecrystal map-object macro reference for source `object_event` layout: `https://raw.githubusercontent.com/pret/pokecrystal/master/macros/scripts/maps.asm`
- local/upstream pokegold references: `home/map.asm`, `home/map_objects.asm`, `engine/overworld/player_object.asm`, `ram/wram.asm`, `constants/map_object_constants.asm`

Implemented fix:

- `tools/debugger/content_scenarios.py`
  - tracks the source object ordinal after `def_object_events`.
  - adds `source_object_ordinal` and `map_object_index` to `map_object_event` triggers and map-position precondition values.
- `tools/debugger/content_state.py`
  - derives the target map-object row from `map_object_index`/`source_object_ordinal`.
  - patches the selected `wMapNObject*` row rather than always patching `wMap2Object*`.
  - writes the selected map-object index into `wObject1Struct+OBJECT_MAP_OBJECT_INDEX`.
  - routes watch symbols, expected sinks, commands, and event context through the selected `wMapNObject` prefix.
- `tools/debugger/catalog.py`
  - updates the generation/fuzzing audit wording from generic multi-object row blocker to selected map-object row generation while retaining full multi-loaded-object occupancy, custom large-object, arbitrary event-engine, script VM, graphics, audio, and mirror blockers.

Regression strengthened:

- `test_content_state_materializes_multi_object_event_row`
  - failed before the patch because no source object ordinal was preserved and the second object still materialized through `wMap2Object`.
  - now verifies the second source object gets `map_object_index=3`, `wObject1Struct+OBJECT_MAP_OBJECT_INDEX=3`, the `wMap3Object*` row patches, selected-row watch symbols, expected sinks, and replay/watch command routing.

Validation after patch:

- Focused multi-object row regression: passed.
- Focused map/content materialization cluster: 10 passed.
- Full debugger suite: 484 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed for touched debugger Python files before this documentation update.

Remaining priority from Pro:

- This closes selected map-object row generation for one targeted visible object, but it remains planned state evidence until replay/watch/trace observes `TryObjectEvent` consuming it. It does not synthesize every visible object struct on the map, object occupancy/collision interactions among multiple loaded objects, custom non-2x2 large-object geometry, arbitrary event-engine states, full script VM behavior under arbitrary context, pixel-accurate graphics/UI mirrors, full audio playback/mixer mirrors, emulator-backed reverse execution, or subsystem-complete causal proof. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Source-Order Companion Object Occupancy Materialization

Date: 2026-05-20.

Context:

- `InitializeVisibleSprites` scans source map-object rows from `wMap2Object` upward and `CopyObjectStruct` fills object structs from `wObject1Struct` upward.
- The selected-row patch wrote the right `wMapNObject` row, but still let a second source object occupy `wObject1Struct`, which is not the source-order loaded-object shape.
- That was useful for a narrow selected target, but it did not model companion occupancy well enough to investigate object-object collision or wrong-NPC interaction cases.

Web references used:

- upstream pokecrystal player-object/object-loader reference: `https://raw.githubusercontent.com/pret/pokecrystal/master/engine/overworld/player_object.asm`
- pret/pokecrystal map-object macro reference: `https://raw.githubusercontent.com/pret/pokecrystal/master/macros/scripts/maps.asm`
- local/upstream pokegold references: `engine/overworld/player_object.asm`, `home/map.asm`, `home/map_objects.asm`, `ram/wram.asm`, `constants/map_object_constants.asm`

Implemented fix:

- `tools/debugger/content_state.py`
  - parses sibling `object_event` records from the selected map source file.
  - patches source-order companion map-object rows and object structs for the selected event state.
  - assigns the selected source object to the corresponding source-order object struct (`source ordinal + 1`) instead of always using `wObject1Struct`.
  - carries companion occupancy context (`companion_object_count`, `loaded_object_count`, `occupancy_model=source_order_all_visible_candidate`) while keeping `proof_status=state_patch_planned`.
- `tools/debugger/catalog.py`
  - updates the generation/fuzzing audit wording to include source-order companion occupancy candidates while retaining runtime-verified occupancy, custom large-object, arbitrary event-engine, script VM, graphics, audio, and mirror blockers.

Regression strengthened:

- `test_content_state_materializes_companion_object_structs`
  - failed before the patch because the second source object still used `wObject1Struct` and no companion object struct was patched.
  - now verifies the first source object occupies `wObject1Struct`/`wMap2Object`, the selected second source object occupies `wObject2Struct`/`wMap3Object`, both object structs are watched, and both object-struct coordinate sinks are routed.
- `test_content_state_materializes_multi_object_event_row`
  - updated to match the source-order struct assignment while preserving selected `wMap3Object` row coverage.

Validation after patch:

- Focused companion + selected-row regressions: 2 passed.
- Focused map/content materialization cluster: 11 passed.
- Full debugger suite: 485 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed for touched debugger Python files before this documentation update.

Remaining priority from Pro:

- This closes a bounded source-order all-visible companion occupancy candidate, but it remains planned state evidence until replay/watch/trace observes the object loader and `TryObjectEvent` consuming the same loaded set. It does not prove actual runtime visibility, offscreen pruning, object masks/event flags/time-of-day filtering, custom non-2x2 large-object geometry, arbitrary event-engine states, full script VM behavior under arbitrary context, pixel-accurate graphics/UI mirrors, full audio playback/mixer mirrors, emulator-backed reverse execution, or subsystem-complete causal proof. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Viewport-Filtered Companion Object Occupancy

Date: 2026-05-20.

Context:

- `ReadObjectEvents` copies source `object_event` rows into `wMap2Object` onward with `MAPOBJECT_OBJECT_STRUCT_ID=-1`.
- `InitializeVisibleSprites` then scans those rows in source order and only calls `CopyObjectStruct` when the object's buffered map coordinates are inside the player-relative `MAPOBJECT_SCREEN_WIDTH`/`MAPOBJECT_SCREEN_HEIGHT` window.
- The previous source-order companion patch treated every sibling object as visible. That could promote an offscreen source row into a live object struct and shift the selected object into the wrong `wObjectNStruct`, which is a proof-boundary overclaim.

Web references used:

- upstream pokecrystal player-object/object-loader reference: `https://raw.githubusercontent.com/pret/pokecrystal/master/engine/overworld/player_object.asm`
- pret/pokecrystal map-object macro reference: `https://raw.githubusercontent.com/pret/pokecrystal/master/macros/scripts/maps.asm`
- local pokegold references: `engine/overworld/player_object.asm`, `home/map.asm`, `constants/map_object_constants.asm`, `ram/wram.asm`

Implemented fix:

- `tools/debugger/content_state.py`
  - separates copied map-object rows from runtime-loaded visible object structs.
  - computes companion visibility with the same player-relative viewport predicate used by `InitializeVisibleSprites`: `object_x + 1 - wXCoord` and `object_y + 1 - wYCoord` must be within `MAPOBJECT_SCREEN_WIDTH`/`MAPOBJECT_SCREEN_HEIGHT`.
  - patches offscreen companion rows with `StructID=$ff` but does not synthesize an object struct or watch a nonexistent `wObjectNStruct` for them.
  - assigns selected object-struct indexes by visible source-order rank, so a selected second source object can correctly occupy `wObject1Struct` when the first source object is offscreen.
  - adds compatibility fields rather than reshaping the report: `offscreen_object_count`, `offscreen_objects`, `map_row_object_count`, `selected_visibility`, `visibility_model=InitializeVisibleSprites_player_viewport`, and `occupancy_model=source_order_viewport_visible_candidate`.
- `tools/debugger/catalog.py`
  - updates generation/fuzzing audit wording from source-order all-visible companion candidates to viewport-filtered companion map-row/object-struct candidates.
  - keeps object masks, event flags, time filters, custom large objects, arbitrary event-engine states, script VM, graphics, audio, and runtime-verified occupancy as blockers.

Regression strengthened:

- `test_content_state_skips_offscreen_companion_object_structs`
  - failed before the patch because an offscreen first source object consumed `wObject1Struct` and forced the selected second source object into `wObject2Struct`.
  - now verifies the offscreen row remains materialized as `wMap2Object*` with `StructID=$ff`, the selected row gets `wMap3ObjectStructID=1`, the selected object uses `wObject1Struct`, and `wObject2Struct` is not watched.

Validation after patch:

- Focused offscreen companion regression: passed.
- Focused object-event materialization cluster: 6 passed.
- Focused map/content materialization cluster: 11 passed.
- Full debugger suite: 486 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed for touched debugger Python files and this review doc.

Remaining priority from Pro:

- This closes the bounded offscreen-pruning proof boundary for source-order object struct materialization, but it remains planned state evidence until replay/watch/trace observes the object loader and `TryObjectEvent` consuming the same loaded set. It still does not prove object mask/event-flag/time-of-day filtering, custom non-2x2 large-object geometry, arbitrary event-engine states, full script VM behavior under arbitrary context, pixel-accurate graphics/UI mirrors, full audio playback/mixer mirrors, emulator-backed reverse execution, or subsystem-complete causal proof. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Object-Event Mask/Event-Flag State Materialization

Date: 2026-05-20.

Context:

- `LoadObjectMasks` clears `wObjectMasks`, then uses `GetObjectTimeMask` and `CheckObjectFlag` to decide whether each map object is masked.
- `CheckObjectFlag` treats a source object with no sprite as masked, `EVENT_FLAG=-1` as unmasked, and a real event flag as hidden when that flag bit is set.
- `CopyObjectStruct` calls `CheckObjectMask` before allocating a live object struct. The previous materializer could patch a visible object struct while leaving the object-mask/event-flag precondition unmodeled.

Web references used:

- upstream pokecrystal object-mask loader reference: `https://raw.githubusercontent.com/pret/pokecrystal/master/engine/overworld/map_objects_2.asm`
- upstream pokecrystal player-object/object-loader reference: `https://raw.githubusercontent.com/pret/pokecrystal/master/engine/overworld/player_object.asm`
- local pokegold references: `engine/overworld/map_objects_2.asm`, `engine/overworld/player_object.asm`, `home/map.asm`, `home/flag.asm`, `engine/overworld/scripting.asm`, `constants/map_object_constants.asm`

Implemented fix:

- `tools/debugger/content_state.py`
  - adds planned object-mask state for object events: `wObjectMasks+N=0` when `wObjectMasks` resolves.
  - adds bit-preserving event-flag reset patches for object events with a real `MAPOBJECT_EVENT_FLAG` when `wEventFlags` resolves.
  - threads the same mask/event-flag preconditions through selected objects, visible companion objects, and offscreen companion map rows.
  - records `object_mask_context` with validation kind, map-object index, required unmasked state, event flag id, bit offset/mask, symbol availability, and `proof_status=state_patch_planned`.
  - keeps compatibility by adding fields and patches, not reshaping existing JSON.
- `tools/debugger/catalog.py`
  - updates generation/fuzzing audit wording to include object-event event-flag reset and `wObjectMasks` unmask preconditions while keeping time filtering, runtime occupancy, custom large-object generation, arbitrary event-engine states, script VM, graphics, and audio blockers.

Regression strengthened:

- `test_content_state_materializes_object_event_flag_mask_state`
  - failed before the patch because object-event materialization had no object-mask/event-flag state context.
  - now verifies `wObjectMasks+2=0`, bit-preserving `wEventFlags+0` reset for `EVENT_UNIT_HIDE_NPC`, selected `wMap2ObjectEventFlag` bytes, watch symbols, and runtime-route expected sinks.

Validation after patch:

- Focused object-event flag/mask regression: passed.
- Focused object-event materialization cluster: 7 passed.
- Focused map/content materialization cluster: 12 passed.
- Full debugger suite: 487 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed for touched debugger Python files and this review doc.

Remaining priority from Pro:

- This closes a bounded object-event mask/event-flag state-generation slice, but it remains planned state evidence until replay/watch/trace observes `LoadObjectMasks`, `CheckObjectFlag`, `CheckObjectMask`, and `TryObjectEvent` consuming the same state. It still does not prove time-of-day/hour filtering, runtime object occupancy, custom non-2x2 large-object geometry, arbitrary event-engine states, full script VM behavior under arbitrary context, pixel-accurate graphics/UI mirrors, full audio playback/mixer mirrors, emulator-backed reverse execution, or subsystem-complete causal proof. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Selected Object-Event Hour State Materialization

Date: 2026-05-20.

Context:

- `LoadObjectMasks` calls `GetObjectTimeMask`, which calls `CheckObjectTime`, before `CopyObjectStruct` can allocate a live object.
- For object events with `MAPOBJECT_HOUR_1 != -1`, `CheckObjectTime` compares the current `hHours` value against the object's hour range.
- The previous materializer could patch the selected object struct and row but leave the clock precondition unmodeled, which made hour-gated object events look ready from object state alone.

Web references used:

- upstream pokecrystal object-mask/time loader reference: `https://raw.githubusercontent.com/pret/pokecrystal/master/engine/overworld/map_objects_2.asm`
- local pokegold references: `home/map_objects.asm`, `engine/overworld/map_objects_2.asm`, `engine/overworld/player_object.asm`, `constants/map_object_constants.asm`

Implemented fix:

- `tools/debugger/content_state.py`
  - adds `object_time_context` for selected object-event materializations.
  - for selected hour-range objects, patches `hHours` to the range start when `hHours` resolves.
  - preserves `proof_status=state_patch_planned`; this is a generated state precondition, not proof that `CheckObjectTime` or `LoadObjectMasks` executed.
- `tools/debugger/catalog.py`
  - updates generation/fuzzing audit wording to include selected object-event hour-filter `hHours` preconditions.
  - keeps runtime-verified multi-object occupancy, time-of-day masks, companion time filtering, custom large-object generation, arbitrary event-engine states, script VM, graphics, and audio blockers.

Regression strengthened:

- `test_content_state_materializes_selected_object_event_hour_state`
  - failed before the patch because selected hour-gated object events had no time-state context or `hHours` patch.
  - now verifies `object_time_context`, `hHours=9`, selected `wMap2ObjectHour1/Hour2`, object mask state, watch symbols, and runtime-route sinks.

Validation after patch:

- Focused selected object-event hour regression: passed.
- Focused map/content materialization cluster: 13 passed.
- Full debugger suite: 488 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed for touched debugger Python files and this review doc.

Remaining priority from Pro:

- This closes a selected-object hour-filter state-generation slice, but it remains planned state evidence until replay/watch/trace observes `GetObjectTimeMask`, `CheckObjectTime`, `LoadObjectMasks`, and `TryObjectEvent` consuming the same state. It still does not prove time-of-day mask selection, companion time-filter compatibility, runtime object occupancy, custom non-2x2 large-object geometry, arbitrary event-engine states, full script VM behavior under arbitrary context, pixel-accurate graphics/UI mirrors, full audio playback/mixer mirrors, emulator-backed reverse execution, or subsystem-complete causal proof. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Companion Hour-Filter Object Occupancy

Date: 2026-05-20.

Context:

- `InitializeVisibleSprites` allocates object structs only after `LoadObjectMasks` has built `wObjectMasks`.
- `LoadObjectMasks` calls `CheckObjectTime` for every copied `wMapNObject` row, not just the selected target.
- The previous selected-hour patch set `hHours` for the target object but still let a visible companion with an incompatible hour range consume an object struct, which shifted the selected target into the wrong `wObjectNStruct`.

Web references used:

- upstream pokecrystal object-mask/time loader reference: `https://raw.githubusercontent.com/pret/pokecrystal/master/engine/overworld/map_objects_2.asm`
- upstream pokecrystal player-object/object-loader reference: `https://raw.githubusercontent.com/pret/pokecrystal/master/engine/overworld/player_object.asm`
- local pokegold references: `home/map_objects.asm`, `engine/overworld/map_objects_2.asm`, `engine/overworld/player_object.asm`, `constants/map_object_constants.asm`

Implemented fix:

- `tools/debugger/content_state.py`
  - applies the selected hour context to source-order companion allocation.
  - leaves hour-incompatible companions as copied map rows with `StructID=$ff` and `wObjectMasks+N=$ff` instead of synthesizing a live object struct.
  - records `time_filtered_object_count`, `time_filtered_objects`, the companion `object_time_context`, and the selected time context.
  - preserves `proof_status=state_patch_planned`; replay/watch/trace must still prove the loader consumed this state.
- `tools/debugger/catalog.py`
  - updates audit wording to include selected-hour companion hour filtering.
  - keeps time-of-day masks, runtime-verified occupancy, custom large-object generation, arbitrary event-engine states, script VM, graphics, and audio blockers.

Regression strengthened:

- `test_content_state_skips_time_filtered_companion_object_structs`
  - failed before the patch because a night-only visible companion consumed `wObject1Struct` even when the selected generated state set `hHours=9` for a day-only target.
  - now verifies the night-only row remains `wMap2Object*` with `StructID=$ff`, `wObjectMasks+2=$ff`, the selected day object gets `wMap3ObjectStructID=1`, and `wObject2Struct` is not watched.

Validation after patch:

- Focused companion time-filter regression: passed.
- Focused object-event materialization cluster: 9 passed.
- Focused map/content materialization cluster: 14 passed.
- Full debugger suite: 489 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `py_compile` passed for touched debugger Python files.
- `git diff --check` passed for touched debugger Python files and this review doc.

Remaining priority from Pro:

- This closes selected-hour-compatible companion pruning, but it remains planned state evidence until replay/watch/trace observes `LoadObjectMasks`, `CheckObjectTime`, `InitializeVisibleSprites`, and `TryObjectEvent` consuming the same state. It still does not prove time-of-day mask selection, arbitrary time contexts across all companions, runtime object occupancy, custom non-2x2 large-object geometry, arbitrary event-engine states, full script VM behavior under arbitrary context, pixel-accurate graphics/UI mirrors, full audio playback/mixer mirrors, emulator-backed reverse execution, or subsystem-complete causal proof. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Time-of-Day Object-Event Mask Materialization

Date: 2026-05-20.

Context:

- `CheckObjectTime` treats `MAPOBJECT_HOUR_1 == -1` as the time-of-day mask path: it reads `MAPOBJECT_TIMEOFDAY`, indexes the local `.TimesOfDay` table by `wTimeOfDay`, and requires the selected `MORN`/`DAY`/`NITE` bit to overlap the object mask.
- The previous materializer could resolve numeric hour ranges but treated `-1, DAY` or `-1, NITE` object events as unmaterialized, so time-of-day-gated map objects stayed blocked or could be miscounted during source-order companion occupancy.
- The parser also did not model the local `shift_const` macro, so `MORN`, `DAY`, `NITE`, and their `_F` index constants were unavailable to content-state generation.

References used:

- RGBDS language docs for `DEF`, `EQU`, variables, macros, and shift expressions: `https://rgbds.gbdev.io/docs/v0.8.0/rgbasm.5`
- Pan Docs memory map for WRAM/HRAM address-space background: `https://gbdev.io/pandocs/Memory_Map.html`
- upstream pret object-time reference consulted: `https://raw.githubusercontent.com/pret/pokecrystal/master/home/map_objects.asm`
- local pokegold source truth: `macros/const.asm`, `home/map_objects.asm`, `constants/ram_constants.asm`, `constants/misc_constants.asm`, `engine/rtc/rtc.asm`

Implemented fix:

- `tools/debugger/content_state.py`
  - loads `constants/misc_constants.asm` for `MORN_HOUR`, `DAY_HOUR`, and `NITE_HOUR`.
  - extends `parse_constant_source` to model `const_def`, `const`, `shift_const`, `const_skip`, and `const_next` closely enough for the object-event constant files.
  - adds `object_time_context` support for time-of-day masks with `timeofday_mask`, `required_timeofday`, `required_timeofday_value`, and coherent `required_hour`.
  - patches `wTimeOfDay` and `hHours` when the symbols resolve, preserving `proof_status=state_patch_planned`.
  - applies selected time-of-day state to companion filtering so incompatible visible companions become masked map rows instead of generated object structs.
- `tools/debugger/catalog.py`
  - updates the generation/fuzzing gap text to credit selected time-of-day mask preconditions and companion filtering.
  - keeps `ready=False` blockers for runtime-verified occupancy, arbitrary time contexts beyond selected source masks, script VM, graphics, audio, reverse execution, and causal proof.

Regression strengthened:

- `test_content_state_materializes_selected_object_event_timeofday_mask_state`
  - failed before the patch because `DAY` was unresolved and no `wTimeOfDay`/coherent `hHours` patch existed.
  - now verifies `timeofday_mask=2`, `required_timeofday=DAY`, `required_timeofday_value=1`, `required_hour=10`, selected row hour fields, watch symbols, and runtime-route sinks.
- `test_content_state_skips_timeofday_mask_filtered_companion_object_structs`
  - failed before the patch because `NITE`/`DAY` masks could not drive companion visibility.
  - now verifies a NITE companion is copied as a masked row with `StructID=$ff`, while the selected DAY object keeps `wObject1Struct`.

Validation after patch:

- Focused time-of-day regressions: 2 passed.
- Focused object-event materialization cluster: 7 passed.
- Full debugger unittest discovery: 491 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile tools/debugger/content_state.py tools/debugger/catalog.py tools/debugger/tests/test_catalog.py`: passed.
- `git diff --check`: passed; it only reported existing CRLF normalization warnings in unrelated dirty files.

Remaining priority from Pro:

- This closes bounded selected-source time-of-day mask state generation and selected-time companion pruning, but it remains planned state evidence until replay/watch/trace observes `LoadObjectMasks`, `CheckObjectTime`, `InitializeVisibleSprites`, and `TryObjectEvent` consuming the same state. It still does not prove runtime object occupancy, arbitrary time contexts beyond selected source masks, custom non-2x2 large-object geometry, arbitrary event-engine states, full script VM behavior under arbitrary context, pixel-accurate graphics/UI mirrors, full audio playback/mixer mirrors, emulator-backed reverse execution, or subsystem-complete causal proof. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Custom BIG_OBJECT Movement Candidate Generation

Date: 2026-05-20.

Context:

- `WillObjectIntersectBigObject` in local source uses a fixed `cp 2` width and `cp 2` height check. There is no current engine support for arbitrary non-2x2 object geometry.
- The real remaining generation gap was narrower: `content_scenarios.py` only recognized three hardcoded big-doll movement tokens when deciding whether to emit all eight large-object surface candidates.
- A custom romhack movement row with `BIG_OBJECT` in `data/sprites/map_objects.asm` would be materialized as a big object by `content_state.py`, but it would not receive the full source-scenario candidate set.

References used:

- RGBDS macro/expression docs: `https://rgbds.gbdev.io/docs/v1.0.1/rgbasm.5`
- upstream pret sprite movement data reference: `https://raw.githubusercontent.com/pret/pokecrystal/master/data/sprites/map_objects.asm`
- local pokegold source truth: `data/sprites/map_objects.asm`, `constants/map_object_constants.asm`, `engine/overworld/npc_movement.asm`

Implemented fix:

- `tools/debugger/content_scenarios.py`
  - passes the active repo root through source scenario generation so object-event preconditions can inspect the current movement-data table.
  - discovers custom large-object movement tokens by reading `data/sprites/map_objects.asm` comment labels and `BIG_OBJECT` palette-flag rows.
  - keeps the historical known big-doll fallback tokens for compatibility.
  - adds `large_object_collision_model=WillObjectIntersectBigObject_fixed_2x2` and `large_object_size_source=engine/overworld/npc_movement.asm:WillObjectIntersectBigObject` to generated values.
- `tools/debugger/content_state.py`
  - carries the fixed 2x2 collision model and source through player/object event contexts.
  - keeps known limits focused on runtime proof of `WillObjectIntersectBigObject`, not nonexistent arbitrary-size geometry.
- `tools/debugger/catalog.py`
  - updates the generation/fuzzing audit wording to credit custom `BIG_OBJECT` movement candidate generation.
  - keeps runtime-observed big-object collision/occupancy as an open blocker.

Regression strengthened:

- `test_content_scenarios_materialize_custom_big_object_movement_candidates`
  - failed before the patch because `SPRITEMOVEDATA_CUSTOM_STATUE` was not in the hardcoded token set, so no large-object surface preconditions were emitted.
  - now verifies 13 map-position preconditions, the `right_bottom` surface candidate, fixed collision-model metadata, `OBJECT_PALETTE=BIG_OBJECT`, and ready planned-state materialization.

Validation after patch:

- Focused custom/large-object/counter-tile regressions: 3 passed.
- Focused time-of-day regressions from the prior patch: 2 passed.
- Full debugger unittest discovery: 492 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile tools/debugger/content_scenarios.py tools/debugger/content_state.py tools/debugger/catalog.py tools/debugger/tests/test_catalog.py`: passed.
- `git diff --check`: passed; it only reported existing CRLF normalization warnings in unrelated dirty files.

Remaining priority from Pro:

- This closes source-discovered custom `BIG_OBJECT` candidate generation for the engine's fixed 2x2 collision path, but it remains planned state evidence until replay/watch/trace observes `IsNPCAtCoord` and `WillObjectIntersectBigObject` consuming the same object struct and player/facing state. It still does not prove runtime object occupancy, arbitrary time contexts beyond selected source masks, arbitrary event-engine states, full script VM behavior under arbitrary context, pixel-accurate graphics/UI mirrors, full audio playback/mixer mirrors, emulator-backed reverse execution, or subsystem-complete causal proof. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - Source Time-of-Day Candidate Generation

Date: 2026-05-20.

Context:

- `CheckObjectTime` accepts a time-of-day object when `wTimeOfDay` indexes `.TimesOfDay` to a bit that overlaps `MAPOBJECT_TIMEOFDAY`.
- The previous time-of-day materializer chose one valid time for the selected object, which made `ANYTIME` or multi-bit masks materially under-covered: MORN/DAY/NITE were source-legal, but only the first choice became a generated state.
- Planned state still must not be mistaken for runtime proof. These candidates only prepare source-declared contexts; replay/watch/trace must still observe `CheckObjectTime` and the object loader consuming them.

References used:

- upstream pret `CheckObjectTime` reference: `https://raw.githubusercontent.com/pret/pokecrystal/master/home/map_objects.asm`
- upstream pret RTC time-of-day reference: `https://raw.githubusercontent.com/pret/pokecrystal/master/engine/rtc/rtc.asm`
- local pokegold source truth: `home/map_objects.asm`, `engine/rtc/rtc.asm`, `constants/ram_constants.asm`, `constants/misc_constants.asm`

Implemented fix:

- `tools/debugger/content_scenarios.py`
  - emits `map_object_event_timeofday_morn/day/nite_position` preconditions for source masks that explicitly include `MORN`, `DAY`, `NITE`, or `ANYTIME`.
  - adds `selected_timeofday`, `selected_hour`, and `selected_time_context_source=source_timeofday_mask_candidate` to those precondition values.
  - adds `wTimeOfDay` and `hHours` to the generated watch symbols for those candidates.
- `tools/debugger/content_state.py`
  - honors requested `selected_timeofday` and `selected_hour` values when materializing object-event time context.
  - patches coherent `wTimeOfDay`/`hHours` values for the requested source time.
  - rejects requested time contexts that are not allowed by the object mask/range instead of silently falling back to the first valid time.
- `tools/debugger/catalog.py`
  - updates the generation/fuzzing gap text to credit source-declared MORN/DAY/NITE candidate preconditions.
  - keeps arbitrary hour/runtime time contexts and runtime-verified occupancy as blockers.

Regression strengthened:

- `test_content_scenarios_materialize_all_timeofday_mask_candidates`
  - failed before the patch because an `ANYTIME` object had no separate MORN/DAY/NITE precondition ids.
  - now verifies the three candidate ids exist, the NITE candidate materializes `required_timeofday=NITE`, `required_timeofday_value=2`, `required_hour=18`, `wTimeOfDay=2`, `hHours=18`, and both time watches.

Validation after patch:

- Focused time-context/custom-object regressions: 4 passed.
- Full debugger unittest discovery: 493 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile tools/debugger/content_scenarios.py tools/debugger/content_state.py tools/debugger/catalog.py tools/debugger/tests/test_catalog.py`: passed.
- `git diff --check`: passed; it only reported existing CRLF normalization warnings in unrelated dirty files.

Remaining priority from Pro:

- This closes generated state coverage for source-declared MORN/DAY/NITE mask candidates, but it remains planned state evidence until replay/watch/trace observes `GetObjectTimeMask`, `CheckObjectTime`, `LoadObjectMasks`, `InitializeVisibleSprites`, and `TryObjectEvent` consuming the same state. It still does not prove runtime object occupancy, arbitrary hour/runtime time contexts beyond generated source candidates, arbitrary event-engine states, full script VM behavior under arbitrary context, pixel-accurate graphics/UI mirrors, full audio playback/mixer mirrors, emulator-backed reverse execution, or subsystem-complete causal proof. The whole-ROM proof-substrate goal remains incomplete.

## Implementation Note - PyBoy Hook-Order Matrix and Hardware Proof Gates

Date: 2026-05-20.

Context:

- The `whole_rom_replay_localization` blocker was aimed at the wrong abstraction level: PyBoy hooks are debugger-style opcode-replacement breakpoints, not a clean non-mutating before/after instruction event stream.
- The new hook-order probe must therefore be treated as ground-truth about the current PyBoy hook mechanism only. It can say what the callback observes around specific opcodes and side effects, but it cannot prove hardware-accurate CPU/PPU/APU timing.
- Last-writer, dynamic-taint, visual, and audio reports must not promote emulator-observed facts into hardware proof when the evidence path crosses DMA, timer overflow, LCD mode edges, interrupt entry, framebuffer digests, or sound-buffer digests.

References used:

- Supervisor Deep Research report: `C:\Users\lolno\Downloads\codex-supervisor\consults\2026-05-19T2327-response.md`
- PyBoy API docs for `hook_register`: `https://docs.pyboy.dk/`
- Pan Docs OAM DMA timing and bus conflict model: `https://gbdev.io/pandocs/OAM_DMA_Transfer.html`
- Pan Docs CGB VRAM DMA length/mode/timing model: `https://gbdev.io/pandocs/CGB_Registers.html#ff51ff55--hdma1hdma5-vram-dma`
- Pan Docs TIMA overflow A/B-cycle behavior: `https://gbdev.io/pandocs/Timer_Obscure_Behaviour.html`
- Pan Docs interrupt-entry stack/PC behavior: `https://gbdev.io/pandocs/Interrupts.html`
- Pan Docs rendering/dot-mode timing model: `https://gbdev.io/pandocs/Rendering.html`

Implemented fix:

- `tools/debugger/hook_order.py`
  - upgrades `python -m tools.debugger hook-order-probe --execute` from a narrow RMW check into a seven-scenario micro-ROM matrix: `INC [HL]`, `PUSH rr`, taken `CALL`, taken `RST`, interrupt entry, FF46 OAM DMA write, and CGB FF55 VRAM DMA write.
  - emits machine-readable rows with `observes_pre_fetch`, `observes_pre_write`, `observes_post_write`, `observes_post_interrupt`, and `observes_post_dma`.
  - labels the mechanism as `pyboy_opcode_replacement_breakpoint`, with `non_mutating_instruction_events=false` and `pre_fetch_runtime_observed=false`.
- `tools/debugger/effect_trace.py`
  - fences modeled DMA, TIMA overflow, interrupt-entry, and LCD-mode-edge side effects behind explicit runtime hardware-event evidence.
  - downgrades matching side-effect items to `planned_only` with `hardware_proof_gate=explicit_runtime_event_missing` when the chain has only modeled/emulator-adjacent evidence.
- `tools/debugger/reverse_query.py`
  - prevents reverse-query last-writer results from promoting to strong proof when a required hardware event is missing.
  - carries the downgrade reason into report evidence atoms and normalized history.
- `tools/debugger/dynamic_taint.py`
  - preserves effect-level proof downgrades through sink matching so taint attribution cannot silently promote gated hardware writes.
- `tools/debugger/visual_snapshot.py`, `tools/debugger/audio_snapshot.py`, `tools/debugger/ranking.py`, and `tools/debugger/__main__.py`
  - label PyBoy framebuffer and sound-buffer digests as emulator-observed evidence with `hardware_behavior_proven=false`.
  - keep UI/report wording visibly distinct from hardware graphics/audio proof.
- `tools/debugger/catalog.py`
  - updates the audit wording for `whole_rom_replay_localization` and content mirrors so the capability bucket advertises the new guardrails without claiming side-effect-complete reverse execution.
- `tools/debugger/tests/test_catalog.py`
  - locks the hook-order matrix shape, hardware side-effect proof gate, dynamic-taint downgrade propagation, and visual/audio evidence-class boundaries.

Validation after patch:

- `python -m tools.debugger hook-order-probe --execute --json-out .local\tmp\hook_order_matrix.json`
  - passed: 7 scenarios, 14 observations, 14/14 rows matched expected callback-state observations.
  - observed no pre-fetch/non-mutating instruction event source; observed post-write/post-interrupt/post-DMA callback state only where the current PyBoy mechanism exposes it.
- Focused hook/reverse-query/effect-trace/visual/audio regressions: 8 passed.
- Broader validation is still required after this note: full debugger unittest discovery, `python -m tools.debugger audit`, py_compile for touched Python, and `git diff --check`.

Remaining priority from Pro:

- Build the Pan Docs regression suite for TIMA overflow A/B-cycle cases, OAM DMA RAM-access/timing cases, GP/HBlank VRAM DMA timing cases, interrupt-entry stack writes, and boot-ROM end-state cases.
- Treat a small PyBoy fork or instrumentation layer as the strategic direction: add a non-mutating event recorder inside `cpu.fetch_and_execute()` and `cpu.handle_interrupt()` with explicit events such as `before_execute`, `after_execute`, `interrupt_enter`, `stack_write`, `oam_dma_copy`, and `hdma_block_copy`.
- Keep `ready=False` until a fresh audit proves every capability bucket complete with zero blocking gaps and no remaining unproven claims around side-effect-complete reverse execution, subsystem-boundary causal proof, arbitrary runtime/event generation, or script/graphics/audio/map behavioral mirrors.

## Implementation Note - Pan Docs Hardware Regression Gate

Date: 2026-05-20.

Context:

- The hook-order matrix gives a useful self-check for PyBoy's debugger hook boundary, but it is not a Pan Docs hardware-conformance suite.
- The proof substrate now needs an explicit fence for the exact hardware side effects named in the top blocker: TIMA overflow A/B-cycle writes, OAM DMA timing and bus restrictions, CGB GP/HBlank VRAM DMA timing, interrupt-entry stack writes, boot-ROM end state, and LCD dot/mode edges.
- Hook observations, modeled effect traces, framebuffer digests, and sound-buffer digests must remain emulator-observed evidence unless an evidence chain contains explicit runtime hardware events or dedicated case-pass results for the exact hardware case.

References used:

- Supervisor Deep Research report: `C:\Users\lolno\Downloads\codex-supervisor\consults\2026-05-19T2327-response.md`
- Pan Docs OAM DMA timing and bus conflict model: `https://gbdev.io/pandocs/OAM_DMA_Transfer.html`
- Pan Docs TIMA overflow A/B-cycle behavior: `https://gbdev.io/pandocs/Timer_Obscure_Behaviour.html`
- Pan Docs CGB VRAM DMA length/mode/timing model: `https://gbdev.io/pandocs/CGB_Registers.html#ff51ff55--hdma1hdma5-vram-dma`
- Pan Docs interrupt-entry stack/PC behavior: `https://gbdev.io/pandocs/Interrupts.html`
- Pan Docs boot/power-up state model: `https://gbdev.io/pandocs/Power_Up_Sequence.html`
- Pan Docs rendering/dot-mode timing model: `https://gbdev.io/pandocs/Rendering.html`
- PyBoy hook API docs for opcode-replacement hooks: `https://docs.pyboy.dk/`
- Local installed PyBoy source inspected: `C:\Users\lolno\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\pyboy\pyboy.py`, `core\mb.py`, `core\lcd.py`, and `core\timer.py`.

Implemented fix:

- `tools/debugger/hardware_regression.py`
  - adds `build_hardware_regression_report()` and a strict `unified_debugger_hardware_regression_gate` report.
  - defines ten Pan Docs-backed cases: three TIMA overflow A/B-cycle write cases, OAM DMA 160 M-cycle timing, DMG OAM DMA RAM-access restriction, CGB GP DMA CPU-halt timing, CGB HBlank DMA block timing, interrupt-entry stack writes, boot-ROM plus Pokemon Gold end state, and LCD dot/mode edge timing.
  - scans the installed PyBoy source for known fidelity gaps: opcode-replacement hook model, instant OAM DMA TODO, GP DMA cycle TODO, fixed HBlank DMA cycle cost with double-speed TODO, fixed LCD mode buckets, and direct TIMA reload without Pan Docs A/B-cycle semantics.
  - accepts explicit dedicated case-pass evidence only when a matching case carries `hardware_behavior_proven=true` or equivalent passed case metadata.
  - records hook-order matrix rows as `emulator_observed_not_hardware`, so FF46/FF55/interrupt observations can inform investigation without satisfying hardware proof.
- `tools/debugger/__main__.py`
  - adds `python -m tools.debugger hardware-regression-gate`.
  - supports `--execute` to attach a fresh hook-order probe, `--report` for external evidence, `--bootrom` and `--rom` paths, `--strict`, `--json`, and `--json-out`.
- `tools/debugger/catalog.py`
  - makes `python -m tools.debugger hardware-regression-gate --execute` the first command for the `whole_rom_replay_localization` blocker.
  - updates the gap text to state that the Pan Docs gate remains blocking unless each side-effect case has explicit runtime hardware-event or dedicated case-pass evidence.
- `tools/debugger/tests/test_catalog.py`
  - locks the case list, hook-matrix downgrade behavior, explicit-case-pass behavior, strict CLI exit behavior, JSON output, and audit/catalog wording.

Validation after patch:

- `python -m py_compile tools\debugger\hardware_regression.py tools\debugger\__main__.py tools\debugger\__init__.py tools\debugger\catalog.py tools\debugger\tests\test_catalog.py`: passed.
- `python -m tools.debugger hardware-regression-gate --execute --json-out .local\tmp\hardware_regression_gate.json`: passed as a command, intentionally `passed=False`; reported 0/10 cases proven, 10 blocking cases, 6 PyBoy source gaps, and status counts `blocked_pyboy_fidelity_gap=5`, `emulator_observed_not_hardware=4`, `missing_artifact=1`.
- Full debugger unittest discovery: 498 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority from Pro:

- The Pan Docs gate is now present, but every case is still unproven hardware behavior until real runtime hardware-event evidence or dedicated Pan Docs regression case results exist.
- The boot-ROM case still needs a real boot ROM artifact plus Pokemon Gold execution evidence; file presence alone is deliberately insufficient.
- Stock PyBoy still has the local source gaps named above, so a small fork or instrumentation layer remains the likely strategic direction: record non-mutating `before_execute`, `after_execute`, `interrupt_enter`, `stack_write`, `oam_dma_copy`, and `hdma_block_copy` events from inside CPU/interrupt/DMA execution instead of treating opcode-replacement hooks as proof-grade attribution.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Causal Graph Proof Boundary Preservation

Date: 2026-05-20.

Context:

- `effect_trace.py` now marks hardware-modeled DMA/timer/interrupt/LCD side-effect items as `proof_status=planned_only` when the chain lacks explicit runtime hardware-event evidence.
- `effect_trace.py` also marks bank-qualified watch hits as `target_match_proof_status=planned_only` when a requested banked target only matched by 16-bit bus address without runtime bank state.
- The causal graph and visualization consumers still need to preserve those downgrades. Otherwise a downstream report can make a planned hardware model or bank-unverified target hit look like instruction-observed proof.

References used:

- Pan Docs memory map for bank-qualified versus unbanked address spaces: `https://gbdev.io/pandocs/Memory_Map.html`
- Pan Docs OAM DMA timing and bus conflict model: `https://gbdev.io/pandocs/OAM_DMA_Transfer.html`
- Local source truth: `tools/debugger/address.py`, `tools/debugger/effect_trace.py`, `tools/debugger/causal_graph.py`, `tools/debugger/visualization.py`

Implemented fix:

- `tools/debugger/causal_graph.py`
  - derives graph effect-node and effect-edge proof from each effect item's `proof_status`, `hardware_event_required`, and `hardware_proof_gate` instead of hardcoding `instruction_observed`.
  - derives watch-hit node and edge proof from `target_match_proof_status`, `proof_status`, and bank-match status.
  - keeps observed instruction nodes as `instruction_observed`, while the claimed effect/target relationship can remain `planned_only`.
  - includes proof-gate and downgrade fields in effect evidence without dropping existing transfer-blocked evidence.
- `tools/debugger/effect_trace.py`
  - carries aggregate `proof_status` and `proof_statuses` through `side_effect_index` entries and side-effect triggers.
- `tools/debugger/visualization.py`
  - shows planned-only proof on bank-unverified effect watch-hit timeline events.
  - preserves effect proof on visualization graph nodes/edges for post-value, register-write, and unmodeled-effect surfaces.
  - derives side-effect timeline proof from the side-effect index instead of silently omitting it.
- `tools/debugger/catalog.py`
  - updates the `causal_provenance` blocker to credit the new proof-preserving consumer boundary while keeping the bucket partial.

Regression strengthened:

- `test_effect_trace_banked_symbol_watch_requires_runtime_bank_match`
  - now verifies causal graph watch-hit nodes/edges and the visualization timeline keep bank-unverified target matches at `planned_only`.
- `test_causal_graph_preserves_hardware_gated_effect_proof_status`
  - covers an FF46 OAM DMA trigger where modeled DMA copy reads/writes are present but hardware runtime events are missing.
  - verifies the graph keeps those DMA copy effect nodes and address edges at `planned_only`.
- `test_capability_report_keeps_whole_rom_goal_incomplete`
  - now checks the audit text advertises this boundary without claiming causal proof completion.

Validation after patch:

- Focused causal/effect/visual proof-boundary regressions: 4 passed.
- Full debugger unittest discovery: 499 passed.
- `python -m py_compile tools\debugger\causal_graph.py tools\debugger\effect_trace.py tools\debugger\visualization.py tools\debugger\catalog.py tools\debugger\tests\test_catalog.py`: passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `git diff --check`: passed; it only reported existing CRLF normalization warnings in unrelated dirty files.

Remaining priority from Pro:

- This prevents a concrete downstream proof promotion path, but it does not replace subsystem dynamic proof.
- Whole-ROM causal proof still needs a non-mutating event source for hardware side effects, stronger checkpointed reverse execution, and runtime evidence for script/graphics/audio/map behavioral mirrors.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Visual/Audio Snapshot Mirror Proof Boundary

Date: 2026-05-20.

Context:

- Visual and audio snapshot reports already carried `hardware_behavior_proven=false`, but the expectation-to-compare bridge could still turn a passed framebuffer or audio-sample expectation into `proof_status=mirror_passed`.
- That blurred the UI/report distinction between "PyBoy framebuffer or sound buffer digest observed" and "hardware PPU/APU behavior proven."
- The proof substrate must let these expectations pass as emulator-observed evidence without promoting them to hardware behavioral mirrors.

References used:

- PyBoy screen API docs: `https://docs.pyboy.dk/api/screen.html`
- PyBoy sound API docs: `https://docs.pyboy.dk/api/sound.html`
- Local source truth: `tools/debugger/visual_snapshot.py`, `tools/debugger/audio_snapshot.py`, `tools/debugger/expect.py`, `tools/debugger/mirrors.py`, `tools/debugger/ranking.py`, and `tools/debugger/impact.py`

Implemented fix:

- `tools/debugger/expect.py`
  - carries `evidence_class`, `hardware_behavior_proven`, `hardware_proof_status`, and `hardware_proof_boundary` into visual framebuffer and audio snapshot expectation evidence.
  - keeps framebuffer/audio expectations passable when executed PyBoy snapshot evidence exists, but exposes that the evidence is emulator-observed and not hardware-proven.
- `tools/debugger/mirrors.py`
  - carries the same hardware-boundary fields through runtime mirror evidence records for visual/audio snapshots.
  - adds `mirror_status`, `actual_proof_status`, `expected_proof_status`, `runtime_proof_statuses`, `hardware_proof_statuses`, `emulator_observed_runtime_kinds`, and `proof_downgrade_reason` to snapshot-backed dynamic expectation mirror matches.
  - keeps `status=passed` and `mirror_status=passed` for satisfied expectations, but downgrades snapshot-backed proof from `mirror_passed` to `runtime_observed` when the evidence chain only proves PyBoy framebuffer/audio snapshot state.
- `tools/debugger/catalog.py`
  - updates the `differential_mirrors` gap text to say snapshot-backed compare/expectation matches stay `runtime_observed` with `hardware_proof_statuses=not_proven` rather than promoting to hardware mirror proof.
- `tools/debugger/tests/test_catalog.py`
  - strengthens visual/audio expectation and compare tests so expectation pass, compare match, ranking, and impact all preserve the hardware-not-proven boundary.

Validation after patch:

- Focused visual/audio expectation boundary regressions: 6 passed.
- Sampled snapshot and adjacent output-mirror proof-boundary regressions: 9 passed.
- Full debugger unittest discovery: 499 passed.
- `python -m py_compile tools\debugger\expect.py tools\debugger\mirrors.py tools\debugger\catalog.py tools\debugger\tests\test_catalog.py`: passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `git diff --check`: passed; it only reported existing CRLF normalization warnings in unrelated dirty files.

Remaining priority from Pro:

- This closes another UI/report proof-promotion leak, but it does not implement pixel-accurate graphics/UI behavior, full audio playback/mixer behavior, arbitrary script/event runtime generation, side-effect-complete reverse execution, or subsystem-complete causal proof.
- PyBoy framebuffer and sound-buffer evidence remains useful runtime observation, not hardware proof.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Hardware Gate Explicit Evidence Proof Boundary

Date: 2026-05-20.

Context:

- The Pan Docs hardware regression gate accepts external/dedicated case-result reports so future hardware-event recorders or test ROM runners can feed it.
- That import path must not let a generic `passed=true` case result close a hardware side-effect gate unless the result also explicitly proves hardware behavior.
- This matters because the top blocker is specifically about TIMA overflow cycles, DMA timing/bus restrictions, interrupt entry, boot-ROM end state, and LCD mode edges; emulator-only or modeled checks should remain evidence, not proof.

References used:

- Pan Docs OAM DMA timing and bus conflict model: `https://gbdev.io/pandocs/OAM_DMA_Transfer.html`
- Pan Docs TIMA overflow A/B-cycle behavior: `https://gbdev.io/pandocs/Timer_Obscure_Behaviour.html`
- Pan Docs CGB VRAM DMA timing model: `https://gbdev.io/pandocs/CGB_Registers.html#ff51ff55--hdma1hdma5-vram-dma`
- PyBoy API docs for current emulator/runtime integration context: `https://docs.pyboy.dk/`

Implemented fix:

- `tools/debugger/hardware_regression.py`
  - requires imported per-case `passed`/`hardware_passed` records to also carry `hardware_behavior_proven=true`, `hardware_event_observed=true`, or an explicit hardware-event evidence marker before classifying them as `explicit_hardware_case_pass`.
  - records weak case results as `explicit_hardware_case_result` with `status=declared_pass_without_hardware_proof` so they remain visible evidence without satisfying the gate.
- `tools/debugger/catalog.py`
  - updates the top blocker wording to state that dedicated case-pass evidence must carry `hardware_behavior_proven=true`.
- `tools/debugger/tests/test_catalog.py`
  - adds a regression proving a `passed=true` OAM DMA case without hardware proof stays `planned_only` and does not close the gate.

Validation after patch:

- Focused hardware-gate proof-boundary regressions: 4 passed.
- `python -m py_compile tools\debugger\hardware_regression.py tools\debugger\catalog.py tools\debugger\tests\test_catalog.py`: passed.
- Full debugger unittest discovery: 500 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `git diff --check`: passed; it only reported existing CRLF normalization warnings in unrelated dirty files.

Remaining priority from Pro:

- This closes an import/proof-promotion leak, but it still does not implement the dedicated Pan Docs runtime case runner for TIMA A/B-cycle behavior, OAM DMA timing and RAM-access restriction, GP/HBlank VRAM DMA timing, interrupt entry, boot-ROM end state, or LCD dot-mode edges.
- The hardware gate remains intentionally blocking until those side effects have explicit runtime hardware-event evidence or proven dedicated case results.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Output Sink Mirror Hardware-Gated Effect Boundary

Date: 2026-05-20.

Context:

- Content output-sink mirrors can pass when supplied runtime evidence observes every requested sink.
- `effect_trace` now marks hardware-modeled side effects such as OAM DMA, CGB VRAM DMA, timer overflow, LCD mode edges, and interrupt-entry effects as `planned_only` unless explicit runtime hardware-event evidence exists.
- The compare bridge must preserve that downgrade. A modeled hardware effect write to a requested output address is useful evidence, but it is not a strong output-sink mirror pass without the hardware event.

References used:

- Pan Docs OAM DMA timing and bus conflict model: `https://gbdev.io/pandocs/OAM_DMA_Transfer.html`
- Local source truth: `tools/debugger/effect_trace.py`, `tools/debugger/mirrors.py`, `tools/debugger/catalog.py`, and `tools/debugger/tests/test_catalog.py`

Implemented fix:

- `tools/debugger/mirrors.py`
  - splits effect-trace concrete writes into strong and weak records.
  - treats concrete writes as strong only when they are not missing a required hardware runtime event and their proof status is strong enough.
  - carries hardware-gated concrete writes into weak output-sink evidence with a downgrade reason instead of letting them satisfy `content_output_behavioral_mirror`.
- `tools/debugger/catalog.py`
  - updates the `differential_mirrors` blocker text to say hardware-gated effect-trace writes remain weak evidence until explicit runtime hardware events exist.
- `tools/debugger/tests/test_catalog.py`
  - adds `test_compare_output_sink_mirror_does_not_pass_from_hardware_gated_effect_write`, covering an FF46 output sink backed only by a planned-only OAM DMA effect write.

Validation after patch:

- Focused output-sink mirror proof-boundary regressions: 4 passed.
- `python -m py_compile tools\debugger\mirrors.py tools\debugger\tests\test_catalog.py`: passed.
- Full debugger unittest discovery: 501 passed.
- `python -m py_compile tools\debugger\mirrors.py tools\debugger\catalog.py tools\debugger\tests\test_catalog.py`: passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `git diff --check`: passed; it only reported existing CRLF normalization warnings in unrelated dirty files.

Remaining priority from Pro:

- This closes a concrete compare/mirror proof-promotion path, but it does not produce the missing hardware runtime events.
- Full script VM behavior, pixel-accurate graphics/UI behavior, full audio playback/mixer behavior, arbitrary map interactions, side-effect-complete reverse execution, and subsystem-complete causal proof remain incomplete.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Invalid Runtime Report Evidence Boundary

Date: 2026-05-20.

Context:

- Several compare/mirror import paths consume already-built debugger reports as evidence.
- A report carrying `valid=false` must not become runtime proof, runtime attempt evidence, or hardware case-pass evidence.
- This is a report-boundary proof-promotion issue rather than a hardware-model change: invalid packets should stay ignored or visible as invalid evidence, not close a mirror or Pan Docs gate.

References used:

- Local source truth: `tools/debugger/mirrors.py`, `tools/debugger/hardware_regression.py`, and `tools/debugger/tests/test_catalog.py`

Implemented fix:

- `tools/debugger/mirrors.py`
  - ignores invalid loaded reports when collecting explicit runtime observations.
  - ignores invalid watch/replay attempts.
  - ignores invalid reports when deriving runtime mirror evidence.
  - skips invalid content-state and content-fuzz reports before building behavioral mirror matches.
- `tools/debugger/hardware_regression.py`
  - treats invalid hardware evidence reports as `invalid_report` / `ignored`, so even `hardware_behavior_proven=true` inside an invalid report cannot satisfy a Pan Docs gate.
- `tools/debugger/tests/test_catalog.py`
  - adds regressions for invalid hardware case-pass evidence, invalid watch evidence in dynamic expectation mirrors, and invalid effect-trace evidence in output-sink mirrors.

Validation after patch:

- Focused invalid-report proof-boundary regressions: 5 passed.
- `python -m py_compile tools\debugger\mirrors.py tools\debugger\hardware_regression.py tools\debugger\tests\test_catalog.py`: passed.
- Full debugger unittest discovery: 504 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- Final touched-file `py_compile`: passed.
- `git diff --check`: passed; it only reported existing CRLF normalization warnings in unrelated dirty files.

Remaining priority from Pro:

- This closes a report-ingestion proof-promotion leak. It does not add the missing runtime generators, hardware event recorder, full script VM mirror, pixel/audio hardware mirrors, side-effect-complete reverse execution, or subsystem-complete causal proof.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Hardware Gate Fact-Class Separation

Date: 2026-05-20.

Context:

- The Pan Docs hardware gate deliberately keeps PyBoy hook observations and modeled traces from satisfying hardware cases.
- Its case records still exposed the original mixed `evidence` list as the main machine surface, which made static case requirements, static source blockers, emulator/runtime observations, and hardware-proof evidence easy for downstream reports to blur.
- The proof substrate needs these fact classes separated without breaking existing JSON/report consumers.

References used:

- Pan Docs TIMA overflow A/B-cycle behavior: `https://gbdev.io/pandocs/Timer_Obscure_Behaviour.html`
- Pan Docs OAM DMA timing and bus conflict model: `https://gbdev.io/pandocs/OAM_DMA_Transfer.html`
- Pan Docs CGB VRAM DMA GP/HBlank timing model: `https://gbdev.io/pandocs/CGB_Registers.html#ff51ff55--hdma1hdma5-vram-dma`
- Pan Docs interrupt-entry stack/PC behavior: `https://gbdev.io/pandocs/Interrupts.html`
- Pan Docs boot/power-up state model: `https://gbdev.io/pandocs/Power_Up_Sequence.html`
- Pan Docs rendering/dot-mode timing model: `https://gbdev.io/pandocs/Rendering.html`
- PyBoy hook/API documentation: `https://docs.pyboy.dk/`

Implemented fix:

- `tools/debugger/hardware_regression.py`
  - keeps the existing per-case `evidence` list intact for compatibility.
  - adds per-case `requested_static_facts`, `observed_runtime_facts`, `emulator_observed_facts`, `hardware_proof_facts`, and `static_blocker_facts` with matching counts.
  - adds top-level `observed_runtime_case_count`, `hardware_proof_case_count`, and `static_blocker_case_count`.
  - labels fact summaries with explicit `fact_type` values such as `emulator_runtime_observation`, `static_source_gap`, and `dedicated_hardware_case_proof`.
- `tools/debugger/__main__.py`
  - prints the new hardware-gate fact counts in the text report so the CLI visibly separates emulator observations from hardware proof.
- `tools/debugger/catalog.py`
  - updates the replay/localization blocker wording to advertise the new boundary while keeping the bucket partial.
- `tools/debugger/tests/test_catalog.py`
  - verifies hook-order evidence increments runtime/emulator fact counts without incrementing hardware-proof counts.
  - verifies explicit dedicated hardware passes populate hardware-proof facts.
  - verifies boot-ROM missing-artifact evidence remains a static blocker and not runtime observation.

Validation after patch:

- Focused hardware-gate fact separation regressions: 7 passed.
- `python -m py_compile tools\debugger\hardware_regression.py tools\debugger\__main__.py tools\debugger\catalog.py tools\debugger\tests\test_catalog.py`: passed.
- `python -m tools.debugger hardware-regression-gate --execute`: passed as a command, still intentionally `passed=False`; reported 4 runtime-observed emulator cases, 0 hardware-proof cases, and 10 static-blocker cases.
- Full debugger unittest discovery: 504 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- Final touched-file `py_compile`: passed.
- `git diff --check`: passed; it only reported existing CRLF normalization warnings in unrelated dirty files.

Remaining priority from Pro:

- This makes the hardware gate safer for UI/report consumers, but it does not add the missing non-mutating event recorder or dedicated Pan Docs runtime case runner.
- TIMA A/B-cycle behavior, OAM DMA timing/RAM-access restriction, GP/HBlank VRAM DMA timing, interrupt-entry stack writes, boot-ROM end state, and LCD dot/mode edge timing remain unproven hardware cases.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Runtime Bank-State Address Fact Boundary

Date: 2026-05-20.

Context:

- Address proof needs a clean boundary between requested/static address syntax and observed runtime address facts.
- External instruction traces can carry raw bank-register values. If those raw values are used directly as address-key banks, the debugger can create impossible exact keys such as `wramx:00:D141` or `vram:FE:8000`.
- Pan Docs defines ROMX as banks 1-NN, CGB VRAM as bank 0/1, and CGB WRAM D000-DFFF as banks 1-7 with FF70 value 0 mapping to bank 1. The debugger should canonicalize runtime bank state before generating proof keys and reject impossible exact requested bank keys.

References used:

- Pan Docs memory map, including ROMX bank 1-NN, VRAM bank 0/1, and WRAM bank 1-7 address ranges: `https://gbdev.io/pandocs/Memory_Map.html`
- Pan Docs FF4F VRAM bank register: `https://gbdev.io/pandocs/CGB_Registers.html#ff4f--vbk-cgb-mode-only-vram-bank`
- Pan Docs FF70 WRAM bank register: `https://gbdev.io/pandocs/CGB_Registers.html#ff70--svbk-cgb-mode-only-wram-bank`

Implemented fix:

- `tools/debugger/address.py`
  - rejects impossible exact requested bank keys for ROMX, CGB WRAMX, and VRAM: ROMX must be bank 1+, WRAMX must be bank 1-7, and VRAM must be bank 0-1.
  - keeps static bank 0 prefixes for unbanked spaces such as WRAM0/IO as non-exact compatibility syntax.
  - keeps invalid observed bank requests visible through `requested_bank`, `bank_semantics`, and `bank_valid=false` rather than producing an exact runtime key.
- `tools/debugger/dynamic_taint.py`
  - canonicalizes parsed runtime bank state before effect tracing uses it: WRAM values are masked to 0-7 with 0 remapped to 1, VRAM values are masked to bit 0, and ROM bank 0 is normalized to bank 1 for the current MBC-style observed ROM bank field.
  - derives canonical WRAM/VRAM banks from raw `wram_raw`/`vram_raw` fields when a trace only supplies raw register bytes.
  - stops treating bank 0 as "unbanked" for banked VRAM/ROM watch-value matching.
- `tools/debugger/reverse_query.py`
  - adds additive `requested_static_address`, `observed_runtime_address`, and `address_fact_boundary` objects to each reverse-query result.
  - preserves existing result fields while making exact matches, bus-address fallback, ambiguous runtime banks, and proof downgrades machine-visible for downstream UI/report consumers.
- `tools/debugger/catalog.py`
  - updates the replay/localization blocker wording to mention canonicalized runtime bank state and requested-static versus observed-runtime address boundaries.
- `tools/debugger/tests/test_catalog.py`
  - adds regressions for invalid requested WRAMX/VRAM bank syntax, invalid observed bank requests, raw runtime bank-state canonicalization, VRAM bank-0 watch matching, and reverse-query address fact boundaries.

Validation after patch:

- Focused address/bank/reverse-query regressions: 8 passed.
- `python -m py_compile tools\debugger\address.py tools\debugger\dynamic_taint.py tools\debugger\effect_trace.py tools\debugger\reverse_query.py tools\debugger\catalog.py tools\debugger\tests\test_catalog.py`: passed.
- Full debugger unittest discovery: 505 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- Final touched-file `py_compile`: passed.
- `git diff --check`: passed; it only reported existing CRLF normalization warnings in unrelated dirty files.

Remaining priority from Pro:

- This improves address/bank precision for reverse proof and prevents impossible exact bank keys, but it is not a full typed `BankState` object or side-effect-complete reverse executor.
- Runtime bank proof still depends on supplied trace bank-state evidence or inferred bank writes in the captured window.
- Full script VM behavior, arbitrary event-engine state generation, pixel/audio hardware mirrors, and dedicated Pan Docs runtime hardware cases remain incomplete.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Reverse Query Boundary Propagation

Date: 2026-05-20.

Context:

- The reverse-query report now distinguishes requested/static address facts from observed/runtime address facts.
- Downstream consumers still formed ranked findings, impact items, causal graph nodes/edges, visualization events, and static report evidence primarily from older `matched_address`, `match_precision`, and `bank_match` strings.
- That made a UI/report boundary capable of flattening "requested D141" into "observed banked writer" unless a reader opened the raw reverse-query result.

References used:

- Local source truth: `tools/debugger/reverse_query.py`, `tools/debugger/ranking.py`, `tools/debugger/impact.py`, `tools/debugger/causal_graph.py`, `tools/debugger/visualization.py`, and `tools/debugger/reporting.py`.

Implemented fix:

- `tools/debugger/address_boundary.py`
  - adds shared formatting for reverse-query address-boundary fields, evidence strings, related address keys, and timeline summaries.
  - exposes a boundary veto used by downstream consumers when `exact_runtime_address_proven=false`.
- `tools/debugger/reverse_query.py`
  - prepends boundary evidence to each result and includes requested/observed address keys plus `exact_runtime_address_proven` in evidence atoms.
- `tools/debugger/ranking.py`
  - carries `requested_static_address`, `observed_runtime_address`, and `address_fact_boundary` into reverse-query findings.
  - puts boundary evidence first so static reports and humans see proof caveats before older writer evidence.
  - forces planned-only proof when an imported reverse-query result carries an unproven exact runtime address boundary, even if the rest of the packet claims stronger proof.
- `tools/debugger/impact.py`
  - preserves reverse-query boundary fields when converting ranked findings into impact items.
- `tools/debugger/causal_graph.py`
  - adds requested-static-address and observed-runtime-address nodes.
  - adds `requests_static_address`, `supplies_runtime_address`, and `address_fact_boundary` edges.
  - keeps the boundary edge `planned_only` unless `exact_runtime_address_proven=true`.
  - treats `exact_runtime_address_proven=false` as a downstream proof-promotion veto for reverse-query nodes and edges.
- `tools/debugger/visualization.py`
  - carries boundary fields into timeline events and graph nodes/edges.
  - adds visible requested/observed address nodes and boundary relations in the visualization graph.
  - treats `exact_runtime_address_proven=false` as a downstream proof-promotion veto for reverse-query timeline and graph surfaces.
- `tools/debugger/tests/test_catalog.py`
  - extends the ambiguous WRAM bank-collision reverse-query regression through ranked findings, impact items, static reports, causal graph, and visualization surfaces.
  - adds a contradictory imported reverse-query packet regression where validation and report-level proof claim instruction-observed, but `exact_runtime_address_proven=false` keeps ranking, impact, graph, and visualization planned-only.

Validation after patch:

- Focused reverse-query boundary propagation regressions: 10 passed.
- `python -m py_compile tools\debugger\address_boundary.py tools\debugger\reverse_query.py tools\debugger\ranking.py tools\debugger\impact.py tools\debugger\causal_graph.py tools\debugger\visualization.py tools\debugger\tests\test_catalog.py`: passed.
- Full debugger unittest discovery: 505 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `git diff --check`: passed; it only reported existing CRLF normalization warnings in unrelated dirty files.

Remaining priority from Pro:

- This closes a UI/report flattening path for requested/static versus observed/runtime address facts, but it does not add new runtime hardware events, a non-mutating PyBoy event recorder, or side-effect-complete reverse execution.
- Full script VM behavior, arbitrary event-engine runtime generation, pixel/audio hardware mirrors, dedicated Pan Docs runtime hardware cases, and subsystem-complete causal proof remain incomplete.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Hardware Runtime Event Fact Scope

Date: 2026-05-20.

Context:

- The Pan Docs hardware gate already separated requested/static case facts, emulator/runtime observations, static blockers, and hardware-proof facts.
- A runtime hardware-event fact was still counted under `hardware_proof_facts` even when the case did not assert `hardware_behavior_proven=true` and did not pass the exact Pan Docs case.
- That is a proof-promotion risk: an observed interrupt/OAM/HDMA/timer event is useful runtime evidence, but it is not by itself proof of the full case-specific timing, bus, or A/B-cycle behavior.

References used:

- Pan Docs OAM DMA timing and bus restrictions: `https://gbdev.io/pandocs/OAM_DMA_Transfer.html`
- Pan Docs CGB VRAM DMA GP/HBlank timing: `https://gbdev.io/pandocs/CGB_Registers.html#ff51ff55--hdma1hdma5-vram-dma`
- Pan Docs TIMA overflow A/B-cycle behavior: `https://gbdev.io/pandocs/Timer_Obscure_Behaviour.html`
- Pan Docs interrupt entry stack/PC behavior: `https://gbdev.io/pandocs/Interrupts.html`

Implemented fix:

- `tools/debugger/hardware_regression.py`
  - keeps `runtime_hardware_event` in observed runtime facts.
  - removes `runtime_hardware_event` from hardware-proof facts; only explicit case passes with hardware proof now populate `hardware_proof_facts`.
  - adds `proof_scope` to summarized evidence facts so downstream reports can distinguish `observed_runtime_not_case_complete` from `case_hardware_proof`.
  - adds `runtime_observed_not_case_complete` gate status when runtime hardware events exist but no exact case-level hardware proof is supplied.
- `tools/debugger/tests/test_catalog.py`
  - verifies hook-order emulator facts carry `proof_scope=emulator_observed_not_hardware`.
  - verifies an effect-trace runtime hardware event for interrupt entry remains observed runtime evidence, keeps `hardware_proof_fact_count=0`, and leaves the case planned-only until exact case proof exists.
  - verifies explicit dedicated case passes still populate `hardware_proof_facts` with `proof_scope=case_hardware_proof`.

Validation after patch:

- Focused hardware-regression fact-scope regressions: 7 passed.
- `python -m tools.debugger hardware-regression-gate --execute`: passed as a command, still intentionally `passed=False`; reported 0/10 cases passing, 10 blocking cases, 4 runtime-observed emulator cases, 0 hardware-proof cases, and 10 static-blocker cases.
- Full debugger unittest discovery: 507 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile tools\debugger\hardware_regression.py tools\debugger\tests\test_catalog.py`: passed.
- `git diff --check`: passed; it only reported existing CRLF normalization warnings in unrelated dirty files.

Remaining priority from Pro:

- This fixes a hardware-gate fact classification leak, but it still does not create the missing dedicated Pan Docs runtime case runner or non-mutating PyBoy event recorder.
- TIMA A/B-cycle cases, OAM DMA timing/RAM-access restriction, CGB GP/HBlank VRAM DMA timing, interrupt-entry stack writes, boot-ROM end state, and LCD dot/mode edge timing remain unproven unless exact hardware case evidence is supplied.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Hardware Fact Scope Report Propagation

Date: 2026-05-20.

Context:

- `unified_debugger_hardware_regression_gate` now emits `proof_scope` distinctions, but ranked/static/impact reports previously treated the report as an unsupported kind.
- Visualization and causal graph output also lacked first-class Pan Docs hardware case nodes, so runtime observations could become visible only through generic report blobs instead of explicit "observed runtime, not case proof" relationships.
- This is another subsystem-boundary proof-promotion risk: the hardware gate can be honest internally while downstream UI/report surfaces lose the distinction.

References used:

- Pan Docs OAM DMA timing and bus restrictions: `https://gbdev.io/pandocs/OAM_DMA_Transfer.html`
- Pan Docs CGB VRAM DMA GP/HBlank timing: `https://gbdev.io/pandocs/CGB_Registers.html#ff51ff55--hdma1hdma5-vram-dma`
- Pan Docs TIMA overflow A/B-cycle behavior: `https://gbdev.io/pandocs/Timer_Obscure_Behaviour.html`
- Pan Docs interrupt entry stack/PC behavior: `https://gbdev.io/pandocs/Interrupts.html`

Implemented fix:

- `tools/debugger/ranking.py`
  - adds first-class `hardware_regression_blocker` findings for blocked Pan Docs cases.
  - includes gate status, hardware proof counts, observed runtime counts, `proof_scope`, required evidence, and Pan Docs URLs in finding evidence.
- `tools/debugger/impact.py`
  - receives the new findings through the existing ranked-finding pipeline, preserving planned-only proof and fact-scope evidence.
- `tools/debugger/reporting.py`
  - receives the new findings through the existing static report pipeline, so static reports no longer show hardware gates as unsupported report kinds.
- `tools/debugger/visualization.py`
  - adds hardware regression timeline events and graph nodes for cases, runtime facts, hardware proof facts, and static blockers.
  - uses `observes_runtime_not_case_proof` edges for runtime observations that do not prove the case.
- `tools/debugger/causal_graph.py`
  - adds matching hardware gate, case, runtime-fact, proof-fact, and static-blocker nodes.
  - keeps runtime-fact edges planned-only unless exact case proof is present.
- `tools/debugger/catalog.py`
  - updates the replay/localization blocker wording to mention downstream `proof_scope` propagation.
- `tools/debugger/tests/test_catalog.py`
  - verifies a runtime interrupt hardware event remains planned-only through rank, impact, static report, visualization, and causal graph surfaces.

Validation after patch:

- Focused hardware fact-scope propagation regressions: 5 passed.
- `python -m tools.debugger hardware-regression-gate --execute`: passed as a command, still intentionally `passed=False`; reported 0/10 cases passing, 10 blocking cases, 4 runtime-observed emulator cases, 0 hardware-proof cases, and 10 static-blocker cases.
- Full debugger unittest discovery: 508 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile tools\debugger\ranking.py tools\debugger\visualization.py tools\debugger\causal_graph.py tools\debugger\catalog.py tools\debugger\tests\test_catalog.py`: passed.
- `git diff --check`: passed; it only reported existing CRLF normalization warnings in unrelated dirty files.

Remaining priority from Pro:

- This closes a downstream report/UI propagation leak for Pan Docs hardware case evidence, but it still does not add the missing dedicated hardware runner or non-mutating event recorder.
- The hardware gate still reports no case-level proof for TIMA A/B-cycle behavior, OAM DMA timing/RAM-access restriction, CGB GP/HBlank VRAM DMA timing, interrupt-entry stack writes, boot-ROM end state, or LCD dot/mode edge timing without explicit exact evidence.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Case-Specific Hardware Event Requirements

Date: 2026-05-20.

Context:

- The hardware regression gate correctly required `hardware_behavior_proven=true` for imported dedicated case passes, but a bare case pass could still omit the actual event coverage that made the Pan Docs claim true.
- That was another proof-promotion boundary risk: a future hardware runner or PyBoy fork should be able to close cases, but only by supplying the event types that match the exact timer, DMA, interrupt, boot-ROM, or LCD behavior under test.

References used:

- Pan Docs TIMA overflow A/B-cycle behavior: `https://gbdev.io/pandocs/Timer_Obscure_Behaviour.html`
- Pan Docs OAM DMA timing and bus restrictions: `https://gbdev.io/pandocs/OAM_DMA_Transfer.html`
- Pan Docs CGB VRAM DMA GP/HBlank timing: `https://gbdev.io/pandocs/CGB_Registers.html#ff51ff55--hdma1hdma5-vram-dma`
- Pan Docs interrupt entry stack/PC behavior: `https://gbdev.io/pandocs/Interrupts.html`
- Pan Docs boot-ROM register end state: `https://gbdev.io/pandocs/Power_Up_Sequence.html`
- Pan Docs rendering dot/mode timing and memory restrictions: `https://gbdev.io/pandocs/Rendering.html`

Implemented fix:

- `tools/debugger/hardware_regression.py`
  - adds `required_event_types` to every Pan Docs hardware case.
  - rejects imported dedicated case passes that declare `hardware_behavior_proven=true` but do not include the required case-specific event types in `hardware_events`, `event_types`, or related event fields.
  - records observed and missing event types on explicit case evidence, preserving the report shape while adding proof-auditable fields.
- `tools/debugger/ranking.py`, `tools/debugger/causal_graph.py`, and `tools/debugger/visualization.py`
  - surface `required_event_types` and missing event types so downstream UI/report consumers do not flatten a weak external case result into hardware proof.
- `tools/debugger/catalog.py`
  - updates the replay/localization blocker wording to say hardware passes require both `hardware_behavior_proven=true` and the required case-specific hardware event types.
- `tools/debugger/tests/test_catalog.py`
  - verifies Pan Docs cases expose required event types.
  - verifies a valid interrupt-entry case pass with `interrupt_enter` and `stack_write` events still passes that one case.
  - verifies an imported pass missing `stack_write` stays planned-only and does not populate `hardware_proof_facts`.

Validation after patch:

- Focused hardware event-requirement regressions: 6 passed.
- `python -m tools.debugger hardware-regression-gate --execute`: passed as a command, still intentionally `passed=False`; reported 0/10 cases passing, 10 blocking cases, 4 runtime-observed emulator cases, 0 hardware-proof cases, and 10 static-blocker cases.
- Full debugger unittest discovery: 509 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile tools\debugger\hardware_regression.py tools\debugger\ranking.py tools\debugger\visualization.py tools\debugger\causal_graph.py tools\debugger\catalog.py tools\debugger\tests\test_catalog.py`: passed.
- `git diff --check`: passed; it only reported existing CRLF normalization warnings in unrelated dirty files.

Remaining priority from Pro:

- This closes a dedicated-case import overclaim path, but it still does not implement the actual Pan Docs runtime case runner or non-mutating event recorder.
- TIMA A/B-cycle cases, OAM DMA timing/RAM-access restriction, CGB GP/HBlank VRAM DMA timing, interrupt-entry stack writes, boot-ROM end state, and LCD dot/mode edge timing remain unproven without exact runtime case evidence.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Non-Mutating Hardware Event Stream Ingestion

Date: 2026-05-20.

Context:

- The hardware gate could consume dedicated case-result reports, but it did not have a first-class schema for the strategic PyBoy fork / non-mutating recorder direction.
- That made the next proof path too vague: future runtime instrumentation should emit explicit per-case event streams such as `oam_dma_start`, `oam_dma_copy`, `elapsed_160_mcycles`, `interrupt_enter`, and `stack_write`, not a single broad pass flag.
- The gate still must not treat stock PyBoy hook observations or incomplete event streams as hardware proof.

References used:

- Pan Docs OAM DMA timing and HRAM-only bus restriction: `https://gbdev.io/pandocs/OAM_DMA_Transfer.html`
- Pan Docs CGB GP/HBlank VRAM DMA mode and timing behavior: `https://gbdev.io/pandocs/CGB_Registers.html#ff51ff55--hdma1hdma5-vram-dma`
- Pan Docs TIMA overflow A/B-cycle behavior: `https://gbdev.io/pandocs/Timer_Obscure_Behaviour.html`
- Pan Docs interrupt entry stack/PC behavior: `https://gbdev.io/pandocs/Interrupts.html`

Implemented fix:

- `tools/debugger/hardware_regression.py`
  - adds first-class ingestion for `kind="unified_debugger_hardware_event_stream"` reports.
  - matches events to Pan Docs cases through `hardware_regression_case_id`, `hardware_regression_case_ids`, `case_id`, or `case_ids`.
  - accepts a case as hardware proof only when the stream is proof-grade (`non_mutating_event_recorder=true`, `recorder_kind=non_mutating_event_recorder`, `source_kind=non_mutating_event_recorder`, or explicit hardware-event evidence status), declares `hardware_behavior_proven=true`, and covers every case-specific required event type.
  - records incomplete or non-proof-grade event streams as `hardware_event_stream_result` with `proof_scope=observed_runtime_not_case_complete` instead of case proof.
- `tools/debugger/ranking.py`, `tools/debugger/causal_graph.py`, and `tools/debugger/visualization.py`
  - surface observed and missing event types for hardware event-stream facts.
- `tools/debugger/catalog.py`
  - updates the whole-ROM replay/localization blocker wording to name non-mutating hardware event-stream evidence explicitly.
- `tools/debugger/tests/test_catalog.py`
  - verifies complete non-mutating OAM DMA timing event streams can pass exactly that case.
  - verifies incomplete streams remain runtime-observed/not-case-complete.
  - verifies complete event streams without proof-grade recorder metadata still do not close a case.

Validation after patch:

- Focused hardware event-stream regressions: 6 passed.
- `python -m tools.debugger hardware-regression-gate --execute`: passed as a command, still intentionally `passed=False`; reported 0/10 cases passing, 10 blocking cases, 4 runtime-observed emulator cases, 0 hardware-proof cases, and 10 static-blocker cases.
- Full debugger unittest discovery: 512 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile tools\debugger\hardware_regression.py tools\debugger\ranking.py tools\debugger\visualization.py tools\debugger\causal_graph.py tools\debugger\catalog.py tools\debugger\tests\test_catalog.py`: passed.
- `git diff --check`: passed; it only reported existing CRLF normalization warnings in unrelated dirty files.

Remaining priority from Pro:

- This creates the report contract needed by a non-mutating event recorder, but it still does not implement the recorder inside PyBoy/CPU/DMA/interrupt execution.
- The live hardware gate remains blocked because stock PyBoy supplies hook-matrix observations and source-gap scans, not proof-grade event streams for TIMA, DMA, interrupt, boot-ROM, or LCD cases.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Executable Hardware Event Stream Probe

Date: 2026-05-20.

Context:

- The gate could consume `unified_debugger_hardware_event_stream` reports, but the debugger had no executable route to ask the active PyBoy runtime whether such a recorder exists.
- That left the strategic PyBoy fork direction only as an import contract. The proof substrate needs a command that stock PyBoy can run and truthfully report "no proof-grade recorder here", while an instrumented fork can feed case events into the Pan Docs gate.

References used:

- PyBoy API docs for hooks and the opcode-replacement warning: `https://docs.pyboy.dk/index.html`
- Pan Docs OAM DMA timing and bus restrictions: `https://gbdev.io/pandocs/OAM_DMA_Transfer.html`
- Pan Docs interrupt entry stack/PC behavior: `https://gbdev.io/pandocs/Interrupts.html`

Implemented fix:

- `tools/debugger/hardware_event_stream.py`
  - adds `build_hardware_event_stream_report()` and the report kind `unified_debugger_hardware_event_stream`.
  - probes `pyboy.hardware_event_recorder` or `pyboy.mb.hardware_event_recorder`.
  - accepts only recorders marked `non_mutating_event_recorder` / `non_mutating` / `recorder_kind=non_mutating_event_recorder` as proof-grade.
  - normalizes recorder events to stable `event_type` values and infers candidate Pan Docs case ids from the required event types.
  - reports stock PyBoy as valid executed evidence with `recorder_available=false`, `hardware_behavior_proven=false`, and `proof_status=planned_only`.
- `tools/debugger/__main__.py` and `tools/debugger/__init__.py`
  - add `python -m tools.debugger hardware-event-stream --execute`.
  - add a concise text formatter that makes missing-recorder status visible.
- `tools/debugger/hardware_regression.py`
  - runs the hardware event stream probe during `hardware-regression-gate --execute` in addition to the hook-order matrix.
  - includes the generated event-stream report in gate evidence, while stock PyBoy still contributes no hardware proof facts.
- `tools/debugger/catalog.py`
  - adds the event-stream probe command to the whole-ROM replay/localization capability.
- `tools/debugger/tests/test_catalog.py`
  - verifies missing recorder stays planned-only.
  - verifies a fake proof-grade recorder normalizes OAM DMA events into complete case coverage.
  - verifies `hardware-regression-gate --execute` imports the event-stream probe and can pass exactly the interrupt-entry case when a fake non-mutating recorder emits `interrupt_enter` and `stack_write`.
  - verifies the CLI writes a JSON event-stream report.

Validation after patch:

- Focused hardware event-stream probe regressions: 5 passed.
- `python -m tools.debugger hardware-event-stream --execute`: passed as a command; reported `recorder_available=false`, `hardware_behavior_proven=false`, and `proof=planned_only` on stock PyBoy.
- `python -m tools.debugger hardware-regression-gate --execute`: passed as a command, still intentionally `passed=False`; reported 0/10 cases passing, 10 blocking cases, 4 runtime-observed emulator cases, 0 hardware-proof cases, and 10 static-blocker cases.
- Full debugger unittest discovery: 516 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `PYTHONPYCACHEPREFIX=.local\tmp\pycompile_cache python -m py_compile tools\debugger\hardware_event_stream.py tools\debugger\hardware_regression.py tools\debugger\__main__.py tools\debugger\__init__.py tools\debugger\catalog.py tools\debugger\tests\test_catalog.py`: passed. A first plain `py_compile` attempt hit a Windows pycache rename permission error in `tools\debugger\tests\__pycache__`, so syntax was verified with an isolated pycache prefix.
- `git diff --check`: passed; it only reported existing CRLF normalization warnings in unrelated dirty files.

Remaining priority from Pro:

- This adds the executable integration point for a non-mutating recorder, but stock PyBoy still lacks that recorder and still uses opcode-replacement hooks for debugger callbacks.
- The next strategic implementation step remains the PyBoy fork/instrumentation layer that emits `before_execute`, `after_execute`, `interrupt_enter`, `stack_write`, `oam_dma_copy`, and `hdma_block_copy` events from inside CPU/interrupt/DMA execution.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Object-Event Runtime-Hour Generation

Date: 2026-05-20.

Context:

- The generation audit still named arbitrary hour/runtime event contexts beyond source-declared candidates as a blocker.
- `content-scenarios` already emitted object-event time-of-day mask candidates for each source-declared `MORN`/`DAY`/`NITE` bit, but that gave one representative hour per source time bucket.
- `content-state` could patch `hHours` for numeric hour ranges, but a requested hour for time-of-day mask objects still fell back to the first allowed source mask choice unless a matching `selected_timeofday` was supplied.

References used:

- Local engine source: `home/map_objects.asm:CheckObjectTime` for inclusive hour ranges, overnight ranges, and `wTimeOfDay` mask checks.
- Local RTC source: `engine/rtc/rtc.asm:GetTimeOfDay` for the default 04:00-09:59 morning, 10:00-17:59 day, and 18:00-03:59 night mapping.
- Local object layout source: `constants/map_object_constants.asm` for `MAPOBJECT_HOUR_1`, `MAPOBJECT_HOUR_2`, and `MAPOBJECT_TIMEOFDAY`.
- pret pokecrystal map-event docs for `object_event x, y, sprite, movement, rx, ry, h1, h2, ...`: `https://pret.github.io/pokecrystal/map_event_scripts.html`
- pret pokegold upstream source cross-check for `CheckObjectTime`: `https://raw.githubusercontent.com/pret/pokegold/master/home/map_objects.asm`

Implemented fix:

- `tools/debugger/content_scenarios.py`
  - adds runtime-hour map-position preconditions for time-filtered object events.
  - emits every inclusive numeric hour in source hour ranges, including overnight ranges.
  - emits the concrete `hHours` values corresponding to `MORN`, `DAY`, `NITE`, `ANYTIME`, and numeric time-of-day masks.
  - marks those routes with `selected_time_context_source=runtime_hour_candidate` and `runtime_hour_candidate=true`.
- `tools/debugger/content_state.py`
  - honors a requested numeric `selected_hour` for time-of-day mask objects by deriving the matching `wTimeOfDay` value through the same hour boundaries used by `GetTimeOfDay`.
  - rejects a requested hour whose derived time-of-day value is not allowed by the object mask instead of silently falling back to the first source-declared mask choice.
  - keeps generated hour contexts as planned state materializations until replay/watch/trace evidence proves `CheckObjectTime` consumed them.
- `tools/debugger/catalog.py` and `tools/debugger/generate.py`
  - update generation-gap wording to distinguish generated runtime-hour states from runtime-observed `CheckObjectTime` proof.
- `tools/debugger/tests/test_catalog.py`
  - verifies numeric hour ranges emit generated runtime-hour candidates and materialize an interior hour.
  - verifies `ANYTIME` time-of-day masks emit all runtime-hour candidates and materialize hour 17 as `DAY` with `hHours=17`.

Validation after patch:

- Focused object-event runtime-hour and event-runtime materialization regressions: 24 passed.
- `python -m tools.debugger content-scenarios --source-file maps\PlayersHouse1F.asm --max-cases 24 --json-out .local\tmp\debugger_runtime_hour_scenarios.json`: passed; generated 48 runtime probes and object-event runtime-hour candidates for the PlayersHouse1F Mom morning/day/night variants.

Remaining priority:

- This expands event-state generation, but it does not prove runtime behavior by itself.
- Runtime-observed `CheckObjectTime` consumption for generated hour states, runtime-verified multi-object occupancy, big-object collision/occupancy proof, full script VM behavior under arbitrary event-engine context, pixel/audio playback mirrors, causal proof, and side-effect-complete reverse execution remain incomplete.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Runtime Consumer Requirements for Generated-Hour Mirrors

Date: 2026-05-20.

Context:

- The runtime-hour generator created concrete `hHours`/`wTimeOfDay` states, but a generic content-state behavioral mirror could still pass when runtime observations covered only state sinks.
- For generated object-event hour states, sink observations alone do not prove the event engine consumed the selected hour through `CheckObjectTime`.
- That was a proof-promotion boundary risk between content-state generation and compare/report mirrors.

References used:

- Local engine source: `home/map_objects.asm:CheckObjectTime`.
- Local RTC source: `engine/rtc/rtc.asm:GetTimeOfDay`.
- pret pokegold upstream source cross-check for `CheckObjectTime`: `https://raw.githubusercontent.com/pret/pokegold/master/home/map_objects.asm`

Implemented fix:

- `tools/debugger/content_scenarios.py`
  - attaches `trace_symbols=["TryObjectEvent", "CheckObjectTime"]` and `required_runtime_symbols=["CheckObjectTime"]` to generated runtime-hour object-event preconditions.
  - carries those symbols into `event_runtime_materialization` routes.
  - adds a focused trace-instruction command for route-declared runtime symbols instead of leaving generated-hour proof as a watch-only route.
- `tools/debugger/mirrors.py`
  - aggregates route-declared `required_runtime_symbols` from content-state materializations.
  - keeps content-state behavioral mirrors inconclusive when all expected sinks are observed but required runtime symbols are missing.
  - exposes `required_runtime_symbols`, `observed_runtime_symbols`, and explicit runtime evidence gaps in compare output.
- `tools/debugger/catalog.py`
  - updates the differential mirror blocker wording to make the generated-hour consumer-symbol requirement visible in the audit.
- `tools/debugger/tests/test_event_runtime_materialization.py` and `tools/debugger/tests/test_catalog.py`
  - verify route construction includes `CheckObjectTime` as a required runtime symbol and trace target.
  - verify compare refuses to pass a generated-hour mirror until runtime evidence includes the required consumer symbol.

Validation after patch:

- Focused event-runtime materialization and generated-hour route regressions: 24 passed.
- `python -m py_compile tools\debugger\content_scenarios.py tools\debugger\mirrors.py tools\debugger\tests\test_event_runtime_materialization.py tools\debugger\tests\test_catalog.py`: passed.

Remaining priority:

- This prevents a generated-hour state from promoting to behavioral proof without a `CheckObjectTime` trace, but it still does not execute that trace for arbitrary maps/states.
- Runtime-verified multi-object occupancy, big-object collision/occupancy proof, full script VM behavior under arbitrary event-engine context, pixel/audio playback mirrors, causal proof, and side-effect-complete reverse execution remain incomplete.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Runtime Consumer Requirements for Content-Fuzz Mirrors

Date: 2026-05-20.

Context:

- The content-state mirror now refused to pass generated-hour object-event states without observing the route-declared runtime consumer symbol, but `content_fuzz_behavioral_mirror` still used only expected sink coverage.
- For generated object-event hour fuzz cases, observing patched `hHours`/`wTimeOfDay` sinks is not enough to prove the event route consumed those values through `CheckObjectTime`.
- This left a second proof-promotion boundary at compare/report consumers of content fuzz manifests.

References used:

- Local engine source: `home/map_objects.asm:CheckObjectTime`.
- Local RTC source: `engine/rtc/rtc.asm:GetTimeOfDay`.
- pret pokegold upstream source cross-check for `CheckObjectTime`: `https://raw.githubusercontent.com/pret/pokegold/master/home/map_objects.asm`

Implemented fix:

- `tools/debugger/mirrors.py`
  - aggregates `required_runtime_symbols` from content fuzz cases, runtime targets, state preconditions, and event-runtime materialization routes.
  - keeps content-fuzz behavioral mirrors inconclusive when all expected sinks are observed but required runtime symbols are missing.
  - exposes `required_runtime_symbols`, `observed_runtime_symbols`, and explicit runtime evidence gaps in content-fuzz compare output.
  - includes required runtime symbols in content-fuzz related symbols so localization/trace consumers can see the required consumer.
- `tools/debugger/catalog.py`
  - updates the differential mirror blocker wording to say generated-hour object-event content-state and content-fuzz mirrors both require route-declared runtime consumer symbols such as `CheckObjectTime` before passing.
- `tools/debugger/tests/test_event_runtime_materialization.py`
  - verifies content-fuzz mirrors do not pass from sink coverage alone when `CheckObjectTime` is required.
  - verifies they pass once runtime evidence observes both the sinks and the required runtime consumer symbol.

Validation after patch:

- Focused content-fuzz runtime-consumer regressions: 2 passed.
- Adjacent event-runtime/content-fuzz mirror regressions: 28 passed.
- Full debugger unittest discovery: 521 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `python -m py_compile tools\debugger\mirrors.py tools\debugger\catalog.py tools\debugger\tests\test_event_runtime_materialization.py`: passed, with isolated `PYTHONPYCACHEPREFIX=.local\tmp\pycompile_cache` during the final syntax check.

Remaining priority:

- This prevents content fuzz manifests from promoting generated-hour behavioral proof without a `CheckObjectTime` observation, but it still does not execute the trace for arbitrary event-engine states.
- Runtime-verified multi-object occupancy, big-object collision/occupancy proof, full script VM behavior under arbitrary event-engine context, pixel/audio playback mirrors, causal proof, side-effect-complete reverse execution, and the non-mutating hardware event recorder remain incomplete.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Snapshot Hardware Boundary for Output-Sink Mirrors

Date: 2026-05-20.

Context:

- Visual/audio expectation mirrors already kept PyBoy framebuffer and sound-buffer digest evidence distinct from hardware proof.
- Content output-sink mirrors could also consume visual/audio snapshot runtime evidence, but their match shape did not carry the same hardware downgrade fields.
- That left a UI/report risk where a passed output-sink mirror backed only by PyBoy snapshot evidence could be overread as hardware PPU/APU behavior proof.

References used:

- Local visual/audio snapshot contracts in `tools/debugger/visual_snapshot.py` and `tools/debugger/audio_snapshot.py`.
- Existing compare snapshot boundary handling in `tools/debugger/mirrors.py`.

Implemented fix:

- `tools/debugger/mirrors.py`
  - distinguishes non-snapshot runtime coverage from visual/audio snapshot coverage for content output-sink mirrors.
  - keeps snapshot-only output-sink passes at `proof_status=runtime_observed` and `actual_proof_status=runtime_observed` instead of `mirror_passed`/`observed`.
  - exposes `hardware_behavior_proven`, `hardware_proof_statuses`, `hardware_proof_boundaries`, `emulator_observed_runtime_kinds`, `proof_downgrade_reason`, and `non_snapshot_covered_*` fields on output-sink mirror matches.
  - preserves `mirror_status=passed` when the requested output sink was observed, while making the hardware boundary explicit in evidence and runtime evidence gaps.
- `tools/debugger/catalog.py`
  - updates the differential mirror blocker wording so output-sink mirrors promote to strong passed mirrors only for non-snapshot runtime evidence, while snapshot-only evidence remains runtime-observed/hardware-unproven.
- `tools/debugger/tests/test_catalog.py`
  - verifies effect-trace output-sink evidence still promotes to `mirror_passed`.
  - verifies snapshot-only output-sink evidence remains `runtime_observed`, carries `hardware_behavior_proven=false`, and propagates the downgrade through rank and impact reports.

Validation after patch:

- Focused snapshot/output-sink boundary regressions: 4 passed.
- Adjacent output-sink mirror regressions: 10 passed.
- Full debugger unittest discovery: 522 passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `PYTHONPYCACHEPREFIX=.local\tmp\pycompile_cache python -m py_compile tools\debugger\mirrors.py tools\debugger\catalog.py tools\debugger\tests\test_catalog.py`: passed.

Remaining priority:

- This is a report/proof-boundary fence only; it does not add pixel-accurate PPU playback, full APU playback/mixer proof, or hardware behavior validation for PyBoy snapshot evidence.
- Full script VM behavior under arbitrary event-engine state, runtime-verified object occupancy, causal proof, side-effect-complete reverse execution, and the non-mutating hardware event recorder remain incomplete.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Hook-Order Boundary Propagation for RMW Pre-State Proof

Date: 2026-05-20.

Context:

- The hook-order probe correctly reports PyBoy debugger-hook timing as opcode-replacement breakpoint evidence, not a non-mutating CPU event stream.
- Effect traces could use a passed hook-order matrix to mark RMW old-byte pre-state samples as runtime-observed, but downstream effect history, reverse-query evidence, ranking, and causal graph evidence did not carry the hook mechanism/proof-boundary details.
- That made the evidence easier to overread as proof-grade before-execute CPU instrumentation instead of PyBoy hook callback timing.

References used:

- PyBoy API documentation for `hook_register`, including the hook replacement behavior: `https://docs.pyboy.dk/index.html`
- Local hook-order probe contract in `tools/debugger/hook_order.py`.

Implemented fix:

- `tools/debugger/effect_trace.py`
  - propagates `proof_boundary`, `hook_mechanism`, `non_mutating_instruction_events`, and `pre_fetch_runtime_observed` from hook-order reports into effect-trace hook-order validations.
  - exposes aggregate `hook_order_proof_boundary`, `hook_order_mechanisms`, and `hook_order_non_mutating_instruction_events` on effect-trace reports.
  - attaches `pre_state_observation_model`, `pre_state_proof_boundary`, and `pre_state_non_mutating_instruction_event` to RMW memory effects, source operands, write-index history, and evidence atoms.
- `tools/debugger/reverse_query.py`
  - preserves those pre-state boundary fields in reverse-query history and result evidence.
- `tools/debugger/causal_graph.py` and `tools/debugger/ranking.py`
  - surface hook mechanism and non-mutating-event boundary fields in causal validation evidence and ranked effect-trace evidence.
- `tools/debugger/catalog.py`
  - updates the replay/localization blocker wording to state that RMW pre-state proof now carries the hook mechanism/non-mutating-event boundary.
- `tools/debugger/tests/test_catalog.py`
  - verifies the boundary fields survive from hook-order report ingestion through effect trace, write index, reverse query, causal graph, and ranking.

Validation after patch:

- Focused hook-order/effect/reverse/causal regressions: 4 passed.
- `PYTHONPYCACHEPREFIX=.local\tmp\pycompile_cache python -m py_compile tools\debugger\effect_trace.py tools\debugger\reverse_query.py tools\debugger\causal_graph.py tools\debugger\ranking.py tools\debugger\catalog.py tools\debugger\tests\test_catalog.py`: passed.

Remaining priority:

- This prevents PyBoy hook-order evidence from losing its observation-model boundary, but it does not replace the hook path with a non-mutating CPU/hardware event recorder.
- Full side-effect-complete reverse execution, hardware side-effect event streams, arbitrary event-engine execution, script/graphics/audio/map behavioral mirrors, and subsystem-complete causal proof remain incomplete.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Instruction Trace Planned Target Runtime Boundary

Date: 2026-05-20.

Context:

- Generated-hour content-state and content-fuzz mirrors now require route-declared runtime consumer symbols such as `CheckObjectTime` before they can pass.
- Loaded `unified_debugger_instruction_trace` reports exposed both executed hook hits and planned `functions` targets through the same `symbols` field when compare harvested runtime observations.
- That could let a planned trace target satisfy `required_runtime_symbols` even if the trace only observed the sink writes and never hit the consumer function.

References used:

- Local compare/report contracts in `tools/debugger/mirrors.py`.
- Local generated-hour route contract in `tools/debugger/content_scenarios.py`.

Implemented fix:

- `tools/debugger/mirrors.py`
  - separates runtime observation sink coverage from observed runtime consumer symbols when harvesting loaded runtime-evidence reports.
  - keeps instruction-trace `functions` as additive `planned_function_symbols` / `target_symbols` evidence, not observed runtime symbols.
  - counts only `execution_validation.hit_function_symbols` as instruction-trace `observed_runtime_symbols`.
- `tools/debugger/catalog.py`
  - updates the generation and differential-mirror blocker wording so `CheckObjectTime` proof requires observed instruction hits or explicit runtime observations, not merely planned trace functions.
- `tools/debugger/tests/test_event_runtime_materialization.py`
  - verifies content-fuzz mirrors remain inconclusive when `CheckObjectTime` appears only as a planned instruction-trace function.
  - verifies the same mirror passes when `CheckObjectTime` appears in instruction-trace hit symbols.

Validation after patch:

- Focused content-fuzz runtime-consumer regressions: 3 passed.
- Event-runtime materialization suite: 26 passed.
- Focused audit/catalog regression: 1 passed.
- Full debugger unittest discovery: 525 passed.
- `PYTHONPYCACHEPREFIX=.local\tmp\pycompile_cache python -m py_compile tools\debugger\mirrors.py tools\debugger\catalog.py tools\debugger\tests\test_event_runtime_materialization.py`: passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority:

- This prevents planned instruction-trace targets from promoting generated-hour behavioral proof, but it still does not execute those runtime consumers across arbitrary event-engine states.
- Runtime-verified multi-object occupancy, big-object collision/occupancy proof, full script VM behavior under arbitrary event-engine context, pixel/audio playback mirrors, causal proof, side-effect-complete reverse execution, and the non-mutating hardware event recorder remain incomplete.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Object-Event Occupancy Runtime Boundary

Date: 2026-05-20.

Context:

- Object-event content-state materialization can patch source-order companion object structs and fixed 2x2 big-object state.
- Those patches are still planned WRAM/map-object state until runtime evidence proves the object loader and collision path consumed them.
- Without route-level runtime consumer requirements, a compare mirror could pass from patched object row/struct sink observations while leaving the multi-loaded-object or big-object collision path unobserved.

References used:

- Local engine source: `engine/overworld/player_object.asm:InitializeVisibleSprites` and `CopyObjectStruct`.
- Local engine source: `engine/overworld/npc_movement.asm:IsNPCAtCoord` and `WillObjectIntersectBigObject`.
- Local engine source: `engine/overworld/events.asm:TryObjectEvent`.
- Upstream pret pokegold cross-checks:
  - `https://raw.githubusercontent.com/pret/pokegold/master/engine/overworld/events.asm`
  - `https://raw.githubusercontent.com/pret/pokegold/master/engine/overworld/player_object.asm`
  - `https://raw.githubusercontent.com/pret/pokegold/master/engine/overworld/npc_movement.asm`

Implemented fix:

- `tools/debugger/content_state.py`
  - augments content-state runtime routes after materialization, preserving existing route fields while adding requirements derived from the actual object context.
  - requires `InitializeVisibleSprites` and `CopyObjectStruct` runtime evidence for materialized multi-loaded-object companion occupancy.
  - requires `IsNPCAtCoord` and `WillObjectIntersectBigObject` runtime evidence for materialized large-object collision candidates.
  - rebuilds route proof commands so the required symbols appear in follow-up instruction-trace commands.
- `tools/debugger/content_scenarios.py`
  - attaches the big-object collision runtime symbols to generated large-object content-fuzz preconditions before state materialization.
- `tools/debugger/catalog.py`
  - updates generation and differential-mirror blocker wording so these planned object states cannot be mistaken for runtime occupancy/collision proof.
- `tools/debugger/tests/test_catalog.py`
  - verifies big-object routes carry required collision symbols and proof commands.
  - verifies custom `BIG_OBJECT` content-scenario candidates carry the same runtime requirements.
  - verifies multi-loaded-object content-state routes require the object-loader symbols.

Validation after patch:

- Focused object-event occupancy regressions: 3 passed.
- Adjacent object-event content-state cluster: 12 passed.
- Full debugger unittest discovery: 524 passed.
- `PYTHONPYCACHEPREFIX=.local\tmp\pycompile_cache python -m py_compile tools\debugger\content_scenarios.py tools\debugger\content_state.py tools\debugger\catalog.py tools\debugger\tests\test_catalog.py`: passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority:

- This is a proof-promotion fence and route-upgrade patch; it does not execute the loader/collision traces across arbitrary event-engine states.
- Runtime-verified multi-object occupancy across arbitrary maps, runtime-observed big-object collision across arbitrary maps, full script VM behavior under arbitrary event-engine context, pixel/audio playback mirrors, causal proof, side-effect-complete reverse execution, and the non-mutating hardware event recorder remain incomplete.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Script and Movement Entry Runtime Consumers

Date: 2026-05-20.

Context:

- Script-entry and movement-entry content-state routes already produced trace commands, but the route contract did not mark the dispatcher/engine helpers as required runtime consumer symbols.
- That left a proof-promotion gap: patched `wScriptPos`/movement-pointer WRAM sinks could be observed without proving `RunScriptCommand` or the movement engine consumed the entry state.
- The audit still requires full script VM behavior under arbitrary event-engine context; this patch only prevents patched entry state from being overread as that behavior.

References used:

- Local engine source: `engine/overworld/scripting.asm:ScriptEvents` dispatches to `RunScriptCommand`.
- Local engine source: `engine/overworld/scripting.asm:ApplyMovement`, `home/map.asm:GetMovementData`, and `engine/overworld/map_objects.asm:HandleMovementData`.
- Upstream pret pokecrystal source cross-check for the script dispatcher: `https://github.com/pret/pokecrystal/blob/master/engine/overworld/scripting.asm`
- Upstream pret pokecrystal source cross-check for movement handling: `https://github.com/pret/pokecrystal/blob/master/engine/overworld/map_objects.asm`

Implemented fix:

- `tools/debugger/content_scenarios.py`
  - adds default profile `trace_symbols` and `required_runtime_symbols` for `script_entry` routes.
  - adds default profile `trace_symbols` and `required_runtime_symbols` for `movement_entry` routes.
  - merges profile-required runtime symbols with call-site required symbols while preserving existing route fields.
- `tools/debugger/catalog.py`
  - updates generation and differential-mirror blocker wording to state that script-entry mirrors require `RunScriptCommand` evidence and movement-entry mirrors require `ApplyMovement`/`HandleMovementData` evidence.
- `tools/debugger/tests/test_event_runtime_materialization.py`
  - verifies route helper defaults include required script runtime consumer symbols.
- `tools/debugger/tests/test_catalog.py`
  - verifies materialized script-entry routes require `RunScriptCommand`.
  - verifies materialized movement-entry routes require `ApplyMovement` and `HandleMovementData`.

Validation after patch:

- Focused script/movement route and materialization regressions: 4 passed.
- Adjacent event-runtime/script/movement/catalog regressions: 31 passed.
- Full debugger unittest discovery: 524 passed.
- `PYTHONPYCACHEPREFIX=.local\tmp\pycompile_cache python -m py_compile tools\debugger\content_scenarios.py tools\debugger\catalog.py tools\debugger\tests\test_event_runtime_materialization.py tools\debugger\tests\test_catalog.py`: passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority:

- This prevents script/movement entry state from promoting without required consumer hits, but it still does not implement a full script VM mirror or arbitrary event-engine execution context.
- Pixel/audio playback mirrors, arbitrary map interactions, causal proof, side-effect-complete reverse execution, and the non-mutating hardware event recorder remain incomplete.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Output-Sink Helper Runtime Boundary

Date: 2026-05-20.

Context:

- Audio, asset-loader, and UI output-sink materializations already declare helper `runtime_symbols` and generate trace/dynamic-taint commands.
- `content_output_behavioral_mirror` could still pass from observed output sinks alone when a report declared the selected helper symbols but the runtime evidence did not observe those helpers.
- That blurred "the sink changed" with "the selected drawing/audio/loader helper produced the sink."

References used:

- Local output-sink materialization contracts in `tools/debugger/content_state.py`.
- Local compare proof-status contract in `tools/debugger/mirrors.py`.
- Local effect-trace event contract in `tools/debugger/effect_trace.py`, where `pc_label` identifies the instruction helper frame.

Implemented fix:

- `tools/debugger/mirrors.py`
  - aggregates output materialization helper requirements into additive `required_runtime_symbol_groups`.
  - keeps output-sink mirrors partial/inconclusive when every requested sink is observed but the declared helper symbol group is not observed.
  - exposes `required_runtime_symbol_groups`, `observed_runtime_symbols`, and `missing_runtime_symbol_groups` on output-sink mirror matches.
  - carries strong effect-trace event `pc_label` values into runtime evidence symbols so instruction-backed writes from helpers such as `PlaceString` can satisfy the helper runtime boundary.
- `tools/debugger/catalog.py`
  - updates differential-mirror blocker wording to say audio/asset/UI output-sink mirrors require declared helper runtime-symbol groups before passing.
- `tools/debugger/tests/test_catalog.py`
  - verifies an effect-trace output write from `PlaceString` still passes and exposes the observed helper symbol.
  - verifies a watch-only `wTilemap` output change stays partial when `PlaceString` is missing.

Validation after patch:

- Focused output-sink helper-boundary regressions: 4 passed.
- Full debugger unittest discovery: 524 passed.
- `PYTHONPYCACHEPREFIX=.local\tmp\pycompile_cache python -m py_compile tools\debugger\mirrors.py tools\debugger\catalog.py tools\debugger\tests\test_catalog.py`: passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority:

- This prevents helper-declared output sinks from promoting without helper runtime evidence, but it still does not implement full pixel-accurate UI/graphics behavior or full audio playback/mixer behavior.
- Full script VM behavior under arbitrary event-engine state, arbitrary map interactions, causal proof, side-effect-complete reverse execution, and the non-mutating hardware event recorder remain incomplete.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Hardware Event Stream Case-Proof Boundary

Date: 2026-05-20.

Context:

- The supervisor review correctly framed stock PyBoy hooks as debugger breakpoints, not non-mutating CPU/hardware events.
- The local `hardware-event-stream` placeholder had the right strategic direction, but a future non-mutating recorder with any event could mark the stream-level `hardware_behavior_proven=true` before any Pan Docs case had complete required event coverage.
- That was a UI/report proof-promotion risk: "hardware event observed" and "case-complete hardware behavior proven" need to be visibly separate before a PyBoy fork starts emitting real events.

Primary references used:

- PyBoy public docs for frame-level `tick()` plus hook-based fine control: `https://docs.pyboy.dk/`
- Pan Docs OAM DMA timing and bus restrictions: `https://gbdev.io/pandocs/OAM_DMA_Transfer.html`
- Pan Docs CGB GP/HBlank VRAM DMA timing model: `https://gbdev.io/pandocs/CGB_Registers.html#ff51ff55--hdma1hdma5-vram-dma`
- Pan Docs TIMA overflow A/B-cycle behavior: `https://gbdev.io/pandocs/Timer_Obscure_Behaviour.html`

Implemented fix:

- `tools/debugger/hardware_event_stream.py`
  - separates `proof_grade_event_stream`, `hardware_event_observed`, `hardware_behavior_proven`, and `hardware_proof_status`.
  - sets stream-level `hardware_behavior_proven=true` only after a proof-grade non-mutating stream contains at least one complete Pan Docs case event coverage set.
  - exposes `hardware_proven_case_count`, `hardware_proven_case_ids`, `incomplete_case_event_count`, and `incomplete_case_event_ids`.
  - keeps stock PyBoy output at `hardware_event_observed=false`, `hardware_behavior_proven=false`, `hardware_proof_status=not_proven`.
- `tools/debugger/__main__.py`
  - prints observed-event and case-proof fields separately in `hardware-event-stream` output.
- `tools/debugger/catalog.py`
  - updates the replay/localization blocker wording so the audit names the hardware-event-stream case-proof boundary.
- `tools/debugger/tests/test_catalog.py`
  - verifies missing recorders remain planned-only.
  - verifies incomplete non-mutating event streams are runtime-observed but not hardware-proven.
  - verifies complete OAM DMA timing event coverage still reports case-level proof.

Validation after patch:

- Focused hardware-event-stream and hardware-regression regressions: 6 passed.
- `python -m tools.debugger hardware-event-stream --execute`: passed as a command on stock PyBoy, reported `hardware_event_observed=False`, `hardware_behavior_proven=False`, `hardware_proof_status=not_proven`.
- `python -m tools.debugger hardware-regression-gate --execute`: passed as a command, still intentionally `passed=False`; reported 0/10 cases passing, 10 blocking cases, 4 runtime-observed emulator cases, 0 hardware-proof cases, and 10 static-blocker cases.
- Full debugger unittest discovery: 526 passed.
- `PYTHONPYCACHEPREFIX=.local\tmp\pycompile_cache python -m py_compile tools\debugger\hardware_event_stream.py tools\debugger\__main__.py tools\debugger\catalog.py tools\debugger\tests\test_catalog.py`: passed.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `git diff --check`: passed with unrelated CRLF warnings from pre-existing dirty files outside this debugger slice.

Remaining priority:

- This closes a report/UI overclaim path for future non-mutating event recorder output, but it does not implement the recorder itself.
- TIMA A/B-cycle cases, OAM DMA timing/RAM-access restriction, CGB GP/HBlank VRAM DMA timing, interrupt-entry stack writes, boot-ROM end state, and LCD dot/mode timing remain unproven without exact runtime case evidence.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Hardware Event Stream Recorder Identity Boundary

Date: 2026-05-20.

Context:

- The previous event-stream patch separated observed events from case-complete proof, but `hardware_regression.py` still treated generic evidence-source labels as enough to make a hardware-event-stream report proof-grade.
- For this proof path, the identity boundary needs to be narrower: generic `runtime_hardware_event_observed` labels can describe runtime facts, but Pan Docs case proof from an event stream requires the stream to identify as a non-mutating recorder.

Primary references used:

- PyBoy public docs for `tick()` and hook-based fine control: `https://docs.pyboy.dk/`
- Pan Docs OAM DMA timing and bus restrictions: `https://gbdev.io/pandocs/OAM_DMA_Transfer.html`
- Pan Docs CGB GP/HBlank VRAM DMA timing model: `https://gbdev.io/pandocs/CGB_Registers.html#ff51ff55--hdma1hdma5-vram-dma`
- Pan Docs TIMA overflow A/B-cycle behavior: `https://gbdev.io/pandocs/Timer_Obscure_Behaviour.html`

Implemented fix:

- `tools/debugger/hardware_regression.py`
  - now accepts `unified_debugger_hardware_event_stream` evidence as proof-grade only when the report declares `non_mutating_event_recorder=true`, `recorder_kind=non_mutating_event_recorder`, or `source_kind=non_mutating_event_recorder`.
  - no longer lets generic evidence-source/status labels satisfy the event-stream recorder identity requirement.
- `tools/debugger/catalog.py`
  - updates the replay/localization blocker wording to require proof-grade recorder identity in addition to `hardware_behavior_proven=true` and required event types.
- `tools/debugger/tests/test_catalog.py`
  - verifies a complete interrupt event stream with only generic runtime evidence labels remains runtime-observed, not case proof.

Validation after patch:

- Focused recorder-identity regressions: 5 passed.
- Full debugger unittest discovery: 527 passed.
- `PYTHONPYCACHEPREFIX=.local\tmp\pycompile_cache python -m py_compile tools\debugger\hardware_regression.py tools\debugger\catalog.py tools\debugger\tests\test_catalog.py`: passed.
- `python -m tools.debugger hardware-regression-gate --execute`: passed as a command, still intentionally `passed=False`; reported 0/10 cases passing, 10 blocking cases, 4 runtime-observed emulator cases, 0 hardware-proof cases, and 10 static-blocker cases.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `git diff --check`: passed with unrelated CRLF warnings from pre-existing dirty files outside this debugger slice.

Remaining priority:

- This closes another proof-promotion path for future recorder reports, but it still does not implement the PyBoy fork or non-mutating CPU/DMA/interrupt event recorder.
- The hardware gate remains blocked on exact runtime evidence for TIMA, OAM DMA, CGB VRAM DMA, interrupt entry, boot ROM end state, and LCD dot/mode timing.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Hardware Side-Effect Runtime Label Boundary

Date: 2026-05-20.

Context:

- `effect_trace.py` and `reverse_query.py` still treated generic hardware labels such as `hardware_event_observed` and `emulator_hardware_event` as enough to satisfy the hardware side-effect runtime gate.
- That left a last-writer promotion path: an OAM DMA, CGB VRAM DMA, timer-overflow, interrupt-entry, or LCD-mode-edge write could be marked `instruction_observed` from a generic event label instead of an explicit hardware runtime event source.
- The boundary needs to preserve weak runtime labels for report/UI context while preventing them from becoming proof-grade side-effect evidence.

Primary references used:

- PyBoy public docs for hook behavior and opcode replacement: `https://docs.pyboy.dk/#pyboy.PyBoy.hook_register`
- Pan Docs OAM DMA timing and bus restrictions: `https://gbdev.io/pandocs/OAM_DMA_Transfer.html`
- Pan Docs CGB GP/HBlank VRAM DMA timing model: `https://gbdev.io/pandocs/CGB_Registers.html#ff51ff55--hdma1hdma5-vram-dma`
- Pan Docs TIMA overflow A/B-cycle behavior: `https://gbdev.io/pandocs/Timer_Obscure_Behaviour.html`

Implemented fix:

- `tools/debugger/hardware_evidence.py`
  - adds a shared hardware runtime-event boundary helper.
  - classifies `non_mutating_event_recorder`, `runtime_hardware_event_observed`, and explicit `hardware_runtime_event=true` as side-effect runtime evidence.
  - classifies `hardware_event_observed`, `emulator_hardware_event`, and report-level `hardware_event_observed=true` as generic labels that do not satisfy the gate by themselves.
  - exposes additive `hardware_event_identity`, `hardware_event_labels`, `hardware_runtime_event_source_fields`, `hardware_generic_event_label_present`, and `hardware_event_types`.
- `tools/debugger/effect_trace.py`
  - uses the shared boundary before setting `hardware_runtime_event` and `hardware_proof_gate`.
  - keeps generic labels visible on gated effects and watch hits but downgrades the effect to `planned_only` when no explicit side-effect runtime event is present.
- `tools/debugger/reverse_query.py`
  - uses the same boundary for last-writer hardware gates.
  - exposes the hardware event identity fields in result evidence and evidence atoms so UI/report consumers can distinguish generic labels from explicit runtime side-effect evidence.
- `tools/debugger/tests/test_catalog.py`
  - verifies a generic hardware event label does not satisfy effect-trace hardware gates.
  - verifies reverse-query last-writer proof stays `planned_only` for a generic-labeled OAM DMA write.

Validation after patch:

- Focused hardware-label boundary regressions: 2 passed.
- Adjacent hardware-regression/event-stream regressions: 6 passed.
- Full debugger unittest discovery: 529 passed.

Remaining priority:

- This closes a proof-promotion leak for generic hardware event labels, but it still does not create the non-mutating PyBoy recorder or prove hardware behavior for DMA, timer, interrupt, LCD, or boot-ROM cases.
- The next audit blocker remains the same strategic one: execute the hook-order micro-ROM matrix and/or add a proof-grade recorder plus Pan Docs regressions before allowing side-effect-complete reverse execution claims.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Dedicated Hardware Case Proof Boundary

Date: 2026-05-20.

Context:

- `hardware_regression.py` already required hardware-event-stream evidence to identify as a proof-grade non-mutating recorder before case proof.
- Dedicated hardware-regression case rows still had a weaker boundary: a row with `passed=true`, required event types, and generic hardware evidence labels such as `hardware_event_observed` or `runtime_hardware_event_observed` could satisfy `explicit_case_item_proof()` without declaring `hardware_behavior_proven=true`.
- That could blur "a hardware event was observed" with "this exact Pan Docs case has been proven."

Primary references used:

- Pan Docs OAM DMA timing and bus restrictions: `https://gbdev.io/pandocs/OAM_DMA_Transfer.html`
- Pan Docs CGB GP/HBlank VRAM DMA timing model: `https://gbdev.io/pandocs/CGB_Registers.html#ff51ff55--hdma1hdma5-vram-dma`
- Pan Docs TIMA overflow A/B-cycle behavior: `https://gbdev.io/pandocs/Timer_Obscure_Behaviour.html`
- PyBoy hook docs showing opcode replacement rather than non-mutating event capture: `https://docs.pyboy.dk/#pyboy.PyBoy.hook_register`

Implemented fix:

- `tools/debugger/hardware_regression.py`
  - now accepts dedicated case proof only when the case item explicitly declares `hardware_behavior_proven=true` and contains all required event types.
  - no longer treats `hardware_event_observed`, `proof_status`, `evidence_source`, or `evidence_status` labels as equivalent to case-level hardware proof.
- `tools/debugger/tests/test_catalog.py`
  - adds a dedicated-case regression where a row declares `passed=true`, includes complete interrupt event types, and carries generic runtime hardware labels, but lacks `hardware_behavior_proven=true`; the gate keeps it `planned_only`.

Validation after patch:

- Focused dedicated hardware case regressions: 5 passed.

Remaining priority:

- Dedicated case rows are now proof-fenced, but no TIMA, OAM DMA, CGB VRAM DMA, interrupt-entry, boot-ROM, or LCD case is actually proven on stock PyBoy.
- The hardware-regression gate remains intentionally failing until exact case evidence or proof-grade non-mutating recorder evidence lands.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Dynamic Taint Hardware Side-Effect Boundary

Date: 2026-05-20.

Context:

- Reverse-query and effect-trace hardware gates had been tightened, but dynamic-taint effect-report attribution still derived `proof_status` from address precision and `effect_proof_status` only.
- An imported effect trace could therefore present a hardware-side-effect write with `proof_status=instruction_observed`, a generic `hardware_event_observed` label, and no explicit runtime side-effect event, and dynamic taint would preserve the attribution as instruction-observed.
- That is a downstream proof-promotion gap for DMA, timer-overflow, LCD-mode-edge, interrupt-entry, and CGB VRAM DMA effects.

Primary references used:

- PyBoy public docs for hook behavior and opcode replacement: `https://docs.pyboy.dk/#pyboy.PyBoy.hook_register`
- Pan Docs OAM DMA timing and bus restrictions: `https://gbdev.io/pandocs/OAM_DMA_Transfer.html`
- Pan Docs CGB GP/HBlank VRAM DMA timing model: `https://gbdev.io/pandocs/CGB_Registers.html#ff51ff55--hdma1hdma5-vram-dma`
- Pan Docs TIMA overflow A/B-cycle behavior: `https://gbdev.io/pandocs/Timer_Obscure_Behaviour.html`

Implemented fix:

- `tools/debugger/dynamic_taint.py`
  - uses the shared hardware runtime-event boundary for effect-report sink matches.
  - treats hardware-required models/kinds as `planned_only` unless an explicit runtime hardware event is present.
  - carries additive `hardware_event_required`, `hardware_runtime_event`, `hardware_event_identity`, `hardware_event_labels`, and `hardware_generic_event_label_present` fields through dynamic-taint match/evidence records.
  - keeps generic labels such as `hardware_event_observed` visible in evidence while preventing them from promoting dynamic write attribution.
- `tools/debugger/tests/test_catalog.py`
  - adds a regression where an OAM DMA write with `proof_status=instruction_observed` and only a generic hardware event label remains `planned_only` in dynamic-taint attribution.

Validation after patch:

- Focused dynamic-taint hardware-boundary regression: 2 passed.
- Adjacent reverse-query/causal/dynamic bank+hardware boundary regressions: 6 passed.

Remaining priority:

- This prevents one more downstream proof promotion path, but it does not provide a side-effect-complete reverse execution engine or proof-grade non-mutating hardware recorder.
- Dynamic-taint still depends on the supplied trace/effect-report window; writers outside that window, unmodeled CPU effects, and unproven hardware side effects remain blockers.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Hardware Regression Effect-Trace Runtime Boundary

Date: 2026-05-20.

Context:

- `hardware_regression.py` classified effect-trace entries as `runtime_hardware_event` when they carried generic labels such as `hardware_event_observed` or `emulator_hardware_event`.
- That did not mark a Pan Docs case as proven, but it still blurred modeled effect-trace evidence into observed hardware-runtime facts for DMA/timer/interrupt/LCD cases.
- The hardware-regression report needs the same boundary used by effect trace, reverse query, and dynamic taint: generic labels may remain visible, but they must not become observed runtime hardware events without an explicit runtime flag or proof-grade recorder identity.

Primary references used:

- PyBoy public docs for hook behavior and opcode replacement: `https://docs.pyboy.dk/#pyboy.PyBoy.hook_register`
- Pan Docs OAM DMA timing and bus restrictions: `https://gbdev.io/pandocs/OAM_DMA_Transfer.html`
- Pan Docs CGB GP/HBlank VRAM DMA timing model: `https://gbdev.io/pandocs/CGB_Registers.html#ff51ff55--hdma1hdma5-vram-dma`
- Pan Docs TIMA overflow A/B-cycle behavior: `https://gbdev.io/pandocs/Timer_Obscure_Behaviour.html`

Implemented fix:

- `tools/debugger/hardware_regression.py`
  - now uses the shared `hardware_runtime_event_boundary()` helper when classifying effect-trace case evidence.
  - no longer treats `hardware_event_observed`, `emulator_hardware_event`, or `hardware_proof_gate=explicit_runtime_event_present` as sufficient runtime hardware-event evidence by themselves.
  - still accepts explicit `hardware_runtime_event=true`, `runtime_hardware_event_observed`, or `non_mutating_event_recorder` evidence as runtime-observed facts that remain below case proof until all Pan Docs case requirements are satisfied.
- `tools/debugger/tests/test_catalog.py`
  - adds a regression where an OAM DMA effect trace with only a generic `hardware_event_observed` label stays `modeled_effect_trace`, carries `proof_scope=modeled_not_hardware_proof`, and does not create a `runtime_hardware_event` fact.

Validation after patch:

- Focused hardware-regression runtime-boundary regressions: 3 passed.
- Full debugger unittest discovery: 532 passed.
- `PYTHONPYCACHEPREFIX=.local\tmp\pycompile_cache python -m py_compile tools\debugger\hardware_regression.py tools\debugger\tests\test_catalog.py`: passed.
- `python -m tools.debugger hardware-regression-gate --execute`: passed as a command, still intentionally `passed=False`; reported 0/10 cases passing, 10 blocking cases, 4 runtime-observed emulator cases, 0 hardware-proof cases, and 10 static-blocker cases.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority:

- This tightens report classification, but it does not implement the non-mutating PyBoy recorder or prove the TIMA, OAM DMA, CGB VRAM DMA, interrupt-entry, boot-ROM, or LCD cases.
- The hardware-regression gate remains intentionally blocked until exact runtime side-effect events or dedicated hardware case proofs exist.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Hardware-Gated Watch-Hit UI Boundary

Date: 2026-05-20.

Context:

- Hardware-gated effect writes were downgraded at the effect level, but exact watch hits over those writes still received `target_match_proof_status=instruction_observed`.
- That let ranking, causal graph, and visualization surfaces make a DMA/timer/interrupt/LCD watched write look stronger than the underlying hardware side-effect proof.
- Watch-hit proof must inherit the weakest relevant boundary: exact address matching is not enough when the matched effect itself is `planned_only` because a hardware side effect lacks explicit runtime event evidence.

Primary references used:

- PyBoy public docs for hook behavior and opcode replacement: `https://docs.pyboy.dk/#pyboy.PyBoy.hook_register`
- Pan Docs OAM DMA timing and bus restrictions: `https://gbdev.io/pandocs/OAM_DMA_Transfer.html`
- Pan Docs CGB GP/HBlank VRAM DMA timing model: `https://gbdev.io/pandocs/CGB_Registers.html#ff51ff55--hdma1hdma5-vram-dma`
- Pan Docs TIMA overflow A/B-cycle behavior: `https://gbdev.io/pandocs/Timer_Obscure_Behaviour.html`

Implemented fix:

- `tools/debugger/effect_trace.py`
  - now sets watch-hit `target_match_proof_status=planned_only` when the matched effect is `planned_only`, requires a hardware runtime event that is absent, or carries `hardware_proof_gate=explicit_runtime_event_missing`.
  - carries the effect downgrade reason into the watch hit so the UI can explain why an exact watch address still is not proof-grade.
  - adds `effect_proof_status_counts`, `planned_only_effect_count`, `instruction_observed_effect_count`, `hardware_gated_effect_count`, and `hardware_runtime_event_effect_count` so report consumers can see the downgraded effect mix without inferring it from the global report proof label.
- `tools/debugger/ranking.py`
  - excludes planned-only watch writes from the "verified watched write" count.
  - keeps the `effect_trace_observed` finding at `planned_only` when all write hits are hardware-gated or bank-unverified, and adds `planned_only_watch_writes` plus hardware-gated effect-count evidence.
- `tools/debugger/causal_graph.py` and `tools/debugger/visualization.py`
  - make watch-hit nodes, edges, and timeline entries inherit `planned_only` from hardware-gated effect proof.
  - expose `effect_proof_status`, `target_match_proof_status`, `hardware_proof_gate`, and downgrade reason in watch-hit visualization details.
- `tools/debugger/__main__.py`
  - prints effect proof-status counts and hardware-gated/runtime-event effect totals in the `effect-trace` CLI summary.
- `tools/debugger/tests/test_catalog.py`
  - adds a regression where an FF46-triggered OAM DMA watch on `$FE00` stays planned-only across effect trace, ranking, causal graph, and visualization even though the watch address matches exactly, while the report exposes hardware-gated effect counts.

Validation after patch:

- Focused watch-hit proof-boundary regressions: 3 passed.
- Full debugger unittest discovery: 533 passed.
- `PYTHONPYCACHEPREFIX=.local\tmp\pycompile_cache python -m py_compile tools\debugger\effect_trace.py tools\debugger\ranking.py tools\debugger\causal_graph.py tools\debugger\visualization.py tools\debugger\__main__.py tools\debugger\tests\test_catalog.py`: passed.
- `python -m tools.debugger hardware-regression-gate --execute`: passed as a command, still intentionally `passed=False`; reported 0/10 cases passing, 10 blocking cases, 4 runtime-observed emulator cases, 0 hardware-proof cases, and 10 static-blocker cases.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority:

- This closes a UI/report promotion path for watched hardware side effects, but the underlying side-effect-complete reverse execution remains missing.
- The non-mutating recorder and dedicated hardware regressions are still required before DMA, timer, interrupt, LCD, or boot-ROM paths can become hardware proof.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Output Mirror Hardware-Gated Watch-Hit Gap Reason

Date: 2026-05-20.

Context:

- Content output-sink mirrors already rejected weak effect-trace evidence when a write/watch path was planned-only.
- The weak runtime-evidence explanation for watch-hit paths was still too generic: all weak watch hits were described as bank-unverified even when the actual blocker was a hardware-gated DMA/timer/interrupt/LCD side effect with no explicit runtime hardware-event evidence.
- This did not promote the mirror to passed, but it weakened the report boundary by pointing future agents at the wrong cause.

Primary references used:

- PyBoy public docs for hook behavior and opcode replacement: `https://docs.pyboy.dk/#pyboy.PyBoy.hook_register`
- Pan Docs OAM DMA timing and bus restrictions: `https://gbdev.io/pandocs/OAM_DMA_Transfer.html`

Implemented fix:

- `tools/debugger/mirrors.py`
  - now distinguishes hardware-gated weak effect-trace watch hits from bank-unverified weak watch hits when building output-sink mirror runtime-evidence gaps.
  - preserves planned-only mirror status; this is an explanatory/report-boundary patch, not a proof promotion.
- `tools/debugger/tests/test_catalog.py`
  - keeps the existing hardware-gated concrete-write output-sink mirror regression.
  - adds a separate hardware-gated weak watch-hit fixture and verifies the mirror gap names the missing explicit runtime hardware-event evidence.

Validation after patch:

- Focused output-sink mirror regressions: 2 passed.
- Full debugger unittest discovery: 534 passed.
- `PYTHONPYCACHEPREFIX=.local\tmp\pycompile_cache python -m py_compile tools\debugger\mirrors.py tools\debugger\tests\test_catalog.py`: passed.
- `python -m tools.debugger hardware-regression-gate --execute`: passed as a command, still intentionally `passed=False`; reported 0/10 cases passing, 10 blocking cases, 4 runtime-observed emulator cases, 0 hardware-proof cases, and 10 static-blocker cases.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority:

- This improves blocker routing for output-sink mirrors, but it does not produce the missing runtime hardware events.
- Full script/graphics/audio/map behavioral mirrors and side-effect-complete reverse execution remain incomplete.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Effect-Trace Visualization Report Proof Boundary

Date: 2026-05-20.

Context:

- Effect-trace item, watch-hit, ranking, causal graph, and timeline surfaces had been fenced for hardware-gated DMA/timer/interrupt/LCD effects.
- The visualization graph's effect-trace report node still used the report-level `proof_status` directly, so a report with observed instruction callbacks but only planned hardware-side-effect effects could appear as `instruction_observed` at the report node.
- That blurred PyBoy hook observation into side-effect-complete proof, which is unsafe because PyBoy's public hook path is breakpoint/debugger-oriented and Pan Docs require explicit DMA/HDMA timing and bus-effect handling for hardware proof.

Primary references used:

- PyBoy public docs for hook/breakpoint behavior: `https://docs.pyboy.dk/#pyboy.PyBoy.hook_register`
- Pan Docs OAM DMA timing and bus restrictions: `https://gbdev.io/pandocs/OAM_DMA_Transfer.html`
- Pan Docs CGB GP/HBlank VRAM DMA behavior and timing: `https://gbdev.io/pandocs/CGB_Registers.html#ff55--hdma5-cgb-mode-only-vram-dma-lengthmodestart`

Implemented fix:

- `tools/debugger/visualization.py`
  - derives the effect-trace graph report-node `proof_status` from the weakest contained effect proof when effect proof counts are present.
  - preserves the stronger observed instruction context as a mixed `proof_summary`/`proof_badge` instead of replacing the side-effect boundary with a global observed label.
  - exposes additive report-node counts for effect proof statuses, hardware-gated effects, runtime hardware-event effects, hardware side effects, DMA copy writes, and interrupt entries.
  - honors explicit graph-node `proof_summary` inputs so imported causal graph nodes and effect-trace report nodes can show mixed proof ranges.
- `tools/debugger/tests/test_catalog.py`
  - extends the hardware-gated OAM DMA watch-hit regression to assert the visualization graph report node remains `planned_only`, carries a mixed `planned_only -> instruction_observed` proof range, and exposes the hardware-gated effect counts.

Validation after patch:

- Focused hardware-gated watch-hit UI/report regression: 1 passed.
- Full debugger unittest discovery: 534 passed.
- `PYTHONPYCACHEPREFIX=.local\tmp\pycompile_cache python -m py_compile tools\debugger\visualization.py tools\debugger\tests\test_catalog.py`: passed.
- `python -m tools.debugger hardware-regression-gate --execute`: passed as a command, still intentionally `passed=False`; reported 0/10 cases passing, 10 blocking cases, 4 runtime-observed emulator cases, 0 hardware-proof cases, and 10 static-blocker cases.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.
- `git diff --check`: passed with unrelated pre-existing CRLF warnings in Boss AI trace/generated/doc fixture files.

Remaining priority:

- This closes another UI/report promotion path, but it does not create the missing non-mutating event recorder or hardware regressions.
- The audit still requires side-effect-complete reverse execution, subsystem-boundary causal proof, arbitrary runtime/event generation, and script/graphics/audio/map behavioral mirrors before `ready=True` is valid.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.

## Implementation Note - Trace-Index Evidence-Atom Proof Boundary

Date: 2026-05-20.

Context:

- Trace-index causal paths and reverse attributions can carry item-level `evidence_atoms` whose proof is weaker than the enclosing report's global `proof_status`.
- Ranking and impact already preserved explicit item `proof_status`, but if an item omitted the flat field while carrying planned-only evidence atoms, the surfaces fell back to the report-level proof.
- Visualization did the same for reverse-attribution timeline entries. That could make compact/static trace-index facts appear instruction-observed after aggregation.

Implemented fix:

- `tools/debugger/ranking.py`
  - derives trace-index item proof from the weakest supplied evidence-atom proof before considering report-level proof.
  - exposes a shared `weakest_proof_status()` helper for downstream consumers.
- `tools/debugger/impact.py`
  - applies the same evidence-atom-first trace-index item proof rule.
- `tools/debugger/visualization.py`
  - uses the ranking helper for trace-index reverse-attribution timeline proof instead of directly falling back to the report proof.
- `tools/debugger/tests/test_catalog.py`
  - updates the trace-index planned-proof regression so the report is `instruction_observed`, the items omit flat `proof_status`, and planned-only evidence atoms still keep ranked, impact, and visualization outputs planned-only.

Validation after patch:

- Focused trace-index proof-boundary regression: 1 passed.
- Full debugger unittest discovery: 534 passed.
- `PYTHONPYCACHEPREFIX=.local\tmp\pycompile_cache python -m py_compile tools\debugger\ranking.py tools\debugger\impact.py tools\debugger\visualization.py tools\debugger\tests\test_catalog.py`: passed.
- `python -m tools.debugger hardware-regression-gate --execute`: passed as a command, still intentionally `passed=False`; reported 0/10 cases passing, 10 blocking cases, 4 runtime-observed emulator cases, 0 hardware-proof cases, and 10 static-blocker cases.
- `python -m tools.debugger audit`: passed as a command, still `ready=False`, 7 complete buckets, 4 partial buckets, 4 blocking gaps.

Remaining priority:

- This prevents one more aggregation-layer proof promotion, but it does not add new runtime evidence.
- Trace-index compact/static facts remain useful routing evidence, not replacements for dynamic subsystem proof.
- The whole-ROM proof-substrate goal remains incomplete and `ready=False`.
