; Pure immediate HP facts for joint action valuation. These use the attacker
; fields of a caller-owned public context, so they also work after projected
; HP changes. No battle writes, item/input peeks, or random calls.

; ai-layer: POLICY
BossAI_ContextEntryDamage::
; DE=context, B=Spikes layers. BC=entry HP loss, capped at current HP.
; Flying bypasses Spikes; Air Balloon does not. Entry precedes Imposter.
; DE preserved; AF/HL and math scratch clobbered.
	ld a, b
	and a
	jr z, .none
	ld a, FLYING
	call BossAI_DamageKernel.AttackerContribution
	and a
	jr nz, .none
	ld a, b
	cp 1
	ld a, 8
	jr z, .denominator
	ld a, b
	cp 2
	ld a, 6
	jr z, .denominator
	ld a, 4
.denominator
	push af
	ad_address AD_ATTACKER_MAXHP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	pop af
	ld h, a
	ld a, 1
	call BossAI_DamageKernel.Scale
	push bc
	ad_address AD_ATTACKER_HP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	pop hl
	ld a, l
	sub c
	ld a, h
	sbc b
	ret nc ; current HP is the smaller quantity
	ld b, h
	ld c, l
	ret
.none
	ld bc, 0
	ret

; ai-layer: POLICY
BossAI_ContextRecovery::
; DE=context. BC=HP recovered if this move executes in the supplied state;
; carry=recognized recovery effect (including zero recovery at full/fainted HP).
; Status changes/Rest sleep are action transitions, not part of this HP amount.
; DE preserved; AF/HL and math scratch clobbered.
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_HEAL
	jr z, .ordinary
	cp EFFECT_MORNING_SUN
	ld b, MORN_F
	jr z, .time_heal
	cp EFFECT_SYNTHESIS
	ld b, DAY_F
	jr z, .time_heal
	cp EFFECT_MOONLIGHT
	ld b, NITE_F
	jr z, .time_heal
	ld bc, 0
	and a
	ret
.ordinary
	ad_address AD_MOVE
	ld a, [hl]
	cp REST
	ld a, 1
	jr z, .fraction
	ld a, 2
	jr .fraction
.time_heal
	ld c, 2 ; index 0..3 = eighth, quarter, half, whole
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
	ld b, 0
	ld hl, .Denominators
	add hl, bc
	ld a, [hl]
.fraction
	push af
	ad_address AD_ATTACKER_HP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	or c
	jr z, .zero_pop
	push bc
	ad_address AD_ATTACKER_MAXHP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	pop hl
	ld a, c
	sub l
	ld l, a
	ld a, b
	sbc h
	ld h, a ; missing HP, max HP remains BC
	jr c, .zero_pop
	pop af
	push hl
	ld h, a
	ld a, 1
	call BossAI_DamageKernel.Scale
	pop hl
	ld a, c
	sub l
	ld a, b
	sbc h
	jr c, .supported
	ld b, h
	ld c, l
.supported
	scf
	ret
.zero_pop
	pop af
	ld bc, 0
	scf
	ret
.Denominators
	db 8, 4, 2, 1

; ai-layer: POLICY
BossAI_ContextRecoil::
; DE=context, BC=raw damage of an executing recoil command (not capped HP loss).
; BC=own HP lost. Steel mono cancels, dual halves after minimum-one quarter.
; DE preserved; AF/HL clobbered. Caller establishes effect and execution.
	srl b
	rr c
	srl b
	rr c
	call BossAI_DamageKernel.MinOne
	ld a, STEEL
	call BossAI_DamageKernel.AttackerContribution
	and a
	jr z, .cap
	cp 2
	jr z, .none
	srl b
	rr c
.cap
	push bc
	ad_address AD_ATTACKER_HP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	pop hl
	ld a, l
	sub c
	ld a, h
	sbc b
	ret nc
	ld b, h
	ld c, l
	ret
.none
	ld bc, 0
	ret

; ai-layer: POLICY
BossAI_ContextDrain::
; DE=context, BC=raw damage of an executing drain command. BC=HP recovered.
; SapHealth uses half raw damage with minimum one, then caps at missing HP.
; Caller establishes effect, successful execution and Substitute eligibility.
; Matches command arithmetic even at zero HP; caller handles action denial.
; DE preserved; AF/HL clobbered.
	srl b
	rr c
	call BossAI_DamageKernel.MinOne
	push bc
	ad_address AD_ATTACKER_HP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	push bc
	ad_address AD_ATTACKER_MAXHP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	pop hl
	ld a, c
	sub l
	ld c, a
	ld a, b
	sbc h
	ld b, a
	jr c, .none
	pop hl
	ld a, l
	sub c
	ld a, h
	sbc b
	ret nc
	ld b, h
	ld c, l
	ret
.none
	pop bc
	ld bc, 0
	ret

; ai-layer: POLICY
BossAI_ContextSpeeds::
; DE=outgoing owned context. BC=owned effective Speed, HL=public player Speed.
; Bench begins at neutral stages. Unknown player item/DVs are not read.
; DE preserved. Active own Speed already includes status/type adjustments.
; Carry=ordinary modeled order is usable; clear for player Transform or bench
; Ditto whose entry Imposter may replace Speed. Returned priors remain diagnostic.
	ld hl, wEnemyMonSpeed
	ld c, MON_SPD
	call BossAI_BuildPublicDamageContext.OwnAddress
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ad_address AD_OWN_SLOT
	ld a, [hl]
	cp $ff
	jr z, .own_item
	push bc
	ad_address AD_ATTACKER_TYPES
	ld a, [hli]
	ld l, [hl]
	ld h, a
	push hl
	call BossAI_BuildPublicDamageContext.OwnStatus
	pop hl
	pop bc
	call .AdjustSpeed
.own_item
	push bc
	call BossAI_BuildPublicDamageContext.OwnItem
	pop bc
	cp CHOICE_SCARF
	jr nz, .player
	ld a, 3
	ld h, 2
	call BossAI_DamageKernel.Scale
.player
	push bc
	ld bc, $0102
	call BossAI_EstimatePlayerDamageStat
	ld a, [wBattleMonType1]
	ld h, a
	ld a, [wBattleMonType2]
	ld l, a
	ld a, [wBattleMonStatus]
	call .AdjustSpeed
	ld h, b
	ld l, c
	pop bc
	ld a, [wPlayerSubStatus5]
	bit SUBSTATUS_TRANSFORMED, a
	jr nz, .unknown
	push hl
	ad_address AD_OWN_SLOT
	ld a, [hl]
	cp $ff
	jr z, .known_pop
	push bc
	ld hl, wEnemyMonSpecies
	ld c, MON_SPECIES
	call BossAI_BuildPublicDamageContext.OwnByte
	pop bc
	cp DITTO
	jr z, .unknown_pop
.known_pop
	pop hl
	scf
	ret
.unknown_pop
	pop hl
.unknown
	and a
	ret
.AdjustSpeed
; BC=staged speed, H/L=types, A=status. Exact Electric then paralysis order.
	push af
	push hl
	ld a, ELECTRIC
	call .Contribution
	and a
	jr z, .paralysis
	cp 2
	ld a, ELECTRIC_SPD_HALF_NUM
	ld h, ELECTRIC_SPD_HALF_DEN
	jr nz, .electric
	ld a, ELECTRIC_SPD_FULL_NUM
	ld h, ELECTRIC_SPD_FULL_DEN
.electric
	call BossAI_DamageKernel.Scale
.paralysis
	pop hl
	pop af
	bit PAR, a
	ret z
	ld a, FIGHTING
	call .Contribution
	and a
	jr z, .ordinary
	cp 2
	ld a, PRZ_SPD_FIGHTING_HALF_NUM
	ld h, PRZ_SPD_FIGHTING_HALF_DEN
	jr nz, .scale
	ld a, PRZ_SPD_FIGHTING_FULL_NUM
	ld h, PRZ_SPD_FIGHTING_FULL_DEN
	jr .scale
.ordinary
	ld a, PRZ_SPD_NUM
	ld h, PRZ_SPD_DEN
.scale
	jp BossAI_DamageKernel.Scale
.Contribution
; A=query type, H/L=types; A=0,1,2. BC/DE/HL preserved.
	cp h
	jr z, .first
	cp l
	ld a, 0
	ret nz
	inc a
	ret
.first
	cp l
	ld a, 1
	ret nz
	inc a
	ret
