"""Declarative boss-AI decision-path fixtures.

Each Case names a decision path, seeds the branch conditions, invokes the real
routine on the ROM, and asserts a behavioural outcome. Adding a fixture should be
a few lines here, not a new script.

House rule, learned from three shipped bugs: pin every branch with BOTH
polarities. A collapsed branch still passes a one-sided test, which is exactly
how "mono Grass heals at the dual rate" and "paralysed Electric skips the
Fighting check" survived their audits. Where a case has a twin, the `pins` text
says so.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from tools.boss_ai_fixtures.harness import (
    AI_TIER_EARLY, AI_TIER_MID, BATTLEPLAYERACTION_SWITCH,
    BATTLEPLAYERACTION_USEMOVE, HAKI_ELIGIBLE_F, HAKI_SPENT_F, MOVES,
    SUBSTATUS_ENCORED, TRAINER_CLASSES, Mon,
)

# Morty's ace and the wall that exposed all of this. Gengar is GHOST/PSYCHIC in
# this hack and Steel is Ghost-immune, so Shadow Ball is a guaranteed no-op here
# while Psychic is the best legal move (0.5x but STAB off base 130 SpA).
GENGAR_MOVES = ["SHADOW_BALL", "THUNDERBOLT", "DESTINY_BOND", "PSYCHIC_M"]
IMMUNE_MOVE = "SHADOW_BALL"
BEST_MOVE = "PSYCHIC_M"


def gengar(hp_pct: int = 100) -> Mon:
    return Mon.of("GENGAR", 26, GENGAR_MOVES, hp_pct=hp_pct)


def magnemite(hp_pct: int = 100) -> Mon:
    return Mon.of("MAGNEMITE", 24, ["THUNDERBOLT", "SWIFT"], hp_pct=hp_pct)


@dataclass
class Case:
    id: str
    path: str
    pins: str
    boss: Mon
    player: Mon
    entry: tuple[str, ...]
    expect: dict
    tier: int = AI_TIER_MID
    scores: list[int] | None = None
    prescore: bool = False
    extra: dict = field(default_factory=dict)


def _haki_ready(over: dict | None = None) -> dict:
    """Boss-first Haki, player locked into a move, window open, no bench.

    Takes a positional dict rather than **kwargs because some keys are
    (symbol, offset) tuples, which kwargs cannot express.
    """
    base = {
        ("wBossAIRevealedMovesBitmapSpare", 1): 1 << HAKI_ELIGIBLE_F,
        "wEnemyGoesFirst": 1,
        "wBattlePlayerAction": BATTLEPLAYERACTION_USEMOVE,
        "wCurPlayerMove": MOVES["THUNDERBOLT"],
        "wEnemySubStatus5": 0,
        "wOTPartyCount": 1,
        "wCurEnemyMove": 0,
        "wBossAIMoveChoiceReady": 0,
    }
    base.update(over or {})
    return base


HAKI_READ = ("BossAI_OracleHakiRead",)
HAKI_AFTER = ("BossAI_OracleHakiAfterPlayerAction",)
NORMAL = ("BossAI_ApplyMoveModel", "BossAI_SelectMove")


CASES: list[Case] = [

    # ---------------- boss-first Haki: the shipped bug and its guard ----------
    Case(
        id="haki_boss_first_scored_array",
        path="haki/boss-first",
        pins="boss-first Haki with a correctly scored array picks the best legal "
             "move (twin of haki_boss_first_unscored_array)",
        boss=gengar(), player=magnemite(), entry=HAKI_READ, prescore=True,
        extra=_haki_ready(),
        expect={"haki_spent": True, "choice_ready": 1,
                "chosen_move": BEST_MOVE, "chosen_move_not": [IMMUNE_MOVE]},
    ),
    Case(
        id="haki_boss_first_unscored_array",
        path="haki/boss-first",
        pins="boss-first Haki must rebuild scores itself; with an array that does "
             "not describe this defender it must still refuse the immune move. "
             "This is the exact shipped defect (chose SHADOW_BALL from slot 1)",
        boss=gengar(), player=magnemite(), entry=HAKI_READ,
        scores=[20, 20, 20, 20],
        extra=_haki_ready(),
        expect={"haki_spent": True, "chosen_move_not": [IMMUNE_MOVE]},
    ),
    Case(
        id="haki_boss_first_immune_move_favoured",
        path="haki/boss-first",
        pins="adversarial array that makes the immune move look best must not "
             "survive the rebuild",
        boss=gengar(), player=magnemite(), entry=HAKI_READ,
        scores=[0, 60, 60, 60],
        extra=_haki_ready(),
        expect={"chosen_move_not": [IMMUNE_MOVE]},
    ),

    # ---------------- boss-first Haki: entry gates (must NOT fire) ------------
    Case(
        id="haki_gate_requires_boss_first",
        path="haki/gates",
        pins="wEnemyGoesFirst == 0 routes to the after-player hook instead, so "
             "the boss-first path must not consume Haki",
        boss=gengar(), player=magnemite(), entry=HAKI_READ, prescore=True,
        extra=_haki_ready({"wEnemyGoesFirst": 0}),
        expect={"haki_spent": False, "choice_ready": 0},
    ),
    Case(
        id="haki_gate_requires_usemove",
        path="haki/gates",
        pins="a switching player is the after-player hook's job; boss-first must "
             "not consume Haki on a switch turn",
        boss=gengar(), player=magnemite(), entry=HAKI_READ, prescore=True,
        extra=_haki_ready({"wBattlePlayerAction": BATTLEPLAYERACTION_SWITCH}),
        expect={"haki_spent": False, "choice_ready": 0},
    ),
    Case(
        id="haki_gate_requires_eligible_window",
        path="haki/gates",
        pins="Haki only fires inside the one-turn ace window",
        boss=gengar(), player=magnemite(), entry=HAKI_READ, prescore=True,
        extra=_haki_ready({("wBossAIRevealedMovesBitmapSpare", 1): 0}),
        expect={"haki_spent": False, "choice_ready": 0},
    ),
    Case(
        id="haki_gate_once_per_battle",
        path="haki/gates",
        pins="already-spent Haki must never fire again (once per battle)",
        boss=gengar(), player=magnemite(), entry=HAKI_READ, prescore=True,
        extra=_haki_ready({
            ("wBossAIRevealedMovesBitmapSpare", 1):
                (1 << HAKI_SPENT_F) | (1 << HAKI_ELIGIBLE_F)}),
        expect={"choice_ready": 0},
    ),
    Case(
        id="haki_gate_no_player_move_locked",
        path="haki/gates",
        pins="nothing to read means nothing to cheat with; wCurPlayerMove == 0 "
             "must not consume Haki",
        boss=gengar(), player=magnemite(), entry=HAKI_READ, prescore=True,
        extra=_haki_ready({"wCurPlayerMove": 0}),
        expect={"haki_spent": False, "choice_ready": 0},
    ),
    Case(
        id="haki_gate_locked_in_enemy",
        path="haki/gates",
        pins="a locked-in boss (mid-Outrage, Encore) has no free choice, so it "
             "must not burn Haki",
        boss=gengar(), player=magnemite(), entry=HAKI_READ, prescore=True,
        extra=_haki_ready({"wEnemySubStatus5": 1 << SUBSTATUS_ENCORED}),
        expect={"haki_spent": False, "choice_ready": 0},
    ),

    # ---------------- Haki trainer eligibility (the real tier/class gate) -----
    # NOTE: BossAI_HakiReadyCommon only checks tier != 0. The tier>=MID and
    # excluded-class rules live in BossAI_HakiTrainerEligible, which runs when the
    # one-turn window is ARMED (BossAI_UpdateHakiAceWindow), not when Haki fires.
    # So these pin the arming gate directly; forcing the eligible bit on with an
    # early tier would be a state the real game cannot produce.
    Case(
        id="eligible_mid_tier_gym_leader",
        path="haki/eligibility",
        pins="a mid-tier, non-excluded leader IS Haki-eligible (twin of the two "
             "negative rows below)",
        boss=gengar(), player=magnemite(),
        entry=("BossAI_HakiTrainerEligible",), tier=AI_TIER_MID,
        extra={"wTrainerClass": TRAINER_CLASSES["MORTY"]},
        expect={"carry": True},
    ),
    Case(
        id="eligible_early_tier_refused",
        path="haki/eligibility",
        pins="AI_TIER_EARLY trainers never arm a Haki window",
        boss=gengar(), player=magnemite(),
        entry=("BossAI_HakiTrainerEligible",), tier=AI_TIER_EARLY,
        extra={"wTrainerClass": TRAINER_CLASSES["MORTY"]},
        expect={"carry": False},
    ),
    Case(
        id="eligible_excluded_class_refused",
        path="haki/eligibility",
        pins="classes on BossAIHakiExcludedClasses (the Kanto leaders) never arm "
             "a Haki window even at mid tier",
        boss=gengar(), player=magnemite(),
        entry=("BossAI_HakiTrainerEligible",), tier=AI_TIER_MID,
        extra={"wTrainerClass": TRAINER_CLASSES["BROCK"]},
        expect={"carry": False},
    ),

    # ---------------- player-first Haki hook ---------------------------------
    Case(
        id="haki_after_player_switch",
        path="haki/after-player",
        pins="player switched: the hook rebuilds against the NEW public target "
             "and must not pick a move it is immune to",
        boss=gengar(), player=magnemite(), entry=HAKI_AFTER,
        scores=[20, 20, 20, 20],
        extra=_haki_ready({"wEnemyGoesFirst": 0,
                             "wBattlePlayerAction": BATTLEPLAYERACTION_SWITCH}),
        expect={"haki_spent": True, "chosen_move_not": [IMMUNE_MOVE]},
    ),
    Case(
        id="haki_after_player_move",
        path="haki/after-player",
        pins="player moved first: hook rebuilds against the resolved state "
             "(twin of haki_after_player_switch)",
        boss=gengar(), player=magnemite(), entry=HAKI_AFTER,
        scores=[20, 20, 20, 20],
        extra=_haki_ready({"wEnemyGoesFirst": 0}),
        expect={"haki_spent": True, "chosen_move_not": [IMMUNE_MOVE]},
    ),

    # ---------------- normal (non-Haki) move choice --------------------------
    Case(
        id="normal_turn_refuses_immune_move",
        path="normal/move-choice",
        pins="the ordinary path hard-blocks an immune damaging move at 80 and the "
             "selector skips it",
        boss=gengar(), player=magnemite(), entry=NORMAL,
        scores=[20, 20, 20, 20],
        extra={"wCurEnemyMove": 0, "wBossAIMoveChoiceReady": 0},
        expect={"choice_ready": 1, "chosen_move": BEST_MOVE,
                "chosen_move_not": [IMMUNE_MOVE], "score_ge": [(0, 80)]},
    ),
    Case(
        id="normal_turn_immune_move_poisoned_low",
        path="normal/move-choice",
        pins="the immunity block overrides an attractive pre-existing score, so "
             "the model does not merely decline to raise it",
        boss=gengar(), player=magnemite(), entry=NORMAL,
        scores=[0, 60, 60, 60],
        extra={"wCurEnemyMove": 0, "wBossAIMoveChoiceReady": 0},
        expect={"chosen_move_not": [IMMUNE_MOVE], "score_ge": [(0, 80)]},
    ),

    # ---------------- Destiny Bond trade window, both polarities -------------
    Case(
        id="destiny_bond_declined_at_full_hp",
        path="scoring/destiny-bond",
        pins="outside the trade window the bond can never cash in, so a usable "
             "attack must outrank it (twin of destiny_bond_taken_when_dying)",
        boss=gengar(hp_pct=100), player=magnemite(), entry=NORMAL,
        scores=[20, 20, 20, 20],
        extra={"wCurEnemyMove": 0, "wBossAIMoveChoiceReady": 0},
        expect={"chosen_move": BEST_MOVE, "chosen_move_not": ["DESTINY_BOND"],
                "score_lt": [(3, 2)]},
    ),
    Case(
        id="destiny_bond_taken_when_dying",
        path="scoring/destiny-bond",
        pins="inside the trade window the bond is a real play and must stay "
             "reachable; guards against over-correcting the fix above",
        boss=gengar(hp_pct=20), player=magnemite(), entry=NORMAL,
        scores=[20, 20, 20, 20],
        extra={"wCurEnemyMove": 0, "wBossAIMoveChoiceReady": 0},
        expect={"chosen_move": "DESTINY_BOND"},
    ),
]


def by_path() -> dict[str, list[Case]]:
    out: dict[str, list[Case]] = {}
    for c in CASES:
        out.setdefault(c.path, []).append(c)
    return out
