# Delete Duplicate Diary Bundle

Date: 2026-04-28

## Decision

Delete `outbox/diaries.md`.

The file was a concatenated bundle of already tracked outbox notes. After
ignoring only the inserted `---` separators and `## Source file:` headings, each
section matched its separate source file, including
`outbox/codex_weird_attraction_notebook_sgb.md`.

## Rejected

- Keeping both the bundle and the separate files. That makes grep noisier and
  gives future sessions two surfaces for the same writing.
- Moving the bundle to an archive folder. An archive would preserve duplication
  without adding source truth.

## What Would Change My Mind

If the project wants single-file anthologies for reading outside the repo, create
them from the separate files as generated/exported artifacts, not as another
tracked source of truth.
