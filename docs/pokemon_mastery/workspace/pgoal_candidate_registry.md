# /pgoal Replay Candidate Registry — fresh smogtours-gen2ou replays

Selected from Showdown's gen2ou replay search 2026-05-16. All
verified unused (`grep -r <id> docs/pokemon_mastery/` zero hits) and
turn-count >= 31.

Five-replay slate for /pgoal packets 046-050. Distinct player pairs to
maximize cross-replay team-and-style diversity (no two replays share a
player so teams don't repeat across packets).

| Packet | Replay ID                        | Turns | Players                          | Notes                          |
|--------|----------------------------------|-------|----------------------------------|--------------------------------|
| 046    | smogtours-gen2ou-936075          | 82    | leoperi99 / KeshBa45             | p2 won — selected for study    |
| 047    | smogtours-gen2ou-936065          | 82    | s.islands / justifine            | TBD side at packet start       |
| 048    | smogtours-gen2ou-936057          | 93    | shiloh / gorgie                  | TBD side at packet start       |
| 049    | smogtours-gen2ou-935991          | 62    | Ionic_CMD / strictsceptile1      | TBD side at packet start       |
| 050    | smogtours-gen2ou-935999          | ?     | just fabbio / mayo               | turn count to verify before run |

If any of replays 047-050 fail to yield 30 scored decisions (Exclusions
fire too often), swap from the backup list:

| Backup | Replay ID                        | Turns | Players                          |
|--------|----------------------------------|-------|----------------------------------|
| B1     | smogtours-gen2ou-936003          | 31    | just fabbio / mayo               |
| B2     | smogtours-gen2ou-935995          | ?     | just fabbio / mayo               |

## Selection rules followed

- Smogtours format only (not ladder; tournament-quality play).
- Distinct player pairs per packet (so teams don't repeat).
- Turn count > 30 confirmed via `grep -c "^|turn|" <log>`.
- Cross-referenced against the already-used registry in
  `pgoal_packet_protocol.md` § Already-used replay registry.

## How to re-fetch

If the slate needs refresh (e.g., these IDs become contaminated by
some other workflow), re-search:

```bash
curl -fsSL "https://replay.pokemonshowdown.com/search.json?format=gen2ou" \
  | python -c "import json,sys; d=json.load(sys.stdin); [print(r['id'], r['players']) for r in d if r['id'].startswith('smogtours-gen2ou-')]"
```

Filter out anything already referenced in `docs/pokemon_mastery/`.

## Log fetch (once per replay)

```bash
mkdir -p docs/pokemon_mastery/workspace/replays
curl -fsSL "https://replay.pokemonshowdown.com/<replay-id>.log" \
  -o docs/pokemon_mastery/workspace/replays/<replay-id>.log
```

Log size is small (typically <1 MB per replay). Committing them to the
repo is acceptable — they're durable record of what was studied and
needed for re-scoring if methodology changes.
