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

## Decisões-chave

1. Não trocar MLP da variante Surrogate; ranking real em trajetórias GWO permanece fraco.
2. Extrator `taillard_pfsp_features_v1` congelado; preditores só da matriz P.
3. Expansão para 36 instâncias (3 por grupo) baixada do espelho PISCO; custo viável no hardware local.
4. Não iniciar 60/120 nem treino meta-modelo até o piloto 36×3×4 fechar e auditar.

## Comandos de verificação

```bash
python -m scripts.validate_gwo_populations_csv
python -m scripts.analyze_gwo_population_distribution
python -m scripts.evaluate_surrogate_on_gwo_populations
python -m pytest -q tests/test_meta_learning_features.py tests/test_gwo_population_deduplicate.py tests/test_week6_surrogate.py
python -m scripts.run_meta_learning_metabasis_pilot
```
