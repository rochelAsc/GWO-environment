"""Build defesa_metodologica_gwo_pfsp_v4.html from v3 (layout only)."""
from __future__ import annotations

import re
from pathlib import Path

SRC = Path(r"C:\Users\roche\Downloads\defesa_metodologica_gwo_pfsp_v3.html")
DST = Path(r"C:\Users\roche\Downloads\defesa_metodologica_gwo_pfsp_v4.html")

# Brand palette for Matplotlib series (Baseline, Optuna, Surrogate, Fuzzy / order of appearance)
MPL_MAP = {
    "#1f77b4": "#0A7A72",  # accent teal
    "#ff7f0e": "#C45C26",  # warm secondary
    "#2ca02c": "#2F6B4F",  # green
    "#d62728": "#B33A2B",  # warn red
    "#ffffff": "#F4F7F8",
    "#FFFFFF": "#F4F7F8",
}

ACTS = [
    (1, 30, "Núcleo", "estudo principal"),
    (31, 46, "Extensão", "surrogate e meta-learning"),
    (47, 54, "Fecho", "ameaças, conclusões e apêndice"),
]


def act_for(index: int) -> tuple[str, str]:
    for start, end, name, sub in ACTS:
        if start <= index <= end:
            return name, sub
    return "Núcleo", "estudo principal"


CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,600;8..60,700&display=swap');
:root{
  --ink:#0B1F33;--muted:#5A717F;--accent:#0A7A72;--accent-soft:#D7EDEB;
  --warn:#B33A2B;--warn-soft:#F6E6E3;--paper:#F4F7F8;--panel:transparent;
  --line:#C9D5DC;--stage:#07131C;--chrome:#101E29;--chrome-btn:#1C3443;
  --serif:'Source Serif 4',Georgia,'Times New Roman',serif;
  --sans:'IBM Plex Sans',system-ui,sans-serif;
  --mono:'IBM Plex Mono',ui-monospace,monospace;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:var(--stage);color:var(--ink);font-family:var(--sans)}
body{min-height:100vh}
.page{
  display:none;position:relative;overflow:hidden;
  width:min(100vw, calc(100vh * 16 / 9));
  height:min(100vh, calc(100vw * 9 / 16));
  aspect-ratio:16/9;margin:0 auto;
  padding:clamp(28px,4.2vw,52px) clamp(28px,5vw,68px) 64px;
  background:
    radial-gradient(1200px 420px at 100% -10%, #0a7a7214, transparent 55%),
    linear-gradient(180deg, #f7fafb 0%, var(--paper) 100%);
  box-shadow:0 18px 50px #0006;
  opacity:0;transform:translateY(6px);
}
.page.active{display:block;opacity:1;transform:none;animation:pageIn .16s ease-out}
@keyframes pageIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){
  .page,.page.active{animation:none;transform:none;opacity:1}
}
.top{
  position:absolute;left:0;top:0;right:0;height:36px;
  display:flex;align-items:center;justify-content:space-between;
  padding:0 clamp(28px,5vw,68px);
  background:linear-gradient(90deg, var(--accent) 0%, #0d5f5a 55%, #16384a 100%);
  color:#e8f6f5;font-size:11px;letter-spacing:1.4px;text-transform:uppercase;font-weight:600;
}
.top .act{opacity:.95}.top .act-sub{opacity:.72;font-weight:500;margin-left:10px;letter-spacing:.8px}
.kicker{
  font-size:13px;letter-spacing:1.8px;text-transform:uppercase;color:var(--accent);
  font-weight:700;margin:18px 0 14px;
}
h1{
  font-family:var(--serif);font-size:clamp(26px,3.2vw,42px);line-height:1.08;
  color:var(--ink);margin:0 0 clamp(12px,1.8vw,22px);max-width:1100px;font-weight:700;
}
h2{font-family:var(--serif);font-size:22px;color:var(--ink);margin:0 0 10px}
h3{font-size:16px;color:var(--ink);margin:0 0 8px;font-weight:700;letter-spacing:.2px}
p,li{font-size:clamp(13px,1.4vw,18px);line-height:1.38;color:#2C4454}
p{margin:8px 0}ul{margin:8px 0;padding-left:22px}li{margin:7px 0}
.lead{font-size:clamp(16px,1.7vw,22px);line-height:1.32;color:#243F50;margin-top:18px;max-width:980px}
.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:clamp(10px,1.4vw,18px);margin:14px 0}
.cards-2{grid-template-columns:repeat(2,minmax(0,1fr))}
.cards-4{grid-template-columns:repeat(2,minmax(0,1fr))}
.card{
  background:transparent;border:none;border-top:3px solid var(--accent);
  border-radius:0;padding:14px 4px 8px;min-height:unset;
}
.card p{font-size:clamp(12px,1.3vw,17px);margin:0}
.points{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin:28px 0 8px}
.points article{border-left:3px solid var(--accent);padding:4px 0 4px 14px}
.points h3{font-family:var(--serif);font-size:20px;margin-bottom:6px}
.rqgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px 28px;margin:18px 0}
.rqgrid article{display:grid;grid-template-columns:auto 1fr;gap:12px;align-items:start;padding:10px 0;border-bottom:1px solid var(--line)}
.rqgrid .n{font-family:var(--serif);font-size:28px;color:var(--accent);line-height:1;font-weight:700}
.concl{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px 28px;margin:16px 0}
.concl article{padding:8px 0 12px;border-top:2px solid var(--ink)}
.concl h3{font-family:var(--serif);font-size:22px;color:var(--accent)}
table{border-collapse:collapse;width:100%;margin:12px 0 8px;background:transparent;font-size:clamp(11px,1.2vw,15px)}
th{background:var(--ink);color:#fff;text-align:left;padding:10px 12px;font-size:clamp(10px,1.1vw,13px);font-weight:600}
td{border-bottom:1px solid var(--line);padding:8px 12px;color:#243F50;vertical-align:top}
tbody tr:nth-child(even){background:#e8eef1}
.table-wrap{overflow:hidden}
.table-pair{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:12px 0;align-items:start}
.table-pair table{margin:0}
.foot{font-size:clamp(10px,1.05vw,13px);color:var(--muted);margin-top:8px}
.callout{
  background:var(--accent-soft);border-left:5px solid var(--accent);
  padding:12px 16px;margin:14px 0;font-size:clamp(13px,1.4vw,17px);
  font-weight:600;color:#123B47;
}
.callout.warn{background:var(--warn-soft);border-left-color:var(--warn);color:#6E241C}
.metric{font-family:var(--serif);font-size:clamp(20px,2.2vw,28px);font-weight:700;color:var(--accent);margin:14px 0}
.equation{
  font-family:var(--serif);font-size:clamp(18px,2.4vw,30px);font-weight:700;text-align:center;
  color:var(--ink);background:transparent;border:1px solid var(--line);border-radius:0;
  padding:16px;margin:12px 0;
}
.equation.small{font-size:clamp(15px,1.8vw,22px)}
.flow{display:flex;flex-direction:column;align-items:center;gap:8px;margin:14px 0}
.node{
  background:var(--accent-soft);border:2px solid var(--accent);border-radius:0;
  padding:12px 22px;font-size:clamp(15px,1.7vw,20px);font-weight:700;text-align:center;min-width:min(470px,80%);
}
.node.bad{background:var(--warn-soft);border-color:var(--warn);color:#6E241C}
.arrow{font-size:22px;color:var(--accent);font-weight:700}
.timeline{display:grid;grid-template-columns:repeat(7,1fr);gap:8px;margin:36px 0 12px}
.timeline div{border-top:5px solid var(--accent);background:transparent;padding:14px 8px;min-height:110px}
.timeline b{display:block;font-family:var(--serif);font-size:22px;color:var(--ink);margin-bottom:8px}
.timeline span{font-size:13px;color:#344B5A}
.bars{margin:14px 0}
.barrow{display:grid;grid-template-columns:140px 1fr 100px;gap:12px;align-items:center;margin:10px 0;font-size:15px}
.track{height:14px;background:#DCE5EA;border-radius:0;overflow:hidden}
.fill{height:100%;background:var(--accent)}
.split,.cols{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:16px 0}
.split article,.cols>div{
  background:transparent;border:none;border-top:3px solid var(--accent);
  border-radius:0;padding:16px 4px;
}
.footer{
  position:absolute;bottom:14px;left:clamp(28px,5vw,68px);right:clamp(28px,5vw,68px);
  display:flex;justify-content:space-between;color:#7A8D98;font-size:12px;
  border-top:1px solid var(--line);padding-top:8px;
}
.page .chart{margin:2px auto 4px;text-align:center}
.page .chart svg{width:100%;height:auto;max-height:340px}
.page.chart-heavy .chart svg{max-height:220px}
.page.chart-heavy table{font-size:clamp(10px,1.05vw,12px);margin:4px 0}
.page.chart-heavy td,.page.chart-heavy th{padding:5px 8px}
.page.chart-heavy .callout{margin:8px 0;padding:8px 12px;font-size:clamp(12px,1.2vw,15px)}
.page.chart-heavy h1{margin-bottom:8px}
.page.chart-heavy .kicker{margin:14px 0 8px}
.page figcaption{font-size:11px;color:var(--muted);text-align:left;margin-top:0}
.page .mathgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.page .mathcard{
  background:transparent;border:none;border-top:3px solid var(--accent);
  border-radius:0;padding:12px 4px;
}
.page .mathcard p{font-size:13px}
.page .formula{font-family:var(--serif);font-size:clamp(15px,1.8vw,22px);padding:6px 0;color:var(--ink)}
.page .subtle{font-size:16px;color:var(--muted);font-family:var(--sans);font-weight:500}
.page .references{column-count:2;column-gap:28px;margin:8px 0}
.page .references li{font-size:12px;margin:0 0 10px;break-inside:avoid;line-height:1.35}
.page a{color:var(--accent)}
.page.dense table{font-size:clamp(10px,1.1vw,13px)}
.page.dense td,.page.dense th{padding:6px 8px}
.page.title-slide{padding-top:72px}
.page.title-slide h1{font-size:clamp(34px,4.4vw,56px);max-width:980px;margin-bottom:18px}
.page.title-slide .meta{
  display:flex;flex-wrap:wrap;gap:10px 22px;margin:8px 0 28px;
  font-size:14px;color:var(--muted);letter-spacing:.3px;
}
.page.title-slide .meta span{border-left:2px solid var(--accent);padding-left:10px}
.page.title-slide .lead{margin-top:8px;max-width:900px}
#deckbar{
  position:fixed;z-index:50;left:0;right:0;bottom:0;display:flex;align-items:center;gap:8px;
  padding:8px 12px;background:var(--chrome);color:#EAF2F5;font:12px/1.2 var(--sans);
}
#deckbar .group{display:flex;align-items:center;gap:6px}
#deckbar .sep{width:1px;height:18px;background:#3A5160;margin:0 4px}
#deckbar button,.overlay button{
  border:1px solid #516473;background:var(--chrome-btn);color:#fff;border-radius:4px;
  padding:6px 9px;cursor:pointer;font:12px var(--sans);
}
#deckbar button:hover,.overlay button:hover{background:#285163}
#progress{height:3px;background:#243540;position:fixed;z-index:55;left:0;top:0;width:100%}
#progress>i{display:block;height:100%;background:var(--accent);width:0;transition:width .12s linear}
#counter,#timer{min-width:64px;text-align:center;font-variant-numeric:tabular-nums;font-family:var(--mono);font-size:12px}
#deckbar .spacer{flex:1}
.overlay{display:none;position:fixed;z-index:60;inset:0;background:#06111BEE;color:#EAF2F5;padding:5vh 6vw;overflow:auto}
.overlay.open{display:block}
.overlay h2{color:#fff;font-family:var(--serif);font-size:26px}
.toc-act{margin:18px 0 8px;color:#9DE1E4;font-size:12px;letter-spacing:1.5px;text-transform:uppercase;font-weight:700}
#toclist{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:8px}
#toclist button{text-align:left}
#notesText{white-space:pre-wrap;line-height:1.5;max-width:900px;font-size:17px}
#noteTitle{color:#9DE1E4}
#help{font-size:13px;color:#C6D3DA;line-height:1.7}
@media(max-width:800px){
  .page{width:100vw;height:100vh;aspect-ratio:auto;overflow:auto}
  .page .mathgrid,.cards,.cards-4,.rqgrid,.concl,.table-pair,.points{grid-template-columns:1fr}
  .page .references{column-count:1}
  .page .chart svg{max-height:240px}
  #deckbar{gap:4px;padding:6px;flex-wrap:wrap}
}
@media print{
  @page{size:landscape;margin:0}
  html,body{background:#fff!important}
  #deckbar,#progress,.overlay{display:none!important}
  .page,.page.active{
    display:block!important;width:100vw;height:100vh;margin:0;box-shadow:none;
    page-break-after:always;overflow:hidden;opacity:1;transform:none;animation:none;
  }
  .page .footer{display:flex}
  .top{print-color-adjust:exact;-webkit-print-color-adjust:exact}
}
"""


def recolor_svg(html: str) -> str:
    out = html
    for old, new in MPL_MAP.items():
        out = out.replace(old, new)
        out = out.replace(old.upper(), new)
        out = out.replace(old.lower(), new)
    # Matplotlib figure patch often fill white via style
    out = re.sub(
        r'(id="patch_1">\s*<path[^>]*style="fill: )#F4F7F8',
        r"\1#F4F7F8",
        out,
    )
    # axes white patches -> paper already mapped from #ffffff
    return out


def count_cards(section: str) -> int:
    return len(re.findall(r'class="card"', section))


def transform_cards(section: str, index: int) -> str:
    n = count_cards(section)
    if n == 0:
        return section

    # Title slide: convert cards to points
    if index == 1:
        section = section.replace('class="cards"', 'class="points"', 1)
        section = re.sub(r'<article class="card">', "<article>", section)
        return section

    # RQ / conclusions / 4-item grids -> typographic grids
    label = re.search(r'data-label="([^"]+)"', section)
    label_txt = label.group(1) if label else ""
    if index == 2 or "Perguntas" in label_txt:
        section = section.replace('class="cards"', 'class="rqgrid"', 1)
        # wrap each card into rq article with number
        i = 0

        def rq_repl(m: re.Match[str]) -> str:
            nonlocal i
            i += 1
            inner = m.group(1)
            # extract h3 and p
            h = re.search(r"<h3>(.*?)</h3>", inner, re.S)
            p = re.search(r"<p>(.*?)</p>", inner, re.S)
            title = h.group(1) if h else ""
            body = p.group(1) if p else inner
            return (
                f'<article><div class="n">{i:02d}</div>'
                f"<div><h3>{title}</h3><p>{body}</p></div></article>"
            )

        section = re.sub(
            r'<article class="card">(.*?)</article>',
            rq_repl,
            section,
            flags=re.S,
        )
        return section

    if index == 48 or "Conclusões" in label_txt:
        section = section.replace('class="cards"', 'class="concl"', 1)
        section = re.sub(r'<article class="card">', "<article>", section)
        return section

    if n == 4:
        section = section.replace('class="cards"', 'class="cards cards-4"', 1)
    elif n == 2:
        section = section.replace('class="cards"', 'class="cards cards-2"', 1)
    return section


def wrap_table_pairs(section: str) -> str:
    tables = list(re.finditer(r"<table>.*?</table>", section, re.S))
    if len(tables) < 2:
        return section
    # Only pair consecutive tables with little text between them
    first, second = tables[0], tables[1]
    between = section[first.end() : second.start()]
    if re.search(r"<(h1|h2|ul|div class=\"cards|figure|div class=\"flow)", between):
        return section
    if len(re.sub(r"<[^>]+>", "", between).strip()) > 80:
        return section
    paired = (
        '<div class="table-pair">'
        + section[first.start() : first.end()]
        + section[second.start() : second.end()]
        + "</div>"
    )
    return section[: first.start()] + paired + section[second.end() :]


def inject_act_bar(section: str, index: int) -> str:
    act, sub = act_for(index)
    bar = (
        f'<div class="top"><span class="act">{act}</span>'
        f'<span class="act-sub">{sub}</span></div>'
    )
    section = re.sub(r'<div class="top"></div>', bar, section, count=1)
    # act class on page for optional styling
    act_cls = {"Núcleo": "act-core", "Extensão": "act-ext", "Fecho": "act-close"}[act]
    section = section.replace(
        'class="page"', f'class="page {act_cls}"', 1
    )
    section = section.replace(
        'class="page active"', f'class="page active {act_cls}"', 1
    )
    return section


def enhance_title(section: str) -> str:
    section = section.replace(
        'class="page active act-core"',
        'class="page active act-core title-slide"',
        1,
    )
    # Insert meta after h1 if missing
    if 'class="meta"' not in section:
        meta = (
            '<div class="meta">'
            "<span>Rochel Andrey dos Santos Costa</span>"
            "<span>Sistemas Inteligentes</span>"
            "<span>Defesa metodológica · 2026</span>"
            "</div>"
        )
        section = re.sub(r"(</h1>)", r"\1" + meta, section, count=1)
    return section


def enhance_audit(section: str) -> str:
    if 'class="callout warn"' in section:
        return section
    callout = (
        '<p class="callout warn">Resultados v1 ficam como histórico de auditoria; '
        "não são evidência de desempenho do GWO iterativo.</p>"
    )
    # insert before footer
    section = section.replace('<div class="footer">', callout + '<div class="footer">', 1)
    return section


def mark_dense(section: str, index: int) -> str:
    dense_idx = {3, 11, 26, 27, 42, 53, 54}
    if index in dense_idx or section.count("<table") >= 2 or 'class="chart"' in section:
        if "dense" not in section[:80]:
            section = section.replace('class="page ', 'class="page dense ', 1)
    if 'class="chart"' in section and "<table" in section:
        section = section.replace('class="page dense ', 'class="page dense chart-heavy ', 1)
        section = section.replace('class="page ', 'class="page chart-heavy ', 1)
    return section


def transform_section(section: str, index: int) -> str:
    section = inject_act_bar(section, index)
    section = transform_cards(section, index)
    section = wrap_table_pairs(section)
    section = mark_dense(section, index)
    if index == 1:
        section = enhance_title(section)
    if index == 15:
        section = enhance_audit(section)
    if index == 54:
        section = section.replace(
            '<ol class="references">',
            '<ol class="references">',
            1,
        )
    return section


DECKBAR = """
<div id="progress"><i></i></div>
<div id="deckbar">
  <div class="group">
    <button id="prev" title="Slide anterior (←)">←</button>
    <button id="next" title="Próximo slide (→)">→</button>
    <span id="counter">1 / 1</span>
  </div>
  <div class="sep"></div>
  <div class="group">
    <span id="timer">00:00</span>
    <button id="timerToggle">Iniciar</button>
    <button id="timerReset">Zerar</button>
  </div>
  <span class="spacer"></span>
  <div class="group">
    <button id="tocOpen">Índice</button>
    <button id="notesWindow" title="Abrir notas em uma janela separada">Notas ↗</button>
    <button id="notesOpen">Notas</button>
    <button id="full">Tela cheia</button>
    <button id="print">PDF</button>
  </div>
</div>
<div class="overlay" id="toc">
<button class="close">Fechar (Esc)</button><h2>Índice da apresentação</h2><div id="toclist"></div>
</div>
<div class="overlay" id="notes">
<button class="close">Fechar (Esc)</button><h2 id="noteTitle">Notas do apresentador</h2><div id="notesText"></div>
<p id="help">Atalhos: ←/→ ou espaço · Home/End · I índice · N notas · F tela cheia · P imprimir · Esc fechar.</p>
</div>
"""

SCRIPT = r"""
<script>
(() => {
 const pages=[...document.querySelectorAll('.page')];
 let current=0, elapsed=0, timerId=null, notesWindow=null;
 const $=id=>document.getElementById(id);
 const toc=$('toc'), notes=$('notes');
 const fmt=s=>String(Math.floor(s/60)).padStart(2,'0')+':'+String(s%60).padStart(2,'0');
 const ACTS=[
   {start:0,end:29,title:'Núcleo — estudo principal'},
   {start:30,end:45,title:'Extensão — surrogate e meta-learning'},
   {start:46,end:53,title:'Fecho — ameaças, conclusões e apêndice'},
 ];
 function syncPresenterNotes(){
   if(notesWindow && !notesWindow.closed){
     notesWindow.postMessage({
       type:'gwo-presenter-notes',
       index:current+1,
       total:pages.length,
       title:pages[current].dataset.label,
       notes:pages[current].dataset.speakerNotes||'Sem notas para este slide.'
     },'*');
   }
 }
 function openPresenterNotes(){
   if(!notesWindow || notesWindow.closed){
     notesWindow=window.open('','gwoPresenterNotes','width=640,height=820');
     if(!notesWindow){alert('O navegador bloqueou a janela. Permita pop-ups para abrir as notas.');return;}
     notesWindow.document.open();
     notesWindow.document.write(`<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Notas do apresentador</title><style>body{margin:0;padding:28px;background:#101e29;color:#edf4f7;font:17px/1.55 'IBM Plex Sans',Arial}small{color:#8fd8dc;letter-spacing:1px;text-transform:uppercase}h1{font-family:'Source Serif 4',Georgia,serif;font-size:25px;line-height:1.2;margin:12px 0 24px}#notes{white-space:pre-wrap;background:#1b303e;border:1px solid #385365;border-radius:4px;padding:20px;min-height:280px}#count{color:#9fb2bd;font-size:13px}</style></head><body><small>Notas do apresentador</small><h1 id="title">Aguardando slide…</h1><div id="count"></div><p id="notes">Abra a apresentação principal e clique em “Notas ↗”.</p><script>window.addEventListener('message',e=>{const d=e.data;if(!d||d.type!=='gwo-presenter-notes')return;document.getElementById('title').textContent=d.title;document.getElementById('count').textContent='Slide '+d.index+' de '+d.total;document.getElementById('notes').textContent=d.notes;});<\/script></body></html>`);
     notesWindow.document.close();
   }
   syncPresenterNotes();
   notesWindow.focus();
 }
 function show(i){
   current=Math.max(0,Math.min(pages.length-1,i));
   pages.forEach((p,j)=>p.classList.toggle('active',j===current));
   $('counter').textContent=(current+1)+' / '+pages.length;
   $('progress').firstElementChild.style.width=((current+1)/pages.length*100)+'%';
   $('noteTitle').textContent='Notas · '+(current+1)+' — '+pages[current].dataset.label;
   $('notesText').textContent=pages[current].dataset.speakerNotes||'Sem notas para este slide.';
   document.title=(current+1)+'/'+pages.length+' — '+pages[current].dataset.label;
   syncPresenterNotes();
   window.scrollTo(0,0);
 }
 function toggle(panel){panel.classList.toggle('open')}
 function closePanels(){toc.classList.remove('open');notes.classList.remove('open')}
 $('prev').onclick=()=>show(current-1);
 $('next').onclick=()=>show(current+1);
 $('tocOpen').onclick=()=>{notes.classList.remove('open');toggle(toc)};
 $('notesOpen').onclick=()=>{toc.classList.remove('open');toggle(notes)};
 $('notesWindow').onclick=openPresenterNotes;
 $('full').onclick=()=>{if(!document.fullscreenElement)document.documentElement.requestFullscreen?.();else document.exitFullscreen?.()};
 $('print').onclick=()=>window.print();
 $('timerToggle').onclick=()=>{
   if(timerId){clearInterval(timerId);timerId=null;$('timerToggle').textContent='Continuar'}
   else{timerId=setInterval(()=>{elapsed++;$('timer').textContent=fmt(elapsed)},1000);$('timerToggle').textContent='Pausar'}
 };
 $('timerReset').onclick=()=>{elapsed=0;$('timer').textContent='00:00'};
 document.querySelectorAll('.overlay .close').forEach(b=>b.onclick=closePanels);
 const list=$('toclist');
 ACTS.forEach(act=>{
   const h=document.createElement('div');
   h.className='toc-act';
   h.style.gridColumn='1 / -1';
   h.textContent=act.title;
   list.appendChild(h);
   for(let i=act.start;i<=act.end && i<pages.length;i++){
     const b=document.createElement('button');
     b.textContent=String(i+1).padStart(2,'0')+' · '+pages[i].dataset.label;
     b.onclick=()=>{show(i);closePanels()};
     list.appendChild(b);
   }
 });
 document.addEventListener('keydown',e=>{
   if(e.target.matches('input,textarea,select'))return;
   if(e.key==='ArrowRight'||e.key===' '||e.key==='PageDown'){e.preventDefault();show(current+1)}
   else if(e.key==='ArrowLeft'||e.key==='PageUp'){e.preventDefault();show(current-1)}
   else if(e.key==='Home'){show(0)}
   else if(e.key==='End'){show(pages.length-1)}
   else if(e.key.toLowerCase()==='i'){toggle(toc);notes.classList.remove('open')}
   else if(e.key.toLowerCase()==='n'){toggle(notes);toc.classList.remove('open')}
   else if(e.key.toLowerCase()==='f'){$('full').click()}
   else if(e.key.toLowerCase()==='p'){window.print()}
   else if(e.key==='Escape'){closePanels()}
 });
 show(0);
})();
</script>
"""


def main() -> None:
    html = SRC.read_text(encoding="utf-8")
    html = recolor_svg(html)

    # Replace both style blocks with one design system
    html = re.sub(
        r"<style>.*?</style>\s*<style>.*?</style>",
        f"<style>\n{CSS}\n</style>",
        html,
        count=1,
        flags=re.S,
    )

    sections = re.findall(r"<section class=\"page.*?</section>", html, flags=re.S)
    if len(sections) != 54:
        raise SystemExit(f"expected 54 sections, found {len(sections)}")

    new_sections = [transform_section(sec, i + 1) for i, sec in enumerate(sections)]

    # Replace body content: from first section through last, then chrome+script
    start = html.index(sections[0])
    end = html.index(sections[-1]) + len(sections[-1])
    # Drop old chrome/script after sections
    head = html[:start]
    rebuilt = head + "\n".join(new_sections) + "\n" + DECKBAR + SCRIPT + "\n</body></html>\n"

    # Fix title tag
    rebuilt = rebuilt.replace(
        "<title>Defesa metodológica — GWO e PFSP</title>",
        "<title>Defesa metodológica — GWO e PFSP (v4)</title>",
        1,
    )

    DST.write_text(rebuilt, encoding="utf-8")
    print(f"wrote {DST} ({DST.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
