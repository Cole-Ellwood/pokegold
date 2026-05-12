"""M3 acceptance: walk BattleCommand_DamageCalc and print the disassembly."""

from __future__ import annotations

LEGACY_EXIT = (
    "tools.damage_debugger.legacy scripts are pruned one-shot drivers; "
    "use active tools.damage_debugger modules instead."
)
raise SystemExit(LEGACY_EXIT)

import sys

from .disasm import walk_function
from .emulator import DebugSession


def main() -> int:
    target = "BattleCommand_DamageCalc"
    with DebugSession.open("pokegold_debug") as sess:
        def read_byte(bank: int, addr: int) -> int:
            if addr < 0x4000:
                return int(sess.pyboy.memory[addr])
            return int(sess.pyboy.memory[bank, addr])

        instrs = walk_function(read_byte, sess.symbols, target, max_bytes=0x600)
        if not instrs:
            print(f"FAIL: walker returned 0 instructions for {target}", file=sys.stderr)
            return 1
        print(f"# {target}: {len(instrs)} instructions, "
              f"${instrs[0].bank:02x}:{instrs[0].pc:04x}-${instrs[-1].end-1:04x}")
        for instr in instrs[:30]:
            label = sess.symbols.render(instr.bank, instr.pc)
            byte_str = " ".join(f"{b:02x}" for b in
                                 ([instr.opcode] + list(instr.operand)))
            print(f"  ${instr.bank:02x}:{instr.pc:04x}  {byte_str:<10}  "
                  f"{instr.mnemonic:<28}  ; {label}")
        if len(instrs) > 30:
            print(f"  ... +{len(instrs) - 30} more")
        last_pc = instrs[-1].pc
        last_end = instrs[-1].end
        print(f"# Last instruction at ${last_pc:04x}, ends at ${last_end:04x}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
