# Decisão: congelar o extrator de características de instância

**Data:** 2026-11-27  
**Status:** aprovada  
**Gate:** Fase 3 do roadmap de Meta-Learning

## Decisão

Congelar `FEATURE_VERSION = taillard_pfsp_features_v1` em  
`experiments/meta_learning/scripts/extract_instance_features.py`.

Regras:
1. Features só da matriz de tempos de processamento (inteiros positivos).
2. Metadados `instance`, `sha256`, `feature_version` não entram como preditores.
3. Não usar makespan, UB/LB, seed, caminho ou resultado de algoritmo como feature.
4. Qualquer normalização/seleção aprendida ocorre **dentro** dos folds de treino, nunca no dataset completo.
5. Mudança de schema gera nova `FEATURE_VERSION`; não sobrescrever silenciosamente.

## Artefato

Regenerado em 2026-11-27 a partir de 36 instâncias Taillard:

```bash
python -m experiments.meta_learning.scripts.extract_instance_features \
  --input-dir data/benchmarks/taillard \
  --output experiments/meta_learning/data/instance_features.csv
```

35 colunas preditivas + 3 metadados. Testes: `tests/test_meta_learning_features.py` (determinismo, rejeição de inválidos, invariância a caminho, 12+ grupos Taillard).
