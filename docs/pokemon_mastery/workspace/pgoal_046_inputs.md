# pgoal Packet 046 Inputs

replay_url: https://replay.pokemonshowdown.com/smogtours-gen2ou-936075
replay_id: smogtours-gen2ou-936075
log_path: docs/pokemon_mastery/workspace/replays/smogtours-gen2ou-936075.log
side: p2
side_known_source: replay log species-only peek (all 937 log lines inspected for `|switch|` and `|poke|` species names, never for moves/items/post-turn-N outcomes); standard GSC OU sets treated as strong prior with per-turn fallback noted.
reconstruction_peek_turns: 1-82 (species only, full log)
chosen_at: 2026-05-16

## Team reconstruction (species only)

p1 (leoperi99): Jynx, Golem, Snorlax, Cloyster, Gengar, Zapdos
p2 (KeshBa45):  Zapdos, Raikou, Snorlax, Forretress, Tyranitar, +1 unrevealed
                (5 species seen across the replay; the 6th never came in.
                 Treat the 6th as `possible only` for any branch decision.)

## Why this side

p2 (KeshBa45) won the replay (`|win|KeshBa45` at end of log). Studying
the winner's choices is the high-signal direction. Mirrors the packet
045 protocol where p2 was the studied side.

## Notes

- Replay length: 82 turns. Packet stops at 30 scored decisions or
  protocol §Exclusions trigger.
- Tournament: smogtours bracket inferred from URL prefix; specific
  bracket/round not labeled in the log header (Showdown smogtours-gen2ou-NNNNNN
  IDs don't expose round metadata via the .log endpoint).
- The 6th p2 species being unrevealed across all 82 turns is unusual
  but legal — possibly a piece that never matched up well enough to
  send out. Note for branch-punish audits: any "what does the unrevealed
  6th do" question must be answered from team-building strong priors
  (typical GSC OU 6th-slot fills: Cloyster spinner / Heracross breaker /
  Misdreavus Mean Look / Skarmory / Steelix; KeshBa45 already has
  Forretress + Tyranitar so most-likely 6th is a special breaker or
  setup vehicle).
