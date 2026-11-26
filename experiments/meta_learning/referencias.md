# Referências — Surrogate Modeling e Curvas de Aprendizagem

Este arquivo reúne referências utilizadas para fundamentar o experimento de curva de aprendizagem do surrogate de makespan no PFSP/Taillard. As referências estão classificadas por proximidade metodológica. A presença nesta lista não significa que todos os trabalhos estudem exatamente o mesmo problema.

## Evidência próxima de PFSP / flow shop

1. **José M. Framinan (2025).** *Combining Simulation and Gradient Boosted Trees for the Stochastic Permutation Flowshop Scheduling Problem.* IET Collaborative Intelligent Manufacturing, 7(1), e70049. DOI: [10.1049/cim2.70049](https://doi.org/10.1049/cim2.70049).
   - PFSP estocástico, makespan esperado, sequências/permutations e surrogate Gradient Boosted Trees integrado a GRASP.
   - Compara 10, 100 e 1.000 amostras de treinamento em instâncias pequenas (5 máquinas; 5, 10, 15 e 20 jobs). Reporta melhora da precisão à medida que aumenta o conjunto de treinamento; erro médio agregado aproximadamente 5%, 4% e abaixo de 3%, respectivamente.
   - Também usa as primeiras dez instâncias Taillard em uma etapa separada de avaliação do procedimento de busca. Não confundir esse teste com a experiência de tamanho amostral, cujas instâncias de treino foram geradas para o estudo e são pequenas.
   - Limitação para nosso caso: variante estocástica, GBT em vez de MLP, e até 20 jobs na análise de tamanho amostral.

2. **Roderich Wallrath e Meik B. Franke (2024).** *Integrating MILP, Discrete-Event Simulation, and Data-Driven Models for Distributed Flow Shop Scheduling Using Benders Cuts.* Processes, 12(8), 1772. DOI: [10.3390/pr12081772](https://doi.org/10.3390/pr12081772).
   - DPFSP com objetivo makespan e modelo data-driven baseado em MLPRegressor.
   - O modelo de demonstração foi treinado com 400.000 permutações aleatórias rotuladas por simulação. É uma referência de escala de dados e representação por permutação, não uma curva comparativa de tamanhos amostrais.
   - Limitação: DPFSP com três fábricas, modelo artificial para demonstrar integração Benders e não o PFSP Taillard de uma fábrica.

## Surrogates para otimização combinatória e scheduling

3. **Shulei Liu, Handing Wang, Wei Peng e Wen Yao (2024).** *Surrogate-Assisted Evolutionary Algorithms for Expensive Combinatorial Optimization: A Survey.* Complex & Intelligent Systems, 10, 5933–5949. DOI: [10.1007/s40747-024-01465-5](https://doi.org/10.1007/s40747-024-01465-5).
   - Revisão de SAEAs para otimização combinatória cara. Discute seleção, construção e gestão de surrogates, amostragem, diversidade e desafios de representar espaços discretos.
   - Fundamenta a necessidade de avaliar cobertura e gestão de amostras, não apenas aumentar N.

4. **Luyao Zhu, Fangfang Zhang, Xiaodong Zhu, Ke Chen e Mengjie Zhang (2023).** *Sample-Aware Surrogate-Assisted Genetic Programming for Scheduling Heuristics Learning in Dynamic Flexible Job Shop Scheduling.* Proceedings of the 2023 Genetic and Evolutionary Computation Conference (GECCO '23), 384–392. DOI: [10.1145/3583131.3590440](https://doi.org/10.1145/3583131.3590440).
   - Scheduling dinâmico em flexible job shop; surrogate k-NN sobre caracterizações fenotípicas de indivíduos de genetic programming.
   - Propõe estratégia sample-aware: a composição/seleção das amostras melhora a qualidade das heurísticas aprendidas sob orçamento de treino comparável.
   - Limitação: não é PFSP, não usa MLP sobre permutações e não isola uma curva de N para nosso problema.

5. **Tomohiro Harada (2023).** *A Pairwise Ranking Estimation Model for Surrogate-Assisted Evolutionary Algorithms.* Complex & Intelligent Systems, 9, 6875–6890. DOI: [10.1007/s40747-023-01113-4](https://doi.org/10.1007/s40747-023-01113-4).
   - Propõe ELDR, surrogate de ranking pareado, e avalia problemas contínuos de otimização com dimensões 20 e 100.
   - Compara conjuntos de treino de 2d e 5d amostras, teste independente de 10d e 20 repetições; usa Kendall tau como métrica de qualidade de ordenação. Também descreve LHS para amostras iniciais em sua integração SAEA.
   - Limitação: benchmarks contínuos, não scheduling/permutação; o modelo de ranking difere da nossa MLP de regressão.

## Fundamentação para ranking e seleção

6. **Gary Tom, Stanley Lo, Samantha Corapi, Alán Aspuru-Guzik e Benjamín Sánchez-Lengeling (2025).** *Ranking over Regression for Bayesian Optimization and Molecule Selection.* APL Machine Learning, 3, 036113. DOI: [10.1063/5.0272663](https://doi.org/10.1063/5.0272663).
   - Compara regressão e ranking pareado em seleção/otimização molecular.
   - Mostra por que a ordenação relativa pode ser mais importante que a precisão numérica quando o modelo é usado para selecionar candidatos.
   - Limitação: domínio molecular, não scheduling; evidência indireta para justificar Spearman/Kendall, top-k recall e regret como métricas adicionais.

## Fundamentação da progressão geométrica/logarítmica

7. **Mario Andrés Muñoz e Michael Kirley (2021).** *Sampling Effects on Algorithm Selection for Continuous Black-Box Optimization.* Algorithms, 14(1), 19. DOI: [10.3390/a14010019](https://doi.org/10.3390/a14010019).
   - Estuda efeitos do tamanho/amostragem sobre características e seleção automática de algoritmos em otimização contínua black-box.
   - Para comparar tamanhos amostrais, divide um intervalo entre 100D e 1.000D em cinco intervalos igualmente espaçados em escala logarítmica, resultando em fatores {100, 178, 316, 562, 1.000} × D; usa Latin Hypercube Sampling.
- Representando matematicamente os cinco níveis descritos no artigo, podemos escrever \(N_i = 10^{(2+i/4)}D\), para \(i=0,1,2,3,4\). Essa expressão é a reconstrução algébrica do espaçamento logarítmico e dos limites reportados (não uma transcrição de uma equação explicitamente numerada pelos autores).
   - É a justificativa metodológica mais direta, entre as referências consultadas, para usar níveis geometricamente espaçados em vez de incrementos lineares.
   - Limitação: domínio contínuo e amostragem de features ELA; não estabelece que a mesma curva seja ótima para PFSP. Usamos o princípio de espaçamento logarítmico como desenho de experimento, não os valores absolutos.

## Síntese e limites da evidência

- Há evidência próxima de PFSP de que mais dados podem reduzir erro (Framinan, 2025), mas o experimento é pequeno e usa GBT.
- Há evidência de que a seleção/composição das amostras pode importar (Zhu et al., 2023) e de que espaços combinatórios trazem desafios específicos (Liu et al., 2024).
- Há evidência indireta para medir ranking separadamente da regressão (Harada, 2023; Tom et al., 2025).
- A progressão geométrica é apoiada como desenho de curva de aprendizagem em seleção de algoritmos (Muñoz e Kirley, 2021), mas sua aplicação a nosso PFSP é uma decisão experimental a validar.
- Não foi encontrada, nesta busca, uma publicação que reproduza exatamente Taillard 100×10/500×20 + random keys + LHS + MLP 64×64 + curva de aprendizagem de surrogate de makespan. Essa lacuna deve ser explicitada no relatório, sem alegar que a literatura prova antecipadamente o resultado.
