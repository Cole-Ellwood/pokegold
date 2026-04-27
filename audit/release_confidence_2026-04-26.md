# Release Confidence Capsule - 2026-04-26

Lane: release confidence.

Purpose: prove the current dirty checkout still has the core source, AI,
navigation, and build guarantees expected by the helper docs. This is not manual
playtest proof.

2026-04-27 supersession note: later Boss AI trace work refreshed the trace ROM
basis, regenerated real-trainer states, and completed the `shared_switch_loop`
fixture. Treat `audit/boss_ai_trace/live_capture_ledger.md` as current proof
truth.

## Scope

Covered dirty gameplay surfaces visible at session start:

- Boss AI source and trace tooling.
- Battle math / late-gen held-item hooks.
- QoL map/script/item-text surfaces.
- Helper docs and navigation checks.
- Normal Gold/Silver assembly status.

No source fixes were required during this pass.

## Commands And Results

All commands were run from `C:\Users\lolno\Downloads\pokemon gold hack` on
2026-04-26.

| Command | Result |
| --- | --- |
| `python tools\audit\check_release_smoke.py` | PASS: all release smoke checks passed, including TM Tutor item-state restore and QoL communication/script checks. |
| `python tools\audit\check_ai_tiers.py` | PASS: 35 required boss entries covered; tier counts `EARLY=9`, `MID=9`, `LATE=17`; 17 adaptive lead entries covered. |
| `python tools\audit\check_boss_items_present.py` | PASS: `OK|entries=35|mons=163|items_present=true`; only documented Rival1 early itemless allowlist entries remain. |
| `python tools\audit\check_boss_moves_complete.py` | PASS: `OK|entries=35|mons=163|no_no_move_tokens=true`. |
| `python tools\audit\check_battle_math_safety.py` | PASS: scanned 188 ASM files; effective-category helpers and late-gen item stat/damage hooks are guarded. |
| `python tools\audit\check_boss_ai_no_cheat.py` | PASS: scanned Boss AI move/item paths with no hidden-information audit failure. |
| `python tools\audit\check_boss_ai_gating.py` | PASS: guarded Boss AI entrypoints intact. |
| `python tools\audit\check_boss_ai_trace_invariants.py` | PASS: trace invariants intact, including cursor preservation, public fail gates, switch-loop pressure, and known item/passive tactical reasoning. |
| `python tools\audit\check_boss_ai_memory_budget.py` | PASS: Enemy Trainers bank `normal=0e:4000-7dd1`, `trace=0e:4000-7ee3`; Boss AI WRAM `normal_free=65`, `trace_free=46`. |
| `python tools\audit\check_boss_ai_live_capture_ledger.py` | PASS at snapshot time: Morty and Jasmine were `FINISHED`. Superseded on 2026-04-27: all current manifest rows are now `FINISHED`, including `shared_switch_loop`. |
| `python tools\audit\check_docs_navigation.py` | PASS: all doc navigation checks passed; generated dev index and balance audit match current outputs/data. |
| `bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'` | PASS: `pokegold.gbc` and `pokesilver.gbc` reported up to date. |

## Evidence Type

- Source/audit evidence: automated checks above.
- Build evidence: WSL make reported both normal ROM targets up to date.
- Live trace evidence: snapshot recognized Morty and Jasmine proofs; current
  ledger now recognizes all manifest rows, including `shared_switch_loop`.
- Manual emulator evidence: not performed in this pass.

## Remaining Uncertainty

- This snapshot did not prove boss feel beyond the then-captured Morty and
  Jasmine live decisions. Later trace work completed the current manifest
  proof floor, but manual boss-feel playtesting remains separate.
- QoL changes still need manual emulator feel checks where the roadmap names
  them, especially Repel renewal accept/decline flow.
- No checkpoint, staging, or commit was requested.
