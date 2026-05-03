# TD-008 — RGBDS upgrade research

**Generated:** 2026-05-03
**Source:** `claude/great-germain-2c8cb8` session.
**Reason:** `FIX_PROPOSALS.md` TD-008 step 1: "Pick target version. As
of 2026, RGBDS v1.7+ likely. Read the RGBDS changelog… to understand
syntax/behavior changes between v1.0.1 and target." This file pins the
actual current state of upstream RGBDS, identifies whether an upgrade
is even applicable, and what migration cost (if any) a future upgrade
will have. **Does not perform the upgrade** — that is a separate session.

## Headline finding

**The current pin (`v1.0.1`) IS the current upstream stable.** No
upgrade is available; "upgrade RGBDS" right now is a no-op.

`FIX_PROPOSALS.md` TD-008's step 1 anticipated v1.7+ in 2026, but the
project re-numbered to SemVer with `v1.0.0` (2025-11-01) and `v1.0.1`
(2026-01-01) — see "Version timeline" below. The leap from v0.9.x →
v1.0.0 was the SemVer pivot, not a feature dump that pushed past v0.9.

TD-008 should remain **open** as a watch item for the next stable
(`v1.1.0` or `v2.0.0`), with the work currently scoped to this
research step only.

## Version timeline

Pulled from `https://api.github.com/repos/gbdev/rgbds/releases` on
2026-05-03.

| Tag | Published | Type | Notes |
| --- | --- | --- | --- |
| **v1.0.1** | 2026-01-01 | stable | **Current pin.** Bug fixes only over v1.0.0; SemVer-patch, fully backwards-compatible. |
| v1.0.0 | 2025-11-01 | stable | SemVer pivot. **Removed** several long-deprecated forms (see below). |
| v0.9.4 | 2025-07-31 | stable | Bug fixes |
| v0.9.3 | 2025-06-30 | stable | Bug fixes |
| v0.9.2 | 2025-05-04 | stable | Bug fixes |
| v0.9.1 | 2025-02-02 | stable | Bug fixes |
| v0.9.0 | 2024-12-25 | stable | Last 0.x; deprecated `ldio`/`ld [c]`/`ldh [$xx]` (removed in v1.0.0) |
| v0.8.0 | 2024-06-28 | stable | C++ refactor; removed un-`DEF`'d symbols and `-i`/`-H`/`-l`/`-L` |
| v0.7.0 | 2023-12-31 | stable | Static Linux binaries; many additions; deprecated un-`DEF`'d symbols |
| v0.6.x | 2022 | stable | — |
| v0.5.x | 2021 | stable | — |

`master` branch (HEAD `f0161b41`, 2026-04-29) is **170 commits ahead**
of `v1.0.1` (`api.github.com/.../compare/v1.0.1...master`); none of
those commits has been tagged a release. Inspecting recent commit
subjects: lexer refactoring, fuzzing-found UB fixes, internal
renaming. Consistent with patch/minor groundwork, no breaking syntax
shifts visible at the surface.

`https://rgbds.gbdev.io/` confirms: docs default route is `v1.0.1`,
"master" is listed only as a separate dropdown entry alongside tagged
versions.

## What changed at v0.9.x → v1.0.0 (and why this codebase is unaffected)

`v1.0.0` removed three long-deprecated forms. We verified none are
present in this codebase:

| Removed in v1.0.0 | Replacement | Project search |
| --- | --- | --- |
| `ldio [c], a` / `ldio a, [c]` | `ldh [c], a` / `ldh a, [c]` | `grep -rn '\bldio\b'` → 0 hits |
| `ld [c], a` / `ld a, [c]` | `ldh [c], a` / `ldh a, [c]` | `grep -rEn '^\s*ld\s+\[c\]\s*,\s*a\|^\s*ld\s+a\s*,\s*\[c\]'` → 0 hits |
| `ldh [$xx]` short form | `ldh [$FFxx]` long form | `grep -rEn 'ldh\s+\[\$[0-9a-fA-F]{2}\]'` → 0 hits |
| Multi-value strings as numbers (`-Wnumeric-string`) | Single `'c'` char constant or `CHARVAL` | warning was tied to the deprecated form; non-issue once the form is gone |

`v1.0.0` also **deprecated** (still buildable, warns under
`-Weverything`) several legacy idioms; we verified none are present:

| Deprecated in v1.0.0 | Replacement | Project search |
| --- | --- | --- |
| `STRIN`, `STRRIN`, `STRSUB`, `CHARSUB` (1-indexed) | `STRFIND`, `STRRFIND`, `STRSLICE`, `STRCHAR` (0-indexed) | `grep -rEn '\b(STRIN\|STRRIN\|STRSUB\|CHARSUB)\b'` → 0 hits |
| `rgbfix -O/--overwrite` | (use the default behavior) | Makefile uses `-cjsv -k 01 -l 0x33 -m MBC3+TIMER+RAM+BATTERY -r 3 -p 0`, no `-O` |
| Single-value strings as numbers | `'c'` or `CHARVAL` | not applicable — no migration trigger seen in the build |

`Makefile` already runs `-Weverything` on rgbasm/rgblink/rgbfix/rgbgfx
(no `-Wno-obsolete`), so a clean build on v1.0.1 is implicit
confirmation we have no deprecated forms slipping through.

**Conclusion:** the current build is fully clean against everything
v1.0.0 removed and everything v1.0.0 deprecated. Migration cost from
v1.0.x to a hypothetical v1.0.x patch is zero.

## What v1.0.1 fixed over v1.0.0

From the v1.0.1 release notes (2026-01-01):

- **rgbasm:** stray `...`/`....` symbol names; `SECTION UNION` of ROM
  sections; `-MG`/`-MC` not seeing `-P/--preinclude`; non-UTF-8 EOF
  hang.
- **rgblink:** misleading messages on undefined-symbol expressions and
  invalid object files.
- **rgbgfx:** ambiguous-alpha crash; doc clarifications.
- **All:** `errno`-related option-parse mis-reporting; long error
  backtraces could stack-overflow during fuzzing.

None of these affect the project as built, but they're all "free" if
we move from v1.0.0 → v1.0.1. Since we're already on v1.0.1, this is
moot.

## Where the v1.0.1 pin lives in this repo

Verified 2026-05-03:

- `rgbdscheck.asm` — checks `__RGBDS_MAJOR__ >= 1` (loose: permits any
  v1+, including hypothetical v2). Could be tightened.
- `.github/workflows/main.yml:9` — `rgbds_version: v1.0.1`.
- `CLAUDE.md:77` — build command points at `rgbds-1.0.1/`.
- `tools/audit/check_docs_navigation.py:149,194` — vendored-toolchain
  prefix `rgbds-1.0.1/`.
- `tools/audit/check_workspace_hygiene.py:120` — `rgbds-1.0.1` zip-
  bundle ignore rule.
- `docs/agent_navigation/verification_matrix.md:26` — example invocation.
- `docs/boss_ai_post_patch_notes.md:302-303` — historical reference.
- Various `audit/*.md` historical docs — older invocations; not load-
  bearing.

A future upgrade has to touch the first five (vendored toolchain
folder, CI workflow, build command in `CLAUDE.md`, two audit scripts,
and `rgbdscheck.asm` if we tighten the version floor). The historical
audit docs are immutable journal entries — leave them.

## Recommendation: target version pin

**Stay on v1.0.1.** The next concrete decision point is when upstream
ships a new tagged release. The hand-off for that future session:

| Trigger | What target this codebase should adopt |
| --- | --- |
| **v1.0.x patch** (e.g. v1.0.2) | Adopt within one session. SemVer says zero migration cost. Re-run the v1.0.0 deprecation grep table above as confirmation; rebuild; `make compare` against `roms.sha1`. |
| **v1.x.0 minor** (e.g. v1.1.0) | Adopt within one session, *but* read the release notes carefully — minor releases add features and may deprecate (not remove) idioms. Same verification floor as a patch, plus a deprecation grep pass. |
| **v2.0.0 major** | Multi-session. Major bumps allow removed-since-v1 forms. Re-walk `__RGBDS_MAJOR__` floor in `rgbdscheck.asm`. SHA1 may shift — be ready to refresh `roms.sha1` only after a clean diff explanation. |

Until upstream tags any of those, TD-008 stays **open** as a watch
item rather than a workable backlog row. Recommend leaving the
severity at MEDIUM but updating the "order" rank — without an
available upgrade target, the work simply cannot be sequenced ahead
of items that have a real fix path.

## Side finding: `rgbdscheck.asm` floor is loose

```asm
IF !DEF(__RGBDS_MAJOR__)
    fail "pokegold requires rgbds v1.0.0 or newer."
ENDC
IF __RGBDS_MAJOR__ < 1
    fail "pokegold requires rgbds v1.0.0 or newer."
ENDC
```

This permits any v1+, **including a hypothetical v2** that may have
removed forms we still depend on. Not a TD-008 deliverable, but the
right time to tighten this is *before* v2.0.0 ships, not after a
silent build break.

Suggested follow-up (small, separate task — not in scope for this
research session): add an upper-bound check, e.g.

```asm
IF __RGBDS_MAJOR__ > 1
    fail "pokegold has been validated against rgbds v1.x; \
          v2.x may remove forms used here. Re-run the validation \
          checklist before unpinning."
ENDC
```

That belongs in TD-008's "Updated" subsection in `FIX_PROPOSALS.md` as
a recommended pre-emptive task, not a standalone TD-### finding.

## Reproduction recipe

If a future agent needs to refresh this evidence file:

```bash
# 1. List all releases (no auth needed for public repo).
curl -sL 'https://api.github.com/repos/gbdev/rgbds/releases?per_page=100' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); \
    [print(f\"{r['tag_name']}\t{r['published_at'][:10]}\tprerelease={r['prerelease']}\") for r in d]"

# 2. Pull body of a specific release.
curl -sL 'https://api.github.com/repos/gbdev/rgbds/releases/tags/v1.0.1' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['body'])"

# 3. Compare a pinned tag to master HEAD.
curl -sL 'https://api.github.com/repos/gbdev/rgbds/compare/v1.0.1...master' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); \
    print('ahead:', d.get('ahead_by'), 'behind:', d.get('behind_by'))"

# 4. Confirm no v1.0.0-removed forms in this codebase.
grep -rEn '\bldio\b' --include='*.asm' .
grep -rEn '^\s*ld\s+\[c\]\s*,\s*a|^\s*ld\s+a\s*,\s*\[c\]' --include='*.asm' .
grep -rEn 'ldh\s+\[\$[0-9a-fA-F]{2}\]' --include='*.asm' .
grep -rEn '\b(STRIN|STRRIN|STRSUB|CHARSUB)\b' --include='*.asm' --include='*.inc' .
```

If any of those greps return hits at the time of refresh, that's a
**regression** — these forms were verified absent on 2026-05-03. The
build would also fail under v1.0.x, so a regression here is unlikely
to ship silently.
