# TD-005 Pattern 3 — Site Enumeration

**Generated:** 2026-05-03
**Source:** `claude/trusting-kare-692dd4` session, classifier in
`.local/classify_pattern3.py` (worktree-only, not committed).
**Reason:** `FIX_PROPOSALS.md` TD-005 "Updated 2026-05-02" requires
enumeration to file:line before any conversion work. `META_AUDIT.md`
TD-A06 flagged the original "100+ instances project-wide" claim as
unverifiable.

## Summary

| Class | Count | Eligible for `_GetSidedAddr`? |
| --- | ---: | --- |
| **A — side-branch** (matched player+enemy sided pointer load on same reg16) | **66** | yes |
| **B — control-flow** (turn flag read for branching, no sided pointer) | 138 | no |
| **C — other** (turn flag used as data: `xor 1`, `cp`, etc.) | 30 | no |
| **Total** `ldh a, [hBattleTurn]` reads | 234 | — |

Class A is what Pattern 3 conversion targets. The 66 is below the
report's "100+" claim but well above the "speculative until measured"
bar — conversion is worthwhile in principle.

## Per-file Class A breakdown

| File | Class A sites | Bank | Notes |
| --- | ---: | --- | --- |
| `engine/battle/effect_commands.asm` | 27 | ROMX 0d | **canary bank, 6 free** — biggest concentrated win |
| `engine/battle/type_passive_damage_mods.asm` | 10 | ROMX 0e | 568 free post-TD-005 P1 |
| `engine/battle/core.asm` | 6 | ROMX 0f | 0f roomy |
| `engine/battle/move_effects/future_sight.asm` | 3 | varies | move_effects/* are small files |
| `engine/battle/move_effects/bide.asm` | 3 | varies | |
| `engine/battle/move_effects/substitute.asm` | 2 | varies | |
| `engine/battle/move_effects/rollout.asm` | 2 | varies | |
| `engine/battle/move_effects/fury_cutter.asm` | 2 | varies | |
| `engine/battle/used_move_text.asm` | 1 | ROMX 0d | canary; same bank as effect_commands |
| `engine/battle/move_effects/spikes.asm` | 1 | varies | |
| `engine/battle/move_effects/safeguard.asm` | 1 | varies | |
| `engine/battle/move_effects/rapid_spin.asm` | 1 | varies | |
| `engine/battle/move_effects/pursuit.asm` | 1 | varies | |
| `engine/battle/move_effects/psych_up.asm` | 1 | varies | |
| `engine/battle/move_effects/protect.asm` | 1 | varies | |
| `engine/battle/move_effects/encore.asm` | 1 | varies | |
| `engine/battle/move_effects/disable.asm` | 1 | varies | |
| `engine/battle/move_effects/curse.asm` | 1 | varies | |
| `engine/battle/late_gen_held_items.asm` | 1 | ROMX 0e | |

The high-leverage observation: 28 of the 66 sites are in the canary
bank (ROMX 0x0d, currently 6 bytes free). At ~5 bytes per site,
converting just those 28 could free ~140 bytes in 0x0d — meaningful
relief for the new tight bank from `TECH_DEBT_REPORT_ADDENDUM.md`
2026-05-03.

## Class A full list (file:line, register)

```
engine/battle/core.asm:381	reg=hl
engine/battle/core.asm:1087	reg=de
engine/battle/core.asm:1209	reg=hl
engine/battle/core.asm:1278	reg=hl
engine/battle/core.asm:1534	reg=hl
engine/battle/core.asm:3981	reg=hl
engine/battle/effect_commands.asm:963	reg=de
engine/battle/effect_commands.asm:1918	reg=hl
engine/battle/effect_commands.asm:2016	reg=de
engine/battle/effect_commands.asm:2245	reg=de
engine/battle/effect_commands.asm:2325	reg=hl
engine/battle/effect_commands.asm:2452	reg=de
engine/battle/effect_commands.asm:3397	reg=de
engine/battle/effect_commands.asm:3673	reg=de
engine/battle/effect_commands.asm:3915	reg=hl
engine/battle/effect_commands.asm:4024	reg=hl
engine/battle/effect_commands.asm:4061	reg=de
engine/battle/effect_commands.asm:4121	reg=bc
engine/battle/effect_commands.asm:4207	reg=hl
engine/battle/effect_commands.asm:4280	reg=de
engine/battle/effect_commands.asm:4539	reg=hl
engine/battle/effect_commands.asm:4570	reg=de
engine/battle/effect_commands.asm:4766	reg=de
engine/battle/effect_commands.asm:4807	reg=de
engine/battle/effect_commands.asm:5083	reg=de
engine/battle/effect_commands.asm:5300	reg=bc
engine/battle/effect_commands.asm:5491	reg=hl
engine/battle/effect_commands.asm:5657	reg=bc
engine/battle/effect_commands.asm:6024	reg=hl
engine/battle/effect_commands.asm:6145	reg=hl
engine/battle/effect_commands.asm:6251	reg=hl
engine/battle/effect_commands.asm:6263	reg=hl
engine/battle/effect_commands.asm:6393	reg=hl
engine/battle/late_gen_held_items.asm:220	reg=hl
engine/battle/move_effects/bide.asm:8	reg=hl
engine/battle/move_effects/bide.asm:29	reg=hl
engine/battle/move_effects/bide.asm:73	reg=de
engine/battle/move_effects/curse.asm:4	reg=bc
engine/battle/move_effects/disable.asm:8	reg=de
engine/battle/move_effects/encore.asm:4	reg=de
engine/battle/move_effects/fury_cutter.asm:3	reg=hl
engine/battle/move_effects/fury_cutter.asm:43	reg=hl
engine/battle/move_effects/future_sight.asm:4	reg=hl
engine/battle/move_effects/future_sight.asm:40	reg=hl
engine/battle/move_effects/future_sight.asm:56	reg=de
engine/battle/move_effects/protect.asm:16	reg=de
engine/battle/move_effects/psych_up.asm:4	reg=hl
engine/battle/move_effects/pursuit.asm:5	reg=hl
engine/battle/move_effects/rapid_spin.asm:13	reg=hl
engine/battle/move_effects/rollout.asm:5	reg=de
engine/battle/move_effects/rollout.asm:30	reg=hl
engine/battle/move_effects/safeguard.asm:4	reg=hl
engine/battle/move_effects/spikes.asm:3	reg=hl
engine/battle/move_effects/substitute.asm:5	reg=de
engine/battle/move_effects/substitute.asm:47	reg=hl
engine/battle/type_passive_damage_mods.asm:212	reg=hl
engine/battle/type_passive_damage_mods.asm:479	reg=hl
engine/battle/type_passive_damage_mods.asm:507	reg=hl
engine/battle/type_passive_damage_mods.asm:532	reg=hl
engine/battle/type_passive_damage_mods.asm:592	reg=hl
engine/battle/type_passive_damage_mods.asm:616	reg=hl
engine/battle/type_passive_damage_mods.asm:626	reg=hl
engine/battle/type_passive_damage_mods.asm:683	reg=hl
engine/battle/type_passive_damage_mods.asm:693	reg=hl
engine/battle/type_passive_damage_mods.asm:784	reg=hl
engine/battle/used_move_text.asm:222	reg=hl
```

## Conversion notes for the implementer

The recipe in `FIX_PROPOSALS.md` TD-005 "Updated 2026-05-02" calls for
a shared subroutine `_GetSidedAddr` taking player addr in `de`, enemy
addr in `bc`, returning the right one in `hl`. Several practical caveats
the classifier surfaced:

1. **Helper bank placement.** ROM0 has 236 free; the helper is 8-12
   bytes; logical home is `home/battle.asm`. Putting it in ROM0 means
   any caller can `call` (same-bank) reach it without `farcall` — at 3
   bytes per call site versus 5 for `callfar`, this materially affects
   per-site savings. Putting it in a ROMX bank forces `callfar` and
   probably costs more bytes than it saves.

2. **Three target registers, not one.** 38 of the 66 sites land the
   sided pointer in `hl`, 23 in `de`, 5 in `bc`. The recipe's
   "returning the right one in `hl`" only fits 38/66 cleanly. The other
   28 either need a register move after the call (1 byte: `ld d, h /
   ld e, l` is 2 bytes; pushing/popping is worse) or two helper variants
   (`_GetSidedAddrHL`, `_GetSidedAddrDE`, `_GetSidedAddrBC`).

   Per-site math:
   - HL target (38 sites): clean, ~5 bytes saved per site = ~190 bytes.
   - DE/BC target with reg-move (28 sites): ~3 bytes saved per site = ~84 bytes.
   - With per-reg helpers (3 helpers × ~10 bytes = 30 bytes overhead):
     ~5 bytes per site × 66 - 30 = ~300 bytes saved gross.

3. **Site-shape variance to watch for.** Spot checks showed:
   - Most common shape: `ldh a, [hBattleTurn]; and a; ld <reg>,
     wPlayerXxx; jr z, .label; ld <reg>, wEnemyXxx; .label`.
   - Less common: sided pointer load happens **before** the
     `ldh a, [hBattleTurn]` (e.g. `engine/battle/core.asm:1087`
     loads `de, wPlayerToxicCount` first, then reads turn).
   - Some sites have additional work between the turn read and the
     sided load (push/pop, intermediate calls). Those won't convert
     cleanly to a single `call _GetSidedAddrHL` without local refactoring.
   - Some sites' "player" address is actually the user's address and
     "enemy" is the opponent's — that's fine semantically, but the
     helper ABI must be `de = side-A, bc = side-B, return = matching
     side per turn flag`, not "player vs. enemy" specifically.

4. **Build measurement protocol** (per FIX_PROPOSALS recipe): convert
   one site, build before/after, diff `pokegold.map` for the affected
   bank. Stop and re-evaluate if the measured per-site recovery is
   below ~3 bytes (helper overhead won't pay back).

5. **Recommended starting site.** Try
   `engine/battle/effect_commands.asm:1918` (hl-target, simple shape)
   for first-conversion measurement, then bulk through the
   `effect_commands.asm` cluster (27 sites in the canary bank — the
   most leverage per session).

## Reproducing this enumeration

The classifier source lives at `.local/classify_pattern3.py` in this
worktree (deliberately not committed — it's a one-shot tool, not part
of the audit floor). To regenerate:

```bash
python3 .local/classify_pattern3.py > .local/pattern3_full.txt
grep "	A	" .local/pattern3_full.txt | sort > .local/pattern3_class_a.txt
```

The classifier uses a 12-line window around each `ldh a, [hBattleTurn]`
match and looks for both `wPlayer*` and `wEnemy*` loads on the same
register (hl, de, or bc). False negatives are possible where the
sided load is more than 8 lines after the turn read; the spot checks
suggest this is rare.

If a future agent wants higher precision, the classifier can be
upgraded to consume `pokegold.map` for actual instruction byte counts,
but that requires a build artifact and the current source-only pass is
sufficient for picking conversion targets.
