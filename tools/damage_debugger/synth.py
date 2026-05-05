"""Synthetic damage-calc scenarios.

Instead of driving real gameplay to a damage moment, we boot the ROM,
let it initialize basic state, then manually populate WRAM with a
controlled battle context (attacker/defender stats, move power, items,
stat-stage levels, etc.) and call BattleCommand_DamageCalc directly by
setting PC + pushing a sentinel return address.

This is the unit-test path: total control over inputs, repeatable, and
reveals divergence between the live calc and the pure-Python oracle
(M7) the moment one occurs.

The synthetic context is described by a SynthBattle dataclass; the
runner sets up WRAM and runs DamageCalc, returning a Tracer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .emulator import DebugSession
from .tracer import Tracer


# Constants we care about (resolved at runtime from sym; defaults match
# the current build but symbols win).
DEFAULT_BOOT_FRAMES = 240  # Enough to get past Init / RAM-clear


# Stat layout in wPlayerMon / wEnemyMon (computed stats, big-endian u16):
#   +0 Attack  +2 Defense  +4 Speed  +6 SpAtk  +8 SpDef
# (Verified by sym: wEnemyMonAttack=01:d103, wEnemyMonDefense=01:d105.)


@dataclass
class SynthMon:
    """One Pokémon's runtime battle slot (computed stats + meta)."""
    species: int = 0x9C        # CYNDAQUIL=0x9C in this build
    level: int = 50
    type1: int = 0x14          # FIRE
    type2: int = 0x14          # FIRE (monotype)
    item: int = 0              # 0 = no item
    attack: int = 100
    defense: int = 100
    speed: int = 100
    spatk: int = 100
    spdef: int = 100
    max_hp: int = 200
    cur_hp: int = 200
    atk_stage: int = 7         # +0 (BASE_STAT_LEVEL=7)
    def_stage: int = 7
    spe_stage: int = 7
    spa_stage: int = 7
    spd_stage: int = 7


@dataclass
class SynthMove:
    """A move struct (matches wPlayerMoveStruct layout)."""
    move_id: int = 0xA1        # ROCK_THROW=0xA1 typical (verify per build)
    effect: int = 0x00         # EFFECT_NORMAL_HIT=0
    power: int = 50
    type: int = 0x05           # ROCK
    accuracy: int = 0x90       # 90/256? or percent... rendered as %
    pp: int = 15
    crit: int = 0


@dataclass
class SynthBattle:
    """Full pre-DamageCalc state."""
    name: str = "synth_baseline"
    player: SynthMon = field(default_factory=SynthMon)
    enemy: SynthMon = field(default_factory=SynthMon)
    move: SynthMove = field(default_factory=SynthMove)
    is_player_turn: bool = True   # which side is attacking
    is_critical: bool = False
    move_category_physical: bool = True
    type_effectiveness: int = 0x10  # 1.0× neutral (Gen2 uses 0x10 = 16/16)
    boot_frames: int = DEFAULT_BOOT_FRAMES


# Pokemon Gold/Silver battle struct constants (offsets within
# wBattleMon / wEnemyMon). Many of these are in CLAUDE.md and sym.
# We only set the ones relevant to DamageCalc execution.
def write_be_u16(sess: DebugSession, bank: int, addr: int, value: int) -> None:
    """Battle stat fields are runtime-populated big-endian."""
    hi = (value >> 8) & 0xFF
    lo = value & 0xFF
    if 0xD000 <= addr <= 0xDFFF and bank:
        old = int(sess.pyboy.memory[0xFF70])
        sess.pyboy.memory[0xFF70] = bank
        try:
            sess.pyboy.memory[addr] = hi
            sess.pyboy.memory[addr + 1] = lo
        finally:
            sess.pyboy.memory[0xFF70] = old
    else:
        sess.pyboy.memory[addr] = hi
        sess.pyboy.memory[addr + 1] = lo


def write_byte(sess: DebugSession, bank: int, addr: int, value: int) -> None:
    if 0xD000 <= addr <= 0xDFFF and bank:
        old = int(sess.pyboy.memory[0xFF70])
        sess.pyboy.memory[0xFF70] = bank
        try:
            sess.pyboy.memory[addr] = value & 0xFF
        finally:
            sess.pyboy.memory[0xFF70] = old
    else:
        sess.pyboy.memory[addr] = value & 0xFF


def install_synth_battle(sess: DebugSession, battle: SynthBattle) -> None:
    """Populate WRAM with battle's state, leaving the game in a position
    where calling BattleCommand_DamageCalc with d/b/c/e set up will run
    the calc against this scenario.

    We *don't* set up everything a real battle has — only the fields
    DamageCalc and its callees read. Other fields are whatever the boot
    sequence left there (mostly zero).
    """
    # --- Player mon (wBattleMon* in this codebase, but we'll resolve
    # symbols defensively).
    sym = sess.symbols
    pmon = battle.player
    emon = battle.enemy
    move = battle.move

    # Battle-mon stat slots (computed) — sym names differ; try common ones.
    def trywrite_u16(name: str, value: int) -> bool:
        s = sym.get(name)
        if s is None:
            return False
        write_be_u16(sess, s.bank, s.address, value)
        return True

    def trywrite_byte(name: str, value: int) -> bool:
        s = sym.get(name)
        if s is None:
            return False
        write_byte(sess, s.bank, s.address, value)
        return True

    # Try multiple sym name conventions (this hack vs vanilla pokegold).
    PLAYER_STAT_NAMES = ("wBattleMonAttack", "wBattleMonAtk", "wPlayerMonAttack")
    PLAYER_DEF_NAMES = ("wBattleMonDefense", "wBattleMonDef", "wPlayerMonDefense")
    PLAYER_SPE_NAMES = ("wBattleMonSpeed", "wBattleMonSpe", "wPlayerMonSpeed")
    PLAYER_SPA_NAMES = ("wBattleMonSpclAtk", "wBattleMonSpAtk", "wPlayerMonSpclAtk")
    PLAYER_SPD_NAMES = ("wBattleMonSpclDef", "wBattleMonSpDef", "wPlayerMonSpclDef")
    PLAYER_LV_NAMES = ("wBattleMonLevel", "wPlayerMonLevel")
    PLAYER_HP_NAMES = ("wBattleMonHP", "wPlayerMonHP")
    PLAYER_TYPE1_NAMES = ("wBattleMonType1", "wPlayerMonType1")
    PLAYER_TYPE2_NAMES = ("wBattleMonType2", "wPlayerMonType2")
    PLAYER_ITEM_NAMES = ("wBattleMonItem", "wPlayerMonItem")
    PLAYER_SPECIES_NAMES = ("wBattleMonSpecies", "wPlayerMonSpecies")

    ENEMY_STAT_NAMES = ("wEnemyMonAttack",)
    ENEMY_DEF_NAMES = ("wEnemyMonDefense",)
    ENEMY_SPE_NAMES = ("wEnemyMonSpeed",)
    ENEMY_SPA_NAMES = ("wEnemyMonSpclAtk", "wEnemyMonSpAtk")
    ENEMY_SPD_NAMES = ("wEnemyMonSpclDef", "wEnemyMonSpDef")
    ENEMY_LV_NAMES = ("wEnemyMonLevel",)
    ENEMY_HP_NAMES = ("wEnemyMonHP",)
    ENEMY_TYPE1_NAMES = ("wEnemyMonType1",)
    ENEMY_TYPE2_NAMES = ("wEnemyMonType2",)
    ENEMY_ITEM_NAMES = ("wEnemyMonItem",)
    ENEMY_SPECIES_NAMES = ("wEnemyMonSpecies",)

    def write_mon(mon: SynthMon, prefix: str,
                  stat_names, def_names, spe_names, spa_names, spd_names,
                  lv_names, hp_names, t1_names, t2_names, item_names, sp_names) -> dict:
        results = {}
        for name in stat_names:
            if trywrite_u16(name, mon.attack):
                results["attack_at"] = name; break
        for name in def_names:
            if trywrite_u16(name, mon.defense):
                results["defense_at"] = name; break
        for name in spe_names:
            if trywrite_u16(name, mon.speed):
                results["speed_at"] = name; break
        for name in spa_names:
            if trywrite_u16(name, mon.spatk):
                results["spatk_at"] = name; break
        for name in spd_names:
            if trywrite_u16(name, mon.spdef):
                results["spdef_at"] = name; break
        for name in lv_names:
            if trywrite_byte(name, mon.level):
                results["level_at"] = name; break
        for name in hp_names:
            if trywrite_u16(name, mon.cur_hp):
                results["hp_at"] = name; break
        for name in t1_names:
            if trywrite_byte(name, mon.type1):
                results["type1_at"] = name; break
        for name in t2_names:
            if trywrite_byte(name, mon.type2):
                results["type2_at"] = name; break
        for name in item_names:
            if trywrite_byte(name, mon.item):
                results["item_at"] = name; break
        for name in sp_names:
            if trywrite_byte(name, mon.species):
                results["species_at"] = name; break
        return results

    p_results = write_mon(pmon, "Player",
                          PLAYER_STAT_NAMES, PLAYER_DEF_NAMES, PLAYER_SPE_NAMES,
                          PLAYER_SPA_NAMES, PLAYER_SPD_NAMES, PLAYER_LV_NAMES,
                          PLAYER_HP_NAMES, PLAYER_TYPE1_NAMES, PLAYER_TYPE2_NAMES,
                          PLAYER_ITEM_NAMES, PLAYER_SPECIES_NAMES)
    e_results = write_mon(emon, "Enemy",
                          ENEMY_STAT_NAMES, ENEMY_DEF_NAMES, ENEMY_SPE_NAMES,
                          ENEMY_SPA_NAMES, ENEMY_SPD_NAMES, ENEMY_LV_NAMES,
                          ENEMY_HP_NAMES, ENEMY_TYPE1_NAMES, ENEMY_TYPE2_NAMES,
                          ENEMY_ITEM_NAMES, ENEMY_SPECIES_NAMES)

    # Stat-stage levels (base-7 encoded; +0 = 7, +6 = 13)
    trywrite_byte("wPlayerAtkLevel", pmon.atk_stage)
    trywrite_byte("wPlayerDefLevel", pmon.def_stage)
    trywrite_byte("wPlayerSpdLevel", pmon.spe_stage)
    trywrite_byte("wPlayerSAtkLevel", pmon.spa_stage)
    trywrite_byte("wPlayerSDefLevel", pmon.spd_stage)
    trywrite_byte("wEnemyAtkLevel", emon.atk_stage)
    trywrite_byte("wEnemyDefLevel", emon.def_stage)
    trywrite_byte("wEnemySpdLevel", emon.spe_stage)
    trywrite_byte("wEnemySAtkLevel", emon.spa_stage)
    trywrite_byte("wEnemySDefLevel", emon.spd_stage)

    # Move struct (wPlayerMoveStruct layout, 7 bytes typically)
    move_sym = sym.get("wPlayerMoveStruct")
    if move_sym is None:
        move_sym = sym.get("wEnemyMoveStruct")
    if move_sym is not None:
        # Standard layout: anim, effect, power, type, accuracy, pp, crit
        # See macros/wram.asm or move_struct in this build.
        bank = move_sym.bank
        base = move_sym.address
        write_byte(sess, bank, base + 0, move.move_id)        # anim/move_id
        write_byte(sess, bank, base + 1, move.effect)         # effect
        write_byte(sess, bank, base + 2, move.power)          # power
        write_byte(sess, bank, base + 3, move.type)           # type
        write_byte(sess, bank, base + 4, move.accuracy)       # acc
        write_byte(sess, bank, base + 5, move.pp)             # pp
        write_byte(sess, bank, base + 6, move.crit)           # crit_rate

    # wCurPlayerMove / wCurEnemyMove
    trywrite_byte("wCurPlayerMove", move.move_id)
    trywrite_byte("wCurEnemyMove", move.move_id)

    # Critical hit + type matchup
    trywrite_byte("wCriticalHit", 0x01 if battle.is_critical else 0x00)
    trywrite_byte("wTypeMatchup", battle.type_effectiveness)
    trywrite_byte("wIsConfusionDamage", 0)
    trywrite_byte("wEffectFailed", 0)

    # Battle turn
    trywrite_byte("hBattleTurn", 0 if battle.is_player_turn else 1)

    return {
        "player_addrs": p_results,
        "enemy_addrs": e_results,
        "move_at": move_sym.name if move_sym else None,
    }


def boot_to_ready(sess: DebugSession, frames: int = DEFAULT_BOOT_FRAMES) -> None:
    """Tick past initial boot/init so HRAM/WRAM scratch is in defined state."""
    sess.tick(frames)


def call_function(sess: DebugSession, name: str, *,
                  budget: int = 600, sentinel: int = 0x0008,
                  setup_args: dict | None = None) -> int:
    """Push a sentinel return address and run the named function until it
    returns. Returns the number of frames ticked. Args via setup_args may
    set rf.B/.C/.D/.E/.A before invoking.
    """
    sym = sess.symbols.get(name)
    if sym is None:
        raise KeyError(f"{name} not in sym table")
    rf = sess.pyboy.register_file
    sp = int(rf.SP)
    new_sp = (sp - 2) & 0xFFFF
    sess.pyboy.memory[new_sp] = sentinel & 0xFF
    sess.pyboy.memory[new_sp + 1] = (sentinel >> 8) & 0xFF
    rf.SP = new_sp
    if setup_args:
        for k, v in setup_args.items():
            setattr(rf, k.upper(), v & 0xFF if k.upper() not in ("HL", "SP", "PC") else v & 0xFFFF)
    rf.PC = sym.address
    rom_bank_sym = sess.symbols.get("hROMBank")
    if rom_bank_sym is not None:
        sess.pyboy.memory[rom_bank_sym.address] = sym.bank
    sess.pyboy.memory[0x2000] = sym.bank

    returned = [False]
    def on_ret(_ctx):
        returned[0] = True
    sess.hook_register(0x00, sentinel, on_ret, None)
    ticked = 0
    try:
        while ticked < budget and not returned[0]:
            sess.tick(2, False)
            ticked += 2
    finally:
        sess.hook_deregister(0x00, sentinel)
    if not returned[0]:
        raise RuntimeError(f"{name} did not return within {budget} frames")
    return ticked


def read_cur_damage(sess: DebugSession) -> int | None:
    s = sess.symbols.get("wCurDamage")
    if s is None:
        return None
    hi = int(sess.pyboy.memory[s.bank, s.address])
    lo = int(sess.pyboy.memory[s.bank, s.address + 1])
    return (hi << 8) | lo


def run_synth(battle: SynthBattle, *, rom: str = "pokegold_trace",
              chain: tuple[str, ...] | None = None) -> dict[str, Any]:
    """Run a synthesized damage chain. By default calls just
    BattleCommand_DamageCalc; pass chain to call multiple functions in
    sequence (e.g. ('BattleCommand_Critical', 'BattleCommand_DamageStats',
    'BattleCommand_DamageCalc', 'BattleCommand_Stab')).
    """
    if chain is None:
        chain = ("BattleCommand_DamageCalc",)
    out_dir = Path(__file__).resolve().parents[2] / "audit" / "damage_debugger"
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / f"synth_{battle.name}.jsonl"

    with DebugSession.open(rom) as sess:
        boot_to_ready(sess, battle.boot_frames)
        addr_map = install_synth_battle(sess, battle)

        # For reporting only — verify primary target exists.
        primary = chain[-1]
        sym = sess.symbols.get(primary)
        if sym is None:
            raise KeyError(f"{primary} not in {rom}.sym")

        # Tracer instruments only the primary (last) function in chain.
        tr = Tracer.for_function(sess, primary)
        tr.install()

        # Run each function in sequence, recording wCurDamage after each.
        per_step: list[dict] = []
        damage_args = {
            "D": battle.move.power,
            "E": (battle.player.level if battle.is_player_turn else battle.enemy.level),
            "B": (battle.player.attack if battle.is_player_turn else battle.enemy.attack),
            "C": (battle.enemy.defense if battle.is_player_turn else battle.player.defense),
        }
        try:
            for name in chain:
                # Only set arg registers for the inner formula function.
                args = damage_args if name == "BattleCommand_DamageCalc" else None
                ticked = call_function(sess, name, setup_args=args)
                per_step.append({
                    "fn": name,
                    "ticks": ticked,
                    "wCurDamage": read_cur_damage(sess),
                })
        finally:
            tr.uninstall()
        tr.write_jsonl(jsonl_path)

        return {
            "battle": battle,
            "chain": list(chain),
            "per_step": per_step,
            "trace_frames": len(tr.frames),
            "trace_jsonl": str(jsonl_path),
            "cur_damage": read_cur_damage(sess),
            "addr_map": addr_map,
            "first_pc": tr.frames[0].pc if tr.frames else None,
            "last_pc": tr.frames[-1].pc if tr.frames else None,
        }


def main() -> int:
    """Smoke: run the default baseline scenario."""
    battle = SynthBattle(name="baseline_phys_50pow")
    res = run_synth(battle)
    print(f"scenario        : {res['battle'].name}")
    print(f"returned        : {res['returned_in_frames']}")
    print(f"trace frames    : {res['trace_frames']}")
    print(f"first/last PC   : {res['first_pc']} / {res['last_pc']}")
    print(f"cur_damage      : {res['cur_damage']}")
    print(f"jsonl           : {res['trace_jsonl']}")
    print(f"addr map        : {res['addr_map']}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
