# Taillard PFSP benchmark — inventário para Meta-Learning

Este diretório contém atualmente o subconjunto de **36 instâncias** utilizado no piloto metabasis_pilot_v1 (3 instâncias em cada um dos 12 grupos de dimensão). A expansão aprovada tem como alvo o inventário completo de **120 instâncias** (10 por grupo), sujeito à validação dos arquivos e da proveniência.

## Cobertura atualmente versionada

| Grupo | Instâncias |
|---|---|
| 20×5 | ta001, ta002, ta003 |
| 20×10 | ta011, ta012, ta013 |
| 20×20 | ta021, ta022, ta023 |
| 50×5 | ta031, ta032, ta033 |
| 50×10 | ta041, ta042, ta043 |
| 50×20 | ta051, ta052, ta053 |
| 100×5 | ta061, ta062, ta063 |
| 100×10 | ta071, ta072, ta073 |
| 100×20 | ta081, ta082, ta083 |
| 200×10 | ta091, ta092, ta093 |
| 200×20 | ta101, ta102, ta103 |
| 500×20 | ta111, ta112, ta113 |

## Alvo de expansão

O inventário-alvo é 10 instâncias em cada grupo acima (120 no total). Os 36 arquivos atuais já foram usados em desenvolvimento e não podem integrar o holdout confirmatório. Antes de qualquer nova execução GWO:

1. obter os arquivos faltantes a partir da fonte espelho;
2. validar parser, dimensões, metadados/bounds e SHA-256;
3. registrar origem e proveniência de cada arquivo;
4. congelar split determinístico por grupo: das 7 instâncias ainda não usadas em cada grupo, 5 para desenvolvimento e 2 para holdout;
5. registrar seed, algoritmo e hash do manifesto de split.

A composição por estágio será 60 = 48 desenvolvimento + 12 holdout selado; 120 = 96 desenvolvimento + 24 holdout selado. Se o estudo avançar de 60 para 120, os 12 holdouts iniciais não serão consultados nem usados para decidir a expansão. Ver [decisão de expansão](../../docs/decisions/2026-11-27-meta-learning-expansion-v2.md) e [runbook](../../docs/reports/2026-11-27-meta-learning-next-execution-runbook.md).

## Proveniência

- Benchmark: Taillard (1993), *Benchmarks for basic scheduling problems*, European Journal of Operational Research, 64(2), 278–285. DOI: https://doi.org/10.1016/0377-2217(93)90182-M
- Source mirror: [PISCO Taillard PFSP instances](https://github.com/arnaud-m/pisco/tree/master/pisco-shop/src/main/benchmarks/instances/flow-shop/taillard)
- Os arquivos devem permanecer no formato original do benchmark. O parser lê dimensões, tempos de processamento e, quando disponíveis, metadados de seed/upper/lower bound.
- O extrator registra SHA-256 por arquivo. Hash, origem e bounds são metadados de proveniência, nunca preditores.

Não sobrescrever arquivos de benchmark ou resultados experimentais existentes. Novos arquivos devem ser validados e registrados; cópias corrigidas devem ser versionadas separadamente.
