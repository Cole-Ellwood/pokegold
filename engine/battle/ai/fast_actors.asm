; Import the HP portion of the two compact actors from an owned public context.
; Other actor fields remain unpopulated until their producer owns them. Once
; per defender: a cold section, reached by farcall (C and DE in, carry out).
PUSHS
SECTION "Boss AI Fast Actors", ROMX
BossAI_FastImportActorHP::
; C=own weight128/192, plus bit0 when the player HP table built by an earlier
; import may be kept if its maximum is unchanged (the caller vouches that
; nothing wrote the SRAM reservation since). DE=owned AD context, SRAM0 open.
; Context/DE/SP preserved. Validates both HP/max pairs before writing.
; Carry=success; rejects malformed HP, zero maxima, wrong direction or weight
; without writes. Writes actor80, the two HP-table reservations,
; table-builder arithmetic scratch and wFastPlayerTable only.
	ld a, c
	and $fe ; the weight without the keep bit
	cp 128
	jr z, .weight_ok
	cp 192
	jp nz, .reject
.weight_ok
	ad_address AD_DIRECTION
	ld a, [hl]
	cp 1
	jp nz, .reject
	push bc
	ad_address AD_ATTACKER_HP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ad_address AD_ATTACKER_MAXHP
	call .ValidHP
	jp nc, .reject_pop
	ad_address AD_DEFENDER_HP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ad_address AD_DEFENDER_MAXHP
	call .ValidHP
	jp nc, .reject_pop
	ld hl, FSA_OWN
	ld b, 80
	xor a
.clear
	ld [hli], a
	dec b
	jr nz, .clear
	pop bc
	ld a, c
	and 1
	ld [wFastPlayerTable + 3], a ; the keep bit, once the import is accepted
	xor c
	ld [FSA_WEIGHT], a
	ld a, 128
	ld [FSA_PLAYER + 34], a
	ad_address AD_ATTACKER_HP
	ld a, [hli]
	ld [FSA_START_HP], a
	ld [FSA_ENTRY_HP], a
	ld a, [hli]
	ld [FSA_START_HP + 1], a
	ld [FSA_ENTRY_HP + 1], a
	ld a, [hli]
	ld [FSA_MAX_HP], a
	ld b, a
	ld a, [hl]
	ld [FSA_MAX_HP + 1], a
	ld c, a
	farcall BossAI_FastBuildOwnHPTableFar
	ld [FSA_HP_MODE], a
	ld a, [FSA_START_HP]
	ld b, a
	ld a, [FSA_START_HP + 1]
	ld c, a
	farcall BossAI_FastOwnPotentialFar
	ld a, b
	ld [FSA_START_PHI], a
	ld [FSA_ENTRY_PHI], a
	ld a, c
	ld [FSA_START_PHI + 1], a
	ld [FSA_ENTRY_PHI + 1], a
	ad_address AD_DEFENDER_HP
	ld a, [hli]
	ld [FSA_PLAYER], a
	ld [FSA_PLAYER + 6], a
	ld a, [hl]
	ld [FSA_PLAYER + 1], a
	ld [FSA_PLAYER + 7], a
	ad_address AD_DEFENDER_MAXHP
	ld a, [hli]
	ld [FSA_PLAYER + 2], a
	ld b, a
	ld a, [hl]
	ld [FSA_PLAYER + 3], a
	ld c, a
; the player table depends on the maximum alone
	ld hl, wFastPlayerTable
	ld a, [hli]
	cp b
	jr nz, .build_player_table
	ld a, [hli]
	cp c
	jr nz, .build_player_table
	inc hl
	ld a, [hld] ; the keep bit
	and a
	jr z, .build_player_table
	ld a, [hl] ; the mode recorded with the table
	jr .player_table_ready
.build_player_table
	farcall BossAI_FastBuildPlayerHPTableFar
	ld [wFastPlayerTable + 2], a
	ld hl, wFastPlayerTable
	ld a, [FSA_PLAYER + 2]
	ld [hli], a
	ld a, [FSA_PLAYER + 3]
	ld [hl], a
	ld a, [wFastPlayerTable + 2]
.player_table_ready
	ld [FSA_PLAYER + 37], a
	ld a, [FSA_PLAYER]
	ld b, a
	ld a, [FSA_PLAYER + 1]
	ld c, a
	farcall BossAI_FastPlayerPotentialFar
	ld a, b
	ld [FSA_PLAYER + 4], a
	ld [FSA_PLAYER + 8], a
	ld a, c
	ld [FSA_PLAYER + 5], a
	ld [FSA_PLAYER + 9], a
	scf
	ret
.reject_pop
	pop bc
.reject
	and a
	ret
.ValidHP
; BC=current HP, HL=maximum word. Require positive max and current<=max.
	ld a, [hli]
	push af
	or [hl]
	jr z, .zero
	pop af
	cp b
	jr c, .invalid_hp
	jr nz, .valid_hp
	ld a, [hl]
	cp c
	jr c, .invalid_hp
.valid_hp
	scf
	ret
.zero
	pop af
.invalid_hp
	and a
	ret
POPS
