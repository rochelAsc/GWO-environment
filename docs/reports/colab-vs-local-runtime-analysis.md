# Comparação de tempos: máquina local × Google Colab

**Data:** 25/11/2026  
**Execução Colab:** `colab_20261125_01`  
**Baterias locais:** `week2_baseline_v2`, `week3_optuna_v2`, `week4_surrogate_v2`, `week5_fuzzy_v2` e `week6_benchmark_v1`

## 1. Objetivo e critério

Este documento compara os tempos registrados nas baterias locais e na reprodução no Google Colab. O objetivo é explicar por que os tempos diferem e delimitar o que pode ser concluído a partir deles.

Os dados vêm dos arquivos `runs.csv`, `fuzzy_runs.csv`, `summary.csv` e `metrics.json` de cada bateria. Para as Semanas 2, 3 e 5, foi calculada a média aritmética de `runtime_seconds` por instância, usando 30 execuções. Para a Semana 6, foram usados os campos `mean_runtime_seconds` dos resumos por variante e instância.

A razão apresentada é:

[
\text{Razão} = \frac{\text{tempo médio no Colab}}{\text{tempo médio local}}
]

Uma razão acima de 1 indica que o tempo medido no Colab foi maior. Os percentuais são diferenças observadas, não estimativas universais de desempenho de hardware.

## 2. Ambientes registrados

| Característica | Máquina local | Google Colab |
|---|---|---|
| Sistema operacional | Windows 11 | Linux x86_64, kernel 6.6.159+ |
| Python | 3.14.6 | 3.13.18 |
| Arquitetura | AMD64 | x86_64 |
| NumPy | Metadado da bateria local | 2.4.6 |

O manifesto Colab registra também SciPy 1.16.3, scikit-learn 1.6.1, pandas 2.2.3, Optuna 4.9.0, Matplotlib 3.10.0 e joblib 1.6.0. O manifesto local da Semana 6 registra Windows 11 e Python 3.14.6.

Os ambientes não são idênticos. Também não há, nos manifestos consultados, informação suficientemente detalhada e comparável sobre modelo de CPU, frequência efetiva, número de vCPUs disponíveis, política de escalonamento ou carga concorrente. Por isso, não é possível atribuir causalmente a diferença a um componente específico.

## 3. Semanas 2, 3 e 5

Tempos médios por execução, em segundos:

| Semana | Instância | Local (s) | Colab (s) | Razão Colab/local |
|---|---|---:|---:|---:|
| 2 — Baseline | ta001 | 0,879 | 1,834 | 2,09× |
| 2 — Baseline | ta011 | 1,423 | 2,914 | 2,05× |
| 3 — Optuna final | ta001 | 0,831 | 1,724 | 2,07× |
| 3 — Optuna final | ta011 | 1,349 | 2,873 | 2,13× |
| 5 — Fuzzy | ta001 | 1,043 | 2,162 | 2,07× |
| 5 — Fuzzy | ta011 | 1,606 | 3,356 | 2,09× |

Nas seis comparações, o tempo medido no Colab ficou aproximadamente entre 2,05× e 2,13× o tempo local. A diferença é consistente entre essas baterias, mas não deve ser interpretada como um fator fixo de conversão para outras máquinas ou sessões.

## 4. Semana 6 — comparação por variante

Tempos médios por execução, em segundos:

| Instância | Variante | Local (s) | Colab (s) | Razão Colab/local |
|---|---|---:|---:|---:|
| ta001 | Baseline | 0,936 | 1,863 | 1,99× |
| ta001 | Optuna | 0,897 | 1,806 | 2,01× |
| ta001 | Surrogate | 0,618 | 1,283 | 2,07× |
| ta001 | Fuzzy | 1,026 | 2,001 | 1,95× |
| ta011 | Baseline | 1,672 | 2,894 | 1,73× |
| ta011 | Optuna | 1,596 | 2,858 | 1,79× |
| ta011 | Surrogate | 0,778 | 1,427 | 1,83× |
| ta011 | Fuzzy | 1,794 | 3,105 | 1,73× |

A diferença observada na Semana 6 foi de aproximadamente 1,73× a 2,07×. A ordenação relativa das variantes permaneceu igual nas duas plataformas e instâncias: Surrogate teve menor tempo médio, seguido por Optuna/Baseline e Fuzzy conforme os valores registrados. Isso não significa que o custo total de preparação do Surrogate esteja incluído em cada execução; o treinamento foi realizado anteriormente e é contabilizado separadamente.

## 5. Semana 4 — treinamento e latência do surrogate

A Semana 4 mede geração do dataset, treinamento e latência de avaliação. Esses tempos não devem ser misturados com o tempo de uma execução completa da Semana 6.

### Geração dos dados e treinamento

| Instância | Local (s) | Colab (s) | Razão Colab/local |
|---|---:|---:|---:|
| ta001 | 0,406 | 0,807 | 1,99× |
| ta011 | 0,553 | 1,083 | 1,96× |

O valor é a soma de `dataset_generation_and_exact_labels_seconds` e `training_seconds` de cada `metrics.json`.

### Speedup de inferência em lote sobre avaliação exata

| Instância | Local | Colab |
|---|---:|---:|
| ta001 | 3,31× | 3,21× |
| ta011 | 5,45× | 5,27× |

O speedup em lote permaneceu próximo entre os ambientes. A inferência individual do modelo, por outro lado, continuou mais lenta que a avaliação exata nas duas plataformas. O protocolo de comparação usa o mesmo conjunto de chaves aleatórias e inclui decodificação e extração de atributos; os valores são específicos à implementação e ao ambiente.

## 6. Interpretação

As diferenças observadas são compatíveis com a execução em ambientes computacionais distintos. Entre os fatores que podem influenciar os tempos estão:

- processador e recursos de CPU efetivamente disponibilizados à sessão;
- frequência dinâmica, limites de energia e compartilhamento de recursos na VM;
- sistema operacional e versões de Python/bibliotecas;
- carga concorrente e variabilidade da infraestrutura do Colab;
- custos de inicialização, alocação e chamadas de bibliotecas;
- pequenas diferenças no estado do ambiente durante a medição.

Esses fatores são explicações plausíveis, não causas isoladas demonstradas pelos dados. Não há medições controladas de CPU, frequência ou carga que permitam decompor a diferença.

## 7. O que permanece comparável

A diferença de tempo não invalida a reprodução dos resultados de qualidade. As baterias mantiveram as mesmas instâncias, seeds, configurações, parâmetros congelados e orçamentos definidos nos protocolos. Além disso, os makespans das execuções Baseline, Optuna e Fuzzy coincidiram em 180 comparações por instância/seed; a Semana 6 do Colab também respeitou os contadores previstos para Surrogate.

Assim:

- **Makespan, hits de upper bound e estatísticas de qualidade:** comparáveis e consistentes entre as baterias verificadas.
- **Número de avaliações exatas e predições:** comparável e conferido contra o protocolo.
- **Tempo absoluto:** específico ao ambiente; não deve ser tratado como constante do algoritmo.
- **Comparações de tempo entre variantes dentro da mesma bateria:** mais adequadas do que comparar segundos absolutos entre máquinas, pois as variantes foram medidas no mesmo ambiente da respectiva bateria.
- **Custo de treinamento do Surrogate:** deve continuar separado do tempo de busca e ser amortizado conforme o número de execuções em uma aplicação real.

## 8. Conclusão

O Colab registrou tempos aproximadamente 1,7× a 2,1× maiores que a máquina local nas baterias comparadas. A diferença é sistemática, mas os dados disponíveis não permitem atribuí-la a uma causa única nem estabelecer um fator universal de correção.

A reprodução deve, portanto, ser considerada consistente quanto aos resultados de qualidade e aos contadores experimentais, enquanto os tempos absolutos devem ser reportados com identificação do ambiente. Para o artigo e a apresentação, recomenda-se apresentar os tempos locais e os tempos Colab como medições de ambientes distintos, sem misturá-los na mesma média e sem afirmar que uma plataforma é intrinsecamente mais lenta com base apenas nesta execução.
