# Defesa deck — redesign visual v4

**Data:** 2026-11-27  
**Entrada:** `Downloads/defesa_metodologica_gwo_pfsp_v3.html` (conteúdo auditado, intocado)  
**Saída:** `Downloads/defesa_metodologica_gwo_pfsp_v4.html`  
**Builder:** `scripts/_build_defesa_deck_v4.py`  
**v2/v3:** preservados

## O que mudou (layout only)

- Tipografia: Source Serif 4 (títulos) + IBM Plex Sans/Mono; Arial removido.
- Tokens: ink `#0B1F33`, accent `#0A7A72`, warn `#B33A2B`, paper `#F4F7F8`, stage `#07131C`.
- Barra de ato no topo: Núcleo (01–30) / Extensão (31–46) / Fecho (47–54).
- Cards: grelha 2×2 para 4 itens; título usa `.points`; RQs usam `.rqgrid`; conclusões usam `.concl` tipográfico.
- Tabelas empilhadas adjacentes → `.table-pair` (Baseline, Optuna, testes S6).
- SVGs Matplotlib: cores default remapeadas para a paleta da marca; fundo branco → paper.
- Deckbar agrupada (Nav | Tempo | Ferramentas); TOC indexado por ato.
- Motion leve no slide ativo; `prefers-reduced-motion` respeitado.
- Slide 15: callout warn reforçando que v1 não é evidência de desempenho.
- Slide 01: meta com autor, disciplina e ano.

## O que não mudou

- 54 slides, labels, speaker notes (bit-a-bit).
- Números Week 6 / surrogate / meta-learning.
- Atalhos ←/→, I, N, F, P, Home/End, janela de notas.

## QA

- Viewport 1280×800: overflow vertical = 0 em 54/54 slides.
- Amostra 1920×1080: overflow = 0 nos slides densos (01, 02, 15, 19, 26, 42, 48, 54).
- TOC abre com 3 atos; notas (N) abrem; único erro de console: favicon 404 irrelevante.
- Contagens-chave preservadas (`1272,73`, `−1,47`, `240 execuções`, `576/576`, etc.).

## Regenerar

```bash
python scripts/_build_defesa_deck_v4.py
```
