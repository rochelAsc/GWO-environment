# Auditoria da Semana 6 — Benchmark comparativo

**Data da auditoria:** 25/11/2026  
**Commit auditado:** `341d0e4c1253b5ae5d9f0a6952cdf7b5fc5942d5`  
**Bateria:** `results/week6_benchmark_v1/`  
**Protocolo:** [week6_benchmark_protocol.md](../reports/week6_benchmark_protocol.md)  
**Decisão:** [Surrogate-assisted evaluation](../decisions/2026-11-25-week6-surrogate-assisted-evaluation.md)

## 1. Escopo e veredito

Esta auditoria verifica a bateria confirmatória da Semana 6: quatro variantes de GWO — Baseline, Optuna, Surrogate assistido e Fuzzy — no PFSP clássico de uma fábrica, minimizando makespan, em duas instâncias Taillard: `ta001` (20 jobs, 5 máquinas) e `ta011` (20 jobs, 10 máquinas).

**Veredito:** a bateria está estruturalmente completa, os contadores agregados são coerentes com o protocolo congelado, os resultados e metadados estão publicados e a CI do commit auditado terminou com sucesso. Os resultados sustentam conclusões específicas por instância, mas não uma variante universalmente superior.

Esta avaliação não mistura os resultados com PFS/tardiness dos relatórios históricos nem com DPFSP-DD. A Semana 6 usa PFSP/makespan e as instâncias Taillard indicadas.

## 2. Integridade e reprodutibilidade

O manifesto registra:

- 2 instâncias, 4 variantes e 30 seeds (0–29);
- 240 execuções esperadas e 240 registradas;
- 30 execuções por combinação instância/variante;
- hashes SHA-256 das duas instâncias e dos dois modelos surrogate;
- parâmetros Optuna congelados, versões do ambiente e métricas de teste dos modelos;
- custo de preparação do surrogate separado do custo da busca.

Os arquivos publicados são:

- `runs.csv`: resultados por execução;
- `summary.csv`: estatísticas descritivas por instância e variante;
- `pairwise_statistics.csv`: Wilcoxon pareado e p-valores corrigidos por Holm;
- `convergence.csv` e `convergence_summary.csv`: histórico de convergência;
- `surrogate_trace.csv` e `fuzzy_trace.csv`: rastros de execução;
- `metadata.json`: configuração, hashes, contadores e análise agregada.

Os contadores agregados conferem com o protocolo:

| Variante | Execuções | Avaliações exatas por execução | Total de avaliações exatas |
|---|---:|---:|---:|
| Baseline | 60 | 15.030 | 901.800 |
| Optuna | 60 | 15.030 | 901.800 |
| Surrogate | 60 | 1.530 | 91.800 |
| Fuzzy | 60 | 15.030 | 901.800 |
| **Busca** | **240** | — | **2.797.200** |

O Surrogate também realizou 15.000 predições por execução, totalizando 900.000 predições. Sua inicialização foi avaliada exatamente; em cada geração, 30 candidatos foram preditos e os três melhores segundo o modelo foram reavaliados pelo makespan exato. O arquivo de líderes e a convergência usam apenas fitness exato.

A preparação dos modelos da Semana 4 consumiu 2.000 rótulos exatos por instância, ou 4.000 no total, e aproximadamente 0,959 s de geração de dados/treino registrados no manifesto. Incluindo esses rótulos, o histórico completo contabiliza 2.801.200 avaliações exatas entre preparação e busca. Esse total não deve ser confundido com o orçamento online de cada execução.

### CI

A GitHub Actions associada ao commit auditado concluiu com **success**:

- Workflow: Python tests
- Run: 127
- Commit: `341d0e4c1253b5ae5d9f0a6952cdf7b5fc5942d5`
- [Execução no GitHub Actions](https://github.com/rochelAsc/GWO-environment/actions/runs/45734389917)

A CI confirma que a suíte automatizada passou nesse commit; ela não substitui a auditoria dos dados experimentais nem prova, por si só, a validade externa dos resultados.

## 3. Configurações comparadas

| Variante | População | Iterações | Configuração | Avaliações exatas/run |
|---|---:|---:|---|---:|
| Baseline | 30 | 500 | Agenda linear, 2 → 0 | 15.030 |
| Optuna | 45 | 333 | (a_{start}=1,5441), (a_{end}=0,1082), expoente (0,5517) | 15.030 |
| Surrogate | 30 | 500 | MLP congelado, top-3 reavaliados exatamente/geração | 1.530 |
| Fuzzy | 30 | 500 | Controlador Mamdani da Semana 5 v2 | 15.030 |

A configuração Optuna foi carregada de `results/week3_optuna_v2/best_params.json`. Os modelos surrogate foram reutilizados sem retreinamento durante a bateria.

O orçamento de avaliações exatas **não é igual** entre Surrogate e as outras variantes. Assim, esta é uma comparação entre estratégias conforme o protocolo, não um experimento com orçamento igual de avaliações exatas. Também não equivale a orçamento computacional total igual: o Surrogate adiciona inferência e custo de preparação, enquanto as demais variantes executam mais avaliações exatas.

## 4. Resultados descritivos

O objetivo é minimizar makespan; portanto, valores menores são melhores. O desvio padrão é amostral.

### ta001 — 20 jobs × 5 máquinas

| Variante | Média | Mediana | DP | Mín.–máx. | Hits UB (1278) | Tempo médio |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 1272,73 | 1265,0 | 15,42 | 1265–1338 | 20/30 | 0,936 s |
| Optuna | **1268,40** | 1265,0 | 11,33 | 1265–1309 | **27/30** | 0,897 s |
| Surrogate | 1275,13 | 1267,5 | 14,61 | 1265–1319 | 18/30 | **0,618 s** |
| Fuzzy | 1269,10 | 1265,0 | **6,24** | 1265–1279 | 22/30 | 1,026 s |

Na `ta001`, Optuna teve a menor média e mais hits no upper bound; Fuzzy teve a menor dispersão; Surrogate teve o menor tempo médio, mas a pior média e menos hits que as outras variantes. As diferenças descritivas entre as variantes não foram confirmadas por comparações pareadas após correção de Holm (Seção 5).

### ta011 — 20 jobs × 10 máquinas

| Variante | Média | Mediana | DP | Mín.–máx. | Hits UB (1582) | Tempo médio |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | 1640,23 | 1634,0 | 24,08 | 1626–1731 | 0/30 | 1,672 s |
| Optuna | 1638,77 | 1627,5 | 18,11 | 1626–1684 | 0/30 | 1,596 s |
| Surrogate | 1660,20 | 1653,5 | 22,64 | 1631–1731 | 0/30 | **0,778 s** |
| Fuzzy | **1633,83** | 1630,0 | **11,53** | **1619–1677** | 0/30 | 1,794 s |

Na `ta011`, Fuzzy teve a menor média, mediana e desvio padrão, além do melhor resultado observado. Nenhuma variante atingiu o upper bound publicado de 1582. Surrogate foi o mais rápido, mas teve a pior média e mediana.

### Tempo e compromisso qualidade–custo

Em relação ao tempo médio do Baseline, o Surrogate foi aproximadamente 34,0% mais rápido na `ta001` e 53,5% mais rápido na `ta011`. Essa redução de tempo veio acompanhada de pior qualidade média, especialmente na `ta011`.

O tempo de inferência do Surrogate não deve ser omitido: em média, foram 0,444 s na `ta001` e 0,518 s na `ta011`, além de 0,098 s e 0,171 s, respectivamente, em avaliações exatas. O tempo total inclui esses componentes. A preparação do modelo foi feita anteriormente e é reportada separadamente; uma análise de uso em produção deveria amortizar esse custo pelo número de execuções.

## 5. Análise estatística

Os testes foram realizados separadamente por instância, usando os 30 seeds como blocos. Friedman avalia diferença global entre as quatro variantes. Para as seis comparações par a par por instância, foi aplicado Wilcoxon pareado e correção de Holm.

### Teste global de Friedman

| Instância | Estatística | p-valor |
|---|---:|---:|
| ta001 | 9,8914 | 0,01951 |
| ta011 | 37,6596 | 3,34 × 10⁻⁸ |

Com nível de significância de 5%, os testes globais rejeitam a hipótese de igualdade de desempenho entre as quatro variantes em ambas as instâncias. O teste global não identifica, sozinho, quais pares diferem.

### Comparações pareadas após Holm

Na `ta001`, **nenhuma das seis comparações** permaneceu significativa após a correção de Holm. Embora Optuna tenha média menor que Baseline em 4,33 unidades e Surrogate tenha média maior que Fuzzy em 6,03 unidades, esses contrastes não foram estatisticamente significativos após o ajuste.

Na `ta011`, as três comparações envolvendo Surrogate foram significativas após Holm:

| Comparação | Diferença média (esquerda − direita) | p ajustado |
|---|---:|---:|
| Baseline − Surrogate | −19,97 | 0,001990 |
| Optuna − Surrogate | −21,43 | 0,001878 |
| Surrogate − Fuzzy | +26,37 | 0,0000808 |

Como makespan menor é melhor, os sinais indicam que Surrogate foi pior que Baseline, Optuna e Fuzzy na `ta011`. As outras três comparações nessa instância não foram significativas após Holm.

**Interpretação:** há evidência de diferença global entre variantes nas duas instâncias. A evidência pareada pós-hoc localiza diferenças robustas na `ta011`, todas desfavoráveis ao Surrogate. Não há evidência pós-hoc suficiente para declarar uma vencedora na `ta001`, nem para afirmar superioridade geral de Optuna ou Fuzzy.

### Limitação do pareamento

As variantes receberam os mesmos rótulos de seed, permitindo comparar os resultados por bloco. Isso não garante números aleatórios comuns idênticos: as variantes podem consumir o gerador aleatório de maneiras diferentes, inclusive por usarem tamanhos de população distintos. Portanto, o pareamento por seed deve ser descrito como bloqueio por seed, e não como controle perfeito de todas as fontes de aleatoriedade. A interpretação inferencial deve permanecer restrita a estas instâncias, implementações e protocolo.

## 6. Qualidade dos modelos surrogate

Os modelos foram treinados na Semana 4 com 2.000 rótulos exatos por instância. As métricas no conjunto de teste foram:

| Instância | RMSE | MAE | R² | Spearman |
|---|---:|---:|---:|---:|
| ta001 | 43,21 | 34,10 | 0,573 | 0,758 |
| ta011 | 65,94 | 51,38 | 0,252 | 0,539 |

O modelo da `ta011` apresenta capacidade de ordenação e explicação mais fraca no teste. Isso é compatível com o pior desempenho observado na busca assistida nessa instância, embora não prove causalidade isoladamente. O mecanismo top-3 reduz o número de avaliações exatas, mas depende da qualidade do ranking predito: candidatos promissores podem ser descartados antes da reavaliação exata.

As previsões não foram tratadas como makespan real, nem usadas para atualizar diretamente o arquivo elite ou a curva de convergência. Essa separação é essencial para a validade dos resultados reportados.

## 7. Limitações e ameaças à validade

1. **Cobertura de instâncias:** somente duas instâncias Taillard de 20 jobs foram avaliadas. Não se pode generalizar os resultados para outras dimensões, distribuições ou variantes de scheduling.
2. **Orçamento desigual:** Surrogate usa 1.530 avaliações exatas por execução, contra 15.030 nas outras variantes. O ganho de tempo é relevante, mas a comparação não isola exclusivamente a qualidade dos algoritmos sob custo equivalente.
3. **Custo de preparação:** o treinamento é anterior à bateria e deve ser considerado em cenários com poucas execuções. O custo de preparação foi registrado, mas não incorporado ao tempo de cada run.
4. **Modelos limitados:** o desempenho preditivo, especialmente na `ta011`, é moderado. A política top-3 pode perder candidatos bons que o modelo classifica incorretamente.
5. **Pareamento por seed:** seeds iguais não garantem trajetórias aleatórias equivalentes entre implementações com consumo distinto de RNG.
6. **Upper bounds:** hits no upper bound são referências aos melhores valores publicados, não prova de ótimo global. A ausência de hits na `ta011` não invalida a execução, mas evidencia a distância para a referência.
7. **Tempo de execução:** tempos dependem do hardware, sistema operacional, bibliotecas e carga da máquina registrados no manifesto; não devem ser tratados como constantes universais.
8. **Inferência estatística:** os testes são condicionados às duas instâncias e ao protocolo escolhido. O resultado global de Friedman não substitui os testes pós-hoc corrigidos.
9. **Fuzzy:** o resultado favorável em média na `ta011` não autoriza retunar regras com os mesmos dados e depois apresentar esses dados como validação independente.

## 8. Conclusões

- **Baseline:** referência estável para comparação; não foi a melhor média em nenhuma das duas instâncias.
- **Optuna:** melhor média e maior número de hits no upper bound na `ta001`; na `ta011`, média próxima ao Baseline, sem diferença pareada significativa entre ambos.
- **Fuzzy:** menor dispersão na `ta001` e melhor média/mediana/desvio padrão na `ta011`; não demonstrou superioridade estatística sobre Baseline ou Optuna nas comparações pareadas corrigidas.
- **Surrogate:** reduziu o tempo médio de execução nas duas instâncias, mas perdeu qualidade, com desvantagem estatisticamente significativa frente às outras três variantes na `ta011`. É uma estratégia de economia de avaliações exatas com compromisso de qualidade, não um substituto equivalente do avaliador exato.

**Conclusão geral:** não existe uma variante vencedora em todos os critérios. Optuna é a melhor escolha descritiva para qualidade na `ta001`; Fuzzy é a melhor escolha descritiva para qualidade na `ta011`; Surrogate é a opção mais rápida, mas sua perda de qualidade — estatisticamente sustentada na `ta011` — impede recomendá-lo como substituto geral. A escolha depende de priorizar qualidade ou tempo e deve respeitar o escopo limitado das instâncias avaliadas.

## 9. Estado da Semana 6

A implementação, a bateria de 240 execuções, os arquivos brutos, os resumos, as análises estatísticas e a CI estão publicados. A auditoria formal registra os resultados sem alterar os dados experimentais nem retunar as variantes.

A Semana 6 pode ser considerada **experimentalmente concluída** dentro do escopo definido. A etapa seguinte do trabalho é a consolidação do artigo e da apresentação, respeitando o roteiro atualizado pelo professor. A etapa de Meta-Learning foi retirada pelo professor e não integra este trabalho.
