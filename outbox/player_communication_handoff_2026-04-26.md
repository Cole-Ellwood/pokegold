# Player Communication Handoff - 2026-04-26

This session chose player communication as the improvement lane.

Why this was the right move after the release-confidence pass:

- The source/audit/build floor was already green.
- The player can still experience fair changes as cheap if the game never says
  the rules out loud.
- Earl's Academy is early, optional, and already exists to teach battle basics.

What changed:

- `maps/EarlsPokemonAcademy.asm`: the notebook now explains Set/no-Pack trainer
  battles, legal Gym Leader memory from revealed moves, stronger type habits,
  and serious held-item lock/boost behavior.
- `tools/audit/check_release_smoke.py`: the communication text is now guarded by
  release smoke.
- `audit/player_communication_2026-04-26.md`: evidence capsule for this lane.
- `docs/project_roadmap.md`: `COMM-001` records the completed communication
  pass and remaining manual-render gap.
- `docs/generated/dev_index.md`: refreshed after the Gold/Silver build relinked
  map data.

Verification:

- `python tools\audit\check_release_smoke.py` passed.
- WSL `make ... pokegold.gbc pokesilver.gbc` passed and relinked both ROMs.
- `python scripts\generate_dev_index.py --rom pokegold` refreshed the generated
  index.
- `python tools\audit\check_docs_navigation.py` passed after the refresh.
- `git diff --check` had no whitespace errors; it only repeated the existing
  CRLF warning for `audit/boss_ai_trace/morty_live.txt`.

Next good move:

If a future session stays in player communication, do not start by adding more
text everywhere. First check whether a player can discover the changed type
passives and held-item rules at the moments they matter. Add only one more
surface if a real blind spot appears.
