# Protocolo — Curva de aprendizagem do surrogate PFSP

**Status:** protocolo definido; implementação/execução pendente. Nenhum resultado da curva foi produzido por este documento.

## 1. Pergunta

Como o tamanho e o mecanismo de amostragem do conjunto de treinamento afetam (a) a qualidade de regressão e (b) a qualidade de seleção do surrogate de makespan em ta071 (100×10) e ta111 (500×20)?

O experimento é específico por instância: um modelo independente será treinado para cada matriz de processamento. Não reutilizar modelos da Semana 4 ou entre instâncias com dimensões diferentes.

## 2. Fundamentação para a função de crescimento

Muñoz e Kirley (2021) estudam efeitos de tamanho amostral em seleção de algoritmos black-box e distribuem cinco tamanhos igualmente no eixo logarítmico, entre 100D e 1.000D. A progressão resultante é geométrica (fatores 100, 178, 316, 562 e 1.000) e os autores usam LHS. Isso fundamenta o uso de pontos igualmente espaçados em escala logarítmica para uma curva de aprendizagem: cobre uma faixa ampla de tamanhos com resolução relativa semelhante, sem concentrar todos os pontos na extremidade alta.

Framinan (2025) oferece evidência de domínio mais próxima: no PFSP estocástico, compara 10, 100 e 1.000 amostras para treinar GBT e relata melhoria da precisão com mais amostras. O estudo usa instâncias pequenas (até 20 jobs), outro modelo e outra variante de PFSP; portanto, não determina nossos tamanhos, mas apoia testar uma progressão por ordens de grandeza.

**A adaptação para nosso estudo é uma decisão de desenho experimental**, não uma fórmula prescrita por esses artigos.

## 3. Função de crescimento proposta

Usaremos uma progressão geométrica com cinco pontos, mínimo de 300 e máximo de 4.000 amostras:

N_i = round(N_min × (N_max / N_min)^(i / (K − 1))), para i = 0,...,K−1.

Com N_min=300, N_max=4000 e K=5, a razão constante é r=(4000/300)^(1/4)≈1,915.

Tamanhos resultantes (arredondados): **300, 574, 1.098, 2.103 e 4.000**.

A função é preferível a incrementos lineares porque cada etapa aumenta aproximadamente pela mesma proporção. Isso permite observar ganhos iniciais e saturação sem escolher arbitrariamente vários pontos próximos uns dos outros. O limite 4.000 é um teto inicial de viabilidade, não uma alegação de suficiência.

## 4. Fatores e repetições

- Instâncias: ta071 e ta111.
- Tamanhos: 300, 574, 1.098, 2.103, 4.000.
- Repetições independentes por ponto: 5.
- Amostragem: dois braços — (A) LHS em random keys seguido de stable argsort, que preserva o procedimento atual; (B) permutações uniformes geradas diretamente.
- Teste: um conjunto externo fixo de 1.000 permutações uniformes por instância, gerado com seed separada e compartilhado por todos os tamanhos, métodos e repetições.
- Modelo: mesma MLP da Semana 4, MLPRegressor(hidden_layer_sizes=(64,64), activation='relu', solver='adam', alpha=1e-4, learning_rate_init=1e-3, max_iter=1000, early_stopping=True, validation_fraction=0.15, n_iter_no_change=30); StandardScaler nas entradas e transformação padronizada do alvo.
- Seed do modelo e seed da amostragem serão registrados separadamente.
- Cada combinação será executada sequencialmente nesta fase. **Não iniciar treinamento paralelo** antes de observar consumo de memória/CPU e duração.

### Por que o teste é fixo?

O mesmo conjunto de teste externo evita que diferenças na composição do teste sejam confundidas com o efeito do tamanho de treinamento. Ele nunca participa da geração/seleção do treino, do early stopping ou da escolha de hiperparâmetros.

### Aninhamento dos conjuntos

As permutações uniformes serão geradas em uma sequência máxima por repetição e os menores tamanhos serão prefixos desse conjunto (subconjuntos aninhados). Isso reduz a variação da composição ao comparar N.

LHS convencional não oferece, em geral, designs aninhados válidos para todos os tamanhos. Para não chamar prefixos de um LHS grande de “LHS em N menor”, cada tamanho do braço LHS será gerado como um design LHS independente, com seed registrada. O teste permanece idêntico nos dois braços. Essa diferença de aninhamento será documentada como característica do desenho.

## 5. Métricas

### Regressão
- RMSE, MAE e R² no conjunto externo fixo.

### Ordenação
- Spearman rho e Kendall tau-b entre makespan previsto e exato no conjunto externo.

### Seleção
Para k ∈ {3, 10, 50}:
- top-k recall: interseção entre os k melhores reais e os k selecionados pelo surrogate, dividida por k;
- regret top-k: melhor makespan exato entre os k selecionados menos o melhor makespan exato de todo o teste;
- registrar também makespan médio dos selecionados.

O top-k é uma avaliação de seleção no conjunto externo; não equivale por si só ao desempenho do GWO em uma trajetória adaptativa. Após a curva, a validação no loop do GWO será uma etapa separada.

### Custo
- tempo para gerar e rotular o treino;
- tempo de treinamento;
- número de avaliações exatas;
- tempo de avaliação do conjunto de teste (contabilizado separadamente e uma única vez por instância).

## 6. Análise

- Exibir média e desvio padrão entre as cinco repetições para cada tamanho e método de amostragem.
- Plotar curvas de RMSE, Spearman, Kendall e top-k recall/regret em eixo x logarítmico.
- Não tratar as cinco repetições de uma mesma instância como cinco instâncias independentes.
- Não escolher modelo/hiperparâmetro pelo teste. A MLP e seus hiperparâmetros ficam congelados nesta etapa.
- Reportar separadamente ta071 e ta111; não agregar os dois em uma única média.
- Comparar LHS e uniforme como fator experimental. A diferença entre métodos será descritiva nesta fase; com cinco repetições, evitar alegações fortes de significância.

## 7. Critérios de interpretação e parada

Não definir um limiar universal de R² para declarar o surrogate útil. A finalidade é selecionar bons candidatos, então ranking e regret são desfechos centrais.

- Se regressão melhorar mas ranking/top-k não, o modelo não está necessariamente mais útil para o GWO.
- Se métricas de ranking e regret melhorarem com N, há evidência de benefício de mais dados.
- Se as curvas saturarem, escolher o menor N próximo do platô para reduzir custo.
- Se houver melhora contínua em 4.000, considerar uma nova etapa com limite maior, após medir custo.
- Se as curvas forem fracas em ambos os braços, investigar representação e distribuição de dados antes de aumentar N novamente.

## 8. Limitações explícitas

- O teste externo é formado por permutações uniformes; os candidatos visitados pelo GWO podem seguir outra distribuição. Portanto, a curva mede generalização para permutações uniformes, não garante ranking correto na população evolutiva.
- A representação atual codifica cada permutação como vetor de ranks normalizados com dimensão igual ao número de jobs. A dificuldade cresce de 100 para 500 features.
- LHS em random keys não implica distribuição uniforme de permutações depois de argsort; deduplicação e distribuição resultante devem ser registradas.
- Cinco repetições fornecem uma primeira curva exploratória, não uma análise estatística confirmatória.
- O orçamento de labels é significativo; a geração dos conjuntos será medida e reportada.

## 9. Referências

Ver experiments/meta_learning/referencias.md, especialmente Framinan (2025), Muñoz e Kirley (2021), Harada (2023), Liu et al. (2024) e Zhu et al. (2023).
