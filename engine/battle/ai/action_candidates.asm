; Legal owned actions, independent of legacy preference scores and nomination.
; No battle state, move index, item lock or RNG is changed by this enumerator.

DEF AC_MOVES EQU 0 ; four move IDs indexed by exact active PP slot; zero=absent
DEF AC_SWITCH_MASK EQU AC_MOVES + NUM_MOVES ; bits 0..5, zero-based party slots
DEF AC_MODE EQU AC_SWITCH_MASK + 1
DEF AC_FORCED_MOVE EQU AC_MODE + 1
DEF AC_FORCED_SLOT EQU AC_FORCED_MOVE + 1
DEF AC_CONTEXT_SIZE EQU AC_FORCED_SLOT + 1

DEF AC_CHOICE EQU 0
DEF AC_FORCED EQU 1
DEF AC_WAIT EQU 2
DEF AC_REPLACE EQU 3

BossAI_EnumeratePublicActionsFromC::
; Cross-bank adapter: farcall replaces A/HL. Decision kind arrives in C.
	ld a, c
	jp BossAI_EnumeratePublicActions

; ai-layer: POLICY
BossAI_EnumeratePublicActions::
; DE=AC_CONTEXT_SIZE caller-owned bytes. A=AV_REPLACEMENT_ACTION for a faint
; replacement, otherwise an ordinary decision. DE preserved; AF/BC/HL scratch.
; AC_CHOICE: enumerate each nonzero AC_MOVES entry and AC_SWITCH_MASK bit.
; AC_FORCED: use AC_FORCED_MOVE/AC_FORCED_SLOT, plus any legal switch entries.
; AC_WAIT: recharge consumes the active turn, with no voluntary switch.
; AC_REPLACE: enumerate only the living bench, ignoring voluntary switch gates.
; Forced moves are selected actions, not promises that their commands succeed.
; In particular, Encore can retain an exhausted/disabled action; execution must
; still model combat's failure checks. Normal actions enforce exact slot PP.
	push af
	ld h, d
	ld l, e
	ld b, AC_CONTEXT_SIZE
	xor a
.clear
	ld [hli], a
	dec b
	jr nz, .clear
	pop af
	cp AV_REPLACEMENT_ACTION
	jr z, .replacement
	call .Moves
	call .CanSwitch
	ret nc
	jp .Bench
.replacement
	ad_address AC_MODE
	ld [hl], AC_REPLACE
	jp .Bench

.Moves
; Non-link ParseEnemyAction selects Encore before the forced-turn gate. Held
; normalization follows Encore; ordinary forced turns bypass it altogether.
	ld a, [wEnemySubStatus5]
	bit SUBSTATUS_ENCORED, a
	jr nz, .encore
	ld a, [wEnemySubStatus4]
	bit SUBSTATUS_RECHARGE, a
	jp nz, .recharge
	push de
	farcall CheckEnemyLockedIn
	pop de
	jp nz, .locked_turn
	call .ChoiceLock
	jr c, .force_choice
	ld b, 0
.ordinary_slot
	call .SlotUsable
	jr nc, .ordinary_next
	push bc
	ad_address AC_MOVES
	ld c, b
	ld b, 0
	add hl, bc
	ld [hl], a
	pop bc
.ordinary_next
	inc b
	ld a, b
	cp NUM_MOVES
	jr c, .ordinary_slot
	ad_address AC_MOVES
	ld b, NUM_MOVES
	xor a
.any_move
	or [hl]
	inc hl
	dec b
	jr nz, .any_move
	and a
	ret nz
	jp .struggle

.encore
	ld a, [wCurEnemyMoveNum]
	ld b, a
	ld a, [wLastEnemyMove]
	call .StoreForced
; EnforceEnemyHeldMoveRestrictions exits before items on these sentinel moves.
	and a
	ret z
	cp $ff
	ret z
	cp STRUGGLE
	ret z
	push af
	call .ChoiceLock
	jr c, .encore_choice
	pop af
	call .VestBlocked
	ret nc
; Combat's Vest fallback uses the first usable attacking slot, not a free
; selection among all moves after an otherwise forced Encore command.
	ld b, 0
.vest_fallback
	call .SlotUsable
	jp c, .StoreForced
	inc b
	ld a, b
	cp NUM_MOVES
	jr c, .vest_fallback
	jp .struggle
.encore_choice
	pop bc ; discard saved AF; force_choice finds its own exact slot
.force_choice
; Choice enforcement synchronizes the FIRST matching slot. A duplicate in a
; later PP slot cannot rescue an exhausted first match.
	ld c, a
	ld b, 0
	ld hl, wEnemyMonMoves
.choice_slot
	ld a, [hli]
	cp c
	jr z, .choice_found
	inc b
	ld a, b
	cp NUM_MOVES
	jr c, .choice_slot
	jr .struggle
.choice_found
	call .SlotUsable
	jr nc, .struggle
	jp .StoreForced

.recharge
	ad_address AC_MODE
	ld [hl], AC_WAIT
	ret
.locked_turn
	ld a, [wCurEnemyMoveNum]
	ld b, a
	ld a, [wCurEnemyMove]
	jp .StoreForced
.struggle
	ld b, 0
	ld a, STRUGGLE
.StoreForced
; A=actual selected move, B=its PP slot. Preserve both for the caller.
	ad_address AC_FORCED_MOVE
	ld [hli], a
	ld [hl], b
	ad_address AC_MODE
	ld [hl], AC_FORCED
	ret

.ChoiceLock
; A=known active lock, carry=currently holding a Choice item with a lock.
	ld a, [wEnemyMonItem]
	cp CHOICE_BAND
	jr z, .choice_item
	cp CHOICE_SPECS
	jr z, .choice_item
	cp CHOICE_SCARF
	jr nz, .no_choice
.choice_item
	ld a, [wEnemyChoiceLockedMove]
	and a
	ret z
	scf
	ret
.no_choice
	and a
	ret

.SlotUsable
; B=exact PP slot. A=move ID and carry=usable; B/DE preserved.
	push bc
	ld c, b
	ld b, 0
	ld hl, wEnemyMonMoves
	add hl, bc
	ld a, [hl]
	and a
	jr z, .slot_no
	cp $ff
	jr z, .slot_no
	push af
	ld hl, wEnemyMonPP
	add hl, bc
	ld a, [hl]
	and PP_MASK
	jr z, .slot_no_pop
	pop af
	ld c, a
	ld a, [wEnemyDisabledMove]
	cp c
	jr z, .slot_no
	ld a, c
	call .VestBlocked
	jr c, .slot_no
	pop bc
	scf
	ret
.slot_no_pop
	pop af
.slot_no
	pop bc
	and a
	ret

.VestBlocked
; A=move; preserve A/BC/DE. Use combat's full fixed/counter/Bide whitelist.
	push af
	ld a, [wEnemyMonItem]
	cp ASSAULT_VEST
	jr z, .vest_item
	pop af
	and a
	ret
.vest_item
	pop af
	push af
	push bc
	push de
	ld e, a
	farcall IsMoveBlockedByAssaultVestFromE_Far
	pop de
	pop bc
	jr c, .vest_no
	pop af
	and a
	ret
.vest_no
	pop af
	scf
	ret

.CanSwitch
; These are the ordinary outer AI_SwitchOrTryItem gates, without nomination.
	ld a, [wBattleMode]
	cp TRAINER_BATTLE
	jr nz, .cannot_switch
	ld a, [wLinkMode]
	and a
	jr nz, .cannot_switch
	push de
	farcall CheckEnemyLockedIn
	pop de
	jr nz, .cannot_switch
	ld a, [wPlayerSubStatus5]
	bit SUBSTATUS_CANT_RUN, a
	jr nz, .cannot_switch
	ld a, [wEnemyWrapCount]
	and a
	jr nz, .cannot_switch
	scf
	ret
.cannot_switch
	and a
	ret

.Bench
	ld b, 0 ; party slot
	ld c, 1 ; corresponding mask bit
	ld hl, wOTPartyMon1HP
.bench_slot
	ld a, [wOTPartyCount]
	cp b
	ret z
	ret c
	ld a, [wCurOTMon]
	cp b
	jr z, .bench_next
	ld a, [hli]
	or [hl]
	dec hl
	jr z, .bench_next
	push hl
	ad_address AC_SWITCH_MASK
	ld a, [hl]
	or c
	ld [hl], a
	pop hl
.bench_next
	push de
	ld de, PARTYMON_STRUCT_LENGTH
	add hl, de
	pop de
	sla c
	inc b
	ld a, b
	cp PARTY_LENGTH
	jr c, .bench_slot
	ret
