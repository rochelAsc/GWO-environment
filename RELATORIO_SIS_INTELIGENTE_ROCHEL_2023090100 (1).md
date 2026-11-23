# **Relatório Parcial: Surrogate Modeling e Controle Fuzzy Adaptativo no Grey Wolf Optimizer** 

**Discente:** Rochel Andrey dos Santos Costa Matrícula: 2023090100 

_Universidade Federal do Maranhão (UFMA)_ 

**Disciplina:** Sistemas Inteligentes 

**Docente:** Prof. Dr. Alexandre Cesar Muniz de Oliveira 7 de novembro de 2026 

## **1 Introdução** 

Este relatório descreve a implementação das etapas 4 e 5 do projeto de Sistemas Inteligentes: a substituição da função objetivo por um modelo _Surrogate_ (Rede Neural) e a integração de um Controlador Fuzzy Adaptativo ao _Grey Wolf Optimizer_ (GWO) para o problema de Flow Shop Permutacional (PFS). O objetivo é reduzir o custo computacional das simulações e adicionar adaptabilidade dinâmica à busca do algoritmo. 

## **2 Semana 4: Modelo Surrogate (Rede Neural)** 

Em problemas reais de engenharia, o cálculo da função objetivo pode ser computacionalmente caro. Para mitigar isso, treinamos uma Rede Neural _Multilayer Perceptron_ (MLP) para aproximar o comportamento do FlowShopEngine. 

### **2.1 Pipeline de Amostragem e Treinamento** 

Os dados foram gerados utilizando a técnica de Amostragem por Hipercubo Latino (LHS), garantindo uma cobertura uniforme do espaço de busca contínuo. Foram geradas 500 amostras na instância I_3_4_2_3.txt, que foram utilizadas para treinar uma MLP com duas camadas ocultas de 64 neurônios cada. A saída (Tardiness) foi normalizada com _StandardScaler_ para acelerar a convergência da rede. 

### **2.2 Métricas de Regressão** 

A Tabela 1 apresenta as métricas de erro da rede neural no conjunto de teste. O coeficiente de determinação ( _R_<sup>2</sup> ) de 0,879 indica que a rede conseguiu capturar a maior parte da variância do problema, embora o RMSE de 24,60 mostre que ainda há um erro médio de predição considerável para essa instância. 

1 

Tabela 1: Métricas de Regressão da Rede Neural (Surrogate). 

|**Métrica**|**Valor**|
|---|---|
|MSE|605,14|
|RMSE<br>_R_<sup>2</sup>|24,60<br>0,879|



A Figura 1 mostra o gráfico de paridade (valores reais vs. preditos), e a Figura 2 exibe a curva de aprendizado da rede neural. 



<!-- Start of picture text -->
Surrogate: Tardiness Real vs Predito<br>== Ideal (x=y)y Oeoe<br>500 ey”88° °°<br>° 846<br>o 1 0<br>o,f 0<br>So<br>— 450 ° ° @° ©<br>5 ° o So<br>2 oe” oe<br>5 © 8 °@<br>2 $ e%ve<br>5 ° 4 °<br>é 400 ° °<br>F oo OF<br>2¢<br>5-<br>2 on @e<br>e 350 “ °°<br>° Ye<br>oe<br>go 00”<br>oF<br>300} e4<br>90o<br>°<br>300 350 400 450 500<br>Tardiness Real (FlowShopEngine)<br><!-- End of picture text -->

Figura 1: Gráfico de Paridade: Tardiness Real vs. Predito. 



<!-- Start of picture text -->
Curva de Aprendizado da Rede Neural (Surrogate)<br>oa<br>503<br>&<br>Boz<br>oa<br>oo fy 100 200 300 200 00<br>Epoca Iteracéo de Treino)<br><!-- End of picture text -->

Figura 2: Curva de Aprendizado da Rede Neural. 

### **2.3 Comparativo de Ganho Computacional** 

Em instâncias de pequeno porte (Small), a avaliação via Surrogate apresentou um tempo de 1,31s contra 0,21s da avaliação real. Isso ocorre porque o FlowShopEngine em Python é 

2 

extremamente rápido para poucos jobs, enquanto a chamada individual do scikit-learn possui um alto _overhead_ de validação por amostra. 

Contudo, em instâncias de grande porte (Large), o cenário se inverte. Enquanto a avaliação real exige simulações complexas, a inferência da rede neural mostrou-se **1,90 vezes mais rápida** que a avaliação real. Esse ganho valida o uso do Surrogate para problemas reais de engenharia, onde o custo de simulação é proibitivo. 

Apesar da eficiência computacional, o Surrogate encontrou um fitness predito de 265,95 na instância Small, enquanto o ótimo real era 306,0. Isso evidencia o erro de aproximação da rede ( _R_<sup>2</sup> = 0 _,_ 879), mostrando que o GWO estava otimizando a "alucinação"da rede neural e não a realidade. Tal fato reforça a necessidade de validação final das soluções no motor real. 

## **3 Semana 5: Controle Fuzzy Adaptativo** 

O Optuna definiu na Semana 3 que a melhor configuração fixa era _n_  wolves_ = 55 e decaimento exponencial. No entanto, parâmetros estáticos não se adaptam à dinâmica da população. Para resolver isso, foi implementado um Controlador Fuzzy do tipo Mamdani, mantendo os parâmetros base do Optuna. 

### **3.1 Funções de Pertinência e Base de Regras** 

O controlador possui duas variáveis de entrada (Diversidade Populacional e Estagnação) e uma de saída (Fator de Ajuste do parâmetro _a_ ). A Figura 3 ilustra as funções de pertinência triangulares. 



<!-- Start of picture text -->
06 06 06)<br>5 — Baixa — baa > diminuir<br>$ —s — — Aumentar<br><!-- End of picture text -->

Figura 3: Funções de Pertinência do Sistema Fuzzy. 

A base de regras foi definida para equilibrar exploração e explotação: 

- Se Diversidade é Baixa E Estagnação é Alta _→_ Aumentar _a_ (forçar exploração). 

- Se Diversidade é Alta E Estagnação é Baixa _→_ Diminuir _a_ (forçar convergência). 

- Se Diversidade é Baixa E Estagnação é Baixa _→_ Diminuir _a_ . 

- Se Diversidade é Alta E Estagnação é Alta _→_ Manter _a_ . 

3 

### **3.2 Resultados do Controlador** 

A Figura 4 demonstra a variação dinâmica do parâmetro _a_ ao longo das gerações, comparado ao decaimento linear padrão. Observa-se que o controlador Fuzzy intervém para manter o _a_ mais alto em momentos de estagnação. 



<!-- Start of picture text -->
Evolucao do Parametro ‘a' ao Longo das Geracées<br>2.00 Pe — a<br>ais as ==- a(fuzzy) (Linear Padrao)<br>150 a<br>ye 125 eg<br>050 ote<br>0.25 ——<br>0.00 —S<br>3 % ra & % 100<br><!-- End of picture text -->

Figura 4: Variação dinâmica do parâmetro _a_ ajustado pelo Fuzzy. 

## **4 Análise Comparativa das 4 Versões** 

A Tabela 2 consolida os resultados preliminares das 4 versões do solver na instância I_3_4_2_3.txt. 

Tabela 2: Desempenho Comparativo das 4 Versões do Solver. 

|**Versão**|**Média**|**Desvio**|**Tempo **|**(s)**<br>**Avaliações**|
|---|---|---|---|---|
|Baseline|306,00|0,00|0,65|3000|
|Tunado|306,00|0,00|0,66|5500|
|Surrogate|268,49|2,03|1,19|3000|
|Fuzzy|306,00|0,00|1,14|5500|



### **4.1 Discussão dos Resultados** 

- **Estagnação no Ótimo Real:** Baseline, Tunado e Fuzzy encontraram exatamente o mesmo ótimo (306,0) com desvio zero. Isso indica que, para esta instância pequena, o problema é relativamente fácil e as variações do GWO convergem para o mesmo ponto. 

- **Custo Computacional do Fuzzy:** O Fuzzy executou as mesmas 5500 avaliações que o Tunado (pois herdou _n_  wolves_ = 55 do Optuna) e demorou 1,14s contra 0,66s. Esse aumento de tempo é o custo da inferência das regras a cada geração. Contudo, o controle adaptativo permitiu que o algoritmo mantivesse um equilíbrio dinâmico entre exploração e explotação. 

- **O Falso Ótimo do Surrogate:** O Surrogate reportou a melhor média (268,49), mas isso é um artefato do erro da rede neural. O GWO otimizou a predição da rede, e não a realidade, demonstrando a importância da validação cruzada. 

4 

## **5 Conclusão** 

As implementações das Semanas 4 e 5 foram concluídas com sucesso. O modelo Surrogate mostrou-se uma alternativa viável para reduzir o custo computacional em instâncias complexas. O Controlador Fuzzy adicionou adaptabilidade ao GWO, provando-se uma ferramenta robusta para manter a diversidade populacional. Os dados e códigos gerados formam uma base sólida para a etapa de benchmarking estatístico (Semana 6). 

5 

