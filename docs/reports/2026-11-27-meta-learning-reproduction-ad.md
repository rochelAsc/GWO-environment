# Reprodução A–D do piloto Meta-Learning — 2026-11-27

**Status:** aprovada  
**Decisão Fase 5:** pendente (não tomada neste documento)  
**Runbook seguido:** [2026-11-27-meta-learning-next-execution-runbook.md](2026-11-27-meta-learning-next-execution-runbook.md)

## 1. Objetivo

Reproduzir de forma independente o freeze `metabasis_pilot_v1` e a avaliação LOO exploratória, sem regenerar o freeze e sem sobrescrever `selector_eval_exploratory_v1/`. Esta rodada não autoriza expansão nem encerra a extensão: só fecha o gate de reprodutibilidade antes da decisão formal.

## 2. Ambiente e repositório

| Item | Valor |
|---|---|
| Branch | `recovery/surrogate-learning-curve-v2-oom` |
| HEAD | `b5456d1f20523aca267c03ca379e58b3406c38fc` |
| Commits recentes | `b5456d1`, `5dec18e` |
| Working tree no início | limpa (`git status --short` vazio) |
| Python | 3.14.6 (MSC v.1944, win_amd64) |
| NumPy | 2.5.1 |
| pandas | 2.3.3 |
| scikit-learn | 1.9.0 |

## 3. Etapa A — testes

Comando:

```bash
python -m pytest -q tests/test_meta_learning_features.py tests/test_meta_learning_metabasis_pilot.py tests/test_gwo_population_deduplicate.py tests/test_week6_surrogate.py
```

Resultado: **29 passed**.  
Warnings: 2 de dependências externas (`anyio` CallSpec2; `dateutil.utcfromtimestamp`). Nenhum falhou.

## 4. Etapa B — hashes do freeze

Diretório: `experiments/meta_learning/data/metabasis_pilot_v1/`  
Freeze **não** regenerado.

| Arquivo | SHA-256 | Status |
|---|---|---|
| `instance_features.csv` | `0d4a7c4435596bc867ab69ac5624e81e82ccc78a33eb1c27b8ffc82bc2cd80a1` | OK |
| `per_instance_targets.csv` | `2891dc6c29bbbcfdb37237390cd5169b76723112f44e877bb0a656e72f422a35` | OK |
| `instance_manifest.csv` | `e5ecc06260339b8b401697aea9b09f0d4a0b3e1386f573bd6ee9d5ce7ae8c796` | OK |
| `runs.csv` | `177bd3ef67b382863f9ff71f46e69a01794aea840b5d84a58687d0bc086b744f` | OK |

Manifesto: schema `metabasis_pilot_v1`; 36 instâncias; 432 runs; `taillard_pfsp_features_v1`; 35 preditores.

## 5. Etapa C — LOO em diretório novo

Comando:

```bash
python -m scripts.evaluate_meta_learning_selectors_pilot \
  --freeze-dir experiments/meta_learning/data/metabasis_pilot_v1 \
  --output results/meta_learning_metabasis_pilot_v1/selector_eval_recheck_20261127 \
  --seed 0 --random-repeats 100
```

Comparação com o publicado:

| Artefato | Publicado | Recheck | SHA-256 | Igual? |
|---|---|---|---|---|
| `summary.json` | `selector_eval_exploratory_v1/` | `selector_eval_recheck_20261127/` | `218c448f80f4f16a2aab7afca43a511665420824c2f0484328ef4351ec70a2ba` | sim |
| `per_instance_predictions.csv` | idem | idem | `68edebba8e9e61c95b28e585f58687512cd22fef2adc4bd337c21a40fa14ae0d` | sim |

Métricas-chave reproduzidas:

| Métrica | Valor |
|---|---:|
| n instâncias / folds | 36 |
| accuracy RF classifier | 0,2222 |
| accuracy RF regressor | 0,4722 |
| regret médio always Fuzzy | 0,0029187 |
| regret médio RF regressor | 0,0029053 |
| regret médio RF classifier | 0,0052324 |
| RF regressor vs Fuzzy (↑/↓/=) | 5 / 3 / 28 |

Registro machine-readable:  
`results/meta_learning_metabasis_pilot_v1/selector_eval_recheck_20261127/reproduction_record.json`

## 6. Etapa D — versões

Já listadas na §2. Sem divergência de ambiente relevante para a bit-identidade dos artefatos LOO.

## 7. O que esta reprodução confirma

1. Freeze íntegro e imutável sob os hashes publicados.
2. Avaliação LOO determinística neste ambiente (seed 0, 100 sorteios aleatórios/fold).
3. Conclusão exploratória permanece: **RF não demonstra ganho operacional útil vs sempre Fuzzy**.
4. Nenhuma evidência nova autoriza Fase 5 por si só.

## 8. O que esta reprodução não faz

- não regenera `metabasis_pilot_v1`;
- não executa novas variantes GWO;
- não expande para 60/120 instâncias nem aumenta seeds;
- não faz tuning/seleção de features;
- **não escolhe** entre continuar, encerrar ou reformular.

## 9. Decisão ainda pendente

Após este relatório, a decisão formal deve ser registrada em um dos três caminhos do runbook §8:

1. Continuar com expansão de instâncias (`metabasis_v2` + holdout pré-reservado).
2. Encerrar a extensão como exploratória sem ganho demonstrado.
3. Reformular a pergunta com novo protocolo.

Até essa decisão existir como documento/decisão versionada, a Fase 5 permanece bloqueada.

## 10. Documentos atualizados em conjunto

- [Status das fases](2026-11-27-meta-learning-phase-status.md)
- [Runbook](2026-11-27-meta-learning-next-execution-runbook.md)
- [Relatório LOO](2026-11-27-meta-learning-selector-loo-exploratory.md)
- [Freeze decision](../decisions/2026-11-27-metabasis-pilot-v1-freeze.md)
- [Roadmap](../plans/2026-11-27-meta-learning-completion-roadmap.md)
- [README Meta-Learning](../../experiments/meta_learning/README.md)
