# Context Management Plan

Date: 2026-05-14

Purpose: keep the Pokemon mastery project usable as the documentation archive
grows. The plan favors small live context, measured transfer, and evidence
preservation over broad reorganization.

## Sources Checked

Local docs read or sampled:

- `master_index.md`
- `active_goal.md`
- `training_cycle.md`
- `measurement_minigoal_2026-05.md`
- `replay_turn_pause_protocol.md`
- `boss_turn_advice_template.md`
- `cookbook.md`
- `source_to_policy_ledger.md`
- `cross_domain_autonomy_policy.md`
- `study_roadmap_2026-05-14.md`
- recent `workspace/quick_tests/replay_turn_pause_052` through `057`

Web sources checked:

- [Pokemon Showdown ladder help](https://pokemonshowdown.com/pages/ladderhelp):
  Elo, GXE, and Glicko-1 are separate ladder ratings; no universal official Elo
  standard.
- [OpenAI evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices):
  define the eval objective, dataset, metrics, comparison loop, and continuous
  evaluation.
- [Anthropic subagents documentation](https://code.claude.com/docs/en/sub-agents):
  subagents can preserve main-context space by doing bounded exploration in
  separate contexts and returning compact summaries.
- [Anthropic agent guide](https://resources.anthropic.com/building-effective-ai-agents):
  choose single-agent, workflow, or multi-agent complexity based on value and
  context-management needs.

## Problem Comparisons

Context volume:

- Option A: split large docs by topic. This improves physical readability but
  creates migration cost, broken references, and more upkeep.
- Option B: keep archives intact and add small context packets per work mode.
  This preserves evidence while limiting live context.
- Decision: Option B.

Retrieval and overfitting:

- Option A: tag every prompt and policy by theme. This speeds study but can leak
  the intended lesson into scored prompts.
- Option B: separate visible study tags from sealed/public prompt text.
- Decision: Option B.

Measurement:

- Option A: normalize the full CSV now. Clean but risky and high-cost.
- Option B: keep the ledger append-only and use small derived summaries.
- Decision: Option B.

Latest lessons:

- Option A: always load the newest quick tests. This risks recency bias and
  overcorrection.
- Option B: load active failure classes with opposite-boundary summaries.
- Decision: Option B.

Romhack mechanics:

- Option A: load vanilla strategy first and append a generic "verify local"
  warning. This warning becomes easy to ignore.
- Option B: put local mechanics status into the retrieval gate.
- Decision: Option B.

Tooling:

- Option A: build a full retrieval app, embeddings, selector, and schema.
- Option B: run the process manually first; automate only repeated pain points.
- Decision: Option B.

Subagents:

- Option A: main-agent-led specialist bursts.
- Option B: standing council for every work block.
- Decision: Option A by default; Option B only for declared audits.

## Granular Vote Record

Majority rule: main assistant plus Copernicus, Carson, Euler, and Curie. An
idea passes with at least 3 yes votes. `A` means abstain with caveat.

| ID | Atomic implementation idea | Main | Copernicus | Carson | Euler | Curie | Result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P01 | Create `active_context.md` capped near 100-150 lines. | Y | Y | Y | Y | Y | Pass 5/5 |
| P02 | Create this canonical plan and vote record. | Y | Y | Y | Y | Y | Pass 5/5 |
| P03 | Create `policy_cards/README.md` with compact card format. | Y | Y | Y | Y | Y | Pass 5/5 |
| P04 | Create only 4-6 active policy cards now. | Y | Y | Y | Y | Y | Pass 5/5 |
| P05 | Keep quick tests and reviews append-only evidence. | Y | Y | Y | Y | Y | Pass 5/5 |
| P06 | Do not bulk-split `source_to_policy_ledger.md`. | Y | Y | Y | Y | Y | Pass 5/5 |
| P07 | Postpone manifest/tooling until manual retrieval pain repeats twice. | Y | Y | Y | Y | Y | Pass 5/5 |
| P08 | Define five context packets. | Y | Y | Y | Y | Y | Pass 5/5 |
| P09 | Add a session header template. | Y | Y | Y | Y | Y | Pass 5/5 |
| P10 | Add active-error digest from recent fresh replay runs. | Y | Y | Y | Y | Y | Pass 5/5 |
| P11 | Require opposite-boundary summaries before live-context promotion. | Y | Y | Y | Y | Y | Pass 5/5 |
| P12 | Create mechanics-pending index before ambitious tooling. | Y | Y | Y | Y | Y | Pass 5/5 |
| P13 | Define sealed replay-transfer packet as primary gate. | Y | Y | Y | Y | Y | Pass 5/5 |
| P14 | Use runs 052-057 as current baseline. | Y | Y | Y | A | Y | Pass 4/5 |
| P15 | Label future ledger rows using existing conventions, no CSV migration. | Y | Y | Y | Y | Y | Pass 5/5 |
| P16 | Use provisional gate: 55% top, 70% acceptable, 0 severe, no repeated uncorrected error twice. | Y | A | Y | A | Y | Pass 3/5 |
| P17 | Cap regression probes: one small probe per fresh miss by default; retire/merge after transfer. | Y | Y | Y | Y | A | Pass 4/5 |
| P18 | Reject artifact-count as a progress metric. | Y | Y | Y | Y | Y | Pass 5/5 |
| P19 | Default to main-agent-led specialist bursts. | Y | Y | Y | Y | Y | Pass 5/5 |
| P20 | Use standing councils only for declared audit blocks. | Y | Y | Y | Y | Y | Pass 5/5 |
| P21 | Define web-search and local-only triggers. | Y | Y | Y | Y | Y | Pass 5/5 |
| P22 | Require bounded subagent packets. | Y | Y | Y | Y | Y | Pass 5/5 |
| P23 | Require subagent output to map to policy format before adoption. | Y | Y | Y | Y | Y | Pass 5/5 |
| P24 | Validate edits with lightweight checks. | Y | Y | Y | Y | Y | Pass 5/5 |

Vote caveats:

- P14 is a current baseline only, not a mastery baseline.
- P16 thresholds are provisional and should be recalibrated after 1-2 sealed
  packets.
- P17 does not delete evidence. "Retire/merge" means mark or index the probe
  after transfer. If one replay exposes multiple distinct error classes, allow
  one small probe per distinct boundary.

## Approved Operating Model

Use an evidence pyramid:

1. `active_context.md` is the live packet.
2. `policy_cards/` contains compact active rules with opposite boundaries.
3. Existing quick tests, reviews, ledgers, and STP entries remain the evidence
   archive.

Use sealed replay-transfer packets as the official improvement gate. Use
constructed probes as bounded regression checks. Use artifact creation only as
hygiene.

Use web search when it creates or checks an expert source, current GSC replay,
current Showdown/rating source, source-to-policy extraction, or repeated-error
investigation. Do not use web search before sealed answers or for local romhack
mechanics.

Use subagents as bounded specialists by default. Use a standing council only
for declared architecture, audit, or major research blocks.

## Implementation Roadmap

Done in this patch:

- Add `active_context.md`.
- Add this plan and vote record.
- Add `policy_cards/README.md`.
- Add active policy cards for cash-out, sleep/set ambiguity, hazard Spin
  windows, support handoff, and romhack mechanics firewall.
- Add `romhack_deltas/mechanics_pending_index.md`.
- Update `master_index.md` so future starts route through the context packet.

Next manual cycle:

1. Run one sealed replay-transfer packet using the active context packet.
2. Score against the provisional gate.
3. Update at most one policy card and one measurement row.
4. If the same retrieval pain happens twice, consider a read-only trend report.

Rejected for now:

- Full doc split.
- Full retrieval app.
- Embeddings or selector tooling.
- CSV schema migration.
- Artifact-count progress scoring.
