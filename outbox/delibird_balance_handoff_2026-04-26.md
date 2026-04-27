# Delibird Balance Handoff - 2026-04-26

Start here if the next session touches weak-Pokemon usefulness.

## Current State

This pass resolved Delibird's medium-priority backlog question at the source
level. Delibird was not weak because its stats were ignored; it was weak because
its level-up identity was still basically `PRESENT` and nothing else.

Changed source:

- `data/pokemon/evos_attacks.asm`

Changed balance docs:

- `docs/balance_intent.md`
- `docs/buff_backlog.md`
- `docs/agent_navigation/subsystems/pokemon_balance.md`
- `docs/generated/balance_audit.md` via `python scripts\generate_balance_audit.py`
- `docs/generated/dev_index.md` via `python scripts\generate_dev_index.py --rom pokegold`

Evidence:

- `audit/delibird_balance_2026-04-26.md`

## Delibird Role

Delibird is now a provisional special-delivery Ice/Flying utility wall:

- Keeps `PRESENT` as the joke/identity hook.
- Adds `QUICK_ATTACK`, `ICY_WIND`, `AURORA_BEAM`, `AGILITY`, `WING_ATTACK`,
  `HAZE`, and late `BLIZZARD`.
- Leaves raw stats unchanged at `100/55/45/75/65/150`.
- Leaves type unchanged as `ICE, FLYING`.
- Leaves low Attack intact so `WING_ATTACK` is useful STAB, not a generic
  sweep button.

Important encounter/use facts:

- Wild Delibird appears in Johto grass tables at levels 22-24.
- PokefanM Colin has a level 32 Delibird with `BERRY`.

## Verification Already Run

Passed:

```powershell
python scripts\generate_balance_audit.py
python tools\audit\check_release_smoke.py
python tools\audit\check_docs_navigation.py
python tools\audit\check_cheap_difficulty.py
git diff --check
```

Build passed:

```powershell
bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'
```

Gold relinked, Silver was up to date. After the Gold relink,
`python scripts\generate_dev_index.py --rom pokegold` refreshed the generated
index and `python tools\audit\check_docs_navigation.py` passed again.

Important caveat: the worktree already had unrelated dirty source edits. The
generated dev-index refresh records the current whole-linker state, so not every
anchor/size movement in `docs/generated/dev_index.md` came from Delibird.

`git diff --check` only printed CRLF normalization warnings for
`audit/boss_ai_trace/morty_live.txt` and `docs/generated/balance_audit.md`.

After notes were written, `python tools\audit\check_navigation_floor.py` also
passed.

## Next Useful Moves

Best playtest:

1. In Silver, catch Delibird around level 22-24 and confirm it arrives with a
   useful-enough early kit.
2. Fight PokefanM Colin and check whether level 32 Delibird feels like a funny
   utility opponent rather than dead air.
3. If Delibird still feels too weak, adjust move timing before touching stats.

Next weak-Pokemon queue:

- `FARFETCH_D`: check Stick availability and whether Flying/Normal STAB is real.
- `ARIADOS`: decide whether bulky status utility actually lands in play.
- `YANMA`: check whether Speed/offense and Bug/Flying move quality justify use.

Do not reopen `LEDIAN` or `DELIBIRD` just because generated audit rows look odd;
both now have provisional role rows in `docs/balance_intent.md`.
