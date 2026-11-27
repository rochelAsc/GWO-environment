# Status das fases Meta-Learning — 2026-11-27

## Gates

| Gate | Status | Artefato |
|---|---|---|
| C1 populações | Aprovado | `scripts/validate_gwo_populations_csv.py`; SHA-256 `ca6212d2…abc0`; 300.600 linhas |
| C1 análise | Aprovado | `results/gwo_population_distribution_audit_v1/analysis/` |
| C1 dedupe streaming | Aprovado | `scripts/run_gwo_population_distribution_audit.py` |
| C2 Surrogate freeze | Aprovado | `docs/decisions/2026-11-27-surrogate-variant-freeze.md`; ranking GWO fraco (recall top-3 mediana 0) |
| C3 features freeze | Aprovado | `docs/decisions/2026-11-27-meta-feature-extractor-freeze.md`; 36 instâncias |
| C4 custo 36 | Medido | `results/meta_learning_cost_pilot_v3/cost_projection.json` ≈ **1,06 h** (3 seeds) / **3,54 h** (10 seeds) |
| C4 meta-base piloto | Aprovado | `results/meta_learning_metabasis_pilot_v1/`: **432/432** runs (36 instâncias × 4 variantes × 3 seeds) |
| C4 análise do piloto | Concluída | `results/meta_learning_metabasis_pilot_v1/analysis/` |

## Decisões-chave

1. Não trocar MLP da variante Surrogate; ranking real em trajetórias GWO permanece fraco.
2. Extrator `taillard_pfsp_features_v1` congelado; preditores só da matriz P.
3. Expansão para 36 instâncias (3 por grupo) baixada do espelho PISCO; custo viável no hardware local.
4. Piloto 36×3×4 fechado e agregado; treino meta-modelo ainda não autorizado como evidência confirmatória.
5. Baseline operacional forte do piloto: **sempre Fuzzy**. Meta-Learning só se justifica se superar esse seletor em holdout por instância.

## Análise do piloto meta-base (36 instâncias)

Protocolo: média de makespan em 3 seeds por variante; normalização por UB publicado quando disponível, senão pela melhor média entre variantes da própria instância. Unidade = instância. Fonte: `analysis/summary.json` e `analysis/per_instance_targets.csv`.

### Desempenho agregado

| Variante | Vitórias / 36 | y médio (norm.) | Regret médio vs oráculo | Tempo médio (s) |
|---|---:|---:|---:|---:|
| fuzzy | **17** | **1,046** | **0,0029** | 11,44 |
| baseline | 9 | 1,049 | 0,0061 | 11,15 |
| optuna | 9 | 1,050 | 0,0068 | 11,20 |
| surrogate | **1** | 1,063 | 0,0193 | **1,93** |

### Comparações pareadas (média normalizada)

| Par | Placar |
|---|---|
| baseline vs optuna | 17–18 (1 empate) |
| baseline vs fuzzy | 12–22 (2 empates) |
| optuna vs fuzzy | 12–23 (1 empate) |
| baseline vs surrogate | 31–4 (1 empate) |
| optuna vs surrogate | 33–1 (2 empates) |
| fuzzy vs surrogate | 32–3 (1 empate) |

### Vitórias por grupo de dimensão

| Grupo | Vencedores |
|---|---|
| 20×5 | optuna 2, fuzzy 1 |
| 20×10 | fuzzy 2, baseline 1 |
| 20×20 | 1 cada (baseline / fuzzy / optuna) |
| 50×5 | 1 cada (optuna / fuzzy / baseline) |
| 50×10 | 1 cada (fuzzy / optuna / baseline) |
| 50×20 | fuzzy 2, baseline 1 |
| 100×5 | 1 cada (baseline / surrogate / optuna) |
| 100×10 | fuzzy 3 |
| 100×20 | fuzzy 2, baseline 1 |
| 200×10 | optuna 2, baseline 1 |
| 200×20 | fuzzy 2, optuna 1 |
| 500×20 | fuzzy 2, baseline 1 |

### Limitações do piloto

- **22/36** rótulos com margem &lt; 0,5% entre 1º e 2º → muitos empates práticos; classificação será instável.
- Surrogate permanece barato e de qualidade inferior neste protocolo; não usar vitórias de qualidade para alegar utilidade de ranking.
- Três seeds por instância estimam ruído, não criam 36×3 unidades independentes.
- Resultado exploratório: não alegar generalização confirmatória nem promover Fuzzy como ótimo universal fora desta amostra.

## Próximos passos recomendados

**Runbook operacional da próxima rodada:** [2026-11-27-meta-learning-next-execution-runbook.md](2026-11-27-meta-learning-next-execution-runbook.md). Ele contém os comandos ordenados para reprodução, auditoria de completude, integridade numérica e alinhamento de features/alvos. Execute as etapas A–E e envie as saídas antes de iniciar treinamento ou expansão.


1. Congelar a meta-base derivada do piloto (`per_instance_targets.csv` + features v1) como versão `metabasis_pilot_v1`.
2. Implementar baselines de seleção + RF classificador/regressor com divisão **por instância** (Fases 6–8), tratando o resultado como exploratório.
3. Só então decidir expansão para 10 seeds e/ou 60–120 instâncias, com base no custo já medido.
4. Não retunar Surrogate nem misturar orçamentos sem reportar a diferença.

## Comandos de verificação

```bash
python -m scripts.validate_gwo_populations_csv
python -m scripts.analyze_gwo_population_distribution
python -m scripts.evaluate_surrogate_on_gwo_populations
python -m pytest -q tests/test_meta_learning_features.py tests/test_gwo_population_deduplicate.py tests/test_week6_surrogate.py
python -m scripts.run_meta_learning_metabasis_pilot
python -m scripts.analyze_meta_learning_metabasis_pilot
```
