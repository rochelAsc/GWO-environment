"""Apply v5 content/exposition map onto defesa deck v4 HTML."""
from __future__ import annotations

import html as html_lib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _defesa_deck_v5_content_map import SLIDES  # noqa: E402

SRC = Path(r"C:\Users\roche\Downloads\defesa_metodologica_gwo_pfsp_v4.html")
DST = Path(r"C:\Users\roche\Downloads\defesa_metodologica_gwo_pfsp_v5.html")

SECTION_RE = re.compile(r"<section class=\"page.*?</section>", re.S)
NOTES_RE = re.compile(r'data-speaker-notes="([^"]*)"')
LEAD_RE = re.compile(r'(<p class="lead">)(.*?)(</p>)', re.S)
CALLOUT_RE = re.compile(
    r'<p class="callout(?! warn)[^"]*">.*?</p>',
    re.S,
)
FOOTER_RE = re.compile(r'<div class="footer">')


def esc_attr(text: str) -> str:
    return (
        html_lib.escape(text, quote=True)
        .replace("&#x27;", "'")  # keep apostrophes readable in notes
    )


def set_notes(section: str, notes: str) -> str:
    return NOTES_RE.sub(
        lambda m: f'data-speaker-notes="{esc_attr(notes)}"',
        section,
        count=1,
    )


def set_lead(section: str, lead: str) -> str:
    lead_html = html_lib.escape(lead)
    if LEAD_RE.search(section):
        return LEAD_RE.sub(rf"\1{lead_html}\3", section, count=1)
    # insert after h1 / meta block
    return re.sub(
        r"(</h1>(?:\s*<div class=\"meta\">.*?</div>)?)",
        rf'\1<p class="lead">{lead_html}</p>',
        section,
        count=1,
        flags=re.S,
    )


def set_takeaway(section: str, takeaway: str, replace: bool) -> str:
    callout = f'<p class="callout">{html_lib.escape(takeaway)}</p>'
    if replace and CALLOUT_RE.search(section):
        return CALLOUT_RE.sub(callout, section, count=1)
    if takeaway in section:
        return section
    # Prefer before footer; avoid duplicating if an identical callout exists
    if CALLOUT_RE.search(section) and not replace:
        # Keep existing factual callouts; append takeaway only if distinct
        existing = CALLOUT_RE.findall(section)
        for block in existing:
            if takeaway in block:
                return section
        return FOOTER_RE.sub(callout + '<div class="footer">', section, count=1)
    return FOOTER_RE.sub(callout + '<div class="footer">', section, count=1)


def mark_backup_kicker(section: str, index: int) -> str:
    if index < 50:
        return section
    return re.sub(
        r'(<div class="kicker">)([^<]*)(</div>)',
        r"\1Backup Q&A · \2\3",
        section,
        count=1,
    )


def patch_title(html: str) -> str:
    html = html.replace(
        "<title>Defesa metodológica — GWO e PFSP (v4)</title>",
        "<title>Defesa metodológica — GWO e PFSP (v5)</title>",
        1,
    )
    # TOC backup label hint in script ACTS stays; add note in help line
    html = html.replace(
        "Atalhos: ←/→ ou espaço · Home/End · I índice · N notas · F tela cheia · P imprimir · Esc fechar.",
        "Atalhos: ←/→ ou espaço · Home/End · I índice · N notas · F tela cheia · P imprimir · Esc fechar. "
        "Slides 50–54 são backup Q&A.",
        1,
    )
    return html


def transform_section(section: str, index: int) -> str:
    cfg = SLIDES.get(index)
    if not cfg:
        raise SystemExit(f"missing content map for slide {index}")
    notes = cfg.get("notes")
    if not isinstance(notes, str) or not notes.strip():
        raise SystemExit(f"slide {index} missing notes")
    section = set_notes(section, notes)
    lead = cfg.get("lead")
    if isinstance(lead, str) and lead.strip():
        section = set_lead(section, lead)
    takeaway = cfg.get("takeaway")
    if isinstance(takeaway, str) and takeaway.strip():
        section = set_takeaway(
            section,
            takeaway,
            bool(cfg.get("replace_callout")),
        )
    section = mark_backup_kicker(section, index)
    return section


def main() -> None:
    raw = SRC.read_text(encoding="utf-8")
    sections = SECTION_RE.findall(raw)
    if len(sections) != 54:
        raise SystemExit(f"expected 54 sections, found {len(sections)}")
    if set(SLIDES) != set(range(1, 55)):
        missing = set(range(1, 55)) - set(SLIDES)
        raise SystemExit(f"content map incomplete: {sorted(missing)}")

    new_sections = [transform_section(sec, i + 1) for i, sec in enumerate(sections)]
    start = raw.index(sections[0])
    end = raw.index(sections[-1]) + len(sections[-1])
    out = raw[:start] + "\n".join(new_sections) + raw[end:]
    out = patch_title(out)
    DST.write_text(out, encoding="utf-8")
    print(f"wrote {DST} ({DST.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
