# Auditoria numérica — defesa metodológica GWO/PFSP

**Data:** 2026-11-27  
**Deck auditado (v2):** `c:\Users\roche\Downloads\defesa_metodologica_gwo_pfsp_v2.html`  
**Deck corrigido (v3):** `c:\Users\roche\Downloads\defesa_metodologica_gwo_pfsp_v3.html`  
**HEAD de referência:** `8c276c9563adbb0779596cf5cd786a35921cec55`  
**Branch:** `recovery/surrogate-learning-curve-v2-oom`

## Veredito

Os números centrais do estudo principal (Weeks 2–6, n=30, ta001/ta011) batem com os artefatos versionados. A correção v3 fecha inconsistências de **notas do apresentador**, **arredondamento cruzado**, **separador decimal** e **higiene/proveniência**. Nenhum P0 permanece aberto no v3.

## Fontes de autoridade

| Camada | Artefato |
|---|---|
| Week 6 agregados | `results/week6_benchmark_v1/metadata.json` |
| Week 6 narrativa | `docs/audits/2026-11-25-week6-benchmark-audit.md` |
| Reprodução Colab | `docs/audits/2026-11-25-colab-reproduction-audit.md` |
| Correção população v1 | `docs/audits/2026-11-23-gwo-population-freeze-correction.md` |
| Curva surrogate v2 | `experiments/meta_learning/reports/surrogate_learning_curve_v2_extension_statistical_analysis.md` |
| Fits originais / recuperados | `results/meta_learning_surrogate_learning_curve_v2/learning_curve_runs.csv` (100); `results/meta_learning_surrogate_learning_curve_v2_extension_recovered/recovered_runs.csv` (60) |
| Comparação de modelos | `experiments/meta_learning/reports/surrogate_model_comparison_protocol.md` |
| Surrogate freeze | `docs/decisions/2026-11-27-surrogate-variant-freeze.md` |
| Checkpoint 60 | `docs/reports/2026-11-27-meta-learning-v2-checkpoint60-dev.md` |
| LOO piloto | `results/meta_learning_metabasis_pilot_v1/selector_eval_exploratory_v1/summary.json` |

## Correções aplicadas no v3

| ID | Slide | Problema | Status v3 |
|---|---|---|---|
| P0-1 | 39 | Notes de ta071 copiavam recalls de ta111 (8%/10%) | **Corrigido** → 12% LHS / 10% uniforme em ta071 |
| P0-2 | 36, 39 | “não integrar o surrogate ao GWO” contradizia Week 6 | **Corrigido** → manter MLP histórico; não usar predição como fitness de líderes; não escalar além do top-3 + reavaliação exata |
| P0-3 | 24 | Notes do boxplot ta011 falavam de empates em ta001 | **Corrigido** |
| P1-4 | 11 | Δ ta011 −1,46 vs +1,47 no slide 26 | **Corrigido** → −1,47 (pareado 1,4666…) |
| P1-5 | 26–27 | Decimais com ponto | **Corrigido** → vírgula; `8,08×10⁻⁵` |
| P1-6 | 16 | “100 testes” sem data/contexto | **Corrigido** → CI da correção (23/11) |
| P2-7 | topo | DOCTYPE triplicado | **Corrigido** → um `<!DOCTYPE html>` |
| P2-8 | 53 | Paths da curva ambíguos | **Corrigido** → 100 (N≤4k) + 60 (8k–32k) explícitos |
| P2-9 | 11 | Cabeçalho “Diferença média” ambíguo | **Corrigido** → `Δ (Optuna − Baseline)` |

## Claims principais — status

| Slide | Claim | Fonte | Status |
|---|---|---|---|
| 4 | UB ta001=1278; ta011=1582 | Week 6 metadata | OK |
| 10 | Baseline média 1272,73 / 1640,23; 15.030 evals | `week2_baseline_v2` / Week 6 | OK |
| 11 | Optuna 45×333; a_start/a_end/γ; Δ −4,33 / −1,47 | Week 6 `optuna.parameters` + pairwise | OK (v3) |
| 12 | RMSE/MAE/R²/Spearman Week 4 | Week 6 `surrogate.models.*.test_metrics` | OK |
| 13 | Speedup 3,31× / 5,45×; break-even 11,6k / 8,1k | Week 4 audit | OK |
| 16 | CI 100 testes run 45104636797 | Freeze correction audit (23/11) | OK (v3 contextualizado) |
| 17–18 | Fuzzy médias; orçamentos; 240 runs | Week 5/6 | OK |
| 21 | ta001 tabela completa (média/med/DP/hits/tempo) | Week 6 metadata | OK |
| 23 | ta011 tabela; 0 hits UB | Week 6 metadata | OK |
| 25 | Friedman + 3 pares Holm só em ta011 (Surrogate) | Week 6 pairwise Holm | OK |
| 26–27 | Diferenças pareadas e p Holm | Week 6 pairwise | OK (v3 vírgulas) |
| 28 | 2.797.200 + 4.000 = 2.801.200; speed 34,0% / 53,5% | Week 6 audit / protocol | OK |
| 29 | 180/180; Python 3.13.18 Colab / 3.14.6 local | Colab audit | OK |
| 32–34 | Curva @32k e ganhos 4k→32k | Análise estatística curva v2 | OK |
| 41–42 | Piloto modelos ta111 N=8k; recall top-10=0 | Model comparison protocol | OK |
| 43 | 20 exec; 300.600 linhas; ~551 MB; Cost Pilot v2 | Population audit | OK |
| 44 | 35 preditores `taillard_pfsp_features_v1` | Feature freeze | OK |
| 45 | Piloto RF≈Fuzzy; checkpoint 60 wins 20/14/13/1; holdout selado | LOO + checkpoint60-dev | OK |
| 50 | Branch `recovery/surrogate-learning-curve-v2-oom` | Checkout atual | OK |
| 53 | HEAD `8c276c95…`; 100+60 fits | master-runbook SA0 + CSVs | OK (v3 paths) |

## P0 abertos

Nenhum.

## Como revalidar antes da defesa

1. Abrir `defesa_metodologica_gwo_pfsp_v3.html`.
2. Conferir notas dos slides 24, 36 e 39 (atalho N).
3. Conferir tabela Optuna (slide 11): Δ ta011 = −1,47.
4. Conferir slides 26–27: vírgulas e notação `8,08×10⁻⁵`.
5. Se o HEAD mudar, atualizar o slide 53 antes de apresentar.

## Fora de escopo desta auditoria

- Redesenho visual / tipografia do deck.
- Regeneração dos SVG embutidos.
- Decisão formal 60→120 do meta-learning.
- Conteúdo científico das referências (slide 54) além da citação padrão.
