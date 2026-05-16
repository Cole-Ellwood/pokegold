"""Audio register snapshot and music position tracker.

Reads the Game Boy audio IO registers (NR10-NR52, wave RAM) and
the music engine's position pointers from WRAM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChannelState:
    """State of one audio channel."""
    channel: int  # 1-4
    enabled: bool = False
    frequency: int = 0
    volume: int = 0
    duty: int = 0
    length: int = 0
    envelope_dir: str = ""  # "up" or "down"
    sweep: int = 0

    def __str__(self) -> str:
        state = "ON " if self.enabled else "OFF"
        return (
            f"CH{self.channel} [{state}] freq={self.frequency:4d} "
            f"vol={self.volume:2d} duty={self.duty}"
        )


@dataclass
class AudioSnapshot:
    """Full audio register state."""
    channels: list[ChannelState] = field(default_factory=list)
    master_enable: bool = False
    master_volume_left: int = 0
    master_volume_right: int = 0
    wave_ram: bytes = b""
    music_id: int = 0
    music_bank: int = 0
    sfx_id: int = 0

    @staticmethod
    def from_io(io_regs: bytes, wram: bytes | None = None, wram_base: int = 0xC000) -> AudioSnapshot:
        """Build from IO register dump (0xFF00-0xFF7F)."""
        snap = AudioSnapshot()

        if len(io_regs) < 0x40:
            return snap

        nr52 = io_regs[0x26]
        snap.master_enable = bool(nr52 & 0x80)

        nr50 = io_regs[0x24]
        snap.master_volume_left = (nr50 >> 4) & 0x07
        snap.master_volume_right = nr50 & 0x07

        # Channel 1 (square + sweep)
        ch1 = ChannelState(channel=1)
        ch1.enabled = bool(nr52 & 0x01)
        ch1.sweep = io_regs[0x10] >> 4
        ch1.duty = (io_regs[0x11] >> 6) & 0x03
        ch1.volume = (io_regs[0x12] >> 4) & 0x0F
        ch1.envelope_dir = "up" if io_regs[0x12] & 0x08 else "down"
        ch1.frequency = io_regs[0x13] | ((io_regs[0x14] & 0x07) << 8)
        snap.channels.append(ch1)

        # Channel 2 (square)
        ch2 = ChannelState(channel=2)
        ch2.enabled = bool(nr52 & 0x02)
        ch2.duty = (io_regs[0x16] >> 6) & 0x03
        ch2.volume = (io_regs[0x17] >> 4) & 0x0F
        ch2.envelope_dir = "up" if io_regs[0x17] & 0x08 else "down"
        ch2.frequency = io_regs[0x18] | ((io_regs[0x19] & 0x07) << 8)
        snap.channels.append(ch2)

        # Channel 3 (wave)
        ch3 = ChannelState(channel=3)
        ch3.enabled = bool(nr52 & 0x04)
        ch3.volume = (io_regs[0x1C] >> 5) & 0x03
        ch3.frequency = io_regs[0x1D] | ((io_regs[0x1E] & 0x07) << 8)
        snap.channels.append(ch3)

        # Channel 4 (noise)
        ch4 = ChannelState(channel=4)
        ch4.enabled = bool(nr52 & 0x08)
        ch4.volume = (io_regs[0x21] >> 4) & 0x0F
        ch4.envelope_dir = "up" if io_regs[0x21] & 0x08 else "down"
        snap.channels.append(ch4)

        # Wave RAM: FF30-FF3F
        if len(io_regs) >= 0x40:
            snap.wave_ram = io_regs[0x30:0x40]

        return snap

    def summary(self) -> str:
        master = "ON" if self.master_enable else "OFF"
        lines = [f"Audio [{master}] L={self.master_volume_left} R={self.master_volume_right}"]
        for ch in self.channels:
            lines.append(f"  {ch}")
        if self.music_id:
            lines.append(f"  Music ID: ${self.music_id:02X} (bank ${self.music_bank:02X})")
        return "\n".join(lines)


__all__ = ["ChannelState", "AudioSnapshot"]
