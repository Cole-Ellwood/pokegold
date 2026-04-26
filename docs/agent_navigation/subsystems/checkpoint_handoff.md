# Checkpoint And Handoff Micro-Index

Use this when the task is broad, a session is ending, the worktree is dirty, or
future helpers need a clean stopping point.

## Fast Route

| Need | Go to |
| --- | --- |
| Current workstreams | `docs/project_roadmap.md` |
| Helper-doc entrypoint | `docs/README.md` |
| Verification floors | `docs/agent_navigation/verification_matrix.md` |
| Durable evidence | `docs/agent_navigation/artifact_catalog.md` |
| Prior handoff pattern | `outbox/` |
| Current dirty state | `git status --short --branch` |

## Dirty Worktree Protocol

1. Run `git status --short --branch`.
2. Identify which files this session touched.
3. Do not revert, reset, or clean unrelated changes.
4. If a file contains both old and new edits, inspect before patching.
5. If the user asks for a checkpoint, split by logical ownership rather than by
   whichever files happen to be dirty.

## Commit Boundary Hints

Good commit slices:

- gameplay/source change plus generated/audit updates needed for that change;
- docs/navigation-only pass;
- trace artifact or proof-capsule evidence pass;
- tooling/audit improvement pass.

Weak commit slices:

- mixed gameplay and unrelated docs beauty;
- generated files without the source or generator reason;
- scratch outputs from `.local/`, `workspace/`, or `dist/` during ordinary source
  cleanup.

## Handoff File Shape

When context is tight or another session needs one artifact, write a markdown
file under `outbox/` with:

- current branch and dirty status;
- user request and nonfunctional/functionality boundary;
- files changed in this pass;
- exact verification commands and results;
- source-truth vs generated vs scratch distinction;
- blocked items with exact unblock steps;
- first files the next session should read;
- copy-pastable prompt for the next session.

## Stopping-Point Report

Every stopping point should answer:

- What changed?
- What did not change?
- What passed?
- What remains blocked?
- Which dirty files were pre-existing or outside this pass?

Do not present a checkpoint as cleaner than it is. A beautiful handoff is one
where the next helper can trust the map, including the warnings.

