# Semana 2 — estado da reconstrução experimental

**Data da atualização:** 2026-11-23  
**Base:** reconstrução Taillard/PFSP na branch `main`.  
**Relação com a auditoria inicial:** este documento complementa `2026-11-22-week2-implementation-review.md`; não altera a caracterização do código e dos resultados históricos.

## 1. Decisão

A Semana 2 foi refeita como experimento novo e versionado, pois os documentos antigos específicos não estão disponíveis. A ausência desses documentos não impediu a reconstrução: o roteiro do professor, a implementação histórica, o repositório e o conjunto Taillard permitiram definir um protocolo explícito.

A reconstrução usa PFSP de uma fábrica, sem due dates, e minimiza makespan. Ela não substitui os experimentos PFS com tardiness nem os experimentos DPFSP-DD.

## 2. Artefatos

- `data/benchmarks/taillard/ta001.txt` e `ta011.txt`: duas instâncias Taillard.
- `scripts/pfs_taillard.py`: parser e avaliador de makespan.
- `scripts/gwo_pfs.py`: GWO com random keys e atualização síncrona.
- `scripts/run_week2_benchmark.py`: executor reproduzível com CSVs e metadados.
- `scripts/plot_week2_convergence.py`: gráficos de média ± desvio padrão.
- `tests/test_week2_pfs_gwo.py`: testes do parser, decoder, avaliador, determinismo e orçamento.
- `docs/reports/week2_reconstruction_protocol.md`: formulação, parâmetros e orçamento.
- `docs/reports/week2_results_analysis.md`: análise dos resultados completos.
- `results/week2_pilot/`: piloto preservado.
- `results/week2_baseline_v1/`: bateria completa, metadados, dados brutos e gráficos.

## 3. Protocolo executado

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
| Total | 60 execuções; 901.800 avaliações |

Os UB/LB que acompanham as instâncias são referências publicadas. A diferença em relação ao UB não é chamada de gap para o ótimo provado.

## 4. Validação automatizada

O GitHub Actions executou a suíte completa na revisão `ac3fcbe6f03bb02a907d838679a6445f1c31da8b` com Python 3.12:

- **73 testes passaram**.
- Inclui os testes novos de Semana 2.
- Execução do CI: https://github.com/rochelAsc/GWO-environment/actions/runs/45095139046

Durante a reconstrução, o primeiro teste do parser identificou que o espelho Taillard armazena seed/UB/LB em comentário. O parser foi corrigido para ler essa metadata; a suíte subsequente passou. As falhas de CI nos commits intermediários pertencem a revisões anteriores à correção e permanecem no histórico do Actions.

## 5. Execução experimental concluída

O piloto foi executado com 3 seeds, 10 lobos e 50 iterações. Em seguida, a bateria completa foi executada com 30 seeds, 30 lobos e 500 iterações.

Resultados agregados:

| Métrica | ta001 | ta011 |
|---|---:|---:|
| Execuções | 30 | 30 |
| Média | 1265,97 | 1628,53 |
| Mediana | 1265 | 1626 |
| Desvio padrão amostral | 3,55 | 8,22 |
| Melhor | 1265 | 1596 |
| Pior | 1279 | 1644 |
| UB publicado | 1278 | 1582 |
| Tempo médio por execução | 0,861 s | 1,351 s |

Na ta001, 28 das 30 execuções atingiram makespan igual ou inferior ao UB publicado. Na ta011, nenhuma atingiu o UB; a melhor ficou 14 unidades acima dele. Portanto, o desempenho depende da instância e não deve ser apresentado como igualmente forte nas duas.

A convergência média do melhor resultado por execução caiu de 1400,50 para 1265,97 na ta001 (redução de 9,61%) e de 1875,60 para 1628,53 na ta011 (redução de 13,17%). A média da ta001 alcançou o UB na geração 135; a média da ta011 não o alcançou em 500 iterações.

A análise detalhada, limitações e links para os artefatos estão em `docs/reports/week2_results_analysis.md`.

## 6. Verificações dos artefatos

- `runs.csv`: 60 registros, 30 por instância.
- `convergence.csv`: 1.002 registros, 501 gerações por instância.
- `metadata.json`: protocolo, ambiente, seeds, hashes, limites publicados e estatísticas.
- Duas figuras de convergência.
- Cada execução registrou 15.030 avaliações; total calculado: 901.800.
- Os hashes das instâncias na bateria completa coincidem com os do piloto.
- Os resultados do piloto foram preservados, sem sobrescrita.

## 7. Conclusão e estado

**Semana 2 concluída.** A reconstrução experimental foi implementada, testada em CI, executada em escala completa e registrada no repositório com dados brutos, metadados, convergência e análise.

A conclusão deve manter a diferença observada entre as instâncias: resultado consistente em relação ao UB na ta001 e distância ainda não eliminada na ta011. O experimento é um baseline de PFSP/makespan e não substitui os resultados históricos de PFS/tardiness ou DPFSP-DD.

A próxima etapa do roteiro poderá começar após a revisão desta análise, sem misturar os objetivos e protocolos das diferentes formulações.
