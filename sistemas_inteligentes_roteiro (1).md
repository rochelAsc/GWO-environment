## Semana 1 (09/10): Apresentação da Pesquisa sobre um Solver Bioinspirado

- **Instruções ao Aluno:** Escolha um algoritmo bioinspirado da literatura (ex: *Particle* *Swarm Optimization-PSO, Ant Colony Optimization-ACO, Firefly, Bat, Gray Wolf,* *Estimation of Distribution Algorithm-EDA, ABC-Bee Colony*). Analise o funcionamento dos operadores biológicos/naturais que sustentam o algoritmo e identifique as variáveis críticas de estado (ex: diversidade populacional, taxa de convergência).
- **Entregável:** Apresentação (Slides em PDF) e documento de 2 páginas contendo: o Formulação matemática dos operadores do algoritmo. o Mapeamento de entradas, saídas e representação dos indivíduos/partículas. o Função de aptidão (*fitness*) e espaço de busca inicial selecionados para os
testes.

## Semana 2(16/10): Implementação e Teste do Solver (Versão Baseline)

- **Instruções ao Aluno:** Codifique a versão canônica do algoritmo do zero (em Python ou C/C++), evitando frameworks prontos para a lógica do solver em si. Avalie a corretude da implementação aplicando o solver em pelo menos duas funções de teste (***benchmarks* de Taillard para o Flowshop Permutacional-PFS**) com parâmetros padrão da literatura.
- **Entregável:** o Código-fonte modularizado e documentado. o Gráfico do histórico de convergência (Aptidão vs. Gerações/Iterações)
mostrando média e desvio padrão de 30 execuções independentes.

## Semana 3 (23/10): Sintonia do Solver (Hiperparâmetros via Optuna)

- **Instruções ao Aluno:** Utilize o *framework* **Optuna** para realizar a otimização dos hiperparâmetros estáticos do seu solver (ex: tamanho da população, taxa de mutação, fator de escala $F$, constante cognitiva/social $c_1, c_2$). O objetivo do Optuna é encontrar a combinação fixa de parâmetros que minimiza o valor final da função objetivo no limite de iterações.
- **Entregável:** o Script de integração Optuna + Solver. o Gráficos de Importância de Hiperparâmetros (*Hyperparameter Importance*) e
Histórico de Otimização gerados pelo Optuna.

o Tabela comparativa: Configuração Padrão (*Baseline*) vs. Configuração Sintetizada (*Tunada*).

## Semana 4 (30/10): Treino do Surrogate (Rede Neural para Função Objetivo) [1,5 Pontos]

- **Instruções ao Aluno:** Em problemas reais de engenharia, a função objetivo pode exigir simulações dispendiosas (ex: CFD ou FEA). Substitua a função objetivo por um **Modelo** **Surrogate** (Rede Neural Multilayer Perceptron ou RBF). Colete um conjunto de dados ($X$: soluções, $y$: aptidão real), treine a rede e utilize as predições da rede no loop do solver bioinspirado.
- **Entregável:** o Pipeline de amostragem de dados (ex: *Latin Hypercube Sampling*- LHS) e
treinamento da RNA.

o Relatório de métricas de regressão da RNA ($MSE$, $RMSE$, $R^2$).

o Comparativo de desempenho e ganho computacional (tempo de execução) entre a avaliação real e a avaliação via Surrogate.

## Semana 5 (06/11): Controle Fuzzy Adaptativo do Solver [1,5 Pontos]

- **Instruções ao Aluno:** Diferente da sintonia estática (Semana 3), o controle adaptativo altera os parâmetros do solver em *tempo de execução*. Utilize os dados obtidos com o Optuna para criar um **Mapeamento/Sistema de Inferência Fuzzy (Mamdani ou Takagi-** **Sugeno)**. As entradas do sistema Fuzzy devem ser variáveis de estado do solver (ex: *Diversidade da População* e *Estagnação*) e a saída deve ajustar dinamicamente um parâmetro dinâmico (ex: *Taxa de Mutação* ou *Inércia*).
- **Entregável:** o Definição das funções de pertinência, variáveis linguísticas e base de regras do
Controlador Fuzzy.

o Código do Solver integrado ao controlador Fuzzy executando a cada geração.

o Gráfico temporal exibindo a variação dinâmica do parâmetro ajustado ao longo das gerações.

## Semana 6 (13/11): Espaço de Desempenho e Benchmarking [1,5 Pontos]

- **Instruções ao Aluno:** Submeta as 4 versões do solver (**Baseline**, **Tunado/Optuna**, **Surrogate** e **Fuzzy Adaptativo**) a um conjunto diversificado de instâncias de problemas (variando dimensão, multimodalidade e desconexão do espaço de busca). Realize testes estatísticos rigorosos para validar os resultados.
- **Entregável:** o **Tabela de Desempenho Comparativa** contemplando: Média, Mediana, Desvio
Padrão, Tempo Computacional e NÚMERO de avaliações da função objetivo.

o Aplicação de testes estatísticos de hipótese (média + desvio padrão) para comprovar a superioridade estatística entre as versões.

## Semana 7(20/11): Meta-Learning (Metacaracterização e Recomendação) [1,5 Pontos]

- **Instruções ao Aluno:** O objetivo do Meta-Learning é prever *qual* versão do solver performará melhor sem precisar executar todas. Extraia metacaracterísticas das instâncias dos problemas (ex: rugosidade da paisagem de aptidão, convexidade, dimensão, estatísticas de gradiente amostrado) e monte uma **Tabela Meta-Dataset**. Treine um classificador (ex: Random Forest ou Decision Tree) que receba as metacaracterísticas da instância e recomende o algoritmo do Espaço de Desempenho ideal.
- **Entregável:** o Conjunto de metacarakterísticas calculadas para as instâncias de teste. o Algoritmo de meta-classificação treinado e avaliado (Acurácia, F1-Score e
Matriz de Confusão).

o Árvore de decisão ou regras extraídas mostrando a lógica de recomendação do solver.

## Semana 8 (27/11): Relatório Final

- **Instruções ao Aluno:** Consolide todo o trabalho desenvolvido ao longo do semestre no formato de um artigo científico completo (SBC, IEEE ou similar). A escrita deve ser rigorosa, integrando os resultados parciais acumulados das Semanas 1 a 7.
- **Entregável:** o **Artigo Científico em PDF** (8 a 10 páginas) estruturado em: Introdução,
Referencial Teórico, Metodologia, Experimentos e Resultados (com tabelas e estatísticas das etapas 3 a 7), Discussão e Conclusão.

o Repositório do GitHub limpo, com instruções claras de reprodução no arquivo README.md.
