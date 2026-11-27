# Decisão: congelar metabasis_pilot_v1

**Data:** 2026-11-27  
**Status:** aprovada  
**Gate:** pós C4 / pré-expansão (Fases 5+)

## Decisão

Congelar a meta-base derivada do piloto 36×3×4 como `metabasis_pilot_v1` em  
`experiments/meta_learning/data/metabasis_pilot_v1/`.

Conteúdo imutável desta versão:

| Arquivo | Papel |
|---|---|
| `instance_features.csv` | Features `taillard_pfsp_features_v1` (35 preditores) |
| `per_instance_targets.csv` | Alvos por instância (winner + quatro `y_*`) |
| `instance_manifest.csv` | Inventário/UB |
| `runs.csv` | 432 execuções brutas |
| `freeze_manifest.json` | Hashes SHA-256, commit, schema |

## Regras

1. Unidade = instância; seeds não inflacionam n.
2. Preditores = somente colunas de feature além de `instance`/`sha256`/`feature_version`.
3. Normalização deste freeze: **UB em 36/36** instâncias (`norm=ub`). Fallback `rel_best` permanece no agregador para casos futuros.
4. Métrica primária de seleção: **regret por instância** vs oráculo.
5. Baseline operacional a superar: **sempre Fuzzy** (também recalculado como melhor global do treino em cada fold LOO).
6. Resultado exploratório. Não alegar generalização confirmatória nem abrir expansão 60/120 só por este freeze.
7. Qualquer correção gera nova versão (`metabasis_pilot_v2`…); não sobrescrever este diretório.

## Evidência de integridade

- Validação: 432 chaves únicas, 0 missing/extra/duplicata, hashes de instância e modelo Surrogate preenchidos.
- Recheck agregador = análise publicada (Fuzzy 17/36; low-conf 22/36).
- Freeze via `python -m scripts.freeze_meta_learning_metabasis_pilot`.

## Avaliação exploratória associada

`results/meta_learning_metabasis_pilot_v1/selector_eval_exploratory_v1/`  
(LOO por instância; RF classifier/regressor + baselines). Não é holdout confirmatório.

Relatório: [2026-11-27-meta-learning-selector-loo-exploratory.md](../reports/2026-11-27-meta-learning-selector-loo-exploratory.md).
