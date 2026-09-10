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

from dataclasses import dataclass, field, replace

from tools.boss_ai_fixtures.harness import (
    AI_TIER_EARLY, AI_TIER_LATE, AI_TIER_MID, BATTLEPLAYERACTION_SWITCH,
    BATTLEPLAYERACTION_USEMOVE, HAKI_ELIGIBLE_F, HAKI_SPENT_F, MOVES,
    SUBSTATUS_ENCORED, TRAINER_CLASSES, Mon, SPECIES, TYPES, ROOT, _parse_const_file,
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
    registers: dict = field(default_factory=dict)
    stop_at: str | None = None
    skip_calls: tuple[str, ...] = ()
    damage_check: dict | None = None
    action_check: dict | None = None
    exchange_check: dict | None = None
    candidate_check: dict | None = None
    reply_check: dict | None = None
    joint_check: dict | None = None

    @property
    def requires_reference(self) -> bool:
        return (any(spec is not None for spec in (
            self.action_check, self.exchange_check, self.candidate_check,
            self.reply_check, self.joint_check))
            or bool(self.damage_check and self.damage_check.get("speed_facts")))


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
        extra={"wCurEnemyMove": 0, "wBossAIMoveChoiceReady": 0,
               "wPlayerUsedMoves": MOVES["THUNDERBOLT"]},
        expect={"chosen_move": "DESTINY_BOND"},
    ),
]


def by_path() -> dict[str, list[Case]]:
    out: dict[str, list[Case]] = {}
    for c in CASES:
        out.setdefault(c.path, []).append(c)
    return out


# Strategic audit regressions: paired real-ROM predicates and selection paths.
ITEMS = _parse_const_file(ROOT / "constants/item_constants.asm")
for name, move, extra, allowed in [
    ("pp_live", "PSYCHIC_M", {}, True),
    ("pp_empty", "PSYCHIC_M", {("wEnemyMonPP", 3): 0}, False),
    ("pp_up_bits_only", "PSYCHIC_M", {("wEnemyMonPP", 3): 192}, False),
    ("disabled", "PSYCHIC_M", {"wEnemyDisabledMove": MOVES["PSYCHIC_M"]}, False),
    ("choice_same", "PSYCHIC_M", {"wEnemyMonItem": ITEMS["CHOICE_SCARF"],
       "wEnemyChoiceLockedMove": MOVES["PSYCHIC_M"]}, True),
    ("choice_other", "PSYCHIC_M", {"wEnemyMonItem": ITEMS["CHOICE_SCARF"],
       "wEnemyChoiceLockedMove": MOVES["THUNDERBOLT"]}, False),
    ("stale_choice", "PSYCHIC_M", {"wEnemyChoiceLockedMove": MOVES["THUNDERBOLT"]}, True),
    ("vest_attack", "PSYCHIC_M", {"wEnemyMonItem": ITEMS["ASSAULT_VEST"]}, True),
    ("vest_status", "DESTINY_BOND", {"wEnemyMonItem": ITEMS["ASSAULT_VEST"]}, False),
]:
    CASES.append(Case(id=f"available_{name}", path="strategy/availability",
        pins="same moveset, change one availability condition; both polarities",
        boss=gengar(), player=magnemite(), entry=("BossAI_MoveIsAvailable",),
        registers={"A": MOVES[move]}, extra=extra, expect={"carry": allowed}))

for name, extra, available in [
    ("usable", {}, True),
    ("no_pp", {"wEnemyMonPP": 0}, False),
    ("disabled", {"wEnemyDisabledMove": MOVES["PSYCHIC_M"]}, False),
    ("choice_elsewhere", {"wEnemyMonItem": ITEMS["CHOICE_SCARF"],
        "wEnemyChoiceLockedMove": MOVES["DESTINY_BOND"]}, False),
]:
    CASES.append(Case(id=f"ko_scan_{name}", path="strategy/available-ko",
        pins="an unavailable lethal attack must not suppress other tactics",
        boss=Mon.of("GENGAR",26,["PSYCHIC_M","DESTINY_BOND"]),
        player=magnemite(1), entry=("BossAI_HasAnyKOMoveUncached",),
        extra=extra, expect={"carry": available}))

for hp, mask in [(24,0),(25,32),(26,32),(64,32),(65,32)]:
    CASES.append(Case(id=f"quarter_hp_{hp}", path="strategy/quarter-hp",
        pins="threshold includes exact quarter and survives low-byte bit6",
        boss=gengar(), player=magnemite(),
        entry=("FindEnemyMonsWithAtLeastQuarterMaxHP",), registers={"C":32},
        extra={"wOTPartyCount":1,"wOTPartySpecies":SPECIES["GENGAR"],
            ("wOTPartySpecies",1):255,"wOTPartyMon1HP":0,
            ("wOTPartyMon1HP",1):hp,"wOTPartyMon1MaxHP":0,
            ("wOTPartyMon1MaxHP",1):100}, expect={"a":mask}))

for turn, hp, threat, allowed in [(0,100,0,True),(7,100,0,True),
                                 (7,20,0,False),(7,100,1,False)]:
    CASES.append(Case(id=f"setup_window_t{turn}_hp{hp}_threat{threat}",
        path="strategy/setup-window", pins="late safe windows work; HP/threat gates remain",
        boss=gengar(hp), player=magnemite(), entry=("BossAI_SetupTurnIsAffordable",),
        extra={"wEnemyTurnsTaken":turn,"wBossAIRevealedPriorityCache":0,
               "wBossAIPublicThreatCache":threat}, expect={"carry":allowed}))

for cached in (0,1):
    CASES.append(Case(id=f"scout_cached_{cached}", path="strategy/scout",
        pins="repeated consumers reuse one decision within a tick",
        boss=gengar(), player=magnemite(), entry=("BossAI_ShouldScout",)*4,
        extra={"wBossAIShouldScoutPrereqCache":cached,
               "wBossAIShouldScoutThresholdCache":0},
        expect={"carry":bool(cached), "memory":{"wBossAIShouldScoutPrereqCache":cached}}))

for tier, weight in [(1,4),(2,7),(3,10)]:
    for label, mask_kind, expected in [("none",None,0),
         ("likely","wBossAILikelyTypeMaskCache",2*weight),
         ("possible","wBossAIPlausibleTypeMaskCache",2*max(1,weight//2))]:
        extra={"wOTPartySpecies":SPECIES["MANTINE"],
               "wOTPartyMon1HP":0,("wOTPartyMon1HP",1):100,
               "wOTPartyMon1MaxHP":0,("wOTPartyMon1MaxHP",1):100,
               "wBattleMonType1":TYPES["NORMAL"],"wBattleMonType2":TYPES["NORMAL"],
               "wBossAIPrimaryThreatCache":32}
        for cache in ("wBossAILikelyTypeMaskCache","wBossAIPlausibleTypeMaskCache"):
            extra.update({(cache,i):0 for i in range(4)})
        if mask_kind:
            typ=TYPES["ELECTRIC"]
            extra[(mask_kind,typ//8)]=1<<(typ%8)
        CASES.append(Case(id=f"switch_risk_t{tier}_{label}",path="strategy/switch-risk",
            pins="quad weakness uses tier weight rather than mask scratch byte",
            boss=gengar(), player=magnemite(), tier=tier,
            entry=("BossAI_ComputeSwitchCandidateRisk",),registers={"A":1},
            extra=extra,expect={"a":expected}))

for before, addition, expected in [(90,20,99),(250,20,99),(10,20,30)]:
    CASES.append(Case(id=f"risk_accumulation_{before}_{addition}",
        path="strategy/switch-risk", pins="risk caps before byte overflow",
        boss=gengar(),player=magnemite(),
        entry=("BossAI_ComputeSwitchCandidateRisk.AccumulateRisk",),
        registers={"A":addition,"B":before},expect={"a":expected}))

for speed, stage, level, status, scarf, faster in [
    (59,7,24,0,False,True), (20,7,24,0,False,False),
    (59,13,24,0,False,False), (59,1,24,0,False,True),
    (59,7,80,0,False,False), (20,7,24,64,False,True),
    (25,7,24,0,False,False), (25,7,24,0,True,True),
    (300,13,80,0,False,False),
]:
    CASES.append(Case(id=f"speed_own{speed}_stage{stage}_level{level}_status{status}_scarf{scarf}",
        path="strategy/public-speed",pins="public level/stage/status and own effective Speed change race",
        boss=gengar(),player=Mon.of("MAGNEMITE",level,["THUNDERBOLT"],status=status),
        entry=("BossAI_PublicEnemyFasterUncached",),
        extra={"wEnemyMonSpeed":speed>>8,("wEnemyMonSpeed",1):speed&255,
               "wPlayerSpdLevel":stage,"wEnemyMonItem":ITEMS["CHOICE_SCARF"] if scarf else 0},
        expect={"carry":faster}))


for scores in ([20,20,20,20],[1,40,79,60],[80,20,80,60]):
    CASES.append(Case(id="lookahead_all_"+"_".join(map(str,scores)),
        path="strategy/exhaustive-lookahead", pins="every selectable slot matches independent evaluation",
        boss=gengar(),player=magnemite(),tier=3,scores=scores,
        entry=("BossAI_ApplyLookaheadToTopMoveCandidates",),
        extra={"wBossAIShouldScoutPrereqCache":0},expect={"exhaustive_lookahead":True}))

CASES.append(Case(id="scout_new_tick_resets",path="strategy/scout",
    pins="a cached yes cannot carry into the next decision",
    boss=gengar(),player=magnemite(),entry=("BossAI_ResetTurnCaches",),
    extra={"wBossAIShouldScoutPrereqCache":1},
    expect={"memory":{"wBossAIShouldScoutPrereqCache":255}}))


def _bench(names, hp=None, perish=False, threat="ELECTRIC"):
    extra={"wOTPartyCount":len(names),"wCurOTMon":0,"wEnemySwitchMonParam":49,
           "wBossAITargetMonIdx":4,"wBossAIPrimaryThreatCache":TYPES[threat],
           "wEnemySubStatus1":16 if perish else 0,"wEnemyPerishCount":1,
           "wPlayerUsedMoves":0,"wBattleMonType1":TYPES[threat],
           "wBattleMonType2":TYPES[threat]}
    for i,name in enumerate(names):
        extra[("wOTPartySpecies",i)]=SPECIES[name]
        extra[f"wOTPartyMon{i+1}Species"]=SPECIES[name]
        for field,value in (("HP",(hp or {}).get(i,100)),("MaxHP",100)):
            extra[f"wOTPartyMon{i+1}{field}"]=value>>8
            extra[(f"wOTPartyMon{i+1}{field}",1)]=value&255
    extra[("wOTPartySpecies",len(names))]=255
    extra["wCurSpecies"]=SPECIES[names[0]]
    extra[("wBossAILikelyTypeMaskCache",TYPES[threat]//8)]=1<<(TYPES[threat]%8)
    return extra

for names, hp, expected in [
    (["MANTINE","MANTINE","MANTINE","MANTINE","MANTINE","GOLEM"],{},53),
    (["MANTINE","GOLEM","MANTINE","MANTINE","MANTINE","MANTINE"],{},49),
    (["MANTINE","LANTURN","RAICHU"],{1:1},50),
    (["MANTINE","MANTINE"],{},0),
]:
    CASES.append(Case(id="refiner_"+"_".join(names)+str(bool(hp)),
        path="strategy/switch-selection",pins="screen before ranking; visit fifth bench; stable plan scratch",
        boss=Mon.of("MANTINE",40,["SURF"]),player=magnemite(),
        entry=("BossAI_RefineSwitchCandidateForPlausibleRisk",),extra=_bench(names,hp),
        expect={"memory":{"wEnemySwitchMonParam":expected,"wBossAITargetMonIdx":4}}))

for hp, expected in [(100,49),(1,49),(0,0)]:
    CASES.append(Case(id=f"perish_neutral_escape_hp{hp}",path="strategy/perish",
        pins="Perish permits neutral and dying escape; requires a living bench",
        boss=gengar(),player=magnemite(),entry=("BossAI_PickPerishEscape",),
        extra=_bench(["GENGAR","GENGAR"],{1:hp},perish=True,threat="NORMAL"),
        expect={"carry":bool(hp),"memory":{"wEnemySwitchMonParam":expected} } if hp else {"carry":False}))


CASES.append(Case(id="scout_one_actual_roll",path="strategy/scout",
    pins="one real cache miss rolls once; all four consumers agree",
    boss=Mon.of("MANTINE",40,["PROTECT"]),player=magnemite(),
    entry=("BossAI_ShouldScout",)*4,
    extra={"wBossAIPrimaryThreatCache":TYPES["ELECTRIC"],
           "wBossAIShouldScoutPrereqCache":255},
    expect={"random_calls":1,"consistent_decisions":True}))

for count, forced in [(0,False),(1,True),(2,False),(3,False)]:
    CASES.append(Case(id=f"perish_forced_count{count}",path="strategy/perish",
        pins="force exit only on last safe action; earlier countdown retains tempo",
        boss=gengar(),player=magnemite(),entry=("BossAI_EnemyPerishEscapeForced",),
        extra={"wEnemySubStatus1":16,"wEnemyPerishCount":count},expect={"carry":forced}))

for species,level,types,status,stage,expected in [
    ("SHUCKLE",1,None,0,7,5),
    ("MAGNEMITE",24,("ELECTRIC","ELECTRIC"),0,7,31),
    ("MAGNEMITE",24,("ELECTRIC","STEEL"),0,7,30),
    ("MAGNEMITE",24,("FIGHTING","FIGHTING"),64,7,15),
    ("MAGNEMITE",24,("FIGHTING","ELECTRIC"),64,7,11),
    ("MAGNEMITE",24,("NORMAL","NORMAL"),64,7,7),
    ("ELECTRODE",100,None,0,13,1048),
]:
    CASES.append(Case(id=f"speed_estimate_{species}_{types}_{status}_{stage}",
        path="strategy/public-speed",pins="exact estimate rounding and passive fractions",
        boss=gengar(),player=Mon.of(species,level,[],types=types,status=status),
        entry=("BossAI_EstimatePlayerSpeed",),extra={"wPlayerSpdLevel":stage},
        expect={"bc":expected}))

for revealed, tainted, expected in [(False,False,True),(True,False,False),(True,True,True)]:
    extra={"wBossAISeenPlayerSpeciesCount":1,"wBossAISeenPlayerSpecies":SPECIES["MAGNEMITE"],
           "wBossAISeenPlayerAliveMask":1,"wBossAIRevealedMovesBitmapSpare":1 if tainted else 0}
    if revealed:
        extra.update({("wPlayerUsedMoves",i):MOVES[move] for i,move in enumerate(
            ["PROTECT","REST","TOXIC","SUBSTITUTE"])})
    CASES.append(Case(id=f"revealed_threat_full{revealed}_tainted{tainted}",
        path="strategy/revealed-threat",pins="four stable harmless reveals remove invented STAB; taint preserves uncertainty",
        boss=Mon.of("MANTINE",40,["PROTECT"]),player=magnemite(),
        entry=("BossAI_PlayerHasPublicThreatVsEnemyUncached",),extra=extra,expect={"carry":expected}))

for move, expected in [("THUNDERBOLT",True),("COUNTER",False),("MIRROR_COAT",False),
                       ("HIDDEN_POWER",False),("PROTECT",False),("SWIFT",False)]:
    CASES.append(Case(id=f"bond_retaliation_{move}",path="strategy/bond-retaliation",
        pins="neutral revealed attacks count; counter/status/immune hits do not",
        boss=gengar(20),player=magnemite(),
        entry=("BossAI_ApplyMoveModel.HasDestinyBondRetaliation",),
        extra={"wPlayerUsedMoves":MOVES[move]},expect={"carry":expected}))


for alive, expected in [(0,0),(1,2)]:
    CASES.append(Case(id=f"choice_regret_alive{alive}",path="strategy/choice-memory",
        pins="a fainted revealed Ghost cannot punish a future Normal lock",
        boss=Mon.of("LANTURN",40,["TACKLE"]),player=magnemite(),
        entry=("AIGetEnemyMove_HL","BossAI_ApplyMoveModel.SeenSpeciesChoiceLockRisk"),
        registers={"A":MOVES["TACKLE"]},
        extra={"wBossAISeenPlayerSpeciesCount":1,"wBossAISeenPlayerSpecies":SPECIES["GENGAR"],
               "wBossAISeenPlayerAliveMask":alive},expect={"a":expected}))

for matchup, expected in [(0,0),(2,20),(5,40),(10,80),(20,160)]:
    CASES.append(Case(id=f"dominance_type_scale{matchup}",path="strategy/dominance",
        pins="quarter resistance is distinct from half; other tiers retain scaling",
        boss=gengar(),player=magnemite(),
        entry=("BossAI_ApplyDamageDominanceBias.ScalePowerByMatchup",),
        registers={"A":matchup,"B":80},extra={"wTypeMatchup":matchup},expect={"a":expected}))

for live in (False,True):
    for helper in ("BossAI_ApplyDamageDominanceBias","BossAI_ApplyMoveModel.HasStrongMatchupDamagingMove"):
        CASES.append(Case(id=f"available_alternative_{helper}_pp{live}",
            path="strategy/dominance",pins="an unusable alternative cannot dominate or suppress utility",
            boss=Mon.of("LANTURN",40,["TACKLE","SURF"]),
            player=Mon.of("GEODUDE",40,["TACKLE"]),
            entry=("AIGetEnemyMove_HL","BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem",helper),
            registers={"A":MOVES["TACKLE"]},extra={("wEnemyMonPP",1):30 if live else 0},
            expect={"memory":{"wEnemyAIMoveScores":28 if live else 20}}
                if helper=="BossAI_ApplyDamageDominanceBias" else {"carry":live}))

CASES.append(Case(id="status_failure_stays_blocked",path="strategy/hard-block",
    pins="status plan and later bonuses cannot reopen Toxic against Steel",
    boss=Mon.of("GENGAR",26,["TOXIC","THUNDERBOLT","PROTECT","PSYCHIC_M"]),
    player=magnemite(),entry=NORMAL,scores=[20]*4,
    extra={"wBossAIPlanId":2,"wBossAIPlanConfidence":90},
    expect={"score_ge":[(0,80)],"chosen_move_not":["TOXIC"]}))

for trap in ("mean_look","wrap"):
    extra=_bench(["GENGAR","GENGAR"],perish=True,threat="NORMAL")
    extra.update({"wBattleMode":2,"wLinkMode":0,"wEnemySwitchMonIndex":0})
    extra["wPlayerSubStatus5" if trap=="mean_look" else "wEnemyWrapCount"]=128 if trap=="mean_look" else 1
    CASES.append(Case(id=f"perish_trapped_{trap}",path="strategy/perish",
        pins="outer trapping gate still blocks emergency escape",
        boss=gengar(),player=magnemite(),entry=("AI_SwitchOrTryItem",),extra=extra,
        expect={"memory":{"wEnemySwitchMonIndex":0},"random_calls":0}))


for original in list(CASES):
    if original.path=="strategy/revealed-threat":
        CASES.append(Case(id=original.id.replace("revealed_threat","revealed_mask"),
            path="strategy/revealed-mask",pins="stable full reveals narrow both masks and fallback threat reasoning",
            boss=original.boss,player=original.player,
            entry=("BossAI_ComputePlayerPlausibleTypeMask","BossAI_TestLikelyMaskBit"),
            registers={"A":TYPES["ELECTRIC"]},extra=original.extra,expect=original.expect))

for visible, stale, resisted in [("STEEL","NORMAL",True),("NORMAL","STEEL",False)]:
    CASES.append(Case(id=f"coach_visible_{visible}_stale_{stale}",path="strategy/coach-context",
        pins="Outrage stop condition uses active public defender, not last-loaded base data",
        boss=Mon.of("DRAGONITE",50,["OUTRAGE"]),
        player=Mon.of("MAGNEMITE",40,[],types=(visible,visible)),
        entry=("BossAI_CoachExpectedMoveResistedByPlayer",),
        registers={"HL":("BossAICoachPlanTemplates",3)},
        extra={"wBossAIPlanPhase":1,"wBaseType1":TYPES[stale],"wBaseType2":TYPES[stale]},
        expect={"carry":resisted}))

# Exact fixed-damage finishes. Same cases drive the current move and the
# availability-filtered moveset consumer, not a Python damage approximation.
for move, level, hp, types, sub, identified, lethal in [
    ("DRAGON_RAGE",20,39,("NORMAL","NORMAL"),False,False,True),
    ("DRAGON_RAGE",20,40,("NORMAL","NORMAL"),False,False,True),
    ("DRAGON_RAGE",20,41,("NORMAL","NORMAL"),False,False,False),
    ("DRAGON_RAGE",20,256,("NORMAL","NORMAL"),False,False,False),
    ("DRAGON_RAGE",20,40,("STEEL","STEEL"),False,False,True),
    ("DRAGON_RAGE",20,40,("DRAGON","DRAGON"),False,False,True),
    ("DRAGON_RAGE",20,1,("NORMAL","NORMAL"),True,False,False),
    ("SONICBOOM",20,20,("NORMAL","NORMAL"),False,False,True),
    ("SONICBOOM",20,21,("NORMAL","NORMAL"),False,False,False),
    ("SONICBOOM",20,20,("GHOST","GHOST"),False,False,False),
    ("SONICBOOM",20,20,("GHOST","GHOST"),False,True,True),
    ("SEISMIC_TOSS",26,25,("NORMAL","NORMAL"),False,False,True),
    ("SEISMIC_TOSS",26,26,("NORMAL","NORMAL"),False,False,True),
    ("SEISMIC_TOSS",26,27,("NORMAL","NORMAL"),False,False,False),
    ("SEISMIC_TOSS",26,26,("GHOST","GHOST"),False,False,False),
    ("SEISMIC_TOSS",26,26,("GHOST","GHOST"),False,True,True),
    ("NIGHT_SHADE",26,26,("NORMAL","NORMAL"),False,False,False),
    ("NIGHT_SHADE",26,26,("STEEL","STEEL"),False,False,False),
    ("NIGHT_SHADE",26,26,("WATER","WATER"),False,False,True),
    ("SUPER_FANG",20,1,("NORMAL","NORMAL"),False,False,True),
    ("SUPER_FANG",20,2,("NORMAL","NORMAL"),False,False,False),
    ("SUPER_FANG",20,255,("NORMAL","NORMAL"),False,False,False),
    ("SUPER_FANG",20,256,("NORMAL","NORMAL"),False,False,False),
    ("SUPER_FANG",20,0,("NORMAL","NORMAL"),False,False,False),
]:
    for consumer in ("BossAI_CurrentEnemyMoveHasKOPressure", "BossAI_HasAnyKOMove"):
        CASES.append(Case(
            id=f"fixed_ko_{move}_{level}_{hp}_{types[0]}_sub{sub}_id{identified}_{consumer}",
            path="strategy/fixed-damage",pins="exact HP boundary, true immunity and Substitute; Dragon cannot bypass fixed immunity",
            boss=Mon.of("DRATINI",level,[move]),
            player=Mon.of("SNORLAX",80,[],types=types),
            entry=("AIGetEnemyMove_HL",consumer),registers={"A":MOVES[move]},
            extra={"wBattleMonHP":hp>>8,("wBattleMonHP",1):hp&255,
                   "wPlayerSubStatus4":16 if sub else 0,"wPlayerSubStatus1":8 if identified else 0},
            expect={"carry":lethal}))

for available in (False, True):
    CASES.append(Case(id=f"fixed_ko_available_{available}",path="strategy/fixed-damage",
        pins="exact lethal amount still needs an available move",
        boss=Mon.of("DRATINI",20,["DRAGON_RAGE"]),player=Mon.of("SNORLAX",80,[]),
        entry=("BossAI_HasAnyKOMove",),
        extra={"wBattleMonHP":0,("wBattleMonHP",1):40,"wEnemyMonPP":10 if available else 0},
        expect={"carry":available}))

# Synthetic low-pressure attacker isolates the KO reward from retained nonlethal
# pressure bonuses. A Dragon STAB user can receive the same +4 through either
# branch, which would conceal a regression in the lookahead KO predicate.
for move, hp, delta in [("DRAGON_RAGE",40,-4),("DRAGON_RAGE",41,-2),
                        ("TACKLE",40,-2),("TACKLE",41,-2)]:
    CASES.append(Case(id=f"fixed_lookahead_{move}_{hp}",path="strategy/fixed-damage",
        pins="lookahead shares exact finishes; low-level Tackle cannot finish a high-level defender",
        boss=Mon.of("PIDGEY",20,[move]),player=Mon.of("SNORLAX",80,[]),
        entry=("BossAI_EvaluateActionLookahead",),registers={"A":MOVES[move]},
        extra={"wBattleMonHP":0,("wBattleMonHP",1):hp,
               "wBossAIShouldScoutPrereqCache":0,"wBossAIPrimaryThreatCache":254},
        expect={"a":delta&255}))

# Full arithmetic compares against the actual combat routines on the same ROM.
for direction in (0, 1):
    for move in ("TACKLE", "EMBER", "SURF", "THUNDERBOLT", "DRAGON_RAGE", "SEISMIC_TOSS", "SUPER_FANG"):
        CASES.append(Case(id=f"damage_kernel_basic_{direction}_{move}",
            path="strategy/damage-kernel",pins="shared direction-free arithmetic equals combat, with no RNG or battle-state writes",
            boss=Mon.of("DRATINI",50,[move]),player=Mon.of("SNORLAX",50,[move]),
            entry=(),expect={},damage_check={"direction":direction,"move":move}))

for direction in (0, 1):
    for move in ("TACKLE", "EMBER", "SURF", "THUNDERBOLT", "DRAGON_RAGE", "SEISMIC_TOSS", "SUPER_FANG"):
        CASES.append(Case(id=f"damage_adapter_basic_{direction}_{move}",
            path="strategy/damage-adapter",pins="public context construction independently matches combat",
            boss=Mon.of("DRATINI",50,[move]),player=Mon.of("SNORLAX",50,[move]),
            entry=(),expect={},damage_check={"direction":direction,"move":move,"adapter":True}))

for direction, species, item, move, count in [
    (1,"CUBONE","THICK_CLUB","TACKLE",0),
    (1,"SNORLAX","THICK_CLUB","TACKLE",0),
    (1,"PIKACHU","LIGHT_BALL","THUNDERBOLT",0),
    (1,"PIKACHU","LIGHT_BALL","TACKLE",0),
    (1,"SNORLAX","CHOICE_BAND","TACKLE",0),
    (1,"SNORLAX","CHOICE_BAND","SURF",0),
    (1,"SNORLAX","CHOICE_SPECS","SURF",0),
    (1,"SNORLAX","CHOICE_SPECS","TACKLE",0),
    (1,"SNORLAX","LIFE_ORB","TACKLE",0),
    (1,"SNORLAX","MUSCLE_BAND","TACKLE",0),
    (1,"SNORLAX","WISE_GLASSES","SURF",0),
    (1,"SNORLAX","EXPERT_BELT","DYNAMICPUNCH",0),
    (1,"SNORLAX","EXPERT_BELT","TACKLE",0),
    (1,"SNORLAX","CHARCOAL","EMBER",0),
    (1,"SNORLAX","CHARCOAL","SURF",0),
    (1,"SNORLAX","METRONOME_ITEM","TACKLE",0),
    (1,"SNORLAX","METRONOME_ITEM","TACKLE",5),
    (1,"SNORLAX","METRONOME_ITEM","TACKLE",8),
    (0,"DRATINI","EVOLITE","TACKLE",0),
    (0,"DRATINI","EVOLITE","SURF",0),
    (0,"SNORLAX","EVOLITE","TACKLE",0),
    (0,"SNORLAX","ASSAULT_VEST","SURF",0),
    (0,"SNORLAX","ASSAULT_VEST","TACKLE",0),
    (0,"DITTO","METAL_POWDER","TACKLE",0),
    (0,"DITTO","METAL_POWDER","SURF",0),
]:
    CASES.append(Case(id=f"damage_item_{direction}_{species}_{item}_{move}_{count}",
        path="strategy/damage-adapter",pins="known own item normalization agrees with combat on both axes",
        boss=Mon.of(species,50,[move]),player=Mon.of("SNORLAX",50,[move]),
        entry=(),expect={},extra={"wEnemyMonItem":ITEMS[item],"wEnemyMetronomeCount":count},
        damage_check={"direction":direction,"move":move,"adapter":True}))

for direction in (0, 1):
    for stage in (1, 6, 7, 8, 13):
        for special in (False, True):
            move = "SURF" if special else "TACKLE"
            CASES.append(Case(id=f"damage_stage_{direction}_{stage}_{special}",
                path="strategy/damage-adapter",pins="public stat-stage rounding and cap match real battle recalculation",
                boss=Mon.of("SHUCKLE",100,[move]),player=Mon.of("SNORLAX",100,[move]),
                entry=(),expect={},extra={"wPlayerAtkLevel":stage,"wPlayerDefLevel":stage,
                    "wPlayerSAtkLevel":stage,"wPlayerSDefLevel":stage},
                damage_check={"direction":direction,"move":move,"adapter":True}))

for types in (("NORMAL","NORMAL"),("FIGHTING","NORMAL"),("FIGHTING","FIGHTING")):
    for burned in (False, True):
        CASES.append(Case(id=f"damage_burn_{types}_{burned}",
            path="strategy/damage-adapter",pins="ordinary/dual/mono Fighting burn fractions use public status",
            boss=Mon.of("SNORLAX",50,["TACKLE"]),
            player=Mon.of("SNORLAX",50,["TACKLE"],types=types,status=16 if burned else 0),
            entry=(),expect={},damage_check={"direction":0,"move":"TACKLE","adapter":True}))

for passive, move, on_attacker, needs_status, hp_pct in [
    ("NORMAL","TACKLE",True,False,100),
    ("FIRE","EMBER",True,False,33),
    ("GHOST","SURF",True,True,100),
    ("DRAGON","TACKLE",False,False,100),
    ("GROUND","SURF",False,False,100),
    ("BUG","TACKLE",False,False,100),
    ("WATER","THUNDERBOLT",False,False,100),
    ("ICE","TACKLE",False,False,100),
]:
    for mono in (False, True):
        passive_types=(passive,passive if mono else ("FLYING" if on_attacker else "NORMAL"))
        CASES.append(Case(id=f"damage_passive_{passive}_{mono}",
            path="strategy/damage-adapter",pins="hack-specific deterministic passive fractions preserve sequential rounding",
            boss=Mon.of("SNORLAX",50,[move],types=passive_types if on_attacker else ("NORMAL","NORMAL"),hp_pct=hp_pct),
            player=Mon.of("SNORLAX",50,[move],types=passive_types if not on_attacker else ("NORMAL","NORMAL"),status=8 if needs_status else 0),
            entry=(),expect={},damage_check={"direction":1,"move":move,"adapter":True}))

for move, minimum, maximum in [("SPIKE_CANNON",2,5),("DOUBLE_KICK",2,2),("TWINEEDLE",2,2)]:
    for hp_pct in (100, 51, 49):
        CASES.append(Case(id=f"damage_multihit_{move}_{hp_pct}",
            path="strategy/damage-adapter",pins="each hit rounds separately and updates Ice's HP threshold",
            boss=Mon.of("CLOYSTER",50,[move]),
            player=Mon.of("SNORLAX",50,[move],types=("ICE","ICE"),hp_pct=hp_pct),
            entry=(),expect={},damage_check={"direction":1,"move":move,"adapter":True,
                "min_hits":minimum,"max_hits":maximum}))

for move, state, value in [
    ("EARTHQUAKE","wPlayerSubStatus3",0),("EARTHQUAKE","wPlayerSubStatus3",32),
    ("GUST","wPlayerSubStatus3",0),("GUST","wPlayerSubStatus3",64),
    ("TWISTER","wPlayerSubStatus3",64),("STOMP","wPlayerMinimized",0),
    ("STOMP","wPlayerMinimized",1),("PURSUIT","wPlayerMinimized",0),
    ("FALSE_SWIPE","wPlayerMinimized",0),
]:
    CASES.append(Case(id=f"damage_postroll_{move}_{state}_{value}",
        path="strategy/damage-adapter",pins="post-variation modifiers and conditional Pursuit range use public state",
        boss=Mon.of("SNORLAX",50,[move]),player=Mon.of("SNORLAX",50,[move],hp_pct=10),
        entry=(),expect={},extra={state:value},
        damage_check={"direction":1,"move":move,"adapter":True}))

for species in ("DRATINI", "ABRA", "MEW"):
    for stage in (1, 13):
        CASES.append(Case(id=f"damage_outrage_raw_{species}_{stage}",
            path="strategy/damage-adapter",pins="Outrage uses public raw offensive stats, including ties; stages cannot flip category",
            boss=Mon.of("SNORLAX",50,["OUTRAGE"]),
            player=Mon.of(species,50,["OUTRAGE"],types=("DRAGON","DRAGON")),
            entry=(),expect={},extra={"wPlayerAtkLevel":stage,"wPlayerSAtkLevel":14-stage},
            damage_check={"direction":0,"move":"OUTRAGE","adapter":True}))

for direction in (0, 1):
    for move in ("THUNDERBOLT", "DRAGON_RAGE"):
        CASES.append(Case(id=f"damage_transform_{direction}_{move}",
            path="strategy/damage-adapter",pins="copied player stats are uncertain; fixed damage remains known",
            boss=Mon.of("SNORLAX",50,[move]),player=Mon.of("DITTO",50,[move]),
            entry=(),expect={},extra={"wPlayerSubStatus5":8},
            damage_check={"direction":direction,"move":move,"adapter":True,"supported":move=="DRAGON_RAGE"}))

_private_noise={"wBattleMonItem":ITEMS["CHOICE_BAND"],"wBattleMonDVs":255,
                ("wBattleMonDVs",1):255,"wCurPlayerMove":MOVES["EXPLOSION"],"wBattlePlayerAction":2}
for stat in ("Attack", "Defense", "Speed", "SpclAtk", "SpclDef"):
    _private_noise["wBattleMon"+stat]=255
    _private_noise[("wBattleMon"+stat,1)]=255
for stat in ("Attack", "Defense", "Speed", "SpAtk", "SpDef"):
    _private_noise["wPlayer"+stat]=255
    _private_noise[("wPlayer"+stat,1)]=255
for direction in (0, 1):
    for move in ("TACKLE", "SURF", "OUTRAGE"):
        CASES.append(Case(id=f"damage_private_invariance_{direction}_{move}",
            path="strategy/damage-adapter",pins="private stats/DVs/item/selected input cannot alter the public estimate",
            boss=Mon.of("SNORLAX",50,[move]),player=Mon.of("DRATINI",50,[move]),
            entry=(),expect={},damage_check={"direction":direction,"move":move,"adapter":True,
                                          "hidden_noise":_private_noise}))

for direction in (0, 1):
    for accuracy, evasion, identified in [(7,7,False),(1,13,False),(13,1,False),(1,13,True)]:
        for mono in (False, True):
            attacker_types=("FLYING","FLYING" if mono else "NORMAL")
            user_side="Enemy" if direction else "Player"
            target_side="Player" if direction else "Enemy"
            CASES.append(Case(id=f"damage_hit_accuracy_{direction}_{accuracy}_{evasion}_{identified}_{mono}",
                path="strategy/damage-adapter",pins="real CheckHit confirms stage floors, Foresight and Flying accuracy fractions",
                boss=Mon.of("SNORLAX",50,["FIRE_BLAST"],types=attacker_types if direction else None),
                player=Mon.of("SNORLAX",50,["FIRE_BLAST"],types=attacker_types if not direction else None),
                extra={f"w{user_side}AccLevel":accuracy,f"w{target_side}EvaLevel":evasion,
                       f"w{target_side}SubStatus1":8 if identified else 0},
                entry=(),expect={},damage_check={"direction":direction,"move":"FIRE_BLAST",
                                               "adapter":True,"hit_facts":True}))
for move, direction, extra in [
    ("THUNDER",1,{"wBattleWeather":1}),
    ("THUNDER",1,{"wBattleWeather":2}),
    ("SWIFT",0,{"wEnemyMonItem":ITEMS["BRIGHTPOWDER"]}),
    ("TACKLE",0,{"wEnemyMonItem":ITEMS["BRIGHTPOWDER"]}),
    ("TACKLE",1,{"wEnemySubStatus4":1}),
    ("TACKLE",1,{"wPlayerSubStatus5":32}),
    ("TACKLE",1,{"wPlayerSubStatus3":64}),
    ("GUST",1,{"wPlayerSubStatus3":64}),
    ("EARTHQUAKE",1,{"wPlayerSubStatus3":64,"wPlayerSubStatus5":32}),
    ("VITAL_THROW",1,{}),
    ("QUICK_ATTACK",1,{}),
]:
    CASES.append(Case(id=f"damage_hit_special_{move}_{direction}_{extra}",
        path="strategy/damage-adapter",pins="accuracy exceptions and real priority stay separate from damage amounts",
        boss=Mon.of("SNORLAX",50,[move]),player=Mon.of("SNORLAX",50,[move]),
        entry=(),expect={},extra=extra,damage_check={"direction":direction,"move":move,"adapter":True,"hit_facts":True}))

for direction in (0, 1):
    for move in ("SPIKE_CANNON", "TACKLE"):
        CASES.append(Case(id=f"damage_substitute_{direction}_{move}",
            path="strategy/damage-adapter",pins="multi-hit Substitute HP is explicitly unknown; single-hit arithmetic remains available",
            boss=Mon.of("CLOYSTER",50,[move]),player=Mon.of("SNORLAX",50,[move]),
            entry=(),expect={},extra={"wPlayerSubStatus4" if direction else "wEnemySubStatus4":16},
            damage_check={"direction":direction,"move":move,"adapter":True,"supported":move=="TACKLE"}))
CASES.append(Case(id="damage_multihit_overkill_bounds",path="strategy/damage-adapter",
    pins="one upper-roll hit vs two lower-roll hits cannot invert HP-loss endpoints",
    boss=Mon.of("CLOYSTER",50,["SPIKE_CANNON"]),player=Mon.of("SNORLAX",50,["TACKLE"]),
    extra={"wBattleMonHP":0,("wBattleMonHP",1):16},entry=(),expect={},
    damage_check={"direction":1,"move":"SPIKE_CANNON","adapter":True,"min_hits":2,"max_hits":5}))
CASES.append(Case(id="damage_pursuit_repeated_context",path="strategy/damage-adapter",
    pins="a reusable public context preserves minimum Pursuit multiplier",
    boss=Mon.of("UMBREON",50,["PURSUIT"]),player=Mon.of("SNORLAX",50,["TACKLE"]),
    entry=(),expect={},damage_check={"direction":1,"move":"PURSUIT","adapter":True,"repeat_context":True}))

for direction in (0, 1):
    for move, screen in (("TACKLE",16),("SURF",8)):
        for enabled in (False, True):
            CASES.append(Case(id=f"damage_screen_{direction}_{move}_{enabled}",path="strategy/damage-adapter",
                pins="screen doubles the defense word before item boosts and joint truncation",
                boss=Mon.of("SHUCKLE",100,[move]),player=Mon.of("SNORLAX",100,[move]),
                extra={"wPlayerScreens" if direction else "wEnemyScreens":screen if enabled else 0},
                entry=(),expect={},damage_check={"direction":direction,"move":move,"adapter":True}))
for direction, species, item, move in [(1,"CUBONE","THICK_CLUB","TACKLE"),
        (1,"PIKACHU","LIGHT_BALL","SURF"),(1,"SNORLAX","CHOICE_BAND","TACKLE"),
        (0,"DITTO","METAL_POWDER","TACKLE"),(0,"DRATINI","EVOLITE","TACKLE")]:
    CASES.append(Case(id=f"damage_item_cap_{direction}_{species}_{item}",path="strategy/damage-adapter",
        pins="known stat items preserve their own cap rules at boosted level 100 stats",
        boss=Mon.of(species,100,[move]),player=Mon.of("SHUCKLE",100,[move]),
        extra={"wEnemyMonItem":ITEMS[item],"wEnemyAtkLevel":13,"wEnemySAtkLevel":13,"wEnemyDefLevel":13},
        entry=(),expect={},damage_check={"direction":direction,"move":move,"adapter":True}))
for direction in (0, 1):
    for balloon in (False, True):
        CASES.append(Case(id=f"damage_balloon_{direction}_{balloon}",path="strategy/damage-adapter",
            pins="only the known own defender balloon can nullify Ground damage",
            boss=Mon.of("SNORLAX",50,["EARTHQUAKE"]),player=Mon.of("SNORLAX",50,["EARTHQUAKE"]),
            extra={"wEnemyMonItem":ITEMS["AIR_BALLOON"] if balloon else 0},entry=(),expect={},
            damage_check={"direction":direction,"move":"EARTHQUAKE","adapter":True}))

for boss, player, move, extra, lethal in [
    (Mon.of("DRAGONITE",100,["TACKLE"]),Mon.of("MAGIKARP",5,[]),"TACKLE",{},True),
    (Mon.of("PIDGEY",20,["TACKLE"]),Mon.of("SNORLAX",80,[],hp_pct=10),"TACKLE",{},False),
    (Mon.of("DRAGONITE",100,["TACKLE"]),Mon.of("MAGIKARP",5,[]),"TACKLE",{"wPlayerSubStatus3":64},False),
    (Mon.of("DRAGONITE",100,["GUST"]),Mon.of("MAGIKARP",5,[]),"GUST",{"wPlayerSubStatus3":64},True),
    (Mon.of("DRAGONITE",100,["TACKLE"]),Mon.of("MAGIKARP",5,[]),"TACKLE",{"wPlayerSubStatus4":16},False),
    (Mon.of("DRAGONITE",100,["TACKLE"]),Mon.of("MAGIKARP",5,[]),"TACKLE",{"wPlayerSubStatus5":8},False),
]:
    for consumer in ("BossAI_CurrentEnemyMoveHasKOPressure","BossAI_HasAnyKOMove"):
        CASES.append(Case(id=f"public_ko_{boss.species}_{move}_{extra}_{consumer}",path="strategy/public-ko",
            pins="current and available-moveset KO premises use public HP loss and hit feasibility together",
            boss=boss,player=player,extra=extra,entry=("AIGetEnemyMove_HL",consumer),
            registers={"A":MOVES[move]},expect={"carry":lethal}))
for boss, player, extra, threat in [
    (Mon.of("MAGIKARP",5,["TACKLE"]),Mon.of("DRAGONITE",100,["QUICK_ATTACK"]),{},True),
    (Mon.of("SHUCKLE",100,["TACKLE"],hp_pct=20),Mon.of("RATTATA",5,["QUICK_ATTACK"]),{},False),
    (Mon.of("MAGIKARP",5,["TACKLE"]),Mon.of("DRAGONITE",100,["QUICK_ATTACK"]),{"wEnemySubStatus3":64},False),
    (Mon.of("MAGIKARP",5,["TACKLE"]),Mon.of("DRAGONITE",100,["QUICK_ATTACK"]),{"wEnemySubStatus4":16},False),
    (Mon.of("SHUCKLE",100,["TACKLE"]),Mon.of("DITTO",5,["QUICK_ATTACK"]),{"wPlayerSubStatus5":8},True),
]:
    CASES.append(Case(id=f"public_priority_{boss.species}_{extra}",path="strategy/public-ko",
        pins="revealed priority maximum replaces quarter-HP/power bands and preserves uncertainty",
        boss=boss,player=player,entry=("BossAI_PlayerHasRevealedPriorityThreatUncached",),
        extra={"wPlayerUsedMoves":MOVES["QUICK_ATTACK"],**extra},expect={"carry":threat}))

for direction in (0, 1):
    for blocked in ("sub", "fainted", "flying"):
        target = "Player" if direction else "Enemy"
        extra = {"w"+target+"SubStatus4":16}
        if blocked == "fainted":
            hp = "wBattleMonHP" if direction else "wEnemyMonHP"
            extra.update({hp:0,(hp,1):0})
        if blocked == "flying":
            extra["w"+target+"SubStatus3"] = 64
        CASES.append(Case(id=f"public_multi_sub_{direction}_{blocked}",path="strategy/public-ko",
            pins="unknown multi-hit Substitute damage is conservatively incoming unless fainted or impossible to hit",
            boss=Mon.of("CLOYSTER",50,["SPIKE_CANNON"]),player=Mon.of("SNORLAX",50,["SPIKE_CANNON"]),
            extra=extra,entry=("BossAI_PublicDamageKO",),registers={"B":direction,"C":MOVES["SPIKE_CANNON"]},
            expect={"carry":not direction and blocked=="sub"}))

for direction in (0, 1):
    for psychic, expected in (("none",0),("dual",6),("mono",13)):
        types = ("NORMAL","NORMAL") if psychic=="none" else ("PSYCHIC_TYPE","NORMAL" if psychic=="dual" else "PSYCHIC_TYPE")
        CASES.append(Case(id=f"damage_survival_{direction}_{psychic}",path="strategy/damage-adapter",
            pins="separate per-hit Psychic 6/256 or13/256 and known own FocusBand30/256 match combat thresholds",
            boss=Mon.of("SNORLAX",50,["TACKLE"],types=types if not direction else None),
            player=Mon.of("SNORLAX",50,["TACKLE"],types=types if direction else None),
            extra={"wEnemyMonItem":ITEMS["FOCUS_BAND"]},entry=(),expect={},
            damage_check={"direction":direction,"move":"TACKLE","adapter":True,"survival_facts":[expected,0 if direction else 30]}))

for attack, defense in ((255,255),(256,255),(255,256),(256,256),(999,999),(1498,1998),(1024,1),(1,1024)):
    for move in ("TACKLE", "EXPLOSION"):
        boss=Mon.of("SNORLAX",100,[move])
        player=Mon.of("SNORLAX",100,[move])
        boss.atk=attack
        player.deff=defense
        CASES.append(Case(id=f"damage_truncation_{attack}_{defense}_{move}",path="strategy/damage-kernel",
            pins="joint once-only truncation and selfdestruct defense floor match actual combat at byte boundaries",
            boss=boss,player=player,entry=(),expect={},damage_check={"direction":1,"move":move}))
for direction in (0, 1):
    for passive, divisor, move in (("FIRE",3,"EMBER"),("ICE",2,"TACKLE")):
        for offset in (-1,0,1):
            boss=Mon.of("SNORLAX",50,[move],types=(passive,passive))
            player=Mon.of("SNORLAX",50,[move],types=(passive,passive))
            # Fire gates the attacker; Ice gates the defender.
            target_enemy = bool(direction) if passive=="FIRE" else not direction
            hp_name = "wEnemyMonHP" if target_enemy else "wBattleMonHP"
            hp = (boss if target_enemy else player).max_hp // divisor + offset
            CASES.append(Case(id=f"damage_hp_threshold_{direction}_{passive}_{offset}",path="strategy/damage-adapter",
                pins="strict public one-third/half HP passive boundaries agree with combat",
                boss=boss,player=player,extra={hp_name:hp>>8,(hp_name,1):hp&255},entry=(),expect={},
                damage_check={"direction":direction,"move":move,"adapter":True}))

for direction in (0, 1):
    CASES.append(Case(id=f"damage_status_survival_{direction}",path="strategy/damage-adapter",
        pins="zero-power actions do not inherit direct-damage negation or survival thresholds",
        boss=Mon.of("ALAKAZAM",50,["TOXIC"]),player=Mon.of("ALAKAZAM",50,["TOXIC"]),
        extra={"wEnemyMonItem":ITEMS["FOCUS_BAND"]},entry=(),expect={},
        damage_check={"direction":direction,"move":"TOXIC","adapter":True,"supported":False,"survival_facts":[0,0]}))

for direction in (0, 1):
    for slot in (0, 5):
        for species, item, move in [
            ("SNORLAX",None,"TACKLE"),("SNORLAX",None,"SURF"),
            ("DRAGONITE",None,"OUTRAGE"),("CUBONE","THICK_CLUB","TACKLE"),
            ("PIKACHU","LIGHT_BALL","THUNDERBOLT"),("SNORLAX","CHOICE_BAND","TACKLE"),
            ("SNORLAX","CHOICE_SPECS","SURF"),("DRATINI","EVOLITE","TACKLE"),
            ("SNORLAX","ASSAULT_VEST","SURF"),("SNORLAX","AIR_BALLOON","EARTHQUAKE"),
            ("DITTO","METAL_POWDER","TACKLE"),("DITTO",None,"DRAGON_RAGE"),
        ]:
            CASES.append(Case(id=f"party_damage_{direction}_{slot}_{species}_{item}_{move}",path="strategy/party-damage",
                pins="owned party stats/items/types reconstruct entry damage independent of polluted active context",
                boss=Mon.of(species,50,[move]),player=Mon.of("SNORLAX",50,[move]),
                extra={"wEnemyMonItem":ITEMS[item] if item else 0},entry=(),expect={},
                damage_check={"direction":direction,"move":move,"adapter":True,"own_slot":slot,
                              "supported":species!="DITTO","hit_facts":True}))
for species in ("SNORLAX", "MACHAMP", "HERACROSS"):
    for burned in (False, True):
        CASES.append(Case(id=f"party_damage_burn_{species}_{burned}",path="strategy/party-damage",
            pins="bench Attack starts at neutral stages and applies burn/Fighting fractions once",
            boss=Mon.of(species,50,["TACKLE"],status=16 if burned else 0),player=Mon.of("SNORLAX",50,[]),
            entry=(),expect={},damage_check={"direction":1,"move":"TACKLE","adapter":True,"own_slot":2}))
for direction, item, move, supported in [
    (1,"LIFE_ORB","SPIKE_CANNON",False),(1,"SHELL_BELL","SPIKE_CANNON",False),
    (1,"LIFE_ORB","TACKLE",True),(1,"SHELL_BELL","TACKLE",True),
    (0,"ROCKY_HELMET","DOUBLE_KICK",False),(0,"ROCKY_HELMET","SPIKE_CANNON",True),
    (0,"ROCKY_HELMET","TACKLE",True),(0,None,"DOUBLE_KICK",True),
    (1,None,"SPIKE_CANNON",True),
]:
    CASES.append(Case(id=f"party_item_multihit_{direction}_{item}_{move}",path="strategy/party-damage",
        pins="known per-hit user-HP item transitions remain explicit unknown; noncontact and single hits retain support",
        boss=Mon.of("CLOYSTER",50,[move]),player=Mon.of("SNORLAX",50,[move]),
        extra={"wEnemyMonItem":ITEMS[item] if item else 0},entry=(),expect={},
        damage_check={"direction":direction,"move":move,"adapter":True,"own_slot":1,"supported":supported,
                      "min_hits":2 if move in ("SPIKE_CANNON","DOUBLE_KICK") else 1,
                      "max_hits":5 if move=="SPIKE_CANNON" else 2 if move=="DOUBLE_KICK" else 1}))

CASES.append(Case(id="party_ditto_fixed_immunity_unknown",path="strategy/party-damage",
    pins="entry Imposter changes types too, so original Normal typing cannot establish fixed-damage immunity",
    boss=Mon.of("DITTO",50,["TRANSFORM"]),player=Mon.of("GENGAR",50,["NIGHT_SHADE"]),
    entry=(),expect={},damage_check={"direction":0,"move":"NIGHT_SHADE","adapter":True,"own_slot":2,"supported":False}))

for move in ("TAKE_DOWN", "GIGA_DRAIN", "PURSUIT"):
    CASES.append(Case(id=f"party_raw_overkill_{move}",path="strategy/party-damage",
        pins="side-effect raw damage stays independent of low target HP loss, including conditional Pursuit",
        boss=Mon.of("SNORLAX",100,[move]),player=Mon.of("MAGIKARP",5,["TACKLE"],hp_pct=5),
        entry=(),expect={},damage_check={"direction":1,"move":move,"adapter":True,"own_slot":1,"raw_facts":True}))

for species in ("SNORLAX", "PIDGEOT"):
    for layers, fraction in ((0,"GetEighthMaxHP"),(1,"GetEighthMaxHP"),
                             (2,"GetSixthMaxHP_Far"),(3,"GetQuarterMaxHP")):
        for hp, maximum in ((0,317),(1,317),(299,317),(1,1)):
            CASES.append(Case(id=f"action_entry_{species}_{layers}_{hp}_{maximum}",path="strategy/action-facts",
                pins="projected Spikes HP loss matches combat fractions, flying immunity, faint and overkill caps",
                boss=Mon.of(species,50,["TACKLE"]),player=Mon.of("SNORLAX",50,[]),
                extra={"wEnemyMonItem":ITEMS["AIR_BALLOON"]},entry=(),expect={},
                action_check={"layers":layers,"fraction":fraction,"hp":hp,"max_hp":maximum}))

for move, fraction in (("RECOVER","GetHalfMaxHP"),("REST","GetMaxHP")):
    for hp, maximum in ((0,317),(1,317),(316,317),(317,317),(1,3)):
        CASES.append(Case(id=f"action_recovery_{move}_{hp}_{maximum}",path="strategy/action-facts",
            pins="projected recovery matches combat fractions and missing-HP/fainted caps",
            boss=Mon.of("SNORLAX",50,[move]),player=Mon.of("SNORLAX",50,[]),entry=(),expect={},
            action_check={"move":move,"fraction":fraction,"hp":hp,"max_hp":maximum}))

for move, matching_time in (("MORNING_SUN",0),("SYNTHESIS",1),("MOONLIGHT",2)):
    for link in (0,1):
        for matched in (False,True):
            for weather in (0,1,2,3):
                index = 2 - int(not link and not matched) + (1 if weather == 2 else -1 if weather else 0)
                fraction = ("GetEighthMaxHP","GetQuarterMaxHP","GetHalfMaxHP","GetMaxHP")[index]
                CASES.append(Case(id=f"action_time_heal_{move}_{link}_{matched}_{weather}",path="strategy/action-facts",
                    pins="time/weather/link recovery follows actual combat fraction selection",
                    boss=Mon.of("SNORLAX",50,[move]),player=Mon.of("SNORLAX",50,[]),
                    extra={"wLinkMode":link,"wTimeOfDay":matching_time if matched else (matching_time+1)%3,
                           "wBattleWeather":weather},entry=(),expect={},
                    action_check={"move":move,"fraction":fraction,"hp":1,"max_hp":317}))

for effect, move in (("Recoil","TAKE_DOWN"),("Drain","GIGA_DRAIN")):
    for types in (("NORMAL","NORMAL"),("STEEL","STEEL"),("STEEL","GROUND")):
        for raw, hp in ((0,100),(1,100),(7,100),(511,100),(511,1),(511,0),(65535,100)):
            CASES.append(Case(id=f"action_self_{effect}_{types[0]}_{types[1]}_{raw}_{hp}",path="strategy/action-self-effects",
                pins="executing recoil/drain raw damage matches combat HP arithmetic, Steel fraction and caps",
                boss=Mon.of("SNORLAX",50,[move],types=types),player=Mon.of("SNORLAX",50,[]),
                entry=(),expect={},action_check={"self_effect":effect,"move":move,"raw":raw,"hp":hp,"max_hp":317}))

for slot in (None, 2):
    for species in ("SNORLAX","JOLTEON","RAICHU","MACHAMP"):
        for paralyzed in (False,True):
            for scarf in (False,True):
                spec = {"direction":1,"move":"TACKLE","adapter":True,"speed_facts":True}
                if slot is not None:
                    spec["own_slot"] = slot
                CASES.append(Case(id=f"action_speeds_{slot}_{species}_{paralyzed}_{scarf}",path="strategy/action-speeds",
                    pins="owned entry/current and public speed match combat Electric/Fighting/status/item order",
                    boss=Mon.of(species,50,["TACKLE"],status=64 if paralyzed else 0),
                    player=Mon.of(species,50,["TACKLE"],status=64 if paralyzed else 0),
                    extra={"wEnemyMonItem":ITEMS["CHOICE_SCARF"] if scarf else 0},entry=(),expect={},damage_check=spec))

for level in (1,100):
    for stage in (1,7,13):
        for slot in (None,2):
            spec = {"direction":1,"move":"TACKLE","adapter":True,"speed_facts":True}
            if slot is not None:
                spec["own_slot"] = slot
            CASES.append(Case(id=f"action_speed_stage_{level}_{stage}_{slot}",path="strategy/action-speeds",
                pins="Speed stage caps precede Electric/paralysis/scarf, with low-level fractional rounding",
                boss=Mon.of("RAICHU",level,["TACKLE"],status=64),
                player=Mon.of("JOLTEON",level,["TACKLE"],status=64),
                extra={"wEnemyMonItem":ITEMS["CHOICE_SCARF"],"wPlayerSpdLevel":stage,
                       "wEnemySpdLevel":stage if slot is None else 7},entry=(),expect={},damage_check=spec))

for ditto in (False,True):
    CASES.append(Case(id=f"action_speed_transform_unknown_{ditto}",path="strategy/action-speeds",
        pins="copied player stats or bench Imposter cannot establish a species-prior action order",
        boss=Mon.of("DITTO" if ditto else "SNORLAX",50,["DRAGON_RAGE"]),
        player=Mon.of("SNORLAX",50,["TACKLE"]),extra={"wPlayerSubStatus5":0 if ditto else 8},entry=(),expect={},
        damage_check={"direction":1,"move":"DRAGON_RAGE","adapter":True,"own_slot":2,
                      "speed_facts":True,"speed_known":False,"supported":not ditto}))

for name, boss, player, spec, extra in [
    ("trade_damage", "JOLTEON", "SNORLAX", {"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DRAGON_RAGE","reply":"DRAGON_RAGE","successor":[60,60],"value":1024}, {}),
    ("cache_fire_crossing", "TYPHLOSION", "JOLTEON", {"own_hp":90,"own_max":200,"player_hp":200,"player_max":200,
        "move":"FLAMETHROWER","reply":"DRAGON_RAGE","uncertain":24,"cache_ready":True,"cache_hits":0}, {}),
    ("cache_fire_same_band", "TYPHLOSION", "JOLTEON", {"own_hp":160,"own_max":200,"player_hp":200,"player_max":200,
        "move":"FLAMETHROWER","reply":"DRAGON_RAGE","uncertain":24,"cache_ready":True,"cache_hits":1}, {}),
    ("cache_ice_crossing", "SNORLAX", "DEWGONG", {"own_hp":200,"own_max":200,"player_hp":105,"player_max":200,
        "move":"TACKLE","reply":"DOUBLE_EDGE","uncertain":16,"cache_ready":True,"cache_hits":0}, {}),
    ("cache_target_cap_growth", "SNORLAX", "BELLOSSOM", {"own_hp":200,"own_max":200,"player_hp":20,"player_max":200,
        "move":"SEISMIC_TOSS","reply":"GIGA_DRAIN","uncertain":16,"cache_ready":True,"cache_hits":1}, {}),
    ("cache_false_swipe_excluded", "SNORLAX", "JOLTEON", {"own_hp":200,"own_max":200,"player_hp":10,"player_max":200,
        "move":"FALSE_SWIPE","reply":"DRAGON_RAGE","uncertain":0,"cache_ready":False,"cache_hits":0}, {}),
    ("cache_fang_excluded", "SNORLAX", "JOLTEON", {"own_hp":200,"own_max":200,"player_hp":200,"player_max":200,
        "move":"SUPER_FANG","reply":"DRAGON_RAGE","uncertain":2,"cache_ready":False,"cache_hits":0}, {}),
    ("cache_multihit_excluded", "SNORLAX", "JOLTEON", {"own_hp":200,"own_max":200,"player_hp":200,"player_max":200,
        "move":"DOUBLESLAP","reply":"DRAGON_RAGE","uncertain":16,"cache_ready":False,"cache_hits":0}, {}),
    ("cache_pursuit_normalized", "SNORLAX", "JOLTEON", {"own_hp":200,"own_max":200,"player_hp":200,"player_max":200,
        "move":"PURSUIT","reply":"DRAGON_RAGE","uncertain":16,"cache_ready":True,"cache_hits":1}, {}),
    ("cache_unknown_speed", "SNORLAX", "JOLTEON", {"own_hp":160,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DRAGON_RAGE","reply":"DRAGON_RAGE","successor":[120,60],"value":1024,
        "uncertain":4,"cache_ready":True,"cache_hits":1}, {"wPlayerSubStatus5":8}),
    ("cache_own_vital_throw", "JOLTEON", "SNORLAX", {"own_hp":40,"own_max":200,"player_hp":200,"player_max":200,
        "move":"VITAL_THROW","reply":"DRAGON_RAGE","successor":[0,200],"value":743,
        "cache_ready":True,"cache_hits":0}, {}),
    ("cache_reply_vital_throw", "SNORLAX", "JOLTEON", {"own_hp":100,"own_max":200,"player_hp":40,"player_max":200,
        "move":"SEISMIC_TOSS","reply":"VITAL_THROW","successor":[100,0],"value":1305,
        "cache_ready":True,"cache_hits":1}, {}),
    ("cache_reply_miss", "SNORLAX", "JOLTEON", {"own_hp":90,"own_max":200,"player_hp":200,"player_max":200,
        "move":"TACKLE","reply":"SUPER_FANG","branch":2,"uncertain":18,"cache_ready":True,"cache_hits":1}, {}),
    ("cache_both_miss", "TYPHLOSION", "JOLTEON", {"own_hp":90,"own_max":200,"player_hp":200,"player_max":200,
        "move":"FIRE_BLAST","reply":"SUPER_FANG","branch":3,"uncertain":10,"cache_ready":True,"cache_hits":0,
        "successor":[90,200],"value":1024}, {}),
    ("cache_reuse_all_events", "TYPHLOSION", "AERODACTYL", {"own_hp":160,"own_max":300,"player_hp":200,"player_max":200,
        "move":"FIRE_BLAST","reply":"ROCK_SLIDE","uncertain":30,"cache_ready":True,"branch_reuse":True},
        {"wEnemyMonItem":ITEMS["QUICK_CLAW"]}),
    ("fast_finish", "JOLTEON", "SNORLAX", {"own_hp":100,"own_max":200,"player_hp":40,"player_max":200,
        "move":"DRAGON_RAGE","reply":"DRAGON_RAGE","successor":[100,0],"value":1305}, {}),
    ("denied_by_finish", "SNORLAX", "JOLTEON", {"own_hp":40,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DRAGON_RAGE","reply":"DRAGON_RAGE","successor":[0,100],"value":743}, {}),
    ("fast_recover", "JOLTEON", "SNORLAX", {"own_hp":180,"own_max":200,"player_hp":100,"player_max":200,
        "move":"RECOVER","reply":"DRAGON_RAGE","successor":[160,100],"value":1011}, {}),
    ("slow_recover", "SNORLAX", "JOLTEON", {"own_hp":180,"own_max":200,"player_hp":100,"player_max":200,
        "move":"RECOVER","reply":"DRAGON_RAGE","successor":[200,100],"value":1037}, {}),
    ("switch_tempo", "SNORLAX", "JOLTEON", {"slot":2,"kind":1,"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DRAGON_RAGE","reply":"DRAGON_RAGE","successor":[10,100],"value":966}, {"wEnemyScreens":3}),
    ("replacement_no_extra_turn", "SNORLAX", "JOLTEON", {"slot":2,"kind":2,"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DRAGON_RAGE","reply":"DRAGON_RAGE","successor":[50,100],"value":992}, {"wEnemyScreens":3}),
    ("entry_faint", "SNORLAX", "JOLTEON", {"slot":2,"kind":1,"own_hp":40,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DRAGON_RAGE","reply":"DRAGON_RAGE","successor":[0,100],"value":743}, {"wEnemyScreens":3}),
    ("large_hp_fraction", "JOLTEON", "SNORLAX", {"own_hp":500,"own_max":999,"player_hp":100,"player_max":200,
        "move":"RECOVER","successor":[999,100],"value":1088}, {}),
    ("wincon_fraction", "JOLTEON", "SNORLAX", {"own_hp":500,"own_max":999,"player_hp":100,"player_max":200,
        "move":"RECOVER","successor":[999,100],"value":1120}, {"wBossAIWinconMonIdx":1}),
    ("selfdestruct_guaranteed_miss", "JOLTEON", "SNORLAX", {"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"EXPLOSION","reply":"DRAGON_RAGE","successor":[0,100],"value":704}, {"wPlayerSubStatus3":64}),
    ("recoil_immunity", "JOLTEON", "GENGAR", {"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"TAKE_DOWN","successor":[100,100],"value":1024,"uncertain":2}, {}),
    ("drain_immunity", "JOLTEON", "UMBREON", {"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DREAM_EATER","successor":[100,100],"value":1024}, {"wBattleMonStatus":2}),
    ("sleep_denies_action", "JOLTEON", "SNORLAX", {"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DRAGON_RAGE","reply":"DRAGON_RAGE","successor":[60,100],"value":998}, {"wEnemyMonStatus":2}),
    ("recharge_denies_action", "JOLTEON", "SNORLAX", {"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DRAGON_RAGE","reply":"DRAGON_RAGE","successor":[60,100],"value":998}, {"wEnemySubStatus4":32}),
    ("frozen_denies_explosion", "JOLTEON", "SNORLAX", {"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"EXPLOSION","reply":"DRAGON_RAGE","successor":[60,100],"value":998}, {"wEnemyMonStatus":32}),
    ("snore_wakes_and_fails", "JOLTEON", "SNORLAX", {"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"SNORE","reply":"DRAGON_RAGE","successor":[60,100],"value":998,"uncertain":8}, {"wEnemyMonStatus":1}),
    ("reply_sleep_denied", "JOLTEON", "SNORLAX", {"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DRAGON_RAGE","reply":"DRAGON_RAGE","successor":[100,60],"value":1050}, {"wBattleMonStatus":2}),
    ("reply_recovers", "JOLTEON", "SNORLAX", {"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DRAGON_RAGE","reply":"RECOVER","successor":[100,160],"value":986}, {}),
    ("rest_full_fails", "JOLTEON", "SNORLAX", {"own_hp":200,"own_max":200,"player_hp":100,"player_max":200,
        "move":"REST","successor":[200,100],"value":1024}, {}),
    ("fixed_own_miss_branch", "JOLTEON", "SNORLAX", {"own_hp":100,"own_max":200,"player_hp":40,"player_max":200,
        "move":"DRAGON_RAGE","reply":"DRAGON_RAGE","branch":1,"successor":[60,40],"value":998,"uncertain":2}, {"wEnemyAccLevel":1}),
    ("fixed_own_hit_branch", "JOLTEON", "SNORLAX", {"own_hp":100,"own_max":200,"player_hp":40,"player_max":200,
        "move":"DRAGON_RAGE","reply":"DRAGON_RAGE","successor":[100,0],"value":1305,"uncertain":2}, {"wEnemyAccLevel":1}),
    ("ordinary_amount_range", "JOLTEON", "SNORLAX", {"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"TACKLE","reference_damage":True,"uncertain":16,"hidden_invariance":True}, {}),
    ("overkill_raw_range", "JOLTEON", "SNORLAX", {"own_hp":100,"own_max":200,"player_hp":1,"player_max":200,
        "move":"TACKLE","reference_damage":True,"uncertain":16}, {}),
    ("switch_pursuit_unresolved", "SNORLAX", "JOLTEON", {"slot":2,"kind":1,"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DRAGON_RAGE","reply":"PURSUIT","successor":[50,100],"value":992,"uncertain":8}, {"wEnemyScreens":3}),
    ("quick_claw_order_uncertain", "JOLTEON", "SNORLAX", {"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DRAGON_RAGE","reply":"DRAGON_RAGE","successor":[60,60],"value":1024,"uncertain":4}, {"wEnemyMonItem":ITEMS["QUICK_CLAW"]}),
    ("flinch_denies_action", "JOLTEON", "SNORLAX", {"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DRAGON_RAGE","reply":"DRAGON_RAGE","successor":[60,100],"value":998}, {"wEnemySubStatus3":8}),
    ("attract_unresolved", "JOLTEON", "SNORLAX", {"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DRAGON_RAGE","reply":"DRAGON_RAGE","successor":[60,60],"value":1024,"uncertain":8}, {"wEnemySubStatus1":128}),
    ("life_orb_then_reply", "JOLTEON", "SNORLAX", {"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DRAGON_RAGE","reply":"DRAGON_RAGE","successor":[40,60],"value":1011}, {"wEnemyMonItem":ITEMS["LIFE_ORB"]}),
    ("life_orb_faint", "JOLTEON", "SNORLAX", {"own_hp":10,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DRAGON_RAGE","reply":"DRAGON_RAGE","successor":[0,60],"value":788}, {"wEnemyMonItem":ITEMS["LIFE_ORB"]}),
    ("shell_bell_raw_overkill", "JOLTEON", "SNORLAX", {"own_hp":100,"own_max":200,"player_hp":1,"player_max":200,
        "move":"DRAGON_RAGE","successor":[105,0],"value":1283}, {"wEnemyMonItem":ITEMS["SHELL_BELL"]}),
    ("shell_bell_cap", "JOLTEON", "SNORLAX", {"own_hp":198,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DRAGON_RAGE","successor":[200,60],"value":1052}, {"wEnemyMonItem":ITEMS["SHELL_BELL"]}),
    ("shell_bell_cannot_revive_explosion", "JOLTEON", "SNORLAX", {"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"EXPLOSION","reply":"DRAGON_RAGE","successor":[0,100],"value":704}, {"wEnemyMonItem":ITEMS["SHELL_BELL"],"wPlayerSubStatus3":64}),
    ("helmet_contact", "JOLTEON", "SNORLAX", {"slot":2,"kind":1,"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DRAGON_RAGE","reply":"SEISMIC_TOSS","successor":[50,67],"value":1014}, {"wEnemyMonItem":ITEMS["ROCKY_HELMET"]}),
    ("helmet_noncontact", "JOLTEON", "SNORLAX", {"slot":2,"kind":1,"own_hp":100,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DRAGON_RAGE","reply":"NIGHT_SHADE","successor":[50,100],"value":992}, {"wEnemyMonItem":ITEMS["ROCKY_HELMET"]}),
    ("helmet_holder_faints", "JOLTEON", "SNORLAX", {"slot":2,"kind":1,"own_hp":40,"own_max":200,"player_hp":100,"player_max":200,
        "move":"DRAGON_RAGE","reply":"SEISMIC_TOSS","successor":[0,67],"value":765}, {"wEnemyMonItem":ITEMS["ROCKY_HELMET"]}),
    ("life_orb_zero_then_drain", "JOLTEON", "SNORLAX", {"own_hp":1,"own_max":200,"player_hp":200,"player_max":200,
        "move":"GIGA_DRAIN","reference_items":"drain","uncertain":16}, {"wEnemyMonItem":ITEMS["LIFE_ORB"]}),
    ("helmet_zero_then_drain", "JOLTEON", "SNORLAX", {"slot":2,"kind":1,"own_hp":200,"own_max":200,"player_hp":1,"player_max":200,
        "move":"DRAGON_RAGE","reply":"LEECH_LIFE","reference_items":"drain","uncertain":16}, {"wEnemyMonItem":ITEMS["ROCKY_HELMET"]}),
    ("shell_bell_then_recoil", "JOLTEON", "SNORLAX", {"own_hp":199,"own_max":200,"player_hp":200,"player_max":200,
        "move":"DOUBLE_EDGE","reference_items":"recoil","uncertain":16}, {"wEnemyMonItem":ITEMS["SHELL_BELL"]}),
    ("own_maximum_amount", "JOLTEON", "SNORLAX", {"own_hp":100,"own_max":200,"player_hp":200,"player_max":200,
        "move":"TACKLE","branch":16,"reference_damage":True,"uncertain":16}, {}),
    ("reply_minimum_amount", "JOLTEON", "SNORLAX", {"slot":2,"kind":1,"own_hp":200,"own_max":200,"player_hp":200,"player_max":200,
        "move":"DRAGON_RAGE","reply":"TACKLE","branch":32,"reference_damage":"incoming","uncertain":16}, {}),
    ("reply_maximum_amount", "JOLTEON", "SNORLAX", {"slot":2,"kind":1,"own_hp":200,"own_max":200,"player_hp":200,"player_max":200,
        "move":"DRAGON_RAGE","reply":"TACKLE","reference_damage":"incoming","uncertain":16}, {}),
    ("claw_own_first_branch", "SNORLAX", "JOLTEON", {"own_hp":40,"own_max":200,"player_hp":40,"player_max":200,
        "move":"DRAGON_RAGE","reply":"DRAGON_RAGE","branch":12,"successor":[40,0],"value":1305,"uncertain":4}, {"wEnemyMonItem":ITEMS["QUICK_CLAW"]}),
    ("claw_reply_first_branch", "SNORLAX", "JOLTEON", {"own_hp":40,"own_max":200,"player_hp":40,"player_max":200,
        "move":"DRAGON_RAGE","reply":"DRAGON_RAGE","branch":4,"successor":[0,40],"value":743,"uncertain":4}, {"wEnemyMonItem":ITEMS["QUICK_CLAW"]}),
    ("priority_precedes_order_branch", "SNORLAX", "JOLTEON", {"own_hp":40,"own_max":200,"player_hp":1,"player_max":200,
        "move":"QUICK_ATTACK","reply":"DRAGON_RAGE","branch":4,"successor":[40,0],"value":1280,"uncertain":16}, {}),
]:
    CASES.append(Case(id="exchange_"+name,path="strategy/action-exchange",
        pins="one material/HP scale respects action order, interruption, recovery caps and switch tempo",
        boss=Mon.of(boss,50,[spec["move"]]),player=Mon.of(player,50,["DRAGON_RAGE"]),
        extra=extra,entry=(),expect={},exchange_check=spec))

# One defensive command per actor; compare projected stat/HP with real combat.
for boost in ("HARDEN", "WITHDRAW", "BARRIER", "ACID_ARMOR", "AMNESIA"):
    for side in ("own", "player"):
        for first in (False, True):
            for matching in (False, True):
                attack = "SURF" if (boost == "AMNESIA") == matching else "SCRATCH"
                boss = "JOLTEON" if (side == "own") == first else "SNORLAX"
                player = "SNORLAX" if boss == "JOLTEON" else "JOLTEON"
                spec = {"own_hp":500,"own_max":500,"player_hp":500,"player_max":500,
                    "move":boost if side == "own" else attack,
                    "reply":attack if side == "own" else boost, "uncertain":16,
                    "defense_reference":{"side":side,"first":first},
                    "branch_reuse":boost == "BARRIER" and side == "player" and first and matching,
                    "hidden_invariance":True}
                if side == "player":
                    spec.update(cache_ready=True, cache_hits=int(not (first and matching)))
                CASES.append(Case(id=f"defense_{boost.lower()}_{side}_{int(first)}_{int(matching)}",
                    path="strategy/defense-exchange", pins="combat defensive command and damage order; exact sparse state and cache parity",
                    boss=Mon.of(boss,50,[spec["move"]]), player=Mon.of(player,50,[spec["reply"]]),
                    extra={},entry=(),expect={},exchange_check=spec))

for name, base_id, extra, boss_override in [
    ("reflect", "defense_barrier_own_1_1", {"wEnemyScreens":16}, {}),
    ("light_screen", "defense_amnesia_own_1_1", {"wEnemyScreens":8}, {}),
    ("public_reflect", "defense_barrier_player_1_1", {"wPlayerScreens":16}, {}),
    ("public_light_screen", "defense_amnesia_player_1_1", {"wPlayerScreens":8}, {}),
    ("plus_five", "defense_barrier_own_1_1", {"wEnemyDefLevel":12}, {}),
    ("plus_six", "defense_barrier_own_1_1", {"wEnemyDefLevel":13}, {}),
    ("already_999", "defense_barrier_own_1_1", {}, {"deff":999}),
    ("eviolite_reflect", "defense_barrier_own_1_1", {"wEnemyMonItem":ITEMS["EVOLITE"],"wEnemyScreens":16}, {"species":SPECIES["PIKACHU"]}),
    ("eviolite_light_screen", "defense_amnesia_own_1_1", {"wEnemyMonItem":ITEMS["EVOLITE"],"wEnemyScreens":8}, {"species":SPECIES["PIKACHU"]}),
    ("metal_powder_reflect", "defense_barrier_own_1_1", {"wEnemyMonItem":ITEMS["METAL_POWDER"],"wEnemyScreens":16}, {"species":SPECIES["DITTO"]}),
]:
    base = next(c for c in CASES if c.id == base_id)
    spec = dict(base.exchange_check, branch_reuse=True)
    CASES.append(replace(base, id="defense_edge_"+name, extra=extra,
        boss=replace(base.boss, **boss_override), exchange_check=spec))
for side, order in (("own", 12), ("own", 4), ("player", 12), ("player", 4)):
    base = next(c for c in CASES if c.id == f"defense_barrier_{side}_1_1")
    spec = dict(base.exchange_check, branch=order, uncertain=20,
        defense_reference={"side":side,"first":(order == 12) == (side == "own")}, branch_reuse=True)
    if side == "player":
        spec["cache_hits"] = int(order == 12)
    CASES.append(replace(base, id=f"defense_tie_{side}_{order}",
        player=Mon.of("JOLTEON" if side == "own" else "SNORLAX",50,[spec["reply"]]), exchange_check=spec))

_CANDIDATE_MOVES = ["TACKLE", "RECOVER", "DRAGON_RAGE", "COUNTER"]
for name, spec, extra in [
    ("all_legal_including_low_hp_bench", {"moves":_CANDIDATE_MOVES,"hidden_invariance":True}, {}),
    ("exact_slot_pp_mask", {"moves":[None,"RECOVER",None,"COUNTER"],"pp":[0,193,192,20]}, {}),
    ("disabled", {"moves":["TACKLE",None,"DRAGON_RAGE","COUNTER"]}, {"wEnemyDisabledMove":MOVES["RECOVER"]}),
    ("empty_pp_struggle", {"mode":1,"forced":"STRUGGLE","pp":[0]*4,"reference_parse":True}, {}),
    ("choice_lock", {"mode":1,"forced":"DRAGON_RAGE","slot":2,"reference_parse":True},
        {"wEnemyMonItem":ITEMS["CHOICE_SCARF"],"wEnemyChoiceLockedMove":MOVES["DRAGON_RAGE"]}),
    ("choice_first_turn", {"moves":_CANDIDATE_MOVES}, {"wEnemyMonItem":ITEMS["CHOICE_BAND"]}),
    ("stale_lock_ignored", {"moves":_CANDIDATE_MOVES}, {"wEnemyChoiceLockedMove":MOVES["DRAGON_RAGE"]}),
    ("choice_missing", {"mode":1,"forced":"STRUGGLE","reference_parse":True},
        {"wEnemyMonItem":ITEMS["CHOICE_SPECS"],"wEnemyChoiceLockedMove":MOVES["THUNDERBOLT"]}),
    ("choice_disabled", {"mode":1,"forced":"STRUGGLE","reference_parse":True},
        {"wEnemyMonItem":ITEMS["CHOICE_BAND"],"wEnemyChoiceLockedMove":MOVES["DRAGON_RAGE"],"wEnemyDisabledMove":MOVES["DRAGON_RAGE"]}),
    ("choice_duplicate_first_exhausted", {"owned_moves":["TACKLE","DRAGON_RAGE","TACKLE","RECOVER"],
        "pp":[0,20,20,20],"mode":1,"forced":"STRUGGLE","reference_parse":True},
        {"wEnemyMonItem":ITEMS["CHOICE_BAND"],"wEnemyChoiceLockedMove":MOVES["TACKLE"]}),
    ("choice_duplicate_first_usable", {"owned_moves":["TACKLE","DRAGON_RAGE","TACKLE","RECOVER"],
        "pp":[20,20,0,20],"mode":1,"forced":"TACKLE","reference_parse":True},
        {"wEnemyMonItem":ITEMS["CHOICE_BAND"],"wEnemyChoiceLockedMove":MOVES["TACKLE"]}),
    ("vest_fixed_and_counter", {"owned_moves":["RECOVER","DRAGON_RAGE","COUNTER","BIDE"],
        "moves":[None,"DRAGON_RAGE","COUNTER","BIDE"]}, {"wEnemyMonItem":ITEMS["ASSAULT_VEST"]}),
    ("vest_no_usable_attack", {"owned_moves":["RECOVER","AGILITY","PROTECT","REST"],
        "mode":1,"forced":"STRUGGLE","reference_parse":True}, {"wEnemyMonItem":ITEMS["ASSAULT_VEST"]}),
    ("encore", {"mode":1,"forced":"RECOVER","slot":1,"reference_parse":True},
        {"wEnemySubStatus5":1<<SUBSTATUS_ENCORED,"wLastEnemyMove":MOVES["RECOVER"],"wCurEnemyMoveNum":1}),
    ("encore_disabled_selection", {"mode":1,"forced":"RECOVER","slot":1,"reference_parse":True},
        {"wEnemySubStatus5":1<<SUBSTATUS_ENCORED,"wLastEnemyMove":MOVES["RECOVER"],"wCurEnemyMoveNum":1,"wEnemyDisabledMove":MOVES["RECOVER"]}),
    ("encore_then_choice", {"mode":1,"forced":"DRAGON_RAGE","slot":2,"reference_parse":True},
        {"wEnemySubStatus5":1<<SUBSTATUS_ENCORED,"wLastEnemyMove":MOVES["RECOVER"],"wCurEnemyMoveNum":1,
         "wEnemyMonItem":ITEMS["CHOICE_SCARF"],"wEnemyChoiceLockedMove":MOVES["DRAGON_RAGE"]}),
    ("encore_then_vest", {"mode":1,"forced":"TACKLE","reference_parse":True},
        {"wEnemySubStatus5":1<<SUBSTATUS_ENCORED,"wLastEnemyMove":MOVES["RECOVER"],"wCurEnemyMoveNum":1,"wEnemyMonItem":ITEMS["ASSAULT_VEST"]}),
    ("encore_vest_scans_to_slot_one", {"owned_moves":["RECOVER","TACKLE","DRAGON_RAGE","COUNTER"],
        "mode":1,"forced":"TACKLE","slot":1,"reference_parse":True},
        {"wEnemySubStatus5":1<<SUBSTATUS_ENCORED,"wLastEnemyMove":MOVES["RECOVER"],"wEnemyMonItem":ITEMS["ASSAULT_VEST"]}),
    ("encore_vest_no_attack", {"owned_moves":["RECOVER","AGILITY","PROTECT","REST"],
        "mode":1,"forced":"STRUGGLE","reference_parse":True},
        {"wEnemySubStatus5":1<<SUBSTATUS_ENCORED,"wLastEnemyMove":MOVES["RECOVER"],"wEnemyMonItem":ITEMS["ASSAULT_VEST"]}),
    ("recharge_wait", {"mode":2,"switches":0}, {"wEnemySubStatus4":32}),
    ("encore_before_recharge", {"mode":1,"forced":"RECOVER","slot":1,"switches":0,"reference_parse":True},
        {"wEnemySubStatus5":1<<SUBSTATUS_ENCORED,"wLastEnemyMove":MOVES["RECOVER"],"wCurEnemyMoveNum":1,"wEnemySubStatus4":32}),
    ("charged_bypasses_choice", {"mode":1,"forced":"FLY","switches":0,"reference_parse":True},
        {"wCurEnemyMove":MOVES["FLY"],"wEnemySubStatus3":16,"wEnemyMonItem":ITEMS["CHOICE_SCARF"],"wEnemyChoiceLockedMove":MOVES["DRAGON_RAGE"]}),
    ("rampage", {"mode":1,"forced":"THRASH","switches":0,"reference_parse":True},
        {"wCurEnemyMove":MOVES["THRASH"],"wEnemySubStatus3":2}),
    ("bide", {"mode":1,"forced":"BIDE","switches":0,"reference_parse":True},
        {"wCurEnemyMove":MOVES["BIDE"],"wEnemySubStatus3":1}),
    ("rollout", {"mode":1,"forced":"ROLLOUT","switches":0,"reference_parse":True},
        {"wCurEnemyMove":MOVES["ROLLOUT"],"wEnemySubStatus1":64}),
    ("trapped", {"moves":_CANDIDATE_MOVES,"switches":0}, {"wPlayerSubStatus5":128}),
    ("wrapped", {"moves":_CANDIDATE_MOVES,"switches":0}, {"wEnemyWrapCount":2}),
    ("wild_no_switch", {"moves":_CANDIDATE_MOVES,"switches":0}, {"wBattleMode":1}),
    ("link_no_switch", {"moves":_CANDIDATE_MOVES,"switches":0}, {"wLinkMode":1}),
    ("replacement_ignores_active_restrictions", {"kind":2,"mode":3},
        {"wPlayerSubStatus5":128,"wEnemyWrapCount":2,"wEnemySubStatus4":32,
         "wEnemySubStatus5":1<<SUBSTATUS_ENCORED,"wEnemyMonItem":ITEMS["CHOICE_BAND"]}),
    ("party_count_boundary", {"kind":2,"mode":3,"count":3,"switches":3}, {}),
    ("no_bench", {"moves":_CANDIDATE_MOVES,"active":0,"count":1,"switches":0}, {}),
]:
    CASES.append(Case(id="candidates_"+name,path="strategy/action-candidates",
        pins="complete legal slot enumeration follows combat's forced/item precedence without preference or HP vetoes",
        boss=Mon.of("SNORLAX",50,spec.get("owned_moves",_CANDIDATE_MOVES)),
        player=Mon.of("GENGAR",50,["SHADOW_BALL"]),scores=[80]*4,
        extra=extra,entry=(),expect={},candidate_check=spec))

for name, species, level, spec, extra in [
    ("inherited_above_hatch_level", "PIDGEY", 5, {"must_include":["QUICK_ATTACK"]}, {}),
    ("inherited_through_evolution", "PIDGEOTTO", 18, {"must_include":["AGILITY"]}, {}),
    ("baby", "PICHU", 5, {}, {}),
    ("pre_evolution", "PIKACHU", 5, {}, {}),
    ("two_ancestors_low_level", "RAICHU", 5, {}, {}),
    ("two_ancestors_high_level", "RAICHU", 50, {}, {}),
    ("stat_evolution", "HITMONTOP", 20, {}, {}),
    ("branched_evolution", "JOLTEON", 40, {}, {}),
    ("ordinary_boss_species", "GENGAR", 50, {}, {}),
    ("observed_beyond_learnability", "PIDGEY", 5, {"revealed":["RECOVER"]}, {}),
    ("four_observed", "PIDGEY", 5, {"revealed":["TACKLE","GROWL","SAND_ATTACK","QUICK_ATTACK"],"closed":True}, {}),
    ("temporary_observation_not_complete", "PIDGEY", 5, {"revealed":["TACKLE","GROWL","SLEEP_TALK","QUICK_ATTACK"]}, {}),
    ("tainted_history_not_complete", "PIDGEY", 5, {"revealed":["TACKLE","GROWL","SAND_ATTACK","QUICK_ATTACK"]},
        {"wBossAISeenPlayerSpeciesCount":1,"wBossAISeenPlayerSpecies":SPECIES["PIDGEY"],"wBossAIRevealedMovesBitmapSpare":1}),
    ("sketch_prior", "SMEARGLE", 20, {"authored":True}, {}),
    ("sketch_prior_with_observed", "SMEARGLE", 20, {"authored":True,"revealed":["TACKLE"]}, {}),
    ("sketch_four_observed", "SMEARGLE", 20, {"revealed":["TACKLE","GROWL","SAND_ATTACK","QUICK_ATTACK"],"closed":True}, {}),
    ("transformed_prior", "PIDGEY", 20, {"transformed":True,"broad":True}, {}),
    ("transformed_known", "DITTO", 20, {"transformed":True,"copied":["TACKLE","RECOVER","SEISMIC_TOSS","REST"]}, {}),
    ("transformed_known_bench_slot", "DITTO", 20, {"transformed":True,"copied":["EARTHQUAKE","ROCK_SLIDE"],"source_slot":2}, {}),
    ("transformed_known_with_observed", "MEW", 50, {"transformed":True,"copied":["TACKLE","RECOVER","SEISMIC_TOSS","REST"],"revealed":["SWIFT"]}, {}),
    ("transformed_source_out_of_range", "DITTO", 20, {"transformed":True,"broad":True}, {"wBossAITransformSource":7}),
    ("transformed_recorded_by_effect", "DITTO", 20, {"transformed":True,"copied":["TACKLE","RECOVER","SEISMIC_TOSS","REST"],"source_slot":1,"record":0}, {}),
    ("transformed_recorded_boss_turn_ignored", "DITTO", 20, {"transformed":True,"copied":["TACKLE","RECOVER","SEISMIC_TOSS","REST"],"source_slot":1,"record":1}, {}),
    ("transformed_recorded_no_boss_ignored", "DITTO", 20, {"transformed":True,"copied":["TACKLE","RECOVER","SEISMIC_TOSS","REST"],"source_slot":1,"record":0,"tier":0}, {}),
    ("not_transformed_ignores_source", "PIDGEY", 20, {}, {"wBossAITransformSource":1}),
    ("ditto_before_transform", "DITTO", 20, {}, {}),
    ("false_swipe_never_weighed", "SCYTHER", 40, {"revealed":["FALSE_SWIPE"]}, {}),
    ("false_swipe_not_in_closed_set", "SCYTHER", 40, {"revealed":["FALSE_SWIPE","SLASH","WING_ATTACK","AGILITY"],"closed":True}, {}),
]:
    CASES.append(Case(id="replies_"+name,path="strategy/public-replies",
        pins="exhaustive ROM learnability/ancestry plus observed moves, without hidden move/PP/item/input reads",
        boss=Mon.of("SNORLAX",50,["TACKLE"]),player=Mon.of(species,level,["TACKLE"]),
        extra=extra,entry=(),expect={},reply_check=spec))

for name, boss, player, spec, extra in [
    ("fast_finish", Mon.of("ALAKAZAM", 50, ["SEISMIC_TOSS", "RECOVER"]),
     Mon.of("PIDGEY", 5, ["TACKLE"]), {"best":0}, {}),
    # Was joint_broad_prior_mass while Smeargle's set was all 254 moves; it now
    # measures the authored Smeargle prior (16 moves) against five bench mons.
    ("smeargle_authored_prior", Mon.of("SNORLAX", 50, ["TACKLE", "RECOVER", "SEISMIC_TOSS", "REST"]),
     Mon.of("SMEARGLE", 50, ["TACKLE"]),
     {"revealed":["TACKLE"], "bench":[Mon.of("STEELIX",50,["TACKLE"]),
       Mon.of("PIDGEOT",50,["TACKLE"]),Mon.of("GENGAR",50,["TACKLE"]),
       Mon.of("ALAKAZAM",50,["TACKLE"]),Mon.of("MACHAMP",50,["TACKLE"])]}, {}),
    # The widest natural prior of any species at level 50 (58 moves): the
    # realistic worst case for the two-second budget now that Smeargle's set is
    # authored.
    ("broad_nidoqueen", Mon.of("SNORLAX", 50, ["TACKLE", "RECOVER", "SEISMIC_TOSS", "REST"]),
     Mon.of("NIDOQUEEN", 50, ["TACKLE"]),
     {"revealed":["TACKLE"], "bench":[Mon.of("STEELIX",50,["TACKLE"]),
       Mon.of("PIDGEOT",50,["TACKLE"]),Mon.of("GENGAR",50,["TACKLE"]),
       Mon.of("ALAKAZAM",50,["TACKLE"]),Mon.of("MACHAMP",50,["TACKLE"])]}, {}),
    # A transformed player mon whose Transform the boss saw: the reply set is
    # the boss's own remembered moves (slot 1) plus Struggle.
    ("transformed_known", Mon.of("SNORLAX", 50, ["TACKLE", "RECOVER", "SEISMIC_TOSS", "REST"]),
     Mon.of("DITTO", 50, ["TACKLE"]),
     {"bench":[Mon.of("STEELIX",50,["TACKLE"])]}, {"wPlayerSubStatus5": 8, "wBossAITransformSource": 1}),
    ("equal_slots", Mon.of("SNORLAX", 50, ["TACKLE", "TACKLE"]),
     Mon.of("PIDGEY", 50, ["TACKLE"]), {"best":0}, {}),
    ("cache_reinitialize", Mon.of("SNORLAX", 50, ["TACKLE", "TOXIC", "SEISMIC_TOSS", "QUIVER_DANCE"]),
     Mon.of("PIDGEY", 50, ["TACKLE"]), {}, {}),
    ("open_prior", Mon.of("SNORLAX", 50, ["TACKLE", "RECOVER"], hp_pct=30),
     Mon.of("PIDGEY", 50, ["TACKLE"]),
     {"revealed":["TACKLE"], "bench":[Mon.of("STEELIX", 50, ["EARTHQUAKE"])]}, {}),
    ("replacement_hazards", Mon.of("SNORLAX", 50, ["TACKLE"]),
     Mon.of("PIDGEY", 50, ["TACKLE"]),
     {"kind":2, "best":6, "check_ties":True, "tie_count":0, "bench":[Mon.of("STEELIX",50,["TACKLE"],hp_pct=1),
                                     Mon.of("PIDGEOT",50,["TACKLE"])]}, {"wEnemyScreens":3}),
    ("empty_replacement", Mon.of("SNORLAX", 50, ["TACKLE"]),
     Mon.of("PIDGEY", 50, ["TACKLE"]), {"kind":2,"best":255}, {}),
    ("recharge_wait", Mon.of("SNORLAX", 50, ["HYPER_BEAM"]),
     Mon.of("PIDGEY", 50, ["TACKLE"]), {"best":11,"check_ties":True,"tie_count":0,"wait_hazard_invariance":True}, {"wEnemySubStatus4":32,"wEnemyScreens":3}),
    ("exhausted_struggle", Mon.of("SNORLAX", 50, ["TACKLE"]),
     Mon.of("PIDGEY", 50, ["TACKLE"]), {"best":10}, {("wEnemyMonPP",0):0}),
    ("encore_exhausted", Mon.of("SNORLAX",50,["SEISMIC_TOSS"]),
     Mon.of("PIDGEY",50,["TACKLE"]), {"best":10,"forced_wait":True},
     {"wEnemySubStatus5":16,"wLastEnemyMove":MOVES["SEISMIC_TOSS"],("wEnemyMonPP",0):0}),
    ("encore_exhausted_confused", Mon.of("SNORLAX",50,["SEISMIC_TOSS"]),
     Mon.of("PIDGEY",50,["TACKLE"]), {"best":10,"forced_wait":True,"required_uncertainty":8},
     {"wEnemySubStatus5":16,"wEnemySubStatus3":128,"wLastEnemyMove":MOVES["SEISMIC_TOSS"],("wEnemyMonPP",0):0}),
    ("encore_disabled", Mon.of("SNORLAX",50,["SEISMIC_TOSS"]),
     Mon.of("PIDGEY",50,["TACKLE"]), {"best":10,"forced_wait":True},
     {"wEnemySubStatus5":16,"wLastEnemyMove":MOVES["SEISMIC_TOSS"],
      "wEnemyDisabledMove":MOVES["SEISMIC_TOSS"],"wEnemyDisableCount":2}),
    ("encore_disable_expires", Mon.of("SNORLAX",50,["SEISMIC_TOSS"]),
     Mon.of("PIDGEY",50,["TACKLE"]), {"best":10},
     {"wEnemySubStatus5":16,"wLastEnemyMove":MOVES["SEISMIC_TOSS"],
      "wEnemyDisabledMove":MOVES["SEISMIC_TOSS"],"wEnemyDisableCount":1}),
    ("encore_zero_counter_disabled", Mon.of("SNORLAX",50,["SEISMIC_TOSS"]),
     Mon.of("PIDGEY",50,["TACKLE"]), {"best":10,"forced_wait":True},
     {"wEnemySubStatus5":16,"wLastEnemyMove":MOVES["SEISMIC_TOSS"],
      "wEnemyDisabledMove":MOVES["SEISMIC_TOSS"],"wEnemyDisableCount":0}),
]:
    CASES.append(Case(id="joint_"+name,path="strategy/joint-actions",
        pins="all legal action/reply exchanges match exhaustive weighted aggregation in every traversal order",
        boss=boss,player=player,extra=extra,entry=(),expect={},joint_check=spec))


# Public-model speed ties use both orders without increasing a reply's prior.
_tie_moves = ["SEISMIC_TOSS", "QUICK_ATTACK", "VITAL_THROW", "RECOVER"]
for name, extra, tie_count in (
    ("mixed", {}, 8),
    ("quick_claw", {"wEnemyMonItem": ITEMS["QUICK_CLAW"]}, 0),
    # A transformed player mon in a boss battle always has its copy recorded
    # (BossAI_RecordPlayerTransform runs in the Transform effect); slot 1 is
    # the boss itself, so the reply set is its own four moves plus Struggle.
    ("transformed", {"wPlayerSubStatus5": 8, "wBossAITransformSource": 1}, 0),
    ("speed_high_byte", {("wEnemyMonSpeed", 0): 1}, 0),
):
    CASES.append(Case(id="joint_speed_tie_" + name, path="strategy/joint-actions",
        pins="modeled ties average explicit order branches with equal reply mass; unknown order remains conditional",
        boss=Mon.of("SNORLAX", 50, _tie_moves, hp_pct=10),
        player=Mon.of("SNORLAX", 50, ["SEISMIC_TOSS"], hp_pct=10),
        extra=extra, entry=(), expect={}, joint_check={"revealed":_tie_moves,
            "check_ties":True, "tie_count":tie_count, "tie_changes_outcome":bool(tie_count)}))

CASES.append(Case(id="joint_speed_tie_round_once", path="strategy/joint-actions",
    pins="odd order-branch sums round only after all reply weights are accumulated",
    boss=replace(Mon.of("SNORLAX", 50, _tie_moves), hp=20),
    player=replace(Mon.of("SNORLAX", 50, ["SEISMIC_TOSS"]), hp=10),
    extra={}, entry=(), expect={}, joint_check={"revealed":_tie_moves,
        "check_ties":True, "tie_count":8, "tie_changes_outcome":True,
        "early_rounding_difference":True, "bench":[Mon.of("SNORLAX",50,["TACKLE"])]}))


_accuracy_replies = ["FIRE_BLAST", "SELFDESTRUCT", "GIGA_DRAIN", "QUICK_ATTACK"]
for name, boss, player, extra, spec in [
    ("mixed", Mon.of("SNORLAX",50,["FIRE_BLAST","RECOVER","DOUBLE_EDGE","GIGA_DRAIN"],hp_pct=40),
     Mon.of("SNORLAX",50,["FIRE_BLAST"],hp_pct=40), {}, {"revealed":_accuracy_replies}),
    ("own_selfdestruct_miss", Mon.of("PIDGEOT",50,["SELFDESTRUCT"]),
     Mon.of("SNORLAX",50,["FIRE_BLAST"]), {"wEnemyAccLevel":1},
     {"revealed":_accuracy_replies,"own_miss_faints":0}),
    ("reply_selfdestruct_miss", Mon.of("SNORLAX",50,["RECOVER","TACKLE"]),
     Mon.of("PIDGEOT",50,["SELFDESTRUCT"]), {"wPlayerAccLevel":1},
     {"revealed":_accuracy_replies,"reply_miss_faints":"SELFDESTRUCT"}),
    ("early_ko", Mon.of("ALAKAZAM",50,["SEISMIC_TOSS"]),
     replace(Mon.of("SNORLAX",50,["FIRE_BLAST"]),hp=20), {},
     {"revealed":_accuracy_replies,"interrupted_reply":"FIRE_BLAST"}),
    ("impossible_hits", Mon.of("SNORLAX",50,["TACKLE"]),
     Mon.of("SNORLAX",50,["TACKLE"]), {"wEnemySubStatus3":64,"wPlayerSubStatus3":64},
     {"revealed":["TACKLE","GROWL","LEER","TAIL_WHIP"],"only_hit_event":3}),
    ("focus_band", Mon.of("SNORLAX",50,["TACKLE"]),
     Mon.of("SNORLAX",50,["TACKLE"]), {"wEnemyMonItem":ITEMS["FOCUS_BAND"]},
     {"revealed":["TACKLE","SEISMIC_TOSS","SWIFT","RECOVER"],"required_uncertainty":2}),
]:
    CASES.append(Case(id="joint_accuracy_"+name,path="strategy/joint-actions",
        pins="exact accuracy and order event weights match exhaustive conditional exchanges without early rounding",
        boss=boss,player=player,extra=extra,entry=(),expect={},
        joint_check=dict(spec,check_accuracy=True)))

CASES.append(Case(id="joint_defense_transitions",path="strategy/joint-actions",
    pins="defensive successor changes and prepared damage invalidation agree with exhaustive accuracy/tie enumeration",
    boss=Mon.of("SNORLAX",50,["BARRIER","AMNESIA","SCRATCH","SURF"]),
    player=Mon.of("SNORLAX",50,["BARRIER","AMNESIA","SCRATCH","SURF"]),
    extra={},entry=(),expect={},joint_check={"revealed":["BARRIER","AMNESIA","SCRATCH","SURF"],"check_accuracy":True}))

# The boss's own defense boosts against plain replies in both single orders
# (the tie is joint_defense_transitions): Defense+1 twice over, Defense+2 and
# Special Defense+2 behind both screens, both axes under Eviolite with the
# boss moving second, and a multihit reply that keeps the direct fallback.
_boost_replies = ["BODY_SLAM", "SURF", "SEISMIC_TOSS", "DOUBLE_EDGE"]
for name, boss, player, extra, revealed in (
    ("own_harden_first", Mon.of("PIDGEOT",50,["HARDEN","WITHDRAW","TACKLE","GUST"]),
     Mon.of("SNORLAX",50,["BODY_SLAM"]), {}, _boost_replies),
    ("own_barrier_screens_first", Mon.of("ALAKAZAM",50,["BARRIER","AMNESIA","PSYCHIC_M","RECOVER"]),
     Mon.of("SNORLAX",50,["BODY_SLAM"]), {"wEnemyScreens": 1 << 3 | 1 << 4}, _boost_replies),
    ("own_boosts_eviolite_slow", Mon.of("SLOWPOKE",50,["AMNESIA","WITHDRAW","SURF","REST"]),
     Mon.of("ALAKAZAM",50,["PSYCHIC_M"]), {"wEnemyMonItem": ITEMS["EVOLITE"]},
     ["PSYCHIC_M", "THUNDERBOLT", "SEISMIC_TOSS", "TRI_ATTACK"]),
    ("own_harden_multihit", Mon.of("PIDGEOT",50,["HARDEN","TACKLE"]),
     Mon.of("SNORLAX",50,["FURY_ATTACK"]), {}, ["FURY_ATTACK", "BODY_SLAM", "FALSE_SWIPE", "SURF"]),
):
    CASES.append(Case(id="joint_"+name,path="strategy/joint-actions",
        pins="the boss's own defense boosts lower the replies that follow them in every order, with screens and items",
        boss=boss,player=player,extra=extra,entry=(),expect={},
        joint_check={"revealed":revealed,"check_accuracy":True}))

# A transformed player mon carries the copied species in wBattleMonSpecies.
# The Transform recorder stashes which seen player species transformed, the
# faint recorder retires that entry (not the copied species), and the
# seen-species lookups neither record nor pollute the copied species while the
# transform lasts. Each branch is pinned at both polarities.
_seen_pidgey_ditto = {
    "wBossAISeenPlayerSpeciesCount": 2, "wBossAISeenPlayerSpecies": SPECIES["PIDGEY"],
    ("wBossAISeenPlayerSpecies", 1): SPECIES["DITTO"], "wBossAISeenPlayerAliveMask": 3}
for name, player, extra, entry, expect in (
    ("faint_untransformed_clears_species", Mon.of("DITTO", 20, ["TRANSFORM"]),
     {"wPlayerSubStatus5": 0}, ("BossAI_RecordPlayerFaint",),
     {"memory": {"wBossAISeenPlayerAliveMask": 1, "wBossAISeenPlayerSpeciesCount": 2}}),
    ("faint_transformed_clears_recorded_species", Mon.of("GENGAR", 20, ["TACKLE"]),
     {"wPlayerSubStatus5": 8, "wBossAITransformSource": 0x21}, ("BossAI_RecordPlayerFaint",),
     {"memory": {"wBossAISeenPlayerAliveMask": 1, "wBossAISeenPlayerSpeciesCount": 2}}),
    ("faint_transformed_without_record_keeps_bench", Mon.of("GENGAR", 20, ["TACKLE"]),
     {"wPlayerSubStatus5": 8, "wBossAITransformSource": 0x01}, ("BossAI_RecordPlayerFaint",),
     {"memory": {"wBossAISeenPlayerAliveMask": 3, "wBossAISeenPlayerSpeciesCount": 2}}),
    ("faint_transformed_record_out_of_range_keeps_bench", Mon.of("GENGAR", 20, ["TACKLE"]),
     {"wPlayerSubStatus5": 8, "wBossAITransformSource": 0x71}, ("BossAI_RecordPlayerFaint",),
     {"memory": {"wBossAISeenPlayerAliveMask": 3, "wBossAISeenPlayerSpeciesCount": 2}}),
    ("seen_index_untransformed_appends", Mon.of("GENGAR", 20, ["TACKLE"]),
     {"wPlayerSubStatus5": 0}, ("BossAI_GetActiveSpeciesSeenIndex",),
     {"a": 3, "memory": {"wBossAISeenPlayerSpeciesCount": 3, ("wBossAISeenPlayerSpecies", 2): SPECIES["GENGAR"]}}),
    ("seen_index_transformed_is_none", Mon.of("GENGAR", 20, ["TACKLE"]),
     {"wPlayerSubStatus5": 8}, ("BossAI_GetActiveSpeciesSeenIndex",),
     {"a": 0, "memory": {"wBossAISeenPlayerSpeciesCount": 2, ("wBossAISeenPlayerSpecies", 2): 0}}),
    ("used_moves_slot_untransformed_found", Mon.of("PIDGEY", 20, ["TACKLE"]),
     {"wPlayerSubStatus5": 0}, ("BossAI_GetActiveSpeciesUsedMovesPointer",), {"carry": True}),
    ("used_moves_slot_transformed_none", Mon.of("PIDGEY", 20, ["TACKLE"]),
     {"wPlayerSubStatus5": 8}, ("BossAI_GetActiveSpeciesUsedMovesPointer",), {"carry": False}),
    ("record_stashes_seen_index", Mon.of("DITTO", 20, ["TRANSFORM"]),
     {"wPlayerSubStatus5": 0, "hBattleTurn": 0, "wCurOTMon": 0}, ("BossAI_RecordPlayerTransform",),
     {"memory": {"wBossAITransformSource": 0x21, "wBossAISeenPlayerSpeciesCount": 2}}),
    ("record_boss_turn_ignored", Mon.of("DITTO", 20, ["TRANSFORM"]),
     {"wPlayerSubStatus5": 0, "hBattleTurn": 1, "wCurOTMon": 0}, ("BossAI_RecordPlayerTransform",),
     {"memory": {"wBossAITransformSource": 0, "wBossAISeenPlayerSpeciesCount": 2}}),
    ("record_unseen_species_appends", Mon.of("MEW", 20, ["TRANSFORM"]),
     {"wPlayerSubStatus5": 0, "hBattleTurn": 0, "wCurOTMon": 2}, ("BossAI_RecordPlayerTransform",),
     {"memory": {"wBossAITransformSource": 0x33, "wBossAISeenPlayerSpeciesCount": 3}}),
):
    CASES.append(Case(id="transform_"+name, path="strategy/transform-bookkeeping",
        pins="a transformed player mon is bookkept as the Pokémon that transformed, never as the copied species",
        boss=Mon.of("SNORLAX", 50, ["TACKLE"]), player=player, entry=entry,
        extra={**_seen_pidgey_ditto, **extra}, expect=expect))

# BossAI_TrySwitch keeps the tier switch threshold in c across three helpers.
# Each helper must hand bc back untouched on both of its answers; the review
# of 2026-09-08 found all three clobbering it (a type id, a party slot or a
# player HP byte was compared against the 60/70/80 threshold instead).
_two_gengar = _bench(["GENGAR", "GENGAR"], threat="NORMAL")
for name, boss, extra, entry, carry in (
    ("wincon_path", gengar(), {"wBossAIWinconMonIdx": 2}, ("BossAI_IsSwitchingIntoWinconRisk",), None),
    ("not_wincon", gengar(), {"wBossAIWinconMonIdx": 1}, ("BossAI_IsSwitchingIntoWinconRisk",), False),
    ("loop_exceptions", gengar(), {"wBossAISwitchCooldown": 1, "wBossAILastSwitchedOut": 2}, ("BossAI_NeedsLoopPenalty",), None),
    ("no_cooldown", gengar(), {"wBossAISwitchCooldown": 0}, ("BossAI_NeedsLoopPenalty",), False),
    ("sack_low_hp", Mon.of("GENGAR", 26, ["LICK"], hp_pct=10), {"wBossAIWinconMonIdx": 2, "wBossAIHasKOMoveCache": 0}, ("BossAI_ShouldSackInsteadOfSwitch",), True),
    ("sack_full_hp", gengar(), {"wBossAIWinconMonIdx": 2, "wBossAIHasKOMoveCache": 0}, ("BossAI_ShouldSackInsteadOfSwitch",), False),
):
    expect = {"bc": 0x1246}
    if carry is not None:
        expect["carry"] = carry
    CASES.append(Case(id="switch_threshold_"+name, path="strategy/switch-threshold",
        pins="the threshold helpers preserve bc on both answers, so BossAI_TrySwitch compares confidence against the tier threshold and not helper scratch",
        boss=boss, player=magnemite(), entry=entry, registers={"B": 0x12, "C": 0x46},
        extra={**_two_gengar, **extra}, expect=expect))

# The role-package mask of the player's last move: one bit per role, or none.
# BossAI_IsStatusEffect used to let IsInArray overwrite b and c, so every mask
# came back as the move effect id with stray bits and the trap/perish role was
# unreachable.
for move, mask in (("ROAR", 1 << 1), ("THUNDER_WAVE", 1 << 5), ("MEAN_LOOK", 1 << 6),
                   ("SPIKES", 0), ("EARTHQUAKE", 1 << 7), ("RECOVER", 1 << 3),
                   ("SWORDS_DANCE", 1 << 2), ("QUICK_ATTACK", 1 << 4), ("RAPID_SPIN", 1 << 0)):
    CASES.append(Case(id=f"role_mask_{move}", path="strategy/role-package",
        pins="the last player move maps to exactly its role bits (status, trap and none included)",
        boss=gengar(), player=magnemite(), entry=("BossAI_LastPlayerMoveRolePackageMask",),
        extra={"wLastPlayerMove": MOVES[move]}, expect={"a": mask}))

# A Mean Looked or Wrapped ace keeps its once-per-battle Haki read (the move
# half is legal while trapped); only the switch half is refused.
for trap, extra in (("free", {}), ("mean_look", {"wPlayerSubStatus5": 128}), ("wrap", {"wEnemyWrapCount": 2})):
    CASES.append(Case(id=f"haki_read_while_{trap}", path="haki/gates",
        pins="the boss-first dispatch reaches the Haki read even when the boss cannot switch",
        boss=gengar(), player=magnemite(), entry=("AI_SwitchOrTryItem",), prescore=True,
        extra=_haki_ready({"wBattleMode": 2, "wLinkMode": 0, "wEnemySwitchMonIndex": 0, **extra}),
        expect={"haki_spent": True, "choice_ready": 1, "chosen_move_not": [IMMUNE_MOVE],
                "memory": {"wEnemySwitchMonIndex": 0}}))
# Ground into Magnemite with a Ground-immune Gengar on the bench: the Haki
# pivot is found when the boss is free and refused when it is trapped.
for trap, extra, found in (("free", {}, True), ("mean_look", {"wPlayerSubStatus5": 128}, False),
                           ("wrap", {"wEnemyWrapCount": 2}, False)):
    CASES.append(Case(id=f"haki_pivot_{trap}", path="haki/gates",
        pins="the Haki immunity pivot is legal only when the boss can switch",
        boss=Mon.of("MAGNEMITE", 24, ["THUNDERBOLT"]), player=Mon.of("GEODUDE", 24, ["EARTHQUAKE"]),
        entry=("BossAI_HakiFindImmunitySwitch",),
        extra={**_bench(["MAGNEMITE", "GENGAR"], threat="GROUND"), "wCurPlayerMove": MOVES["EARTHQUAKE"], **extra},
        expect={"carry": found}))

# The KO-band oracle is consulted for every super-effective move, STAB or
# coverage, and never for a resisted one (its own gate would refuse anyway).
for name, boss, player, move, calls in (
    ("stab_se", gengar(), Mon.of("ALAKAZAM", 40, ["PSYCHIC_M"]), "SHADOW_BALL", 1),
    ("coverage_se", gengar(), Mon.of("MANTINE", 40, ["SURF"]), "THUNDERBOLT", 1),
    ("resisted", Mon.of("SNORLAX", 40, ["BODY_SLAM"]), Mon.of("STEELIX", 40, ["TACKLE"]), "BODY_SLAM", 0),
):
    CASES.append(Case(id=f"ko_band_oracle_{name}", path="strategy/ko-band-oracle",
        pins="super-effective coverage reaches the KO-band oracle like STAB does; resisted moves skip it",
        boss=boss, player=player, entry=("AIGetEnemyMove_HL", "BossAI_CurrentEnemyMovePressureScore"),
        registers={"A": MOVES[move]}, tier=AI_TIER_MID,
        expect={"calls": {"BossAI_ApplyKOBandOraclePressure": calls}}))

# The Speed-cap rule by base Speed band (CLAUDE.md): >= 90 caps at +1,
# 60..89 at +2, <= 59 at +3, pinned one stage either side of every boundary
# with the public speed estimate held at "not faster".
for base, stage, further in ((90, 0, True), (90, 1, False), (89, 1, True), (89, 2, False),
                             (60, 1, True), (60, 2, False), (59, 2, True), (59, 3, False)):
    CASES.append(Case(id=f"speed_cap_base{base}_stage{stage}", path="strategy/setup-window",
        pins="Agility has further value only below the base-Speed band cap",
        boss=Mon.of("GENGAR", 26, ["AGILITY"]), player=magnemite(),
        entry=("AIGetEnemyMove_HL", "BossAI_SetupBoostHasFurtherValue"), registers={"A": MOVES["AGILITY"]},
        extra={("wEnemyMonBaseStats", 3): base, "wEnemySpdLevel": 7 + stage, "wBossAIPublicEnemyFasterCache": 0},
        expect={"carry": further}))

# Haki eligibility: the last excluded class (the loop must advance past the
# first entry) and the baseline tier (the tier gate's zero polarity).
CASES.append(Case(id="eligible_excluded_last_class_refused", path="haki/eligibility",
    pins="the excluded-class walk reaches the last table entry",
    boss=gengar(), player=magnemite(), entry=("BossAI_HakiTrainerEligible",), tier=AI_TIER_MID,
    extra={"wTrainerClass": TRAINER_CLASSES["BLAINE"]}, expect={"carry": False}))
CASES.append(Case(id="eligible_baseline_tier_refused", path="haki/eligibility",
    pins="a non-boss tier never arms a Haki window",
    boss=gengar(), player=magnemite(), entry=("BossAI_HakiTrainerEligible",), tier=0,
    extra={"wTrainerClass": TRAINER_CLASSES["MORTY"]}, expect={"carry": False}))

# A bench mon that faints to entry hazards reaches no reply: identity
# (zero-power) replies must carry no flags at that start state, exactly as
# plain damage replies do. Found by the 2026-09-08 review as a frozen-oracle
# mismatch on the switch record's uncertainty byte.
CASES.append(Case(id="joint_entry_ko_identity_replies", path="strategy/joint-actions",
    pins="identity replies at a start state the bench mon does not survive carry no flags",
    boss=Mon.of("SNORLAX", 50, ["TACKLE", "RECOVER"]), player=Mon.of("PIDGEY", 50, ["TACKLE"]),
    extra={"wEnemyScreens": 3}, entry=(), expect={},
    joint_check={"revealed": ["GROWL", "LEER", "AGILITY", "SPLASH"],
                 "bench": [Mon.of("STEELIX", 50, ["TACKLE"], hp_pct=1)]}))

# Ordinary (tier-0) trainer layer: the chart stops damaging moves only. An
# immune attack is blocked at 80; a status move into the same defender keeps
# vanilla's +10 nudge (Growl still lands on a Ghost).
CASES.append(Case(id="tier0_types_immune_status_only_discouraged", path="normal/tier-zero",
    pins="AI_Types blocks an immune attack and only discourages a status move of an immune type",
    boss=Mon.of("PIDGEY", 20, ["GROWL", "TACKLE"]), player=Mon.of("GENGAR", 26, ["LICK"]),
    tier=0, scores=[20, 20, 20, 20], entry=("AI_Types",),
    expect={"memory": {"wEnemyAIMoveScores": 30, ("wEnemyAIMoveScores", 1): 80}}))

# One definition of "ace" (design lead, 2026-09-09): the highest-level party
# member, later slot on ties. The ace-timing switch hook and the Haki window
# must agree.
_three_gengar = _bench(["GENGAR", "GENGAR", "GENGAR"])
for name, levels, slot, ace in (("highest_mid_slot", (30, 50, 40), 1, True),
                                ("last_slot_not_highest", (30, 50, 40), 2, False),
                                ("tie_later_slot", (30, 50, 50), 2, True),
                                ("tie_earlier_slot", (30, 50, 50), 1, False)):
    extra = {**_three_gengar, "wEnemySwitchMonParam": 0x30 | slot, "wTrainerClass": TRAINER_CLASSES["CLAIR"],
             "wBossAITurnsElapsed": 5}
    for i, level in enumerate(levels):
        extra[f"wOTPartyMon{i + 1}Level"] = level
    CASES.append(Case(id=f"ace_timing_{name}", path="strategy/ace",
        pins="the ace-timing hook uses the highest-level rule, later slot on ties",
        boss=gengar(), player=magnemite(), tier=AI_TIER_LATE, entry=("BossAI_AceTimingHook",),
        extra=extra, expect={"carry": ace}))
    CASES.append(Case(id=f"current_is_ace_{name}", path="strategy/ace",
        pins="the Haki window's ace test is the same highest-level rule",
        boss=gengar(), player=magnemite(), entry=("BossAI_CurrentEnemyIsAce",),
        extra={**extra, "wCurOTMon": slot}, expect={"carry": ace}))


# Baton Pass: exact tier-scaled score deltas, with cached public facts isolated.
# Prediction >=40: historic switching plus public quarter HP gives 50 points.
def _baton_prediction(predicted):
    return {"wBossAITurnsElapsed": 4, "wBossAIPlayerSwitchCount": 2 if predicted else 0,
            "wBattleMonHP": 0, ("wBattleMonHP", 1): 10 if predicted else 100,
            "wBattleMonMaxHP": 0, ("wBattleMonMaxHP", 1): 100}


def _baton_case(name, verdict, *, status=0, setup=False, available=True,
                threat=0, faster=1, hp=100, predicted=False, toxic=False,
                poison=False, ko=0, sub=False, seed=False, perish=0, boost=7,
                bench=True, attack=False, disabled=False):
    for tier, row, weights in [(AI_TIER_EARLY, 0, (4, 1, 1, 1)),
                               (AI_TIER_LATE, 2, (7, 4, 2, 3))]:
        # BossAITierWeights columns: ko=0, tempo=2, status=4, role=5.
        ko_weight, tempo_weight, status_weight, role_weight = weights
        score = {"strong":20-tempo_weight, "moderate":20-role_weight,
                 "small":20-status_weight, "cargo":20-ko_weight,
                 "penalty":26+ko_weight, "mild":26}[verdict]
        passer = "LEDIAN" if tier == AI_TIER_EARLY else "ESPEON"
        extra = _bench([passer, "SNORLAX"] if bench else [passer], threat="NORMAL")
        extra.update(_baton_prediction(predicted))
        extra.update({"wBossAITierWeightRow":row, "wBossAIPublicThreatCache":threat,
                      "wBossAIPublicEnemyFasterCache":faster, "wBossAIHasKOMoveCache":ko,
                      "wEnemyMonHP":0, ("wEnemyMonHP",1):hp,
                      "wEnemyMonMaxHP":0, ("wEnemyMonMaxHP",1):100,
                      "wEnemySubStatus4":(16 if sub else 0) | (128 if seed else 0),
                      "wEnemySubStatus5":1 if toxic else 0,
                      "wEnemySubStatus1":16 if perish else 0, "wEnemyPerishCount":perish,
                      "wEnemyAtkLevel":boost,
                      "wEnemyDisabledMove":MOVES["QUIVER_DANCE"] if disabled else 0})
        moves = ["BATON_PASS"] + (["QUIVER_DANCE"] if setup else []) + (["STRENGTH"] if attack else [])
        if setup and not available:
            extra[("wEnemyMonPP",1)] = 0
        CASES.append(Case(id=f"baton_{name}_tier{tier}", path="strategy/baton-pass",
            pins=f"{name}: {verdict}; paired public-state and availability boundaries",
            boss=Mon.of(passer,18 if tier == AI_TIER_EARLY else 62,moves,
                        status=8 if toxic or poison else 0),
            player=Mon.of("SNORLAX",62,[],status=status),
            tier=tier, entry=("AIGetEnemyMove_HL","BossAI_ApplyMoveModel.ApplyBatonPassBias"),
            registers={"A":MOVES["BATON_PASS"]}, scores=[20]*4, extra=extra,
            expect={"memory":{"wEnemyAIMoveScores":score}}))

_baton_case("neutral", "mild")
_baton_case("sleep_no_setup", "strong", status=3)
_baton_case("sleep_setup", "mild", status=3, setup=True)
_baton_case("sleep_setup_no_pp", "strong", status=3, setup=True, available=False)
_baton_case("sleep_setup_disabled", "strong", status=3, setup=True, disabled=True)
_baton_case("freeze_no_setup", "strong", status=32)
_baton_case("freeze_setup", "mild", status=32, setup=True)
_baton_case("paralysis", "mild", status=64)
_baton_case("player_poison", "mild", status=8)
_baton_case("predict_threat", "moderate", predicted=True, threat=1, setup=True)
_baton_case("no_predict_fast_threat", "mild", threat=1, setup=True)
_baton_case("predict_no_stay_value", "moderate", predicted=True)
_baton_case("predict_setup_value", "mild", predicted=True, setup=True)
_baton_case("predict_attack_value", "mild", predicted=True, attack=True)
_baton_case("slow_threat_above_half", "moderate", threat=1, faster=0, hp=51)
_baton_case("fast_threat_above_half", "mild", threat=1, faster=1, hp=51)
_baton_case("slow_threat_at_half", "mild", threat=1, faster=0, hp=50)
_baton_case("slow_threat_below_half", "mild", threat=1, faster=0, hp=49)
_baton_case("slow_no_threat", "mild", faster=0, hp=51)
_baton_case("own_toxic", "small", toxic=True)
_baton_case("own_plain_poison", "mild", poison=True)
_baton_case("ko_over_sleep", "penalty", status=3, ko=1)
_baton_case("ko_over_prediction", "penalty", predicted=True, ko=1)
_baton_case("substitute", "cargo", sub=True)
_baton_case("boost", "cargo", boost=8)
_baton_case("seed_over_substitute", "penalty", sub=True, seed=True)
_baton_case("seed_dry", "penalty", seed=True)
_baton_case("perish_one", "penalty", perish=1)
_baton_case("perish_two", "mild", perish=2)
_baton_case("no_bench_sleep", "mild", status=3, bench=False)

# Drive the real effect through the Set-mode predetermined-index consumer.
# Only rendering is bypassed; stop before loading/animating the incoming mon.
for tier in (0, AI_TIER_LATE):
    for threat, species, expected in [("WATER", "VAPOREON", 3), ("ELECTRIC", "AMPHAROS", 2)]:
        extra = _bench(["ESPEON","GOLEM","LANTURN"], threat=threat)
        extra.update({"wBattleMode":2,"wLinkMode":0,"wBattleHasJustStarted":0,
                      "wEnemySwitchMonIndex":5})
        for i, move in [(2,"EARTHQUAKE"),(3,"THUNDERBOLT")]:
            for slot in range(4):
                extra[(f"wOTPartyMon{i}Moves",slot)] = MOVES[move] if slot==0 else 0
                extra[(f"wOTPartyMon{i}PP",slot)] = 10 if slot==0 else 0
        CASES.append(Case(id=f"baton_picker_{threat}_tier{tier}",path="strategy/baton-pass",
            pins="effect uses resolved active matchup; tier zero keeps vanilla routing; stale index cleared",
            boss=Mon.of("ESPEON",62,["BATON_PASS"]), player=Mon.of(species,62,[]),tier=tier,
            entry=("BattleCommand_BatonPass.Enemy",), extra=extra,
            skip_calls=("AnimateCurrentMove","SlideBattlePicOut","EmptyBattleTextbox","LoadStandardMenuHeader"),stop_at="LoadEnemyMonToSwitchTo",
            expect={"memory":{"wEnemySwitchMonIndex":expected if tier else 0},
                    "calls":{"BossAI_FaintRepl_EvalCandidate":3 if tier else 0,
                             "FindMonInOTPartyToSwitchIntoBattle":0 if tier else 1}}))
