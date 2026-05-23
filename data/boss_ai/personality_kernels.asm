; Boss AI personality kernels.
;
; Per-leader 8-byte records consumed by the scoring layer at battle init.
; Loaded into wBossAIKernel by LoadBossAIPersonalityKernel (see
; engine/battle/read_trainer_attributes.asm). Layout constants in
; constants/battle_constants.asm: KERNEL_PLAN_BIAS_MULTIPLIER, KERNEL_SOFTMAX_TEMP,
; KERNEL_PRESERVATION_THRESHOLD, KERNEL_RISK_TOLERANCE, KERNEL_SWITCH_AGGRESSION,
; KERNEL_SETUP_PATIENCE, KERNEL_FLAGS, KERNEL_RESERVED.
;
; P1a ships three tier-default kernels (EARLY/MID/LATE) with neutral values so
; behavior matches the pre-P1 baseline (plan_bias_multiplier = 2 across all
; tiers). P1b ships per-leader entries with curated personalities.
;
; Lookup contract:
;   - Iterate BossAIPersonalityKernelMap looking for matching trainer_class + trainer_id.
;   - On match, copy the 8-byte kernel into wBossAIKernel.
;   - On no match, copy the tier-default kernel for wBossAITier.
;   - On wBossAITier == 0 (non-boss), skip the kernel load (BossAI scoring
;     paths are gated on wBossAITier anyway).
;
; The byte-by-byte record shape MUST stay 8 bytes; the audit at
; tools/audit/check_personality_kernel_coverage.py enforces this.

BossAIPersonalityKernels::

; --- Tier-default kernels (3 entries, indexed by tier value 1/2/3) ---
; Order matches AI_TIER_EARLY(1)/AI_TIER_MID(2)/AI_TIER_LATE(3) so the loader
; can do a single index multiply.
BossAITierDefaultKernels::
; AI_TIER_EARLY default
	db 2 ; KERNEL_PLAN_BIAS_MULTIPLIER — pre-P1 baseline (was hardcoded ld a, 2)
	db 0 ; KERNEL_SOFTMAX_TEMP — sharpest; consumed by P4
	db 0 ; KERNEL_PRESERVATION_THRESHOLD — placeholder
	db 0 ; KERNEL_RISK_TOLERANCE — placeholder
	db 0 ; KERNEL_SWITCH_AGGRESSION — placeholder
	db 0 ; KERNEL_SETUP_PATIENCE — placeholder
	db 0 ; KERNEL_FLAGS — placeholder
	db 0 ; KERNEL_RESERVED
; AI_TIER_MID default
	db 2 ; KERNEL_PLAN_BIAS_MULTIPLIER
	db 0, 0, 0, 0, 0, 0, 0
; AI_TIER_LATE default
	db 2 ; KERNEL_PLAN_BIAS_MULTIPLIER
	db 0, 0, 0, 0, 0, 0, 0

; --- Per-leader kernels (P1b extends below this marker) ---
; Map format: db trainer_class, trainer_id, 8 kernel bytes
; Terminator: db 0 (when trainer_class lookup returns 0)
BossAIPersonalityKernelMap::
	db 0 ; end-of-map sentinel; P1b inserts entries above this line
