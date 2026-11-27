# Avaliação exploratória LOO dos seletores meta — 2026-11-27

**Status:** exploratório (não confirmatório); reprodução A–D aprovada  
**Freeze:** `metabasis_pilot_v1`  
**Branch/commit da avaliação original:** `recovery/surrogate-learning-curve-v2-oom` / `f51f96d0…`  
**Branch/commit da reprodução:** `recovery/surrogate-learning-curve-v2-oom` / `b5456d1f…`  
**Artefatos publicados:** `results/meta_learning_metabasis_pilot_v1/selector_eval_exploratory_v1/`  
**Artefatos recheck:** `results/meta_learning_metabasis_pilot_v1/selector_eval_recheck_20261127/`  
**Script:** `python -m scripts.evaluate_meta_learning_selectors_pilot`  
**Relatório de reprodução:** [2026-11-27-meta-learning-reproduction-ad.md](2026-11-27-meta-learning-reproduction-ad.md)

## 1. Pergunta

Nas 36 instâncias do piloto, um seletor meta (RF classifier/regressor) reduz o regret por instância em relação a baselines fixos — em especial **sempre Fuzzy**?

## 2. Protocolo

| Item | Valor |
|---|---|
| Unidade | instância |
| Validação | Leave-One-Instance-Out (36 folds) |
| Features | `taillard_pfsp_features_v1` (35 preditores; sem metadados) |
| Alvos | `winner` + `y_baseline/optuna/fuzzy/surrogate` (norm=`ub` 36/36) |
| RF | 200 árvores; seed 0; classifier com `class_weight=balanced` |
| Regressor | multioutput; escolha = `argmin` das 4 previsões |
| Aleatório | média de 100 sorteios uniformes por fold |
| Melhor global do treino | moda dos winners no treino do fold |
| Métrica primária | regret vs oráculo por instância; média/mediana + IC95 bootstrap |
| Comparador operacional | always Fuzzy; placar pareado melhor/pior/empate |

Não houve holdout reservado, tuning de hiperparâmetros nem seleção de features. Amostra: 22/36 rótulos com margem &lt; 0,5%.

## 3. Resultados

Fonte: `selector_eval_exploratory_v1/summary.json`.

| Seletor | Regret médio | Mediana | IC95 | vs Fuzzy (↑/↓/=) |
|---|---:|---:|---|---|
| always Fuzzy | 0,00292 | 0,00011 | [0,00159, 0,00441] | — |
| RF regressor | 0,00291 | 0,00009 | [0,00154, 0,00430] | 5 / 3 / 28 |
| best-global-treino | 0,00292 | 0,00011 | [0,00159, 0,00441] | 0 / 0 / 36 |
| RF classifier | 0,00523 | 0,00309 | [0,00342, 0,00707] | 8 / 17 / 11 |
| always Baseline | 0,00614 | 0,00460 | [0,00425, 0,00829] | 12 / 22 / 2 |
| always Optuna | 0,00681 | 0,00468 | [0,00445, 0,00920] | 12 / 23 / 1 |
| random (média) | 0,00905 | 0,00879 | [0,00717, 0,01098] | 6 / 29 / 1 |
| always Surrogate | 0,01931 | 0,01764 | [0,01473, 0,02388] | 3 / 32 / 1 |

Accuracy LOO (complementar): classifier **22,2%**; regressor **47,2%**.

`best_global_train` empatou Fuzzy em 36/36: no treino de cada fold, Fuzzy foi a variante mais frequente — o seletor “aprendido” colapsa no baseline operacional.

## 4.1 Leitura quantitativa e limites da incerteza

A diferença pontual entre RF regressor e sempre Fuzzy é `0,0029053 - 0,0029187 ≈ -0,0000134`. Embora o número seja ligeiramente menor para o regressor, o placar pareado é 5 melhores, 3 piores e 28 empates em 36 instâncias; os IC95 bootstrap se sobrepõem amplamente. Isso não demonstra superioridade operacional.

O intervalo bootstrap foi calculado reamostrando os 36 regrets por instância. Ele resume a variabilidade entre as instâncias observadas, mas não incorpora integralmente a incerteza de treinamento/seleção do modelo. Além disso, os 36 folds LOO têm conjuntos de treino fortemente sobrepostos. Portanto, os ICs não devem ser interpretados como substitutos de um holdout independente.

A relação de 35 preditores para apenas 36 instâncias independentes é desfavorável. O RF pode estar sujeito a alta variância e o piloto não permite estimar com confiança o desempenho em novas famílias/dimensões. Aumentar seeds não corrige essa limitação estrutural; se a extensão continuar, a prioridade deve ser ampliar a diversidade de instâncias.

## 4. Interpretação

1. **RF classifier piora** o regret vs sempre Fuzzy.
2. **RF regressor empatou** Fuzzy (quase o mesmo regret médio; 28 empates pareados). Sem ganho operacional útil.
3. Accuracy baixa e rótulos instáveis batem com o piloto: classificação de “vencedor” é frágil quando a margem é &lt; 0,5%.
4. Surrogate fixo continua o pior seletor de qualidade neste protocolo (orçamento desigual permanece explícito).

Conclusão honestamente delimitada: **no piloto 36×3×4, não há evidência de que Meta-Learning selecione melhor que sempre Fuzzy.** Isso não prova impossibilidade em meta-base maior; só bloqueia alegação de benefício com estes dados.

## 5. O que este relatório não autoriza

- generalização confirmatória;
- promoção de Fuzzy como ótimo universal fora da amostra;
- expansão silenciosa de seeds/instâncias sem decisão de Fase 5;
- retuning de Surrogate/RF consultando holdout inexistente.

## 6. Reprodução

```bash
python -m scripts.evaluate_meta_learning_selectors_pilot \
  --freeze-dir experiments/meta_learning/data/metabasis_pilot_v1 \
  --output results/meta_learning_metabasis_pilot_v1/selector_eval_recheck_20261127 \
  --seed 0 --random-repeats 100
```

**Recheck 2026-11-27 (aprovado):**

| Item | Valor |
|---|---|
| `summary.json` SHA-256 | `218c448f80f4f16a2aab7afca43a511665420824c2f0484328ef4351ec70a2ba` (idêntico) |
| predictions SHA-256 | `68edebba8e9e61c95b28e585f58687512cd22fef2adc4bd337c21a40fa14ae0d` (idêntico) |
| Ambiente | Python 3.14.6; NumPy 2.5.1; pandas 2.3.3; scikit-learn 1.9.0 |
| Freeze | 4/4 hashes OK; não regenerado |

Detalhes: [relatório A–D](2026-11-27-meta-learning-reproduction-ad.md).

Docs relacionados:

- [Status das fases](2026-11-27-meta-learning-phase-status.md)
- [Freeze metabasis_pilot_v1](../decisions/2026-11-27-metabasis-pilot-v1-freeze.md)
- [Roadmap](../plans/2026-11-27-meta-learning-completion-roadmap.md)
- [Runbook](2026-11-27-meta-learning-next-execution-runbook.md)

Próximo passo: decisão formal Fase 5 (continuar / encerrar / reformular). Nenhuma opção pré-selecionada.
