# Fase A metabasis_v2 — inventário 120 e split pré-registrado

**Data:** 2026-11-27  
**Status:** concluída  
**Decisão:** [2026-11-27-meta-learning-expansion-v2.md](../decisions/2026-11-27-meta-learning-expansion-v2.md)  
**HEAD da geração:** registrar no `split_summary.json` do diretório de saída

## 1. O que foi feito

1. Baixados **84** arquivos Taillard faltantes do espelho PISCO (`ta001`–`ta120` completos).
2. Revalidados os **36** hashes do piloto: OK (sem alteração dos arquivos já congelados).
3. Inventário 120 com dimensões, UB/LB e SHA-256.
4. Split determinístico `split_seed=20261127` congelado.
5. Features `taillard_pfsp_features_v1` extraídas para as 120 instâncias.

## 2. Artefatos

| Artefato | Caminho |
|---|---|
| Inventário CSV | `results/meta_learning_metabasis_v2/inventory/instance_manifest_120.csv` |
| Features 120 | `results/meta_learning_metabasis_v2/inventory/instance_features_all.csv` |
| Split (results) | `results/meta_learning_metabasis_v2/split/split_manifest.csv` |
| Split (freeze path) | `experiments/meta_learning/data/metabasis_v2/split_manifest.csv` |
| Summary | `results/meta_learning_metabasis_v2/split/split_summary.json` |
| Script | `scripts/build_meta_learning_metabasis_v2_inventory_split.py` |

Hashes (ver `split_summary.json` para valores canônicos):

- inventário e split SHA-256 gravados no summary;
- UB ausente: **nenhuma** instância.

## 3. Regra de split aplicada

- Grupos em ordem lexicográfica de `jobsxmachines`.
- Em cada grupo: 3 piloto (`stage=pilot_v1`, development) + 7 restantes.
- `numpy.random.default_rng(20261127)` consome permutações sequencialmente entre grupos.
- Dos 7: primeiros 5 = development; últimos 2 = holdout.
- Primeiro development e primeiro holdout → `stage=60`; demais → `stage=120`.
- Holdout **não** contém nenhuma das 36 do piloto.

## 4. Checkpoint 60 — listas congeladas

**Novas development (a executar):**
`ta007, ta015, ta029, ta038, ta049, ta058, ta067, ta077, ta087, ta094, ta109, ta116`

**Holdout selado (não executar/consultar targets agora):**
`ta004, ta019, ta027, ta039, ta046, ta059, ta065, ta076, ta088, ta095, ta110, ta119`

Composição do checkpoint 60: 36 piloto + 12 novas development + 12 holdout selado = 60.

## 5. Gate técnico (scripts)

Criados/testados sem sobrescrever o piloto:

- `scripts/run_meta_learning_metabasis_v2.py` — protocol `meta_learning_metabasis_v2`
- `scripts/freeze_meta_learning_metabasis_v2.py` — recusa sobrescrita
- testes: `tests/test_meta_learning_metabasis_v2_split.py`, `tests/test_meta_learning_metabasis_v2_runner.py`

## 6. Próximo passo

~~Fase B: executar as 12 development `stage=60`.~~ **Concluída** — ver [checkpoint 60 development](2026-11-27-meta-learning-v2-checkpoint60-dev.md) (576/576 runs agregados; holdout selado). Próximo: decisão formal 60→120.
