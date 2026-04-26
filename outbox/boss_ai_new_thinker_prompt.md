# Boss AI New Thinker Prompt

Purpose: wake a fresh session into the next Boss AI thinking pass without
making it rediscover the proof standard, the Haki boundary, or the current live
capture gaps.

Use this when the user wants a deep Boss AI idea/review/design session, not a
mechanical source patch. This is a prompt artifact, not source truth.

## Current Ground

- Repo: `C:\Users\lolno\Downloads\pokemon gold hack`
- Entrypoint: `docs/README.md`
- Project north star: make Pokemon Gold feel unknown and dangerous again for a
  veteran player without turning the hack into generic hard mode.
- Current proof state: Morty and Jasmine have accepted live Boss AI proof
  capsules.
- Remaining proof gaps: Clair, Koga, Champion Lance, Red if added, the other
  unfinished gym leaders, and shared switch-loop behavior.
- Haki state: design contract only. There is no broad Haki implementation.
- First source Haki recommendation, if ever approved later:
  `HAKI_LANCE_DRAGON_KINGS_PRIVILEGE` through `BossAI_SwitchOrTryItem`, because
  that path runs after player action is committed and avoids the first prototype
  needing a post-input move override.
- Interesting adjacent note:
  `outbox/codex_curiosity_boss_ai_public_imagination.md`

## Read Order

1. `docs/README.md`
2. `docs/codex_context.md`
3. `docs/project_map.md`
4. `docs/project_roadmap.md`
5. `docs/boss_ai_spec.md`
6. `docs/boss_ai_trace_capture.md`
7. `docs/agent_navigation/subsystems/boss_ai_trace.md`
8. `audit/boss_ai_trace/live_capture_ledger.md`
9. `audit/boss_ai_trace/live_capture_manifest.json`
10. `outbox/codex_curiosity_boss_ai_public_imagination.md`
11. `engine/battle/ai/boss.asm`

## Paste-Ready Prompt

You are in `C:\Users\lolno\Downloads\pokemon gold hack`.

Read the files in this order:

1. `docs/README.md`
2. `docs/codex_context.md`
3. `docs/project_map.md`
4. `docs/project_roadmap.md`
5. `docs/boss_ai_spec.md`
6. `docs/boss_ai_trace_capture.md`
7. `docs/agent_navigation/subsystems/boss_ai_trace.md`
8. `audit/boss_ai_trace/live_capture_ledger.md`
9. `audit/boss_ai_trace/live_capture_manifest.json`
10. `outbox/codex_curiosity_boss_ai_public_imagination.md`
11. `engine/battle/ai/boss.asm`

Do not start coding yet.

Choose exactly one next Boss AI branch and defend it:

- live proof expansion for Clair, Koga, Lance, Red, another unfinished gym leader, or shared
  switch-loop behavior;
- a Lance-first Haki source prototype plan;
- a public-imagination/fairness design pass around plausible vs likely threat
  modeling;
- a cheap-difficulty audit focused on whether Boss AI ever feels unfair rather
  than merely hard.

Give one recommendation, not a menu. Name the strongest alternative and the
second-order consequence of rejecting it. If you propose source work, include
the smallest source surface, exact trace/audit commands, memory budget checks,
and the no-cheat failure modes. If you propose no source work, say what evidence
would make coding justified later.

Keep Morty and Jasmine proof in their proper size: they prove two current live
decisions, not whole-game fairness.

## My Recommendation

Start with Champion Lance live proof before Haki source work.

Reason: Lance is already the recommended first Haki plumbing candidate, and that
makes him the boss whose normal legal behavior most needs live evidence before
any cheating exception is allowed near the source. Haki is attractive, but
without a current Lance trace it is too easy to solve a vibe problem with an
architecture problem.

The fork is real:

- Implement Haki first: exciting, but it risks turning an unmeasured design
  desire into permanent battle architecture.
- Prove Lance first: slower, but it tells whether the legal boss model already
  creates the Dragon-king pressure the design wants, and where it fails.

If Lance already feels ruthless from public information, Haki should become a
rarer ace. If Lance looks flat, the trace will say whether the missing piece is
proof, tuning, or a deliberately quarantined cheat.
