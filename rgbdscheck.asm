IF !DEF(__RGBDS_MAJOR__)
	fail "pokegold requires rgbds v1.0.0 or newer."
ENDC
IF __RGBDS_MAJOR__ < 1
	fail "pokegold requires rgbds v1.0.0 or newer."
ENDC
; Upper bound: a future rgbds v2 may remove syntax this codebase depends on
; (v1.0.0 already removed ldio, ld [c], and STRIN/STRSUB forms). Vet the
; changelog, then raise this bound alongside the vendored toolchain pin.
; See tech_debt/EVIDENCE/td_008_rgbds_changelog.md for the upgrade recipe.
IF __RGBDS_MAJOR__ > 1
	fail "pokegold is only vetted against rgbds v1.x; see rgbdscheck.asm before building with a newer major version."
ENDC
