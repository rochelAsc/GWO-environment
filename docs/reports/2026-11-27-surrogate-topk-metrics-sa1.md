# S-A1 — contrato de métricas top-k

**Data:** 2026-11-27  
**Status:** **aprovado** (funções + testes). Históricos da curva **não** regenerados.  
**Pré-requisito:** [S-A0](2026-11-27-master-runbook-sa0-audit.md).

## Entrega

| Item | Caminho |
|---|---|
| Módulo | `experiments/meta_learning/scripts/surrogate_topk_metrics.py` |
| Testes | `tests/test_surrogate_topk_metrics.py` (13 passed) |
| Consumidor futuro | `run_surrogate_model_comparison_pilot.py` agora grava também as chaves S-A1 |

## Contrato

- Makespan: menor é melhor.
- **strict:** exatamente `k` índices; desempate por índice original ascendente (`lexsort`).
- **inclusive:** todos com score ≤ limiar da posição `k` strict; denominador de recall = `|real|` (variável).
- `best_selected_regret` = `min(y_selected) - min(y_true)`
- `mean_selected_regret` = `mean(y_selected) - min(y_true)`
- Baseline aleatório: `random_topk_baseline(..., seed=...)` com repetições documentadas.

Nomes novos no suite: `top{k}_{strict|inclusive}_{recall|best_selected_regret|mean_selected_regret|...}`.

## Histórico preservado

CSVs da learning curve v2 mantêm `top{k}_regret` (= best-selected sob argsort legado). Não sobrescrever. Reavaliação versionada usa o módulo novo quando houver NPZs suficientes.

`evaluate_predictions` em `run_surrogate_learning_curve_v2.py` **não** foi alterado nesta etapa.

## Testes cobertos

Empate no limite k; todos iguais; k=1; k>n; previsão constante; ranking inverso; ótimo selecionado; nenhum ótimo; recall inclusive; invariância sob permutação de linhas; nomes best vs mean; baseline seed-determinístico; rejeição de shapes/NaN/policy inválida.

```bash
python -m pytest -q tests/test_surrogate_topk_metrics.py
```

## Próximo

S-A2: smoke cell (`ta111`, N=8000, 1 modelo) depois matriz ampliada — sem concorrer com baterias Meta-Learning pesadas. M-B0 continua pendente de decisão formal 60→120.
