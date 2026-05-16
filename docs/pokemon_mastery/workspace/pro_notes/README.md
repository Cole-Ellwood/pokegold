# Pokemon Mastery Pro Notes

Purpose: preserve the GPT-5.5 Pro guidance as a reference library for the
active Pokemon mastery goal. These notes are not the curriculum by themselves;
they are an operating system for studying expert play, reviewing long games,
and converting real lessons into tested policies.

## File Map

| File | Role | How to use it |
| --- | --- | --- |
| `01_mastery_curriculum_and_battle_review.md` | Mastery definition, staged curriculum, battle-review protocol, mistake loop, and broad drill plan. | Use as the high-level checklist for whether learning work is actually improving long-game play. |
| `02_state_transition_policy_critique.md` | Critique of prose-heavy heuristics, live resource ledger requirements, opponent-model tiers, hard heuristic cards, and mastery gates. | Use before study blocks to keep work focused on move choice, threat-answer graphs, passive clocks, and earliest irreversible errors. |
| `03_benchmark_architecture_and_policy_schema.md` | Detailed public-card / hidden-oracle architecture, policy-answer schema, mutation strategy, role maps, route objects, and anti-overfitting rules. | Use when turning learned principles into tests or benchmark cards. Do not let this replace Smogon/replay study. |
| `04_type_effectiveness_evidence_firewall.md` | Type-effectiveness evidence protocol, type-claim taxonomy, vanilla smoke tests, romhack passive checks, and wording rules. | Use whenever a benchmark, policy explanation, or battle review wants to say super effective, resisted, immune, or neutral. |

## Integration Rules

- Expert play study is primary. Smogon articles, analyses, tournament replays,
  and full battle logs should drive future learning.
- These pro notes are method guidance, not proof of Pokemon skill. They should
  shape how I read and review, not become a substitute for reading and
  reviewing.
- User-provided RLHF cards are calibration examples. They should not dominate
  the curriculum unless they reveal a concrete mechanic, answer flip, or
  repeated decision error.
- Romhack claims must remain fork-scoped. Vanilla GSC principles transfer only
  after local docs, source, debugger output, or fixtures validate the relevant
  mechanics.
- The source hierarchy in `04_type_effectiveness_evidence_firewall.md` should
  be read with the later correction already applied: source code is authority
  for general mechanics, validated debugger traces are authority for exact
  battle-state damage, and disagreements mean a source/tooling/version mismatch
  to investigate.

## Useful Concepts To Carry Forward

- The unit of learning is a state transition: in this exact visible state, under
  this mechanics profile, choose the move that improves a named route without
  opening a worse plausible opponent route.
- The live ledger matters more than commentary: HP, status, sleep, Rest turns,
  PP, hazards, revealed moves, hidden possibilities, phazers, spinners,
  Explosion resources, and irreplaceable pieces.
- Heuristics need arbitration. Set Spikes, preserve answers, use sleep, attack
  now, Rest now, phaze, scout, and Explode can all be true; the hard part is
  deciding which dominates this turn.
- Reviews must freeze public information at the turn being judged. Using later
  replay knowledge to label an earlier decision trains clairvoyance.
- Damage and type words are not strategy. They matter only when tied to KO
  thresholds, forced Rest, setup denial, hazard ranges, or route conversion.
- Simulations are microscopes. They can test mechanics, branch assumptions, and
  counterexamples, but they do not prove broad strategic truth.

## Next Study Bias

Future work blocks should start with expert play sources and long-game review:

1. Read a Smogon GSC article, analysis, or replay thread.
2. Extract how strong players choose moves and manage routes.
3. Review a full game or long constructed position using the ledger/checklist.
4. Only then decide whether a new benchmark, policy rule, or local romhack test
   is worth adding.
