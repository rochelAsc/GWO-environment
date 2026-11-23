# Semana 2 — estado da reconstrução experimental

**Data:** 2026-11-23  
**Base:** reconstrução Taillard/PFSP adicionada à branch `main`.  
**Relação com a auditoria inicial:** este documento complementa `2026-11-22-week2-implementation-review.md`; não altera a caracterização do código e dos resultados históricos.

## 1. Decisão

A Semana 2 será refeita como experimento novo e versionado, pois os documentos antigos específicos não estão disponíveis. A ausência desses documentos não impede a reconstrução: o roteiro do professor, a implementação histórica, o repositório e o conjunto Taillard permitem definir um protocolo explícito.

A reconstrução usa PFSP de uma fábrica, sem due dates, e minimiza makespan. Ela não substitui os experimentos PFS com tardiness nem os experimentos DPFSP-DD.

## 2. Artefatos adicionados

- `data/benchmarks/taillard/ta001.txt`
- `data/benchmarks/taillard/ta011.txt`
- `scripts/pfs_taillard.py`: parser e avaliador de makespan.
- `scripts/gwo_pfs.py`: GWO com random keys e atualização síncrona.
- `scripts/run_week2_benchmark.py`: executor reproduzível com CSVs e metadados.
- `scripts/plot_week2_convergence.py`: gráfico de média ± desvio padrão.
- `tests/test_week2_pfs_gwo.py`: testes do parser, decoder, avaliador, determinismo e orçamento.
- `docs/reports/week2_reconstruction_protocol.md`: formulação, parâmetros e orçamento.
- README: comandos de piloto e execução completa.

## 3. Protocolo congelado para a nova bateria

| Parâmetro | Valor |
|---|---:|
| Instâncias | ta001 (20×5), ta011 (20×10) |
| Objetivo | Makespan |
| Codificação | n random keys em [0,1], argsort estável |
| Lobos | 30 |
| Iterações | 500 |
| Schedule de a | Linear de 2 a 0 |
| Seeds | 0–29 |
| Atualização | Síncrona, líderes congelados por geração |
| Avaliações por execução | 15.030 |
| Total previsto | 60 execuções; 901.800 avaliações |

Os UB/LB que acompanham as instâncias são registrados como referências publicadas. O gap em relação ao UB não será chamado de gap para o ótimo provado.

## 4. Validação automatizada

O GitHub Actions executou a suíte completa na revisão `ac3fcbe6f03bb02a907d838679a6445f1c31da8b` com Python 3.12:

- **73 testes passaram**.
- Inclui os testes novos de Semana 2.
- Execução do CI: https://github.com/rochelAsc/GWO-environment/actions/runs/45095139046

Durante a reconstrução, o primeiro teste do parser identificou que o espelho Taillard armazena seed/UB/LB em comentário. O parser foi corrigido para ler essa metadata; a suíte subsequente passou. As falhas de CI nos commits intermediários pertencem a revisões anteriores à correção e permanecem no histórico do Actions.

## 5. O que ainda falta para concluir a Semana 2

A suíte automatizada valida componentes e reprodutibilidade em pequena escala; ela não equivale à execução experimental de 30 seeds × 500 iterações.

Etapas pendentes:
1. Executar o piloto curto recomendado no README para medir tempo e verificar arquivos de saída na máquina local.
2. Conferir os CSVs e o gráfico de convergência do piloto.
3. Executar a bateria final de 30 seeds nas duas instâncias.
4. Registrar os resultados brutos e metadados em `results/week2_baseline_v1/`.
5. Atualizar a análise com média, mediana, desvio padrão, melhor/pior resultado, distância ao UB publicado e comportamento de convergência.

Até que a bateria seja executada e os resultados sejam verificados, a reconstrução está **implementada e testada em CI, mas experimentalmente pendente**.

## 6. Comandos

Piloto:
```bash
python -m scripts.run_week2_benchmark --seeds 3 --wolves 10 --iterations 50 --output results/week2_pilot
```

Bateria:
```bash
python -m scripts.run_week2_benchmark
python -m scripts.plot_week2_convergence
```
