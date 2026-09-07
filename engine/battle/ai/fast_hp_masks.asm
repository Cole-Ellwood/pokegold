; Page-aligned event mask table for the exact selector's HP threshold
; construction (see fast_hp.asm). Included first in the aligned construction
; section so the alignment wastes nothing.
ALIGN 8
BossAI_FastHPEventMasks:
for n, 256
if n % 8 == 0
	db 0
else
	db 1 << ((n % 8) - 1)
endc
endr
