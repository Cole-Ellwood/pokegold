# Boss AI Preference Audit Artifacts

`python -m tools.boss_ai_preference report` writes the latest Markdown and JSON
preference report here.

These reports summarize fixture coverage, label counts, baseline disagreements,
pairwise preference counts, and conflicting duplicate labels. They are
generated artifacts and can be refreshed as feedback accumulates.

`python -m tools.boss_ai_preference threat-report` writes the source-derived
player threat availability report here. That report summarizes boss checkpoints,
voucher/tutor access, available/current-public species counts, direct TM moves,
and incoming fixture threat samples.
