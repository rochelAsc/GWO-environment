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
| C4 recheck A–E | Aprovado | `analysis_recheck_20261127/` idêntico ao publicado; 432/432; norm=ub 36/36 |
| Freeze metabasis_pilot_v1 | Aprovado | `experiments/meta_learning/data/metabasis_pilot_v1/`; decisão `docs/decisions/2026-11-27-metabasis-pilot-v1-freeze.md` |
| LOO seletores (exploratório) | Concluído | `results/meta_learning_metabasis_pilot_v1/selector_eval_exploratory_v1/` |
| Reprodução freeze+LOO | Aprovada | [relatório A–D](2026-11-27-meta-learning-reproduction-ad.md); hashes 4/4; LOO recheck bit-idêntico |

## Decisões-chave

1. Não trocar MLP da variante Surrogate; ranking real em trajetórias GWO permanece fraco.
2. Extrator `taillard_pfsp_features_v1` congelado; preditores só da matriz P.
3. Expansão para 36 instâncias (3 por grupo) baixada do espelho PISCO; custo viável no hardware local.
4. Piloto 36×3×4 fechado, auditado e congelado como `metabasis_pilot_v1`. Avaliação LOO é exploratória; não é evidência confirmatória.
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

## Avaliação exploratória LOO (36 instâncias)

Relatório completo: [2026-11-27-meta-learning-selector-loo-exploratory.md](2026-11-27-meta-learning-selector-loo-exploratory.md).

Protocolo: leave-one-instance-out; RF 200 árvores; seed 0; aleatório = média de 100 sorteios/fold. Fonte: `selector_eval_exploratory_v1/summary.json`.

| Seletor | Regret médio | IC95 | vs Fuzzy (melhor/pior/empate) |
|---|---:|---|---|
| always Fuzzy | **0,00292** | [0,00159, 0,00441] | — |
| RF regressor | 0,00291 | [0,00154, 0,00430] | 5 / 3 / 28 |
| best-global-treino (= Fuzzy) | 0,00292 | [0,00159, 0,00441] | 0 / 0 / 36 |
| RF classifier | 0,00523 | [0,00342, 0,00707] | 8 / 17 / 11 |
| always Baseline | 0,00614 | [0,00425, 0,00829] | 12 / 22 / 2 |
| always Optuna | 0,00681 | [0,00445, 0,00920] | 12 / 23 / 1 |
| random | 0,00905 | [0,00717, 0,01098] | 6 / 29 / 1 |
| always Surrogate | 0,01931 | [0,01473, 0,02388] | 3 / 32 / 1 |

Accuracy LOO: classifier 22,2%; regressor 47,2%. RF regressor empatou Fuzzy em regret; classifier piorou. Sem evidência de ganho operacional no piloto.

## Auditoria crítica da avaliação LOO

- A diferença pontual de regret entre RF regressor e sempre Fuzzy é de aproximadamente **−0,0000134** (0,0029053 contra 0,0029187), pequena demais para sustentar ganho operacional; o placar pareado é 5/3/28.
- Os IC95 bootstrap se sobrepõem amplamente. O bootstrap dos 36 regrets descreve variação entre instâncias do piloto, mas não incorpora integralmente a variabilidade do processo de treinamento, seleção de modelo ou mudança de distribuição.
- O LOO treina 36 modelos com 35 instâncias cada e 35 preditores. A relação amostra/dimensão é desfavorável; o resultado deve ser tratado como diagnóstico exploratório, não como estimativa confirmatória de generalização.
- Os folds LOO compartilham grande parte dos dados de treino; não equivalem a um holdout independente. Nenhum holdout confirmatório foi reservado.
- O fato de o melhor-global-do-treino coincidir com Fuzzy em todos os folds mostra que o seletor aprendido por frequência colapsa no baseline operacional neste piloto.

## Reprodução A–D (2026-11-27)

Relatório completo: [2026-11-27-meta-learning-reproduction-ad.md](2026-11-27-meta-learning-reproduction-ad.md).  
Registro JSON: `results/meta_learning_metabasis_pilot_v1/selector_eval_recheck_20261127/reproduction_record.json`.

| Item | Resultado |
|---|---|
| Branch / HEAD | `recovery/surrogate-learning-curve-v2-oom` / `b5456d1f20523aca267c03ca379e58b3406c38fc` |
| Testes | 29 passed |
| Freeze SHA-256 | 4/4 OK (`metabasis_pilot_v1`); freeze **não** regenerado |
| LOO recheck | `summary.json` e `per_instance_predictions.csv` bit-idênticos ao publicado |
| SHA `summary.json` | `218c448f80f4f16a2aab7afca43a511665420824c2f0484328ef4351ec70a2ba` |
| SHA predictions | `68edebba8e9e61c95b28e585f58687512cd22fef2adc4bd337c21a40fa14ae0d` |
| Ambiente | Python 3.14.6; NumPy 2.5.1; pandas 2.3.3; scikit-learn 1.9.0 |
| Divergências | nenhuma |
| Decisão Fase 5 | **pendente** |

## Próximos passos recomendados

1. **Decisão formal obrigatória** (ainda pendente; nenhuma opção pré-selecionada): (a) expandir instâncias → `metabasis_v2` + holdout pré-reservado; (b) encerrar extensão como exploratória sem ganho vs Fuzzy; (c) reformular pergunta com novo protocolo.
2. Se (a): priorizar diversidade 60–120, não só mais seeds; `metabasis_pilot_v1` imutável.
3. Não retunar Surrogate nem misturar orçamentos sem reportar a diferença.
4. Não iniciar bateria GWO até a decisão estar registrada em documento de decisão.

**Gate atual:** reprodução A–D **aprovada e documentada**. Fase 5 **não** autorizada até decisão explícita (a/b/c).

## Comandos de verificação

```bash
python -m pytest -q tests/test_meta_learning_features.py tests/test_meta_learning_metabasis_pilot.py tests/test_gwo_population_deduplicate.py tests/test_week6_surrogate.py
python -m scripts.evaluate_meta_learning_selectors_pilot --freeze-dir experiments/meta_learning/data/metabasis_pilot_v1 --output results/meta_learning_metabasis_pilot_v1/selector_eval_recheck_20261127 --seed 0 --random-repeats 100
```

Não reexecute o freeze no diretório existente: o artefato é imutável. A reprodução LOO deve usar o diretório novo indicado no runbook.


## Runbook vigente

A reprodução A–D do [runbook](2026-11-27-meta-learning-next-execution-runbook.md) está **concluída**. O próximo passo operacional é somente a decisão formal (a/b/c). Não há nova bateria a executar até essa decisão.
