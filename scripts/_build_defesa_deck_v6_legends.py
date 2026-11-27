"""Inject formula/acronym legends into defesa deck v5 → v6."""
from __future__ import annotations

import html as html_lib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _defesa_deck_v6_legends_map import LEGEND_CSS, LEGENDS  # noqa: E402

SRC = Path(r"C:\Users\roche\Downloads\defesa_metodologica_gwo_pfsp_v5.html")
DST = Path(r"C:\Users\roche\Downloads\defesa_metodologica_gwo_pfsp_v6.html")

SECTION_RE = re.compile(r"<section class=\"page.*?</section>", re.S)
NOTES_RE = re.compile(r'(data-speaker-notes=")([^"]*)(")')
# Main deck stylesheet ends at first </style></head> boundary — inject before that
MAIN_STYLE_END = re.compile(r"</style>\s*</head>", re.S)


def render_legend(items: list[tuple[str, str]], compact: bool) -> str:
    cls = "legend compact" if compact else "legend"
    lis = [
        f'<li><span class="sym">{sym}</span>{meaning}</li>'
        for sym, meaning in items
    ]
    return (
        f'<aside class="{cls}"><b>Legenda</b><ul>'
        + "".join(lis)
        + "</ul></aside>"
    )


def insert_before_footer(section: str, block: str) -> str:
    # Prefer after the last callout, still before footer
    footer = section.rfind('<div class="footer">')
    if footer < 0:
        raise SystemExit("footer missing in section")
    return section[:footer] + block + section[footer:]


def insert_after_anchor(section: str, kind: str, html: str) -> str:
    patterns = {
        "equation_small": r'(<div class="equation small">.*?</div>)',
        "mathgrid": r'(<div class="mathgrid">.*?</div>\s*(?:<div class="equation">.*?</div>)?)',
        "first_table": r"(<table>.*?</table>)",
        "table_pair": r'(<div class="table-pair">.*?</div>)',
        "chart": r"(</figure>)",
        "split": r'(<div class="split">.*?</div>)',
    }
    pat = patterns.get(kind)
    if not pat:
        raise SystemExit(f"unknown anchor {kind}")
    m = re.search(pat, section, flags=re.S)
    if not m:
        # fallback: before footer
        return insert_before_footer(section, html)
    return section[: m.end()] + html + section[m.end() :]


def append_note(section: str, text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        notes = m.group(2)
        if text.strip() in notes:
            return m.group(0)
        # escape for attribute
        added = html_lib.escape(text, quote=True).replace("&#x27;", "'")
        return f"{m.group(1)}{notes}{added}{m.group(3)}"

    return NOTES_RE.sub(repl, section, count=1)


def transform_section(section: str, index: int) -> str:
    cfg = LEGENDS.get(index)
    if not cfg:
        return section
    if cfg.get("extra_html") and cfg.get("extra_after"):
        section = insert_after_anchor(
            section, cfg["extra_after"], cfg["extra_html"]
        )
    legend_html = render_legend(
        cfg["legend"], bool(cfg.get("compact"))
    )
    section = insert_before_footer(section, legend_html)
    if cfg.get("note_append"):
        section = append_note(section, str(cfg["note_append"]))
    return section


def inject_css(html: str) -> str:
    if ".legend{" in html:
        return html
    m = MAIN_STYLE_END.search(html)
    if not m:
        raise SystemExit("main </style></head> not found")
    return html[: m.start()] + LEGEND_CSS + "\n" + html[m.start() :]


def patch_title(html: str) -> str:
    return html.replace(
        "<title>Defesa metodológica — GWO e PFSP (v5)</title>",
        "<title>Defesa metodológica — GWO e PFSP (v6)</title>",
        1,
    )


def main() -> None:
    raw = SRC.read_text(encoding="utf-8")
    raw = inject_css(raw)
    sections = SECTION_RE.findall(raw)
    if len(sections) != 54:
        raise SystemExit(f"expected 54 sections, found {len(sections)}")
    new_sections = [
        transform_section(sec, i + 1) for i, sec in enumerate(sections)
    ]
    start = raw.index(sections[0])
    end = raw.index(sections[-1]) + len(sections[-1])
    out = patch_title(raw[:start] + "\n".join(new_sections) + raw[end:])
    DST.write_text(out, encoding="utf-8")
    print(f"wrote {DST} ({DST.stat().st_size} bytes)")
    print(f"slides with legends: {sorted(LEGENDS)}")


if __name__ == "__main__":
    main()
