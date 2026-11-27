# Plano de investigação e protocolo experimental — GWO para PFSP clássico

**Data:** 2026-11-27  
**Status:** decisões metodológicas consolidadas; execução do novo programa experimental ainda não iniciada  
**Repositório:** `rochelAsc/GWO-environment`  
**Ponto de partida:** commit `dd4ef1aa7a702588e7e01b23f93025126eea5d25` — revisão de literatura GWO/PFSP  
**Escopo primário:** Permutation Flow Shop Scheduling Problem (PFSP) clássico, uma fábrica, minimização do makespan (`Cmax`).

> Este documento consolida as decisões tomadas após o commit de revisão de literatura. Ele é um plano prospectivo, não um relatório de experimentos já executados. Valores de orçamento absoluto, IDs de instâncias e configurações finais que dependam de inventário/piloto deverão ser preenchidos e congelados antes da bateria correspondente.

## 1. Decisões de escopo e objetivo científico

1. O problema principal permanece o **PFSP clássico de uma única fábrica**, com a mesma permutação de jobs em todas as máquinas e objetivo de minimizar o makespan.
2. O estudo permanece centrado no **Grey Wolf Optimizer (GWO)**. Não substituir o objeto de pesquisa por outro problema ou por uma comparação genérica de metaheurísticas.
3. A linha atual contínua via **Random Keys + decodificação por ordenação** será mantida como ponto de partida e referência experimental. Suas limitações serão estudadas, não presumidas.
4. O foco imediato é compreender e melhorar o GWO para PFSP. A possibilidade de desenvolver mecanismos adaptativos/generalizáveis para outras classes de problemas combinatórios é uma direção futura, não o escopo da próxima bateria.
5. O **Meta-Learning está pausado, não cancelado**. Não deve avançar para treino/avaliação enquanto não houver uma base experimental mais ampla, consistente e validada das estratégias GWO.
6. Problemas diferentes — PFS com tardiness, Distributed PFSP (DPFSP), setups dependentes de sequência, manutenção, energia e flowshop híbrido — permanecem separados. Podem ser referências de mecanismos, mas seus resultados não serão apresentados como resultados diretamente comparáveis ao PFSP clássico/makespan.

### 1.1 Formulação do problema

Dada uma sequência de jobs \(\pi\), tempos de processamento \(p_{i,j}\), jobs \(i=1,\ldots,n\) e máquinas \(j=1,\ldots,m\), minimizar:

\[
\min_{\pi} C_{\max}(\pi)=C_{\pi_n,m}
\]

com recorrência usual de conclusão:

\[
C_{\pi_k,j}=\max(C_{\pi_{k-1},j},C_{\pi_k,j-1})+p_{\pi_k,j}.
\]

O avaliador exato de makespan é a fonte de verdade. Nenhuma predição de surrogate será tratada como fitness real.

## 2. Estado da investigação e motivação

A revisão de literatura versionada em [gwo_pfsp_literature_review_2026-11-27.md](gwo_pfsp_literature_review_2026-11-27.md) identifica:

- Taillard (1993) como benchmark clássico amplamente usado para PFSP;
- o benchmark hard de Vallada, Ruiz e Framiñán como complemento com maior poder discriminante;
- NEH como baseline construtivo importante e Iterated Greedy (IG) como referência metaheurística forte;
- variantes GWO contínuas, discretas, híbridas e adaptativas, cujos mecanismos devem ser classificados conforme o problema exato resolvido;
- HGWO de Chen e Zheng (2023) como precedente diretamente relevante ao PFSP clássico; variantes para DPFSP ou problemas com setups/manutenção/energia não são equivalentes;
- a importância de comparações com orçamento explícito, sementes independentes, análise estatística, ablação e sensibilidade.

A revisão também alerta que comparações publicadas frequentemente usam protocolos, instâncias, baselines e critérios de parada diferentes. Portanto, resultados reportados por artigos não devem ser comparados numericamente sem verificar as condições experimentais.

## 3. Benchmark Taillard: seleção estratificada

### 3.1 Universo

O benchmark clássico de Taillard contém 120 instâncias organizadas em 12 classes de dimensão, com 10 instâncias por classe:

| Classe | Dimensão jobs × máquinas | IDs |
|---:|---:|---|
| 1 | 20 × 5 | Ta001–Ta010 |
| 2 | 20 × 10 | Ta011–Ta020 |
| 3 | 20 × 20 | Ta021–Ta030 |
| 4 | 50 × 5 | Ta031–Ta040 |
| 5 | 50 × 10 | Ta041–Ta050 |
| 6 | 50 × 20 | Ta051–Ta060 |
| 7 | 100 × 5 | Ta061–Ta070 |
| 8 | 100 × 10 | Ta071–Ta080 |
| 9 | 100 × 20 | Ta081–Ta090 |
| 10 | 200 × 10 | Ta091–Ta100 |
| 11 | 200 × 20 | Ta101–Ta110 |
| 12 | 500 × 20 | Ta111–Ta120 |

Nem todas as combinações jobs × máquinas existem no conjunto original. A seleção deve usar as 12 classes efetivamente disponíveis, sem inventar classes ausentes.

### 3.2 Divisão aprovada: 72 desenvolvimento + 48 holdout

A divisão planejada é:

- **72 instâncias de desenvolvimento:** 6 selecionadas de cada uma das 12 classes;
- **48 instâncias de avaliação final (holdout):** 4 selecionadas de cada classe.

A divisão cobre todas as escalas representadas no benchmark e mantém a mesma quantidade por classe nos dois subconjuntos. Ela é uma decisão de desenho experimental deste projeto, não uma divisão prescrita por Taillard ou pela literatura.

### 3.3 Procedimento de seleção

1. Construir e validar um inventário canônico das 120 instâncias disponíveis.
2. Verificar dimensão, parser, integridade e hash SHA-256 de cada arquivo.
3. Dentro de cada classe, selecionar aleatoriamente 6 IDs para desenvolvimento e reservar os 4 restantes para holdout, usando uma seed fixa e registrada.
4. Persistir o inventário, seed, algoritmo de amostragem, IDs selecionados e hashes em artefato versionado.
5. Não escolher instâncias com base em resultados de GWO, desempenho observado, facilidade de execução ou conveniência.
6. Uma vez gerada e auditada a divisão, não trocar instâncias entre os subconjuntos em resposta aos resultados.

A lista final de IDs **ainda precisa ser gerada a partir do inventário real do repositório**. Não registrar IDs presumidos antes dessa validação.

### 3.4 Uso dos subconjuntos

**Desenvolvimento (72):**
- diagnóstico de comportamento;
- comparação e seleção de variantes;
- sensibilidade de parâmetros;
- ablações;
- calibração do orçamento;
- construção de hipóteses e refinamento do método.

**Holdout (48):**
- avaliação confirmatória após congelar algoritmos, parâmetros, orçamento, métricas e análise;
- nenhuma seleção de variante, ajuste de hiperparâmetros ou mudança de regra com base no holdout;
- qualquer alteração motivada pelos resultados do holdout exigirá novo conjunto independente ou será declarada explicitamente como análise exploratória, não como avaliação final confirmatória.

### 3.5 Descritores estruturais

Registrar, no mínimo:

- número de jobs \(n\) e máquinas \(m\);
- razão \(n/m\);
- produto \(n\times m\) como medida simples de dimensão, sem tratá-lo como variável independente de \(n\) e \(m\);
- estatísticas da matriz de processamento: média, desvio padrão, coeficiente de variação, mínimo, máximo e quantis;
- cargas agregadas por job e por máquina;
- dispersão das cargas e correlações entre máquinas adjacentes, se úteis e implementadas de forma consistente;
- BKS/UB e LB disponíveis, com fonte, data e distinção explícita entre melhor conhecido e ótimo certificado.

Os descritores servem para caracterização e análise de heterogeneidade. A seleção primária permanece estratificada por classe Taillard, não por resultados dos algoritmos. Dificuldade empírica e gap para BKS podem ser analisados depois da seleção, mas não usados para cherry-picking.

## 4. Programa de investigação de variantes GWO

A investigação deve ser sistemática e não concentrada apenas no Surrogate. As quatro estratégias já estudadas permanecem relevantes:

1. **GWO Baseline:** referência contínua via Random Keys.
2. **Optuna-GWO:** GWO com parâmetros ajustados por TPE/Optuna.
3. **Fuzzy-GWO:** controlador Mamdani aplicado ao parâmetro de exploração, com entradas como diversidade e estagnação conforme a implementação vigente.
4. **Surrogate-assisted GWO:** modelo substituto para orientar a seleção de candidatos, mantendo avaliação exata como fonte de verdade.

Além dessas, investigar variantes da literatura e mecanismos candidatos, sem implementar tudo indiscriminadamente:

- GWO discreto e operadores específicos de permutação;
- hibridização com NEH, VND, busca local e/ou mecanismos de intensificação;
- inicialização construtiva e estratégias de diversidade;
- mecanismos adaptativos/dinâmicos para exploração e explotação;
- reinício e tratamento de estagnação;
- mecanismos de preservação de diversidade;
- uso de Random Keys e alternativas de representação/decodificação.

Para cada variante/mecanismo, documentar:

| Campo | Pergunta |
|---|---|
| Problema-alvo | PFSP clássico/makespan ou outra variante? |
| Deficiência-alvo | Convergência prematura, representação, diversidade, exploração/explotação, intensificação etc.? |
| Mecanismo | O que muda precisamente no GWO? |
| Custo adicional | Quantas avaliações exatas, previsões e tempo acrescenta? |
| Evidência | Quais instâncias, baselines, seeds e testes foram usados? |
| Transferibilidade | O mecanismo é aplicável ao nosso PFSP sem alterar o problema? |
| Ablação | Como isolar sua contribuição? |

Não assumir que um método para DPFSP, flowshop com setups ou problema multiobjetivo é uma solução comprovada para PFSP clássico.

## 5. Baselines e comparabilidade

Incluir, quando a implementação e o orçamento permitirem:

- **NEH:** baseline construtivo;
- **Iterated Greedy (IG):** baseline metaheurístico de referência para PFSP/makespan;
- GWO Baseline e variantes desenvolvidas neste projeto.

Todos os métodos comparados devem usar as mesmas instâncias, conjuntos de seeds pareadas quando aplicável e limite de avaliações exatas comparável. Se um método tiver custos adicionais (treinamento, inferência, busca local, inicialização), reportá-los separadamente e no custo total.

Comparações históricas da Semana 6, limitadas a Ta001 e Ta011, continuam válidas como evidência histórica sob seu próprio protocolo, mas não substituem a nova avaliação ampla. Não misturar resultados de protocolos diferentes como se fossem uma única bateria.

## 6. Orçamento experimental crescente

### 6.1 Princípio aprovado

A unidade primária de orçamento será o **número de chamadas/avaliações exatas da função objetivo de makespan**, e não o número nominal de épocas/iterações.

As iterações serão registradas como informação secundária. O orçamento efetivo será contado no ponto em que o avaliador exato é chamado, incluindo a avaliação da população inicial e qualquer avaliação extra de busca local, inicialização, validação ou reavaliação.

Não contabilizar previsões do Surrogate como avaliações exatas. Registrar separadamente:
- avaliações exatas de treinamento/rotulagem;
- avaliações exatas durante a busca;
- avaliações exatas de validação/reavaliação;
- consultas/previsões do surrogate;
- tempo de treinamento, inferência e busca.

### 6.2 Progressão Fibonacci limitada

Adotar uma escada de orçamentos derivados da sequência de Fibonacci, para aumentar o esforço de forma discreta e controlada. A proposta inicial de multiplicadores é:

\[
q_k\in\{1,2,3,5,8\}
\]

com possibilidade de acrescentar \(13\) somente se o piloto demonstrar viabilidade computacional e utilidade científica. Para um orçamento-base calibrado \(B_0\), os checkpoints candidatos são:

\[
B_k=q_k B_0.
\]

O valor absoluto de \(B_0\) ainda não está congelado: será escolhido após medir custo por classe e por algoritmo no piloto. A escada não é uma obrigação de executar todos os níveis. Ela serve para observar a curva qualidade × avaliações exatas e identificar retornos decrescentes.

**Regra de implementação:** os checkpoints devem ser atingidos com contadores reais. Quando um algoritmo trabalha em lotes (por exemplo, uma população inteira por geração), documentar o arredondamento/ajuste para não ultrapassar silenciosamente o limite. O contador efetivo prevalece sobre o número de iterações. Se não for possível atingir exatamente o checkpoint sem interromper uma geração, usar o maior orçamento realizável abaixo do limite e registrar o valor efetivo.

### 6.3 Comparação justa entre algoritmos

- Usar o mesmo teto de avaliações exatas para comparações principais.
- O Surrogate pode fazer mais consultas baratas ao modelo, mas essas consultas não substituem nem são somadas às avaliações exatas; reportar também tempo total e consultas.
- O custo de construir/treinar o Surrogate deve ser mostrado integralmente e também amortizado para diferentes quantidades de execuções, sem ocultá-lo.
- NEH/IG e variantes híbridas devem contabilizar todas as avaliações do makespan, inclusive as usadas por busca local e construção quando houver chamadas ao avaliador.
- Apresentar curvas de melhor makespan conhecido versus avaliações exatas, além de versus tempo de parede.

## 7. Sementes e precisão estatística

### 7.1 Regra geral

As sementes são execuções independentes usadas para estimar variabilidade; não são instâncias independentes. O índice de seed será pareado entre variantes dentro da mesma instância, mas não se pressupõe que algoritmos diferentes consumam fluxos aleatórios idênticos.

Usar listas de seeds aninhadas e determinísticas: ao aumentar a quantidade, preservar as sementes já executadas e adicionar novas seeds. Registrar a lista exata, gerador pseudoaleatório e política de derivação de seeds por componente.

### 7.2 Quantidades por etapa

| Etapa | Progressão/quantidade | Interpretação |
|---|---:|---|
| Piloto | 10 → 20 → 30 por instância/configuração | Estimar custo e variabilidade; adicionar 10 por expansão |
| Desenvolvimento | 20 → 30 → 40 por instância/configuração | Comparação, sensibilidade e ablações; progressão cumulativa |
| Avaliação final | Começar com 40 por instância/configuração | Aumentar apenas se a precisão estatística for insuficiente |

As quantidades são metas iniciais aprovadas para planejamento. O piloto pode justificar ajustes documentados antes do desenvolvimento; a avaliação final começa com 40 e pode crescer conforme a regra abaixo.

### 7.3 Regra adaptativa de aumento na avaliação final

1. Executar inicialmente 40 seeds por combinação instância × algoritmo.
2. Calcular intervalos de confiança para as métricas primárias e diferenças pareadas entre algoritmos.
3. Avaliar a largura dos intervalos e a incerteza da estimativa, não apenas se um p-value ficou abaixo de um limiar.
4. Se a precisão pré-definida não for atingida, adicionar um bloco de seeds (inicialmente +10) e recalcular.
5. Repetir até atingir o critério de precisão ou o teto computacional previamente registrado.
6. Definir antes da avaliação final a métrica primária, método de intervalo, largura/precisão desejada, tamanho do bloco e máximo de seeds. Não parar porque o resultado ficou estatisticamente significativo ou porque favoreceu uma variante.

A regra de precisão deverá ser definida após o piloto, considerando a escala do makespan/RPD, variabilidade observada e custo. Não inventar um limiar universal. A avaliação final não poderá usar seus resultados para reajustar algoritmos.

### 7.4 Reprodutibilidade e pareamento

- Mesma lista de índices de seeds entre algoritmos para cada instância.
- Seeds novas são acrescentadas, não substituem resultados anteriores.
- Usar RNGs explícitos e independentes por execução/componente.
- Randomizar/alternar a ordem de execução das configurações para reduzir efeitos de aquecimento e carga da máquina.
- Preservar resultados individuais por seed; não guardar somente médias.

## 8. Validação específica por estratégia

A validação deve cobrir todas as estratégias, não apenas o Surrogate.

### 8.1 GWO Baseline

- múltiplas seeds independentes;
- curva de convergência por avaliações exatas;
- diversidade medida também após decodificação em permutações;
- frequência de permutações duplicadas/colisões de Random Keys;
- sensibilidade a população, agenda do parâmetro \(a\) e orçamento;
- análise de estagnação e estabilidade entre instâncias/classes.

### 8.2 Optuna-GWO

- separar seeds/instâncias de sintonia e avaliação;
- não avaliar como desempenho independente os mesmos dados usados para escolher hiperparâmetros;
- congelar configuração antes do holdout;
- registrar trials, espaço de busca, objetivo, custo de tuning e orçamento de cada trial;
- preferir avaliação externa por instâncias não usadas na sintonia quando possível.

### 8.3 Fuzzy-GWO

Realizar ablação que isole a contribuição de cada entrada/mecanismo. Como mínimo, avaliar:
- controlador completo;
- sem entrada de diversidade;
- sem entrada de estagnação;
- sem ambas (controle correspondente definido previamente);
- baseline/schedule fixo com população e orçamento equivalentes.

Registrar funções de pertinência, regras, método de defuzzificação, entradas ao longo do tempo, saídas e parâmetros. Não alterar regras após observar holdout.

### 8.4 Surrogate-assisted GWO

- separar treino/teste por permutação decodificada, não por vetor Random Keys bruto;
- chaves distintas que decodificam para a mesma permutação devem permanecer no mesmo grupo;
- usar teste independente e, quando possível, validação agrupada por seed/trajetória;
- reportar MAE, RMSE, R², erro de ranking, Spearman, recall do top-k e métricas de seleção;
- registrar número de permutações únicas, duplicatas e cobertura do espaço observado;
- nunca usar fitness previsto como fitness final, líder exato ou convergência real;
- reavaliar a solução final pelo avaliador exato;
- manter congelado o surrogate durante cada execução, salvo se uma futura variante online for explicitamente definida e avaliada como método diferente;
- contabilizar dados de treino, retreinos e validação no custo total.

### 8.5 Meta-Learning (fase posterior)

Retomar somente após a meta-base ser construída com o protocolo amplo e auditado. A unidade de generalização é a instância. Usar validação agrupada por instância (por exemplo, GroupKFold/leave-one-group-out quando apropriado), nunca split aleatório de linhas/execuções da mesma instância. O meta-learning seleciona uma estratégia GWO; não substitui o avaliador de makespan nem muda o escopo PFSP.

## 9. Métricas e análise estatística

### 9.1 Métricas de qualidade e custo

Por instância, algoritmo, orçamento e seed:
- makespan final exato;
- melhor makespan (best-so-far) ao longo das avaliações;
- RPD em relação ao BKS/UB de referência, com versão/fonte/data;
- tempo de parede;
- número de avaliações exatas;
- previsões/consultas surrogate;
- custo de preparação, treinamento e inferência;
- número de permutações únicas/duplicadas;
- status de execução e falhas.

Resumos por instância/configuração:
- média, mediana, desvio padrão, mínimo e máximo;
- intervalos de confiança;
- curvas de convergência por avaliações exatas e por tempo;
- taxa de alcance do BKS/UB (sem chamar UB de ótimo certificado);
- diferenças pareadas entre variantes.

### 9.2 Testes

- Friedman para comparação global de vários algoritmos em blocos apropriados.
- Wilcoxon pareado para comparações de pares quando os pressupostos/desenho forem adequados.
- Correção de Holm para comparações múltiplas.
- Reportar p-values brutos e ajustados, diferenças pareadas, tamanho de efeito, vitórias/empates/derrotas e intervalos de confiança.
- Considerar bootstrap hierárquico (instâncias e seeds) para intervalos agregados.
- Não tratar seeds como se fossem novas instâncias independentes.
- Apresentar resultados por classe/tamanho e não ocultar heterogeneidade.
- Distinguir inferência dentro de uma instância de generalização para a população de instâncias.

A unidade de análise agregada e o procedimento de agregação entre instâncias devem ser definidos antes da análise. Não combinar indiscriminadamente todos os runs em um único teste.

## 10. Plano de execução em fases

### Fase 0 — Preparação e auditoria
- conferir estado atual do código e testes;
- validar inventário Taillard e proveniência dos arquivos;
- confirmar que todos os métodos resolvem o mesmo PFSP/makespan;
- revisar contadores de avaliação exata e instrumentação;
- identificar scripts e resultados históricos que pertencem a protocolos antigos;
- gerar e auditar split 72/48 com seed fixa.

### Fase 1 — Piloto
- usar subconjunto pequeno, mas cobrindo classes/tamanhos representativos;
- testar 10, 20 e, se necessário, 30 seeds cumulativas;
- executar checkpoints de orçamento Fibonacci derivados de \(B_0\);
- medir runtime e custo por classe/método;
- estimar variabilidade, largura de intervalos e estabilidade;
- validar integridade de logs, retomada e reprodutibilidade;
- congelar \(B_0\), ladder, regra de precisão e teto de seeds antes da etapa de desenvolvimento.

### Fase 2 — Desenvolvimento (72 instâncias)
- começar com 20 seeds e avançar para 30 e 40 conforme plano;
- executar comparações Baseline, Optuna, Fuzzy, Surrogate e variantes adicionais selecionadas;
- realizar ablações, sensibilidade e análise de representação/diversidade;
- incluir NEH e IG quando implementados e auditados;
- escolher mecanismos e configurações com base apenas no desenvolvimento;
- congelar algoritmo(s), parâmetros, orçamento e análise confirmatória.

### Fase 3 — Avaliação final (48 instâncias)
- começar com 40 seeds por combinação;
- ampliar em blocos somente segundo critério de precisão pré-registrado;
- usar o orçamento congelado e a lista de algoritmos congelada;
- não ajustar hiperparâmetros, regras, features ou mecanismo após observar holdout;
- produzir relatório final com resultados individuais, agregados, incerteza e limitações.

### Fase 4 — Meta-Learning (retomada futura)
- só após consolidar e auditar a meta-base;
- validação agrupada por instância;
- comparar classificação e regressão sobre a mesma base;
- relatar regret de seleção e incerteza, não apenas acurácia.

### Fase 5 — Generalização além do PFSP (futura)
- avaliar benchmark complementar, como o conjunto hard de Vallada–Ruiz–Framiñán (VRF), após a fase Taillard;
- somente então considerar outros problemas combinatórios, definindo novo escopo e protocolo.

## 11. Critérios de qualidade para avançar

Uma fase não é considerada concluída apenas porque os notebooks terminaram. Exigir:

1. inventário e hashes válidos;
2. código/testes passando;
3. contadores reais conferidos por testes e logs;
4. ausência de resultados duplicados ou combinações ausentes;
5. seeds e configurações rastreáveis;
6. resultados brutos imutáveis;
7. métricas derivadas por scripts reproduzíveis;
8. custo computacional reportado;
9. análises estatísticas coerentes com a unidade experimental;
10. documentação de desvios, falhas e decisões pós-piloto.

## 12. Riscos e salvaguardas

| Risco | Salvaguarda |
|---|---|
| Cherry-picking de instâncias | Amostragem aleatória estratificada e seed fixa |
| Vazamento do holdout | Congelar métodos antes das 48 instâncias finais |
| Orçamentos desiguais | Contar avaliações exatas e reportar previsões/tempo separadamente |
| Crescimento excessivo do custo | Ladder Fibonacci limitada, piloto e teto pré-registrado |
| Falsa precisão com muitas seeds | Seeds não substituem instâncias independentes |
| Surrogate otimista | Teste por permutação e reavaliação exata |
| Fuzzy sem evidência causal | Ablações das entradas e controle equivalente |
| Optuna superajustado | Separar tuning de avaliação externa |
| Random Keys com diversidade aparente | Medir diversidade após decodificação |
| Mistura de problemas | Separar PFSP/makespan de DPFSP, tardiness e outras variantes |
| Meta-learning prematuro | Pausar até base ampla e validação agrupada por instância |

## 13. Referências principais

1. Taillard, É. (1993). *Benchmarks for basic scheduling problems*. European Journal of Operational Research, 64(2), 278–285. DOI: [10.1016/0377-2217(93)90182-M](https://doi.org/10.1016/0377-2217(93)90182-M).
2. Vallada, E., Ruiz, R., & Framiñán, J. M. (2015). *New hard benchmark for flowshop scheduling problems minimising makespan*. European Journal of Operational Research, 240(3), 666–677. DOI: [10.1016/j.ejor.2014.07.033](https://doi.org/10.1016/j.ejor.2014.07.033).
3. Fernández-Viagas, V., Ruiz, R., & Framiñán, J. M. (2016). *A new vision of approximate methods for the permutation flowshop to minimise makespan: State-of-the-art and computational evaluation*. European Journal of Operational Research, 257, 707–721. DOI: [10.1016/j.ejor.2016.09.055](https://doi.org/10.1016/j.ejor.2016.09.055).
4. Chen, S., & Zheng, J. (2023). *Hybrid grey wolf optimizer for solving permutation flow shop scheduling problem*. Concurrency and Computation: Practice and Experience. DOI: [10.1002/cpe.7942](https://doi.org/10.1002/cpe.7942).
5. Chen, S., & Zheng, J. (2025). *Discrete Gray Wolf Optimizer for Solving Distributed Permutation Flowshop Scheduling Problem*. Concurrency and Computation: Practice and Experience. DOI: [10.1002/cpe.70090](https://doi.org/10.1002/cpe.70090). **DPFSP, não PFSP clássico**; referência de mecanismo, não baseline diretamente comparável.
6. Liu et al. (2024). *Surrogate-assisted evolutionary algorithms for expensive combinatorial optimization: a survey*. DOI: [10.1007/s40747-024-01465-5](https://doi.org/10.1007/s40747-024-01465-5).

A revisão completa, com referências adicionais, classificação de variantes e ressalvas de evidência, está em [gwo_pfsp_literature_review_2026-11-27.md](gwo_pfsp_literature_review_2026-11-27.md).

## 14. Artefatos a produzir antes de executar a bateria

- inventário canônico das 120 instâncias com hashes e dimensões;
- arquivo de split 72/48 reproduzível e IDs definitivos;
- especificação do orçamento-base \(B_0\), multiplicadores escolhidos e limite máximo;
- regra pré-registrada de precisão dos intervalos e teto de seeds;
- matriz de variantes/mecanismos selecionados para implementação;
- matriz de ablações e parâmetros de sensibilidade;
- scripts de execução e agregação com contadores testados;
- plano de análise estatística congelado;
- manifesto de ambiente, versões e hardware.

**Próxima ação recomendada:** auditar o inventário real de Taillard e a instrumentação de avaliações exatas; então gerar o split 72/48 e executar a Fase 1. Não iniciar a bateria completa antes de aprovar os resultados do piloto.
