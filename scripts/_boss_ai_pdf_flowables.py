"""Custom reportlab Flowables for docs/boss_ai_architecture.pdf.

Split out of generate_boss_ai_architecture_pdf.py so each file stays
under the project's 700-line hand-written threshold. Imported by the
generator only.
"""

from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Flowable


# ---------------------------------------------------------------------------
# palette
# ---------------------------------------------------------------------------

INK = colors.HexColor("#1B1F23")
INK_SOFT = colors.HexColor("#3A4149")
ACCENT = colors.HexColor("#0B5FA5")
ACCENT_SOFT = colors.HexColor("#DCE9F4")
WARN = colors.HexColor("#B8540C")
WARN_SOFT = colors.HexColor("#FBE9D6")
GOOD = colors.HexColor("#1F7A4A")
GOOD_SOFT = colors.HexColor("#DCEFE3")
NEUTRAL_BG = colors.HexColor("#F4F4F2")
HAIRLINE = colors.HexColor("#C5C5C0")


# ---------------------------------------------------------------------------
# flowables
# ---------------------------------------------------------------------------


class HRule(Flowable):
    def __init__(self, width=None, color=HAIRLINE, thickness=0.5, space_before=4, space_after=8):
        super().__init__()
        self.width = width
        self.color = color
        self.thickness = thickness
        self.space_before = space_before
        self.space_after = space_after

    def wrap(self, available_width, available_height):  # noqa: ARG002
        w = self.width if self.width is not None else available_width
        self._w = w
        return w, self.thickness + self.space_before + self.space_after

    def draw(self):
        c = self.canv
        c.setStrokeColor(self.color)
        c.setLineWidth(self.thickness)
        y = self.space_after
        c.line(0, y, self._w, y)


class StackedDiagram(Flowable):
    """Top: 'Boss AI Overlay' with three pillars. Bottom: 'Vanilla AI'. Arrow between."""

    def __init__(self, width=6.8 * inch, height=3.6 * inch):
        super().__init__()
        self.width = width
        self.height = height

    def wrap(self, available_width, available_height):  # noqa: ARG002
        return self.width, self.height

    def draw(self):
        c = self.canv
        w = self.width
        h = self.height

        top_h = 1.85 * inch
        top_y = h - top_h
        c.setFillColor(ACCENT_SOFT)
        c.setStrokeColor(ACCENT)
        c.setLineWidth(1.2)
        c.roundRect(0, top_y, w, top_h, 8, stroke=1, fill=1)

        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(14, top_y + top_h - 22, "Boss AI Overlay")
        c.setFillColor(INK_SOFT)
        c.setFont("Helvetica-Oblique", 9.5)
        c.drawString(14, top_y + top_h - 36, "adjustments layered on top of vanilla scoring")

        pillars = [
            ("Sees more", "public state tracking", "seen species,\nrevealed moves,\nswitch tallies"),
            ("Plans further", "lookahead + KO bands", "1-2 turn projection,\nprecomputed matchup\ntables, item math"),
            ("Switches like a human", "type-immune pivots", "revenge respect,\nswitch cooldown,\nbench scan"),
        ]
        pillar_w = (w - 14 * 4) / 3
        pillar_h = 1.05 * inch
        py = top_y + 14
        for i, (title, sub, body) in enumerate(pillars):
            px = 14 + i * (pillar_w + 14)
            c.setFillColor(colors.white)
            c.setStrokeColor(ACCENT)
            c.setLineWidth(0.8)
            c.roundRect(px, py, pillar_w, pillar_h, 6, stroke=1, fill=1)
            c.setFillColor(INK)
            c.setFont("Helvetica-Bold", 10.5)
            c.drawString(px + 10, py + pillar_h - 16, title)
            c.setFillColor(ACCENT)
            c.setFont("Helvetica-Oblique", 8.5)
            c.drawString(px + 10, py + pillar_h - 28, sub)
            c.setFillColor(INK_SOFT)
            c.setFont("Helvetica", 8.5)
            for j, line in enumerate(body.split("\n")):
                c.drawString(px + 10, py + pillar_h - 44 - j * 11, line)

        arrow_top = top_y - 4
        arrow_bot = top_y - 30
        cx = w / 2
        c.setStrokeColor(INK_SOFT)
        c.setLineWidth(2)
        c.line(cx, arrow_top, cx, arrow_bot)
        c.setFillColor(INK_SOFT)
        c.setStrokeColor(INK_SOFT)
        path = c.beginPath()
        path.moveTo(cx - 6, arrow_bot + 2)
        path.lineTo(cx + 6, arrow_bot + 2)
        path.lineTo(cx, arrow_bot - 8)
        path.close()
        c.drawPath(path, stroke=0, fill=1)
        c.setFont("Helvetica-Oblique", 8.5)
        c.setFillColor(INK_SOFT)
        c.drawString(cx + 12, arrow_bot + 8, "calls into vanilla AI for the base score")

        bot_h = 0.95 * inch
        c.setFillColor(NEUTRAL_BG)
        c.setStrokeColor(HAIRLINE)
        c.setLineWidth(1)
        c.roundRect(0, 0, w, bot_h, 8, stroke=1, fill=1)
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(14, bot_h - 22, "Vanilla Gen 2 Trainer AI")
        c.setFillColor(INK_SOFT)
        c.setFont("Helvetica", 9.5)
        c.drawString(14, bot_h - 38, "AI_Basic, AI_Setup, AI_Aggressive, AI_Risky, ...")
        c.drawString(14, bot_h - 52, "score each move, randomize, pick max - this still runs underneath")


class TurnFlowchart(Flowable):
    """8-step vertical flowchart for one boss turn."""

    STEPS = [
        ("1", "Reset turn caches", "boss_platform.asm", "Clear per-turn scratch state."),
        ("2", "Select coach plan", "boss_platform.asm + coach_plan_templates", "Pick fight phase from a per-trainer template."),
        ("3", "Compute plausible-type mask", "boss_policy_move.asm", "Infer what types your active mon can hit, from public info only."),
        ("4", "Oracle Haki read", "boss_platform.asm + haki_taunt_queue", "If this is the eligible ace turn, peek your committed move or switch - ONCE per battle."),
        ("5", "Switch decision", "boss_policy_switch.asm", "Bench scan for immune pivots, respect cooldown, weigh your revenge threat."),
        ("6", "Move scoring + lookahead", "boss_policy_move.asm + ko_band_oracle + scoring.asm", "Vanilla score, then KO bands, type-passive math, repeat-softener, 1-2 turn beam."),
        ("7", "Item check", "items.asm", "If no move scored well, consider Hyper Potion / Full Restore / X-item."),
        ("8", "Append observation", "observation_log.asm", "Record what YOU just did - class, damage band, speed relation."),
    ]

    def __init__(self, width=6.8 * inch):
        super().__init__()
        self.width = width
        self.box_h = 0.62 * inch
        self.gap = 0.10 * inch
        self.height = len(self.STEPS) * self.box_h + (len(self.STEPS) - 1) * self.gap + 0.05 * inch

    def wrap(self, available_width, available_height):  # noqa: ARG002
        return self.width, self.height

    def draw(self):
        c = self.canv
        for i, (num, title, owner, body) in enumerate(self.STEPS):
            y = self.height - (i + 1) * self.box_h - i * self.gap
            self._draw_box(c, 0, y, self.width, self.box_h, num, title, owner, body)
            if i < len(self.STEPS) - 1:
                arrow_top = y - 2
                arrow_bot = y - self.gap + 2
                cx = 0.4 * inch
                c.setStrokeColor(ACCENT)
                c.setLineWidth(1.6)
                c.line(cx, arrow_top, cx, arrow_bot)
                c.setFillColor(ACCENT)
                path = c.beginPath()
                path.moveTo(cx - 4, arrow_bot + 1)
                path.lineTo(cx + 4, arrow_bot + 1)
                path.lineTo(cx, arrow_bot - 5)
                path.close()
                c.drawPath(path, stroke=0, fill=1)

    def _draw_box(self, c, x, y, w, h, num, title, owner, body):
        badge_w = 0.55 * inch
        c.setFillColor(ACCENT)
        c.setStrokeColor(ACCENT)
        c.setLineWidth(0)
        c.roundRect(x, y, badge_w, h, 5, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(x + badge_w / 2, y + h / 2 - 6, num)

        main_x = x + badge_w + 6
        main_w = w - badge_w - 6
        c.setFillColor(colors.white)
        c.setStrokeColor(ACCENT_SOFT)
        c.setLineWidth(0.8)
        c.roundRect(main_x, y, main_w, h, 5, stroke=1, fill=1)

        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(main_x + 10, y + h - 16, title)

        c.setFillColor(ACCENT)
        c.setFont("Courier", 8.5)
        c.drawRightString(main_x + main_w - 10, y + h - 16, owner)

        c.setFillColor(INK_SOFT)
        c.setFont("Helvetica", 9)
        c.drawString(main_x + 10, y + 8, body[:140])


class WRAMReserveBar(Flowable):
    """Horizontal stacked bar showing WRAMX bank 1 reserve."""

    def __init__(self, width=6.8 * inch):
        super().__init__()
        self.width = width
        self.height = 1.6 * inch

    def wrap(self, available_width, available_height):  # noqa: ARG002
        return self.width, self.height

    def draw(self):
        c = self.canv
        w = self.width
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(0, self.height - 14, "WRAMX Bank 1 reserve - 140 bytes total")

        bar_y = self.height - 50
        bar_h = 28

        used_frac = 112 / 140
        c.setFillColor(ACCENT)
        c.setStrokeColor(ACCENT)
        c.rect(0, bar_y, w * used_frac, bar_h, stroke=0, fill=1)
        c.setFillColor(GOOD_SOFT)
        c.setStrokeColor(GOOD)
        c.rect(w * used_frac, bar_y, w * (1 - used_frac), bar_h, stroke=1, fill=1)

        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(8, bar_y + 9, "112 B used (normal build)")
        c.setFillColor(GOOD)
        c.drawRightString(w - 8, bar_y + 9, "28 B free")

        c.setFillColor(INK_SOFT)
        c.setFont("Helvetica-Oblique", 8.5)
        c.drawString(0, bar_y - 12, "normal build")

        bar2_y = bar_y - 40
        c.setFillColor(WARN)
        c.setStrokeColor(WARN)
        c.rect(0, bar2_y, w, bar_h, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(8, bar2_y + 9, "140 B used (trace build) - 0 B free")
        c.setFillColor(INK_SOFT)
        c.setFont("Helvetica-Oblique", 8.5)
        c.drawString(0, bar2_y - 12, "trace build (offline debug only)")


class LayerColumns(Flowable):
    """Two side-by-side cards: PLATFORM | POLICY."""

    def __init__(self, width=6.8 * inch):
        super().__init__()
        self.width = width
        self.height = 3.0 * inch

    def wrap(self, available_width, available_height):  # noqa: ARG002
        return self.width, self.height

    def draw(self):
        c = self.canv
        w = self.width
        col_w = (w - 16) / 2

        c.setFillColor(GOOD_SOFT)
        c.setStrokeColor(GOOD)
        c.setLineWidth(1)
        c.roundRect(0, 0, col_w, self.height, 8, stroke=1, fill=1)
        c.setFillColor(GOOD)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(14, self.height - 24, "PLATFORM")
        c.setFillColor(INK_SOFT)
        c.setFont("Helvetica-Oblique", 9.5)
        c.drawString(14, self.height - 38, "Plumbing. No taste calls.")
        c.setFillColor(INK)
        c.setFont("Helvetica", 9.5)
        items = [
            "Turn counter, switch counter",
            "Seen-species + alive bitmaps",
            "State reset on battle start/end",
            "Bank-switch helpers",
            "Cooldown decay",
            "Haki state machine bits",
        ]
        for i, item in enumerate(items):
            c.drawString(20, self.height - 60 - i * 18, "*  " + item)
        c.setFillColor(INK_SOFT)
        c.setFont("Helvetica-Oblique", 8.5)
        c.drawString(14, 18, "boss_platform.asm  *  observation_log.asm")
        c.drawString(14, 6, "haki_taunt_queue.asm  *  boss_thunks.asm")

        px = col_w + 16
        c.setFillColor(ACCENT_SOFT)
        c.setStrokeColor(ACCENT)
        c.setLineWidth(1)
        c.roundRect(px, 0, col_w, self.height, 8, stroke=1, fill=1)
        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(px + 14, self.height - 24, "POLICY")
        c.setFillColor(INK_SOFT)
        c.setFont("Helvetica-Oblique", 9.5)
        c.drawString(px + 14, self.height - 38, "Taste calls. Change here when you want a fight to feel different.")
        c.setFillColor(INK)
        c.setFont("Helvetica", 9.5)
        items = [
            "Move scoring adjustments",
            "Lookahead beam (1-2 turns)",
            "KO band oracle",
            "Type-passive damage estimate",
            "Switch decision tree",
            "Item usage policy",
        ]
        for i, item in enumerate(items):
            c.drawString(px + 20, self.height - 60 - i * 18, "*  " + item)
        c.setFillColor(INK_SOFT)
        c.setFont("Helvetica-Oblique", 8.5)
        c.drawString(px + 14, 18, "boss_policy_move.asm  *  boss_policy_switch.asm")
        c.drawString(px + 14, 6, "ko_band_oracle.asm  *  scoring/move/switch/items.asm")
