# Defesa deck — legendas de fórmulas/siglas v6

**Data:** 2026-11-27  
**Entrada:** `Downloads/defesa_metodologica_gwo_pfsp_v5.html`  
**Saída:** `Downloads/defesa_metodologica_gwo_pfsp_v6.html`  
**Mapa:** `scripts/_defesa_deck_v6_legends_map.py`  
**Builder:** `scripts/_build_defesa_deck_v6_legends.py`  
**v5:** preservado.

## O que entrou

- CSS `.legend` / `.clarify` (tipografia ~9–11px, grid compacto).
- Legend as locais em **21 slides**: 04–06, 12, 14, 18, 25, 31–40, 42, 44, 50–51.
- Texto extra (`.clarify`) em 04, 06, 12, 25, 36, 39, 44.
- Notes 04/06: apêndice “Olhar também: legenda…”.

## QA

- 54 labels; tabelas e SVGs idênticos ao v5.
- Overflow @1280×800: 0 nos slides prioritários com legenda (04, 05, 06, 12, 14, 18, 25, 36, 39, 42, 44, 50, 51).
- Slides 26–27 (chart+tabela, sem legenda nova) ~17px — residual de densidade prévia, fora do escopo das legendas.

```bash
python scripts/_build_defesa_deck_v6_legends.py
```
