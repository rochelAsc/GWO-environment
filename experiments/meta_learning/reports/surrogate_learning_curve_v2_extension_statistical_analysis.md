# Análise estatística consolidada — curva de aprendizagem do surrogate v2

**Data:** 26/11/2026  
**Branch:** `recovery/surrogate-learning-curve-v2-oom`  
**Escopo:** extensão v2 recuperada, comparada à curva v2 original.  
**Dados:** `results/meta_learning_surrogate_learning_curve_v2_full/learning_curve_runs.csv` e `results/meta_learning_surrogate_learning_curve_v2_extension_recovered/recovered_runs.csv`.

## 1. Pergunta e desenho analisado

A análise verifica se aumentar o conjunto de treinamento de 4.000 para 8.000, 16.000 e 32.000 permutações melhora a capacidade do MLP da Semana 4 de estimar makespan e ordenar soluções.

- Instâncias: `ta071` (100 jobs × 10 máquinas) e `ta111` (500 jobs × 20 máquinas).
- Amostragem: LHS global sobre random keys e permutações uniformes.
- Repetições: cinco por combinação.
- Teste: conjunto fixo de 1.000 permutações por instância, mantido entre os tamanhos e métodos.
- Modelo: MLP da Semana 4, com codificação de permutação por posição normalizada.
- Métricas primárias: RMSE (menor é melhor) e Spearman (maior é melhor). R² e recuperação top-k são complementares.

Os tamanhos 300–4.000 vêm da curva v2 original; 8.000–32.000 vêm da extensão recuperada. A recuperação reutilizou as permutações salvas e regenerou deterministicamente os desenhos ausentes, sem alterar a pasta interrompida.

## 2. Método estatístico e limites dos intervalos

Para cada ponto, calculou-se a média das cinco repetições e o intervalo t bilateral de 95%:

\[
\bar{x} \pm t_{0,975;4}\frac{s}{\sqrt{5}}, \qquad t_{0,975;4}=2,7764.
\]

Os intervalos descrevem a variação entre repetições de treinamento **condicionada ao conjunto de teste fixo**. Não incorporam incerteza decorrente de escolher outro conjunto de teste, nem variação entre instâncias PFSP.

Os ICs individuais não são um teste formal da diferença entre LHS e uniforme ou entre tamanhos. A sobreposição de ICs é apenas uma indicação visual. Não foi executado um teste confirmatório de hipóteses; com cinco repetições, qualquer conclusão inferencial deve ser considerada exploratória.

## 3. Resultados: RMSE e Spearman com IC95%

### ta071 — 100 × 10

| Amostragem | N | RMSE média [IC95%] | Spearman média [IC95%] |
|---|---:|---:|---:|
| LHS | 8.000 | 137,639 [136,46; 138,82] | 0,423 [0,406; 0,439] |
| LHS | 16.000 | 135,953 [134,41; 137,49] | 0,444 [0,421; 0,467] |
| LHS | 32.000 | 132,929 [132,13; 133,73] | 0,483 [0,476; 0,490] |
| Uniforme | 8.000 | 136,788 [134,42; 139,16] | 0,438 [0,407; 0,468] |
| Uniforme | 16.000 | 134,665 [133,75; 135,58] | 0,456 [0,441; 0,470] |
| Uniforme | 32.000 | 132,323 [131,20; 133,45] | 0,482 [0,466; 0,499] |

### ta111 — 500 × 20

| Amostragem | N | RMSE média [IC95%] | Spearman média [IC95%] |
|---|---:|---:|---:|
| LHS | 8.000 | 332,826 [329,11; 336,55] | 0,229 [0,217; 0,240] |
| LHS | 16.000 | 324,156 [320,34; 327,97] | 0,287 [0,268; 0,306] |
| LHS | 32.000 | 312,280 [309,31; 315,25] | 0,350 [0,330; 0,369] |
| Uniforme | 8.000 | 333,838 [330,11; 337,57] | 0,230 [0,199; 0,261] |
| Uniforme | 16.000 | 320,834 [315,78; 325,89] | 0,298 [0,276; 0,320] |
| Uniforme | 32.000 | 311,809 [307,61; 316,01] | 0,353 [0,330; 0,376] |

### R² em N = 32.000

| Instância | Amostragem | R² médio [IC95%] |
|---|---|---:|
| ta071 | LHS | 0,234 [0,224; 0,243] |
| ta071 | Uniforme | 0,241 [0,228; 0,254] |
| ta111 | LHS | 0,119 [0,102; 0,135] |
| ta111 | Uniforme | 0,121 [0,098; 0,145] |

## 4. Análise diferencial: ganho ao dobrar aproximadamente N

A tabela mostra a diferença entre as médias dos pontos consecutivos. Valores negativos de RMSE são melhora; valores positivos de Spearman são melhora. Os intervalos não são exatamente duplicações (por exemplo, 8k→16k e 16k→32k são duplicações).

| Instância | Método | RMSE 4k→8k | RMSE 8k→16k | RMSE 16k→32k | Spearman 4k→8k | Spearman 8k→16k | Spearman 16k→32k |
|---|---|---:|---:|---:|---:|---:|---:|
| ta071 | LHS | -2,19 | -1,69 | -3,02 | +0,0186 | +0,0216 | +0,0389 |
| ta071 | Uniforme | -3,04 | -2,12 | -2,34 | +0,0395 | +0,0181 | +0,0267 |
| ta111 | LHS | -7,99 | -8,67 | -11,88 | +0,0778 | +0,0584 | +0,0625 |
| ta111 | Uniforme | -9,19 | -13,00 | -9,02 | +0,0923 | +0,0685 | +0,0547 |

### Ganho acumulado de 4.000 para 32.000

| Instância | Método | Redução relativa do RMSE | Aumento de Spearman | Aumento de R² |
|---|---|---:|---:|---:|
| ta071 | LHS | 4,94% | +0,0791 | +0,0817 |
| ta071 | Uniforme | 5,36% | +0,0843 | +0,0886 |
| ta111 | LHS | 8,38% | +0,1987 | +0,1684 |
| ta111 | Uniforme | 9,10% | +0,2154 | +0,1848 |

A melhoria é mais expressiva em `ta111`, que também é a instância mais difícil para o modelo. Não há evidência de saturação até 32 mil: RMSE continua caindo e Spearman continua subindo nos dois últimos intervalos. Isso não demonstra que a tendência continuará indefinidamente.

## 5. LHS versus uniforme

Em 32 mil amostras:

| Instância | Método | RMSE | Spearman | R² |
|---|---|---:|---:|---:|
| ta071 | LHS | 132,929 | 0,4831 | 0,2336 |
| ta071 | Uniforme | 132,323 | 0,4825 | 0,2406 |
| ta111 | LHS | 312,280 | 0,3496 | 0,1187 |
| ta111 | Uniforme | 311,809 | 0,3530 | 0,1214 |

As diferenças são pequenas e os ICs apresentados se sobrepõem. Não há base suficiente para declarar superioridade geral de LHS ou uniforme. O LHS é metodologicamente mais estruturado no espaço contínuo das random keys, mas essa propriedade não garante cobertura superior do espaço discreto de permutações após a decodificação por `argsort`.

Na `ta111`, a recuperação top-10 em 32 mil foi 0,08 para LHS e 0,10 para uniforme; top-50 foi 0,176 e 0,204, respectivamente. Esses valores reforçam que correlação global moderada não equivale a identificar com alta precisão as melhores permutações.

## 6. Diagnóstico e interpretação

1. **Mais dados ajudam:** há melhora consistente das médias de RMSE e Spearman conforme N cresce.
2. **O ganho não resolveu a tarefa:** em 32 mil, Spearman fica próximo de 0,48 em `ta071`, mas apenas 0,35 em `ta111`; R² em `ta111` permanece próximo de 0,12.
3. **A ordenação das melhores soluções continua fraca:** top-10 recall em `ta111` permanece baixo.
4. **Amostragem não é o único suspeito:** LHS e uniforme têm resultados próximos. A arquitetura MLP e a representação por vetor de posições podem estar limitando o desempenho.
5. **Não escalar N ainda:** aumentar para 64k/128k multiplicaria custo sem antes testar se modelos diferentes extraem mais informação dos mesmos dados.

## 7. Limitações estatísticas

- Cinco repetições por ponto produzem ICs t com apenas quatro graus de liberdade; a estimativa é sensível a valores extremos.
- O conjunto de teste é fixo e uniforme. Os ICs não representam a variabilidade sobre novos conjuntos de teste.
- Apenas duas instâncias foram analisadas; não generalizar os resultados para todo PFSP.
- As repetições entre métodos/tamanhos não devem ser tratadas automaticamente como pares independentes ou pareados sem demonstrar o pareamento do desenho.
- As métricas top-k são proporções discretas e devem receber intervalos binomiais ou bootstrap apropriado, não IC t irrestrito.
- Comparações múltiplas entre tamanhos, métodos, instâncias e métricas não foram corrigidas; os resultados são exploratórios.
- A recuperação não recompõe tempos originais de geração/rotulagem; os tempos de treinamento recuperados pertencem à execução de recuperação.

## 8. Decisão e próximo experimento

**Decisão:** congelar a curva de dados em 32 mil como evidência suficiente para orientar o próximo diagnóstico. Não iniciar, por enquanto, uma curva de 64 mil/128 mil.

O próximo experimento deve comparar modelos usando exatamente as mesmas matrizes de treino, rótulos, conjuntos de teste e repetições já definidos, isolando o efeito da arquitetura:

- MLP 64×64 atual (baseline de comparação);
- Random Forest Regressor;
- Extra Trees Regressor;
- HistGradientBoosting Regressor, se o custo e a dimensão forem viáveis.

Começar com um piloto em `ta071` e `ta111`, N=8.000 e N=32.000, cinco repetições, reutilizando os mesmos dados e o mesmo teste fixo. Fixar as seeds e os hiperparâmetros antes da execução. Medir RMSE, MAE, R², Spearman, Kendall tau-b, top-10/top-50 recall, regret dos candidatos selecionados, tempo de treinamento, inferência em lote e memória de pico. Não ajustar hiperparâmetros usando o conjunto de teste.

O protocolo operacional dessa comparação será registrado em `surrogate_model_comparison_protocol.md`. A comparação não altera o GWO nem a Semana 6: é uma investigação isolada da extensão opcional do surrogate/meta-learning.
