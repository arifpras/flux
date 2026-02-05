from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Flowable,
)

BASE = Path("/Users/arifpras/Library/CloudStorage/Dropbox/perisai/stockscraper")
SRC = BASE / "results" / "20260130_FOREIGN_BROKER_ANALYSIS.txt"
OUT = BASE / "results" / "20260130_FOREIGN_BROKER_REPORT.pdf"


def parse_sections(text: str):
    lines = [l.rstrip() for l in text.splitlines()]
    return lines


def build_report(lines):
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    subtitle_style = styles["BodyText"]
    h2_style = styles["Heading2"]
    body_style = styles["BodyText"]

    story = []
    story.append(Paragraph("Foreign Broker Activity Report", title_style))
    story.append(Paragraph("Period: January 30, 2026 • Source: Stockbit + Broker Summary", subtitle_style))
    story.append(Spacer(1, 12))

    # Executive summary box
    summary_lines = []
    for line in lines:
        if line.strip().startswith("KEY OBSERVATIONS"):
            break
        if line.strip().startswith("1.") or line.strip().startswith("2."):
            summary_lines.append(line.strip())
    if summary_lines:
        story.append(Paragraph("Executive Summary", h2_style))
        for s in summary_lines[:3]:
            story.append(Paragraph(f"• {s[3:]}", body_style))
        story.append(Spacer(1, 12))

    # Extract key table from the latest summary file
    report_table = None
    in_table = False
    table_rows = []
    for line in lines:
        if line.strip().startswith("Stock") and "Price" in line:
            in_table = True
            continue
        if in_table:
            if not line.strip():
                break
            if line.strip().startswith("-"):
                continue
            parts = line.split()
            if len(parts) >= 5:
                table_rows.append(parts[:5])

    if table_rows:
        story.append(Paragraph("Most Bought Stocks (>=5 Brokers)", h2_style))
        data = [["Stock", "# Brokers", "Price Min", "Price Max", "Price Avg"]] + table_rows
        table = Table(data, colWidths=[60, 70, 70, 70, 70], hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 10))

    # Add narrative sections with better hierarchy
    section = []
    for line in lines:
        if line.strip().startswith("="):
            continue
        if line.strip().endswith(":"):
            if section:
                story.append(Paragraph("<br/>".join(section), body_style))
                story.append(Spacer(1, 8))
                section = []
            story.append(Paragraph(line.strip().rstrip("."), h2_style))
            continue
        if line.strip().startswith("-"):
            section.append(f"• {line.strip()[1:].strip()}")
            continue
        if line.strip().startswith("1)") or line.strip().startswith("2)"):
            section.append(f"• {line.strip()}")
            continue
        if line.strip():
            section.append(line)

    if section:
        story.append(Paragraph("<br/>".join(section), body_style))

    return story


def main():
    if not SRC.exists():
        raise FileNotFoundError(f"Source analysis not found: {SRC}")

    lines = parse_sections(SRC.read_text(encoding="utf-8"))
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
        title="Foreign Broker Activity Report",
        author="Stockscraper",
    )
    story = build_report(lines)
    doc.build(story)


if __name__ == "__main__":
    main()
