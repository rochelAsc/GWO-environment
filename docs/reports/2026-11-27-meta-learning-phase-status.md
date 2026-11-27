# Status das fases Meta-Learning — 2026-11-27

**Estado atual:** Fase A + coleta/agregação development do checkpoint 60 **concluídas**. Holdout selado. Decisão 60→120 pendente (custo/integridade apenas).

## Gates

| Gate | Status | Artefato |
|---|---|---|
| C1 populações | Aprovado | `scripts/validate_gwo_populations_csv.py`; SHA-256 `ca6212d2…abc0`; 300.600 linhas |
| C1 análise | Aprovado | `results/gwo_population_distribution_audit_v1/analysis/` |
| C1 dedupe streaming | Aprovado | `scripts/run_gwo_population_distribution_audit.py` |
| C2 Surrogate freeze | Aprovado | `docs/decisions/2026-11-27-surrogate-variant-freeze.md` |
| C3 features freeze | Aprovado | `docs/decisions/2026-11-27-meta-feature-extractor-freeze.md` |
| C4 custo 36 | Medido | `results/meta_learning_cost_pilot_v3/cost_projection.json` |
| C4 meta-base piloto | Aprovado | `results/meta_learning_metabasis_pilot_v1/` 432/432 |
| Freeze metabasis_pilot_v1 | Aprovado | `experiments/meta_learning/data/metabasis_pilot_v1/` |
| LOO + reprodução A–D | Aprovados | [LOO](2026-11-27-meta-learning-selector-loo-exploratory.md); [A–D](2026-11-27-meta-learning-reproduction-ad.md) |
| Decisão Fase 5 | **Aprovada** | [expansão v2](../decisions/2026-11-27-meta-learning-expansion-v2.md) |
| Inventário 120 + split | **Congelado** | [Fase A](2026-11-27-meta-learning-v2-phase-a-inventory-split.md); SHA split `c17bce88…934a` |
| Checkpoint 60 development | **Concluído** | [relatório](2026-11-27-meta-learning-v2-checkpoint60-dev.md); 576/576 runs; holdout selado |
| Decisão 60→120 | Pendente | Só custo/integridade; sem abrir holdout |

## Decisões-chave

1. Surrogate MLP histórico congelado; orçamento desigual permanece explícito.
2. Features só da matriz P (`taillard_pfsp_features_v1`).
3. Piloto 36 imutável; expansão em `metabasis_v2` com split `seed=20261127`.
4. Baseline operacional a superar: **sempre Fuzzy**.
5. Holdout selado até protocolo confirmatório congelado.
6. Checkpoint 60 development fechado (48 instâncias); não é evidência confirmatória.

## Piloto 36 (histórico)

Fuzzy 17/36; regret Fuzzy 0,0029. LOO: RF sem ganho útil vs Fuzzy. Detalhes nos relatórios do piloto.

## Checkpoint 60 — desenvolvimento (48 instâncias)

Relatório: [2026-11-27-meta-learning-v2-checkpoint60-dev.md](2026-11-27-meta-learning-v2-checkpoint60-dev.md).

| Variante | Vitórias / 48 | y médio | Regret médio | Tempo médio (s) |
|---|---:|---:|---:|---:|
| fuzzy | **20** | **1,050** | **0,0037** | 11,19 |
| optuna | 14 | 1,053 | 0,0070 | 10,95 |
| baseline | 13 | 1,052 | 0,0057 | 10,92 |
| surrogate | 1 | 1,065 | 0,0195 | **1,86** |

- 576 runs = 432 `pilot_v1_reused` + 144 `metabasis_v2_new`
- Low-confidence: 30/48; norm=`ub` 48/48
- Wall-clock novas 12: ≈ 0,33 h; extrapolação ≈ 1,3 h para as 48 development restantes até 120

## Próximos passos

1. Decidir formalmente: avançar a 120 ou encerrar em 60 (documento de decisão).
2. Se avançar: executar development `stage=120` (48 instâncias × 4 × 3 = 576 runs); holdout continua selado.
3. Se encerrar em 60: treinar/CV só nas 48; congelar pipeline; só então abrir holdout 12.
4. Não regenerar split; não tocar `metabasis_pilot_v1`.

## Comandos

```bash
python -m scripts.build_meta_learning_metabasis_v2_checkpoint60_dev
python -m pytest -q tests/test_meta_learning_metabasis_v2_split.py tests/test_meta_learning_metabasis_v2_runner.py
# se avançar a 120:
python -m scripts.run_meta_learning_metabasis_v2 --stages 120 --partitions development
```
