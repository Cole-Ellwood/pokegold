# Pokemon Balance Micro-Index

Use this when the task is about weak Pokemon, stats, typing, learnsets,
evolutions, species roles, or balance review.

Balance promise: make familiar Pokemon worth rediscovering. The player should
not be able to rely on the old solved tier list to dismiss weak or strange
species, but buffs should preserve identity and avoid trivializing early Johto.

## Fast Route

| Need | Go to |
| --- | --- |
| Project balance rules | `docs/codex_context.md`, `docs/balance_intent.md` |
| Evolution policy | `docs/evolution_policy.md` |
| Durable weak-Pokemon queue | `docs/buff_backlog.md` |
| Generated source-derived audit | `docs/generated/balance_audit.md` |
| Stats/types | `data/pokemon/base_stats/`, `data/pokemon/base_stats.asm` |
| Learnsets/evolutions | `data/pokemon/evos_attacks.asm`, `data/pokemon/evos_attacks_pointers.asm` |
| Pokemon constants | `constants/pokemon_constants.asm` |
| Generator | `scripts/generate_balance_audit.py` |

## Current Review Queue

High priority is intentionally empty in `docs/buff_backlog.md`. Do not promote a
medium-priority Pokemon just to keep the queue visually busy.

Medium-priority review starts with:

| Pokemon | First question |
| --- | --- |
| `FARFETCH_D` | Is Stick availability or Flying/Normal STAB strong enough for a standalone final? |
| `ARIADOS` | Is bulky status utility real in play, or does low Speed leave it flat? |
| `YANMA` | Does current Speed/offense make the Bug/Flying role worth using? |

Lower-priority watchlist and generated high-signal rows live in
`docs/buff_backlog.md` and `docs/generated/balance_audit.md`. Treat generated
rows as hints, not verdicts.

## Decision Destinations

| Decision type | Update |
| --- | --- |
| Species role is intentional and stable | Add or update a locked/provisional row in `docs/balance_intent.md`. |
| Species still needs human judgment | Keep or add it in `docs/buff_backlog.md`. |
| Evolution was restored or removed | Update `docs/evolution_policy.md` and `docs/balance_intent.md`. |
| Source data changed | Regenerate `docs/generated/balance_audit.md`. |

## Search Shortcuts

Use exact species labels before broad searches:

```powershell
rg -n -C 4 "FARFETCH_D|ARIADOS|YANMA" docs data constants
rg -n "^(FarfetchDEvosAttacks|AriadosEvosAttacks|YanmaEvosAttacks):" data/pokemon/evos_attacks.asm
```

For base stats, jump to one file:

```powershell
Get-Content data\pokemon\base_stats\farfetch_d.asm
```

## Verification

Use `docs/agent_navigation/verification_matrix.md` row
`Docs-only routing, roadmap, handoff, or organization` for docs triage, or
`Pokemon stats, types, evolutions, learnsets` for source balance changes. Build
both ROMs after source changes. Do not call a balance change complete from
generated audit output alone; name any playtest or boss-usage gap.
