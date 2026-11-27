# Relatório do piloto: distribuição de candidatos GWO

**Data:** 26/11/2026  
**Status:** piloto executado localmente; resumo e metadados publicados; população completa permanece fora do Git por exceder o limite de tamanho do GitHub.  
**Instância:** Taillard `ta111` (500 jobs × 20 máquinas).  
**Protocolo:** `gwo_population_distribution_audit_v1`.

## 1. Objetivo

Investigar as distribuições de candidatos efetivamente visitadas pelas quatro variantes GWO do projeto — Baseline, Optuna, Fuzzy e Surrogate — preservando a dinâmica dos algoritmos. Cada candidato observado recebe um makespan exato para análise posterior. Esses rótulos diagnósticos não são fornecidos ao otimizador e não alteram líderes, fitness interno, seleção ou atualização.

## 2. Configuração executada

- Variantes: Baseline, Optuna, Fuzzy e Surrogate.
- Seeds: 0, 1, 2, 3 e 4.
- Baseline/Fuzzy/Surrogate: 30 lobos e 500 iterações.
- Optuna: 45 lobos e 333 iterações, conforme configuração congelada.
- Surrogate: top-3, modelo MLP do diretório `meta_learning_cost_pilot_v2/surrogates/ta111`.
- Amostragem: população inicial (geração -1) e cada população subsequente.
- Makespan: cálculo exato para cada indivíduo observado.

O modelo usado na variante Surrogate é o artefato Cost Pilot v2 para `ta111`, não o artefato original da Week 4 (que não está disponível para essa instância). O SHA-256 do modelo, da instância e da configuração Optuna está registrado em `metadata.json`. O uso desse modelo deve ser considerado uma configuração identificada do piloto, não uma reprodução bit a bit do modelo Surrogate da Week 6.

## 3. Integridade e volume

Foram registradas 20 execuções (4 variantes × 5 seeds). Cada execução observou 15.030 candidatos, totalizando:

| Medida | Resultado |
|---|---:|
| Execuções | 20 |
| Candidatos por execução | 15.030 |
| Candidatos por variante | 75.150 |
| Candidatos no piloto | 300.600 |
| Rótulos diagnósticos exatos | 300.600 |

O manifesto registra `diagnostic_labels_are_not_used_by_search=true`. Para Baseline, Optuna e Fuzzy, os rótulos diagnósticos repetem o cálculo exato já realizado internamente; para Surrogate, são avaliações diagnósticas adicionais. Portanto, não somar os rótulos diagnósticos ao orçamento algorítmico da Week 6.

Arquivos publicados no repositório:
- `results/gwo_population_distribution_audit_v1/metadata.json`
- `results/gwo_population_distribution_audit_v1/runs.csv`

O arquivo completo `populations.csv` tem aproximadamente 551,40 MB e não foi versionado, pois ultrapassa o limite de 100 MB por arquivo do GitHub. Ele deve ser preservado localmente e disponibilizado por armazenamento externo antes da análise linha a linha. A ausência do CSV no GitHub não significa que os dados tenham sido descartados.

## 4. Makespan observado

Resultados por seed:

| Seed | Baseline | Optuna | Fuzzy | Surrogate |
|---:|---:|---:|---:|---:|
| 0 | 28.316 | 28.561 | 28.874 | 28.543 |
| 1 | 28.845 | 28.639 | 28.103 | 28.530 |
| 2 | 28.042 | 28.571 | 28.182 | 28.610 |
| 3 | 28.419 | 28.482 | 28.712 | 28.317 |
| 4 | 28.775 | 28.779 | 28.376 | 28.473 |

Estatísticas descritivas (média e desvio-padrão amostral):

| Variante | Média | Desvio-padrão | Mínimo | Máximo |
|---|---:|---:|---:|---:|
| Baseline | 28.479,4 | 332,7 | 28.042 | 28.845 |
| Optuna | 28.606,4 | 111,4 | 28.482 | 28.779 |
| Fuzzy | 28.449,4 | 334,0 | 28.103 | 28.874 |
| Surrogate | 28.494,6 | 110,6 | 28.317 | 28.610 |

Essas estatísticas são apenas descritivas. Cinco seeds não sustentam conclusão inferencial robusta nem afirmação de superioridade. A comparação também não elimina a diferença de orçamento entre a variante Surrogate e as variantes de avaliação exata.

## 5. Custo observado

Tempos de execução registrados pelo runner:

| Variante | Tempo médio por execução (s) |
|---|---:|
| Baseline | 112,93 |
| Optuna | 116,00 |
| Fuzzy | 115,95 |
| Surrogate | 64,93 |

O custo de geração dos rótulos diagnósticos está incluído no tempo medido pelo runner. Assim, esses tempos não devem ser comparados diretamente aos tempos originais da Week 6 sem separar o custo de instrumentação. O Surrogate ainda requer 15.030 rótulos diagnósticos exatos por execução, embora sua busca use 1.530 avaliações exatas e 15.000 previsões.

## 6. Interpretação e limites

1. O piloto demonstra viabilidade operacional da coleta e produz os resultados de execução esperados.
2. O resumo de makespan não revela a distribuição das populações. Para isso, ainda é necessário analisar o arquivo completo `populations.csv`.
3. As observações dentro de uma mesma trajetória são temporalmente dependentes. Candidatos individuais não devem ser tratados como amostras independentes.
4. O piloto cobre uma única instância e cinco seeds; não permite generalização para outras dimensões PFSP.
5. O modelo Surrogate usado é o Cost Pilot v2 para `ta111`; sua identidade deve permanecer explícita em qualquer análise posterior.
6. O arquivo de população completo não está no GitHub. Nenhuma análise de frequência posicional, entropia, precedência, Kendall ou concentração de makespan foi reivindicada neste relatório.

## 7. Próximas etapas

Antes de ampliar para 30 seeds:

1. preservar e disponibilizar o `populations.csv` local por armazenamento externo;
2. validar contagem de linhas, gerações, indivíduos por população, duplicatas e consistência com `runs.csv`;
3. conferir amostras de permutações e makespans por recálculo independente;
4. revisar a deduplicação do runner para não carregar o CSV inteiro em memória;
5. atualizar a análise de distribuição com métricas por geração e por execução.

Somente após essas verificações, executar seeds 0–29. Para qualquer treinamento/avaliação posterior, dividir por execução/seed, nunca aleatoriamente por linha de candidato. O piloto de cinco seeds é exploratório e não deve ser usado como dataset final de treino/teste.

## 8. Artefatos e proveniência

- Runner: `scripts/run_gwo_population_distribution_audit.py`.
- Testes do observador: `tests/test_gwo_population_observer.py`.
- Protocolo: `docs/reports/gwo_population_distribution_audit_protocol.md`.
- Metadados: `results/gwo_population_distribution_audit_v1/metadata.json`.
- Resumo por execução: `results/gwo_population_distribution_audit_v1/runs.csv`.
- Populações completas: `results/gwo_population_distribution_audit_v1/populations.csv` (artefato local não versionado; ~551,40 MB).

A instrumentação foi testada por comparação com e sem callback, incluindo igualdade do resultado final, permutação, convergência e contadores. A execução local produziu 20 linhas de execução e os metadados acima. A CI associada ao commit de publicação estava em andamento no momento da atualização deste relatório; não declarar a suíte completa aprovada até a conclusão do workflow.
