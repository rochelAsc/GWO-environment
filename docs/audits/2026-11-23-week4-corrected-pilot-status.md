# Auditoria da Semana 4 — Surrogate PFSP/Taillard

**Status:** execução experimental principal concluída; resultados analisados; limitações documentadas.

## 1. Escopo e preservação do histórico

A reconstrução avalia um surrogate neural para o PFSP de uma fábrica, minimizando makespan nas instâncias Taillard `ta001` (20 jobs, 5 máquinas) e `ta011` (20 jobs, 10 máquinas). Ela usa a mesma formulação e instâncias das Semanas 2 e 3. Não mistura nem substitui os experimentos históricos de PFS com due dates/tardiness.

As execuções foram preservadas em diretórios distintos:
- `results/week4_surrogate_pilot/`: piloto histórico original;
- `results/week4_surrogate_pilot_v2/`: piloto com benchmark corrigido, 300 amostras por instância;
- `results/week4_surrogate_v2/`: execução principal, 2.000 amostras por instância.

A implementação v2 preserva random keys LHS, deduplica por permutação, grava chaves e features, e mede avaliação exata e surrogate sobre as mesmas chaves brutas de teste. Os tempos incluem decodificação nos dois caminhos e codificação das features/inferência no caminho surrogate. O benchmark usa aquecimento e 30 repetições.

## 2. Dataset e protocolo executado

Por instância, a execução principal registrou:
- 2.000 permutações únicas; taxa de duplicação 0%;
- 1.600 amostras de treino e 400 de teste;
- seed `20261123`;
- LHS aplicado a random keys, seguido de stable argsort;
- features de posição dos jobs normalizadas;
- MLPRegressor com duas camadas ocultas de 64 neurônios, ReLU, Adam, alpha 0,0001 e early stopping;
- hashes das instâncias iguais aos usados nas Semanas 2 e 3.

O treinamento realizou 52 iterações em `ta001` e 69 em `ta011`. Os artefatos incluem `dataset.csv`, `metrics.json`, gráficos de previsto versus real e resíduos, e modelo serializado.

## 3. Qualidade preditiva

Métricas no conjunto de teste:

| Instância | Amostras | RMSE | MAE | R² | Spearman |
|---|---:|---:|---:|---:|---:|
| ta001 | 300 (piloto v2) | 49,68 | 39,73 | 0,523 | 0,734 |
| ta001 | 2.000 | 43,21 | 34,10 | 0,573 | 0,758 |
| ta011 | 300 (piloto v2) | 78,31 | 63,48 | -0,015 | 0,224 |
| ta011 | 2.000 | 65,94 | 51,38 | 0,252 | 0,539 |

O aumento de amostras veio acompanhado de melhora descritiva nas métricas de ambas as instâncias. O avanço mais expressivo ocorreu em `ta011`: R² passou de -0,015 para 0,252 e Spearman de 0,224 para 0,539. Em `ta001`, as melhorias foram menores.

Essa comparação entre piloto e execução principal não é pareada: os tamanhos dos conjuntos de teste diferem e as execuções usam divisões com tamanhos distintos. Portanto, não se deve atribuir causalidade ou significância estatística apenas a essas diferenças. Mesmo na execução principal, o desempenho em `ta011` é moderado; o modelo não substitui o avaliador exato.

## 4. Custo computacional

Tempos por predição, mediana de 30 repetições:

| Instância | Avaliação exata | Surrogate em lote | Surrogate individual | Speedup em lote |
|---|---:|---:|---:|---:|
| ta001 | 50,26 µs | 15,16 µs | 368,90 µs | 3,31× |
| ta011 | 83,35 µs | 15,29 µs | 361,45 µs | 5,45× |

A inferência em lote é mais rápida que a avaliação exata nesse microbenchmark. A inferência individual é mais lenta que a avaliação exata nas duas instâncias. O speedup reportado é de avaliação em lote, não do GWO completo.

Custos de preparação:
| Etapa | ta001 | ta011 |
|---|---:|---:|
| Geração do dataset e rótulos exatos | 0,142 s | 0,206 s |
| Treinamento | 0,265 s | 0,346 s |
| Total | 0,406 s | 0,553 s |

Com base nas medianas, a economia por consulta em lote é aproximadamente 35,09 µs em `ta001` e 68,06 µs em `ta011`. Dividindo o custo de preparação e treinamento por essa economia, o ponto de equilíbrio estimado é de aproximadamente 11.600 consultas em lote para `ta001` e 8.100 para `ta011`.

Esses pontos de equilíbrio são aproximações de microbenchmark. Não incluem custos de integração, gerenciamento de lotes ou reavaliação exata de candidatos. As 2.000 avaliações exatas usadas para criar cada dataset são parte do custo de preparação, não consultas gratuitas.

## 5. Seleção de candidatos e risco de falso ótimo

Entre os dez itens do conjunto de teste com menor makespan previsto:

| Métrica | ta001 | ta011 |
|---|---:|---:|
| Melhor previsão | 1384,53 | 1875,83 |
| Melhor makespan exato entre os dez | 1378 | 1810 |
| Média exata dos dez | 1434,7 | 1919,2 |
| Upper Bound publicado | 1278 | 1582 |

Nenhum dos dez candidatos alcançou o upper bound publicado. Os valores previstos não são fitness obtidos e não devem ser reportados como resultados do otimizador. Toda solução selecionada pelo surrogate deve ser reavaliada pelo makespan exato.

A seleção foi feita dentro do conjunto de teste e funciona como diagnóstico do ranking nesse conjunto; não é uma validação independente de um processo de busca integrado ao GWO. A melhora descritiva dos melhores candidatos em relação ao piloto também não constitui comparação pareada, pois os conjuntos de teste são diferentes.

## 6. Testes, CI e rastreabilidade

A implementação e os testes da v2 foram cobertos pela CI. A execução GitHub Actions do piloto corrigido (commit `ec8640d6924c543d27f70fb70e8c69d689403729`, run `45102830749`) concluiu com sucesso. A execução da versão principal de 2.000 amostras (commit `91f13bb8`, run `45103486452`) também concluiu com sucesso. A atualização desta auditoria gerou o run `45103639754`, que estava na fila na última consulta; esse run verifica a documentação atualizada, não invalida os resultados experimentais já concluídos.

Os resultados registram ambiente Python 3.14.6, Windows 11, NumPy 2.5.1, SciPy 1.18.0 e scikit-learn 1.9.0. Os hashes registrados foram:
- `ta001`: `fa586022d3a4a759f2d26c4b61c5267e71c00e4016f3307bbe706982df2b42c3`;
- `ta011`: `16b1e1b2bf1464e5af0f28b7c1aaeed4d65ff00bce51d10f583dfd3fa12a02b6`.

## 7. Conclusão

A Semana 4 está experimentalmente concluída. O aumento para 2.000 amostras melhorou descritivamente a predição e o ranking nas duas instâncias, especialmente em `ta011`. O benchmark corrigido mostrou vantagem de latência apenas para inferência em lote. O custo de preparação e treinamento exige milhares de consultas em lote para ser amortizado.

**Conclusão científica:** o surrogate apresenta sinal preditivo útil, mas ainda moderado, e pode reduzir o custo de avaliações em lote após amortização. Não foi demonstrado que ele melhora a qualidade final da otimização GWO nem que generaliza para todo o espaço de permutações. Não substituir o avaliador exato e não alegar speedup end-to-end.

## 8. Artefatos

- Implementação: `scripts/surrogate_pfs.py`, `scripts/run_week4_surrogate.py`;
- testes: `tests/test_week4_surrogate.py`;
- protocolo: `docs/reports/week4_surrogate_protocol.md`;
- piloto corrigido: `results/week4_surrogate_pilot_v2/`;
- execução principal: `results/week4_surrogate_v2/`;
- esta auditoria: `docs/audits/2026-11-23-week4-corrected-pilot-status.md`.

Os resultados anteriores permanecem preservados; esta auditoria atualiza o status anteriormente pendente com a análise da execução principal.
