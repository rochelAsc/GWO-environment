# Plano de execução — Semana 6

**Status:** implementação, bateria completa e auditoria experimental concluídas; preparação da apresentação/artigo permanece pendente.  
**Decisão:** [Benchmarking comparativo e Surrogate assistido](../docs/decisions/2026-11-25-week6-surrogate-assisted-evaluation.md).  
**Protocolo:** [Benchmark comparativo da Semana 6](../docs/reports/week6_benchmark_protocol.md).

## Relação com o planejamento anterior

Os arquivos `tasks/plan.md` e `tasks/todo.md` são preservados sem alterações. Eles registram o planejamento inicial do projeto, inclusive escolhas que foram revistas durante as auditorias e reconstruções. Este documento é um plano incremental específico para a Semana 6, não uma substituição retroativa.

A evolução entre o planejamento inicial e o protocolo executado deverá ser explicada na apresentação final: decisões iniciais, evidências que motivaram revisões, correções de implementação e protocolo consolidado.

## Objetivo

Comparar Baseline, Optuna, Surrogate assistido e Fuzzy no PFSP/Taillard (`ta001`, `ta011`), com 30 seeds por instância, análise de qualidade, custo computacional e testes estatísticos. Não misturar estes resultados com PFS/tardiness ou DPFSP-DD.

## Fase 1 — Inventário e contratos

- [x] Confirmar parâmetros congelados do Optuna v2 em `results/week3_optuna_v2/best_params.json`.
- [x] Confirmar artefatos, hashes e metadados dos modelos da Semana 4.
- [x] Confirmar parâmetros e contrato de execução do Fuzzy v2.
- [x] Definir interfaces comuns para resultados, convergência e instrumentação de tempo.
- [x] Confirmar dependências estatísticas disponíveis no ambiente/CI.
- [x] Registrar os hashes das instâncias e dos modelos no manifesto do benchmark.

**Checkpoint 1:** entradas e parâmetros identificados; nenhuma execução iniciada com configuração ambígua.

## Fase 2 — Implementar e testar o Surrogate assistido

- [x] Criar solver separado para GWO assistido, sem alterar Baseline, Optuna ou Fuzzy.
- [x] Reutilizar o decoder e a extração de features da Semana 4.
- [x] Avaliar exatamente a população inicial (30).
- [x] Em cada geração, prever em lote os 30 candidatos e reavaliar exatamente os três melhores previstos.
- [x] Atualizar líderes, melhor solução e convergência apenas com fitness exato.
- [x] Registrar previsões, seleção top-3, reavaliações, duplicatas, tempo de inferência e tempo de avaliação exata.
- [x] Testar contadores: 1.530 avaliações exatas e 15.000 previsões por execução.
- [x] Testar determinismo, clipping, ranking top-3 e isolamento do arquivo de líderes contra fitness previsto.
- [x] Testar que o modelo permanece congelado (solver não chama treino/fit).

**Checkpoint 2:** testes unitários e de integração aprovados; nenhuma previsão pode aparecer como resultado real.

## Fase 3 — Runner e instrumentação

- [x] Criar runner único para as quatro variantes e duas instâncias.
- [x] Congelar seeds 0–29 e parâmetros definidos no protocolo.
- [x] Medir tempo total, avaliação exata, inferência e preparação do Surrogate separadamente.
- [x] Reutilizar os modelos da Semana 4; registrar caminho e SHA-256.
- [x] Implementar persistência incremental e validação de combinações ausentes/duplicadas.
- [x] Gerar CSVs brutos, logs de seleção Surrogate e JSON de metadados.
- [x] Implementar retomada sem duplicar execuções concluídas.

**Checkpoint 3:** runner validado em poucas seeds e resultados reproduzíveis.

## Fase 4 — Piloto e bateria integral

- [x] Executar piloto curto nas duas instâncias, com seeds explicitamente identificadas.
- [x] Auditar contadores, integridade dos CSVs, convergência e custos.
- [x] Corrigir problemas encontrados sem sobrescrever artefatos do piloto.
- [x] Executar a bateria completa: 4 variantes × 2 instâncias × 30 seeds = 240 execuções.
- [x] Conferir 15.030 avaliações exatas por execução nas variantes Baseline/Optuna/Fuzzy.
- [x] Conferir 1.530 avaliações exatas e 15.000 previsões por execução Surrogate.
- [x] Confirmar total de 2.797.200 avaliações exatas na busca e 4.000 rótulos exatos de preparação já gerados na Semana 4 (2.801.200 incluindo preparação).

**Checkpoint 4:** conjunto bruto completo, auditável e sem combinações faltantes.

## Fase 5 — Análise e auditoria

- [x] Gerar média, mediana, desvio padrão, mínimo, máximo e hits do upper bound por instância/variante.
- [x] Gerar curvas de convergência em CSV; gráficos comparativos independentes não foram incluídos na bateria.
- [x] Executar Friedman por instância.
- [x] Executar seis Wilcoxon pareados por instância e correção de Holm.
- [x] Reportar p-values brutos/ajustados e diferenças pareadas.
- [x] Separar custo de preparação e custo de busca; custo amortizado é discutido qualitativamente na auditoria.
- [x] Criar relatório de auditoria com limitações e conclusões estritamente suportadas pelos dados.

**Checkpoint 5:** relatório regenerável diretamente dos dados brutos.

## Fase 6 — Qualidade e entrega

- [x] Executar testes completos e CI.
- [x] Revisar código e documentação sem alterar resultados históricos.
- [x] Atualizar README com comandos e limites da Semana 6.
- [x] Publicar protocolo, código, testes, dados e auditoria em commits rastreáveis; gráficos comparativos independentes não foram publicados.
- [ ] Preparar material para a apresentação: linha do tempo de decisões, mudanças de escopo, bug encontrado, reexecuções e justificativas metodológicas.

## Artefatos esperados

- `scripts/gwo_pfs_surrogate.py`
- `scripts/run_week6_benchmark.py`
- `tests/test_week6_surrogate.py`
- `tests/test_week6_benchmark.py`
- `results/week6_benchmark_pilot_v1/`
- `results/week6_benchmark_v1/`
- `docs/audits/2026-11-25-week6-benchmark-audit.md`
- Atualização do README e, se necessário, documentação da apresentação.

## Regras de preservação

- Não editar `tasks/plan.md` nem `tasks/todo.md` como parte desta fase.
- Não sobrescrever resultados das Semanas 2–5.
- Não retunar Optuna nem ajustar Fuzzy/Surrogate usando os resultados finais.
- Não chamar predições de makespan real.
- Não declarar igualdade de orçamento entre Surrogate e as outras variantes.
- Não afirmar significância estatística quando os testes corrigidos não sustentarem a conclusão.
