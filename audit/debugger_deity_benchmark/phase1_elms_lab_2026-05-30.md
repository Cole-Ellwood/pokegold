# Debugger Deity-Mode Benchmark Baseline

- Generated: 2026-05-30T18:50:53Z
- Questions path: audit/debugger_deity_benchmark/questions.jsonl
- Questions: 14
- Passed: 7
- Failed: 7
- Pass rate: 0.500
- Components built: 1/7
- deity_ready: False
- deity_gap_actions: 13

A question passes only when its `driver: auto` proof command runs to
exit 0 AND emits its evidence marker — i.e. the debugger self-drove the
proof with no hand-supplied state/trace/scenario. The godmode triad
(audit 11/11, godmode benchmark 29/29, and the all-green selftest gate)
is the frozen floor and is not scored here.

## Capability components

| component | phase | built |
| --- | --- | --- |
| auto_navigation | 1 | yes |
| auto_taint | 2 | no |
| audio_replay | 3 | no |
| graphics_replay | 3 | no |
| script_vm_replay | 3 | no |
| sm83_model_parity | 4 | no |
| live_view | 5 | no |

## Question results

| id | phase | pass | reason |
| --- | --- | --- | --- |
| deity_nav_new_game_bedroom | 1 | PASS | self-drove to a proof emitting the evidence marker |
| deity_nav_morty_turn3 | 1 | FAIL | proof command exited 1 (capability not built / could not self-drive) |
| deity_nav_first_wild_route29 | 1 | PASS | self-drove to a proof emitting the evidence marker |
| deity_nav_route46_search_waypoint | 1 | PASS | self-drove to a proof emitting the evidence marker |
| deity_nav_route30_search_waypoint | 1 | PASS | self-drove to a proof emitting the evidence marker |
| deity_nav_cherrygrove_rival_trainer_battle | 1 | PASS | self-drove to a proof emitting the evidence marker |
| deity_nav_cherrygrove_post_rival_battle | 1 | PASS | self-drove to a proof emitting the evidence marker |
| deity_nav_elms_lab_post_officer | 1 | PASS | self-drove to a proof emitting the evidence marker |
| deity_taint_curdamage_falkner | 2 | FAIL | proof command exited 2 (capability not built / could not self-drive) |
| deity_taint_arbitrary_wram_byte | 2 | FAIL | proof command exited 2 (capability not built / could not self-drive) |
| deity_replay_audio_cry | 3 | FAIL | proof command exited 2 (capability not built / could not self-drive) |
| deity_replay_graphics_ecruteak_gym | 3 | FAIL | proof command exited 2 (capability not built / could not self-drive) |
| deity_replay_script_vm_elm | 3 | FAIL | proof command exited 2 (capability not built / could not self-drive) |
| deity_live_view_falkner_turn | 5 | FAIL | proof command exited 2 (capability not built / could not self-drive) |
