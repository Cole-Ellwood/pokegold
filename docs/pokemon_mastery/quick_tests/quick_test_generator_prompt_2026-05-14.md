# Prompt For Separate Codex Session: Generate Quick Test 001

Use this prompt in a separate Codex session to generate a better quick test for
the main Pokemon mastery advisor.

```text
You are helping test another Codex session's Pokemon battle-advice skill.

Repository:
C:\Users\lolno\Downloads\pokemon gold hack

Task:
Generate a fresh, harder Quick Test 001 for the Pokemon mastery advisor. The
test must measure whether its Pokemon battle recommendations are improving, not
whether it can recognize obvious lesson labels.

Important contamination rule:
The main advisor already saw and answered external atlas entries P11-P20 from:
docs/pokemon_mastery/external_research_returns/2026-05-14_deep_research_hidden_info_turn_atlas.md

Do not use P11-P20, their anonymized rewrites, or near-paraphrases of those
same ten prompts. You may use the docs for style and context, but build fresh
scenarios.

Read only documented project notes and local repo materials. Do not use private
conversation context from the main session except what is written in docs. You
may inspect:
- docs/pokemon_mastery/
- docs/boss_ai_*.md and docs/agent_navigation/ if needed
- tools/boss_ai_preference/benchmarks/ only to understand schema/style, not to
  copy any exact public/oracle pair into the public test
- local source/docs needed to verify romhack mechanics

Output exactly two files:

1. docs/pokemon_mastery/quick_tests/quick_test_001_public_generated_2026-05-14.md
2. docs/pokemon_mastery/quick_tests/quick_test_001_answer_key_generated_2026-05-14.md

Secrecy requirement:
- The public file must contain only the test prompts.
- The public file must not contain answers, scoring notes, hidden state, source
  IDs, oracle labels, category tags, expert line names, or "this tests X"
  phrasing.
- The answer-key file must contain the expected answers and rubric.
- Do not summarize the answer key in your final response.
- In your final response, tell the user only that the two files were created
  and that they should give the main advisor the public file first, then the
  answer key only after the advisor has answered.

Test shape:
10 scenarios total:
- 3 vanilla GSC decisions
- 3 local Pokemon Gold romhack / Gym Leader Lab boss decisions
- 2 mechanics or edge-case decisions
- 1 long-route or multi-turn branch decision
- 1 adversarial contamination / no-cheat / no-Team-Preview check

Prompt design:
- Anonymize prompts. No source IDs, replay IDs, atlas IDs, STP/PTA IDs, tags,
  or lesson labels.
- Use concrete public board states, not abstract policy slogans.
- Include enough public information to choose a move or ranked move class:
  active Pokemon, approximate HP, visible status, hazards, revealed moves,
  known speed order if public, relevant bench information if public, and any
  local mechanics profile needed.
- Do not include hidden teams, hidden moves as fact, hidden PP/items/stats, or
  current-turn opponent input.
- The candidate actions should be real moves/switches/move classes, not policy
  labels like "robust progress" or "route conversion".
- Include at least two plausible-looking decoys where a familiar heuristic is
  wrong because the public board context changes it.
- Include at least one scenario where the best answer is "needs context /
  cannot decide safely yet" or where confidence must be capped because a
  decision-relevant local mechanic is unverified.
- Include at least one Rapid Spin / Spikes / spinblock scenario, but do not
  telegraph the answer with tags.
- Include at least one no-Team-Preview early-turn uncertainty scenario.
- Include at least one romhack mechanics scenario where vanilla GSC intuition
  can mislead unless local evidence is cited or uncertainty is capped.

Answer key requirements:
For each scenario, include:
- best action or best ranked move class;
- acceptable alternatives;
- catastrophic or capped answers;
- route reason;
- worst plausible branch;
- answer-changing information;
- scoring notes for the five dimensions:
  action quality, mechanics accuracy, reasoning quality, risk management,
  calibration.

Use this score rubric:
- 0-4 action quality, weight 35;
- 0-4 mechanics accuracy, weight 20;
- 0-4 reasoning quality, weight 20;
- 0-4 risk management, weight 15;
- 0-4 calibration, weight 10.

Caps:
- illegal move or impossible switch: max 40;
- hidden-information abuse: max 50;
- severe blunder that loses a required route: max 60;
- romhack-facing answer with decision-relevant unverified mechanic stated as
  fact: max 70;
- no single recommended move or ranked move class: max 75.

Quality bar:
Make this harder than a recognition quiz. The main advisor should have to
choose among competing plausible routes, preserve or spend resources, price
hidden information, and know when a familiar policy does not apply.

After creating both files, run:
python tools\audit\check_docs_navigation.py
python tools\audit\check_pokemon_mastery_measurement.py
git diff --check -- docs\pokemon_mastery\quick_tests\quick_test_001_public_generated_2026-05-14.md docs\pokemon_mastery\quick_tests\quick_test_001_answer_key_generated_2026-05-14.md

Final response:
Do not reveal answers. Say only:
- created public prompt file path;
- created sealed answer-key file path;
- checks run and passed or failed;
- reminder: give the main advisor only the public file first.
```
