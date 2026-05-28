#!/usr/bin/env python3
"""Generate docs/boss_ai_architecture.pdf — a visual tour of the boss-AI overlay.

Output: docs/boss_ai_architecture.pdf
Run: python scripts/generate_boss_ai_architecture_pdf.py

Custom drawn Flowables (StackedDiagram, TurnFlowchart, WRAMReserveBar,
LayerColumns, HRule) and the palette live in
scripts/_boss_ai_pdf_flowables.py so this file stays under the
project's 700-line hand-written threshold.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from _boss_ai_pdf_flowables import (
    ACCENT,
    ACCENT_SOFT,
    GOOD,
    HAIRLINE,
    INK,
    INK_SOFT,
    NEUTRAL_BG,
    WARN,
    WARN_SOFT,
    HRule,
    LayerColumns,
    StackedDiagram,
    TurnFlowchart,
    WRAMReserveBar,
)


DOC_TITLE = "Boss AI Architecture"
DOC_SUBTITLE = "A tour of the overlay code"

PAGE_W, PAGE_H = LETTER
MARGIN = 0.6 * inch


def _make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "cover_title", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=42, leading=46, textColor=INK, alignment=TA_LEFT, spaceAfter=8,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle", parent=base["Title"], fontName="Helvetica",
            fontSize=18, leading=22, textColor=ACCENT, alignment=TA_LEFT, spaceAfter=18,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"], fontName="Helvetica-Bold",
            fontSize=22, leading=26, textColor=INK, spaceBefore=0, spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], fontName="Helvetica-Bold",
            fontSize=14, leading=18, textColor=ACCENT, spaceBefore=14, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body", parent=base["BodyText"], fontName="Helvetica",
            fontSize=10.5, leading=15, textColor=INK, spaceAfter=8,
        ),
        "body_small": ParagraphStyle(
            "body_small", parent=base["BodyText"], fontName="Helvetica",
            fontSize=9, leading=12, textColor=INK_SOFT, spaceAfter=6,
        ),
        "callout": ParagraphStyle(
            "callout", parent=base["BodyText"], fontName="Helvetica",
            fontSize=10, leading=14, textColor=INK, spaceAfter=6,
        ),
        "caption": ParagraphStyle(
            "caption", parent=base["BodyText"], fontName="Helvetica-Oblique",
            fontSize=9, leading=12, textColor=INK_SOFT, spaceBefore=4, spaceAfter=10,
        ),
    }


STYLES = _make_styles()


def _on_page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(HAIRLINE)
    canvas.setLineWidth(0.4)
    canvas.line(MARGIN, MARGIN - 0.18 * inch, PAGE_W - MARGIN, MARGIN - 0.18 * inch)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(INK_SOFT)
    canvas.drawString(MARGIN, MARGIN - 0.32 * inch, "Boss AI Architecture - pokegold hack")
    canvas.drawRightString(PAGE_W - MARGIN, MARGIN - 0.32 * inch, f"page {doc.page}")
    canvas.restoreState()


def _on_cover(canvas, doc):  # noqa: ARG001
    canvas.saveState()
    canvas.setFillColor(ACCENT)
    canvas.rect(0, PAGE_H - 1.4 * inch, PAGE_W, 1.4 * inch, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(MARGIN, PAGE_H - 0.5 * inch, "pokegold hack")
    canvas.setFont("Helvetica", 11)
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 0.5 * inch, "2026-05-26")

    canvas.setFillColor(INK)
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(2)
    canvas.line(MARGIN, 1.2 * inch, MARGIN + 1.6 * inch, 1.2 * inch)
    canvas.setFont("Helvetica-Oblique", 9)
    canvas.setFillColor(INK_SOFT)
    canvas.drawString(MARGIN, 0.95 * inch, "Built for Cole - Claude Opus 4.7 + Codex")
    canvas.restoreState()


def _file_table() -> Table:
    rows = [
        ["File", "Layer", "What it does"],
        ["boss_platform.asm", "PLATFORM", "Turn counter, switch counter, alive/seen bitmaps, cooldown decay, plan picker."],
        ["boss_policy_move.asm", "POLICY", "The big one. Move scoring, lookahead, KO-band pressure, repeat-softener, item math."],
        ["boss_policy_switch.asm", "POLICY", "Switch decision tree: bench scan, type-immune pivot, revenge respect, cooldown gate."],
        ["observation_log.asm", "PLATFORM", "Rolling log of your last 3-6 actions in WRAMX bank 2. Read by policy code."],
        ["ko_band_oracle.asm", "POLICY", "Reads precomputed per-leader matchup tables. Answers KO-in-N questions cheaply."],
        ["haki_taunt_queue.asm", "PLATFORM", "Picks the per-leader taunt line for the one Haki fire per battle."],
        ["boss_thunks.asm", "PLUMBING", "ROM0 trampolines so bank 0e can reach bank 0b scoring helpers."],
        ["boss_trace_topmoves.asm", "TRACE", "Trace-build only. Logs top-4 scored moves with components."],
        ["scoring.asm / move.asm /", "VANILLA", "The base Gen 2 AI. Boss code calls into these for the starting score."],
        ["switch.asm / items.asm / redundant.asm", "VANILLA", "Same. Boss adjusts on top; it does not replace them."],
    ]
    tbl = Table(rows, colWidths=[2.1 * inch, 0.9 * inch, 3.8 * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTNAME", (0, 1), (0, -1), "Courier-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (1, 1), (1, -1), 8),
        ("FONTNAME", (2, 1), (2, -1), "Helvetica"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, NEUTRAL_BG]),
        ("GRID", (0, 0), (-1, -1), 0.4, HAIRLINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return tbl


def _data_table() -> Table:
    rows = [
        ["Data file (data/boss_ai/)", "What it is", "How boss AI uses it"],
        ["matchup_tables.asm", "Generated; per-leader-per-slot 17-byte defensive + 17-byte offensive vectors.", "The boss's 'Smogon page' for its own team - KO-band oracle reads it."],
        ["role_package_classifier.asm", "Generated; 1 byte per species, bits = phazer / sweeper / wall / status / wallbreaker / spinner / priority.", "Tags what each player species is for, biases prediction."],
        ["revealed_effect_matrix.asm", "Move ID -> effect class bits.", "When you reveal a move, widens 'what else might this mon have' inference."],
        ["tendency_counter_weights.asm", "Per-observation-class additive points for switch prediction.", "How strongly each recent player behavior shifts the switch-prediction model."],
        ["coach_plan_templates.asm", "Per-trainer fight plans (lead / sack / save lines).", "Picks a fight phase the AI tries to follow, with allowed deviation."],
        ["haki_taunts.asm", "Per-leader taunt line for the Haki fire.", "Printed before the move animation when Haki triggers."],
    ]
    tbl = Table(rows, colWidths=[2.1 * inch, 2.4 * inch, 2.3 * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GOOD),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTNAME", (0, 1), (0, -1), "Courier-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("FONTNAME", (1, 1), (-1, -1), "Helvetica"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, NEUTRAL_BG]),
        ("GRID", (0, 0), (-1, -1), 0.4, HAIRLINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return tbl


def _haki_callout() -> Table:
    rules = [
        "<b>One fire per battle.</b> Cleared by <font face='Courier'>ClearBossAIState</font> at battle start.",
        "<b>Eligibility gate.</b> Mid-tier and later trainers (Falkner / Bugsy / Whitney never get it). Post-champion Kanto leaders also excluded.",
        "<b>Trigger.</b> First turn the leader's ace mon is due to act with the player having committed (locked move OR revealed switch).",
        "<b>The fire.</b> Boss re-runs normal scoring with your committed action as input, picks the best of the ace's existing 4 moves. No bespoke move.",
        "<b>Defensive pivot variant.</b> If a bench mon is type-immune to your locked move type and the active isn't, boss switches instead.",
        "<b>Player-visible signal.</b> One leader-specific taunt line prints before the move animation. No auras, no status, no impossible visuals.",
    ]
    bullet_paragraphs = [Paragraph("- " + r, STYLES["callout"]) for r in rules]
    content = [
        [Paragraph("<b>Haki - the one carve-out</b>", STYLES["h2"])],
        [Paragraph(
            "Boss AI is public-information-only <i>except</i> for this one authored exception. The design discipline is keeping it quarantined - the rest of the system stays legal so the player can learn the rulebook.",
            STYLES["body"],
        )],
    ] + [[p] for p in bullet_paragraphs]

    tbl = Table(content, colWidths=[6.8 * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WARN_SOFT),
        ("BOX", (0, 0), (-1, -1), 1.2, WARN),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tbl


def _cover_page(story: list) -> None:
    story.append(Spacer(1, 2.4 * inch))
    story.append(Paragraph(DOC_TITLE, STYLES["cover_title"]))
    story.append(Paragraph(DOC_SUBTITLE, STYLES["cover_subtitle"]))
    story.append(Paragraph(
        "How the overlay sits on top of the vanilla Gen 2 trainer AI, what each file does, "
        "how a single boss turn flows, where the state lives, and where the one carve-out "
        "for unfair information sits.",
        STYLES["body"],
    ))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Contents", STYLES["h2"]))
    for line in [
        "1. The big picture - overlay vs vanilla",
        "2. Platform vs Policy - the two layers",
        "3. One boss turn - flow chart",
        "4. ASM file catalog",
        "5. Data table catalog",
        "6. Memory picture - WRAMX bank 1",
        "7. Haki - the one carve-out",
    ]:
        story.append(Paragraph(line, STYLES["body_small"]))


def _section_pages(story: list) -> None:
    # Section 1: big picture
    story.append(PageBreak())
    story.append(Paragraph("1. The big picture", STYLES["h1"]))
    story.append(Paragraph(
        "Vanilla Gen 2 trainer AI is a score-each-move system: every move starts at 20, a fixed "
        "list of rules nudges scores up or down, and the highest-scored move is picked with some "
        "randomness. Switching is rare and crude.",
        STYLES["body"],
    ))
    story.append(Paragraph(
        "The <b>boss AI</b> is an overlay that runs only for major fights - gym leaders, rival, "
        "Elite Four, champion. It does three things vanilla AI doesn't.",
        STYLES["body"],
    ))
    story.append(Spacer(1, 0.1 * inch))
    story.append(StackedDiagram())
    story.append(Spacer(1, 0.05 * inch))
    story.append(Paragraph(
        "Vanilla AI is the base score. The overlay adjusts on top - it doesn't replace anything. "
        "That's why every fight still feels like a Pokemon battle and not a different game.",
        STYLES["caption"],
    ))

    # Section 2: two layers
    story.append(PageBreak())
    story.append(Paragraph("2. Two layers - Platform vs Policy", STYLES["h1"]))
    story.append(Paragraph(
        "Every boss-AI file is tagged either <b>PLATFORM</b> or <b>POLICY</b>. The distinction "
        "matters because changing Platform code is risky but rarely changes feel; changing Policy "
        "code is the opposite - low blast radius, directly changes how a fight feels. When you "
        "say <i>'make Karen play differently'</i>, the changes happen in Policy.",
        STYLES["body"],
    ))
    story.append(Spacer(1, 0.1 * inch))
    story.append(LayerColumns())
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "Rule of thumb: if the change would alter <i>what</i> the boss decides, it's Policy. If "
        "the change is about <i>how</i> the boss remembers or tracks something, it's Platform.",
        STYLES["caption"],
    ))

    # Section 3: turn flowchart
    story.append(PageBreak())
    story.append(Paragraph("3. One boss turn - flow chart", STYLES["h1"]))
    story.append(Paragraph(
        "When the engine asks the boss for its next action, the code runs through these eight "
        "steps in order. Steps 1-4 are setup. Step 5 may end the turn early (boss switches). "
        "Steps 6-7 pick the move or item. Step 8 happens after your action lands and feeds the "
        "next turn's prediction.",
        STYLES["body"],
    ))
    story.append(Spacer(1, 0.1 * inch))
    story.append(TurnFlowchart())

    # Section 4: file catalog
    story.append(PageBreak())
    story.append(Paragraph("4. ASM file catalog", STYLES["h1"]))
    story.append(Paragraph(
        "Every assembly file under <font face='Courier'>engine/battle/ai/</font>, grouped by layer.",
        STYLES["body"],
    ))
    story.append(Spacer(1, 0.05 * inch))
    story.append(_file_table())

    # Section 5: data catalog
    story.append(PageBreak())
    story.append(Paragraph("5. Data table catalog", STYLES["h1"]))
    story.append(Paragraph(
        "ROM-resident lookup tables under <font face='Courier'>data/boss_ai/</font>. These are "
        "computed at build time so runtime cost is just a table lookup.",
        STYLES["body"],
    ))
    story.append(Spacer(1, 0.05 * inch))
    story.append(_data_table())

    # Section 6: memory
    story.append(PageBreak())
    story.append(Paragraph("6. Memory picture", STYLES["h1"]))
    story.append(Paragraph(
        "Boss AI state lives in <b>WRAMX bank 1</b>. The total reserve is fixed at 140 bytes. "
        "Trace builds (used only for the offline debugger) consume the full 140; the shipping ROM "
        "uses 112, leaving 28 bytes of room for new state.",
        STYLES["body"],
    ))
    story.append(Spacer(1, 0.1 * inch))
    story.append(WRAMReserveBar())
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "<b>Why this matters:</b> WRAM0 and HRAM savings (like the PR we just merged) don't help "
        "this region - bank 1 is a different physical memory pool. To free bytes here we'd need "
        "to fold caches, drop the repeat-tracking softener, or relocate the trace block to bank 2.",
        STYLES["body"],
    ))
    story.append(Spacer(1, 0.05 * inch))
    story.append(HRule())
    story.append(Paragraph(
        "Outside bank 1: the <b>observation log</b> lives in WRAMX bank 2 (deliberately, to keep "
        "bank 1 tight). Bank <b>0e</b> is the ROM bank where most boss-AI code lives, and it's "
        "almost full - that's why some helpers route through ROM0 trampolines "
        "(<font face='Courier'>boss_thunks.asm</font>).",
        STYLES["body"],
    ))

    # Section 7: Haki
    story.append(PageBreak())
    story.append(Paragraph("7. Haki - the one carve-out", STYLES["h1"]))
    story.append(Paragraph(
        "Boss AI is public-information-only with exactly one exception: Haki. It exists so the "
        "fights have a dramatic moment - a beat where the boss reveals they were a level above "
        "the whole time. Without an authored exception, the AI would be technically correct but "
        "feel flat at the leader's signature moment.",
        STYLES["body"],
    ))
    story.append(Spacer(1, 0.1 * inch))
    story.append(_haki_callout())
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "<b>Per-leader feel</b> lives in (a) the trainer party + ace moveset, (b) the leader-specific "
        "taunt text - <i>not</i> in bespoke Haki logic. Lance's Hyper Beam pivot, Karen's Pursuit "
        "punish, Morty's Destiny Bond moment: all emerge from the ace having the right 4 moves "
        "and Haki letting normal scoring pick the right one against your committed action.",
        STYLES["body"],
    ))


def build(output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = BaseDocTemplate(
        str(output_path), pagesize=LETTER,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title=DOC_TITLE, author="Claude Opus 4.7 + Codex",
    )
    frame_full = Frame(
        MARGIN, MARGIN, PAGE_W - 2 * MARGIN, PAGE_H - 2 * MARGIN,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, showBoundary=0,
    )
    frame_cover = Frame(
        MARGIN, MARGIN, PAGE_W - 2 * MARGIN, PAGE_H - 2 * MARGIN - 0.4 * inch,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, showBoundary=0,
    )
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[frame_cover], onPage=_on_cover),
        PageTemplate(id="body", frames=[frame_full], onPage=_on_page),
    ])

    story: list = []
    _cover_page(story)
    _section_pages(story)
    doc.build(story)
    return output_path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    out = repo_root / "docs" / "boss_ai_architecture.pdf"
    written = build(out)
    print(f"wrote {written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
