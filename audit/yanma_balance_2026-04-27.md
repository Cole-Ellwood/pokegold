# Yanma Balance Note - 2026-04-27

Scope: one weak-Pokemon lane from `docs/project_roadmap.md` / `docs/buff_backlog.md`.

## Source Truth

- `YANMA` current stats: `85/110/60/95/50/80`, Bug/Flying.
- The older manifest snapshot recorded a faster, sharper statline:
  `65/125/45/140/75/45`. Current source is deliberately bulkier and slower, so
  this pass did not blindly restore the older numbers.
- Route 35 has level 12 wild Yanma in both Gold and Silver.
- Schoolboy Alan uses Yanma at level 17 and again at level 25.
- Before this pass, Yanma learned Leech Life at 19 and Wing Attack at 25, so
  Alan's level 17 Yanma generated without either STAB move.

## Decision

Treat Yanma as a provisional fast physical Bug/Flying disruptor, not a raw
Speed-restoration project.

Implemented:

- `YANMA` learns `LEECH_LIFE` at level 17 instead of level 19.

Why this exact change:

- Level 12 wild Yanma does not immediately get an 80 BP STAB move.
- A trained Route 35 catch reaches Bug STAB before the midgame rematch window.
- Schoolboy Alan's level 17 Yanma now showcases Bug STAB.
- The level 25 rematch still showcases Wing Attack.

Not implemented:

- No stat restoration to the older 125 Attack / 140 Speed snapshot.
- No new moves.
- No trainer roster changes.

## Remaining Gaps

This is source/audit confidence, not feel proof. The useful manual checks are
Route 35 catch feel and Schoolboy Alan's level 17 / level 25 Yanma fights.
