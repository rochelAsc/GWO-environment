# **Grey Wolf Optimizer (GWO): Formulação Matemática e Mapeamento para Aplicação em Predição de Notificações de Dengue** 

## **1 Introdução e Inspiração Biológica** 

O _Grey Wolf Optimizer_ (GWO), proposto por Mirjalili, Mirjalili e Lewis (2014), é uma metaheurística bioinspirada que simula a hierarquia social e o comportamento de caça em matilha do lobo cinzento ( _Canis lupus_ ) [1]. Na natureza, a matilha possui uma estrutura de liderança rígida dividida em quatro categorias [2]: 

- **Alpha (** _α_ **)** : líder da matilha, responsável pelas decisões de caça, descanso e vigília; 

- **Beta (** _β_ **)** : subordinado ao alpha, auxilia na tomada de decisão e impõe disciplina; 

- **Delta (** _δ_ **)** : desempenha papéis específicos (batedores, sentinelas, caçadores, cuidadores); 

- **Omega (** _ω_ **)** : último nível hierárquico, serve como bode expiatório e mantém a estrutura de dominância. 

O processo de caça é dividido em três etapas principais: (i) **rastreamento e aproximação** da presa; (ii) **cerco** à presa; e (iii) **ataque** quando a presa para de se mover [1]. O GWO traduz essas etapas em operadores matemáticos que atualizam iterativamente as posições dos agentes de busca [2]. 

## **2 Variáveis Críticas de Estado** 

As variáveis que controlam o comportamento do algoritmo são: 

- **Diversidade populacional** : medida pela dispersão das posições dos lobos no espaço de busca. Alta diversidade evita convergência prematura para ótimos locais [2]. O coeficiente _⃗C_ atua diretamente na manutenção dessa diversidade [1]. 

- **Taxa de convergência** : velocidade com que a matilha se aproxima do ótimo. Controlada pelo decaimento linear do vetor _⃗a_ de 2 até 0 ao longo das iterações [1]. 

- **Balanceamento exploração/explotacão** : controlado pelo coeficiente _⃗A_ . Quando _|⃗A| ≥_ 1, o algoritmo prioriza exploração (busca em novas regiões); quando _|⃗A| <_ 1, prioriza explotação (refinamento das melhores soluções) [1]. 

## **3 Formulação Matemática dos Operadores** 

### **3.1 Cerco à Presa** 

A distância entre um lobo e a presa é modelada por: 



onde _t_ é a iteração atual, _⃗Xp_ é a posição da presa e _⃗X_ é a posição do lobo. A atualização de posição é: 



Os coeficientes _⃗A_ e _⃗C_ são calculados por: 



onde _⃗r_ 1 _,⃗r_ 2 _∼ U_ [0 _,_ 1] e _⃗a_ decresce linearmente de 2 a 0 [1, 2]. 

1 

### **3.2 Caça (Liderança por** _α_ **,** _β_ **e** _δ_ **)** 

Como a posição da presa é desconhecida, assume-se que os três melhores lobos ( _α_ , _β_ , _δ_ ) têm melhor estimativa. As distâncias são: 



As posições intermediárias são: 



A posição final do lobo _ω_ é a média: 



### **3.3 Ataque à Presa** 

Quando _|⃗A| <_ 1, a matilha converge para a presa (explotação). Quando _|⃗A| ≥_ 1, os lobos se afastam para explorar novas regiões [1]. 

## **4 Mapeamento de Entradas, Saídas e Representação dos Indivíduos** 

### **4.1 Representação dos Indivíduos** 

Cada lobo _i_ é representado por um vetor de dimensão _D_ : 

A população é uma matriz _N × D_ : 



onde _N_ é o tamanho da população (número de lobos) e _D_ é a dimensionalidade do problema [3]. 

### **4.2 Entradas** 

As entradas do algoritmo são: 

- Tamanho da população _N_ ; 

- Número máximo de iterações _T_ max; 

- Limites inferior _lb_ e superior _ub_ de cada dimensão do espaço de busca; 

- Função de aptidão _f_ ( _⃗X_ ) a ser minimizada. 

- A inicialização é feita por: 



### **4.3 Saídas** 

A saída do GWO é a posição do lobo _α_ ao final das iterações: 



que representa a melhor solução encontrada para o problema de otimização [1]. 

2 

## **5 Função de Aptidão e Espaço de Busca para Predição de Dengue** 

### **5.1 Função de Aptidão** 

Para o contexto de predição de notificações de dengue, a função de aptidão é definida como o erro de previsão de um modelo de séries temporais. Seja _y_ ˆ _t_ o valor predito e _yt_ o valor real de notificações no instante _t_ , utiliza-se o RMSE ( _Root Mean Square Error_ ): 



O objetivo é **minimizar** _f_ ( _⃗X_ ). O vetor _⃗X_ representa os hiperparâmetros do modelo preditivo (ex.: taxa de aprendizado, número de camadas ocultas, número de neurônios por camada, tamanho da janela de entrada). 

### **5.2 Espaço de Busca** 

O espaço de busca é definido pelos limites de cada hiperparâmetro. A Tabela 1 apresenta um exemplo para uma rede LSTM aplicada à predição de dengue. 

|Tabela 1: Espaço de busca|para hiperp|arâmetros d|e uma LSTM.|
|---|---|---|---|
|**Hiperparâmetro**|**Mínimo**|**Máximo**|**Tipo**|
|Taxa de aprendizado|10<sup>_−_5</sup>|10<sup>_−_1</sup>|Contínuo (log)|
|Número de camadas LSTM|1|4|Inteiro|
|Unidades por camada|16|256|Inteiro|
|Tamanho da janela|7|90|Inteiro|
|Taxa de dropout|0.0|0.5|Contínuo|



### **5.3 Integração GWO + Modelo Preditivo** 

A cada iteração do GWO, cada lobo representa uma configuração de hiperparâmetros. O modelo é treinado no conjunto de treino e avaliado no conjunto de validação. O RMSE resultante é retornado como aptidão do lobo. Os três melhores lobos ( _α_ , _β_ , _δ_ ) guiam a busca na iteração seguinte. 

## **6 Considerações Finais** 

O GWO é um algoritmo com poucos parâmetros, sem necessidade de informação de derivadas e com mecanismo de busca global robusto [1]. Sua aplicação à predição de notificações de dengue é promissora, pois permite otimizar automaticamente arquiteturas de modelos de séries temporais, reduzindo o esforço manual de ajuste e potencialmente melhorando a acurácia preditiva. 

## **Referências** 

- [1] MIRJALILI, S.; MIRJALILI, S. M.; LEWIS, A. Grey Wolf Optimizer. _Advances in Engineering Software_ , v. 69, p. 46–61, 2014. 

- [2] CHOUDHARY, V.; TANWAR, S.; CHOUDHURY, T. et al. Grey Wolf Optimizer: A review. _MethodsX_ , v. 12, 102747, 2024. 

- [3] BOUCHIBA, K.; BADIS, L. Gray Wolf Optimization for CNN hyperparameter tuning. Trabalho de Conclusão de Curso, Université de Bouira, 2023. 

3 

