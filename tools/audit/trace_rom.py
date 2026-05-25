"""Register/pointer/state preservation invariants for the Boss AI trace family.

These audits enforce engine-ABI invariants: callers that scan tables or
recurse through the boss AI must preserve their cursor registers across
helper calls, switch helpers must restore `wCurSpecies` and re-run
`GetBaseData`, the trace pipeline must not leak through bank-switched
move reads, and the Battle Core source must not host Boss AI labels.
Also covers the data-presence audits (priority trainers, constants) that
ride alongside the engine invariants.

Extracted from `check_boss_ai_trace_invariants.py` per
`audit/non_debugger_code_review_2026-05-26.md` §2 item #8.
"""

from __future__ import annotations

from _common import code_lines, fail
from _trace_helpers import (
    BOSS_TRACE_TOPMOVES,
    TOP_LABEL_RE,
    local_block,
    require_contains,
    require_not_contains,
    require_order,
    top_block,
)


def audit_switch_candidate_state_restoration(boss: str) -> None:
    immunity = top_block(boss, "BossAI_IsImmunityPivotOpportunity")
    require_order(
        immunity,
        [
            "call BossAI_GetPrimaryThreatType",
            "ret nc",
            "ld a, [wCurSpecies]",
            "push af",
            "ld [wCurSpecies], a",
            "call GetBaseData",
            "pop af",
            "ld [wCurSpecies], a",
            "call nz, GetBaseData",
            "scf",
            "ret",
            ".not_immune",
            "pop af",
            "ld [wCurSpecies], a",
            "call nz, GetBaseData",
            "and a",
            "ret",
            ".no",
            "pop af",
            "ld [wCurSpecies], a",
            "call nz, GetBaseData",
            "and a",
            "ret",
        ],
        "immunity pivot candidate base-data restoration",
    )

    compute = top_block(boss, "BossAI_ComputeSwitchCandidateRisk")
    require_order(
        compute,
        [
            "ld a, [wCurSpecies]",
            "push af",
            "ld [wCurSpecies], a",
            "call GetBaseData",
            ".done",
            "jr c, .restore_return",
            "jr .restore_return",
            ".hard_risk",
            "ld a, 99",
            ".restore_return",
            "ld b, a",
            "pop af",
            "ld [wCurSpecies], a",
            "push bc",
            "call GetBaseData",
            "pop bc",
            "ld a, b",
            "ret",
        ],
        "switch candidate risk base-data restoration",
    )


def audit_trace_top_moves_preserves_pointer(boss: str) -> None:
    # BossAI_TraceTopMoves was lifted to its own SECTION/file so the bank can
    # hold the per-tick cache wrappers; read its source file directly.
    trace_source = BOSS_TRACE_TOPMOVES.read_text(encoding="utf-8")
    trace = top_block(trace_source, "BossAI_TraceTopMoves")
    require_order(
        trace,
        [
            "ld de, wEnemyMonMoves",
            "push de",
            "call .InsertCandidate",
            "pop de",
            "inc de",
        ],
        "BossAI trace top-move pointer preservation",
    )


def audit_move_model_trace_snapshots(boss: str, wram: str) -> None:
    move_model = top_block(boss, "BossAI_ApplyMoveModel")
    require_order(
        move_model,
        [
            "call BossAI_ComputePlayerPlausibleTypeMask",
            "call .ClearMoveModelTrace",
            "ld hl, wEnemyAIMoveScores",
            "ld de, wEnemyMonMoves",
            "call .TracePreModelScore",
            "ld a, [hl]",
            "cp 80",
            "jr nc, .scored",
            "call .ScoreMove",
            ".scored",
            "call .TracePostModelScore",
        ],
        "move-model trace snapshots bracket policy scoring",
    )
    for label in (".TracePreModelScore", ".TracePostModelScore"):
        helper = local_block(move_model, label, ".ScoreMove" if label == ".TracePostModelScore" else ".TracePostModelScore")
        require_order(
            helper,
            [
                "push af",
                "push bc",
                "push de",
                "push hl",
                "ld d, [hl]",
                "ld a, NUM_MOVES",
                "sub c",
                "ld c, a",
                "ld b, 0",
                "add hl, bc",
                "ld [hl], d",
                "pop hl",
                "pop de",
                "pop bc",
                "pop af",
                "ret",
            ],
            f"{label} preserves score-loop registers",
        )
    require_contains(
        wram,
        "wBossAITracePreModelScores:: ds NUM_MOVES",
        "trace pre-model score snapshot reserve",
    )
    require_contains(
        wram,
        "wBossAITracePostModelScores:: ds NUM_MOVES",
        "trace post-model score snapshot reserve",
    )


def audit_lookahead_trace_preserves_score_cursor(boss: str) -> None:
    lookahead = top_block(boss, "BossAI_ApplyLookaheadToTopMoveCandidates")
    require_order(
        lookahead,
        [
            "call BossAI_ApplySignedDeltaToScore",
            "pop bc",
            "IF DEF(BOSS_AI_TRACE)",
            "push bc",
            "push hl",
            "ld hl, wBossAITraceLookaheadBonusTop",
            "ld [hl], a",
            ".after_trace",
            "pop hl",
            "pop bc",
            "ENDC",
            "inc b",
            "ld a, b",
            "cp BOSS_AI_LOOKAHEAD_N",
        ],
        "lookahead trace bonus write preserves score cursor",
    )


def audit_boss_move_attr_bank_safety(boss: str) -> None:
    require_not_contains(boss, "call GetMoveAttr", "Boss AI cross-bank move attr reads")
    require_not_contains(boss, "call GetMoveByte", "Boss AI cross-bank move byte reads")
    helper = top_block(boss, "BossAI_GetMoveAttr")
    require_order(
        helper,
        [
            "ld bc, MOVE_LENGTH",
            "call AddNTimes",
            "call BossAI_GetMoveByte",
        ],
        "Boss AI local move attr helper",
    )
    byte_helper = top_block(boss, "BossAI_GetMoveByte")
    require_order(
        byte_helper,
        [
            "ld a, BANK(Moves)",
            "jp GetFarByte",
        ],
        "Boss AI local move byte helper",
    )


def audit_ai_get_enemy_move_thunk_preserves_move_id(boss: str, scoring: str) -> None:
    thunk = top_block(boss, "AIGetEnemyMove_HL")
    require_not_contains(
        thunk,
        "farcall AIGetEnemyMove\n",
        "AIGetEnemyMove_HL must not pass the bank id as the move id",
    )
    require_order(
        thunk,
        [
            "push hl",
            "push bc",
            "ld c, a",
            "farcall AIGetEnemyMoveFromC",
            "pop bc",
            "pop hl",
            "ret",
        ],
        "AIGetEnemyMove_HL preserves hl and passes move id through c",
    )
    wrapper = top_block(scoring, "AIGetEnemyMoveFromC")
    require_contains(wrapper, "ld a, c", "AIGetEnemyMoveFromC restores move id")


def audit_public_threat_scan_preserves_source_pointers(boss: str) -> None:
    level_moves = local_block(
        top_block(boss, "BossAI_AddSpeciesLevelUpMovesToMask"),
        ".move_loop",
        ".skip_move",
    )
    require_order(
        level_moves,
        [
            "call GetFarByte",
            "push hl",
            "call BossAI_AddMoveIdToPlausibleMask",
            "pop hl",
            "inc hl",
            "jr .move_loop",
        ],
        "Boss AI level-up plausible move source pointer preservation",
    )

    likely_moves = local_block(
        top_block(boss, "BossAI_AddSpeciesLevelUpMovesToLikelyMask"),
        ".move_loop",
        ".skip_move",
    )
    require_order(
        likely_moves,
        [
            "call GetFarByte",
            "push hl",
            "call BossAI_AddMoveIdToLikelyMask",
            "pop hl",
            "inc hl",
            "jr .move_loop",
        ],
        "Boss AI level-up likely move source pointer preservation",
    )

    egg_moves = top_block(boss, "BossAI_AddSpeciesEggMovesToMask")
    require_order(
        egg_moves,
        [
            "call GetFarByte",
            "cp -1",
            "ret z",
            "push hl",
            "call BossAI_AddMoveIdToPlausibleMask",
            "pop hl",
            "inc hl",
            "jr .loop",
        ],
        "Boss AI egg move source pointer preservation",
    )


def audit_type_matchup_scan_preserves_table_cursor(boss: str) -> None:
    matchup = local_block(
        top_block(boss, "BossAI_CheckTypeMatchupNoItem"),
        ".yup",
        ".end",
    )
    require_order(
        matchup,
        [
            ".yup",
            "push hl",
            "call GetFarByte",
            "inc hl",
            "call BossAI_ApplyDragonsMajestyNoItem",
            "call Multiply",
            "call Divide",
            "pop hl",
            "jr .types_loop",
        ],
        "Boss AI type-matchup scan table cursor preservation",
    )


def audit_type_threat_severity_preserves_list_cursor(boss: str) -> None:
    revealed = top_block(boss, "BossAI_GetRevealedMoveThreatTypeAndSeverity")
    require_order(
        revealed,
        [
            "ld hl, Moves + MOVE_TYPE",
            "call BossAI_GetMoveAttr",
            "ld b, a",
            "push bc",
            "call BossAI_GetTypeThreatSeverityVsEnemyMon",
            "pop bc",
            "and a",
            "ret z",
            "scf",
        ],
        "revealed primary-threat scan preserves move type across severity scoring",
    )

    severity = top_block(boss, "BossAI_GetTypeThreatSeverityVsEnemyMon")
    require_order(
        severity,
        [
            "push hl",
            "call BossAI_CheckPlayerMoveTypeMatchupVsEnemyNoItem",
            "pop hl",
            ".adjust",
            "ld b, a",
            "push hl",
            "call BossAI_AdjustThreatSeverityForEnemyKnownDefense",
            "pop hl",
            "ret",
        ],
        "Boss AI type-threat severity list cursor preservation",
    )


def audit_primary_threat_fallback_preserves_register_state(boss: str) -> None:
    primary = top_block(boss, "BossAI_GetPrimaryThreatTypeUncached")
    likely = local_block(primary, ".likely_loop", ".possible")
    require_order(
        likely,
        [
            "push hl",
            "push de",
            "call BossAI_TestLikelyMaskBit",
            "pop de",
            "pop hl",
            "push bc",
            "push de",
            "call BossAI_GetTypeThreatSeverityVsEnemyMon",
            "pop de",
            "pop bc",
            "cp d",
        ],
        "primary-threat likely fallback preserves best type/severity registers",
    )

    possible = local_block(primary, ".possible_loop", ".hp_fallback")
    require_order(
        possible,
        [
            "push hl",
            "push de",
            "call BossAI_TestPlausibleMaskBit",
            "pop de",
            "pop hl",
            "push hl",
            "push de",
            "call BossAI_TestLikelyMaskBit",
            "pop de",
            "pop hl",
            "push bc",
            "push de",
            "call BossAI_GetTypeThreatSeverityVsEnemyMon",
            "pop de",
            "pop bc",
            "cp 3",
            "cp d",
        ],
        "primary-threat possible fallback preserves best type/severity registers",
    )

    hp_fallback = local_block(primary, ".hp_fallback", ".done")
    require_order(
        hp_fallback,
        [
            "ld a, BOSS_AI_PLAUSIBLE_HP_RISK_BIT",
            "push de",
            "call BossAI_TestLikelyMaskBit",
            "pop de",
            "ld a, BOSS_AI_PLAUSIBLE_HP_RISK_BIT",
            "push de",
            "call BossAI_TestPlausibleMaskBit",
            "pop de",
            ".hp_loop",
            "push hl",
            "push bc",
            "push de",
            "call BossAI_GetTypeThreatSeverityVsEnemyMon",
            "pop de",
            "pop bc",
            "pop hl",
            "cp d",
        ],
        "primary-threat Hidden Power fallback preserves best type/severity registers",
    )


def audit_legacy_switch_state_restoration(items: str, switch: str) -> None:
    wrapper = top_block(items, "AI_CheckAbleToSwitchPreserveCurSpecies")
    require_order(
        wrapper,
        [
            "ld a, [wCurSpecies]",
            "push af",
            "callfar CheckAbleToSwitch",
            "pop af",
            "ld [wCurSpecies], a",
            "call nz, GetBaseData",
            "ret",
        ],
        "legacy switch entrypoint base-data restoration",
    )

    for label in ("SwitchOften", "SwitchRarely", "SwitchSometimes"):
        require_contains(
            top_block(items, label),
            "call AI_CheckAbleToSwitchPreserveCurSpecies",
            "legacy switch callers restore base data",
        )

    require_order(
        top_block(switch, "FindEnemyMonsThatResistPlayer"),
        [
            "push bc",
            "ld hl, wOTPartySpecies",
            "ld [wCurSpecies], a",
            "call GetBaseData",
            ".done",
            "pop bc",
            "and c",
            "ld c, a",
            "ret",
        ],
        "legacy resist switch scan uses real party species",
    )

    require_order(
        top_block(switch, "FindEnemyMonsWithASuperEffectiveMove"),
        [
            "ld d, 0",
            "ld e, 0",
            ".loop",
            "ld a, b",
            "and c",
            "jr z, .next",
            "ld e, 0",
            "push hl",
            "push bc",
        ],
        "legacy super-effective switch scan resets per-candidate result",
    )


def audit_no_battle_core_boss_labels(core: str, boss: str) -> None:
    if 'SECTION "Battle Core"' in boss or 'BANK("Battle Core")' in boss:
        fail("Boss AI split source must not define or bank into Battle Core")
    for line in code_lines(core):
        stripped = line.strip()
        if TOP_LABEL_RE.match(stripped) and stripped.startswith("BossAI_"):
            fail("Battle Core must not define BossAI labels")


def audit_predetermined_switch_index_guard(core: str) -> None:
    block = top_block(core, "CheckWhetherSwitchmonIsPredetermined")
    require_order(
        block,
        [
            "ld a, [wEnemySwitchMonIndex]",
            "and a",
            "jr z, .check_wBattleHasJustStarted",
            "ld c, a",
            "ld a, [wOTPartyCount]",
            "cp c",
            "jr c, .bad_predetermined_switch",
            "ld a, c",
            "dec a",
            "ld d, a",
            "ld a, [wCurOTMon]",
            "cp d",
            "jr z, .bad_predetermined_switch",
            "ld hl, wOTPartyMon1HP",
            "ld a, d",
            "call GetPartyLocation",
            "ld a, [hli]",
            "or [hl]",
            "jr z, .bad_predetermined_switch",
            "ld b, d",
            "jr .return_carry",
            ".bad_predetermined_switch",
            "xor a",
            "ld [wEnemySwitchMonIndex], a",
            "jr .check_wBattleHasJustStarted",
        ],
        "predetermined enemy switch index must be in-party, alive, and non-current",
    )


def audit_priority_trainers(parties: str, tiers: str) -> None:
    for entry in (
        "db MORTY, MORTY1, AI_TIER_MID",
        "db JASMINE, JASMINE1, AI_TIER_MID",
        "db CLAIR, CLAIR1, AI_TIER_LATE",
        "db KOGA, KOGA1, AI_TIER_LATE",
        "db CHAMPION, LANCE, AI_TIER_LATE",
    ):
        require_contains(tiers, entry, "priority boss AI tier")

    for move in (
        "GENGAR,     SPELL_TAG, SHADOW_BALL, THUNDERBOLT, DESTINY_BOND, PSYCHIC_M",
        "MAGNETON,   MAGNET, SPIKES, THUNDERBOLT, THUNDER_WAVE, SWIFT",
        "STEELIX,    METAL_COAT, EARTHQUAKE, IRON_TAIL, ROCK_SLIDE, ROAR",
        "SKARMORY,   ROCKY_HELMET, SPIKES, STEEL_WING, TOXIC, WHIRLWIND",
        "GLIGAR,     QUICK_CLAW, SPIKES, EARTHQUAKE, WING_ATTACK, TOXIC",
        "TENTACRUEL, MYSTIC_WATER, RAPID_SPIN, SURF, SLUDGE_BOMB, HAZE",
        "GYARADOS,   LEFTOVERS, DRAGON_DANCE, OUTRAGE, HYDRO_PUMP, HYPER_BEAM",
    ):
        require_contains(parties, move, "priority boss scenario move")


def audit_constants(constants: str) -> None:
    for constant in (
        "DEF BOSS_AI_SWITCH_CANDIDATE_CAP EQU 4",
        "DEF BOSS_AI_PLAUSIBLE_HP_RISK_BIT EQU 31",
        "DEF BOSS_AI_PLAUSIBLE_MIN_POWER EQU 45",
    ):
        require_contains(constants, constant, "Boss AI behavior constants")
