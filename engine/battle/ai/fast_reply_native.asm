; Native compact reply compiler. It writes the same 48-byte record as
; BossAI_FastCompileReplyPlan (fast_reply_plans.asm) for an incoming move
; without running the public producers per reply: move facts come from
; in-bank mirrors of the authoritative tables, defender facts are prepared
; once per epoch from the producer templates, and the damage base for each
; category/power pair is cached. Every rule below is a transcription of the
; producer path it replaces (BuildPreparedIncoming, FinishPreparedIncoming,
; PublicHitFacts, the flag exports and the single-hit damage kernel); the
; differential fixture tools/boss_ai_fixtures/fast_reply_native.py holds it
; byte-for-byte against that path over every move.

; Per-defender facts, 32 bytes in the formerly uncommitted tail.
DEF FSN EQU $a5e0
DEF FSN_LEVEL EQU FSN + 0
DEF FSN_PLAYER_TYPES EQU FSN + 1 ; two bytes
DEF FSN_OWN_TYPES EQU FSN + 3 ; two bytes
DEF FSN_WEATHER EQU FSN + 5
DEF FSN_FLAGS EQU FSN + 6 ; template AD_FLAGS (status/identified/substitute/balloon)
DEF FSN_GUARDS EQU FSN + 7 ; bit0 bench Ditto, bit1 player transformed
DEF FSN_ACC_STAGE EQU FSN + 8 ; player accuracy stage
DEF FSN_EVA_STAGE EQU FSN + 9 ; own evasion stage
DEF FSN_OWN_SS5 EQU FSN + 10
DEF FSN_PLAYER_SS4 EQU FSN + 11
DEF FSN_OWN_SS3 EQU FSN + 12
DEF FSN_POWDER EQU FSN + 13 ; Bright Powder subtraction, 0 none
DEF FSN_FLYING EQU FSN + 14 ; 0, 26 or 27: Flying attacker accuracy numerator
DEF FSN_PSYCHIC EQU FSN + 15 ; own Psychic typing: a negation chance exists
DEF FSN_POISON EQU FSN + 16 ; own Poison typing: contact retaliation
DEF FSN_PLAYER_STATUS EQU FSN + 17
DEF FSN_PLAYER_SS3 EQU FSN + 18
DEF FSN_OWN_ITEM EQU FSN + 19
DEF FSN_HELMET EQU FSN + 20 ; two bytes, Helmet quota or 0
DEF FSN_OUTRAGE EQU FSN + 22 ; 1 when Outrage is physical for this player
DEF FSN_PHYS_ATTACK EQU FSN + 23 ; truncated low bytes for the formula
DEF FSN_PHYS_DEFENSE EQU FSN + 24
DEF FSN_SPEC_ATTACK EQU FSN + 25
DEF FSN_SPEC_DEFENSE EQU FSN + 26
DEF FSN_STEEL EQU FSN + 27
DEF FSN_MINIMIZED EQU FSN + 28
DEF FSN_OWN_STATUS EQU FSN + 29
DEF FSN_SWITCH EQU FSN + 30 ; 1 when the defender is a switch candidate (Pursuit)
DEF FSN_FOCUS EQU FSN + 31 ; known own Focus Band parameter (survival chance), 0 none
ASSERT FSN + 32 <= $a600
; Base+2 caches per category, indexed by power/5, zero = not computed.
; Physical: 36 words split across the base-state and group areas; special:
; 51 words in the dead outgoing/incoming template bytes (89..190), which the
; direct fallback evaluator never reads or writes.
DEF FSN_PHYS_CACHE_LOW EQU $a590 ; indices 0..23
DEF FSN_SPEC_CACHE EQU AV_PREPARED_OUT ; context-relative, indices 0..50
; Per-defender chart rows by attacking type: two 2-bit codes in chart order
; (low field first; 1 double, 2 halve, 3 no effect), then whether the
; attacker carries Dragon (no-effect rows halve instead for ordinary effects).
; Compact index: types below UNUSED_TYPES keep their value, later types drop
; the unused gap (CURSE_TYPE..DARK become 10..18).
DEF FSN_CHART EQU $a494 ; 19 bytes
DEF FSN_CHART_ENTRIES EQU TYPES_END - (UNUSED_TYPES_END - UNUSED_TYPES)
DEF FSN_MAJESTY EQU FSN_CHART + FSN_CHART_ENTRIES
ASSERT FSN_MAJESTY + 1 <= $a4a8 ; the regime cache follows ($a4a8..$a4b1)
; Packed type contributions the passives read per amount (two bits each,
; 0 none / 1 one of two types / 2 both): byte 0 own Dragon, Ground, Bug,
; Water; byte 1 own Ice, player Normal, Fire, Ghost.
DEF FSN_PASSIVES EQU $a4b2
ASSERT FSN_PASSIVES + 2 <= FSB_PREFIX
ASSERT FSN_PHYS_CACHE_LOW + 48 <= FSK_OWN
ASSERT FSN_SPEC_CACHE + 102 <= AV_PREPARED_IN_DAMAGE
; Compile scratch (pair scratch is not live while a reply compiles).
DEF FSM_EFFECT EQU $a560
DEF FSM_POWER EQU $a561
DEF FSM_TYPE EQU $a562
DEF FSM_ACCURACY EQU $a563
DEF FSM_CATEGORY EQU $a564 ; 0 physical, 1 special
DEF FSM_POSTROLL EQU $a565
DEF FSM_MAX_POSTROLL EQU $a566
DEF FSM_UNSUPPORTED EQU $a567
DEF FSM_MIN_HITS EQU $a568
DEF FSM_MAX_HITS EQU $a569
DEF FSM_FLAGS EQU $a56a ; AD_FLAGS for the current regime
DEF FSM_MATCHUP EQU $a56b
DEF FSM_AMOUNT EQU $a56c ; two bytes, working amount
DEF FSM_MIN EQU $a56e ; two bytes
DEF FSM_CONTACT EQU $a570
DEF FSM_MOVE EQU $a571
DEF FSM_MASK EQU $a572
DEF FSM_REGIME EQU $a573
DEF FSM_STRUGGLE EQU $a574
DEF FSM_NEGATION EQU $a575
DEF FSM_CHECK_FLAGS EQU $a576
DEF FSM_CAN_ACT EQU $a577
ASSERT FSM_CAN_ACT < $a578
; The header has consumed the check-flags byte before the amounts compile;
; the regime loop reuses it.
DEF FSM_REGIME_REPEAT EQU FSM_CHECK_FLAGS ; 1 when the remaining masked regimes re-store the first regime's amount
DEF FSM_TEMP EQU $a5d8 ; eight bytes
DEF FSM_OPCODE EQU FSM_TEMP + 5
DEF FSM_DELTAS EQU FSM_TEMP + 6 ; store per-regime max-min deltas
DEF FSM_HALVE EQU FSM_TEMP + 7 ; Selfdestruct: halved truncated defense
DEF FSM_VARIANT EQU FSM_TEMP + 4 ; own defensive variant slot+1 while an amount compiles against it, 0 none (the header's uncertainty temporary is dead by then)
ASSERT FSM_TEMP + 8 <= FSN

; In-bank mirrors. Bytes are the authoritative data files' bytes.
DEF BOSSAI_EMIT_LOCAL_MOVES EQU 1
INCLUDE "data/moves/moves.asm"
PURGE BOSSAI_EMIT_LOCAL_MOVES
DEF BOSSAI_EMIT_LOCAL_CONTACT_FLAGS EQU 1
INCLUDE "data/moves/contact_flags.asm"
PURGE BOSSAI_EMIT_LOCAL_CONTACT_FLAGS
DEF BOSSAI_EMIT_LOCAL_ACCURACY EQU 1
INCLUDE "data/battle/accuracy_multipliers.asm"
PURGE BOSSAI_EMIT_LOCAL_ACCURACY
; Effect classes: bit0 directly supported damage effect, bit1 HP-only script
; family, bits 2..3 the effect's move priority, bit4 an effect whose support
; needs the battle state (.EffectSupport's special cases). Built from the
; same lists the producers scan (.DirectEffects and .HPOnlyEffects in the
; public damage/action code) and data/moves/effects_priorities.asm; the
; differential fixture holds every move against the producer path.
MACRO fast_effect_class
	REDEF fast_effect_class_{d:\1} = fast_effect_class_{d:\1} | \2
ENDM
MACRO fast_effect_priority
	REDEF fast_effect_class_{d:\1} = (fast_effect_class_{d:\1} & ~%1100) | (\2 << 2)
ENDM
FOR fx, 256
	DEF fast_effect_class_{d:fx} = BASE_PRIORITY << 2
ENDR
	fast_effect_priority EFFECT_PROTECT, 3
	fast_effect_priority EFFECT_ENDURE, 3
	fast_effect_priority EFFECT_PRIORITY_HIT, 2
	fast_effect_priority EFFECT_FORCE_SWITCH, 0
	fast_effect_priority EFFECT_COUNTER, 0
	fast_effect_priority EFFECT_MIRROR_COAT, 0
	fast_effect_priority EFFECT_FOCUS_PUNCH, 0
	fast_effect_class EFFECT_MULTI_HIT, 16
	fast_effect_class EFFECT_DOUBLE_HIT, 16
	fast_effect_class EFFECT_POISON_MULTI_HIT, 16
	fast_effect_class EFFECT_SOLARBEAM, 16
	fast_effect_class EFFECT_DREAM_EATER, 16
	fast_effect_class EFFECT_SNORE, 16
	fast_effect_class EFFECT_EARTHQUAKE, 16
	fast_effect_class EFFECT_GUST, 16
	fast_effect_class EFFECT_TWISTER, 16
	fast_effect_class EFFECT_STOMP, 16
	fast_effect_class EFFECT_PURSUIT, 16
	fast_effect_class EFFECT_NORMAL_HIT, 1
	fast_effect_class EFFECT_POISON_HIT, 1
	fast_effect_class EFFECT_LEECH_HIT, 1
	fast_effect_class EFFECT_BURN_HIT, 1
	fast_effect_class EFFECT_FREEZE_HIT, 1
	fast_effect_class EFFECT_PARALYZE_HIT, 1
	fast_effect_class EFFECT_SELFDESTRUCT, 1
	fast_effect_class EFFECT_ALWAYS_HIT, 1
	fast_effect_class EFFECT_RAMPAGE, 1
	fast_effect_class EFFECT_FLINCH_HIT, 1
	fast_effect_class EFFECT_PAY_DAY, 1
	fast_effect_class EFFECT_TRI_ATTACK, 1
	fast_effect_class EFFECT_SUPER_FANG, 1
	fast_effect_class EFFECT_STATIC_DAMAGE, 1
	fast_effect_class EFFECT_TRAP_TARGET, 1
	fast_effect_class EFFECT_JUMP_KICK, 1
	fast_effect_class EFFECT_RECOIL_HIT, 1
	fast_effect_class EFFECT_ATTACK_DOWN_HIT, 1
	fast_effect_class EFFECT_DEFENSE_DOWN_HIT, 1
	fast_effect_class EFFECT_SPEED_DOWN_HIT, 1
	fast_effect_class EFFECT_SP_ATK_DOWN_HIT, 1
	fast_effect_class EFFECT_SP_DEF_DOWN_HIT, 1
	fast_effect_class EFFECT_ACCURACY_DOWN_HIT, 1
	fast_effect_class EFFECT_EVASION_DOWN_HIT, 1
	fast_effect_class EFFECT_CONFUSE_HIT, 1
	fast_effect_class EFFECT_HYPER_BEAM, 1
	fast_effect_class EFFECT_RAGE, 1
	fast_effect_class EFFECT_LEVEL_DAMAGE, 1
	fast_effect_class EFFECT_DEFROST_OPPONENT, 1
	fast_effect_class EFFECT_FALSE_SWIPE, 1
	fast_effect_class EFFECT_PRIORITY_HIT, 1
	fast_effect_class EFFECT_THIEF, 1
	fast_effect_class EFFECT_FLAME_WHEEL, 1
	fast_effect_class EFFECT_SACRED_FIRE, 1
	fast_effect_class EFFECT_RAPID_SPIN, 1
	fast_effect_class EFFECT_DEFENSE_UP_HIT, 1
	fast_effect_class EFFECT_ATTACK_UP_HIT, 1
	fast_effect_class EFFECT_ALL_UP_HIT, 1
	fast_effect_class EFFECT_THUNDER, 1
	fast_effect_class EFFECT_NORMAL_HIT, 2
	fast_effect_class EFFECT_ALWAYS_HIT, 2
	fast_effect_class EFFECT_STATIC_DAMAGE, 2
	fast_effect_class EFFECT_LEVEL_DAMAGE, 2
	fast_effect_class EFFECT_SUPER_FANG, 2
	fast_effect_class EFFECT_FALSE_SWIPE, 2
	fast_effect_class EFFECT_SELFDESTRUCT, 2
	fast_effect_class EFFECT_RECOIL_HIT, 2
	fast_effect_class EFFECT_LEECH_HIT, 2
	fast_effect_class EFFECT_DREAM_EATER, 2
	fast_effect_class EFFECT_MULTI_HIT, 2
	fast_effect_class EFFECT_DOUBLE_HIT, 2
	fast_effect_class EFFECT_EARTHQUAKE, 2
	fast_effect_class EFFECT_GUST, 2
	fast_effect_class EFFECT_PURSUIT, 2
	fast_effect_class EFFECT_PAY_DAY, 2
	fast_effect_class EFFECT_PRIORITY_HIT, 2
BossAI_FastEffectClass:
FOR fx, 256
	db fast_effect_class_{d:fx}
ENDR
PURGE fast_effect_class
PURGE fast_effect_priority

BossAI_FastTypeContribution::
; A=type, HL=type pair. A=0 none, 1 one of two distinct types, 2 both.
; BC/DE preserved (callers keep the running amount in BC). The hot copy of
; BossAI_FastPrepareReplyFacts.Contribution for the per-amount STAB test.
	push bc
	ld b, a
	ld a, [hli]
	ld c, a
	ld a, [hl]
	cp c
	jr nz, .dual
	cp b
	ld a, 0
	jr nz, .contribution_done
	ld a, 2
	jr .contribution_done
.dual
	cp b
	jr z, .half
	ld a, c
	cp b
	ld a, 0
	jr nz, .contribution_done
.half
	ld a, 1
.contribution_done
	pop bc
	ret

BossAI_FastCompileReplyNative::
; DE=context, C=regime mask, A=reply move ID (nonzero). FSN prepared for
; this defender. Writes the 48-byte record at FSR_BASE exactly as
; BossAI_FastCompileReplyPlan would (opcode0 records keep their header).
; Carry=represented (damage/recovery/Pursuit opcode). SRAM0 open; DE/SP
; preserved; AF/BC/HL scratch. Uses only compile scratch, the caches and
; FSM_TEMP; no producer prefix byte other than the special cache changes.
	ld [FSM_MOVE], a
	ld a, c
	ld [FSM_MASK], a
	ld hl, FSR_BASE
	add hl, de
	xor a
	rept FSR_SIZE
	ld [hli], a
	endr
; move facts from the mirror
	ld a, [FSM_MOVE]
	dec a
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl ; 4*(move-1): the mirror keeps effect, power, type, accuracy
	ld bc, BossAI_FastMoves
	add hl, bc
	ld a, [hli]
	ld [FSM_EFFECT], a
	ld a, [hli]
	ld [FSM_POWER], a
	ld a, [hli]
	ld [FSM_TYPE], a
	ld a, [hl]
	ld [FSM_ACCURACY], a
	ld a, [FSM_MOVE]
	dec a
	ld c, a
	ld b, 0
	ld hl, BossAI_FastMoveContactFlags
	add hl, bc
	ld a, [hl]
	ld [FSM_CONTACT], a
; category: type bucket, with Outrage's public override
	ld a, [FSM_TYPE]
	cp SPECIAL
	ld a, 0
	jr c, .category_ready
	inc a
	ld b, a
	ld a, [FSM_MOVE]
	cp OUTRAGE
	ld a, b
	jr nz, .category_ready
	ld a, [FSN_OUTRAGE]
	xor 1
.category_ready
	ld [FSM_CATEGORY], a
; defaults, then effect support (BuildPublicDamageContext.EffectSupport)
	ld a, 1
	ld [FSM_POSTROLL], a
	ld [FSM_MAX_POSTROLL], a
	ld [FSM_MIN_HITS], a
	ld [FSM_MAX_HITS], a
	xor a
	ld [FSM_STRUGGLE], a
	ld [FSM_CHECK_FLAGS], a
	ld a, [FSN_GUARDS]
	and 1
	ld [FSM_UNSUPPORTED], a
	call .EffectSupport
; ValuePublicExchange.MoveReplyPursuit: an explicit opposing Pursuit is not a
; switch punish, so its maximum multiplier is normalized to the minimum's.
	ld a, [FSM_EFFECT]
	cp EFFECT_PURSUIT
	jr nz, .pursuit_normalized
	ld a, [FSM_POSTROLL]
	ld [FSM_MAX_POSTROLL], a
.pursuit_normalized
	call .MultiHitItemState
; a multi-hit attack against a substitute stays unknown
	ld a, [FSN_FLAGS]
	bit AD_SUBSTITUTE_F, a
	jr z, .support_ready
	ld a, [FSM_MAX_HITS]
	cp 2
	jr c, .support_ready
	ld a, 1
	ld [FSM_UNSUPPORTED], a
.support_ready
; copyguards: a transformed player keeps only constant damage
	ld a, [FSN_GUARDS]
	and 2
	jr z, .guards_ready
	ld a, [FSM_EFFECT]
	cp EFFECT_STATIC_DAMAGE
	jr z, .guards_ready
	cp EFFECT_LEVEL_DAMAGE
	jr z, .guards_ready
	cp EFFECT_SUPER_FANG
	jr z, .guards_ready
	ld a, 1
	ld [FSM_UNSUPPORTED], a
.guards_ready
; survival facts: a damaging move into a Psychic defender or a known Focus
; Band leaves an independent survival roll, which makes even a certain hit
; uncertain
	xor a
	ld [FSM_NEGATION], a
	ld a, [FSM_POWER]
	and a
	jr z, .negation_ready
	ld a, [FSN_PSYCHIC]
	ld b, a
	ld a, [FSN_FOCUS]
	or b
	ld [FSM_NEGATION], a
.negation_ready
	call .Accuracy
	call .PlayerCanAct
; header
	call .Priority
	ld [FSM_TEMP + 3], a
	call .EffectUncertainty
	ld b, a
	call .HitUncertainty
	or b
	ld [FSM_TEMP + 4], a
	ld hl, FSR_BASE + FSR_MOVE
	add hl, de
	ld a, [FSM_MOVE]
	ld [hli], a
	inc hl
	ld a, [FSM_ACCURACY]
	ld [hli], a
	ld a, [FSM_TEMP + 3]
	ld [hli], a
	ld a, [FSM_CAN_ACT]
	ld [hli], a
	ld a, [FSM_CHECK_FLAGS]
	ld [hli], a
	ld a, [FSM_TEMP + 4]
	ld [hl], a
	ld hl, FSR_BASE + FSR_MIN_HITS
	add hl, de
	ld a, [FSM_MIN_HITS]
	ld [hli], a
	ld a, [FSM_MAX_HITS]
	ld [hl], a
; opcode
	ld a, [FSN_SWITCH]
	and a
	jr z, .ordinary
	ld a, [FSM_EFFECT]
	cp EFFECT_PURSUIT
	jr nz, .ordinary
	ld a, FSR_PURSUIT
	jr .store_opcode
.ordinary
	ld a, [FSM_MOVE]
	ld bc, $0101 ; ValuePublicExchange.DefenseAxis: B=stages, C=axis
	cp HARDEN
	jr z, .boost
	cp WITHDRAW
	jr z, .boost
	inc b
	cp BARRIER
	jr z, .boost
	cp ACID_ARMOR
	jr z, .boost
	ld c, 4
	cp AMNESIA
	jr z, .boost
	call .RecoveryQuota
	jr nc, .damage
	ld hl, FSR_BASE + FSR_RECOVERY_QUOTA
	add hl, de
	ld [hl], b
	inc hl
	ld [hl], c
	ld a, FSR_RECOVERY
.store_opcode
	ld hl, FSR_BASE + FSR_OPCODE
	add hl, de
	ld [hl], a
	and a
	ret z ; unrepresented after all: header written, fallback follows
	scf
	ret
.boost
	ld hl, FSR_BASE + FSR_BOOST_STEPS
	add hl, de
	ld [hl], b
	inc hl
	ld [hl], c
	ld hl, FSR_BASE + FSR_DAMAGE_FLAGS
	add hl, de
	ld [hl], 0
	ld a, FSR_BOOST
	jr .store_opcode
.damage
	ld a, FSR_DAMAGE
	ld [FSM_OPCODE], a
	xor a
	ld [FSM_DELTAS], a
	ld [FSM_HALVE], a
	ld [FSM_VARIANT], a
	ld a, [FSM_EFFECT]
	cp EFFECT_SELFDESTRUCT
	jr nz, .not_selfdestruct
	ld a, FSR_SELFDESTRUCT
	ld [FSM_OPCODE], a
	ld a, 1
	ld [FSM_HALVE], a
	jr .family_ready
.not_selfdestruct
	cp EFFECT_SUPER_FANG
	jr nz, .not_fang
	ld a, FSR_FANG
	ld [FSM_OPCODE], a
	jr .family_ready
.not_fang
	cp EFFECT_FALSE_SWIPE
	jr nz, .not_false_swipe
	ld a, FSR_FALSE_SWIPE
	ld [FSM_OPCODE], a
	ld a, 1
	ld [FSM_DELTAS], a
	jr .family_ready
.not_false_swipe
	ld a, [FSM_MIN_HITS]
	dec a
	jr nz, .multi_family
	ld a, [FSM_MAX_HITS]
	dec a
	jr z, .family_ready
.multi_family
	ld a, FSR_MULTI
	ld [FSM_OPCODE], a
	ld a, 1
	ld [FSM_DELTAS], a
	ld a, 15
	ld [FSM_MASK], a
.family_ready
	ld hl, FSR_BASE + FSR_STEEL
	add hl, de
	ld a, [FSN_STEEL]
	ld [hl], a
	ld hl, FSR_BASE + FSR_POWER
	add hl, de
	ld a, [FSM_POWER]
	ld [hl], a
	call .Descriptor
	ld hl, FSR_BASE + FSR_HP_DEPEND
	add hl, de
	ld a, [FSM_DELTAS]
	and a
	jr nz, .hp_depend_ready ; byte 8 carries the regime-1 delta instead
	ld [hl], 3
.hp_depend_ready
	inc hl
	ld a, [FSM_MASK]
	ld [hl], a
	ld a, [FSM_POWER]
	ld c, a
	ld b, 0
	ld h, b
	ld l, c
	add hl, hl
	add hl, bc
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, bc
	add hl, hl
	add hl, bc
	add hl, hl
	add hl, hl
	add hl, bc ; 205*power
	ld a, h
	srl a
	srl a ; power/5, the base cache index
	ld [FSM_TEMP + 2], a
	xor a
	ld [FSM_REGIME], a
	ld a, [FSM_MASK]
	ld [FSM_TEMP + 3], a
	and a
	jr z, .regimes_done
.first_regime
	ld hl, FSM_TEMP + 3
	srl [hl]
	jr c, .first_masked
	ld hl, FSM_REGIME
	inc [hl]
	jr .first_regime
.first_masked
	call .Amount
	jr nc, .first_unknown
	ld a, [FSM_TEMP + 3]
	and a
	jr z, .regimes_done ; the usual single regime
; The regime bits reach an amount only through the Fire passive (attacker
; low: a Fire reply against a player Fire contribution) and the Ice passive
; (defender high: an own Ice contribution); otherwise the remaining masked
; regimes re-store this amount.
	ld a, [FSN_PASSIVES + 1]
	ld l, a
	and %11
	ld h, 0
	jr nz, .repeat_rule
	ld a, [FSM_TYPE]
	cp FIRE
	jr nz, .repeat_all
	ld a, l
	and %110000
	jr nz, .repeat_rule
.repeat_all
	inc h
.repeat_rule
	ld a, h ; BC still holds the amount the repeats re-store
	jr .repeat_ready
.first_unknown
	xor a ; unknown at every regime: each remaining regime asks .Amount, cheaply
.repeat_ready
	ld [FSM_REGIME_REPEAT], a
.regime
	ld a, [FSM_TEMP + 3]
	and a
	jr z, .regimes_done ; no masked regime remains
	ld hl, FSM_REGIME
	inc [hl]
	ld hl, FSM_TEMP + 3
	srl [hl]
	jr nc, .regime
	ld a, [FSM_REGIME_REPEAT]
	and a
	jr nz, .repeat_amount
	call .Amount
	jr .regime
.repeat_amount
	call .store ; BC and FSM_MIN still hold the previous regime's amount
	jr .regime
.regimes_done
	ld a, [FSM_OPCODE]
	jp .store_opcode
.Bits
	db 1, 2, 4, 8
.MinDeltaOffsets
	db FSR_MIN_DELTA0, FSR_MIN_DELTA1, FSR_MIN_DELTA2, FSR_MIN_DELTA3

.EffectSupport
; BuildPublicDamageContext.EffectSupport for the incoming direction.
	ld a, [FSM_MOVE]
	cp STRUGGLE
	jr nz, .effect
	ld a, 1
	ld [FSM_STRUGGLE], a
	ret
.effect
	ld a, [FSM_EFFECT]
	ld l, a
	ld h, 0
	ld bc, BossAI_FastEffectClass
	add hl, bc
	bit 4, [hl]
	jr nz, .special_effect
	bit 0, [hl]
	ret nz
	jp .unsupported
.special_effect
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
	jr z, .pursuit
	bit 0, [hl]
	ret nz
	jr .unsupported
.double
	ld a, 2
	ld [FSM_MIN_HITS], a
	ld [FSM_MAX_HITS], a
	ret
.multi
	ld a, 2
	ld [FSM_MIN_HITS], a
	ld a, 5
	ld [FSM_MAX_HITS], a
	ret
.solar
	ld a, [FSN_WEATHER]
	cp WEATHER_SUN
	ret z
	ld a, [FSN_PLAYER_SS3]
	bit SUBSTATUS_CHARGED, a
	ret nz
	jr .unsupported
.dream
	ld a, [FSN_OWN_STATUS]
	jr .sleeping
.snore
	ld a, [FSN_PLAYER_STATUS]
.sleeping
	and SLP_MASK
	ret nz
	jr .unsupported
.grounded_attack
	ld a, [FSN_OWN_SS3]
	bit SUBSTATUS_UNDERGROUND, a
	ret z
	jr .double_postroll
.flying_attack
	ld a, [FSN_OWN_SS3]
	bit SUBSTATUS_FLYING, a
	ret z
	jr .double_postroll
.stomp
	ld a, [FSN_MINIMIZED]
	and a
	ret z
.double_postroll
	ld a, 2
	ld [FSM_POSTROLL], a
	ld [FSM_MAX_POSTROLL], a
	ret
.pursuit
	ld a, 2
	ld [FSM_MAX_POSTROLL], a
	ret
.unsupported
	ld a, 1
	ld [FSM_UNSUPPORTED], a
	ret
.MultiHitItemState
; A known Rocky Helmet on the defender makes a contact multi-hit unknown.
	ld a, [FSM_MAX_HITS]
	cp 2
	ret c
	ld a, [FSN_OWN_ITEM]
	cp ROCKY_HELMET
	ret nz
	ld a, [FSM_CONTACT]
	and a
	ret z
	ld a, 1
	ld [FSM_UNSUPPORTED], a
	ret

.Accuracy
; PublicHitFacts.BeforeStages and ApplyAccuracyModifiers, incoming side.
	ld a, [FSN_OWN_SS5]
	bit SUBSTATUS_LOCK_ON, a
	jr z, .fly_dig
	ld a, [FSN_OWN_SS3]
	bit SUBSTATUS_FLYING, a
	jr z, .certain
	ld a, [FSM_MOVE]
	cp EARTHQUAKE
	jr z, .fly_dig
	cp MAGNITUDE
	jr z, .fly_dig
	cp FISSURE
	jr nz, .certain
.fly_dig
	ld a, [FSN_OWN_SS3]
	and 1 << SUBSTATUS_FLYING | 1 << SUBSTATUS_UNDERGROUND
	jr z, .can_hit
	ld b, a
	ld a, [FSM_MOVE]
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
	jr .cannot_hit
.underground
	cp EARTHQUAKE
	jr z, .can_hit
	cp FISSURE
	jr z, .can_hit
	cp MAGNITUDE
	jr nz, .cannot_hit
.can_hit
	ld a, [FSN_PLAYER_SS4]
	bit SUBSTATUS_X_ACCURACY, a
	jr nz, .certain
	ld a, [FSM_EFFECT]
	cp EFFECT_ALWAYS_HIT
	jr z, .certain
	cp EFFECT_THUNDER
	jr nz, .stages
	ld a, [FSN_WEATHER]
	cp WEATHER_RAIN
	jr z, .certain
	cp WEATHER_SUN
	jr nz, .stages
	ld a, 50 percent + 1
	ld [FSM_ACCURACY], a
	jr .stages
.certain
	ld a, $ff
	ld [FSM_ACCURACY], a
	ret
.cannot_hit
	xor a
	ld [FSM_ACCURACY], a
	ret
.stages
	ld a, [FSN_ACC_STAGE]
	ld b, a
	ld a, [FSN_EVA_STAGE]
	cp b
	jr c, .apply_stages
	ld a, [FSN_FLAGS]
	bit AD_IDENTIFIED_F, a
	jr nz, .bright_powder
.apply_stages
	ld a, [FSN_ACC_STAGE]
	cp BASE_STAT_LEVEL
	jr nz, .scale_stages
	ld a, [FSN_EVA_STAGE]
	cp BASE_STAT_LEVEL
	jr z, .bright_powder ; both neutral: the stage ratios are identities
.scale_stages
	ld a, [FSM_ACCURACY]
	ld c, a
	ld b, 0
	ld a, [FSN_ACC_STAGE]
	call .AccuracyStage
	ld a, [FSN_EVA_STAGE]
	ld l, a
	ld a, MAX_STAT_LEVEL + 1
	sub l
	call .AccuracyStage
	call .ClampAccuracy
	ld a, c
	ld [FSM_ACCURACY], a
.bright_powder
	ld a, [FSN_POWDER]
	ld c, a
	ld a, [FSM_ACCURACY]
	sub c
	jr nc, .powder_floor
	xor a
.powder_floor
	ld [FSM_ACCURACY], a
	cp $ff
	ret z
	ld c, a
	ld b, 0
	ld a, [FSN_FLYING]
	and a
	ret z
	ld h, 25
	call .Scale
	call .MinOne
	call .ClampAccuracy
	ld a, c
	ld [FSM_ACCURACY], a
	ret
.AccuracyStage
; A=stage, BC=accuracy. BC scaled by the stage's ratio.
	dec a
	cp MAX_STAT_LEVEL
	jr c, .valid_stage
	ld a, BASE_STAT_LEVEL - 1
.valid_stage
	add a
	ld l, a
	ld h, 0
	push bc
	ld bc, BossAI_FastAccuracyLevelMultipliers
	add hl, bc
	pop bc
	ld a, [hli]
	ld h, [hl]
	jp .Scale
.ClampAccuracy
	ld a, b
	and a
	ret z
	ld bc, $ff
	ret

.PlayerCanAct
; ValuePublicExchange.PlayerCanAct: FSM_CAN_ACT and FSM_CHECK_FLAGS.
	xor a
	ld [FSM_CAN_ACT], a
	ld a, [FSN_PLAYER_SS4]
	bit SUBSTATUS_RECHARGE, a
	ret nz
	ld a, [FSN_PLAYER_SS3]
	bit SUBSTATUS_FLINCHED, a
	ret nz
	bit SUBSTATUS_CONFUSED, a
	call nz, .TransitionFlag
	ld a, [FSN_PLAYER_STATUS]
	bit PAR, a
	call nz, .TransitionFlag
	ld a, [FSN_PLAYER_STATUS]
	and SLP_MASK
	jr z, .not_sleeping
	cp 1
	jr z, .sleep_wake
	ld a, [FSM_MOVE]
	cp SNORE
	jr z, .can_act
	cp SLEEP_TALK
	ret nz
	call .TransitionFlag
	jr .can_act
.sleep_wake
	call .TransitionFlag
	ld a, [FSM_MOVE]
	cp SNORE
	ret z
	cp SLEEP_TALK
	ret z
	jr .can_act
.not_sleeping
	ld a, [FSN_PLAYER_STATUS]
	bit FRZ, a
	jr z, .can_act
	ld a, [FSM_MOVE]
	cp FLAME_WHEEL
	jr z, .thaw
	cp SACRED_FIRE
	ret nz
.thaw
	call .TransitionFlag
.can_act
	ld a, 1
	ld [FSM_CAN_ACT], a
	ret
.TransitionFlag
	ld a, [FSM_CHECK_FLAGS]
	or 1 << AV_UNKNOWN_TRANSITION_F
	ld [FSM_CHECK_FLAGS], a
	ret

.Priority
; A=priority (PublicMovePriority.FromEffect).
	ld a, [FSM_MOVE]
	cp VITAL_THROW
	ld a, 0
	ret z
	ld a, [FSM_EFFECT]
	ld l, a
	ld h, 0
	ld bc, BossAI_FastEffectClass
	add hl, bc
	ld a, [hl]
	rrca
	rrca
	and 3
	ret

.EffectUncertainty
; A=transition flag when the effect is not HP-only, or when a contact move
; meets a Poison defender.
	ld a, [FSM_EFFECT]
	ld l, a
	ld h, 0
	ld bc, BossAI_FastEffectClass
	add hl, bc
	bit 1, [hl]
	jr z, .transition
	ld a, [FSN_POISON]
	and a
	jr z, .no_effect_flag
	ld a, [FSM_CONTACT]
	and a
	jr nz, .transition
.no_effect_flag
	xor a
	ret
.transition
	ld a, 1 << AV_UNKNOWN_TRANSITION_F
	ret
.HitUncertainty
; A=hit flag: any roll, or a certain hit that negation or a substitute can
; still deny.
	ld a, [FSM_ACCURACY]
	and a
	ret z
	cp 255
	jr nz, .uncertain_hit
	ld a, [FSM_NEGATION]
	and a
	jr nz, .uncertain_hit
	ld a, [FSN_FLAGS]
	bit AD_SUBSTITUTE_F, a
	jr nz, .uncertain_hit
	xor a
	ret
.uncertain_hit
	ld a, 1 << AV_UNKNOWN_HIT_F
	ret

.RecoveryQuota
; BC=uncapped quota, carry=recognized (BossAI_FastRecoveryQuota with the
; player's maximum HP).
	ld a, [FSM_EFFECT]
	cp EFFECT_HEAL
	jr z, .ordinary_heal
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
.ordinary_heal
	ld a, [FSM_MOVE]
	cp REST
	ld a, 0
	jr z, .fraction
	inc a
	jr .fraction
.time
	ld c, 2
	ld a, [wLinkMode]
	and a
	jr nz, .weather_fraction
	ld a, [wTimeOfDay]
	cp b
	jr z, .weather_fraction
	dec c
.weather_fraction
	ld a, [FSN_WEATHER]
	and a
	jr z, .time_fraction
	inc c
	cp WEATHER_SUN
	jr z, .time_fraction
	dec c
	dec c
.time_fraction
	ld a, 3
	sub c
.fraction
	push af
	ld a, [FSA_PLAYER + 2]
	ld b, a
	ld a, [FSA_PLAYER + 3]
	ld c, a
	or b
	jr z, .zero_quota
	pop af
	and a
	jr z, .quota_ready
.shift
	srl b
	rr c
	dec a
	jr nz, .shift
	ld a, b
	or c
	jr nz, .quota_ready
	inc c
.quota_ready
	scf
	ret
.zero_quota
	pop af
	scf
	ret

.Descriptor
; Item tag 1 for a known contact Helmet without a substitute, effect tag for
; drain/recoil; same descriptor table as the sequential executors.
	ld c, 0
	ld a, [FSN_OWN_ITEM]
	cp ROCKY_HELMET
	jr nz, .effect_tag
	ld a, [FSN_FLAGS]
	bit AD_SUBSTITUTE_F, a
	jr nz, .effect_tag
	ld a, [FSM_CONTACT]
	and a
	jr z, .effect_tag
	ld hl, FSR_BASE + FSR_ITEM_QUOTA
	add hl, de
	ld a, [FSN_HELMET]
	ld [hli], a
	ld a, [FSN_HELMET + 1]
	ld [hl], a
	ld c, 1
.effect_tag
	ld a, [FSM_EFFECT]
	cp EFFECT_LEECH_HIT
	jr z, .drain
	cp EFFECT_DREAM_EATER
	jr z, .drain
	cp EFFECT_RECOIL_HIT
	jr nz, .descriptor
	ld a, c
	add 6
	ld c, a
	jr .descriptor
.drain
	ld a, c
	add 3
	ld c, a
.descriptor
	sla c
	ld b, 0
	ld hl, BossAI_FastOwnCommandDescriptors
	add hl, bc
	ld b, h
	ld c, l
	ld hl, FSR_BASE + FSR_DESCRIPTOR
	add hl, de
	ld [hl], b
	inc hl
	ld [hl], c
	ret

.Amount
; One regime: RAW_MAX, plus the regime's range and support bits, from the
; single-hit kernel path with a cached formula base. Carry=stored (BC=raw
; maximum, FSM_MIN=raw minimum); clear when unsupported or without power.
	ld a, [FSM_REGIME]
	add a
	and (1 << AD_ATTACKER_LOW_F) | (1 << AD_DEFENDER_HIGH_F)
	ld b, a
	ld a, [FSN_FLAGS]
	or b
	ld [FSM_FLAGS], a
	ld a, [FSM_UNSUPPORTED]
	and a
	jr nz, .unknown
	ld a, [FSM_POWER]
	and a
	jr nz, .known_power
.unknown
	ret ; raw stays zero; no range/support bits
.known_power
	ld bc, EFFECTIVE
	call .Chart
	ld a, c
	ld [FSM_MATCHUP], a
	ld a, b
	or c
	jp z, .fixed ; immune: supported zero
	ld a, [FSN_FLAGS]
	bit AD_BALLOON_F, a
	jr z, .check_fixed
	ld a, [FSM_TYPE]
	cp GROUND
	jr nz, .check_fixed
	ld bc, 0
	jp .fixed
.check_fixed
	ld a, [FSM_EFFECT]
	cp EFFECT_STATIC_DAMAGE
	jr z, .static
	cp EFFECT_LEVEL_DAMAGE
	jr z, .level
	cp EFFECT_SUPER_FANG
	jr z, .fang
	call .Base
	ld a, [FSM_STRUGGLE]
	and a
	jr nz, .variation
	call .Weather
	ld a, [FSM_TYPE]
	ld hl, FSN_PLAYER_TYPES
	call BossAI_FastTypeContribution
	and a
	jr z, .no_stab
	ld a, 3
	ld h, 2
	call .Scale
.no_stab
	call .Chart
	call .Passives
.variation
; minimum endpoint: roll 217/255 then the post-roll multiplier; the maximum
; keeps the pre-roll amount then the post-roll multiplier
	ld a, b
	ld [FSM_AMOUNT], a
	ld a, c
	ld [FSM_AMOUNT + 1], a
	ld a, 217
	ld h, 255
	call .Scale
	ld a, [FSM_POSTROLL]
	ld h, 1
	call .Scale
	ld a, b
	ld [FSM_MIN], a
	ld a, c
	ld [FSM_MIN + 1], a
	ld a, [FSM_AMOUNT]
	ld b, a
	ld a, [FSM_AMOUNT + 1]
	ld c, a
	ld a, [FSM_MAX_POSTROLL]
	ld h, 1
	call .Scale
	jr .store
.static
	ld a, [FSM_POWER]
	jr .fixed_byte
.level
	ld a, [FSN_LEVEL]
.fixed_byte
	ld c, a
	ld b, 0
	jr .fixed
.fang
; the kernel halves the template's defender HP (minimum one); the executor
; recomputes from the real HP and treats a zero here as immunity
	ad_address AV_PREPARED_ACTOR + AD_DEFENDER_HP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	srl b
	rr c
	call .MinOne
.fixed
	ld a, b
	ld [FSM_MIN], a
	ld a, c
	ld [FSM_MIN + 1], a
.store
; BC=raw maximum, FSM_MIN=raw minimum; both supported. BC preserved; carry set.
	ld a, [FSM_VARIANT]
	and a
	jp nz, .StoreVariant
	push bc
	ld a, [FSM_REGIME]
	add a
	ld c, a
	ld b, 0
	ld hl, FSR_BASE + FSR_RAW_MAX
	add hl, de
	add hl, bc
	pop bc
	ld [hl], b
	inc hl
	ld [hl], c
	push bc
	ld a, [FSM_REGIME]
	ld c, a
	ld b, 0
	ld hl, .Bits
	add hl, bc
	ld a, [hl]
	ld [FSM_TEMP], a
	pop bc
	ld hl, FSR_BASE + FSR_SUPPORT
	add hl, de
	or [hl]
	ld [hl], a
	ld a, [FSM_DELTAS]
	and a
	jr z, .no_delta
	push bc
	ld a, [FSM_REGIME]
	ld c, a
	ld b, 0
	ld hl, .MinDeltaOffsets
	add hl, bc
	ld c, [hl]
	ld hl, FSR_BASE
	add hl, bc
	add hl, de
	pop bc
	push bc
	push hl
	ld hl, FSM_MIN + 1
	ld a, c
	sub [hl]
	dec hl
	ld c, a
	ld a, b
	sbc [hl]
	pop hl
	ld [hl], c
	pop bc
	jr z, .no_delta
	xor a
	ld [FSM_OPCODE], a ; a delta wider than a byte leaves the reply to the fallback
.no_delta
	ld a, [FSM_MIN]
	cp b
	jr nz, .range
	ld a, [FSM_MIN + 1]
	cp c
	jr nz, .range
	scf
	ret
.range
	ld a, [FSM_TEMP]
	ld hl, FSR_BASE + FSR_RANGE
	add hl, de
	or [hl]
	ld [hl], a
	scf
	ret
.StoreVariant
; BC=raw maximum at the raised own defense, FSM_MIN=its minimum. The word goes
; to the record offset in FSM_TEMP+3; the slot's valid bit, plus its range bit
; when the endpoints differ, into FSR_VARIANT_FLAGS.
	ld a, [FSM_TEMP + 3]
	add LOW(FSR_BASE)
	ld l, a
	ld a, 0
	adc HIGH(FSR_BASE)
	ld h, a
	add hl, de
	ld [hl], b
	inc hl
	ld [hl], c
	ld a, [FSM_VARIANT]
	dec a
	add a
	ld l, a ; 2*slot: the valid bit's index
	ld a, 1
	jr z, .variant_bit_ready
.variant_bit
	add a
	dec l
	jr nz, .variant_bit
.variant_bit_ready
	ld l, a
	ld a, [FSM_MIN]
	cp b
	jr nz, .variant_range
	ld a, [FSM_MIN + 1]
	cp c
	jr z, .variant_flags
.variant_range
	ld a, l
	add a
	or l
	ld l, a
.variant_flags
	ld a, l
	ld hl, FSR_BASE + FSR_VARIANT_FLAGS
	add hl, de
	or [hl]
	ld [hl], a
	ret
.Base
; BC=capped formula base plus two for this category and power, from the
; cache when present. Selfdestruct's halved defense and the own defensive
; variants are never cached.
	ld a, [FSM_HALVE]
	ld b, a
	ld a, [FSM_VARIANT]
	or b
	jp nz, .Formula
	ld a, [FSM_CATEGORY]
	and a
	jr nz, .special_slot
	ld a, [FSM_TEMP + 2]
	cp 24
	jr nc, .physical_high
	add a
	ld l, a
	ld h, 0
	ld bc, FSN_PHYS_CACHE_LOW
	add hl, bc
	jr .cache_slot
.physical_high
	jr .uncached ; powers of 120 and above: rare, computed each time
.special_slot
	ld a, [FSM_TEMP + 2]
	cp 51
	jr nc, .uncached
	add a
	ld l, a
	ld h, 0
	add hl, de
	ld bc, FSN_SPEC_CACHE
	add hl, bc
.cache_slot
	ld a, [hli]
	ld b, a
	ld c, [hl]
	or c
	jr z, .fill_cache
	ret
.fill_cache
	push hl
	call .Formula
	pop hl
	ld [hl], c
	dec hl
	ld [hl], b
	ret
.uncached
	jr .Formula
.Formula
; BC=cap997(floor(floor(floor((floor(2L/5)+2)*P*A)/D)/50))+2 with the
; category's truncated operands; known incoming item factors are identity.
	ld a, [FSN_LEVEL]
	ld c, a
	ld b, 0
	sla c
	rl b
	ld a, 5
	call .Div16By8
	ld a, c
	add 2 ; the kernel adds two to the low quotient byte only
	ld c, a
	ld a, [FSM_POWER]
	call .Mul16By8 ; A:HL=product
	ld b, 0 ; product < 2^16 (42*250)
	push hl
	call .AttackOperand
	pop bc
	call .Mul16By8 ; A:HL=24-bit product
	ld b, a
	call .DefenseOperand
	ld c, a
	ld a, [FSM_HALVE]
	and a
	jr z, .divide_defense
	srl c
	jr nz, .divide_defense
	inc c ; the kernel's defense-zero guard after halving
.divide_defense
	call .Div24By8
	ld c, 50
	call .Div24By8
; cap at 997, then +2
	ld a, b
	and a
	jr nz, .cap
	ld a, h
	cp HIGH(998)
	jr c, .plus_two
	jr nz, .cap
	ld a, l
	cp LOW(998)
	jr c, .plus_two
.cap
	ld hl, 997
.plus_two
	inc hl
	inc hl
	ld b, h
	ld c, l
	ret
.AttackOperand
; A=the category's truncated attack byte, or the own variant's. HL scratch.
	ld a, [FSM_VARIANT]
	and a
	jr nz, .variant_attack
	ld a, [FSM_CATEGORY]
	and a
	ld a, [FSN_PHYS_ATTACK]
	ret z
	ld a, [FSN_SPEC_ATTACK]
	ret
.variant_attack
	call .VariantSlot
	ld a, [hl]
	ret
.DefenseOperand
; A=the category's truncated defense byte, or the own variant's. B/HL preserved.
	ld a, [FSM_VARIANT]
	and a
	jr nz, .variant_defense
	ld a, [FSM_CATEGORY]
	and a
	ld a, [FSN_PHYS_DEFENSE]
	ret z
	ld a, [FSN_SPEC_DEFENSE]
	ret
.variant_defense
	push hl
	call .VariantSlot
	inc hl
	ld a, [hl]
	pop hl
	ret
.VariantSlot
; HL=own variant slot FSM_VARIANT-1: its attack byte, then its defense byte.
	ld a, [FSM_VARIANT]
	dec a
	add a
	add LOW(FSA_OWN_VARIANTS)
	ld l, a
	ld h, HIGH(FSA_OWN_VARIANTS)
	ret
ASSERT LOW(FSA_OWN_VARIANTS) + 6 <= $100

.Weather
	ld a, [FSN_WEATHER]
	cp WEATHER_RAIN
	jr z, .rain
	cp WEATHER_SUN
	ret nz
	ld a, [FSM_TYPE]
	cp FIRE
	jr z, .weather_up
	cp WATER
	ret nz
	jr .weather_down
.rain
	ld a, [FSM_TYPE]
	cp WATER
	jr z, .weather_up
	cp FIRE
	jr z, .weather_down
	ld a, [FSM_EFFECT]
	cp EFFECT_SOLARBEAM
	ret nz
.weather_down
	ld a, 1
	ld h, 2
	jp .Scale
.weather_up
	ld a, 3
	ld h, 2
	jp .Scale

.Chart
; Apply the defender's precomputed rows for FSM_TYPE to BC in chart order:
; double (saturating), halve (minimum one), or no effect, which a Dragon
; attacker turns into a halving except for fixed-amount effects. Struggle and
; zero pass through, like the kernel's row scan.
	ld a, [FSM_STRUGGLE]
	and a
	ret nz
	ld a, b
	or c
	ret z
	ld a, [FSM_TYPE]
	cp TYPES_END
	ret nc
	cp UNUSED_TYPES_END
	jr c, .chart_index
	sub UNUSED_TYPES_END - UNUSED_TYPES
.chart_index
	push bc
	ld c, a
	ld b, 0
	ld hl, FSN_CHART
	add hl, bc
	ld a, [hl]
	pop bc
	ld [FSM_TEMP + 1], a
	call .chart_apply
	ret c
	ld a, [FSM_TEMP + 1]
	rrca
	rrca
.chart_apply
; A bits 0..1 = row code, BC = amount. Carry when the amount became zero.
	and 3
	ret z
	cp 3
	jr z, .chart_no_effect
	dec a
	jr nz, .chart_halve
	sla c
	rl b
	ret nc
	ld bc, $ffff
	and a
	ret
.chart_halve
	srl b
	rr c
	ld a, b
	or c
	ret nz
	inc c
	ret
.chart_no_effect
	ld a, [FSN_MAJESTY]
	and a
	jr z, .chart_immune
	ld a, [FSM_EFFECT]
	cp EFFECT_STATIC_DAMAGE
	jr z, .chart_immune
	cp EFFECT_LEVEL_DAMAGE
	jr z, .chart_immune
	cp EFFECT_SUPER_FANG
	jr nz, .chart_halve
.chart_immune
	ld bc, 0
	scf
	ret

.Passives
; Type passives in the kernel's order, from the packed per-epoch
; contributions (see FSN_PASSIVES).
	ld a, b
	or c
	ret z
	ld a, [FSM_TYPE]
	cp NORMAL
	jr nz, .fire
	ld a, [FSN_PASSIVES + 1]
	rrca
	rrca
	and %11
	jr z, .fire
	cp 2
	ld a, 31
	ld h, 30
	jr nz, .normal_scale
	ld a, 16
	ld h, 15
.normal_scale
	call .Scale
.fire
	ld a, [FSM_TYPE]
	cp FIRE
	jr nz, .ghost
	ld a, [FSM_FLAGS]
	bit AD_ATTACKER_LOW_F, a
	jr z, .ghost
	ld a, [FSN_PASSIVES + 1]
	rrca
	rrca
	rrca
	rrca
	and %11
	jr z, .ghost
	cp 2
	ld a, 11
	ld h, 10
	jr nz, .fire_scale
	ld a, 6
	ld h, 5
.fire_scale
	call .Scale
.ghost
	ld a, [FSM_FLAGS]
	bit AD_DEFENDER_STATUS_F, a
	jr z, .dragon
	ld a, [FSN_PASSIVES + 1]
	rlca
	rlca
	and %11
	jr z, .dragon
	cp 2
	ld a, 21
	ld h, 20
	jr nz, .ghost_scale
	ld a, 11
	ld h, 10
.ghost_scale
	call .Scale
.dragon
	ld a, [FSM_MATCHUP]
	cp EFFECTIVE + 1
	jr nc, .ground
	ld a, [FSN_PASSIVES]
	and %11
	jr z, .category
	cp 2
	ld a, 2
	ld h, 3
	jr nz, .dragon_scale
	ld a, 1
	ld h, 2
.dragon_scale
	call .Scale
	jr .category
.ground
	ld a, [FSN_PASSIVES]
	rrca
	rrca
	and %11
	jr z, .category
	cp 2
	ld a, 19
	ld h, 20
	jr nz, .ground_scale
	ld a, 9
	ld h, 10
.ground_scale
	call .Scale
.category
	ld a, [FSM_CATEGORY]
	and a
	jr nz, .water
	ld a, [FSN_PASSIVES]
	rrca
	rrca
	rrca
	rrca
	and %11
	jr z, .ice
	cp 2
	ld a, 19
	ld h, 20
	jr nz, .category_scale
	ld a, 9
	ld h, 10
	jr .category_scale
.water
	ld a, [FSN_PASSIVES]
	rlca
	rlca
	and %11
	jr z, .ice
	cp 2
	ld a, 39
	ld h, 40
	jr nz, .category_scale
	ld a, 19
	ld h, 20
.category_scale
	call .Scale
.ice
	ld a, [FSM_FLAGS]
	bit AD_DEFENDER_HIGH_F, a
	ret z
	ld a, [FSN_PASSIVES + 1]
	and %11
	ret z
	cp 2
	ld a, 39
	ld h, 40
	jr nz, .Scale
	ld a, 19
	ld h, 20
.Scale
; BC*A/H, floor, minimum one for positive input, zero stays zero, true
; 16-bit overflow saturates (BossAI_DamageKernel.Scale). DE preserved.
	push af
	ld a, b
	or c
	jr nz, .scale_nonzero
	pop af
	ret
.scale_nonzero
	pop af
	cp h
	ret z
	ld l, h
	dec l
	jr z, .scale_multiply ; divisor 1: the product itself
	inc l
	inc l
	cp l
	jr z, .scale_plus_one ; A=H+1: n+floor(n/H)
	dec l
	dec l
	cp l
	jr z, .scale_minus_one ; A=H-1: n-ceil(n/H)
	cp 217
	jr nz, .scale_multiply
	ld l, h
	inc l
	jr z, .scale_roll ; 217/255
.scale_multiply
	push hl
	call .Mul16By8 ; A:HL=24-bit product
	pop bc
	ld c, b ; divisor
	ld b, a
	ld a, c
	dec a
	jr z, .scale_quotient ; divisor 1
	dec a
	jr z, .scale_halve ; divisor 2
	ld a, c
	inc a
	jp z, .scale_by_255 ; divisor 255
	call .Div24By8 ; B:HL=quotient
.scale_quotient
	ld a, b
	and a
	ld bc, $ffff
	ret nz
	ld b, h
	ld c, l
.MinOne
	ld a, b
	or c
	ret nz
	inc c
	ret
.scale_halve
	srl b
	rr h
	rr l
	jr .scale_quotient
.scale_plus_one
; floor(n*(H+1)/H) = n + floor(n/H); positive input stays positive
	ld a, h
	cp 2
	jr nz, .scale_plus_one_divide
	ld h, b
	ld l, c
	srl h
	rr l
	add hl, bc
	jr c, .scale_saturate
	ld b, h
	ld c, l
	ret
.scale_plus_one_divide
	push bc
	call .Div16By8
	pop hl
	add hl, bc
	jr c, .scale_saturate
	ld b, h
	ld c, l
	ret
.scale_minus_one
; floor(n*(H-1)/H) = n - ceil(n/H) = n - floor((n+H-1)/H)
	ld a, h
	cp 2
	jr nz, .scale_minus_one_divide
	srl b
	rr c
	jp .MinOne
.scale_minus_one_divide
	push bc
	ld a, h
	dec a
	add c
	ld c, a
	ld a, b
	adc 0
	ld b, a
	jr c, .scale_minus_wide
	ld a, h
	call .Div16By8
	pop hl
	ld a, l
	sub c
	ld l, a
	ld a, h
	sbc b
	ld h, a
	ld b, h
	ld c, l
	jp .MinOne
.scale_minus_wide
	pop bc
	ld a, h
	dec a
	jp .scale_multiply
.scale_saturate
	ld bc, $ffff
	ret
.scale_roll
; floor(217*n/255): 217*n = 256*n - 39*n (39 = 100111b by Horner), then the
; division by 255 through the shift identity below.
	push de
	ld h, b
	ld l, c ; HL=n
	ld d, 0 ; D:HL accumulates 39*n
	add hl, hl
	rl d
	add hl, hl
	rl d
	add hl, hl
	rl d ; 8n
	add hl, bc
	jr nc, .roll_9
	inc d
.roll_9
	add hl, hl
	rl d ; 18n
	add hl, bc
	jr nc, .roll_19
	inc d
.roll_19
	add hl, hl
	rl d ; 38n
	add hl, bc
	jr nc, .roll_39
	inc d
.roll_39
	xor a
	sub l
	ld l, a
	ld a, c
	sbc h
	ld h, a
	ld a, b
	sbc d
	ld b, a ; B:HL = 256n - 39n
	pop de
.scale_by_255
; floor(n/255) for n=B:HL below 2^24 without a division: with n=256*q0+r0
; the quotient is q0+floor((q0+r0)/255), and for s=q0+r0=256*q1+r1 that inner
; quotient is q1+floor((q1+r1)/255), where q1+r1 is at most 511.
	push de
	ld a, l ; r0
	ld l, h
	ld h, b ; HL=q0
	add l
	ld c, a ; r1
	ld a, h
	adc 0 ; q1, carry when q1=256
	jr c, .scale_255_wide
	ld d, a
	add c ; t=q1+r1
	ld e, 0
	jr c, .scale_255_wrapped
	cp 255
	jr c, .scale_255_sum
	inc e
	jr .scale_255_sum
.scale_255_wrapped
	inc e
	cp 254 ; t-256>=254 means t>=510
	jr c, .scale_255_sum
	inc e
	jr .scale_255_sum
.scale_255_wide
	ld d, 0
	inc h
	jr z, .scale_255_saturate
	ld e, 1
	ld a, c
	cp 254
	jr c, .scale_255_sum
	inc e
.scale_255_sum
	ld a, l
	add d
	ld l, a
	ld a, h
	adc 0
	ld h, a
	jr c, .scale_255_saturate
	ld a, l
	add e
	ld l, a
	ld a, h
	adc 0
	ld h, a
	jr c, .scale_255_saturate
	pop de
	ld b, h
	ld c, l
	jp .MinOne
.scale_255_saturate
	pop de
	ld bc, $ffff
	ret
.Mul16By8
; BC*A -> A:HL (24-bit, A high). DE preserved.
	push de
	ld e, 8
	ld hl, 0
	ld d, 0
.mul_bit
	add hl, hl
	rl d
	rla
	jr nc, .mul_next
	add hl, bc
	jr nc, .mul_next
	inc d
.mul_next
	dec e
	jr nz, .mul_bit
	ld a, d
	pop de
	ret
.Div24By8
; B:HL / C -> B:HL, A=remainder. DE preserved. A zero high byte needs only
; sixteen quotient trials.
	push de
	ld d, c
	ld a, b
	and a
	jr z, .div_short
	ld e, 24
	xor a
.div_bit
	add hl, hl
	rl b
	rla
	jr c, .div_subtract ; ninth remainder bit
	cp d
	jr c, .div_next
.div_subtract
	sub d
	inc l
.div_next
	dec e
	jr nz, .div_bit
	pop de
	ret
.div_short
	ld e, 16
.div_short_bit
	add hl, hl
	rla
	jr c, .div_short_subtract
	cp d
	jr c, .div_short_next
.div_short_subtract
	sub d
	inc l
.div_short_next
	dec e
	jr nz, .div_short_bit
	pop de
	ret
.Div16By8
; BC / A -> BC, A=remainder. DE preserved. A zero high byte needs only eight
; quotient trials.
	push de
	ld d, a
	ld e, 16
	ld h, b
	ld l, c
	ld a, b
	and a
	jr nz, .div16_wide
	ld e, 8
	ld h, c
	ld l, a
.div16_wide
	xor a
.div16_bit
	add hl, hl
	rla
	jr c, .div16_subtract
	cp d
	jr c, .div16_next
.div16_subtract
	sub d
	inc l
.div16_next
	dec e
	jr nz, .div16_bit
	ld b, h
	ld c, l
	pop de
	ret

BossAI_FastCompileReplyVariants::
; DE=context whose compact reply BossAI_FastCompileReplyNative just compiled
; (its compile scratch is live). For a plain damage reply, compile the raw
; maximum and range bit at the start regime against each own defensive
; variant on the reply's category (FSA_OWN_VARIANTS) into the record's variant
; bytes; other opcodes, or no own boost plan, write nothing. SRAM0 open;
; DE/SP preserved; AF/BC/HL scratch.
	ld hl, FSR_BASE + FSR_OPCODE
	add hl, de
	ld a, [hl]
	cp FSR_DAMAGE
	ret nz
	ld a, [FSA_OWN_VARIANT_MASK]
	and a
	ret z
	ld b, a
	ld a, [FSA_START_REGIME]
	ld [FSM_REGIME], a
	ld a, [FSM_CATEGORY]
	and a
	jr nz, .special_variant
	bit 0, b
	jr z, .physical_second
	ld a, 1 ; Defense+1
	ld c, FSR_VARIANT_A
	call .Variant
	ld a, [FSA_OWN_VARIANT_MASK]
	ld b, a
.physical_second
	bit 1, b
	ret z
	ld a, 2 ; Defense+2
	ld c, FSR_VARIANT_B
	jr .Variant
.special_variant
	bit 2, b
	ret z
	ld a, 3 ; Special Defense+2
	ld c, FSR_VARIANT_A
.Variant
; A=slot+1, C=record offset of the variant word.
	ld [FSM_VARIANT], a
	ld a, c
	ld [FSM_TEMP + 3], a
	call BossAI_FastCompileReplyNative.Amount
	xor a
	ld [FSM_VARIANT], a
	ret

; Once-per-defender facts preparation, out of the hot bank (see the routine
; header). The FSN/FSM constants above are shared with the compiler.
PUSHS
SECTION "Boss AI Fast Reply Facts", ROMX
; The type chart mirror and its index are read only by .BuildChart below.
DEF BOSSAI_EMIT_LOCAL_TYPE_MATCHUPS_FAST EQU 1
INCLUDE "data/types/type_matchups.asm"
PURGE BOSSAI_EMIT_LOCAL_TYPE_MATCHUPS_FAST
BossAI_FastTypeMatchupIndex:
	dw BossAI_FastTypeMatchups.NORMAL, BossAI_FastTypeMatchups.NORMAL_FORESIGHT
	dw BossAI_FastTypeMatchups.FIGHTING, BossAI_FastTypeMatchups.FIGHTING_FORESIGHT
	dw BossAI_FastTypeMatchups.FLYING, BossAI_FastTypeMatchups.END
	dw BossAI_FastTypeMatchups.POISON, BossAI_FastTypeMatchups.END
	dw BossAI_FastTypeMatchups.GROUND, BossAI_FastTypeMatchups.END
	dw BossAI_FastTypeMatchups.ROCK, BossAI_FastTypeMatchups.END
	dw BossAI_FastTypeMatchups.END, BossAI_FastTypeMatchups.END ; BIRD
	dw BossAI_FastTypeMatchups.BUG, BossAI_FastTypeMatchups.END
	dw BossAI_FastTypeMatchups.GHOST, BossAI_FastTypeMatchups.END
	dw BossAI_FastTypeMatchups.STEEL, BossAI_FastTypeMatchups.END
REPT SPECIAL - STEEL - 1
	dw BossAI_FastTypeMatchups.END, BossAI_FastTypeMatchups.END
ENDR
	dw BossAI_FastTypeMatchups.FIRE, BossAI_FastTypeMatchups.END
	dw BossAI_FastTypeMatchups.WATER, BossAI_FastTypeMatchups.END
	dw BossAI_FastTypeMatchups.GRASS, BossAI_FastTypeMatchups.END
	dw BossAI_FastTypeMatchups.ELECTRIC, BossAI_FastTypeMatchups.END
	dw BossAI_FastTypeMatchups.PSYCHIC_TYPE, BossAI_FastTypeMatchups.END
	dw BossAI_FastTypeMatchups.ICE, BossAI_FastTypeMatchups.END
	dw BossAI_FastTypeMatchups.DRAGON, BossAI_FastTypeMatchups.END
	dw BossAI_FastTypeMatchups.DARK, BossAI_FastTypeMatchups.END
ASSERT @ - BossAI_FastTypeMatchupIndex == TYPES_END * 4
ASSERT BANK(BossAI_FastTypeMatchupIndex) == BANK(BossAI_FastPrepareReplyFacts)
BossAI_FastPrepareReplyFacts::
; DE=context after the defender's PreparePublicAction (incoming actor
; template and both stat pairs are current), AV_SLOT=defender, AV_KIND=
; candidate kind. Fills FSN from the templates and the public battle state
; the producers read per reply, and invalidates the base caches. SRAM0 open;
; DE/SP preserved. Once per defender: lives in a cold section, reached by
; farcall (no register inputs besides DE, no register outputs).
	ad_address AV_PREPARED_ACTOR + AD_LEVEL
	ld a, [hl]
	ld [FSN_LEVEL], a
	ad_address AV_PREPARED_ACTOR + AD_ATTACKER_TYPES
	ld a, [hli]
	ld [FSN_PLAYER_TYPES], a
	ld a, [hli]
	ld [FSN_PLAYER_TYPES + 1], a
	ld a, [hli]
	ld [FSN_OWN_TYPES], a
	ld a, [hl]
	ld [FSN_OWN_TYPES + 1], a
	ad_address AV_PREPARED_ACTOR + AD_WEATHER
	ld a, [hl]
	ld [FSN_WEATHER], a
	ad_address AV_PREPARED_ACTOR + AD_FLAGS
	ld a, [hl]
	and (1 << AD_IDENTIFIED_F) | (1 << AD_DEFENDER_STATUS_F) | (1 << AD_SUBSTITUTE_F) | (1 << AD_BALLOON_F)
	ld [FSN_FLAGS], a
	ad_address AV_KIND
	ld a, [hl]
	cp AV_SWITCH_ACTION
	ld a, 0
	jr nz, .kind_ready
	inc a
.kind_ready
	ld [FSN_SWITCH], a
; player facts
	ld a, [wPlayerAccLevel]
	ld [FSN_ACC_STAGE], a
	ld a, [wPlayerSubStatus4]
	ld [FSN_PLAYER_SS4], a
	ld a, [wPlayerSubStatus3]
	ld [FSN_PLAYER_SS3], a
	ld a, [wBattleMonStatus]
	ld [FSN_PLAYER_STATUS], a
	ld a, [wPlayerSubStatus5]
	and 1 << SUBSTATUS_TRANSFORMED
	ld a, 0
	jr z, .transform_ready
	ld a, 2
.transform_ready
	ld [FSN_GUARDS], a
; own facts: active battler or a neutral bench entry
	ad_address AV_SLOT
	ld a, [hl]
	cp $ff
	jr nz, .bench
	ld a, [wEnemyEvaLevel]
	ld [FSN_EVA_STAGE], a
	ld a, [wEnemySubStatus5]
	ld [FSN_OWN_SS5], a
	ld a, [wEnemySubStatus3]
	ld [FSN_OWN_SS3], a
	ld a, [wEnemyMinimized]
	ld [FSN_MINIMIZED], a
	ld a, [wEnemyMonItem]
	ld [FSN_OWN_ITEM], a
	ld a, [wEnemyMonStatus]
	ld [FSN_OWN_STATUS], a
	jr .own_ready
.bench
	ld hl, wOTPartyMon1Species
	ld bc, PARTYMON_STRUCT_LENGTH
	call AddNTimes
	push hl
	ld a, [hl]
	cp DITTO
	jr nz, .not_ditto
	ld hl, FSN_GUARDS
	set 0, [hl]
.not_ditto
	pop hl
	push hl
	ld bc, MON_ITEM
	add hl, bc
	ld a, [hl]
	ld [FSN_OWN_ITEM], a
	pop hl
	ld bc, MON_STATUS
	add hl, bc
	ld a, [hl]
	ld [FSN_OWN_STATUS], a
	ld a, BASE_STAT_LEVEL
	ld [FSN_EVA_STAGE], a
	xor a
	ld [FSN_OWN_SS5], a
	ld [FSN_OWN_SS3], a
	ld [FSN_MINIMIZED], a
.own_ready
; typing-derived constants
	ld a, STEEL
	ld hl, FSN_PLAYER_TYPES
	call .Contribution
	ld [FSN_STEEL], a
	ld a, FLYING
	ld hl, FSN_PLAYER_TYPES
	call .Contribution
	and a
	jr z, .flying_ready
	cp 2
	ld a, 26
	jr nz, .flying_ready
	ld a, 27
.flying_ready
	ld [FSN_FLYING], a
	ld a, PSYCHIC_TYPE
	ld hl, FSN_OWN_TYPES
	call .Contribution
	ld [FSN_PSYCHIC], a
	ld a, POISON
	ld hl, FSN_OWN_TYPES
	call .Contribution
	ld [FSN_POISON], a
; Bright Powder / Focus Band parameters of the known own item
	xor a
	ld [FSN_POWDER], a
	ld [FSN_FOCUS], a
	ld a, [FSN_OWN_ITEM]
	and a
	jr z, .powder_ready
	dec a
	ld hl, ItemAttributes + ITEMATTR_EFFECT
	ld bc, ITEMATTR_STRUCT_LENGTH
	call AddNTimes
	ld a, BANK(ItemAttributes)
	call GetFarByte
	ld b, a
	inc hl
	ld a, BANK(ItemAttributes)
	call GetFarByte
	ld c, a
	ld a, b
	cp HELD_BRIGHTPOWDER
	jr nz, .focus_band
	ld a, c
	ld [FSN_POWDER], a
	jr .powder_ready
.focus_band
	cp HELD_FOCUS_BAND
	jr nz, .powder_ready
	ld a, c
	ld [FSN_FOCUS], a
.powder_ready
; Helmet quota: the attacker's (player's) max HP/6, minimum one, only for a
; known Rocky Helmet on the defender
	xor a
	ld [FSN_HELMET], a
	ld [FSN_HELMET + 1], a
	ld a, [FSN_OWN_ITEM]
	cp ROCKY_HELMET
	jr nz, .helmet_ready
	ad_address AV_PREPARED_ACTOR + AD_ATTACKER_MAXHP
	ld a, [hli]
	ld b, a
	ld a, [hl]
	ld c, a
	or b
	jr z, .helmet_ready
	push de
	call .SixthMinOne
	pop de
	ld a, b
	ld [FSN_HELMET], a
	ld a, c
	ld [FSN_HELMET + 1], a
.helmet_ready
; Outrage's public category: physical only for a Dragon attacker whose raw
; public Attack exceeds its raw public Sp. Atk.
	xor a
	ld [FSN_OUTRAGE], a
	ld a, DRAGON
	ld hl, FSN_PLAYER_TYPES
	call .Contribution
	and a
	jr z, .outrage_ready
	ld bc, 0
	farcall BossAI_EstimatePlayerDamageStat
	ld a, b
	ld [FSM_TEMP], a
	ld a, c
	ld [FSM_TEMP + 1], a
	ld bc, 3
	farcall BossAI_EstimatePlayerDamageStat
	ld hl, FSM_TEMP + 1
	ld a, c
	sub [hl]
	dec hl
	ld a, b
	sbc [hl]
	jr nc, .outrage_ready ; Sp. Atk >= Attack stays special
	ld a, 1
	ld [FSN_OUTRAGE], a
.outrage_ready
; truncated formula operands per category, as .Formula truncates them
	ad_address AV_PREPARED_STATS
	call .TruncateStats
	ld a, b
	ld [FSN_PHYS_ATTACK], a
	ld a, c
	ld [FSN_PHYS_DEFENSE], a
	ad_address AV_PREPARED_STATS + 4
	call .TruncateStats
	ld a, b
	ld [FSN_SPEC_ATTACK], a
	ld a, c
	ld [FSN_SPEC_DEFENSE], a
; base caches
	push de
	ld hl, FSN_PHYS_CACHE_LOW
	ld b, 48
	call .ClearBytes
	pop de
	ad_address FSN_SPEC_CACHE
	ld b, 102
	call .ClearBytes
	jr .BuildChart
.ClearBytes
	xor a
.clear_byte
	ld [hli], a
	dec b
	jr nz, .clear_byte
	ret
.BuildChart
; FSN_CHART and FSN_MAJESTY from the defender's types, its identified flag
; and the attacker's types. Every chart multiplier is 0, 5 or 20.
	ld a, DRAGON
	ld hl, FSN_PLAYER_TYPES
	call .Contribution
	ld [FSN_MAJESTY], a
	push de
	ld de, FSN_CHART
	xor a
	ld [FSM_TEMP], a
.chart_type
	xor a
	ld [FSM_TEMP + 1], a
	ld [FSM_TEMP + 2], a
	ld l, 0
	call .chart_rows
	ld a, [FSN_FLAGS]
	bit AD_IDENTIFIED_F, a
	jr nz, .chart_store
	ld l, 2
	call .chart_rows
.chart_store
	ld a, [FSM_TEMP + 1]
	ld [de], a
	inc de
	ld hl, FSM_TEMP
	inc [hl]
	ld a, [hl]
	cp UNUSED_TYPES
	jr nz, .chart_next_type
	ld a, UNUSED_TYPES_END ; skip the gap: no move carries those types
	ld [hl], a
.chart_next_type
	cp TYPES_END
	jr c, .chart_type
	pop de
; packed contributions for the passives
	ld a, WATER
	ld hl, FSN_OWN_TYPES
	call .Contribution
	ld b, a
	ld a, BUG
	ld hl, FSN_OWN_TYPES
	call .PackContribution
	ld a, GROUND
	ld hl, FSN_OWN_TYPES
	call .PackContribution
	ld a, DRAGON
	ld hl, FSN_OWN_TYPES
	call .PackContribution
	ld a, b
	ld [FSN_PASSIVES], a
	ld a, GHOST
	ld hl, FSN_PLAYER_TYPES
	call .Contribution
	ld b, a
	ld a, FIRE
	ld hl, FSN_PLAYER_TYPES
	call .PackContribution
	ld a, NORMAL
	ld hl, FSN_PLAYER_TYPES
	call .PackContribution
	ld a, ICE
	ld hl, FSN_OWN_TYPES
	call .PackContribution
	ld a, b
	ld [FSN_PASSIVES + 1], a
	ret
.PackContribution
; B=packed so far; shifts B up two bits and adds the contribution of type A
; in the type pair at HL.
	call .Contribution
	sla b
	sla b
	or b
	ld b, a
	ret
.chart_rows
; L=index offset (0 ordinary rows, 2 Foresight-only rows). Appends the codes
; of the rows of FSM_TEMP's attacking type that match a defender type.
	ld a, [FSM_TEMP]
	add a
	add a
	add l
	ld l, a
	ld h, 0
	ld bc, BossAI_FastTypeMatchupIndex
	add hl, bc
	ld a, [hli]
	ld h, [hl]
	ld l, a
.chart_row
	ld a, [hli]
	cp -1
	ret z
	cp -2
	ret z
	ld b, a
	ld a, [FSM_TEMP]
	cp b
	ret nz ; the next attacking type's rows
	ld a, [hli]
	ld b, a
	ld a, [FSN_OWN_TYPES]
	cp b
	jr z, .chart_match
	ld a, [FSN_OWN_TYPES + 1]
	cp b
	jr z, .chart_match
	inc hl
	jr .chart_row
.chart_match
	ld a, [hli]
	ld c, 3
	and a
	jr z, .chart_code
	ld c, 1
	cp NOT_VERY_EFFECTIVE
	jr nz, .chart_code
	ld c, 2
.chart_code
	ld a, [FSM_TEMP + 2]
	and a
	jr z, .chart_first_row
	sla c
	sla c
.chart_first_row
	ld a, [FSM_TEMP + 1]
	or c
	ld [FSM_TEMP + 1], a
	ld a, 2
	ld [FSM_TEMP + 2], a
	jr .chart_row
.TruncateStats
; HL=attack word then defense word. B=attack byte, C=defense byte after the
; kernel's once-only quartering when either stat exceeds 255.
	ld a, [hli]
	ld b, a
	ld c, [hl]
	inc hl
	push bc
	ld a, [hli]
	ld b, a
	ld c, [hl]
	pop hl ; HL=attack, BC=defense
	ld a, h
	or b
	jr z, .truncated
	srl b
	rr c
	srl b
	rr c
	ld a, b
	or c
	jr nz, .defense_truncated
	inc c
.defense_truncated
	srl h
	rr l
	srl h
	rr l
	ld a, h
	or l
	jr nz, .truncated
	inc l
.truncated
	ld b, l
	ld a, c
	and a
	ret nz
	inc c ; the kernel's defense-zero guard
	ret
.Contribution
; A=type, HL=type pair. A=0 none, 1 one of two distinct types, 2 both.
; BC/DE preserved (callers keep the running amount in BC).
	push bc
	ld b, a
	ld a, [hli]
	ld c, a
	ld a, [hl]
	cp c
	jr nz, .dual
	cp b
	ld a, 0
	jr nz, .contribution_done
	ld a, 2
	jr .contribution_done
.dual
	cp b
	jr z, .half
	ld a, c
	cp b
	ld a, 0
	jr nz, .contribution_done
.half
	ld a, 1
.contribution_done
	pop bc
	ret

.SixthMinOne
; BC=BC/ROCKY_HELMET_DEN, minimum one for positive input: what
; BossAI_FastCompileReplyNative.Scale computes for 1/ROCKY_HELMET_DEN.
	ld h, b
	ld l, c
	ld d, ROCKY_HELMET_DEN
	ld e, 16
	xor a
.sixth_bit
	add hl, hl
	rla
	jr c, .sixth_subtract
	cp d
	jr c, .sixth_next
.sixth_subtract
	sub d
	inc l
.sixth_next
	dec e
	jr nz, .sixth_bit
	ld b, h
	ld c, l
	ld a, h
	or l
	ret nz
	inc c
	ret

BossAI_FastTruncateStatsFar::
; BC=pointer to an attack word then a defense word. B=attack byte, C=defense
; byte, as BossAI_FastPrepareReplyFacts.TruncateStats (reached by farcall: the
; pointer travels in BC because farcall clobbers HL).
	ld h, b
	ld l, c
	jp BossAI_FastPrepareReplyFacts.TruncateStats
POPS
