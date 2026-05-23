; SetWRAMBank — switch the WRAMX bank window at $D000-$DFFF.
;
; Input:  a = target bank (1-7). Bank 0 is illegal (maps to bank 1 on hardware).
; Output: [rSVBK] = a; [hWRAMBank] = a. Caller-saved otherwise.
; Clobbers: nothing else.
;
; Direct ldh writes to [rSVBK] are reserved for boot init (before the shadow
; exists). Every other site goes through this helper so [hWRAMBank] stays in
; sync. Inline bank switches are exceptional and MUST update both the hardware
; register and the shadow; see docs/asm_authoring_guide.md §1.6 + Pan Docs SVBK.
;
; No di/ei here: the helper only spans the two writes, not the bank-2 access
; window. Callers that need atomic switch+access+restore around interrupts
; must bracket di/ei themselves.

SetWRAMBank::
	ldh [rSVBK], a
	ldh [hWRAMBank], a
	ret
