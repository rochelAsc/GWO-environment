# Checkpoint 60 — desenvolvimento metabasis_v2

**Data:** 2026-11-27  
**Status:** coleta e agregação de desenvolvimento **concluídas**; holdout **selado**  
**Decisão 60→120:** pendente (somente custo/integridade; sem abrir holdout)

## 1. Escopo

| Item | Valor |
|---|---|
| Desenvolvimento | 48 instâncias (36 piloto + 12 novas `stage=60`) |
| Holdout selado | 12 instâncias `stage=60` (não executadas) |
| Seeds | `[0, 1, 2]` pareadas |
| Variantes | baseline, optuna, fuzzy, surrogate |
| Runs de desenvolvimento | **576/576** (432 `pilot_v1_reused` + 144 `metabasis_v2_new`) |
| Normalização | `ub` em 48/48 |

Instâncias novas executadas:  
`ta007, ta015, ta029, ta038, ta049, ta058, ta067, ta077, ta087, ta094, ta109, ta116`

Holdout não tocado:  
`ta004, ta019, ta027, ta039, ta046, ta059, ta065, ta076, ta088, ta095, ta110, ta119`

## 2. Artefatos

| Artefato | Caminho |
|---|---|
| Runs novos | `results/meta_learning_metabasis_v2/runs.csv` (144) |
| Runs mesclados | `results/meta_learning_metabasis_v2/checkpoint60_dev/development_runs.csv` (576) |
| Manifesto dev | `…/checkpoint60_dev/development_manifest.csv` |
| Targets | `…/checkpoint60_dev/analysis/per_instance_targets.csv` |
| Summary | `…/checkpoint60_dev/analysis/summary.json` |
| Split (imutável) | `experiments/meta_learning/data/metabasis_v2/split_manifest.csv` |
| Scripts | `run_meta_learning_metabasis_v2.py`, `build_meta_learning_metabasis_v2_checkpoint60_dev.py` |

### Hashes SHA-256

| Arquivo | SHA-256 |
|---|---|
| `development_runs.csv` | `3debe5a487ce94b274625d4d2f4f53216bd04d29065f6be3114865ef13948a2e` |
| `development_manifest.csv` | `49afdcbbb35c2e62debe75a8f94679b894cb710cd949954b213f7815a367c4cf` |
| `per_instance_targets.csv` | `9cb446ffce13e706377617eeb96a203dd8b00dd57f4dcbf360fc13bab1daf000` |
| `split_manifest.csv` | `c17bce8856f6e22b35db6e7ad2b43b84ca82df3632f245fbeb7a909ad36a934a` |

## 3. Integridade

- 0 missing / 0 extra / 0 duplicatas nas 144 chaves novas e nas 576 mescladas.
- Hashes de instância batem com o split; piloto reusado só após checagem de `instance_sha256`.
- Surrogate: `model_sha256` preenchido em todas as linhas Surrogate.
- Holdout ausente de `runs.csv` e de `development_runs.csv`.
- Freeze `metabasis_pilot_v1` não foi modificado.

## 4. Desempenho agregado (48 desenvolvimento)

Fonte: `checkpoint60_dev/analysis/summary.json`. Unidade = instância.

| Variante | Vitórias / 48 | y médio (UB) | Regret médio vs oráculo | Tempo médio (s) |
|---|---:|---:|---:|---:|
| fuzzy | **20** | **1,050** | **0,0037** | 11,19 |
| optuna | 14 | 1,053 | 0,0070 | 10,95 |
| baseline | 13 | 1,052 | 0,0057 | 10,92 |
| surrogate | 1 | 1,065 | 0,0195 | **1,86** |

Low-confidence (margem &lt; 0,5%): **30/48**.

Nas **12 novas** apenas: optuna 5, baseline 4, fuzzy 3; low-conf 8/12. Isso é descritivo do subset novo, não substitui a agregação das 48.

Pareado (48): Fuzzy continua o baseline operacional mais forte (ex.: baseline vs fuzzy 17–29; optuna vs fuzzy 18–29).

## 5. Custo observado

| Bloco | Runs | Soma runtime | Wall-clock |
|---|---:|---:|---|
| Piloto reusado (histórico) | 432 | ≈ 1,07 h | — |
| Novas stage=60 | 144 | ≈ 0,33 h | ≈ **0,33 h** (~20 min) |
| Total desenvolvimento 48 | 576 | ≈ 1,40 h | — |

Extrapolação linear simples a partir do wall-clock das 12 novas (~0,33 h):

| Próximo bloco | Runs | Estimativa wall |
|---|---:|---|
| Development restante até 120 (48 inst.) | 576 | ≈ **1,3 h** |
| Holdout final 24 (se 120) | 288 | ≈ **0,7 h** |
| Holdout 12 (se encerrar em 60) | 144 | ≈ **0,3 h** |

Estimativas, não SLA. Instâncias 500×20 e preparação Surrogate podem dominar o tempo.

## 6. O que este checkpoint autoriza / não autoriza

**Autoriza:** revisão de custo/integridade/cobertura para decidir avançar a 120 ou encerrar em 60; treino/CV **somente** nas 48 de desenvolvimento, se a decisão for usar este conjunto.

**Não autoriza:**

- abrir ou consultar targets do holdout;
- alegar evidência confirmatória de Meta-Learning;
- regenerar o split;
- misturar holdout na decisão 60↔120.

## 7. Reprodução

```bash
python -m scripts.run_meta_learning_metabasis_v2 --stages 60 --partitions development
python -m scripts.build_meta_learning_metabasis_v2_checkpoint60_dev
```

Docs: [status](2026-11-27-meta-learning-phase-status.md) · [Fase A](2026-11-27-meta-learning-v2-phase-a-inventory-split.md) · [runbook](2026-11-27-meta-learning-next-execution-runbook.md) · [decisão v2](../decisions/2026-11-27-meta-learning-expansion-v2.md)
