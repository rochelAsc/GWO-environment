# Realize uma revisão de literatura aplicada ao planejamento de um estudo sobre Gr

**Question:** Realize uma revisão de literatura aplicada ao planejamento de um estudo sobre Grey Wolf Optimizer (GWO) para Permutation Flow Shop Scheduling Problem (PFSP), com foco em decisões metodológicas antes de implementar novas variantes. Organize a investigação em quatro partes encadeadas: (1) Seleção de instâncias Taillard: como escolher um subconjunto representativo de instâncias para benchmarking sem cherry-picking? Identifique recomendações metodológicas, dimensões relevantes (número de jobs, máquinas, razão n/m, dificuldade/qualidade dos BKS, famílias/tamanhos), cobertura estratificada, quantidade razoável de instâncias e sementes, e limitações de usar apenas poucas instâncias. Diferencie selecionar instâncias para desenvolvimento de algoritmo e para avaliação final/holdout. (2) GWO contínuo aplicado a permutações via Random Keys e decodificação por ordenação: precedentes, vantagens, limitações conhecidas da representação/operadores contínuos em problemas permutacionais, questões de muitos-para-um, neutralidade, colisões, perda de diversidade e estrutura de vizinhança. (3) Variantes de GWO aplicadas a PFSP e problemas de scheduling relacionados: identifique variantes discretas, híbridas, dinâmicas/adaptativas, multiobjetivo, distributed PFSP e outras, mas classifique claramente o problema estudado para não misturar PFSP clássico com distributed PFSP, setup times, manutenção, energia etc. Para cada variante, explique qual deficiência do GWO original ela tenta corrigir (exploração/explotação, convergência prematura, diversidade, representação discreta, intensificação/local search, inicialização, estagnação, escalabilidade, multiobjetivo), quais mecanismos introduz e quais evidências de desempenho oferece. (4) Síntese de lacunas e desenho experimental: proponha uma matriz de comparação de variantes e um protocolo justo (mesmas instâncias, sementes, orçamento de avaliações exatas, tempo de CPU, parâmetros, baselines NEH/IG quando viável, BKS/RPD, testes estatísticos, ablação, sensibilidade e análise de convergência). Priorize artigos peer-reviewed, clássicos e recentes até 2026, forneça DOI/links e sinalize claramente quando só há evidência de abstract ou quando os resultados não são diretamente comparáveis. Não afirme lacunas como inéditas sem evidência. Entregue recomendações operacionais para o projeto GWO-environment e ressalvas sobre o escopo.

# **GWO** para **PFSP**: Revisão Metodológica Antes de Implementar Variantes

Esta revisão mapeia decisões metodológicas para um estudo de Grey Wolf Optimizer aplicado ao PFSP clássico com minimização de makespan, cobrindo seleção de instâncias, representação contínua via Random Keys, variantes existentes e protocolo experimental. A evidência disponível é majoritariamente de abstracts para as variantes GWO recentes, o que limita comparações diretas de desempenho.

## Seleção de Instâncias Taillard

O benchmark de Taillard (1993) permanece o padrão de facto, mas sua capacidade discriminante é limitada: benchmarks existentes mostram problemas de poder discriminante e desafios para análise estatística [[1.1]](https://consensus.app/papers/vallada-ruíz-new-hard-benchmark-for-flowshop-scheduling/w:defc0e80-6887-4907-a4a2-10dd1971f962/). Um benchmark ideal deve ser exaustivo, adequado à análise estatística e discriminante entre algoritmos [[1.2]](https://consensus.app/papers/vallada-ruíz-new-hard-benchmark-for-flowshop-scheduling/w:defc0e80-6887-4907-a4a2-10dd1971f962/), e benchmarks mais duros que o de Taillard já foram construídos (240 instâncias grandes e 240 pequenas, até 800 jobs e 60 máquinas) [[1.3]](https://consensus.app/papers/vallada-ruíz-new-hard-benchmark-for-flowshop-scheduling/w:defc0e80-6887-4907-a4a2-10dd1971f962/) [[1.4]](https://consensus.app/papers/vallada-ruíz-new-hard-benchmark-for-flowshop-scheduling/w:defc0e80-6887-4907-a4a2-10dd1971f962/).

A cobertura estratificada por tamanho é a prática observada: avaliações recentes usam as 120 instâncias de Taillard com 20 execuções independentes por instância [[2.1]](https://consensus.app/papers/silvamuñoz-palma-a-hybrid-bacterial-foraging-optimization-algorithm/w:0fadb05b-c7d0-4a55-89bb-595838d0afff/), ou 13 instâncias cobrindo 20–200 jobs e 5–20 máquinas com 50 execuções [[3.1]](https://consensus.app/papers/mzili-torki-hybrid-grey-wolf-and-genetic-algorithm-for-the/w:9f4d477d-58b5-47e0-82c8-dac95f775e6e/), ou ainda 15 instâncias [[4.1]](https://consensus.app/papers/mzili-torki-a-novel-hybrid-recruit-simulated-annealing-and-rat/w:5d659823-c054-438d-932e-7aebe3b4c927/). Usar poucas instâncias é arriscado: o desempenho varia entre famílias de Taillard, com desvio médio e variabilidade distintos por família [[2.2]](https://consensus.app/papers/silvamuñoz-palma-a-hybrid-bacterial-foraging-optimization-algorithm/w:0fadb05b-c7d0-4a55-89bb-595838d0afff/).

| Dimensão | Recomendação | Evidência |
|---|---|---|
| Tamanho do conjunto | 120 instâncias (padrão) ou subconjunto estratificado ≥13–15 | [[2.1]](https://consensus.app/papers/silvamuñoz-palma-a-hybrid-bacterial-foraging-optimization-algorithm/w:0fadb05b-c7d0-4a55-89bb-595838d0afff/) [[3.1]](https://consensus.app/papers/mzili-torki-hybrid-grey-wolf-and-genetic-algorithm-for-the/w:9f4d477d-58b5-47e0-82c8-dac95f775e6e/) |
| Sementes/execuções | 20–50 execuções independentes por instância | [[2.1]](https://consensus.app/papers/silvamuñoz-palma-a-hybrid-bacterial-foraging-optimization-algorithm/w:0fadb05b-c7d0-4a55-89bb-595838d0afff/) [[3.1]](https://consensus.app/papers/mzili-torki-hybrid-grey-wolf-and-genetic-algorithm-for-the/w:9f4d477d-58b5-47e0-82c8-dac95f775e6e/) |
| Estratificação | Cobrir famílias por jobs × máquinas (20–200 jobs, 5–20 máquinas) | [[3.1]](https://consensus.app/papers/mzili-torki-hybrid-grey-wolf-and-genetic-algorithm-for-the/w:9f4d477d-58b5-47e0-82c8-dac95f775e6e/) |
| Métrica | RPD vs. BKS + variabilidade entre execuções | [[2.3]](https://consensus.app/papers/silvamuñoz-palma-a-hybrid-bacterial-foraging-optimization-algorithm/w:0fadb05b-c7d0-4a55-89bb-595838d0afff/) |
| Holdout | Separar instâncias de desenvolvimento das de avaliação final | [[1.5]](https://consensus.app/papers/vallada-ruíz-new-hard-benchmark-for-flowshop-scheduling/w:defc0e80-6887-4907-a4a2-10dd1971f962/) |

**Figure 1:** Dimensões de estratificação para seleção de instâncias Taillard

A distinção desenvolvimento/holdout não é explicitada nos papers fornecidos, mas o princípio de que benchmarks duros com grande poder discriminante permitem ascertainar com pouca experimentação se um método supera o estado da arte [[1.5]](https://consensus.app/papers/vallada-ruíz-new-hard-benchmark-for-flowshop-scheduling/w:defc0e80-6887-4907-a4a2-10dd1971f962/) sustenta separar instâncias de tuning das de avaliação final. A qualidade dos BKS importa: bounds melhorados em 112 de 120 instâncias Taillard [[5.1]](https://consensus.app/papers/alejandrosoto-segura-bounds-for-the-permutation-flowshop-scheduling/w:f7ce986d-120f-4aeb-8631-c3d9f5c3049c/) e BKS ainda sendo atualizados (ex.: Ta005 e Ta068) [[6.1]](https://consensus.app/papers/lu-yuan-an-optimized-method-for-solving-the-green/w:dd5e2dcb-8c87-4c6b-b6f4-5568be5088ef/) significam que RPDs calculados contra BKS desatualizados são enganosos.

## GWO Contínuo via Random Keys

O GWO é um metaheurístico inspirado na caça de lobos cinzentos, com três líderes (α, β, δ) guiando o grupo [[7.1]](https://consensus.app/papers/chen-zheng-hybrid-grey-wolf-optimizer-for-solving-permutation/w:2e11417b-952c-453c-a17b-af035db81f43/) [[7.2]](https://consensus.app/papers/chen-zheng-hybrid-grey-wolf-optimizer-for-solving-permutation/w:2e11417b-952c-453c-a17b-af035db81f43/), e destaca-se por convergência rápida e mecanismo de busca simples [[7.3]](https://consensus.app/papers/chen-zheng-hybrid-grey-wolf-optimizer-for-solving-permutation/w:2e11417b-952c-453c-a17b-af035db81f43/). Para problemas permutacionais, a decodificação por ordenação é o precedente documentado: o método Large Rank Value (LRV) converte posições contínuas em sequência de jobs [[8.1]](https://consensus.app/papers/alimron-utama-an-energyefficient-no-idle-permutations-flow-shop/w:ad3c1d79-ce85-4c53-b767-fe15f9402f19/) [[8.2]](https://consensus.app/papers/alimron-utama-an-energyefficient-no-idle-permutations-flow-shop/w:ad3c1d79-ce85-4c53-b767-fe15f9402f19/), descrito como procedimento simples e eficaz [[8.3]](https://consensus.app/papers/alimron-utama-an-energyefficient-no-idle-permutations-flow-shop/w:ad3c1d79-ce85-4c53-b767-fe15f9402f19/). A regra SPV (smallest-position-value) cumpre papel análogo em GWO híbrido para PFSP [[7.4]](https://consensus.app/papers/chen-zheng-hybrid-grey-wolf-optimizer-for-solving-permutation/w:2e11417b-952c-453c-a17b-af035db81f43/).

As limitações da representação contínua são reconhecidas indiretamente: variantes discretas propõem mecanismos de atualização populacional específicos para o problema [[9.1]](https://consensus.app/papers/chen-zheng-discrete-gray-wolf-optimizer-for-solving/w:73328cf9-2c4a-44da-9b4c-5f6c559a064a/) [[10.1]](https://consensus.app/papers/chen-zheng-a-cooperative-grey-wolf-optimizer-for-the-joint/w:226a66aa-82c7-4481-89c9-7e2e6106cdeb/), sugerindo que operadores contínuos não bastam. A questão muitos-para-um, neutralidade e colisões não é tratada explicitamente nos papers fornecidos — uma lacuna de evidência que deve ser sinalizada, não afirmada como inédita. A perda de diversidade é endereçada por inicializações híbridas (NEH melhorado + mapa caótico tent) [[7.5]](https://consensus.app/papers/chen-zheng-hybrid-grey-wolf-optimizer-for-solving-permutation/w:2e11417b-952c-453c-a17b-af035db81f43/) e por mecanismos de reinício [[11.1]](https://consensus.app/papers/sun-sang-efficient-multistart-gray-wolf-optimization/w:0ed6d87b-31d9-4879-88d4-83a40c08dd92/).

## Variantes de GWO: Classificação por Problema

A tabela abaixo separa claramente o problema estudado, evitando misturar PFSP clássico com variantes.

| Variante | Problema | Deficiência corrigida | Mecanismo | Evidência |
|---|---|---|---|---|
| HGWO [[7.6]](https://consensus.app/papers/chen-zheng-hybrid-grey-wolf-optimizer-for-solving-permutation/w:2e11417b-952c-453c-a17b-af035db81f43/) | PFSP clássico | Convergência lenta, ótimo local | NEH+caos, levy flight, crossover/mutação, VND | Supera comparados em Taillard [[7.7]](https://consensus.app/papers/chen-zheng-hybrid-grey-wolf-optimizer-for-solving-permutation/w:2e11417b-952c-453c-a17b-af035db81f43/) |
| DGWO [[9.2]](https://consensus.app/papers/chen-zheng-discrete-gray-wolf-optimizer-for-solving/w:73328cf9-2c4a-44da-9b4c-5f6c559a064a/) | Distributed PFSP | Representação discreta | ENEH2, atualização discreta, VND | Wilcoxon/Friedman [[9.3]](https://consensus.app/papers/chen-zheng-discrete-gray-wolf-optimizer-for-solving/w:73328cf9-2c4a-44da-9b4c-5f6c559a064a/) |
| DGWO_RM [[11.2]](https://consensus.app/papers/sun-sang-efficient-multistart-gray-wolf-optimization/w:0ed6d87b-31d9-4879-88d4-83a40c08dd92/) | DPFSP + manutenção | Convergência prematura | Reinício, 4 buscas locais | Supera 4 algoritmos [[11.3]](https://consensus.app/papers/sun-sang-efficient-multistart-gray-wolf-optimization/w:0ed6d87b-31d9-4879-88d4-83a40c08dd92/) |
| GWO_VNS [[12.1]](https://consensus.app/papers/pesaru-saddikuti-hybrid-greywolf-algorithm-approach-for-solving/w:be904180-a0c8-4459-b0dc-cc58b7125f20/) | PFSP + setup + energia | Multiobjetivo | VNS | 33,25% melhoria FT [[12.2]](https://consensus.app/papers/pesaru-saddikuti-hybrid-greywolf-algorithm-approach-for-solving/w:be904180-a0c8-4459-b0dc-cc58b7125f20/) |
| QMOGWO [[13.1]](https://consensus.app/papers/zheng-chen-a-qlearning-multiobjective-grey-wolf-optimizer-for/w:0ee03099-9c47-4d01-b298-a32ab346ccfd/) | Distributed hybrid FSP | Multiobjetivo, ótimo local | Q-learning | Supera comparados [[13.2]](https://consensus.app/papers/zheng-chen-a-qlearning-multiobjective-grey-wolf-optimizer-for/w:0ee03099-9c47-4d01-b298-a32ab346ccfd/) |

**Figure 2:** Classificação de variantes GWO por tipo de problema de scheduling

Variantes adicionais incluem CGWO para joint flowshop com setup times [[10.2]](https://consensus.app/papers/chen-zheng-a-cooperative-grey-wolf-optimizer-for-the-joint/w:226a66aa-82c7-4481-89c9-7e2e6106cdeb/), DGWO_Q para distributed blocking flowshop com manutenção e setup [[14.1]](https://consensus.app/papers/sun-sang-a-metaheuristic-algorithm-codriven-by-qlearning/w:a6692a4f-5783-4508-b7f2-924661064984/), e GWO-GA híbrido para FSSP clássico [[3.2]](https://consensus.app/papers/mzili-torki-hybrid-grey-wolf-and-genetic-algorithm-for-the/w:9f4d477d-58b5-47e0-82c8-dac95f775e6e/). A motivação recorrente é que o GWO tem estrutura simples e poucos parâmetros [[9.4]](https://consensus.app/papers/chen-zheng-discrete-gray-wolf-optimizer-for-solving/w:73328cf9-2c4a-44da-9b4c-5f6c559a064a/), mas sofre de convergência prematura e desequilíbrio exploração/explotação [[7.8]](https://consensus.app/papers/chen-zheng-hybrid-grey-wolf-optimizer-for-solving-permutation/w:2e11417b-952c-453c-a17b-af035db81f43/).

## Protocolo Experimental e Lacunas

A comparabilidade é o problema central: a maioria dos métodos propostos não é comparada adequadamente com procedimentos existentes, tornando impossível saber quais são os mais eficientes [[15.1]](https://consensus.app/papers/fernándezviagas-ruíz-a-new-vision-of-approximate-methods-for-the/w:021b4953-0c7a-474e-bc75-454baec8e907/). Comparações justas exigem recodificação sob as mesmas condições e múltiplos critérios de parada [[15.2]](https://consensus.app/papers/fernándezviagas-ruíz-a-new-vision-of-approximate-methods-for-the/w:021b4953-0c7a-474e-bc75-454baec8e907/) [[15.3]](https://consensus.app/papers/fernándezviagas-ruíz-a-new-vision-of-approximate-methods-for-the/w:021b4953-0c7a-474e-bc75-454baec8e907/), além de pseudo-código claro para reprodutibilidade [[15.4]](https://consensus.app/papers/fernándezviagas-ruíz-a-new-vision-of-approximate-methods-for-the/w:021b4953-0c7a-474e-bc75-454baec8e907/).

Recomendações operacionais para o projeto GWO-environment:

- **Baselines**: incluir NEH e IG, dado que métodos simples de busca local superam abordagens complexas no PFSP [[16.1]](https://consensus.app/papers/pan-ruíz-local-search-methods-for-the-flowshop-scheduling/w:07ba1f57-e94c-468f-a672-7d13725eb292/) e o IG está entre os melhores para flowtime [[16.2]](https://consensus.app/papers/pan-ruíz-local-search-methods-for-the-flowshop-scheduling/w:07ba1f57-e94c-468f-a672-7d13725eb292/).
- **Métricas**: RPD vs. BKS com variabilidade entre execuções [[2.3]](https://consensus.app/papers/silvamuñoz-palma-a-hybrid-bacterial-foraging-optimization-algorithm/w:0fadb05b-c7d0-4a55-89bb-595838d0afff/), reportando best-run e desvio [[2.4]](https://consensus.app/papers/silvamuñoz-palma-a-hybrid-bacterial-foraging-optimization-algorithm/w:0fadb05b-c7d0-4a55-89bb-595838d0afff/).
- **Testes estatísticos**: Friedman e Wilcoxon são padrão [[7.7]](https://consensus.app/papers/chen-zheng-hybrid-grey-wolf-optimizer-for-solving-permutation/w:2e11417b-952c-453c-a17b-af035db81f43/) [[9.3]](https://consensus.app/papers/chen-zheng-discrete-gray-wolf-optimizer-for-solving/w:73328cf9-2c4a-44da-9b4c-5f6c559a064a/), com ANOVA/Tukey quando aplicável [[3.1]](https://consensus.app/papers/mzili-torki-hybrid-grey-wolf-and-genetic-algorithm-for-the/w:9f4d477d-58b5-47e0-82c8-dac95f775e6e/).
- **Ablação e sensibilidade**: isolar contribuição de inicialização e busca local [[9.5]](https://consensus.app/papers/chen-zheng-discrete-gray-wolf-optimizer-for-solving/w:73328cf9-2c4a-44da-9b4c-5f6c559a064a/), e testar parâmetros [[17.1]](https://consensus.app/papers/utama-hybrid-grey-wolf-algorithm-for-energyefficient/w:76fb912e-2501-4cd8-908e-8efee9a0aef0/).

Illustration of a typical PFSP problem [[8]](https://consensus.app/papers/alimron-utama-an-energyefficient-no-idle-permutations-flow-shop/w:ad3c1d79-ce85-4c53-b767-fe15f9402f19/)

*How to read: Diagrama esquemático de um PFSP: jobs fluem em série pelas máquinas na mesma ordem; cada linha é um job e cada coluna uma máquina, com os blocos representando tempos de processamento.*
**Figure 3:** Estrutura esquemática do problema de flow shop por permutação

Ressalvas de escopo: as variantes GWO recentes (DGWO, DGWO_RM, QMOGWO, DGWO_Q, CGWO) têm evidência apenas de abstract nos dados fornecidos, e seus resultados não são diretamente comparáveis entre si por diferirem em problema, instâncias e baselines. A ausência de tratamento explícito de muitos-para-um e neutralidade na literatura fornecida não autoriza afirmar que sejam lacunas inéditas. Para o PFSP clássico com makespan, o HGWO [[7.6]](https://consensus.app/papers/chen-zheng-hybrid-grey-wolf-optimizer-for-solving-permutation/w:2e11417b-952c-453c-a17b-af035db81f43/) é o precedente mais direto, e o protocolo deve espelhar a rigorosa avaliação comparativa que estabeleceu o estado da arte em heurísticas [[15.5]](https://consensus.app/papers/fernándezviagas-ruíz-a-new-vision-of-approximate-methods-for-the/w:021b4953-0c7a-474e-bc75-454baec8e907/).
 
_These search results were found and analyzed using Consensus, an AI-powered search engine for research. Try it at https://consensus.app. © 2026 Consensus NLP, Inc. Personal, non-commercial use only; redistribution requires copyright holders’ consent._
 
## References
 
`1.` Vallada E, Ruíz R, Framiñán JM. New hard benchmark for flowshop scheduling problems minimising makespan. *European Journal of Operational Research.* 2014;240:666-677. doi:10.1016/j.ejor.2014.07.033
 
> [1.1] Additionally, existing flowshop benchmarks have already shown problems regarding discriminant power and also present challenges as regards the statistical analysis of results. (Conclusion)
 
> [1.2] The new proposed benchmark complies with the desired characteristics of a good benchmark, that is, it is exhaustive, amenable for statistical analysis and discriminant when several algorithms are compared. (Conclusion)
 
> [1.3] The new benchmark consists of two separated sets of instances, small and large, with 240 instances each one. (Conclusion)
 
> [1.4] The new benchmark consists of 240 large instances and 240 small instances with up to 800 jobs and 60 machines. (Abstract)
 
> [1.5] Ideally, hard benchmarks with great discriminant power are preferred so that with little experimentation, researchers can ascertain if a given method outperforms the existing state-of-the-art. (Conclusion)
 
`2.` Silva-Muñoz M, Palma M, Fuertes G, et al. A hybrid bacterial foraging optimization algorithm for makespan minimization in permutation flow shop scheduling. *International Journal of Industrial Engineering Computations.* 2026;17:1933-1944. doi:10.5267/j.ijiec.2026.6.005
 
> [2.1] HBFO is evaluated on Taillard's 120 benchmark instances using 20 independent runs per instance. (Abstract)
 
> [2.2] Configuration-level summaries further indicate that both average deviation and variability vary across Taillard instance families. (Abstract)
 
> [2.3] Performance is assessed using the best-run makespan, the relative percentage deviation (RPD) relative to best-known reference values, and run-to-run variability. (Abstract)
 
> [2.4] Compared with recent advanced metaheuristics reported on the same benchmark families, HBFO achieves the best or tied-best best-run makespan in 115 of the 120 instances, with five instances where another method attains a lower best-run value. (Abstract)
 
`3.` Mzili M, Torki M, Mzili T, et al. Hybrid Grey Wolf and Genetic Algorithm for the Flow Shop Scheduling Problem. *International Journal of Innovative Technology and Interdisciplinary Sciences.* 2025;8. doi:10.15157/ijitis.2025.8.3.666-686
 
> [3.1] Evaluated on 13 Taillard benchmark instances (20-200 jobs, 5-20 machines) over 50 runs, the GWO-GA algorithm demonstrates superior performance compared to established metaheuristics, including SGA, HMSA, NEH, DDE-PFS, DSADE-PFS, and DSADEPFS, with statistical validation via ANOVA and Tukey HSD tests. (Abstract)
 
> [3.2] This study introduces a novel hybrid metaheuristic that integrates Grey Wolf Optimization (GWO) for robust global exploration with Genetic Algorithm (GA) for precise local exploitation, augmented by adaptive crossover, mutation, and 2-opt local search, addressing a significant gap in synthesizing swarm intelligence and evolutionary techniques for permutation-based scheduling. (Abstract)
 
`4.` Mzili M, Torki M, Mzili T, Amine MB, Bačanin N, Shaheen M. A Novel Hybrid Recruit Simulated Annealing and Rat Swarm Optimization Algorithm for Permutation Flow Shop Scheduling. *Engineering Reports.* 2026;8:e70724. doi:10.1002/eng2.70724
 
> [4.1] Experiments used 15 Taillard benchmark instances, comparing HRSA-RSO against 10 state-of-the-art metaheuristics: Spotted Hyena Optimization (SHOA) [13], Hybrid Particle Swarm Optimization (HPSO) [21], Genetic Algorithm (GA) [12], Discrete Whale Optimization Algorithm (DWOA) [14], Moth Flame Optimization (MFO) [13], Monarch Butterfly Optimization (MBO) [13], Ant Colony Optimization (ACO) [13], Iterated Greedy Algorithm (IGA) [13], Differential Evolution (DE) [13], and Tabu Search (TS) [31]. (Results)
 
`5.` Alejandro-Soto JA, Segura C, Trejo-Sánchez JA. Bounds for the permutation flowshop scheduling problem: New framework and theoretical insights. *Computers & Operations Research.* 2026;191:107445-107445. doi:10.1016/j.cor.2026.107445
 
> [5.1] Our method improves the bounds in $112$ out of the $120$ Taillard instances and $430$ out of the $480$ VRF instances. (Abstract)
 
`6.` Lu Y, Yuan Y, Yasenjiang J, Sitahong A, Chao Y, Wang Y. An Optimized Method for Solving the Green Permutation Flow Shop Scheduling Problem Using a Combination of Deep Reinforcement Learning and Improved Genetic Algorithm. *Mathematics.* 2025;13:545-545. doi:10.3390/math13040545
 
> [6.1] Optimal solutions are achieved in 28 test instances, and the latest solutions are updated in instances Ta005 and Ta068 with values of 1235 and 5101, respectively. (Abstract)
 
`7.` Chen S, Zheng J. Hybrid grey wolf optimizer for solving permutation flow shop scheduling problem. *Concurrency and Computation Practice and Experience.* 2023;36:e7942. doi:10.1002/cpe.7942
 
> [7.1] Grey wolf optimizer (GWO) is a metaheuristic proposed by Mirjalili et al., 14 inspired by the hunting activities of grey wolves. (Introduction)
 
> [7.2] And it has three leaders who lead the group toward the optimal value. (Introduction)
 
> [7.3] Compared with other metaheuristics, GWO has more competitive performance, fast convergence, and a simple search mechanism. (Introduction)
 
> [7.4] The smallest-position-value (SPV) rule is proposed for the problem of discrete scheduling. (Conclusion)
 
> [7.5] First, one cooperative initialization strategy is proposed to improve the quality of the initial solution based on the improved Nawaz‐Enscore‐Ham (NEH) method and the tent chaotic map method. (Abstract)
 
> [7.6] To address this problem, a hybrid grey wolf optimizer (HGWO) is proposed in this paper. (Abstract)
 
> [7.7] Finally, nonparametric statistical analysis is performedusingtheFriedmantest.BasedonCarlier,Reeves,andT aillard'sinstances,HGWOisevaluatedandcomparedwithothermethods.Among them, in the Carlier instances, HGWO obtained the best BRPD and ARPD among all the instances. (Conclusion)
 
> [7.8] However, there are still some shortcomings of metaheuristics, such as the slow convergence of features based on different algorithms, so most of the improvements are devoted to solving the problem of slow convergence of metaheuristics. (Introduction)
 
`8.` Al-Imron CN, Utama DM, Dewi SK. An Energy-Efficient No Idle Permutations Flow Shop Scheduling Problem Using Grey Wolf Optimizer Algorithm. *Jurnal Ilmiah Teknik Industri.* 2022;21:1-10. doi:10.23917/jiti.v21i1.17634
 
> [8.1] The second stage involves converting GWO positions to permutation sequences using the Large Rank Value (LRV) principle. (Methods)
 
> [8.2] The LRV method is a simple procedure that effectively converts a herd's position to a permutation job sequence (Utama, 2019) (Widodo & Utama, 2021). (Methods)
 
> [8.3] LRV is an efficient method for mapping continuous values into permutation jobs (Utama, 2021). (Methods)
 
`9.` Chen S, Zheng J. Discrete Gray Wolf Optimizer for Solving Distributed Permutation Flowshop Scheduling Problem. *Concurrency and Computation Practice and Experience.* 2025;37:e70090. doi:10.1002/cpe.70090
 
> [9.1] Second, a discrete population update mechanism is proposed for the characteristics of the solved problem to balance exploration and exploitation. (Abstract)
 
> [9.2] A discrete gray wolf optimizer (DGWO) is proposed to solve the distributed permutation flowshop scheduling problem (DPFSP) to minimize makespan. (Abstract)
 
> [9.3] Finally, the Wilcoxon signed rank and the Friedman test are used for statistical comparison analysis. (Abstract)
 
> [9.4] Second, compared with other metaheuristics, the GWO has a simple structure, fewer parameters, and fast convergence. (Introduction)
 
> [9.5] 1. A discrete gray wolf optimizer (DGWO) is proposed, which integrates the initialization strategy of ENEH2 and random generation, the discrete population update mechanism, and four local searches for variable neighborhood descent search to enhance search capabilities. (Introduction)
 
`10.` Chen S, Zheng J, Zhang W. A cooperative grey wolf optimizer for the joint flowshop scheduling problem with sequence-dependent set-up time. *Engineering Optimization.* 2024;57:739-761. doi:10.1080/0305215x.2024.2333966
 
> [10.1] In the process of searching for prey, a discretized search for prey update mechanism is proposed, which is conducive to balancing exploration and exploitation. (Abstract)
 
> [10.2] In this article, a cooperative grey wolf optimizer (CGWO) is developed to solve the JFSP. (Abstract)
 
`11.` Sun C, Sang H, Meng L, Zhang B, Meng T. Efficient Multi-Start Gray Wolf Optimization Algorithm for the Distributed Permutation Flowshop Scheduling Problem with Preventive Maintenance. *Complex System Modeling and Simulation.* 2025;5:107-124. doi:10.23919/csms.2025.0001
 
> [11.1] Furthermore, a restart mechanism is integrated into algorithm to avert the risk of converging prematurely to a suboptimal solution, thereby ensuring a broader exploration of potential solutions. (Abstract)
 
> [11.2] For solving the problem, a discrete gray wolf optimization algorithm with restart mechanism (DGWO_RM) is proposed. (Abstract)
 
> [11.3] The obtained results show that the proposed DGWO_RM significantly outperforms the four state-of-the-art algorithms in solving PM/DPFSP. (Abstract)
 
`12.` Pesaru V, Saddikuti V, Janardhanan MN. Hybrid Grey-Wolf Algorithm approach for Solving energy efficient permutation flowshop scheduling problem with Setup Times. *Procedia Computer Science.* 2024;241:352-359. doi:10.1016/j.procs.2024.08.047
 
> [12.1] The contribution of this paper includes: (1) a permutation flowshop scheduling problem (PFSP) mathematical model by considering energy consumed and setup time by each machine in the system; (2) a grey-wolf algorithm optimization with variable neighborhood search (VNS) method (GWO_VNS) is proposed for the multi-objective PFSP model; (3) solved 9 benchmarks problems of Taillard (1993) [8] for the minimization of flowtime (FT) and energy consumption (EC). (Abstract)
 
> [12.2] Overall, the proposed algorithm achieved 33.25% and 30.56% average improvement in FT and EC minimization respectively on benchmark problems. (Abstract)
 
`13.` Zheng J, Chen S. A Q-learning multi-objective grey wolf optimizer for the distributed hybrid flowshop scheduling problem. *Engineering Optimization.* 2024;57:2609-2628. doi:10.1080/0305215x.2024.2410844
 
> [13.1] A Q-learning multi-objective grey wolf optimizer (QMOGWO) is designed to optimize the makespan, total energy consumption and total tardiness. (Abstract)
 
> [13.2] To verify the performance of the proposed QMOGWO, different scales of instances are tested in various factories and at different stages, and the simulation results show that the QMOGWO outperforms the comparison methods. (Abstract)
 
`14.` Sun C, Sang H, Li Y, Gong J, Zh H. A metaheuristic algorithm co-driven by Q-learning and a learning mechanism for the distributed blocking flowshop scheduling problem with preventive maintenance and sequence-dependent setup times. *International Journal of Industrial Engineering Computations.* 2025;16:767-784. doi:10.5267/j.ijiec.2025.3.006
 
> [14.1] Second, we propose a Q-learning and learning mechanism co-driven approach, integrating it into the discrete grey wolf optimization algorithm (DGWO_Q). (Abstract)
 
`15.` Fernández-Viagas V, Ruíz R, Framiñán JM. A new vision of approximate methods for the permutation flowshop to minimise makespan: State-of-the-art and computational evaluation. *European Journal of Operational Research.* 2016;257:707-721. doi:10.1016/j.ejor.2016.09.055
 
> [15.1] However, most methods proposed for makesan minimisation are not properly compared with existing procedures so currently it is not possible to know which are the most efficient methods for the problem regarding the quality of the solutions obtained and the computational effort required. (Abstract)
 
> [15.2] The most promising ones, i.e. a total of 31 algorithms (19 constructive heuristics and 12 metaheuristics), have been implemented and compared under the same conditions. (Conclusion)
 
> [15.3] On one hand, the metaheuristics are compared under three different stopping criteria to analyse the evolution of the each algorithm with the computational effort. (Conclusion)
 
> [15.4] To ensure the repeatability and the reproducibility of the algorithms, we consider that at the least a clear pseudo code should be included in the papers, if not the publication of the full source codes on-line, as recommended by the Good Laboratory Practice for Optimization Research (GLP4OPT) practices, recently published by [33]. (Conclusion)
 
> [15.5] In this paper, we identify and exhaustively compare the best existing heuristics and metaheuristics so the state-of-the-art regarding approximate procedures for this relevant problem is established. (Abstract)
 
`16.` Pan Q, Ruíz R. Local search methods for the flowshop scheduling problem with flowtime minimization. *European Journal of Operational Research.* 2012;222:31-43. doi:10.1016/j.ejor.2012.04.034
 
> [16.1] The fact that simple methods perform better than complex existing approaches, and also that for our proposed heuristics using populations did not improve results, reinforces the idea that simple local search based methods are enough to solve the PFSP with total flowtime criterion. (Conclusion)
 
> [16.2] According to the extensive experimental and statistical analyses, the proposed IGA and ILS methods performed better than pIGA and pILS, and they outperform the existing methods for the problem considered. (Conclusion)
 
`17.` Utama DM. Hybrid Grey Wolf Algorithm for Energy-Efficient Scheduling with Sequence-Dependent Setup Times: A Case Study. *IOP Conference Series Materials Science and Engineering.* 2021;1096:012116-012116. doi:10.1088/1757-899x/1096/1/012116
 
> [17.1] The HGWO parameter experiment was also used to test the parameters in the case study solving. (Abstract)
