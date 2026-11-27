# S-A0 — auditoria de entrada (Surrogate + Meta-Learning)

**Data:** 2026-11-27  
**Branch:** `recovery/surrogate-learning-curve-v2-oom`  
**Commit:** `8c276c9563adbb0779596cf5cd786a35921cec55`  
**Status:** **aprovado com ressalvas** — hashes de instância/split/freeze OK; layout da extensão incompleto no diretório raiz.

## Ambiente

| Item | Valor |
|---|---|
| Python local | 3.14.6 |
| numpy / sklearn / pandas | 2.5.1 / 1.9.0 / 2.3.3 |
| Disco livre (C:) | ≈ 15,4 GB |
| Working tree | `.gitignore` modificado; `.cursorignore` untracked (não toca artefatos experimentais) |

Metadados históricos da curva usam Python 3.12.3. Diferença de ambiente local é aceitável para auditoria/código; baterias novas devem registrar o ambiente no próprio metadata.

## Surrogate

| Artefato | Resultado |
|---|---|
| `results/..._v2_full/` | Presente: `metadata.json`, `learning_curve_runs.csv`, `learning_curve_summary.csv`, `ta071/`, `ta111/` |
| `results/..._v2_extension/` | Presente: NPZs + `fixed_test_set.npz` (59 NPZ, ≈415 MB). **Sem** `metadata.json` / `learning_curve_*.csv` na raiz |
| `results/..._v2_extension_recovered/` | Presente: `recovered_runs.csv`, `recovery_metadata.json`, `recovered_runs.jsonl`; 3 NPZ residuais |
| SHA-256 `ta071.txt` | OK vs metadata full e split v2 (`763dcae3…f7d9`) |
| SHA-256 `ta111.txt` | OK (`9f51c103…5fe9`) |
| `fixed_test_set.npz` full vs extension | IDêntico (ta071 e ta111) |

**Ressalva:** a extensão não replica o layout CSV do full; a recuperação documentada em `recovery_metadata.json` (60 records; sizes 8k/16k/32k) é a fonte tabular. Não regenerar NPZs.

## Meta-Learning

| Artefato | Resultado |
|---|---|
| Freeze `metabasis_pilot_v1/` | 4/4 hashes SHA-256 OK |
| Split `metabasis_v2/split_manifest.csv` | SHA-256 `c17bce8856f6e22b35db6e7ad2b43b84ca82df3632f245fbeb7a909ad36a934a` |
| Checkpoint 60 development | 576 runs; 48 instâncias; `partition=development` apenas |
| Holdout stage=60 | **selado** (0 linhas holdout em `development_runs.csv`) |
| Fontes | 432 `pilot_v1_reused` + 144 `metabasis_v2_new` |

## Gate

- Nenhuma divergência de hash de instância Taillard ou freeze piloto.
- Split e holdout intactos.
- Prosseguir para **S-A1** (métricas top-k).
- **Não** iniciar M-B1 (stage=120) sem decisão formal B0 em `docs/decisions/`.
- **Não** iniciar S-A2 completa até A1 fechar e um smoke cell validar RSS/tempo.

## Comandos usados

```bash
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
python -m pytest -q tests/test_meta_learning_metabasis_v2_split.py tests/test_meta_learning_metabasis_v2_runner.py
```
