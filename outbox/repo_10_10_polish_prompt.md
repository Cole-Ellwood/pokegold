# Repo 10/10 Polish Prompt

Use this when starting a fresh Codex session whose job is to make the repository
feel like a 10/10 workspace: organized, visually calm, minimalist where it can
be, and still safe for a brittle Gen 2 ROM-hack build.

## Companion Message To Paste

```text
You are working in:

C:\Users\lolno\Downloads\pokemon gold hack

Goal: make the project a 10/10 for organization, cleanliness, and future Codex
navigation. Treat the current repo as a trusted clean checkpoint. Do not change
gameplay, ROM behavior, trainer/Pokemon data, maps, RAM, generated docs, or build
outputs unless I explicitly approve that scope.

My current read is: 8/10 organized, 7/10 clean, 9/10 future-agent navigable. The
navigation/control-tower docs are strong. The remaining ugliness is mostly
physical workspace clutter: ignored build outputs, object files, ROMs, maps,
symbols, generated graphics outputs, and old-school assembly/build layout noise.

First read, in order:
1. docs/README.md
2. docs/agent_navigation/start_card.md
3. docs/project_roadmap.md
4. docs/agent_navigation/source_output_ownership.md
5. docs/build.md
6. .gitignore
7. Makefile
8. outbox/repo_10_10_polish_prompt.md

Start by inspecting, not editing:
- git status --short --branch
- git status --ignored --short
- git diff --stat
- git clean -ndX
- git check-ignore -v on representative noisy files
- rg -n "pokegold\\.gbc|pokesilver\\.gbc|\\.map|\\.sym|\\.o|dist|\\.local|workspace" docs tools scripts Makefile .gitignore

Task:
1. Define what 10/10 means for this repo on three axes: organization,
   cleanliness, and future-agent navigability.
2. Audit the physical clutter without deleting anything. Separate expected build
   products from stale scratch, release artifacts, local probes, and files that
   only look scary because this is an RGBDS assembly repo.
3. Look for safe improvements with this priority order:
   - documentation that explains raw-folder noise where Codex will see it;
   - .gitignore comments or patterns that clarify ownership without hiding
     source;
   - a tiny source-only or hygiene-check helper if it genuinely reduces future
     confusion;
   - build-output relocation only if it is proven safe and I explicitly approve
     it after a plan.
4. Do not run destructive cleanup. Do not run git clean, Remove-Item, deletion
   scripts, or broad moves. If deletion or relocation seems necessary, stop with
   a concrete plan that names exact files, exact rebuild commands, risks, and how
   to restore the current layout.
5. Keep the old-school ROM-hack constraints honest. Root-level .gbc/.map/.sym
   outputs may be visually ugly, but tools and docs may rely on them as linker
   truth. If you propose moving outputs, audit every script/doc/tool reference
   first and expect to update docs/build.md, docs/generated/dev_index.md
   regeneration flow, release smoke, trace tools, and checksum workflows.

Definition of done:
- The repo should either be visibly cleaner or have a precise no-churn
  recommendation explaining why physical cleanup would be riskier than the noise.
- Any docs/tooling changes must preserve source/generated/output boundaries.
- Run python tools\audit\check_docs_navigation.py.
- Run git diff --check.
- If Makefile/build/tooling/output layout changes, also run the documented WSL
  build for pokegold.gbc and pokesilver.gbc, regenerate docs/generated/dev_index.md
  if linker outputs change, and run python tools\audit\check_release_smoke.py.
- End with a clear report: what improved, what stayed intentionally noisy, what
  still prevents 10/10, and whether the tree is clean or what commit/checkpoint
  is needed.
```

## Notes For The Fresh Session

The danger is a fake cleanup: moving outputs or deleting ignored files can make
the folder look nicer while breaking build, trace, release, or generated-index
assumptions. The right pass starts by making clutter legible. Only after that
should it consider changing where clutter lives.

Prefer small, reversible changes. A 10/10 repo is not one with no artifacts; it
is one where a future worker can tell immediately which artifacts are expected,
which are disposable, and which are source truth.
