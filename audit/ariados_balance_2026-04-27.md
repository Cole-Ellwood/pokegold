# Ariados Balance Note - 2026-04-27

Scope: one weak-Pokemon lane from `docs/project_roadmap.md` / `docs/buff_backlog.md`.

## Source Truth

- `ARIADOS` current stats: `110/90/100/40/60/60`, Bug/Poison.
- `SPINARAK` evolves to `ARIADOS` at level 22.
- Before this pass, Ariados had `SPIKES` only as a level 1 move and `SPIDER_WEB`
  at level 43.
- Spinarak already learned `SPIDER_WEB` at level 37, so a level 40 Ariados could
  justify Spider Web only through delayed evolution or custom trainer scripting,
  not through Ariados's own curve.
- Koga's level 40 Ariados uses `SPIKES`, `TOXIC`, `GIGA_DRAIN`, and
  `SPIDER_WEB`.

## Decision

Treat Ariados as a provisional slow hazard trapper, not a generic stat buff.

Implemented:

- `ARIADOS` learns `SPIKES` at level 22, so a player who evolves Spinarak at the
  normal level can enter the hazard role immediately.
- `ARIADOS` learns `SPIDER_WEB` at level 37, matching Spinarak's timing and
  supporting Koga's level 40 showcase without requiring delayed evolution.

Not implemented:

- No stat restoration from the older `115` Attack snapshot.
- No new damage coverage.
- No trainer roster changes.

## Remaining Gaps

This is source/audit confidence, not feel proof. The remaining useful manual
check is a normal evolved Spinarak around level 22-37 and Koga's trap/hazard
turn feel.
