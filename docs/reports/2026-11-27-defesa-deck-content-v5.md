# Defesa deck — conteúdo e exposição v5

**Data:** 2026-11-27  
**Entrada:** `Downloads/defesa_metodologica_gwo_pfsp_v4.html`  
**Saída:** `Downloads/defesa_metodologica_gwo_pfsp_v5.html`  
**Mapa:** `scripts/_defesa_deck_v5_content_map.py`  
**Builder:** `scripts/_build_defesa_deck_v5_content.py`  
**v4:** preservado (layout). **Números de tabelas/SVG/métricas:** idênticos ao v4.

## Árvore de claims

1. **RQ1 (validade):** v1 não executava GWO iterativo; v2 corrige; CI valida regressão, não o benchmark.
2. **RQ2 (qualidade):** sem vencedor universal — Optuna descritivo em ta001, Fuzzy em ta011; pares Baseline/Optuna/Fuzzy sem Holm.
3. **RQ3 (custo):** Surrogate mais rápido com orçamento exato menor; perda de qualidade sustentada em ta011.
4. **Extensão surrogate:** mais dados melhoram RMSE/Spearman; top-k continua fraco; instância importa; piloto ≠ matriz 80.
5. **Extensão meta:** outro problema; checkpoint 60 exploratório; holdout selado; decisão 60→120 pendente.

## Contrato de fala

Cada note: **Gancho → Olhar → Não concluir → Ponte** (apêndice 50–54: **BACKUP Q&A**).  
Takeaways on-slide com verbo epistêmico; kickers 50–54 prefixados `Backup Q&A ·`.

## Takeaways (resumo)

| # | Takeaway |
|---:|---|
| 01 | Tese no lead: cadeia de evidências + extensões abertas |
| 03 | Hipóteses pré-registradas, não presumidas confirmadas |
| 05 | Fitness = makespan exato decodificado |
| 07 | Auditoria quebra a linearidade S1–S6 |
| 10–14 | Papel de cada variante no desenho |
| 16 | CI ≠ Week 6 |
| 17–18 | Fuzzy descritivo; Surrogate com orçamento desigual |
| 19–27 | Contraste ta001/ta011; Holm como regra |
| 28–30 | Trade-off; Colab; fechamento do Núcleo |
| 31–46 | Fronteira de extensão; 3 mensagens da curva; meta aberto |
| 47–49 | Ameaças; respostas RQ; perguntas ao professor |
| 50–54 | Backup sob demanda |

## QA

- 54/54 labels iguais; 54/54 notes reescritas e estruturadas.
- Tabelas, SVGs, `.metric`, equações: byte-iguais ao v4.
- Callouts: 16 → 46 (takeaways sistemáticos; warn v1 preservado).
- Contagens extras de números no HTML vêm só das notes (“Olhar: …”), não das tabelas.

```bash
python scripts/_build_defesa_deck_v5_content.py
```
