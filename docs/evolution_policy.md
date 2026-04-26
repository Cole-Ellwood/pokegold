# Evolution Policy

Audience: future Codex/helper agents. Purpose: make evolution edits explicit
before balance work treats a Pokemon as forgotten or intentionally standalone.

Intent lens: evolution changes must serve the First-Playthrough Promise. A
removed or altered evolution should create discovery and a real standalone role,
not accidentally strand a familiar Pokemon as weak clutter or inflate it until
progression tension disappears.

## Source Rule

Evolution rules live in `data/pokemon/evos_attacks.asm`. Each species block
starts with zero or more `EVOLVE_*` entries, then:

```asm
	db 0 ; no more evolutions
```

If that `db 0` appears immediately after the label, the current game has no
evolution rule for that species. Do not assume the vanilla evolution still
exists.

## Quick Verification Commands

Use current source first:

```powershell
rg -n -C 3 "^(Ponyta|Seel|Rhyhorn|Dragonair|Chinchou|Smoochum)EvosAttacks:" data/pokemon/evos_attacks.asm
```

Use the audit baseline only to recover comparison facts such as original
evolution levels:

```powershell
git show 060d4accd7c0d01b1697ac97e7d7e2da72e3646b:data/pokemon/evos_attacks.asm | rg -n -C 2 "^(Ponyta|Seel|Rhyhorn|Dragonair|Chinchou|Smoochum)EvosAttacks:"
```

If `data/pokemon/evos_attacks.asm` changes and a ROM build is run, refresh
`docs/generated/dev_index.md` because the Evolutions and Attacks section size can
move:

```powershell
python scripts\generate_dev_index.py --rom pokegold
```

## Policy

- Removing an evolution must be documented in this file before the statline is
  considered final.
- A Pokemon with a removed evolution must be balanced as standalone unless this
  file says the removal is temporary.
- A split line, such as making both `SEEL` and `DEWGONG` separately available,
  must explain availability and role for both species.
- If an evolution was removed only to support a progression experiment, mark it
  `temporary` and add a cleanup condition.
- If an evolution was removed intentionally, document what replaces the power
  normally gained by evolving: stats, moves, item, typing, availability, or a
  gimmick.

## Resolved Removed-Evolution Review

Generated audit source: `docs/generated/balance_audit.md`.
Baseline ref used by the generator: `060d4accd7c0d01b1697ac97e7d7e2da72e3646b`.

| Pokemon | Baseline Evolution | Current Status | Intent | Required Follow-Up |
| --- | --- | --- | --- | --- |
| `SEEL` | `DEWGONG` | Restored `EVOLVE_LEVEL, 34, DEWGONG`. | canonical evolution line | None. |
| `CHINCHOU` | `LANTURN` | Restored `EVOLVE_LEVEL, 27, LANTURN`. | canonical evolution line | None. |
| `SMOOCHUM` | `JYNX` | Restored `EVOLVE_LEVEL, 30, JYNX`. | canonical evolution line | None. |
| `PONYTA` | `RAPIDASH` | Restored `EVOLVE_LEVEL, 40, RAPIDASH`. | canonical evolution line | None. |
| `RHYHORN` | `RHYDON` | Restored `EVOLVE_LEVEL, 42, RHYDON`. | canonical evolution line | None. |
| `DRAGONAIR` | `DRAGONITE` | Restored `EVOLVE_LEVEL, 55, DRAGONITE`. | canonical evolution line | None. |

## Review Notes

This is the exact kind of documentation gap that made the weak-Pokemon audit
harder than it needed to be. The source said several former middle or basic
forms were now standalone, but no doc said whether that was the point. That
forces reviewers to choose between two bad assumptions: either "the evolution
was removed on purpose" or "the Pokemon was forgotten." Both assumptions can
damage the hack.

The table above is now resolved in source. If any of these evolutions are removed
again, update this file and `docs/balance_intent.md` in the same change and give
the unevolved species a real standalone role before considering the line final.
