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
