# S-A2 smoke — comparação com métricas S-A1

**Data:** 2026-11-27  
**Status:** smoke **concluído** (mesma célula do piloto: `ta111`, N=8000, rep=1, uniforme)  
**Saída nova:** `results/meta_learning_surrogate_model_comparison_sa1_metrics_smoke/`  
**Piloto antigo:** preservado em `results/meta_learning_surrogate_model_comparison_pilot/`

## Comando

```bash
python -m experiments.meta_learning.scripts.run_surrogate_model_comparison_pilot \
  --output results/meta_learning_surrogate_model_comparison_sa1_metrics_smoke
```

## Resultado

| model | spearman | top10_regret (legado) | top10_strict_best_selected_regret | top10_strict_mean_selected_regret | fit (s) |
|---|---:|---:|---:|---:|---:|
| mlp_64x64 | 0.213 | 270 | 270 | 815.2 | ≈2 |
| random_forest | 0.251 | 367 | 367 | 703.6 | ≈559 |
| extra_trees | 0.244 | 430 | 430 | 773.0 | ≈202 |
| hist_gradient_boosting | 0.265 | 319 | 319 | 713.6 | ≈7 |

Wall-clock total ≈ 13,4 min. `top10_recall` legado = 0.0 nos quatro modelos (igual ao piloto).

## Gate

- Checkpoint/retomada OK; diretório novo sem sobrescrever piloto.
- Colunas S-A1 presentes no CSV.
- Próximo: matriz A2 ampliada (ta071/ta111 × 8k/32k × 5 reps × 4 modelos) em runner/generalização dedicada — **não** reutilizar este smoke como matriz completa.
