# Prompt To Ask GPT-5.5 Pro

You are an external evaluator for a long-running Pokemon mastery project. You
cannot read the repo directly, so treat the attached `context_files/` packet as
the codebase context. Use the files as canonical evidence and do not assume
unstated files exist.

## Attached Context Files

The packet contains 10 copied repo files:

1. `docs__pokemon_mastery__external_research_context_packet_2026-05-14.md`
2. `docs__pokemon_mastery__active_context.md`
3. `docs__pokemon_mastery__context_management_plan.md`
4. `docs__pokemon_mastery__measurement_minigoal_2026-05.md`
5. `docs__pokemon_mastery__measurement_progress_ledger.csv`
6. `docs__pokemon_mastery__measurement_reports__pokemon_skill_tracking_report_2026-05-14_facts.json`
7. `docs__pokemon_mastery__replay_turn_pause_protocol.md`
8. `docs__pokemon_mastery__boss_sim_readiness_audit_2026-05-13.md`
9. `docs__pokemon_mastery__quick_tests__setup_hidden_role_stop_transfer_001_smogtours-gen2ou-921412_2026-05-14.md`
10. `docs__pokemon_mastery__quick_tests__screen_phaze_third_owner_probe_001_2026-05-14.md`

## Project Goal

The project is trying to make the assistant a measurably stronger Pokemon
singles advisor, roughly using "solid 1500 Elo Pokemon Showdown player" as a
training proxy rather than proof. The practical target is better unseen move
choice: plan multiple turns ahead, re-solve after new public information, and
choose moves that preserve or improve realistic win routes in GSC-style singles
and a Pokemon Gold romhack.

There is no public Team Preview in vanilla GSC or this romhack. Vanilla GSC
replay study must use only public state revealed so far unless a side-known
team sheet is explicitly supplied. Romhack mechanics are a fork and must not be
treated as vanilla truth without local evidence.

## Current Concern

After very long work sessions, the assistant may keep putting in effort but
produce much lower-value work: more policy cards, more constructed probes, and
more polished notes instead of fresh evidence that move choice is improving.

Default hypothesis should not be "the project is failing." The concern is more
specific:

```text
Is the current study loop still producing measurable transfer improvement, or
is it starting to spin wheels by generating artifacts that look useful but do
not improve fresh unseen decisions?
```

## Known Measurement Facts

From the current measurement report and ledger:

- Ledger rows: 162, excluding the CSV header.
- Fresh replay/transfer decisions: 2,125.
- Fresh top-match: 863 / 2,125 = 40.6%.
- Fresh acceptable-match: 1,257 / 2,125 = 59.2%.
- Constructed quick probes: 265 / 265, but these are regression checks, not
  proof of broad skill.
- First 20 fresh replay/transfer rows: 146 / 405 top-match, 233 / 405
  acceptable-match, 5 severe blunders, 2 state errors, 0 hidden-info errors.
- Latest 20 fresh replay/transfer rows: 202 / 544 top-match, 304 / 544
  acceptable-match, 1 severe blunder, 3 state errors, 4 hidden-info errors.
- Most recent fresh transfer:
  `setup_hidden_role_stop_transfer_001_smogtours-gen2ou-921412_2026-05-14`
  scored 16 / 39 top, 25 / 39 acceptable, 0 severe, 0 mechanics errors, 0 state
  errors, 0 hidden-info errors.
- Most recent constructed probe:
  `screen_phaze_third_owner_probe_001_2026-05-14` scored 4 / 4 action-policy
  hits and 4 / 4 boundary hits, with no severe, mechanics, state, or hidden-info
  errors.

## Your Task

Give a skeptical audit and operating recommendation. Do not write a broad GSC
strategy guide.

Answer these questions:

1. Measurement validity:
   Which evidence is most trustworthy, which evidence is weak, and which
   metrics may be contaminated or Goodharted? Explicitly separate fresh replay
   evidence, focused transfer evidence, constructed regression probes, and
   post-oracle notes.

   The data suggests severe blunders are down, but top-move and acceptable-move
   agreement are not clearly improving, and hidden-info errors rose in the
   latest 20 fresh rows. Is the loop optimizing for avoiding obvious mistakes
   rather than selecting stronger moves? If yes, how should the next work blocks
   target positive move-selection skill instead of only error suppression?

2. Wheel-spinning risk:
   Based on the files and facts, is the project currently at meaningful risk of
   low-value repetition after long sessions? If yes, name the exact pattern. If
   no, name the earliest warning sign that would flip your answer.

3. Best next action:
   Choose one primary next action from this list and justify it:
   - fresh unseen replay transfer;
   - expert article/source study;
   - real or reconstructed boss worksheet;
   - mechanics fixture/check;
   - tiny tooling improvement;
   - stop or pause the session.

4. Next 3 work blocks:
   Give exactly three concrete work blocks. For each block include:
   - timebox;
   - objective;
   - files/artifacts to create or update;
   - score or evidence expected;
   - kill condition or stop rule;
   - what must not be done during that block.

5. Long-session stop/continue rules:
   Define operational rules for sessions longer than 4 to 6 hours. Include
   measurable triggers for continue, switch mode, consolidate, or stop.

6. Context management:
   Recommend what should stay in the live context packet, what should be
   archived, and what should only be loaded on demand. Keep this practical and
   small.

7. Optional tooling:
   Only if directly justified by measurement validity, leakage control, or
   replay-transfer throughput, propose at most two tiny helper ideas. Do not
   propose broad tooling or simulation systems.

## Constraints

- Do not import Team Preview assumptions into GSC or the romhack.
- Treat replay actual moves as weak expert comparisons, not infallible answer
  keys.
- Do not treat constructed-probe perfection as proof of mastery.
- Do not let lower severe-blunder count hide a shift into hidden-info, state, or
  mechanics errors. Treat error tags as potentially overlapping.
- Do not claim boss-sim validation until readiness blockers are closed.
- Do not propose broad note-writing as the main next action.
- Do not propose a sealed final exam unless the prompts and answer keys can be
  hidden from the studying assistant before it answers.
- If you recommend source/article study, name the exact failure class it must
  attack and the Pokemon artifact or score it must produce.
- If you recommend tooling, it must create cleaner reps, prevent answer
  leakage, improve scoring, or verify a decision-relevant mechanic.

## Output Format

Use this structure:

1. `Verdict`
2. `Evidence Audit`
3. `Wheel-Spinning Diagnosis`
4. `Primary Next Action`
5. `Three-Block Plan`
6. `Long-Session Stop Rules`
7. `Context Packet Recommendation`
8. `Optional Tiny Tools`
9. `Questions Or Missing Data`

Be direct and adversarial. Prefer a useful "no, do not do that next" over a
balanced list of generic possibilities.
