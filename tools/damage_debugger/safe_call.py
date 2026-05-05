"""Safe function-call helper using HRAM JR-loop sentinel.

Avoids the FarCall RST vector trap that the $0008 sentinel hit. Writes
a 2-byte `jr -2` trap to HRAM at $FFFD-$FFFE, pushes that address as
return, runs the function, and detects completion when PC reaches the
trap.
"""

from __future__ import annotations


SENTINEL_ADDR = 0xFFFD  # 2 bytes free at top of HRAM (right before IE at $FFFF)


def call_function_safe(pyboy, syms, name, *, budget=4800):
    """Call function `name`. Returns (ticks, returned, post_pc).

    On return, the CPU enters an infinite jr-loop at SENTINEL_ADDR. We
    detect completion by checking PC. Caller can then read register
    file for outputs without RST-vector contamination.
    """
    s = syms[name]
    rf = pyboy.register_file

    # Install jr-loop trap at sentinel: 0x18 0xFE = jr -2
    pyboy.memory[SENTINEL_ADDR] = 0x18
    pyboy.memory[SENTINEL_ADDR + 1] = 0xFE

    sp = int(rf.SP)
    new_sp = (sp - 2) & 0xFFFF
    pyboy.memory[new_sp] = SENTINEL_ADDR & 0xFF
    pyboy.memory[new_sp + 1] = (SENTINEL_ADDR >> 8) & 0xFF
    rf.SP = new_sp
    rf.PC = s[1]

    rom_bank_sym = syms.get("hROMBank")
    if rom_bank_sym:
        pyboy.memory[rom_bank_sym[1]] = s[0]
    pyboy.memory[0x2000] = s[0]

    ticked = 0
    while ticked < budget:
        pyboy.tick(2, False, False)
        ticked += 2
        pc = int(rf.PC)
        if pc == SENTINEL_ADDR or pc == SENTINEL_ADDR + 2:
            return ticked, True, pc

    return ticked, False, int(rf.PC)


def read_byte_banked(pyboy, addr, bank=0):
    if 0xD000 <= addr <= 0xDFFF and bank:
        old = int(pyboy.memory[0xFF70])
        pyboy.memory[0xFF70] = bank
        try: return int(pyboy.memory[addr])
        finally: pyboy.memory[0xFF70] = old
    return int(pyboy.memory[addr])


def read_be_u16_banked(pyboy, addr, bank=0):
    if 0xD000 <= addr <= 0xDFFF and bank:
        old = int(pyboy.memory[0xFF70])
        pyboy.memory[0xFF70] = bank
        try:
            hi = int(pyboy.memory[addr]); lo = int(pyboy.memory[addr+1])
        finally: pyboy.memory[0xFF70] = old
    else:
        hi = int(pyboy.memory[addr]); lo = int(pyboy.memory[addr+1])
    return (hi << 8) | lo


def write_byte_banked(pyboy, addr, value, bank=0):
    if 0xD000 <= addr <= 0xDFFF and bank:
        old = int(pyboy.memory[0xFF70])
        pyboy.memory[0xFF70] = bank
        try: pyboy.memory[addr] = value & 0xFF
        finally: pyboy.memory[0xFF70] = old
    else:
        pyboy.memory[addr] = value & 0xFF
