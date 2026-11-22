# Relatório Parcial: Surrogate Modeling e Controle Fuzzy Adaptativo no Grey Wolf

# Optimizer

### Discente: Rochel Andrey dos Santos Costa Matrícula: 2023090100

### Universidade Federal do Maranhão (UFMA) Disciplina: Sistemas Inteligentes

### Docente: Prof. Dr. Alexandre Cesar Muniz de Oliveira 7 de novembro de 2026

## 1 Introdução

Este relatório descreve a implementação das etapas 4 e 5 do projeto de Sistemas Inte- ligentes: a substituição da função objetivo por um modelo *Surrogate* (Rede Neural) e a integração de um Controlador Fuzzy Adaptativo ao *Grey Wolf Optimizer* (GWO) para o problema de Flow Shop Permutacional (PFS). O objetivo é reduzir o custo computacional das simulações e adicionar adaptabilidade dinâmica à busca do algoritmo.

## 2 Semana 4: Modelo Surrogate (Rede Neural)

Em problemas reais de engenharia, o cálculo da função objetivo pode ser computacional- mente caro. Para mitigar isso, treinamos uma Rede Neural *Multilayer Perceptron* (MLP) para aproximar o comportamento do FlowShopEngine.

### 2.1 Pipeline de Amostragem e Treinamento

Os dados foram gerados utilizando a técnica de Amostragem por Hipercubo Latino (LHS), garantindo uma cobertura uniforme do espaço de busca contínuo. Foram geradas 500 amostras na instância I_3_4_2_3.txt, que foram utilizadas para treinar uma MLP com duas camadas ocultas de 64 neurônios cada. A saída (Tardiness) foi normalizada com *StandardScaler* para acelerar a convergência da rede.

### 2.2 Métricas de Regressão

A Tabela 1 apresenta as métricas de erro da rede neural no conjunto de teste. O coeficiente de determinação (*R²*) de 0,879 indica que a rede conseguiu capturar a maior parte da variância do problema, embora o RMSE de 24,60 mostre que ainda há um erro médio de predição considerável para essa instância.

Tabela 1: Métricas de Regressão da Rede Neural (Surrogate).

|Métrica|Valor|
|---|---|
|MSE|605,14|
|RMSE|24,60|
|R²|0,879|

A Figura 1 mostra o gráfico de paridade (valores reais vs. preditos), e a Figura 2 exibe a curva de aprendizado da rede neural.

Figura 1: Gráfico de Paridade: Tardiness Real vs. Predito.

Figura 2: Curva de Aprendizado da Rede Neural.

### 2.3 Comparativo de Ganho Computacional

Em instâncias de pequeno porte (Small), a avaliação via Surrogate apresentou um tempo de 1,31s contra 0,21s da avaliação real. Isso ocorre porque o FlowShopEngine em Python é

extremamente rápido para poucos jobs, enquanto a chamada individual do scikit-learn possui um alto *overhead* de validação por amostra. Contudo, em instâncias de grande porte (Large), o cenário se inverte. Enquanto a avaliação real exige simulações complexas, a inferência da rede neural mostrou-se **1,90** **vezes mais rápida** que a avaliação real. Esse ganho valida o uso do Surrogate para problemas reais de engenharia, onde o custo de simulação é proibitivo. Apesar da eficiência computacional, o Surrogate encontrou um fitness predito de 265,95 na instância Small, enquanto o ótimo real era 306,0. Isso evidencia o erro de aproximação da rede (*R²* = 0*,*879), mostrando que o GWO estava otimizando a "alucinação"da rede neural e não a realidade. Tal fato reforça a necessidade de validação final das soluções no motor real.

## 3 Semana 5: Controle Fuzzy Adaptativo

O Optuna definiu na Semana 3 que a melhor configuração fixa era *n*_*wolves* = 55 e decaimento exponencial. No entanto, parâmetros estáticos não se adaptam à dinâmica da população. Para resolver isso, foi implementado um Controlador Fuzzy do tipo Mamdani, mantendo os parâmetros base do Optuna.

### 3.1 Funções de Pertinência e Base de Regras

O controlador possui duas variáveis de entrada (Diversidade Populacional e Estagnação) e uma de saída (Fator de Ajuste do parâmetro *a*). A Figura 3 ilustra as funções de pertinência triangulares.

Figura 3: Funções de Pertinência do Sistema Fuzzy.

A base de regras foi definida para equilibrar exploração e explotação:

- Se Diversidade é Baixa E Estagnação é Alta *→* Aumentar *a* (forçar exploração).
- Se Diversidade é Alta E Estagnação é Baixa *→* Diminuir *a* (forçar convergência).
- Se Diversidade é Baixa E Estagnação é Baixa *→* Diminuir *a*.
- Se Diversidade é Alta E Estagnação é Alta *→* Manter *a*.

### 3.2 Resultados do Controlador

A Figura 4 demonstra a variação dinâmica do parâmetro *a* ao longo das gerações, com- parado ao decaimento linear padrão. Observa-se que o controlador Fuzzy intervém para manter o *a* mais alto em momentos de estagnação.

Figura 4: Variação dinâmica do parâmetro *a* ajustado pelo Fuzzy.

## 4 Análise Comparativa das 4 Versões

A Tabela 2 consolida os resultados preliminares das 4 versões do solver na instância I_3_4_2_3.txt.

<u>Tabela 2: Desempenho Comparativo das 4 Versões do Solver.</u>

|Versão|Média|Desvio|Tempo (s)|Avaliações|
|---|---|---|---|---|
|Baseline|306,00|0,00|0,65|3000|
|Tunado|306,00|0,00|0,66|5500|
|Surrogate|268,49|2,03|1,19|3000|
|Fuzzy|306,00|0,00|1,14|5500|

### 4.1 Discussão dos Resultados

- **Estagnação no Ótimo Real:** Baseline, Tunado e Fuzzy encontraram exatamente o mesmo ótimo (306,0) com desvio zero. Isso indica que, para esta instância pe- quena, o problema é relativamente fácil e as variações do GWO convergem para o mesmo ponto.
- **Custo Computacional do Fuzzy:** O Fuzzy executou as mesmas 5500 avaliações que o Tunado (pois herdou *n*_*wolves* = 55 do Optuna) e demorou 1,14s contra 0,66s. Esse aumento de tempo é o custo da inferência das regras a cada geração. Contudo, o controle adaptativo permitiu que o algoritmo mantivesse um equilíbrio dinâmico entre exploração e explotação.
- **O Falso Ótimo do Surrogate:** O Surrogate reportou a melhor média (268,49), mas isso é um artefato do erro da rede neural. O GWO otimizou a predição da rede, e não a realidade, demonstrando a importância da validação cruzada.

## 5 Conclusão

As implementações das Semanas 4 e 5 foram concluídas com sucesso. O modelo Surro- gate mostrou-se uma alternativa viável para reduzir o custo computacional em instâncias complexas. O Controlador Fuzzy adicionou adaptabilidade ao GWO, provando-se uma ferramenta robusta para manter a diversidade populacional. Os dados e códigos gerados formam uma base sólida para a etapa de benchmarking estatístico (Semana 6).
