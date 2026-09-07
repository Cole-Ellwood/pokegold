"""Check indexed AI chart coverage and arithmetic against the ROM combat rows."""
from __future__ import annotations

import argparse
from pathlib import Path

from tools.boss_ai_fixtures.harness import open_harness, TYPES
from tools.boss_ai_fixtures.damage import EFFECTS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', default='pokegold')
    args = parser.parse_args()
    rom = Path(args.rom + '.gbc').read_bytes()
    with open_harness(args.rom) as h:
        def offset(name):
            sym = h.syms[name]
            return sym.bank * 0x4000 + sym.address % 0x4000

        start = offset('TypeMatchups')
        at, section = start, 0
        rows = [[], []]
        while rom[at] != 255:
            if rom[at] == 254:
                section = 1
                at += 1
                continue
            rows[section].append(tuple(rom[at:at + 3]))
            at += 3
        local = offset('BossAI_TypeMatchups')
        end = offset('BossAI_TypeMatchupsEnd')
        assert rom[local:end] == rom[start:at + 1], 'local chart differs from combat rows'
        index = offset('BossAI_TypeMatchupIndex')
        index_size = offset('BossAI_TypeMatchupIndexEnd') - index
        assert index_size % 4 == 0, 'partial chart index entry'
        count = index_size // 4
        assert count == max(TYPES.values()) + 1, 'Python and ROM type counts differ'
        bank = h.syms['BossAI_TypeMatchups'].bank
        for attack in range(count):
            for part in range(2):
                entry = index + attack * 4 + part * 2
                pointer = int.from_bytes(rom[entry:entry + 2], 'little')
                cursor = bank * 0x4000 + pointer % 0x4000
                assert local <= cursor < end, (attack, part, pointer)
                actual = []
                while rom[cursor] == attack:
                    actual.append(tuple(rom[cursor:cursor + 3]))
                    cursor += 3
                expected = [row for row in rows[part] if row[0] == attack]
                assert actual == expected, ('index/group coverage', attack, part, actual, expected)

        def reference(value, attack, first, second, identified, dragon, fixed, struggle):
            if struggle:
                return value
            for atk, defender, factor in rows[0] + ([] if identified else rows[1]):
                if atk != attack or defender not in (first, second):
                    continue
                if factor == 0:
                    if fixed or not dragon:
                        return 0
                    factor = 5
                if value:
                    value = min(65535, max(1, value * factor // 10))
            return value

        base = h.syms['wTilemap'].address
        checked = 0

        def check(value, attack, first, second, identified, dragon, effect=0, struggle=False):
            nonlocal checked
            for field, byte in ((2, effect), (3, attack), (9, TYPES['DRAGON'] if dragon else TYPES['NORMAL']),
                                (10, TYPES['NORMAL']), (11, first), (12, second),
                                (15, int(identified) | (64 if struggle else 0))):
                h.wr('wTilemap', byte, field)
            assert h.invoke('BossAI_DamageKernel.Chart', dict(B=value >> 8, C=value & 255,
                                                            D=base >> 8, E=base & 255))
            actual = int(h.pb.register_file.B) << 8 | int(h.pb.register_file.C)
            fixed = effect in {EFFECTS[n] for n in ('EFFECT_STATIC_DAMAGE', 'EFFECT_LEVEL_DAMAGE', 'EFFECT_SUPER_FANG')}
            expected = reference(value, attack, first, second, identified, dragon, fixed, struggle)
            assert actual == expected, (value, attack, first, second, identified, dragon, effect, actual, expected)
            assert int(h.pb.register_file.D) << 8 | int(h.pb.register_file.E) == base
            checked += 1

        for attack in range(count):
            for first in range(count):
                for second in range(count):
                    for identified in (False, True):
                        for dragon in (False, True):
                            for value in (3, 65535):
                                check(value, attack, first, second, identified, dragon)
        for attack in (*range(count), 254, 255):
            for defender in range(count):
                for value in (0, 1, 10, 255):
                    for effect in (EFFECTS['EFFECT_STATIC_DAMAGE'], EFFECTS['EFFECT_LEVEL_DAMAGE'], EFFECTS['EFFECT_SUPER_FANG']):
                        check(value, attack, defender, defender, False, True, effect)
                    check(value, attack, defender, defender, False, True, struggle=True)
    print(f'PASS: chart index covers all combat rows; {checked} ROM chart comparisons')


if __name__ == '__main__':
    main()
