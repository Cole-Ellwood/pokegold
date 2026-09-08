; Native HP primitives for compact continuations. Words are big-endian.
; These helpers consume uncapped amounts. Action reachability (including the
; living-at-entry gate) belongs to the caller; a later drain can revive an
; actor reduced to zero by its own Life Orb within the same action.

BossAI_FastOwnCommandDescriptors:
; Effect tag, item tag. Shell Bell's item quota is derived from selected raw
; damage by the plan consumer; Life Orb uses the plan's fixed max-HP quota.
	db 0, 0, 0, 1, 0, 2
	db 1, 0, 1, 1, 1, 2
	db 2, 0, 2, 1, 2, 2
.end
ASSERT .end - BossAI_FastOwnCommandDescriptors == 18
ASSERT BANK(BossAI_FastOwnCommandDescriptors) == BANK(BossAI_FastDamageScript)

BossAI_FastLoseHP::
; HL=current HP word, BC=raw loss. Store max(0, HP-loss), return BC=actual
; loss. DE and SP preserved; AF/HL scratch. No memory beyond this HP word.
	push de
	ld a, [hli]
	ld d, a
	ld a, [hl]
	ld e, a
	sub c
	ld [hld], a
	ld a, d
	sbc b
	jr c, .zero
	ld [hl], a
	pop de
	ret
.zero
	xor a
	ld [hli], a
	ld [hl], a
	ld b, d
	ld c, e
	pop de
	ret

PUSHS
SECTION "Boss AI Fast Recovery Quota", ROMX
; Reached by farcall only (the owned compiler and the fixtures): out of the hot bank.
BossAI_FastRecoveryQuota::
; DE=public damage context. BC=uncapped recovery quota, carry=recognized.
; Independent of current HP: plans must remain valid after preceding damage.
; Matches ContextRecovery's max/effect/weather/time/link fraction and minimum
; one for positive maximum. DE/SP preserved; AF/HL scratch, no memory writes.
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_HEAL
	jr z, .ordinary
	cp EFFECT_MORNING_SUN
	ld b, MORN_F
	jr z, .time
	cp EFFECT_SYNTHESIS
	ld b, DAY_F
	jr z, .time
	cp EFFECT_MOONLIGHT
	ld b, NITE_F
	jr z, .time
	ld bc, 0
	and a
	ret
.ordinary
	ad_address AD_MOVE
	ld a, [hl]
	cp REST
	ld a, 0
	jr z, .fraction
	inc a
	jr .fraction
.time
	ld c, 2
	ld a, [wLinkMode]
	and a
	jr nz, .weather
	ld a, [wTimeOfDay]
	cp b
	jr z, .weather
	dec c
.weather
	ad_address AD_WEATHER
	ld a, [hl]
	and a
	jr z, .time_fraction
	inc c
	cp WEATHER_SUN
	jr z, .time_fraction
	dec c
	dec c
.time_fraction
	ld a, 3
	sub c ; index0..3 denotes denominator8,4,2,1
.fraction
	push af
	ad_address AD_ATTACKER_MAXHP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	or c
	jr z, .zero
	pop af
	and a
	jr z, .supported
.shift
	srl b
	rr c
	dec a
	jr nz, .shift
	ld a, b
	or c
	jr nz, .supported
	inc c
.supported
	scf
	ret
.zero
	pop af
	scf
	ret
POPS

BossAI_FastGainHP::
; HL=current HP word, BC=uncapped quota, DE=maximum HP (>0).
; Current HP must be <= maximum. Store min(maximum, HP+quota), return
; BC=actual gain, preserve DE/SP. AF/HL scratch. Addition cannot wrap.
	push de
	push hl
	ld a, [hli]
	ld l, [hl]
	ld h, a ; HL=old HP
	push hl
	ld a, e
	sub l
	ld e, a
	ld a, d
	sbc h
	ld d, a ; DE=missing HP
	ld a, c
	sub e
	ld a, b
	sbc d
	jr c, .quota_ready
	ld b, d
	ld c, e
.quota_ready
	pop hl
	add hl, bc
	ld d, h
	ld e, l
	pop hl
	ld [hl], d
	inc hl
	ld [hl], e
	pop de
	ret

BossAI_FastDrainHP::
; HL=current user HP, DE=max HP, BC=raw damage. Same ABI as GainHP.
; Called only after successful damage and the preceding item command.
	srl b
	rr c
	ld a, b
	or c
	jr nz, .gain
	inc c
.gain
	jp BossAI_FastGainHP

BossAI_FastRecoilHP::
; HL=current user HP, BC=raw damage, A=Steel contribution (0,1,2).
; Same ABI as LoseHP. Quarter/min-one precedes dual-Steel halving.
	cp 2
	jr z, .none
	push af
	srl b
	rr c
	srl b
	rr c
	ld a, b
	or c
	jr nz, .scaled
	inc c
.scaled
	pop af
	and a
	jr z, .lose
	srl b
	rr c
.lose
	jp BossAI_FastLoseHP
.none
	ld bc, 0
	ret

; The deterministic damage script owns the first 15 bytes of the assigned
; 48-byte executor workspace. Inputs point into a compact continuation.
DEF FST_USER_HP EQU $a530 ; BE pointer
DEF FST_TARGET_HP EQU FST_USER_HP + 2 ; BE pointer
DEF FST_USER_MAX EQU FST_TARGET_HP + 2 ; BE maximum HP
DEF FST_RAW EQU FST_USER_MAX + 2 ; selected raw damage, never overwritten
DEF FST_ITEM_QUOTA EQU FST_RAW + 2 ; uncapped item amount
DEF FST_RECOIL EQU FST_ITEM_QUOTA + 2 ; Steel contribution0..2
DEF FST_ITEM EQU FST_RECOIL + 1 ; 0none,1user loss,2user gain
DEF FST_EFFECT EQU FST_ITEM + 1 ; 0plain,1drain,2recoil
DEF FST_ACTUAL_LOSS EQU FST_EFFECT + 1 ; BE output
ASSERT FST_ACTUAL_LOSS + 2 <= $a560

BossAI_FastDamageScript::
; SRAM bank0 open. Inputs above describe an already reached successful
; single-hit damage command: both actors lived at action entry, amount is
; valid for this continuation, item/effect eligibility was certified by the
; producer. No selfdestruct or multihit support. The caller owns event flags.
; Target loss -> user item -> drain/recoil, using RAW rather than capped loss.
; DE/SP preserved. Carry=accepted. Invalid tags reject before all mutation;
; raw0 is an accepted no-op. Only the two HP words and actual-loss output
; may change. Pointer domains and HP<=maximum are caller preconditions.
	ld a, [FST_EFFECT]
	cp 3
	jr nc, .reject
	ld a, [FST_ITEM]
	cp 3
	jr nc, .reject
	ld a, [FST_RECOIL]
	cp 3
	jr nc, .reject
	xor a
	ld [FST_ACTUAL_LOSS], a
	ld [FST_ACTUAL_LOSS + 1], a
	call .Raw
	ld a, b
	or c
	jr z, .accepted
	push de
	ld hl, FST_TARGET_HP
	ld a, [hli]
	ld l, [hl]
	ld h, a
	call BossAI_FastLoseHP
	ld a, b
	ld [FST_ACTUAL_LOSS], a
	ld a, c
	ld [FST_ACTUAL_LOSS + 1], a
	call .User
	ld a, [hli]
	or [hl]
	jr z, .after_item
	dec hl
	ld a, [FST_ITEM_QUOTA]
	ld b, a
	ld a, [FST_ITEM_QUOTA + 1]
	ld c, a
	ld a, [FST_ITEM]
	and a
	jr z, .after_item
	dec a
	jr nz, .item_gain
	call BossAI_FastLoseHP
	jr .after_item
.item_gain
	call BossAI_FastGainHP
.after_item
	ld a, [FST_EFFECT]
	and a
	jr z, .done
	push af
	call .User
	call .Raw
	pop af
	dec a
	jr nz, .recoil
	call BossAI_FastDrainHP
	jr .done
.recoil
	ld a, [FST_RECOIL]
	call BossAI_FastRecoilHP
.done
	pop de
.accepted
	scf
	ret
.reject
	and a
	ret
.Raw
	ld a, [FST_RAW]
	ld b, a
	ld a, [FST_RAW + 1]
	ld c, a
	ret
.User
	ld a, [FST_USER_MAX]
	ld d, a
	ld a, [FST_USER_MAX + 1]
	ld e, a
	ld hl, FST_USER_HP
	ld a, [hli]
	ld l, [hl]
	ld h, a
	ret
