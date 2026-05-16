# Boss AI Loop — Operator Runbook

Status: canonical. Entry doc for any Claude or Codex session running boss-ai-loop iterations against the preference + trajectory corpus.

## What this loop is

A divergence-driven iteration cycle that drives the Python scorer at `tools/boss_ai_debugger/scorer.py` to match Claude's labeled preferences across the boss-AI battle fixture corpus. Each iteration finds one place where the scorer's choice disagrees with the labeled answer, identifies the structural reason, ships a minimal scorer rule (or fixture-quality fix, or canonical-scope label), and the audit floor catches any future regression.

The Python scorer is the REVIEW pipeline's model of what the ROM AI does (or should do). The ROM AI is in `engine/battle/ai/boss_policy_*.asm` and changes separately; many improvements there are mirrored by an existing ROM helper (e.g. `BossAI_IsImmunityPivotOpportunity` mirrors iter-14's `type_immunity_pivot` Python rule). Working in Python lets us iterate on alignment without touching asm + risking the selector-replay gate.

## Files in play

| Path | Role |
| --- | --- |
| [tools/boss_ai_debugger/scorer.py](../tools/boss_ai_debugger/scorer.py) | Python scorer; rule-driven per-action contribution accounting. |
| [tools/boss_ai_preference/trajectory_regression.py](../tools/boss_ai_preference/trajectory_regression.py) | Grades scorer vs trajectory labels with first-move + cumulative + route-projection tiebreakers. |
| [tools/boss_ai_preference/route_projection.py](../tools/boss_ai_preference/route_projection.py) | Fixture-aware multi-turn structural validity check (penalises post-self-KO same-mon steps; bonuses honest `boss_next_mon` continuations). |
| [tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json](../tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json) | Battle-state fixtures: boss + player public state, action options, public_notes, tags. |
| [tools/boss_ai_preference/labels/boss_ai_pairwise_preferences.jsonl](../tools/boss_ai_preference/labels/boss_ai_pairwise_preferences.jsonl) | Per-action pairwise preferences with `public_info_scope`. |
| [tools/boss_ai_preference/labels/boss_ai_trajectory_preferences.jsonl](../tools/boss_ai_preference/labels/boss_ai_trajectory_preferences.jsonl) | Per-plan trajectory preferences (3-step plan cards). |
| [tools/audit/check_boss_ai_trajectory_regression.py](../tools/audit/check_boss_ai_trajectory_regression.py) | Legacy-corpus gate (≥ 0.93 strict-label agreement). |
| [tools/audit/check_boss_ai_trajectory_canonical_scope.py](../tools/audit/check_boss_ai_trajectory_canonical_scope.py) | Canonical-scope gate (= 1.0 strict-label agreement on `public_plus_common_meta` labels). |
| [tools/audit/check_boss_ai_preference_regression.py](../tools/audit/check_boss_ai_preference_regression.py) | Pairwise corpus regression (≥ 0.80 strict-label agreement). |

## Iteration template

Per iteration:

1. **Identify a divergence**. Run `python -m tools.boss_ai_preference trajectory-regress` and `python tools/audit/check_boss_ai_preference_regression.py`. The disagreements list is the work queue.
2. **Read the fixture and the label**. Confirm the label's intent before assuming the scorer is wrong. Check `public_info_scope`: a `public_only` label that disagrees with the now-Bayesian scorer may need a `public_plus_common_meta` canonical companion rather than a scorer change. Check the fixture's `public_notes` and `tags` — the labeler's reasoning is often encoded there.
3. **Diagnose the structural reason**. Why does the scorer choose differently? Is a rule missing? Is a text-pattern not being read? Is a structural state condition (HP, status, tag) not being checked?
4. **Choose the fix tier**:
   - **Fixture-quality fix**: bench_state missing, action text typo, etc.
   - **Canonical-scope companion label**: legacy `public_only` label still right under that frame, but loop's canonical frame is now `public_plus_common_meta` — add a Bayesian companion citing the relevant scorer rule.
   - **Python scorer rule**: real reasoning gap. Add a named rule with a narrow trigger and a tested delta. Sized so the legitimate cases win without overpowering unrelated rules.
   - **ROM asm change**: only when the divergence affects actual gameplay AND the Python scorer is already aligned. High risk — gates by selector replay 100%, farcall hl/a, cross-bank, typepassive c-mirror.
5. **Run the verifier floor**:
   ```bash
   python -m unittest discover tools/boss_ai_debugger/tests
   python -m unittest discover tools/boss_ai_preference/tests
   python -m tools.boss_ai_preference trajectory-regress
   python -m tools.boss_ai_preference trajectory-regress --canonical-scope public_plus_common_meta
   python tools/audit/check_boss_ai_preference_regression.py
   python tools/audit/check_release_smoke.py
   ```
   For asm changes also: WSL build (`make pokegold.gbc`), `python scripts/generate_dev_index.py --rom pokegold`, `python tools/audit/check_boss_ai_selector_replay.py`.
6. **Commit** with message `boss-ai-loop: iter N <action>`. Iter numbering is greppable — `git log --oneline | grep '^[0-9a-f]\+ boss-ai-loop: iter '`.
7. **Log a pgoal note** with the specific delta (agreement-rate change, rule added, fixtures affected).

## Scorer rule conventions

Adding a new scorer rule to `scorer.py`:

- **Name** the rule (lowercase snake_case, descriptive). Used in `Contribution.rule` and surfaced in trajectory regression disagreement reports.
- **Narrow trigger first**. Match the labeler's specific phrasing or the fixture's structural condition. A rule that fires on every fixture is almost never right; target the exact divergence.
- **Size the delta** so it overcomes the bonuses on the wrong action without overpowering unrelated context. Typical bonuses are 4–12 points; penalties 6–10. The base score is 50; KO_confirmed is +12; type_wall_pivot is +12.
- **Document the constants** at module top with a comment block explaining what idiom they capture.
- **Unit test** in `tools/boss_ai_debugger/tests/test_regression.py`: positive (the rule fires), negative (unrelated fixture does not), and (if applicable) double-count gating (doesn't stack with related existing rules).

## Canonical-scope companion labels

The loop's canonical reasoning frame is `public_plus_common_meta` (Bayesian inference over revealed-moves-plus-meta priors). Public_only labels written before iter 5 may still be right under both frames but only registered under public_only. When a scorer rule resolves a public_only disagreement under canonical reasoning:

- Add a companion trajectory label at `public_info_scope: "public_plus_common_meta"`.
- Reuse the existing trajectory_a_id / trajectory_b_id from a generated plan card (confirm via `generate_plan_cards(fixture)`).
- Cite the corresponding scorer rule in the note. Explain why the conclusion holds under both scopes if it does.
- The `check_boss_ai_trajectory_canonical_scope.py` audit gates the canonical corpus at 100%; landing a canonical companion that the scorer doesn't actually agree with is a hard fail.

## Verification floor for a boss-ai-loop iter

Mandatory before commit:

- `python -m unittest discover tools/boss_ai_debugger/tests` and `tools/boss_ai_preference/tests` both pass.
- `python tools/audit/check_release_smoke.py` passes (covers preference regression, trajectory regression at 0.93, canonical-scope at 1.0, no-cheat, no stale shipped claims, etc.).
- For asm changes, additionally: `python tools/audit/check_boss_ai_selector_replay.py` at 100%, `check_farcall_hl_clobber.py`, `check_farcall_a_clobber.py`, `check_cross_bank_call.py`, `check_typepassive_c_mirror.py`, `check_boss_ai_no_cheat.py`, `check_boss_ai_memory_budget.py`.

A green floor proves the rule is locally correct and didn't regress something else. The trajectory + pairwise regression numbers are how the loop's progress is measured over time.

## When to stop iterating

- All strict-label disagreements have a structural explanation (scope mismatch, real label-vs-scorer divergence with a justified rule).
- Canonical-scope corpus at 100%; legacy ≥ 95%.
- Pairwise corpus at 100%.
- Manual user gate (boss AI feels right in playtest).

The manual gate is the only thing pgoal cannot auto-complete. The audit gates prevent silent regression.

## When to escalate to ROM-side change

If a divergence:
- affects actual gameplay (not just review-tool agreement);
- the Python scorer is already aligned;
- and the ROM AI is making the same mistake.

Then:
- locate the ROM scoring helper in `engine/battle/ai/boss_policy_*.asm` or `scoring.asm`;
- gate the change behind the AI-overlay flag (the hack's AI uses public-info-only; do not enable hidden-info reads);
- run the full asm audit floor including farcall hl/a, cross-bank, typepassive c-mirror, no-cheat, selector replay, memory budget;
- regenerate `docs/generated/dev_index.md` after the build;
- commit as `boss-ai: <action>` (drop the `-loop` suffix; ROM changes are not Python-loop iters).

## Related docs

- [docs/boss_ai_design_conversation_2026-05-05.md](boss_ai_design_conversation_2026-05-05.md) — the shelved-rebuild context the loop operates within.
- [docs/boss_ai_debugger_state_of_art_implementation_plan_2026-05-15.md](boss_ai_debugger_state_of_art_implementation_plan_2026-05-15.md) — the debugger tooling's long-form plan.
- [docs/pokemon_mastery/compounding_loop.md](pokemon_mastery/compounding_loop.md) — the related mastery-prediction loop (separate; uses its own pgoal state hash).
- [tools/boss_ai_preference/README.md](../tools/boss_ai_preference/README.md) — preference-lab + trajectory-regress CLI surface.
