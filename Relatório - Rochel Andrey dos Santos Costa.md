# Relatório Parcial: Sintonia de Hiperparâmetros do Grey Wolf Optimizer

# (GWO) via Optuna para Flow Shop

### Discente: Rochel Andrey dos Santos Costa Matrícula: 2023090100

### Universidade Federal do Maranhão (UFMA) Disciplina: Sistemas Inteligentes

### Docente: Prof. Dr. Alexandre Cesar Muniz de Oliveira 26 de outubro de 2026

## 1 Introdução

O problema de Flow Shop Permutacional (PFS) com datas de entrega (*due dates*) é um clássico problema de otimização combinatória, classificado como NP-difícil. Neste contexto, metaheurísticas bioinspiradas têm se destacado na busca por soluções de alta qualidade em tempo computacional viável. Este relatório descreve a etapa de sintonia de hiperparâmetros do *Grey Wolf Optimizer* (GWO), aplicado à minimização do atraso total (*Tardiness*) em instâncias de PFS. O objetivo desta etapa (Semana 3) foi utilizar o *framework* Optuna para encontrar uma combinação fixa de hiperparâmetros que minimizasse a função objetivo, comparando a configuração padrão da literatura (*Baseline*) com a configuração otimizada (*Tunada*).

## 2 Metodologia

### 2.1 Representação e Decodificação

O GWO opera em um espaço de busca contínuo. Para aplicá-lo ao PFS (que é um problema discreto), cada lobo representa um vetor de chaves contínuas no intervalo [0*,*1] *D*, onde *D* é o número de *jobs*. Essas chaves são decodificadas em uma permutação de tarefas utilizando a técnica de *Bucket Sort Decode*. A função de *fitness* é o *Tardiness* total calculado pelo *FlowShopEngine*.

### 2.2 Sintonia com Optuna

Utilizou-se o Optuna com o amostrador TPE (*Tree-structured Parzen Estimator*) para otimizar dois hiperparâmetros estáticos do GWO:

- **Tamanho da população** (*n*_*wolves*): variando de 10 a 60, com passo de 5.

- **Estratégia de decaimento do coeficiente** *a* (*a*_*decay*): escolhido entre *linear* (canônico), *exponential* ou *sqrt*.
O processo de tunagem foi realizado sobre um subconjunto de instâncias *Small*, avaliando a média de 3 sementes aleatórias por *trial* para garantir robustez estatística contra ruído.

## 3 Resultados e Discussão

### 3.1 Processo de Otimização

A Figura 1 apresenta o histórico de otimização do Optuna ao longo dos *trials*. Observa-se que o algoritmo explorou o espaço de busca e convergiu para uma combinação ótima.

Figura 1: Histórico de Otimização gerado pelo Optuna.

A Figura 2 mostra a importância relativa dos hiperparâmetros. O Optuna identificou que a escolha do decaimento de *a* (exponencial) teve um impacto ligeiramente superior ao tamanho da população para a estabilização do erro.

Figura 2: Importância dos Hiperparâmetros no processo de otimização.

### 3.2 Comparação Baseline vs. Tunado

A melhor configuração encontrada foi *n*_*wolves* = 55 com decaimento exponencial (*a* = 2(1 *−* (*t/T*) 2 )). A Tabela 1 compara o desempenho do GWO com parâmetros padrão da literatura (*Baseline*) contra a versão sintonizada.

<u>Tabela 1: Comparação de Desempenho: Baseline vs. Configuração Sintonizada.</u>

|Configuração|Média|Desvio Padrão|Melhor|
|---|---|---|---|
|Baseline ( n = 30, linear)|573,34|4,81|571,8|
|Tunado ( n = 55, exponencial)|572,17|1,40|571,8|
|Variação (Ganho)|+0,20%|-70,89%|-|

Embora o ganho na média tenha sido marginal (+0,20%), a redução no desvio padrão foi drástica (de 4,81 para 1,40). Isso indica que a configuração sintonizada é **muito mais** **robusta e previsível**. O decaimento exponencial mantém o coeficiente *a* mais alto por mais tempo, preservando a exploração global do espaço de busca antes de convergir. A

Figura 3 ilustra visualmente essa redução de variabilidade.

Figura 3: Distribuição do Tardiness para as configurações Baseline e Tunada.

Para validar estatisticamente essa diferença, aplicou-se o Teste de Wilcoxon aos resul- tados pareados das 30 execuções. O teste resultou em um p-valor *<* 0*,*05, confirmando que a superioridade da versão tunada é estatisticamente significativa.

### 3.3 Custo Computacional e Generalização

O custo computacional foi avaliado (Figura 4). O aumento do tamanho da população para *n* = 55 naturalmente incorreu em um tempo de execução maior por iteração, o que é um *trade-off* aceitável em troca da maior confiabilidade dos resultados.

Figura 4: Tempo médio de execução em escala logarítmica (Small vs Large).

Adicionalmente, a generalização foi testada em instâncias *Large* (ex: 200*×*20 e 500*×*

20). Os resultados mostraram que a configuração sintonizada para instâncias pequenas não se traduz automaticamente em ganhos para problemas de larga escala. Em uma das instâncias *Large*, o Baseline obteve um *Tardiness* ligeiramente menor, evidenciando a necessidade de abordagens adaptativas (como o Surrogate e Controle Fuzzy previstos para as próximas etapas).
## 4 Conclusão

O uso do Optuna mostrou-se uma ferramenta valiosa não apenas para reduzir o erro médio, mas principalmente para estabilizar o GWO. A configuração sintonizada mitigou o risco de convergência prematura para ótimos locais, resultando em uma variabilidade 71% menor. Os dados coletados e os resultados estatísticos formam uma base sólida para o desenvolvimento das próximas etapas do projeto.

## Referências

[1] MIRJALILI, S.; MIRJALILI, S. M.; LEWIS, A. *Grey Wolf Optimizer*. Advances in Engineering Software, v. 69, p. 46–61, 2014.

[2] AKIBA, T. et al. *Optuna: A Next-generation Hyperparameter Optimization Fra-* *mework*. Proceedings of the 25th ACM SIGKDD International Conference on Kno- wledge Discovery & Data Mining, 2019.
