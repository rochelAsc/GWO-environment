# Auditoria da curva de aprendizagem do surrogate — 26/11/2026

## 1. Conclusão executiva

Esta auditoria examina os resultados de results/meta_learning_surrogate_learning_curve_v1/, o gerador de dados, a representação de permutações e a literatura sobre surrogate-assisted optimization e algorithm selection.

1. Aumentar de 300 para 4.000 amostras melhora RMSE e correlação de ranking nas duas instâncias, mas a qualidade permanece fraca, sobretudo em ta111 (500 jobs × 20 máquinas).
2. O problema não pode ser atribuído apenas à quantidade de dados. A representação tem 500 entradas na ta111 e a MLP possui aproximadamente 36.289 parâmetros. Com 4.000 observações, a razão amostras/parâmetros é baixa. Isso é indício de dificuldade de estimação, não prova isolada de overfitting.
3. O braço chamado LHS não é um único design Latin Hypercube de tamanho N quando N>512: a implementação concatena blocos LHS independentes de até 512 linhas. Os resultados devem ser descritos como **LHS em blocos de random keys + stable argsort**, não como LHS global de N pontos.
4. Treino e teste são amostras de permutações uniformes. A avaliação atual não mede a distribuição de candidatos que o GWO realmente visita. Isso não explica a baixa qualidade no teste uniforme, mas é uma lacuna adicional para o uso dentro do GWO.
5. Aumentar o número de instâncias não foi descartado. É necessário para o Meta-Learning de seleção de algoritmos; é uma pergunta distinta do aumento de amostras por instância no surrogate.

A evidência empírica abaixo é a dos CSVs agregados publicados. A análise da distribuição é uma auditoria do código gerador e do esquema de persistência. Como as permutações individuais não foram armazenadas e a versão do SciPy não foi registrada no metadata, não é possível afirmar que histogramas/frequências empíricas exatas da execução original foram recalculados. Uma próxima execução deve persistir diagnósticos reproduzíveis da distribuição e versões do ambiente.

## 2. Resultados observados

O experimento contém 100 registros: 2 instâncias × 2 métodos × 5 tamanhos × 5 repetições. Tamanhos: 300, 573, 1.095, 2.093 e 4.000.

| Instância | Método | RMSE N=300 | RMSE N=4.000 | Redução | Spearman final | R² final |
|---|---|---:|---:|---:|---:|---:|
| ta071 | LHS em blocos | 160,19 | 140,89 | 12,1% | 0,384 | 0,139 |
| ta071 | Uniforme | 160,73 | 139,82 | 13,0% | 0,398 | 0,152 |
| ta111 | LHS em blocos | 387,03 | 342,23 | 11,6% | 0,144 | -0,058 |
| ta111 | Uniforme | 381,77 | 343,03 | 10,2% | 0,138 | -0,063 |

Na ta071, R² torna-se positivo, porém baixo, e Spearman não chega a 0,40. Na ta111, R² permanece negativo e Spearman fica próximo de 0,14. Top-k recall permanece baixo mesmo em N=4.000. A curva mostra que mais amostras ajudam a regressão, mas não tornam o surrogate confiável para selecionar os melhores candidatos.

### 2.1 Limitações do top-k

O teste tem 1.000 permutações e makespans inteiros, portanto empates são possíveis. A implementação usa argsort para selecionar exatamente k elementos e pode escolher arbitrariamente entre candidatos empatados na fronteira do top-k. Isso torna recall sensível à ordem de desempate. Regret é menos sensível a essa questão, mas depende do melhor valor observado no conjunto de teste.

Na próxima versão, usar avaliação top-k com tratamento explícito de empates (por exemplo, conjunto de todos os candidatos empatados no limiar, com recall fracionário) e reportar regret como métrica central de seleção.

## 3. Auditoria da representação

O código em scripts/run_week4_surrogate.py codifica a permutação como vetor de dimensão n_jobs: feature[j] é a posição normalizada ocupada pelo job j, em [0,1].

É uma representação bijetiva: não perde identidade nem ordem da permutação. O problema não é falta de informação formal, mas falta de viés indutivo apropriado para aprender a estrutura do PFSP.

A MLP recebe 100 entradas na ta071 e 500 na ta111, sem representação explícita de:
- relações de precedência entre pares de jobs;
- vizinhanças/adjacências na sequência;
- perfis de processamento dos jobs e interação desses perfis com a ordem;
- estrutura de conclusão acumulada nas máquinas.

O modelo trata ranks como coordenadas numéricas comuns. Entretanto, as entradas pertencem a um espaço discreto e altamente restrito: somente vetores que codificam permutações são válidos. A proximidade euclidiana entre dois vetores de ranks não necessariamente corresponde a proximidade útil em makespan.

### 3.1 Capacidade da MLP

Para MLPRegressor((64,64)), com entrada d e uma saída, o número de parâmetros treináveis é:

(d+1)×64 + (64+1)×64 + (64+1)×1.

- ta071, d=100: 10.689 parâmetros.
- ta111, d=500: 36.289 parâmetros.

Com 4.000 exemplos, a razão bruta amostras/parâmetros é aproximadamente 0,37 na ta071 e 0,11 na ta111. A quantidade efetiva usada para ajustar pesos é menor por causa da validação interna do early stopping. Isso não prova overfitting, mas evidencia regime de dados escassos em relação à dimensão/capacidade, especialmente na ta111.

**Diagnóstico:** não aumentar N antes de comparar modelos com vieses indutivos diferentes e capacidade controlada.

## 4. Auditoria da distribuição de amostras

### 4.1 Braço uniforme

generate_uniform_permutations usa numpy.random.Generator.permutation(n_jobs), descarta duplicatas e gera um conjunto máximo de 4.000 permutações por repetição. Tamanhos menores são prefixos aninhados. Cada permutação aceita é uniforme sobre o espaço de permutações, salvo o efeito de rejeição de duplicatas.

### 4.2 Braço LHS

generate_lhs_dataset usa scipy.stats.qmc.LatinHypercube(d=n_jobs), gera random keys e decodifica cada linha com stable argsort. Diferentes random keys podem decodificar para a mesma permutação; duplicatas são descartadas.

O gerador limita cada chamada a no máximo 512 linhas e chama sampler.random() repetidamente. Assim, os designs efetivos para os tamanhos configurados são blocos concatenados:

| N solicitado | Blocos LHS gerados |
|---:|---|
| 300 | 300 |
| 573 | 512 + 61 |
| 1.095 | 512 + 512 + 71 |
| 2.093 | 512 + 512 + 512 + 512 + 45 |
| 4.000 | 512 × 7 + 416 |

Portanto, N>512 não representa um único Latin Hypercube de N pontos. A descrição anterior de “design LHS independente para cada N” era imprecisa. A nomenclatura correta para os resultados existentes é **LHS em blocos de random keys, decodificado por stable argsort, com deduplicação**.

Cada linha de random keys é composta por coordenadas contínuas uniformes; a ordenação de coordenadas independentes produz uma permutação uniforme em distribuição marginal. O LHS introduz estratificação/dependência entre linhas de cada bloco, não uma distribuição de permutações conhecida como superior à amostragem uniforme. A deduplicação também altera ligeiramente a distribuição conjunta quando há colisões. Para n_jobs=100/500 e N≤4.000, colisões entre permutações são combinatoriamente muito improváveis, mas o número efetivo de draws não foi persistido e não deve ser declarado como zero sem diagnóstico.

### 4.3 O que os resultados não medem

O conjunto de teste contém 1.000 permutações uniformes fixas por instância. Isso mede generalização para permutações aleatórias, não para a distribuição adaptativa do GWO.

O GWO transforma random keys iterativamente e concentra a população em regiões influenciadas pelos líderes. Suas populações podem apresentar frequências de posição diferentes das uniformes, precedências recorrentes entre jobs, adjacências frequentes, duplicatas e concentração regional, além de mudança de distribuição ao longo das gerações.

A ausência de teste sobre populações GWO é uma lacuna de validade externa para a aplicação do surrogate dentro do algoritmo. Contudo, não explica os baixos resultados observados no teste uniforme.

### 4.4 Diagnósticos necessários na próxima execução

Persistir, por instância, método, N e repetição:
- número de random-key draws, permutações únicas e duplicatas;
- frequência normalizada de posição por job e entropia média;
- frequência de precedência por pares de jobs (amostra ou matriz resumida);
- distribuição de Kendall distance entre pares de permutações;
- correlação média entre ranks de jobs e desvio em relação à permutação uniforme;
- comparação treino/teste e, separadamente, treino/populações GWO por geração;
- versões de Python, NumPy, SciPy e scikit-learn;
- seeds, hashes e identificação do gerador.

Não é necessário versionar matrizes gigantes de permutações para sempre: armazenar resumo estatístico, seeds e amostras representativas comprimidas. Para auditoria exata, salvar os conjuntos de treino/teste em NPZ ou guardar o artefato e seu SHA-256.

## 5. Distribuição do GWO: experimento complementar

1. Executar GWO sem surrogate em seeds de coleta.
2. Salvar permutações das populações em gerações iniciais, intermediárias e finais.
3. Remover duplicatas, mantendo geração e seed como metadados.
4. Avaliar makespan exato para formar rótulos.
5. Comparar a distribuição com permutações uniformes por posição, precedência e distância Kendall.
6. Criar teste externo de candidatos GWO obtidos de seeds que não participem do treino.

Uma mistura de treino global (uniforme) e local (GWO) pode ser testada depois. Amostragem local não deve substituir a global, pois isso pode concentrar o surrogate prematuramente em regiões estreitas.

## 6. Literatura revisitada e implicações

### 6.1 Liu et al. (2024) — survey de SAEAs combinatórios

Liu et al. organizam métodos por seleção, construção e gestão de surrogates. Destacam dificuldades de alta dimensionalidade e estrutura discreta; discutem regressão, classificação e ranking, além de seleção de amostras, incerteza e gestão online.

**Implicação:** o problema pode exigir mudanças simultâneas de representação, modelo e estratégia de aquisição. Apenas aumentar N não aborda esses três pontos.

### 6.2 Harada (2023) — ranking pareado ELDR

Harada propõe Extreme Learning-machine-based DirectRanker, que aprende relações de superioridade entre pares em vez de estimar diretamente o valor objetivo. O artigo testa benchmarks contínuos, não PFSP; a transferência é uma hipótese a testar.

**Implicação:** testar um ranker pareado com pares de permutações rotuladas pelo makespan. O alvo passa a ser prever se Cmax(πa) < Cmax(πb). Medir pairwise accuracy, Kendall tau, top-k recall e regret. Amostrar pares de forma controlada para evitar explosão O(N²) e balancear pares fáceis/difíceis.

### 6.3 Ikeguchi et al. (2025) — GBDT para permutações

A publicação *A Surrogate-Assisted Memetic Algorithm for Permutation-Based Combinatorial Optimization Problems* usa Gradient Boosting Decision Trees como surrogate para espaços discretos de permutação. O estudo relata desempenho melhor que RBF e Random Forest em mais de 35 de 42 instâncias sob orçamento limitado. Não é específico do PFSP Taillard, mas é evidência próxima da estrutura combinatória.

**Implicação:** comparar MLP com GradientBoosting/HistGradientBoosting ou implementação GBDT disponível no ambiente, usando os mesmos conjuntos e seeds. Não assumir que GBDT vencerá.

### 6.4 Framinan (2025) — GBT no PFSP estocástico

Framinan usa Gradient Boosted Trees para estimar expected makespan no PFSP estocástico. No estudo de eficiência, gera 1.000 soluções aleatórias por cenário e compara 10, 100 e 1.000 amostras de treino em instâncias pequenas de 5–20 jobs e 5 máquinas. Número de amostras é fator significativo e interage com número de jobs e hiperparâmetros. É variante estocástica, não idêntica ao nosso PFSP determinístico.

**Implicação:** mais amostras podem ajudar, mas o efeito depende da dimensão e do modelo. Não extrapolar instâncias pequenas para 500 jobs.

### 6.5 Zhu et al. (2025) — seleção sample-aware para scheduling

A versão de 2025 publicada em IEEE Transactions on Artificial Intelligence considera características fenotípicas e genotípicas na seleção de amostras para surrogate KNN em dynamic flexible job shop scheduling. Sustenta investigar composição e representatividade do conjunto, não apenas N.

**Implicação:** construir conjunto representativo que cubra padrões diversos de permutação, em vez de depender exclusivamente de amostras uniformes.

### 6.6 Ribeiro et al. (2026) — Meta-Learning diretamente no PFSP

Este artigo é especialmente relevante para a extensão Meta-Learning, embora não trate do surrogate de permutações. Usa 360 instâncias PFSP de Taillard e VRF, desempenho previamente disponível de dez meta-heurísticas ILS, meta-features extraídas de dois grafos e seleção de cinco atributos; testa Decision Tree, SVM e KNN em 10-fold CV. Reporta 99,7% de acurácia para árvore de decisão, mas discute dependência do performance space e limitações de diversidade/saturação.

**Implicação:** nossa meta-base com 12 instâncias não é suficiente para seleção confiável. Há precedente concreto de centenas de instâncias e reaproveitamento de resultados históricos. O número 99,7% não deve ser transplantado para nosso contexto.

### 6.7 Wallrath e Franke (2024) — escala de dados em flow shop distribuído

O estudo usa MLPRegressor com 400.000 permutações uniformes em DPFSP, rotuladas por simulação. É problema distribuído, não nosso PFSP, e não é curva de aprendizagem. Serve apenas como evidência de escala de dados em outro cenário, não como recomendação direta de 400.000 amostras.

## 7. Plano de solução priorizado

### Etapa A — protocolo e instrumentação

- Tratar curva v1 como concluída, mas nomear corretamente LHS em blocos.
- Na próxima versão, gerar um único design LHS de N random keys por tamanho/repetição, sem concatenar blocos silenciosamente; registrar tentativas e duplicatas. Se houver colisões, regenerar o design completo com seed derivada ou declarar método alternativo.
- Persistir versões de bibliotecas e diagnósticos de distribuição.
- Corrigir top-k para tratar empates.

### Etapa B — ablação de modelos

Usar os mesmos dados e splits para comparar:
1. MLP atual;
2. Gradient Boosting / HistGradientBoosting;
3. ExtraTrees ou Random Forest;
4. ranker pareado em segunda fase.

Métricas primárias: Spearman/Kendall, top-k recall com empates, regret e desempenho de seleção. RMSE/MAE permanecem secundárias. Ajustes devem ocorrer em validação interna, nunca no teste externo.

### Etapa C — representação e amostragem

Testar separadamente:
- rank vector atual;
- representação compacta de precedência/adjacência, sem matriz n×n completa inicialmente;
- amostragem híbrida: parte uniforme global, parte de populações GWO;
- seleção sample-aware por diversidade, distância Kendall e faixas de fitness.

Representação em grafo ou sequência com perfis de processamento dos jobs é linha posterior; não iniciar com GNN antes de estabelecer baselines simples.

### Etapa D — gestão online no GWO

Se os modelos melhorarem:
- preservar avaliações exatas de inicialização e arquivo;
- selecionar candidatos por previsão promissora, incerteza e diversidade;
- incorporar novos rótulos ao treino e atualizar periodicamente;
- manter validação independente e monitorar ranking/regret por geração;
- comparar sob orçamentos explícitos e incluir custo de treino/atualização.

Não usar apenas top-3 previsto: isso favorece exploração local e pode reforçar erros do modelo.

## 8. Aumentar o número de instâncias: decisão

**Não foi descartado; é recomendado para Meta-Learning.** Separar dois objetivos:

- **Surrogate por instância:** cada modelo aprende makespan para uma matriz específica. Mais instâncias testam robustez da abordagem em diferentes escalas, mas não substituem aumentar/selecionar dados dentro de cada instância.
- **Meta-Learning:** cada instância é uma observação independente. Doze instâncias (uma por grupo) são insuficientes para treinar e avaliar com confiança um seletor. Seeds são repetições dentro da mesma instância, não novas instâncias independentes.

Ribeiro et al. (2026) usam 360 instâncias Taillard+VRF. Isso não implica que precisamos imediatamente de 360, mas demonstra que 12 é muito pouco.

Plano recomendado:
1. **36 instâncias Taillard:** três por cada um dos 12 grupos, para piloto da meta-base e avaliação de custo.
2. **60 instâncias:** cinco por grupo, se o custo permitir.
3. **Até 120 instâncias Taillard:** benchmark completo como meta-base mais robusta.
4. **VRF:** expansão posterior, após validar parser, compatibilidade do PFSP e escala de execução.

O projeto já possui uma instância por grupo. A seleção de novas instâncias deve ser estratificada e congelada antes da execução. Para 36 instâncias, começar com 3–5 seeds por variante como piloto de custo; subir para 10 seeds na meta-base exploratória. Não tratar esse tamanho como confirmação definitiva. Reaproveitar Week6 para ta001 e ta011 somente após validar hashes e protocolo; não reexecutar dados compatíveis sem necessidade.

## 9. Decisão recomendada

1. Atualizar documentação e preservar curva v1 como evidência exploratória.
2. Corrigir instrumentação LHS e adicionar diagnósticos de distribuição.
3. Executar ablação MLP × GBDT × ExtraTrees em ta071 e ta111 com splits idênticos.
4. Avaliar candidatos gerados pelo GWO, não apenas permutações uniformes.
5. Só então decidir se N deve subir para 8.000 ou mais.
6. Em paralelo, expandir meta-base de 12 para 36 instâncias, reaproveitando resultados existentes.

A prioridade não é obter R² alto a qualquer custo. É construir um surrogate que ordene candidatos úteis e reduza avaliações exatas sem degradar a qualidade final do GWO.
