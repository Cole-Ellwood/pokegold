# Verification Matrix

Use this file to pick checks by change kind. More checks are allowed, but a
future session should be able to see the floor without re-deriving it.

## Minimum Checks By Change Kind

| Change kind | Minimum checks | Build expectation | Extra notes |
| --- | --- | --- | --- |
| Docs-only routing, roadmap, handoff, or organization | `python tools\audit\check_docs_navigation.py`; `git diff --check` | No ROM build required unless docs claim current build facts changed. | Do not touch gameplay source in this mode. |
| Generated dev index refresh | `python scripts\generate_dev_index.py --rom pokegold`; `python tools\audit\check_docs_navigation.py`; `git diff --check` | Build first if linker outputs changed. | Never hand-edit `docs/generated/dev_index.md`. |
| Pokemon stats, types, evolutions, learnsets | `python scripts\generate_balance_audit.py`; `python tools\audit\check_release_smoke.py`; `python tools\audit\check_docs_navigation.py`; `git diff --check` | Build both ROMs. | Check evolution timing and trainer usage before final confidence. |
| Trainer parties, boss held items, AI tiers | `python tools\audit\check_ai_tiers.py`; `python tools\audit\check_boss_items_present.py`; `python tools\audit\check_boss_moves_complete.py`; release smoke; docs navigation; `git diff --check` | Build both ROMs. | Keep parties separate from species learnsets. |
| Boss AI logic | Boss no-cheat, gating, trace invariants, memory budget, live-capture ledger, release smoke, docs navigation, `git diff --check` | Build both ROMs; build trace ROM if trace behavior changed. | Automated audits are not gameplay proof. Record live proof gaps. |
| Boss AI live trace artifact | `python tools\trace\boss_ai_trace_capture.py --symbols-only`; `python tools\trace\boss_ai_trace_state_probe.py --save-state path\to\candidate.state --expect-morty --strict`; `python tools\trace\boss_ai_trace_batch.py`; `python tools\audit\check_boss_ai_live_capture_ledger.py`; docs navigation; `git diff --check` | Trace ROM must match the state/artifact being claimed. | Old `.local/` RAM is not proof unless tied to the current trace ROM and the strict probe accepts the boss context; the batch runner refuses invalid Morty states using the manifest preflight guard. |
| Battle mechanics or move behavior | `python tools\audit\check_battle_math_safety.py`; release smoke; docs navigation; `git diff --check` | Build both ROMs. | Audit all downstream consumers of category, damage, stat choice, and reflected damage. |
| Map scripts, events, specials, QoL scripts | Release smoke; docs navigation; `git diff --check` | Build both ROMs. | Manual playtest gap should be named if not exercised in emulator. |
| Items and held-item behavior | Release smoke; battle math safety if damage/choice behavior changed; docs navigation; `git diff --check` | Build both ROMs. | Keep item names, descriptions, attributes, pockets, marts, and battle effects consistent. |
| Graphics or audio | Docs navigation; `git diff --check` | Build both ROMs. | Include a visual/audio manual-check gap if not inspected in-game. |

## Build Command

Prefer the documented WSL route on this Windows checkout:

```powershell
bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'
```

If this command reports both targets are up to date, record that exact fact. Do
not inflate it into emulator validation.

## Report Standard

Every stopping point should name:

- files changed by this session;
- checks run and whether they passed;
- build status if source changed;
- generated files refreshed or deliberately untouched;
- remaining gameplay/manual proof gaps.
