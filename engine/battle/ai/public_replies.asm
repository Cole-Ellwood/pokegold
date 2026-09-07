; Public move replies as sets, without private moveslots or mutable BaseData.
; The set is a possibility model, not a claim that every listed move is owned.

DEF PR_POSSIBLE EQU 0 ; 256 move-ID bits, bit zero unused
DEF PR_REVEALED EQU PR_POSSIBLE + 32
DEF PR_FLAGS EQU PR_REVEALED + 32
DEF PR_SPECIES EQU PR_FLAGS + 1
DEF PR_HOPS EQU PR_SPECIES + 1
DEF PR_CONTEXT_SIZE EQU PR_HOPS + 1
DEF PR_FOUR_REVEALED_F EQU 0
DEF PR_UNBOUNDED_COPY_F EQU 1

; ai-layer: POLICY
BossAI_BuildPublicReplySet::
; DE=PR_CONTEXT_SIZE caller-owned bytes, preserved. AF/BC/HL scratch.
; Observed moves remain possible even when absent from natural learnability.
; Otherwise include current/pre-evolution level-up, TM/HM and egg moves. The
; earliest ancestor includes every level-up move: breeding can pass moves
; known by both parents without checking the child's level. This deliberately
; overapproximates breeding eligibility; it never asserts actual ownership. Four
; trusted revealed moves close the natural prior. Unknown transformed/Sketch
; sets stay broad. Struggle remains possible because player PP is private.
; No RNG or live battle writes. The pre-evolution lookup briefly uses and
; restores its non-battle wCurPartySpecies argument; BaseData stays untouched.
	ld h, d
	ld l, e
	ld b, PR_CONTEXT_SIZE
	xor a
.clear
	ld [hli], a
	dec b
	jr nz, .clear
	ld hl, wPlayerUsedMoves
	ld b, NUM_MOVES
.observed
	ld a, [hli]
	push bc
	push hl
	call .AddRevealed
	pop hl
	pop bc
	dec b
	jr nz, .observed
	push de
	farcall BossAI_PlayerActiveFourMoveSaturated
	pop de
	jr nc, .prior
	ad_address PR_FLAGS
	set PR_FOUR_REVEALED_F, [hl]
	jp .done
.prior
	ld a, [wPlayerSubStatus5]
	bit SUBSTATUS_TRANSFORMED, a
	jp nz, .broad
	ld a, [wBattleMonSpecies]
	and a
	jp z, .broad
	cp NUM_POKEMON + 1
	jp nc, .broad
	cp SMEARGLE
	jp z, .broad
	ad_address PR_SPECIES
	ld [hl], a
	ad_address PR_HOPS
	ld [hl], NUM_POKEMON
.species
	call .TMs
	call .LevelMoves
	call .EggMoves
	call .PreEvolution
	jr nc, .done
	ad_address PR_SPECIES
	ld [hl], a
	ad_address PR_HOPS
	dec [hl]
	jr nz, .species
; Malformed evolution cycles must not quietly produce an incomplete prior.
.broad
	ad_address PR_FLAGS
	set PR_UNBOUNDED_COPY_F, [hl]
	ld b, 1
.all_moves
	ld a, b
	push bc
	call .AddPossible
	pop bc
	inc b
	ld a, b
	cp NUM_ATTACKS + 1
	jr c, .all_moves
.done
	ld a, STRUGGLE
	jp .AddPossible

.AddRevealed
	and a
	ret z
	cp NUM_ATTACKS + 1
	ret nc
	push af
	ld bc, PR_REVEALED
	call .SetBit
	pop af
.AddPossible
	and a
	ret z
	cp NUM_ATTACKS + 1
	ret nc
	ld bc, PR_POSSIBLE
.SetBit
; A=move ID, BC=set offset. DE=context. Move IDs are direct bit indices.
	ld h, d
	ld l, e
	add hl, bc
	ld c, a
	srl a
	srl a
	srl a
	ld b, 0
	push bc
	ld c, a
	add hl, bc
	pop bc
	ld a, c
	and 7
	ld c, a
	ld a, 1
	jr z, .set_bit
.shift
	add a
	dec c
	jr nz, .shift
.set_bit
	or [hl]
	ld [hl], a
	ret

.TMs
	ad_address PR_SPECIES
	ld a, [hl]
	dec a
	ld hl, BaseData + BASE_TMHM
	ld bc, BASE_DATA_SIZE
	call AddNTimes
	ld b, 1 ; bit within this compatibility byte
	ld c, 0 ; zero-based TM index
.tm
	ld a, BANK(BaseData)
	call GetFarByte
	and b
	jr z, .next_tm
	push bc
	push hl
	ld hl, TMHMMoves
	ld b, 0
	add hl, bc
	ld a, BANK(TMHMMoves)
	call GetFarByte
	call .AddPossible
	pop hl
	pop bc
.next_tm
	inc c
	ld a, c
	cp NUM_TM_HM
	ret nc
	sla b
	jr nz, .tm
	ld b, 1
	inc hl
	jr .tm

.LevelMoves
	ad_address PR_SPECIES
	ld a, [hl]
	dec a
	ld c, a
	ld b, 0
	ld hl, EvosAttacksPointers
	add hl, bc
	add hl, bc
	ld a, BANK(EvosAttacksPointers)
	call GetFarWord
.skip_evos
	ld a, BANK("Evolutions and Attacks")
	call GetFarByte
	and a
	jr z, .learned
	inc hl
	cp EVOLVE_STAT
	jr nz, .ordinary_evo
	inc hl
.ordinary_evo
	inc hl
	inc hl
	jr .skip_evos
.learned
	inc hl
	push hl
	call .PreEvolution
	pop hl
	ld a, [wBattleMonLevel]
	jr c, .level_cap
	ld a, $ff ; inherited level-up moves at the base of the evolution family
.level_cap
	ld b, a
.level_move
	ld a, BANK("Evolutions and Attacks")
	call GetFarByte
	and a
	ret z
	cp b
	jr z, .include_level
	jr nc, .next_level
.include_level
	inc hl
	ld a, BANK("Evolutions and Attacks")
	call GetFarByte
	push hl
	push bc
	call .AddPossible
	pop bc
	pop hl
	inc hl
	jr .level_move
.next_level
	inc hl
	inc hl
	jr .level_move

.EggMoves
	ad_address PR_SPECIES
	ld a, [hl]
	dec a
	ld c, a
	ld b, 0
	ld hl, EggMovePointers
	add hl, bc
	add hl, bc
	ld a, BANK(EggMovePointers)
	call GetFarWord
.egg
	ld a, BANK("Egg Moves")
	call GetFarByte
	cp -1
	ret z
	push hl
	call .AddPossible
	pop hl
	inc hl
	jr .egg

.PreEvolution
	ld a, [wCurPartySpecies]
	push af
	ad_address PR_SPECIES
	ld a, [hl]
	ld [wCurPartySpecies], a
	push de
	farcall GetPreEvolution
	pop de
	ld a, [wCurPartySpecies]
	ld h, a
	pop bc
	ld a, b
	ld [wCurPartySpecies], a
	ld a, h
	ret
