"""Public reply sets compared with an exhaustive ROM-data reference."""
from tools.boss_ai_fixtures.harness import MOVES, SPECIES, ROOT, _parse_const_file


def natural_moves(h, species, level):
    """Read all source species and ancestry directly from ROM tables.

    Build the complete evolution graph first, independently of the AI's
    backwards first-parent lookup, and take the union over all ancestors.
    """
    rom = h.sess.rom_path.read_bytes()
    def address(bank, pointer):
        return pointer if pointer < 0x4000 else bank * 0x4000 + pointer - 0x4000
    def symbol(name):
        entry = h.syms[name]
        return address(entry.bank, entry.address)
    def pointer(name, index):
        offset = symbol(name) + index * 2
        value = rom[offset] | rom[offset + 1] << 8
        return address(h.syms[name].bank, value)
    parents, learned = {}, {}
    evo_stat = _parse_const_file(ROOT / "constants/pokemon_data_constants.asm")["EVOLVE_STAT"]
    for mon in range(1, SPECIES["CELEBI"] + 1):
        pos = pointer("EvosAttacksPointers", mon - 1)
        while rom[pos]:
            size = 4 if rom[pos] == evo_stat else 3
            parents.setdefault(rom[pos + size - 1], set()).add(mon)
            pos += size
        pos += 1
        learned[mon] = []
        while rom[pos]:
            learned[mon].append((rom[pos], rom[pos + 1]))
            pos += 2
    ancestry, pending = set(), [species]
    while pending:
        mon = pending.pop()
        if mon not in ancestry:
            ancestry.add(mon)
            pending.extend(parents.get(mon, ()))
    base_size = h.syms["wCurBaseDataEnd"].address - h.syms["wCurBaseData"].address
    tm_offset = h.syms["wBaseTMHM"].address - h.syms["wCurBaseData"].address
    tm_moves = []
    pos = symbol("TMHMMoves")
    while rom[pos]:
        tm_moves.append(rom[pos])
        pos += 1
    result = set()
    for mon in ancestry:
        # GetEggMove's shared-parent level-up path checks move identity only,
        # not hatch level. Egg species is the earliest ancestor. Conservatively
        # allow its inherited moves without attempting hidden parent legality.
        result.update(move for learn_level, move in learned[mon]
                      if learn_level <= level or not parents.get(mon))
        base = symbol("BaseData") + (mon - 1) * base_size + tm_offset
        for i, move in enumerate(tm_moves):
            if rom[base + i // 8] & 1 << (i % 8):
                result.add(move)
        pos = pointer("EggMovePointers", mon - 1)
        while rom[pos] != 255:
            result.add(rom[pos])
            pos += 1
    return result


def run_reply_check(h, case):
    spec = case.reply_check
    observed = {MOVES[name] for name in spec.get("revealed", [])}
    h.wr("wPlayerSubStatus5", 8 if spec.get("transformed") else 0)
    h.wr("wBossAISeenPlayerSpeciesCount", 0)
    for i in range(4):
        h.wr("wPlayerUsedMoves", MOVES[spec["revealed"][i]] if i < len(spec.get("revealed", [])) else 0, i)
    for key, value in case.extra.items():
        h.wr(key[0], value, key[1]) if isinstance(key, tuple) else h.wr(key, value)
    if spec.get("closed"):
        expected, flags = observed.copy(), 1
    elif spec.get("broad"):
        expected, flags = set(range(1, MOVES["QUIVER_DANCE"] + 1)), 2
    else:
        expected, flags = natural_moves(h, case.player.species, case.player.level) | observed, 0
    expected.add(MOVES["STRUGGLE"])
    spans = (("wEnemyMon", 48), ("wBattleMon", 48), ("wOTPartyMon1Species", 288),
             ("wCurSpecies", 1), ("wCurPartySpecies", 1), ("wBossAITemp", 5),
             ("wCurBaseData", h.syms["wCurBaseDataEnd"].address - h.syms["wCurBaseData"].address),
             ("wPlayerUsedMoves", 4), ("wBossAIRevealedMovesBitmapSpare", 3))
    before = {(name, i): h.rd(name, i) for name, size in spans for i in range(size)}
    pointer = h.syms["wTilemap"].address
    rf = h.pb.register_file
    start_sp = int(rf.SP)
    random_calls = []
    random_symbol = h.syms["Random"]
    h.pb.hook_register(random_symbol.bank, random_symbol.address, lambda _: random_calls.append(1), None)
    registers = {"D": pointer >> 8, "E": pointer & 255}
    try:
        returned = h.invoke("BossAI_BuildPublicReplySet", registers)
    finally:
        h.pb.hook_deregister(random_symbol.bank, random_symbol.address)
    out = h.outcome()
    raw = [h.rd("wTilemap", i) for i in range(65)]
    possible = {i for i in range(256) if raw[i // 8] & 1 << (i % 8)}
    revealed = {i for i in range(256) if raw[32 + i // 8] & 1 << (i % 8)}
    errors = []
    for name in spec.get("must_include", []):
        if MOVES[name] not in possible:
            errors.append(f"legal inherited move {name} absent from reply set")
    if possible != expected:
        errors.append(f"public replies missing {sorted(expected-possible)}, extra {sorted(possible-expected)}")
    if revealed != observed or raw[64] != flags:
        errors.append(f"reveal metadata {(revealed, raw[64])} != {(observed, flags)}")
    if int(rf.SP) != start_sp or (int(rf.D) << 8 | int(rf.E)) != pointer:
        errors.append("reply builder lost stack/context")
    if any(h.rd(*key) != value for key, value in before.items()):
        errors.append("reply builder changed battle/party/lookup state")
    if random_calls:
        errors.append("reply builder consumed RNG")
    # Neither the player's concealed moves/PP nor the chosen current input may
    # affect the possibility set. Own knowledge and public state stay fixed.
    h.wr("wBattleMonItem", 255)
    h.wr("wCurPlayerMove", MOVES["EXPLOSION"])
    for i in range(4):
        h.wr("wBattleMonMoves", MOVES["EXPLOSION"], i)
        h.wr("wBattleMonPP", 0, i)
    returned &= h.invoke("BossAI_BuildPublicReplySet", registers)
    if raw != [h.rd("wTilemap", i) for i in range(65)]:
        errors.append("reply set depends on private player moves/PP/item/input")
    out.update(returned=returned, damage_errors=errors, memory={}, haki_spent=False,
               possible_moves=sorted(possible), revealed_moves=sorted(revealed), reply_flags=raw[64])
    return out
