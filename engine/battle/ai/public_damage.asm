; Public adapters for the direction-free damage kernel, in its ROM section.
; Unknown player DVs/items/badge boosts are never read, even for preservation.
; Player damage stats assume DV8 and use public species/level/stages/status.

MACRO ad_scale_field
	push af
	push hl
	ad_address \1
	ld a, [hli]
	ld b, a
	ld c, [hl]
	pop hl
	pop af
	call BossAI_DamageKernel.Scale
	ad_address \1
	ld [hl], b
	inc hl
	ld [hl], c
ENDM

; ai-layer: POLICY
BossAI_PublicDamageKO::
; B=1 outgoing minimum, B=0 incoming maximum; C=known/revealed move.
; Carry is an on-hit KO premise, separate from hit probability/action order.
; Unknown outgoing damage cannot claim a finish; unknown incoming damage is
; conservatively a threat. Publicly impossible hits and Substitute are gated.
; BC/DE/HL and live state preserved; AF and math/banking scratch clobbered.
	push bc
	push de
	push hl
	add sp, -AD_CONTEXT_SIZE
	ld hl, sp + 0
	ld d, h
	ld e, l
	call BossAI_BuildPublicDamageContext
	ad_address AD_ACCURACY
	ld a, [hl]
	and a
	jr z, .no
	ad_address AD_DEFENDER_HP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	or c
	jr z, .no
	ad_address AD_FLAGS
	bit AD_SUBSTITUTE_F, [hl]
	jr z, .range
; A single hit ends at the substitute. Multiple hits may break it and reach
; real HP; unknown substitute HP must remain a conservative incoming threat.
	ad_address AD_MAX_HITS
	ld a, [hl]
	cp 2
	jr c, .no
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	jr nz, .no
	scf
	jr .done
.range
	push bc ; target current HP
	ad_address AD_DIRECTION
	ld a, [hl]
	push af
	call BossAI_PublicDamageRange
	jr nc, .unknown
	pop af
	and a
	jr nz, .compare
	ld b, d
	ld c, e
.compare
	pop hl
	ld a, c
	sub l
	ld a, b
	sbc h
	ccf
	jr .done
.unknown
	pop af
	pop hl
	and a
	jr nz, .no
	scf
	jr .done
.no
	and a
.done
	ld a, 0
	adc 0
	add sp, AD_CONTEXT_SIZE
	rrca
	pop hl
	pop de
	pop bc
	ret

; ai-layer: POLICY
BossAI_EstimatePublicDamage::
; B=1 own outgoing, B=0 revealed incoming; C=move id.
; BC=min, DE=max noncritical HP loss on successful hits; carry=supported.
; HL and live battle/AI state preserved. AF, HRAM math/banking scratch clobber.
; The context exists only on the stack; no persistent memory or save change.
	ld d, $ff
; ai-layer: POLICY
BossAI_EstimatePartyDamage::
; Same outputs/preservation as the active adapter; D=owned party slot (or $ff).
	push hl
	ld a, d
	add sp, -AD_CONTEXT_SIZE
	ld hl, sp + 0
	ld d, h
	ld e, l
	call BossAI_BuildOwnedDamageContext
	call BossAI_PublicDamageRange
	ld a, 0
	adc 0 ; keep supported across stack deallocation's flag changes
	add sp, AD_CONTEXT_SIZE
	rrca
	pop hl
	ret

; ai-layer: POLICY
BossAI_PublicDamageRange::
; DE=context. Returns BC=min, DE=max HP loss; HL/AF clobbered. Context remains caller
; owned; only the requested roll/hit count and output scratch are changed.
	ad_address AD_MIN_HITS
	ld a, [hli]
	cp 1
	jr nz, .multiple_hits
	ld a, [hl]
	cp 1
	jp z, BossAI_DamageKernel.SingleHitRange
.multiple_hits
	ad_address AD_MIN_HITS
	ld a, [hl]
	ad_address AD_HITS
	ld [hli], a
	ld [hl], 217
	call BossAI_DamageKernel
	jr nc, .unknown
	push bc
	ad_address AD_TOTAL
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ad_address AD_RAW_MIN
	ld [hl], b
	inc hl
	ld [hl], c
	ad_address AD_POSTROLL
	ld a, [hl]
	push af
	ad_address AD_MAX_POSTROLL
	ld a, [hl]
	ad_address AD_POSTROLL
	ld [hl], a
	ad_address AD_MAX_HITS
	ld a, [hl]
	ad_address AD_HITS
	ld [hli], a
	ld [hl], 255
	call BossAI_DamageKernel
	push bc
	ad_address AD_TOTAL
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ad_address AD_RAW_MAX
	ld [hl], b
	inc hl
	ld [hl], c
	pop bc
	pop af
	ad_address AD_POSTROLL
	ld [hl], a
	pop hl
	ld d, b
	ld e, c
	ld b, h
	ld c, l
	scf
	ret
.unknown
	ad_address AD_RAW_MIN
	xor a
	ld [hli], a
	ld [hli], a
	ld [hli], a
	ld [hl], a
	ld bc, 0
	ld de, 0
	and a
	ret

; ai-layer: POLICY
BossAI_BuildOwnedDamageContext::
; A=owned party slot ($ff active); B=direction, C=move; DE=caller context.
	jp BossAI_BuildPublicDamageContext.with_slot

; ai-layer: POLICY
BossAI_BuildPublicDamageContext::
; B direction, C move; DE points to AD_CONTEXT_SIZE caller-owned bytes.
; DE preserved; AF/BC/HL clobbered. No live battle state is written.
	ld a, $ff
.with_slot
	push af
	push bc
	ld h, d
	ld l, e
	ld b, AD_CONTEXT_SIZE
	xor a
.clear
	ld [hli], a
	dec b
	jr nz, .clear
	pop bc
	pop af
	ad_address AD_OWN_SLOT
	ld [hl], a
	cp $ff
	jr z, .valid_slot
	cp PARTY_LENGTH
	jp nc, .unsupported
	push bc
	ld b, a
	ld a, [wOTPartyCount]
	cp b
	pop bc
	jp z, .unsupported
	jp c, .unsupported
.valid_slot
	ad_address AD_DIRECTION
	ld [hl], b
	ad_address AD_MOVE
	ld [hl], c
	ld a, c
	and a
	jp z, .unsupported
	call BossAI_LoadDamageMoveAttributes
	ad_address AD_ITEM_NUM
	ld [hl], 1
	inc hl
	ld [hl], 1
	ad_address AD_POSTROLL
	ld [hl], 1
	inc hl
	ld [hl], 1
	ad_address AD_MIN_HITS
	ld [hl], 1
	inc hl
	ld [hl], 1
	ld a, [wBattleWeather]
	ad_address AD_WEATHER
	ld [hl], a
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	jr z, .incoming
	ld hl, wEnemyMonLevel
	ld c, MON_LEVEL
	call .OwnByte
	ad_address AD_LEVEL
	ld [hl], a
	ld a, AD_ATTACKER_TYPES
	call .OwnTypes
	ld hl, wBattleMonType1
	ld a, AD_DEFENDER_TYPES
	call .CopyWord
	ld hl, wBattleMonHP
	ld a, AD_DEFENDER_HP
	call .CopyWord
	ld hl, wBattleMonMaxHP
	ld a, AD_DEFENDER_MAXHP
	call .CopyWord
	ld a, [wPlayerSubStatus1]
	ld b, a
	ld a, [wPlayerSubStatus4]
	ld c, a
	ld a, [wBattleMonStatus]
	jr .flags
.incoming
	ld a, [wBattleMonLevel]
	ad_address AD_LEVEL
	ld [hl], a
	ld hl, wBattleMonType1
	ld a, AD_ATTACKER_TYPES
	call .CopyWord
	ld a, AD_DEFENDER_TYPES
	call .OwnTypes
	ld hl, wEnemyMonHP
	ld c, MON_HP
	call .OwnAddress
	ld a, AD_DEFENDER_HP
	call .CopyWord
	ld hl, wEnemyMonMaxHP
	ld c, MON_MAXHP
	call .OwnAddress
	ld a, AD_DEFENDER_MAXHP
	call .CopyWord
	ld hl, wEnemySubStatus1
	xor a
	call .OwnState
	ld b, a
	ld hl, wEnemySubStatus4
	xor a
	call .OwnState
	ld c, a
	call .OwnStatus
.flags
	ad_address AD_FLAGS
	and a
	jr z, .identified
	set AD_DEFENDER_STATUS_F, [hl]
.identified
	bit SUBSTATUS_IDENTIFIED, b
	jr z, .substitute
	set AD_IDENTIFIED_F, [hl]
.substitute
	bit SUBSTATUS_SUBSTITUTE, c
	jr z, .hp_flags
	set AD_SUBSTITUTE_F, [hl]
.hp_flags
	call .HPFlags
	call .Category
	call .Stats
	call .KnownItems
.finish_move
	call .EffectFacts
	call BossAI_PublicHitFacts
.copyguards
; Entry Imposter can replace a bench Ditto's stats and moves. Its original
; party stats are not a valid promise about the state after switching in.
	ad_address AD_OWN_SLOT
	ld a, [hl]
	cp $ff
	jr z, .transformed_player
	ld hl, wEnemyMonSpecies
	ld c, MON_SPECIES
	call .OwnByte
	cp DITTO
	jp z, .unsupported
.transformed_player
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_STATIC_DAMAGE
	ret z
	cp EFFECT_LEVEL_DAMAGE
	ret z
	cp EFFECT_SUPER_FANG
	ret z
; Transform makes the player's copied stats ambiguous under a species/DV prior.
; Constant damage is still known; other estimates stay explicitly unsupported
; until public outcome memory or a successor context supplies copied stats.
	ld a, [wPlayerSubStatus5]
	bit SUBSTATUS_TRANSFORMED, a
	jp nz, .unsupported
	ret

.EffectFacts
	call .EffectSupport
	call .MultiHitItemState
	ad_address AD_FLAGS
	bit AD_SUBSTITUTE_F, [hl]
	ret z
	ad_address AD_MAX_HITS
	ld a, [hl]
	cp 2
	ret c
; A multi-hit attack can break a substitute and then damage real HP. Without
; an explicit substitute-HP successor context, do not fabricate that envelope.
	jp .unsupported

.MoveAttr
; A=attribute offset; return table byte. DE and caller BC preserved.
	push bc
	ld b, a
	ad_address AD_MOVE
	ld a, [hl]
	dec a
	push bc
	ld hl, Moves
	ld bc, MOVE_LENGTH
	call BossAI_AddTableOffset
	pop bc
	ld c, b
	ld b, 0
	add hl, bc
	ld a, BANK(Moves)
	call GetFarByte
	pop bc
	ret

.CopyWord
; Copy two bytes from HL to context offset A. DE preserved.
	push hl
	ld h, 0
	ld l, a
	add hl, de
	ld b, h
	ld c, l
	pop hl
	ld a, [hli]
	ld [bc], a
	inc bc
	ld a, [hl]
	ld [bc], a
	ret

.HPFlags
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	jr z, .public_attacker_hp
	ld hl, wEnemyMonHP
	ld c, MON_HP
	call .OwnAddress
	jr .attacker_hp
.public_attacker_hp
	ld hl, wBattleMonHP
.attacker_hp
	call .ReadHPAndMax
	push hl
	ad_address AD_ATTACKER_HP
	ld [hl], b
	inc hl
	ld [hl], c
	pop bc
	ad_address AD_ATTACKER_MAXHP
	ld [hl], b
	inc hl
	ld [hl], c
.RefreshHPFlags
	ad_address AD_ATTACKER_MAXHP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	push bc
	ad_address AD_ATTACKER_HP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	pop hl
.UpdateHPFlags
; BC=attacker current HP, HL=attacker max HP; defender HP/max already in
; context. Successor valuation can refresh HP thresholds without live writes.
	push hl
	ad_address AD_FLAGS
	res AD_ATTACKER_LOW_F, [hl]
	res AD_DEFENDER_HIGH_F, [hl]
	pop hl
	push de
; BC=current, HL=max; three times current < max is strictly below a third.
	ld d, h
	ld e, l
	ld h, b
	ld l, c
	add hl, hl
	add hl, bc
	ld a, l
	sub e
	ld a, h
	sbc d
	pop de
	jr nc, .defender_hp
	ad_address AD_FLAGS
	set AD_ATTACKER_LOW_F, [hl]
.defender_hp
	ad_address AD_DEFENDER_HP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	sla c
	rl b
	ad_address AD_DEFENDER_MAXHP
	ld a, [hli]
	cp b
	jr c, .above
	ret nz
	ld a, [hl]
	cp c
	ret nc
.above
	ad_address AD_FLAGS
	set AD_DEFENDER_HIGH_F, [hl]
	ret
.ReadHPAndMax
	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld c, a
	ld a, [hli]
	ld l, [hl]
	ld h, a
	ret

.Category
	ad_address AD_MOVE
	ld a, [hl]
	cp OUTRAGE
	ret nz
	ld a, DRAGON
	call BossAI_DamageKernel.AttackerContribution
	and a
	ret z
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	jr z, .public_raw
	ld hl, wEnemyAttack
	ld c, MON_ATK
	call .OwnAddress
	ld a, [hli]
	ld b, a
	ld c, [hl]
	push bc
	ld hl, wEnemySpAtk
	ld c, MON_SAT
	call .OwnAddress
	ld a, [hli]
	ld b, a
	ld c, [hl]
	jr .compare_raw
.public_raw
	ld bc, 0 ; raw public Attack (index 0)
	call BossAI_EstimatePlayerDamageStat
	push bc
	ld bc, 3 ; raw public Sp. Atk (index 3)
	call BossAI_EstimatePlayerDamageStat
.compare_raw
	pop hl ; raw Attack
	ld a, c
	sub l
	ld a, b
	sbc h
	ret nc ; Sp. Atk >= Attack, including ties: special
	ad_address AD_CATEGORY
	ld [hl], NORMAL
	ret

.Stats
	ad_address AD_CATEGORY
	ld a, [hl]
	cp SPECIAL
	ld c, 0
	jr c, .axis
	ld c, 3
.axis
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	jr z, .incoming_stats
	push bc
	ld a, c
	add a
	ld c, a
	ld b, 0
	ld hl, wEnemyMonAttack
	add hl, bc
	ld a, c
	add MON_ATK
	ld c, a
	call .OwnAddress
	ld a, AD_ATTACK
	call .CopyWord
	call .OwnAttackStatus
	pop bc
	inc c
	ld b, 1 ; public effective defense
	call BossAI_EstimatePlayerDamageStat
	ad_address AD_DEFENSE
	ld [hl], b
	inc hl
	ld [hl], c
	ld a, [wPlayerScreens]
	jr .screen
.incoming_stats
	push bc
	ld b, 1
	call BossAI_EstimatePlayerDamageStat
	ad_address AD_ATTACK
	ld [hl], b
	inc hl
	ld [hl], c
	pop bc
	inc c
	ld a, c
	add a
	ld c, a
	ld b, 0
	ld hl, wEnemyMonAttack
	add hl, bc
	ld a, c
	add MON_ATK
	ld c, a
	call .OwnAddress
	ld a, AD_DEFENSE
	call .CopyWord
	ld a, [wEnemyScreens]
.screen
	ld b, a
	ad_address AD_CATEGORY
	ld a, [hl]
	cp SPECIAL
	jr nc, .light_screen
	bit SCREENS_REFLECT, b
	ret z
	jr .double_defense
.light_screen
	bit SCREENS_LIGHT_SCREEN, b
	ret z
.double_defense
	ad_address AD_DEFENSE + 1
	sla [hl]
	dec hl
	rl [hl]
	ret

.KnownItems
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	jp z, .defender_item
	call .HeldEffect
	ld a, b
	cp HELD_CHOICE_BAND
	jr z, .choice_band
	cp HELD_CHOICE_SPECS
	jr z, .choice_specs
	call .OwnItem
	cp THICK_CLUB
	jr z, .thick_club
	cp LIGHT_BALL
	jr z, .light_ball
	jp .damage_item
.choice_band
	ad_address AD_CATEGORY
	ld a, [hl]
	cp SPECIAL
	ret nc
	jr .choice
.choice_specs
	ad_address AD_CATEGORY
	ld a, [hl]
	cp SPECIAL
	ret c
.choice
	ld a, CHOICE_STAT_NUM
	ld h, CHOICE_STAT_DEN
	ad_scale_field AD_ATTACK
	ret
.thick_club
	ad_address AD_CATEGORY
	ld a, [hl]
	cp SPECIAL
	ret nc
	ld hl, wTempEnemyMonSpecies
	ld c, MON_SPECIES
	call .OwnByte
	cp CUBONE
	jr z, .species_double
	cp MAROWAK
	ret nz
	jr .species_double
.light_ball
	ad_address AD_CATEGORY
	ld a, [hl]
	cp SPECIAL
	ret c
	ld hl, wTempEnemyMonSpecies
	ld c, MON_SPECIES
	call .OwnByte
	cp PIKACHU
	ret nz
.species_double
	ld a, 2
	ld h, 1
	ad_scale_field AD_ATTACK
	call BossAI_CapDamageStat
	ad_address AD_ATTACK
	ld [hl], b
	inc hl
	ld [hl], c
	ret

.defender_item
	call .OwnItem
	cp AIR_BALLOON
	jr nz, .defender_stat_item
	ad_address AD_FLAGS
	set AD_BALLOON_F, [hl]
	ret
.defender_stat_item
	call .HeldEffect
	ld a, b
	cp HELD_ASSAULT_VEST
	jr z, .vest
	cp HELD_EVOLITE
	jr z, .eviolite
	call .OwnItem
	cp METAL_POWDER
	ret nz
	ad_address AD_CATEGORY
	ld a, [hl]
	cp SPECIAL
	ret nc
	ld hl, wTempEnemyMonSpecies
	ld c, MON_SPECIES
	call .OwnByte
	cp DITTO
	ret nz
	ld a, 3
	ld h, 2
	ad_scale_field AD_DEFENSE
	call BossAI_CapDamageStat
	ad_address AD_DEFENSE
	ld [hl], b
	inc hl
	ld [hl], c
	ret
.vest
	ad_address AD_CATEGORY
	ld a, [hl]
	cp SPECIAL
	ret c
	jr .boost_defense
.eviolite
	call .OwnSpeciesCanEvolve
	ret nc
.boost_defense
	ld a, 3
	ld h, 2
	ad_scale_field AD_DEFENSE
	ret

.damage_item
	call .HeldEffect
	ld a, b
	cp HELD_LIFE_ORB
	jr z, .orb
	cp HELD_MUSCLE_BAND
	jr z, .muscle
	cp HELD_WISE_GLASSES
	jr z, .wise
	cp HELD_EXPERT_BELT
	jr z, .belt
	cp HELD_METRONOME
	jr z, .metronome
; Known type-item effect/parameter, read from the actual item/type tables.
	push bc
	ld hl, TypeBoostItems
.type_item_loop
	ld a, BANK(TypeBoostItems)
	call GetFarByte
	inc hl
	cp -1
	jr z, .no_type_item
	cp b
	jr z, .type_item_found
	inc hl
	jr .type_item_loop
.type_item_found
	ld a, BANK(TypeBoostItems)
	call GetFarByte
	ad_address AD_TYPE
	cp [hl]
	jr nz, .no_type_item
	pop bc
	ad_address AD_TYPE_ITEM_PERCENT
	ld [hl], c
	ret
.no_type_item
	pop bc
	ret
.muscle
	ad_address AD_CATEGORY
	ld a, [hl]
	cp SPECIAL
	ret nc
	jr .eleven_tenths
.wise
	ad_address AD_CATEGORY
	ld a, [hl]
	cp SPECIAL
	ret c
.eleven_tenths
	ld b, 11
	ld c, 10
	jr .item_fraction
.orb
	ld b, LIFE_ORB_DAMAGE_NUM
	ld c, LIFE_ORB_DAMAGE_DEN
	jr .item_fraction
.belt
	ld bc, EFFECTIVE
	call BossAI_DamageKernel.Chart
	ld a, c
	cp EFFECTIVE + 1
	ret c
	ld b, EXPERT_BELT_NUM
	ld c, EXPERT_BELT_DEN
	jr .item_fraction
.metronome
	ld hl, wEnemyMetronomeCount
	xor a
	call .OwnState
	add a
	add METRONOME_STEP_DEN
	cp METRONOME_MAX_MULT_NUM + 1
	jr c, .metronome_capped
	ld a, METRONOME_MAX_MULT_NUM
.metronome_capped
	ld b, a
	ld c, METRONOME_MAX_MULT_DEN
.item_fraction
	ad_address AD_ITEM_NUM
	ld [hl], b
	inc hl
	ld [hl], c
	ret

.HeldEffect
; B effect, C parameter of the known OWN held item; DE preserved.
	call .OwnItem
	and a
	ld bc, 0
	ret z
	dec a
	ld hl, ItemAttributes + ITEMATTR_EFFECT
	ld bc, ITEMATTR_STRUCT_LENGTH
	call BossAI_AddTableOffset
	ld a, BANK(ItemAttributes)
	call GetFarByte
	ld b, a
	inc hl
	ld a, BANK(ItemAttributes)
	call GetFarByte
	ld c, a
	ret

.EffectSupport
	ad_address AD_MOVE
	ld a, [hl]
	cp STRUGGLE
	jr nz, .effect
	ad_address AD_FLAGS
	set AD_STRUGGLE_F, [hl]
	ret
.effect
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_MULTI_HIT
	jr z, .multi
	cp EFFECT_DOUBLE_HIT
	jr z, .double
	cp EFFECT_POISON_MULTI_HIT
	jr z, .double
	cp EFFECT_SOLARBEAM
	jr z, .solar
	cp EFFECT_DREAM_EATER
	jr z, .dream
	cp EFFECT_SNORE
	jr z, .snore
	cp EFFECT_EARTHQUAKE
	jr z, .grounded_attack
	cp EFFECT_GUST
	jr z, .flying_attack
	cp EFFECT_TWISTER
	jr z, .flying_attack
	cp EFFECT_STOMP
	jr z, .stomp
	cp EFFECT_PURSUIT
	jp z, .pursuit
	ld b, a
	ld hl, .DirectEffects
.supported_loop
	ld a, [hli]
	cp -1
	jp z, .unsupported
	cp b
	jr nz, .supported_loop
	ret
.double
	ad_address AD_MIN_HITS
	ld [hl], 2
	inc hl
	ld [hl], 2
	ret
.multi
	ad_address AD_MIN_HITS
	ld [hl], 2
	inc hl
	ld [hl], 5
	ret
.solar
	ad_address AD_WEATHER
	ld a, [hl]
	cp WEATHER_SUN
	ret z
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	ld a, [wPlayerSubStatus3]
	jr z, .charged
	ld hl, wEnemySubStatus3
	xor a
	call .OwnState
.charged
	bit SUBSTATUS_CHARGED, a
	ret nz
	jr .unsupported
.dream
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	jr nz, .player_sleeping
	call .OwnStatus
	jr .sleeping
.player_sleeping
	ld a, [wBattleMonStatus]
	jr .sleeping
.snore
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	ld a, [wBattleMonStatus]
	jr z, .sleeping
	call .OwnStatus
.sleeping
	and SLP_MASK
	ret nz
	jr .unsupported
.grounded_attack
	call .TargetSubStatus3
	bit SUBSTATUS_UNDERGROUND, a
	ret z
	jr .double_postroll
.flying_attack
	call .TargetSubStatus3
	bit SUBSTATUS_FLYING, a
	ret z
	jr .double_postroll
.stomp
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	jr nz, .player_minimized
	ld hl, wEnemyMinimized
	xor a
	call .OwnState
	jr .minimized
.player_minimized
	ld a, [wPlayerMinimized]
.minimized
	and a
	ret z
.double_postroll
	ad_address AD_POSTROLL
	ld [hl], 2
	inc hl
	ld [hl], 2
	ret
.pursuit
; A target's future switch is not private input the AI may inspect. Preserve
; both on-hit amounts; the successor evaluator can specialize this branch.
	ad_address AD_MAX_POSTROLL
	ld [hl], 2
	ret
.TargetSubStatus3
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	ld a, [wPlayerSubStatus3]
	ret nz
	ld hl, wEnemySubStatus3
	xor a
	jp .OwnState
.unsupported
	ad_address AD_FLAGS
	set AD_UNSUPPORTED_F, [hl]
	ret

.OwnAddress
; HL=active source, C=party field offset. Return corresponding owned address.
; BC/DE preserved. Only the known own party is addressable by this adapter.
	push bc
	push hl
	ad_address AD_OWN_SLOT
	ld a, [hl]
	cp $ff
	pop hl
	jr z, .own_address_done
	push bc
	ld hl, wOTPartyMon1Species
	ld bc, PARTYMON_STRUCT_LENGTH
	call AddNTimes
	pop bc
	ld b, 0
	add hl, bc
.own_address_done
	pop bc
	ret
.MultiHitItemState
; The amount kernel currently advances defender HP only. Known after-hit
; items can change the attacker's HP each hit; keep these two-sided outcomes
; explicit unknowns until the successor model supplies both HP transitions.
	ad_address AD_MAX_HITS
	ld a, [hl]
	cp 2
	ret c
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	jr z, .contact_helmet
	call .OwnItem
	cp LIFE_ORB
	jp z, .unsupported
	cp SHELL_BELL
	jp z, .unsupported
	ret
.contact_helmet
	call .OwnItem
	cp ROCKY_HELMET
	ret nz
	ad_address AD_MOVE
	ld a, [hl]
	dec a
	ld c, a
	ld b, 0
	ld hl, MoveContactFlags
	add hl, bc
	ld a, BANK(MoveContactFlags)
	call GetFarByte
	and a
	jp nz, .unsupported
	ret
.OwnByte
	call .OwnAddress
	ld a, [hl]
	ret
.OwnItem
	push bc
	ld hl, wEnemyMonItem
	ld c, MON_ITEM
	call .OwnByte
	pop bc
	ret
.OwnStatus
	push bc
	ld hl, wEnemyMonStatus
	ld c, MON_STATUS
	call .OwnByte
	pop bc
	ret
.OwnState
; HL=active volatile/stage field, A=ordinary entry default. Bench members
; do not inherit active stages, charging, accuracy items or other volatiles.
	push bc
	ld b, a
	push hl
	ad_address AD_OWN_SLOT
	ld a, [hl]
	cp $ff
	pop hl
	ld a, b
	jr nz, .own_state_done
	ld a, [hl]
.own_state_done
	pop bc
	ret
.OwnTypes
; A=destination context offset. Bench types come from the public base table.
	push af
	ad_address AD_OWN_SLOT
	ld a, [hl]
	cp $ff
	jr z, .active_types
	ld hl, wEnemyMonSpecies
	ld c, MON_SPECIES
	call .OwnByte
	dec a
	ld hl, BaseData + BASE_TYPE_1
	ld bc, BASE_DATA_SIZE
	call BossAI_AddTableOffset
	ld a, BANK(BaseData)
	call GetFarByte
	ld b, a
	inc hl
	ld a, BANK(BaseData)
	call GetFarByte
	ld c, a
	jr .store_types
.active_types
	ld hl, wEnemyMonType1
	ld a, [hli]
	ld b, a
	ld c, [hl]
.store_types
	pop af
	ld h, 0
	ld l, a
	add hl, de
	ld [hl], b
	inc hl
	ld [hl], c
	ret
.OwnSpeciesCanEvolve
	push bc
	push de
	ld hl, wEnemyMonSpecies
	ld c, MON_SPECIES
	call .OwnByte
	and a
	jr z, .cannot_evolve
	dec a
	ld c, a
	ld b, 0
	ld hl, EvosAttacksPointers
	add hl, bc
	add hl, bc
	ld a, BANK(EvosAttacksPointers)
	call GetFarWord
	ld a, BANK("Evolutions and Attacks")
	call GetFarByte
	and a
	jr z, .cannot_evolve
	scf
.cannot_evolve
	pop de
	pop bc
	ret
.OwnAttackStatus
; Active stats already contain status/stage changes. Bench Attack is raw:
; neutral entry stages, with public burn/Fighting fractions applied once.
	ad_address AD_OWN_SLOT
	ld a, [hl]
	cp $ff
	ret z
	ad_address AD_CATEGORY
	ld a, [hl]
	cp SPECIAL
	ret nc
	call .OwnStatus
	bit BRN, a
	ret z
	ad_address AD_ATTACK
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld a, FIGHTING
	call BossAI_DamageKernel.AttackerContribution
	and a
	jr nz, .fighting_burn
	ld a, BRN_ATK_NUM
	ld h, BRN_ATK_DEN
	jr .apply_bench_burn
.fighting_burn
	cp 2
	ld a, BRN_ATK_FIGHTING_HALF_NUM
	ld h, BRN_ATK_FIGHTING_HALF_DEN
	jr nz, .apply_bench_burn
	ld a, BRN_ATK_FIGHTING_FULL_NUM
	ld h, BRN_ATK_FIGHTING_FULL_DEN
.apply_bench_burn
	call BossAI_DamageKernel.Scale
	ad_address AD_ATTACK
	ld [hl], b
	inc hl
	ld [hl], c
	ret

.DirectEffects
; Unlisted effects are explicitly uncertain, never assumed harmless or lethal.
; Conditional/ramping/counter/charge effects need action-state support before
; promotion; their move IDs remain available to the action evaluator.
	db EFFECT_NORMAL_HIT, EFFECT_POISON_HIT, EFFECT_LEECH_HIT
	db EFFECT_BURN_HIT, EFFECT_FREEZE_HIT, EFFECT_PARALYZE_HIT
	db EFFECT_SELFDESTRUCT, EFFECT_ALWAYS_HIT, EFFECT_RAMPAGE
	db EFFECT_FLINCH_HIT, EFFECT_PAY_DAY, EFFECT_TRI_ATTACK
	db EFFECT_SUPER_FANG, EFFECT_STATIC_DAMAGE, EFFECT_TRAP_TARGET
	db EFFECT_JUMP_KICK, EFFECT_RECOIL_HIT
	db EFFECT_ATTACK_DOWN_HIT, EFFECT_DEFENSE_DOWN_HIT, EFFECT_SPEED_DOWN_HIT
	db EFFECT_SP_ATK_DOWN_HIT, EFFECT_SP_DEF_DOWN_HIT
	db EFFECT_ACCURACY_DOWN_HIT, EFFECT_EVASION_DOWN_HIT
	db EFFECT_CONFUSE_HIT, EFFECT_HYPER_BEAM, EFFECT_RAGE, EFFECT_LEVEL_DAMAGE
	db EFFECT_DEFROST_OPPONENT, EFFECT_FALSE_SWIPE, EFFECT_PRIORITY_HIT
	db EFFECT_THIEF, EFFECT_FLAME_WHEEL, EFFECT_SACRED_FIRE, EFFECT_RAPID_SPIN
	db EFFECT_DEFENSE_UP_HIT, EFFECT_ATTACK_UP_HIT, EFFECT_ALL_UP_HIT
	db EFFECT_THUNDER
	db -1

; ai-layer: POLICY
BossAI_EstimatePlayerDamageStat::
; C=Attack(0), Defense(1), Speed(2), Sp.Atk(3), Sp.Def(4).
; B=0 raw, B=1 staged (and burn for Attack). Speed passives are separate.
; BC=result; DE/HL preserved. Public species/level/stage/status only; DV8.
	push de
	push hl
	push bc
	ld a, c
	add BASE_ATK
	ld e, a
	ld d, 0
	ld hl, BaseData
	add hl, de
	ld a, [wBattleMonSpecies]
	dec a
	ld bc, BASE_DATA_SIZE
	call BossAI_AddTableOffset
	ld a, BANK(BaseData)
	call GetFarByte
	ld c, a
	ld b, 0
	ld hl, 8
	add hl, bc
	add hl, hl
	xor a
	ldh [hMultiplicand], a
	ld a, h
	ldh [hMultiplicand + 1], a
	ld a, l
	ldh [hMultiplicand + 2], a
	ld a, [wBattleMonLevel]
	ldh [hMultiplier], a
	call BossAI_Multiply
	ld a, 100
	ldh [hDivisor], a
	ld b, 4
	call BossAI_Divide
	ldh a, [hQuotient + 2]
	ld b, a
	ldh a, [hQuotient + 3]
	ld c, a
	ld hl, 5
	add hl, bc
	ld b, h
	ld c, l
	pop de ; original mode/index
	ld a, d
	and a
	jr z, .done
	push de
	push bc
	ld d, 0
	ld hl, wPlayerAtkLevel
	add hl, de
	ld a, [hl]
	dec a
	cp MAX_STAT_LEVEL
	jr c, .stage_valid
	ld a, BASE_STAT_LEVEL - 1
.stage_valid
	add a
	ld e, a
	ld d, 0
	ld hl, StatLevelMultipliers
	add hl, de
	ld a, BANK(StatLevelMultipliers)
	call GetFarByte
	push af
	inc hl
	ld a, BANK(StatLevelMultipliers)
	call GetFarByte
	ld h, a
	pop af
	pop bc
	call BossAI_DamageKernel.Scale
	call BossAI_CapDamageStat
	pop de
	ld a, e
	and a
	jr nz, .done
	ld a, [wBattleMonStatus]
	bit BRN, a
	jr z, .done
	ld a, [wBattleMonType1]
	cp FIGHTING
	jr z, .fighting
	ld a, [wBattleMonType2]
	cp FIGHTING
	jr z, .fighting
	ld a, BRN_ATK_NUM
	ld h, BRN_ATK_DEN
	jr .burn
.fighting
	ld a, [wBattleMonType1]
	ld h, a
	ld a, [wBattleMonType2]
	cp h
	ld a, BRN_ATK_FIGHTING_HALF_NUM
	ld h, BRN_ATK_FIGHTING_HALF_DEN
	jr nz, .burn
	ld a, BRN_ATK_FIGHTING_FULL_NUM
	ld h, BRN_ATK_FIGHTING_FULL_DEN
.burn
	call BossAI_DamageKernel.Scale
.done
	pop hl
	pop de
	ret

BossAI_CapDamageStat:
	ld a, b
	cp HIGH(MAX_STAT_VALUE)
	ret c
	jr nz, .cap
	ld a, c
	cp LOW(MAX_STAT_VALUE)
	ret c
.cap
	ld bc, MAX_STAT_VALUE
	ret

; ai-layer: POLICY
BossAI_AddTableOffset::
; HL += A * BC modulo 65536; A=0, BC/DE preserved, flags clobbered.
; Large move/species/item indexes need at most eight binary steps. Small
; indexes retain the shorter linear path. No math scratch or banking needed.
; Including dispatch, binary becomes cheaper at index 10.
	cp 10
	jp c, AddNTimes
.binary
	push bc
.bit
	srl a
	jr nc, .next_bit
	add hl, bc
.next_bit
; ADD HL preserves the zero flag from SRL A. Stop before shifting the stride
; when the last index bit was consumed, including an index with its top bit set.
	jr z, .done
	sla c
	rl b
	jr .bit
.done
	pop bc
	ret

; ai-layer: POLICY
BossAI_PublicMovePriority::
; C=move, B=priority result; DE preserved. Priority needs no damage context.
	push bc
	ld a, c
	dec a
	ld hl, Moves + MOVE_EFFECT
	ld bc, MOVE_LENGTH
	call BossAI_AddTableOffset
	ld a, BANK(Moves)
	call GetFarByte
	pop bc
	ld b, a
.FromEffect
; B=already known effect, C=move. Used by the full hit-fact builder too.
	ld a, c
	cp VITAL_THROW
	jr z, .vital_throw
	ld c, b
	ld hl, MoveEffectPriorities
.priority_loop
	ld a, BANK(MoveEffectPriorities)
	call GetFarByte
	inc hl
	cp -1
	jr z, .default
	cp c
	jr z, .priority_found
	inc hl
	jr .priority_loop
.priority_found
	ld a, BANK(MoveEffectPriorities)
	call GetFarByte
	ld b, a
	ret
.default
	ld b, BASE_PRIORITY
	ret
.vital_throw
	ld b, 0
	ret

; ai-layer: POLICY
BossAI_IncomingAccuracy::
; A=owned slot, C=public reply, DE=AD scratch. Return C=accuracy byte.
; Initialize only the facts consumed by PublicHitFacts.accuracy; this is not a
; damage context. Accuracy needs no stat estimation, HP, survival or priority.
	ad_address AD_OWN_SLOT
	ld [hl], a
	ad_address AD_MOVE
	ld [hl], c
	xor a
	ad_address AD_DIRECTION
	ld [hl], a
	ad_address AD_FLAGS
	ld [hl], a
	ld hl, wEnemySubStatus1
	call BossAI_BuildPublicDamageContext.OwnState
	bit SUBSTATUS_IDENTIFIED, a
	jr z, .types
	ad_address AD_FLAGS
	set AD_IDENTIFIED_F, [hl]
.types
	ld a, [wBattleMonType1]
	ad_address AD_ATTACKER_TYPES
	ld [hli], a
	ld a, [wBattleMonType2]
	ld [hl], a
	ld a, [wBattleWeather]
	ad_address AD_WEATHER
	ld [hl], a
	ld a, MOVE_EFFECT
	call BossAI_BuildPublicDamageContext.MoveAttr
	ad_address AD_EFFECT
	ld [hl], a
	ld a, MOVE_ACC
	call BossAI_BuildPublicDamageContext.MoveAttr
	ad_address AD_ACCURACY
	ld [hl], a
	call BossAI_PublicHitFacts.accuracy
	ad_address AD_ACCURACY
	ld c, [hl]
	ret

; ai-layer: POLICY
BossAI_PublicHitFacts::
; DE=public context. Fill independent accuracy and priority metadata. Accuracy
; 255 means no accuracy roll; other values use /256. This does not include
; action denial or a FUTURE Protect/Endure choice. Separate per-hit fields give
; Psychic negation and known own Focus Band thresholds, each divided by 256.
; No RNG or live move-struct writes. Player item modifiers remain unknown.
	call .SurvivalFacts
	ad_address AD_MOVE
	ld c, [hl]
	ad_address AD_EFFECT
	ld b, [hl]
	call BossAI_PublicMovePriority.FromEffect
	ad_address AD_PRIORITY
	ld [hl], b
.accuracy
	call .BeforeStages
	ret nc
	jp .ApplyAccuracyModifiers
.BeforeStages
; Foresight and Lock-On are public persistent effects. Protect/Endure's
; transient flags are deliberately not treated as next-turn promises here.
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	jr z, .incoming
	ld hl, wEnemyAccLevel
	ld a, BASE_STAT_LEVEL
	call BossAI_BuildPublicDamageContext.OwnState
	ld b, a
	ld a, [wPlayerEvaLevel]
	ld c, a
	ld hl, wEnemySubStatus4
	xor a
	call BossAI_BuildPublicDamageContext.OwnState
	push af
	ld a, [wPlayerSubStatus5]
	ld h, a
	pop af
	ld l, a
	jr .sided
.incoming
	ld a, [wPlayerAccLevel]
	ld b, a
	ld hl, wEnemyEvaLevel
	ld a, BASE_STAT_LEVEL
	call BossAI_BuildPublicDamageContext.OwnState
	ld c, a
	ld hl, wEnemySubStatus5
	xor a
	call BossAI_BuildPublicDamageContext.OwnState
	ld h, a
	ld a, [wPlayerSubStatus4]
	ld l, a
.sided
	push hl ; target Lock-On / user X Accuracy flags
	ad_address AD_USER_ACC_STAGE
	ld [hl], b
	inc hl
	ld [hl], c
	call BossAI_BuildPublicDamageContext.TargetSubStatus3
	ld b, a
	pop hl
	bit SUBSTATUS_LOCK_ON, h
	jr z, .fly_dig
	bit SUBSTATUS_FLYING, b
	jr z, .certain
	push hl
	ad_address AD_MOVE
	ld a, [hl]
	pop hl
	cp EARTHQUAKE
	jr z, .fly_dig
	cp MAGNITUDE
	jr z, .fly_dig
	cp FISSURE
	jr nz, .certain
.fly_dig
	push hl
	ld a, b
	and 1 << SUBSTATUS_FLYING | 1 << SUBSTATUS_UNDERGROUND
	jr z, .can_hit
	ad_address AD_MOVE
	ld a, [hl]
	bit SUBSTATUS_FLYING, b
	jr z, .underground
	cp GUST
	jr z, .can_hit
	cp WHIRLWIND
	jr z, .can_hit
	cp THUNDER
	jr z, .can_hit
	cp TWISTER
	jr z, .can_hit
	jr .cannot_hit_pop
.underground
	cp EARTHQUAKE
	jr z, .can_hit
	cp FISSURE
	jr z, .can_hit
	cp MAGNITUDE
	jr nz, .cannot_hit_pop
.can_hit
	pop hl
	bit SUBSTATUS_X_ACCURACY, l
	jr nz, .certain
	ad_address AD_EFFECT
	ld a, [hl]
	cp EFFECT_ALWAYS_HIT
	jr z, .certain
	cp EFFECT_THUNDER
	jr nz, .stages
	ad_address AD_WEATHER
	ld a, [hl]
	cp WEATHER_RAIN
	jr z, .certain
	cp WEATHER_SUN
	jr nz, .stages
	ad_address AD_ACCURACY
	ld [hl], 50 percent + 1 ; ThunderAccuracy runs before CheckHit in combat
	jr .stages
.certain
	ad_address AD_ACCURACY
	ld [hl], $ff
	and a
	ret
.cannot_hit_pop
	pop hl
	ad_address AD_ACCURACY
	ld [hl], 0
	and a
	ret
.stages
	scf
	ret
.ApplyAccuracyModifiers
	ad_address AD_USER_ACC_STAGE
	ld b, [hl]
	inc hl
	ld a, [hl]
	cp b
	jr c, .apply_stages
	ad_address AD_FLAGS
	bit AD_IDENTIFIED_F, [hl]
	jr nz, .bright_powder
.apply_stages
	ad_address AD_ACCURACY
	ld b, 0
	ld c, [hl]
	ad_address AD_USER_ACC_STAGE
	ld a, [hl]
	call .AccuracyStage
	ad_address AD_TARGET_EVA_STAGE
	ld a, MAX_STAT_LEVEL + 1
	sub [hl]
	call .AccuracyStage
	call .ClampAccuracy
	ad_address AD_ACCURACY
	ld [hl], c
.bright_powder
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	jr nz, .flying
	call BossAI_BuildPublicDamageContext.HeldEffect
	ld a, b
	cp HELD_BRIGHTPOWDER
	jr nz, .flying
	ad_address AD_ACCURACY
	ld a, [hl]
	sub c
	jr nc, .powder_floor
	xor a
.powder_floor
	ld [hl], a
.flying
	ad_address AD_ACCURACY
	ld a, [hl]
	cp $ff
	ret z
	ld b, 0
	ld c, a
	ld a, FLYING
	call BossAI_DamageKernel.AttackerContribution
	and a
	ret z
	cp 2
	ld a, 26
	jr nz, .flying_scale
	ld a, 27
.flying_scale
	ld h, 25
	call BossAI_DamageKernel.Scale
	call BossAI_DamageKernel.MinOne
	call .ClampAccuracy
	ad_address AD_ACCURACY
	ld [hl], c
	ret
.AccuracyStage
	dec a
	cp MAX_STAT_LEVEL
	jr c, .valid_stage
	ld a, BASE_STAT_LEVEL - 1
.valid_stage
	push bc
	add a
	ld c, a
	ld b, 0
	ld hl, AccuracyLevelMultipliers
	add hl, bc
	ld a, BANK(AccuracyLevelMultipliers)
	call GetFarByte
	push af
	inc hl
	ld a, BANK(AccuracyLevelMultipliers)
	call GetFarByte
	ld h, a
	pop af
	pop bc
	jp BossAI_DamageKernel.Scale
.ClampAccuracy
	ld a, b
	and a
	ret z
	ld bc, $ff
	ret

.SurvivalFacts
; These are independent random outcomes after hit/damage calculation, not a
; discount to the conditional damage envelope. Unknown player items stay zero
; under the documented prior; callers must not interpret that as an item reveal.
	ad_address AD_NEGATION_CHANCE
	xor a
	ld [hli], a
	ld [hl], a
	ad_address AD_POWER
	ld a, [hl]
	and a
	ret z
	ld a, PSYCHIC_TYPE
	call BossAI_DamageKernel.DefenderContribution
	and a
	jr z, .focus_band
	cp 2
	ld a, 6
	jr nz, .negation
	ld a, 13
.negation
	ad_address AD_NEGATION_CHANCE
	ld [hl], a
.focus_band
	ad_address AD_DIRECTION
	ld a, [hl]
	and a
	ret nz
	call BossAI_BuildPublicDamageContext.HeldEffect
	ld a, b
	cp HELD_FOCUS_BAND
	ret nz
	ad_address AD_SURVIVAL_CHANCE
	ld [hl], c
	ret

; ai-layer: POLICY
BossAI_LoadDamageMoveAttributes::
; AD_MOVE is supplied; copy the four consecutive authoritative move bytes
; with one table offset and one bank switch pair. DE is preserved.
ASSERT MOVE_POWER == MOVE_EFFECT + 1
ASSERT MOVE_TYPE == MOVE_EFFECT + 2
ASSERT MOVE_ACC == MOVE_EFFECT + 3
ASSERT AD_POWER == 1 && AD_EFFECT == 2 && AD_TYPE == 3 && AD_CATEGORY == 4
	ad_address AD_MOVE
	ld a, [hl]
	dec a
	ld hl, Moves + MOVE_EFFECT
	ld bc, MOVE_LENGTH
	call BossAI_AddTableOffset
	push de
	inc de ; temporary effect/power/type/accuracy at AD_POWER..AD_CATEGORY
	ld bc, 4
	ld a, BANK(Moves)
	call FarCopyBytes
	pop de
	ad_address AD_POWER
	ld a, [hli]
	ld b, [hl]
	ld [hld], a
	ld [hl], b
	ad_address AD_TYPE
	ld a, [hli]
	ld b, [hl]
	ld [hl], a ; the initial category follows the Gen 2 type bucket
	ad_address AD_ACCURACY
	ld [hl], b
	ret
