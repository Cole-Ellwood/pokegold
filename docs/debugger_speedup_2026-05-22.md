# Debugger Speedup Report - 2026-05-22

This report emits per-scenario ratios only. Baseline times are historical estimates cited by each scenario's EvidenceAtoms; masterpiece times are local command replays measured by this harness.

- Ready: true
- Scenarios measured: 6 / 6
- Minimum required: 6

## Per-Scenario Ratios

| Scenario | Bug class | Baseline estimate (s) | Masterpiece replay (s) | Ratio | Evidence | Replay commands |
| --- | --- | ---: | ---: | ---: | --- | --- |
| ag_nn_5x_damage_44ca3b29 | ag_nn_register_clobber | 3600 | 0.839 | 4290.82x | speedup.baseline_time_estimate, speedup.masterpiece_replay, speedup.ratio | `python -m tools.debugger clobbers --symbol GetUserItem ; python -m tools.damage_debugger.clobber_smoke` |
| wild_floor_no_op_13a6e3a3 | farcall_a_clobber | 1800 | 1.328 | 1355.42x | speedup.baseline_time_estimate, speedup.masterpiece_replay, speedup.ratio | `python tools/audit/check_farcall_a_clobber.py` |
| rival_1_softlock_farcall_hl | farcall_hl_clobber | 7200 | 1.105 | 6515.84x | speedup.baseline_time_estimate, speedup.masterpiece_replay, speedup.ratio | `python tools/audit/check_farcall_hl_clobber.py` |
| vram_tile_jumble_may_2026 | vram_pyboy_vba_divergence | 5400 | 0.279 | 19354.84x | speedup.baseline_time_estimate, speedup.masterpiece_replay, speedup.ratio | `python -m tools.debugger vram-snapshot --self-test ; python -m tools.debugger vram-diff --self-test` |
| type_immunity_softlock_f2e18554 | cross_bank_call | 5400 | 0.237 | 22784.81x | speedup.baseline_time_estimate, speedup.masterpiece_replay, speedup.ratio | `python tools/audit/check_cross_bank_call.py` |
| value_came_from_where_d141_clobber | value_came_from_where | 2400 | 0.141 | 17021.28x | speedup.baseline_time_estimate, speedup.masterpiece_replay, speedup.ratio | `python -m tools.debugger selftest --component when_wrote` |

## Notes

- A ratio is omitted when any masterpiece replay command fails or when required EvidenceAtoms are missing.
- The harness does not emit an aggregate speedup claim.
