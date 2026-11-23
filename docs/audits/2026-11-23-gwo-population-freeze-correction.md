# Auditoria crítica — correção da população congelada no GWO

**Data:** 2026-11-23  
**Versão corrigida:** GWO PFSP v2  
**Status:** correção implementada e CI aprovada; reexecuções experimentais pendentes.

## 1. Defeito identificado

Nas versões anteriores de `scripts/gwo_pfs.py` e `scripts/gwo_pfs_fuzzy.py`, cada geração calculava `new_positions` e avaliava seus indivíduos, mas não executava a substituição `positions = new_positions`. Consequentemente, a população usada como origem das atualizações permanecia sendo a população inicial durante todas as iterações.

Os líderes alpha, beta e delta eram atualizados e preservados em um arquivo de elite, mas isso não corrigia o problema: os demais lobos nunca passavam a ocupar as posições calculadas na geração anterior. A implementação, portanto, não realizava a evolução populacional iterativa pretendida.

No GWO Fuzzy havia um efeito adicional: `population_diversity(positions)` era calculada sobre a população congelada. O traço do piloto v1 confirmou um único valor de diversidade em todas as 500 gerações de cada execução. Assim, o controlador não recebia uma medida dinâmica da diversidade.

## 2. Impacto nos experimentos

| Etapa | Impacto |
|---|---|
| Semana 2 — baseline v1 | Resultados não representam GWO com população evolutiva. |
| Semana 3 — Optuna v1 | Tanto o tuning quanto a avaliação final otimizaram/avaliaram o solver defeituoso. |
| Semana 5 — Fuzzy v1 | Solver defeituoso e entrada de diversidade congelada; piloto não valida adaptação baseada em diversidade. |
| Semana 4 — surrogate | Não afetada: dataset e rótulos são gerados por amostras de random keys e avaliador exato, sem depender da dinâmica GWO. |
| Histórico PFS/tardiness e DPFSP-DD | Não se deve presumir impacto: são implementações/experimentos separados. |

Os resultados v1 permanecem no repositório para rastreabilidade. Não devem ser apagados nem apresentados como resultados válidos do GWO iterativo. Suas conclusões experimentais ficam supersedidas pelas reexecuções v2.

## 3. Correção implementada

Em ambos os motores, após avaliar a nova população e atualizar o arquivo de líderes, a implementação agora executa:

```python
positions = new_positions
```

Os três líderes continuam congelados durante cada geração e são mantidos em um arquivo de elite separado. A atualização da população é síncrona: todos os novos indivíduos são calculados a partir da mesma população anterior e dos mesmos líderes daquela geração; só depois a população inteira avança.

O `GWOResult` expõe a população final para permitir um teste de regressão de que ela não permaneceu igual à inicial. Isso evita adicionar cálculo quadrático de diversidade ao loop do GWO padrão. No Fuzzy, a diversidade é recalculada no início de cada geração a partir da população já atualizada.

## 4. Testes de regressão e CI

Foram adicionados testes que verificam:
- a população final do GWO padrão difere da população inicial para uma execução determinística de teste;
- a diversidade observada pelo Fuzzy varia entre gerações em uma execução determinística;
- reprodutibilidade, monotonicidade do melhor histórico e orçamento de avaliações continuam validados.

GitHub Actions:
- Run: [45104636797](https://github.com/rochelAsc/GWO-environment/actions/runs/45104636797)
- Commit testado: `e5d1c34cafa7be51c9249db89b2809e4331c3c44`
- Python: 3.12
- Compilação: 25 fontes Python convencionais compiladas.
- Suíte: **100 passed**.

A CI valida sintaxe e testes automatizados; não equivale à execução das baterias experimentais.

## 5. Reexecuções obrigatórias

Executar em sequência, preservando todos os diretórios v1:

1. Semana 2: `python -m scripts.run_week2_benchmark --output results/week2_baseline_v2`
2. Gerar gráficos: `python -m scripts.plot_week2_convergence --input results/week2_baseline_v2/convergence.csv --output results/week2_baseline_v2/figures`
3. Semana 3 tuning: `python -m scripts.tune_week3_optuna --output results/week3_optuna_v2`
4. Semana 3 avaliação: `python -m scripts.run_week3_evaluation --config results/week3_optuna_v2/best_params.json --baseline results/week2_baseline_v2/runs.csv --output results/week3_optuna_v2`
5. Semana 5 piloto: `python -m scripts.run_week5_fuzzy --seeds 0 1 2 --baseline results/week2_baseline_v2/runs.csv --tuned results/week3_optuna_v2/final_runs.csv --output results/week5_fuzzy_pilot_v2`

O piloto Fuzzy deve ser inspecionado antes de qualquer bateria de 30 seeds. Verificar, em especial, se a diversidade não está constante ao longo das gerações, se o número de avaliações permanece em 15.030 por execução e se as comparações usam os resultados v2.

## 6. Estado após a correção

- [x] Corrigir população no GWO padrão.
- [x] Corrigir população no GWO Fuzzy.
- [x] Adicionar testes contra população/diversidade congeladas.
- [x] CI: 100 testes aprovados.
- [x] Versionar novos caminhos de saída v2 e atualizar protocolos.
- [ ] Executar a nova bateria Semana 2 (30 seeds).
- [ ] Executar novo tuning e avaliação Semana 3.
- [ ] Executar e inspecionar novo piloto Semana 5.
- [ ] Atualizar análises e auditorias com os resultados v2.
- [ ] Só então decidir se a bateria completa Semana 5 é justificável.

