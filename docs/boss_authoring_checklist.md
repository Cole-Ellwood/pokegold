# Boss Authoring Checklist

Date: 2026-02-14
Applies to: Gym Leaders, Rival encounters, Elite Four, Champion

## Acceptance Checklist (Required for Every Major Trainer)

- [ ] All mons have 4 moves filled (`no NO_MOVE`).
- [ ] Every held item is intentional and documented (`NO_ITEM` is explicitly justified).
- [ ] Every mon has role clarity (`lead`, `pivot`, `wall`, `breaker`, `cleaner`, or `ace`).
- [ ] Team has required coverage and anti-setup tools for its segment.
- [ ] Encounter sits inside the intended difficulty band for that progression segment.

## Authoring Standard Details

### Move Completeness

- Every slot must be legal and purposeful.
- No filler duplicates unless the role intentionally uses redundancy.

### Held Item Intent

- Item must reinforce role, matchup plan, or encounter pacing.
- Avoid random high-power items with no tactical link.

### Role Clarity Per Mon

- Each mon has one primary role and optional secondary role.
- Team-level role spread must avoid six-mon redundancy.

### Coverage and Anti-Setup Presence

- Team must answer common resist walls in its target segment.
- Mid/Late major trainers must include at least one anti-setup response.
- Anti-setup can be move-based, speed-control-based, phazing-based, or pressure-based.

### Difficulty Band Consistency

- Levels, move quality, item quality, and AI tier must align with segment budget.
- No isolated outlier spike without explicit narrative/boss intent note.

## Segment Band Quick Gate

- Early (Badges 1-3): readable threats, low hard-counter density.
- Mid (Badges 4-6): role interaction required, punish predictable setup.
- Late (Badges 7-8, E4, Champion): full tactical pressure, tighter punishment windows, high role coherence.

## Definition of Done

- Checklist passes for all variants of the trainer (starter branches/rematches where applicable).
- Playtest notes confirm intended role behavior occurs in battle.
- No unresolved failures in move legality, item legality, or AI tier assignment.
