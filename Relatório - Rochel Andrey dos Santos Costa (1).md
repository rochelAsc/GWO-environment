# **Relatório Parcial: Sintonia de Hiperparâmetros do Grey Wolf Optimizer (GWO) via Optuna para Flow Shop** 

**Discente:** Rochel Andrey dos Santos Costa Matrícula: 2023090100 _Universidade Federal do Maranhão (UFMA)_ 

**Disciplina:** Sistemas Inteligentes 

**Docente:** Prof. Dr. Alexandre Cesar Muniz de Oliveira 26 de outubro de 2026 

## **1 Introdução** 

O problema de Flow Shop Permutacional (PFS) com datas de entrega ( _due dates_ ) é um clássico problema de otimização combinatória, classificado como NP-difícil. Neste contexto, metaheurísticas bioinspiradas têm se destacado na busca por soluções de alta qualidade em tempo computacional viável. Este relatório descreve a etapa de sintonia de hiperparâmetros do _Grey Wolf Optimizer_ (GWO), aplicado à minimização do atraso total ( _Tardiness_ ) em instâncias de PFS. 

O objetivo desta etapa (Semana 3) foi utilizar o _framework_ Optuna para encontrar uma combinação fixa de hiperparâmetros que minimizasse a função objetivo, comparando a configuração padrão da literatura ( _Baseline_ ) com a configuração otimizada ( _Tunada_ ). 

## **2 Metodologia** 

### **2.1 Representação e Decodificação** 

O GWO opera em um espaço de busca contínuo. Para aplicá-lo ao PFS (que é um problema discreto), cada lobo representa um vetor de chaves contínuas no intervalo [0 _,_ 1]<sup>_D_</sup> , onde _D_ é o número de _jobs_ . Essas chaves são decodificadas em uma permutação de tarefas utilizando a técnica de _Bucket Sort Decode_ . A função de _fitness_ é o _Tardiness_ total calculado pelo _FlowShopEngine_ . 

### **2.2 Sintonia com Optuna** 

Utilizou-se o Optuna com o amostrador TPE ( _Tree-structured Parzen Estimator_ ) para otimizar dois hiperparâmetros estáticos do GWO: 

- **Tamanho da população** ( _n_  wolves_ ): variando de 10 a 60, com passo de 5. 

1 

- **Estratégia de decaimento do coeficiente** _a_ ( _a_  decay_ ): escolhido entre _linear_ (canônico), _exponential_ ou _sqrt_ . 

O processo de tunagem foi realizado sobre um subconjunto de instâncias _Small_ , avaliando a média de 3 sementes aleatórias por _trial_ para garantir robustez estatística contra ruído. 

## **3 Resultados e Discussão** 

### **3.1 Processo de Otimização** 

A Figura 1 apresenta o histórico de otimização do Optuna ao longo dos _trials_ . Observa-se que o algoritmo explorou o espaço de busca e convergiu para uma combinação ótima. 



<!-- Start of picture text -->
2275 Histdrico de Otimizacgao (Optuna)<br>e e@ Objective Value<br>—— Best Value<br>2270<br>e<br>2265<br>vo e<br>2<br>S$ 2260<br>2<br>5<br>5 2255 ‘|<br>@ e<br>a ee<br>fo) ee<br>22502245 \ \ eee?e e<br>.<br>2240 jeeen oo<br>0 5 10 15 20 25 30<br>Trial<br><!-- End of picture text -->

Figura 1: Histórico de Otimização gerado pelo Optuna. 

A Figura 2 mostra a importância relativa dos hiperparâmetros. O Optuna identificou que a escolha do decaimento de _a_ (exponencial) teve um impacto ligeiramente superior ao tamanho da população para a estabilização do erro. 

2 



<!-- Start of picture text -->
Importancia dos Hiperparametros (Optuna)<br>a_decay | 0.03<br>—eee ["<br>0.0 0.2 0.4 0.6 0.8 1.0<br>Importancia Relativa<br><!-- End of picture text -->

Figura 2: Importância dos Hiperparâmetros no processo de otimização. 

### **3.2 Comparação Baseline vs. Tunado** 

A melhor configuração encontrada foi _n_  wolves_ = 55 com decaimento exponencial ( _a_ = 2(1 _−_ ( _t/T_ )<sup>2</sup> )). A Tabela 1 compara o desempenho do GWO com parâmetros padrão da literatura ( _Baseline_ ) contra a versão sintonizada. 

Tabela 1: Comparação de Desempenho: Baseline vs. Configuração Sintonizada. 

|**Configuração**|**Média**|**Desvio Padrão**|**Melhor**|
|---|---|---|---|
|Baseline (_n_= 30, linear)|573,34|4,81|571,8|
|Tunado (_n_= 55, exponencial)|572,17|1,40|571,8|
|**Variação (Ganho)**|**+0,20%**|**-70,89%**|-|



Embora o ganho na média tenha sido marginal (+0,20%), a redução no desvio padrão foi drástica (de 4,81 para 1,40). Isso indica que a configuração sintonizada é **muito mais robusta e previsível** . O decaimento exponencial mantém o coeficiente _a_ mais alto por mais tempo, preservando a exploração global do espaço de busca antes de convergir. A Figura 3 ilustra visualmente essa redução de variabilidade. 

3 



<!-- Start of picture text -->
Distribuigao do Tardiness (Instancias Small)<br>° °<br>1400 ° ° ° °<br>1200<br>® 1000<br>ira<br>vo<br>3 800<br>£<br>2<br>© 600<br>400<br>200<br>neat) ») ») neat)<br>pasein® (23 yne®" unegine ex?) poles?go (0230 ex? poise? ee ye?"<br><!-- End of picture text -->

Figura 3: Distribuição do Tardiness para as configurações Baseline e Tunada. 

Para validar estatisticamente essa diferença, aplicou-se o Teste de Wilcoxon aos resultados pareados das 30 execuções. O teste resultou em um p-valor _<_ 0 _,_ 05, confirmando que a superioridade da versão tunada é estatisticamente significativa. 

### **3.3 Custo Computacional e Generalização** 

O custo computacional foi avaliado (Figura 4). O aumento do tamanho da população para _n_ = 55 naturalmente incorreu em um tempo de execução maior por iteração, o que é um _trade-off_ aceitável em troca da maior confiabilidade dos resultados. 



<!-- Start of picture text -->
Tempo Médio de Execucao (Escala Logaritmica)<br>10? Porte da Instancia<br>mm Small<br>mmm Large<br>ry<br>8<br>2 10°<br>5<br>a<br>a<br>°<br>a—<br>a<br>: a Wy<br>nea”) 255, x?) _30, &#?) wine”<br>sine 9" odo acho 20 w-5"<br>pose! a pol pple<br><!-- End of picture text -->

Figura 4: Tempo médio de execução em escala logarítmica (Small vs Large). 

4 

Adicionalmente, a generalização foi testada em instâncias _Large_ (ex: 200 _×_ 20 e 500 _×_ 20). Os resultados mostraram que a configuração sintonizada para instâncias pequenas não se traduz automaticamente em ganhos para problemas de larga escala. Em uma das instâncias _Large_ , o Baseline obteve um _Tardiness_ ligeiramente menor, evidenciando a necessidade de abordagens adaptativas (como o Surrogate e Controle Fuzzy previstos para as próximas etapas). 

## **4 Conclusão** 

O uso do Optuna mostrou-se uma ferramenta valiosa não apenas para reduzir o erro médio, mas principalmente para estabilizar o GWO. A configuração sintonizada mitigou o risco de convergência prematura para ótimos locais, resultando em uma variabilidade 71% menor. Os dados coletados e os resultados estatísticos formam uma base sólida para o desenvolvimento das próximas etapas do projeto. 

## **Referências** 

- [1] MIRJALILI, S.; MIRJALILI, S. M.; LEWIS, A. _Grey Wolf Optimizer_ . Advances in Engineering Software, v. 69, p. 46–61, 2014. 

- [2] AKIBA, T. et al. _Optuna: A Next-generation Hyperparameter Optimization Framework_ . Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining, 2019. 

5 

