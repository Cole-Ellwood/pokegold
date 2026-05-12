# Sleep Clause — Codex task spec

## Goal

Add Sleep Clause to this ROM hack: each side can have at most one of the
**opposing** team's Pokémon asleep due to its own moves at any moment.

User's rules (verbatim):
- "you can only put one of your opponents pokemon to sleep at a time"
- "when they wake up, you can sleep something again"
- "putting yourself to sleep like rest does not affect this"
- "the opponent can still put one of your pokemon to sleep"

So the clause is **per-side and symmetric**: the player and the enemy each
have an independent clause slot, tracking only the sleep they themselves
inflicted on the *other* team. Rest is self-inflicted and never consumes
either side's slot.

## Mechanics summary

1. Each side gets a "clause slot." Value = party slot of the opposing mon
   currently asleep due to that side's move, or 0 = "slot free."
2. A side's sleep move that would apply sleep to an opposing mon **fails
   immediately if that side's slot is occupied** — no roll, no animation
   beyond the standard failed-move animation, "But it failed!" text (see
   §6 for text-choice options).
3. The slot is set when sleep is successfully applied via
   `BattleCommand_SleepTarget`, *after* the existing held-item heal check
   (so if a held Berry instantly cures the sleep, no slot is consumed).
4. The slot is cleared when the slept mon wakes up naturally (SLP counter
   ticks to 0).
5. Rest does not touch either slot (Rest uses a different code path that
   never calls `BattleCommand_SleepTarget`).
6. `ClearBattleRAM` zeros battle WRAM at the start of every battle, so
   placing the slot bytes in the cleared range gives free reset.

## Why slot tracking, not "scan party for sleep"

The naive "scan opposing party for any asleep mon" check would false-fail
the clause when the opposing trainer used Rest on their own mon — that
mon is asleep in storage, but it wasn't put there by the *attacker's*
move. Tracking which party slot WE put to sleep, by side, avoids this.

## Files to change

### 1. `ram/wram.asm` — add the two clause-slot bytes

Place inside the `wBattle..wBattleEnd` block so `ClearBattleRAM` zeros
them automatically at the start of every battle. A natural anchor is
right after `wEnemyReflectCount`'s padding (around line 874). Two new
exported labels:

```asm
wPlayerSleepClauseSlot:: db ; 0 = free; 1..6 = wCurOTMon+1 of slept enemy
wEnemySleepClauseSlot::  db ; 0 = free; 1..6 = wCurBattleMon+1 of slept player
```

Make sure they're inside `SECTION "Battle WRAM",WRAMX` and before
`wBattleEnd` — verify by grepping for `wBattleEnd::` and putting these
above it. Do not move existing labels.

### 2. `engine/battle/effect_commands.asm` — `BattleCommand_SleepTarget` (line 3448)

Add a clause check **at the very top** of `BattleCommand_SleepTarget`,
before any existing check. Pattern:

```asm
BattleCommand_SleepTarget:
	; Sleep Clause: each side can have at most one of the OTHER team's
	; mons asleep due to its own move at a time. Self-sleep (Rest) is
	; a different code path and never reaches here.
	ldh a, [hBattleTurn]
	and a
	ld a, [wPlayerSleepClauseSlot]
	jr z, .clause_check_loaded
	ld a, [wEnemySleepClauseSlot]
.clause_check_loaded
	and a
	jr z, .clause_ok
	ld hl, SleepClauseActiveText
	jp .fail
.clause_ok

	call GetOpponentItem
	; ... existing code continues unchanged ...
```

Then, **after** the `farcall UseHeldStatusHealingItem` / `ret nz` pair
(currently line 3498-3499), and **before** `call OpponentCantMove`, record
the clause slot:

```asm
	farcall UseHeldStatusHealingItem
	ret nz

	; Sleep applied AND not immediately cured by held item — record clause.
	ldh a, [hBattleTurn]
	and a
	jr nz, .clause_set_enemy_side
	ld a, [wCurOTMon]
	inc a
	ld [wPlayerSleepClauseSlot], a
	jr .clause_set_done
.clause_set_enemy_side
	ld a, [wCurBattleMon]
	inc a
	ld [wEnemySleepClauseSlot], a
.clause_set_done

	call OpponentCantMove
	ret
```

`.fail` is the existing local label at line 3504 — reuse it; do not add a
new one. Verify the local labels you add (`.clause_check_loaded`,
`.clause_ok`, `.clause_set_enemy_side`, `.clause_set_done`) don't collide
with existing locals in the same function (they don't at time of writing).

### 3. `engine/battle/effect_commands.asm` — wake-up hooks

When a mon wakes up naturally (SLP counter decrements to 0), clear the
*opposing* side's clause slot if it pointed at that mon. There are two
wake-up paths:

**Player wakes up — line 175 `.woke_up` label** (after `dec a; ld
[wBattleMonStatus], a; and SLP_MASK; jr z, .woke_up`):

```asm
.woke_up
	; Sleep Clause: if the enemy was the one who put this player mon
	; to sleep, free their clause slot.
	ld a, [wEnemySleepClauseSlot]
	and a
	jr z, .clause_skip
	ld b, a
	ld a, [wCurBattleMon]
	inc a
	cp b
	jr nz, .clause_skip
	xor a
	ld [wEnemySleepClauseSlot], a
.clause_skip
	ld hl, WokeUpText
	; ... existing code continues unchanged ...
```

**Enemy wakes up — line 409 `.woke_up` label** (mirror, reading
`wPlayerSleepClauseSlot` against `wCurOTMon+1`).

Place the cleanup *before* `ld hl, WokeUpText` so the wake-up message
prints unchanged.

### 4. Faint / held-item Awakening — secondary clear sites (do these)

Two more places where a slept mon stops being asleep without the SLP
counter ticking down:

- **Faint of the slept mon.** When a Pokémon faints, its status byte is
  cleared. Grep for the in-battle faint path (`HandleHealingItems`,
  `HandleEnemyMonFaint`, or whatever calls `xor a; ld [wEnemyMonStatus], a`
  on faint — search for status-clear writes near HP=0 paths). Add a
  parallel clause-clear: if the fainted mon's party slot matches the
  recorded clause slot, zero it.
- **Awakening item / Full Restore used mid-battle.** The player's bag
  status-cure items can wake a slept mon. Grep for the in-battle item
  handler that clears `wBattleMonStatus` (likely in
  `engine/items/item_effects.asm` — the awakening / heal path). Add the
  same conditional clear.

If either of these gets skipped, the only consequence is the clause stays
"used" until the next battle (clears on `ClearBattleRAM`). The base
feature works without these; they're correctness polish. **Do both.**

### 5. AI — out of scope but recommended follow-up

`engine/battle/ai/scoring.asm:313` (`AI_Smart_Sleep`) and several
references in `engine/battle/ai/boss_policy_move.asm` score sleep moves.
Without a clause-aware check, the AI may waste a turn picking a sleep
move that auto-fails. **Do not modify AI scoring in this task** — the
boss AI rebuild is shelved (`docs/boss_ai_design_conversation_2026-05-05.md`)
and uncoordinated edits to scoring risk breaking
`tools/audit/check_boss_ai_trace_invariants.py`. Note it for a later
task.

## 6. Fail-message text

Add a new text constant `SleepClauseActiveText` in `data/text/battle.asm`,
placed immediately after `AlreadyAsleepText` (currently around line 691).
Use this exact body — the user picked the wording explicitly:

```asm
SleepClauseActiveText:
	text "Sleep Clause is"
	line "active!"
	prompt
```

(Gen 2 battle text uses `text` + `line` + `prompt` macros and lowercase
sentence text — match the surrounding style. Don't add a `<USER>` /
`<TARGET>` substitution; the message is global, not actor-specific.)

The clause-check patch in §2 references this label
(`ld hl, SleepClauseActiveText`).

## Edge cases — confirmed handled by this design

| Case | Behavior | Reason |
| --- | --- | --- |
| Player sleeps enemy A; enemy switches to B; player tries Hypnosis on B | Fails | Player's slot still holds A |
| Same as above, but A wakes up later (via SLP counter ticking on a forced switch-in) | Then player can sleep B | A's wake clears player's slot |
| Enemy uses Rest while one of their party is already asleep from player's move | Enemy sleeps normally | Rest doesn't go through SleepTarget |
| Player uses Rest while enemy team has someone asleep from player's earlier Hypnosis | Player rests normally | Rest doesn't touch clause; enemy's clause unaffected (player's mon, not enemy's) |
| Both sides have a slept mon (one each) | Both clauses occupied independently | Clauses are per-side |
| Slept mon faints | Clause clears | Faint-hook cleanup (§4) |
| Player Awakens own mon | Enemy's clause clears | Awakening hook cleanup (§4) |
| Wild battle (1 mon) | Clause naturally a no-op | Sleeping the wild mon fills the clause; nothing else to target |
| Link battle | Same as trainer battle | Same code path |

## Verification floor

Per CLAUDE.md "Build & verification":

1. Build via the WSL invocation:
   ```
   wsl -e bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 PYTHON=python3 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc'
   ```
2. Regenerate dev index:
   `python scripts/generate_dev_index.py --rom pokegold`
3. Run `python tools/audit/check_release_smoke.py`.
4. Run `python tools/audit/check_farcall_hl_clobber.py` (this task
   doesn't add cross-bank calls, but the macro touches battle paths —
   cheap to confirm clean).
5. Run `python tools/audit/check_farcall_a_clobber.py` for the same
   reason.
6. Save-format impact: **none** — both clause bytes live in battle-only
   WRAM, cleared by `ClearBattleRAM`, never written to save. No
   `SAVE_FORMAT_VERSION` bump needed.
7. ROM identity (`make compare`) WILL diverge — that's expected, this
   is a mechanics change. Do not refresh `roms.sha1` in this task; the
   user signs off on identity bumps separately.

## Manual playtest checklist

Boot the resulting `pokegold.gbc` (the user will run this — Codex doesn't
need to). The user will verify:

- Use Hypnosis on an opposing mon. Lands.
- Opponent switches to another mon. Use Hypnosis again — should print
  "But it failed!" without rolling accuracy.
- Wait for first mon to wake (or switch back in). Try Hypnosis on the
  second mon — should work now.
- In a trainer fight where the AI has a sleep move, let it sleep your
  mon, then have a different player mon use Rest. Confirm Rest works
  normally and you wake from Rest normally; AI's clause should still be
  occupied (against the originally-slept mon).
- Confirm both sides can have a mon asleep simultaneously (one from
  player's move, one from enemy's move).

## Don't do

- Don't move existing labels in `effect_commands.asm` — keep line drift
  minimal, the asm authoring guide audits paths by line range.
- Don't add new constants to `constants/battle_constants.asm` for the
  clause slots — they're plain bytes, no constant needed.
- Don't introduce a new audit script in this task — the manual
  playtest is the acceptance gate.
- Don't touch boss AI scoring (see §5).
- Don't bump `SAVE_FORMAT_VERSION`.

## When you think you're done

Report back with:
1. The exact files modified and a one-line summary of each diff.
2. Build output (last 30 lines of `make` or "OK").
3. `check_release_smoke.py` result.
4. Confirmation that `wPlayerSleepClauseSlot` and `wEnemySleepClauseSlot`
   live inside `wBattle..wBattleEnd` (so `ClearBattleRAM` zeros them).
5. Anything you couldn't find or had to guess at (e.g. the awakening-item
   hook site if `engine/items/item_effects.asm` doesn't have an obvious
   one).
