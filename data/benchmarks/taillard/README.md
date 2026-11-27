# Taillard PFSP benchmark — inventário para Meta-Learning

Este diretório contém o inventário completo de **120 instâncias** (10 por grupo × 12 grupos), obtido do espelho PISCO. As **36** instâncias do piloto metabasis_pilot_v1 permanecem intactas (hashes revalidados). O split pré-registrado da expansão v2 está congelado e **não** deve ser regenerado após inspeção de resultados.

## Cobertura versionada (120)

| Grupo | Instâncias |
|---|---|
| 20×5 | ta001–ta010 |
| 20×10 | ta011–ta020 |
| 20×20 | ta021–ta030 |
| 50×5 | ta031–ta040 |
| 50×10 | ta041–ta050 |
| 50×20 | ta051–ta060 |
| 100×5 | ta061–ta070 |
| 100×10 | ta071–ta080 |
| 100×20 | ta081–ta090 |
| 200×10 | ta091–ta100 |
| 200×20 | ta101–ta110 |
| 500×20 | ta111–ta120 |

Piloto (development, `stage=pilot_v1`): 3 primeiras de cada grupo (`ta001–003`, `ta011–013`, …, `ta111–113`).

## Split congelado (metabasis_v2)

- Seed: `20261127`
- Manifesto: `experiments/meta_learning/data/metabasis_v2/split_manifest.csv`
- SHA-256: `c17bce8856f6e22b35db6e7ad2b43b84ca82df3632f245fbeb7a909ad36a934a`
- Relatório: [Fase A](../../../docs/reports/2026-11-27-meta-learning-v2-phase-a-inventory-split.md)

Checkpoint 60 — novas development:  
`ta007, ta015, ta029, ta038, ta049, ta058, ta067, ta077, ta087, ta094, ta109, ta116`

Checkpoint 60 — holdout selado:  
`ta004, ta019, ta027, ta039, ta046, ta059, ta065, ta076, ta088, ta095, ta110, ta119`

## Proveniência

- Benchmark: Taillard (1993), *Benchmarks for basic scheduling problems*, European Journal of Operational Research, 64(2), 278–285. DOI: https://doi.org/10.1016/0377-2217(93)90182-M
- Source mirror: [PISCO Taillard PFSP instances](https://github.com/arnaud-m/pisco/tree/master/pisco-shop/src/main/benchmarks/instances/flow-shop/taillard)
- Arquivos no formato original. Parser lê dimensões, tempos e, quando disponíveis, metadados de seed/upper/lower bound.
- Hash, origem e bounds são metadados de proveniência, **nunca** preditores.

Checkpoint 60 development coletado e documentado em [2026-11-27-meta-learning-v2-checkpoint60-dev.md](../../../docs/reports/2026-11-27-meta-learning-v2-checkpoint60-dev.md). Holdout listado acima permanece selado.

Não sobrescrever arquivos de benchmark existentes. Não alterar o split após observar resultados GWO.
