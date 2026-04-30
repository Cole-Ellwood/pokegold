# Flat Changes Duplicate Subsections

Date: 2026-04-28

## Decision

When `scripts/export_changes_from_manifest.py` flattens `docs/manifest.md`,
leave repeated `### Batch N` headings alone, but disambiguate repeated named
subsections by appending the current category in lowercase.

That is why the second flat `Dragon package` heading becomes
`Dragon package learnsets`.

## Rejected

Do not add category suffixes to every repeated batch heading. The flat
`docs/CHANGES.txt` history already tolerates repeated `Batch N` sections from
different manifest categories.

Do not require every manifest subsection title to be globally unique. The
category-scoped `docs/CHANGES_BY_CATEGORY.txt` output is the precise view.

## What Would Change My Mind

If `docs/CHANGES.txt` gains top-level category headings, remove this duplicate
title suffixing and preserve manifest subsection titles exactly.
