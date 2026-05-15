# Council Vote Summary - 2026-05-14

The user requested four subagents with different perspectives to agree by
majority on the prompt for GPT-5.5 Pro.

## Council Seats

- Measurement Skeptic: focus on metric validity, weak evidence, contamination,
  and proof thresholds.
- Pokemon Coach: focus on GSC singles skill, no-Team-Preview discipline, and
  the best next practice mode.
- Context Minimalist: focus on compact context, avoiding document drift, and
  selecting the fewest sufficient files.
- Adversarial Reviewer: focus on overfitting, hidden-information leakage,
  Goodharting, and preventing generic answers.

## Granular Votes

| Prompt idea | Vote | Decision |
| --- | ---: | --- |
| Ask for external audit of current measurement | 4 yes / 0 no | Include |
| Ask for the next 3 work blocks | 4 yes / 0 no | Include |
| Ask for stop/continue criteria for long sessions | 4 yes / 0 no | Include |
| Require concrete artifacts or scores | 4 yes / 0 no | Include |
| Ask for broad GSC strategy study | 0 yes / 4 no | Exclude |
| Ask for code/tooling ideas as a main topic | 0 yes / 4 no | Exclude |
| Allow tiny tooling only if it improves scoring, leakage control, or rep throughput | 2 yes / 2 no, main agent yes | Include as optional constraint only |

## Context Packet Decision

Majority themes:

- Include score ledger, measurement rules, replay protocol, and current compact
  context.
- Include a measurement summary/facts file so GPT-5.5 Pro does not have to infer
  every trend from the CSV.
- Include a recent fresh transfer and the latest constructed probe so the model
  can compare honest transfer evidence with regression evidence.
- Avoid broad strategy notes, cookbook, source-to-policy archives, large review
  archives, and many policy cards because they invite more doctrine instead of
  auditing whether doctrine is improving decisions.

Final copied context files are in `context_files/` and total exactly 10 copied
repo files.
