# Decisão técnica — adaptação do GWO ao DPFSP-DD

- **Data:** 2026-11-22
- **Status:** decisão inicial para implementação e piloto; não é ainda uma validação de desempenho.
- **Referência canônica:** Mirjalili, Mirjalili e Lewis (2014), *Grey Wolf Optimizer*, Advances in Engineering Software, 69, 46–61. DOI: https://doi.org/10.1016/j.advengsoft.2013.12.007.
- **Escopo:** codificação, decodificação e dinâmica de busca do GWO para o DPFSP-DD; o avaliador independente em `scripts/dpfsp_dd.py` permanece inalterado.

## 1. O que será preservado do artigo original

O artigo define uma população de lobos representados por vetores contínuos. A melhor solução é alfa, a segunda beta e a terceira delta. Para cada lobo e dimensão, são calculadas três posições candidatas:

\[
D_\alpha=|C_1X_\alpha-X|,\quad
D_\beta=|C_2X_\beta-X|,\quad
D_\delta=|C_3X_\delta-X|
\]

\[
X_1=X_\alpha-A_1D_\alpha,\quad
X_2=X_\beta-A_2D_\beta,\quad
X_3=X_\delta-A_3D_\delta
\]

\[
X(t+1)=\frac{X_1+X_2+X_3}{3}
\]

com \(A_k=2ar_{1,k}-a\), \(C_k=2r_{2,k}\), \(r_1,r_2\sim U[0,1]\). O parâmetro \(a\) decresce linearmente de 2 para 0 no GWO canônico. O módulo de \(A\) controla a tendência de exploração (\(|A|>1\)) ou explotação/ataque (\(|A|<1\)); \(C\) permanece aleatório durante a busca.

O pseudocódigo do artigo atualiza todos os agentes, avalia a população atualizada e então atualiza a hierarquia. A implementação nova seguirá atualização **síncrona**: todos os novos lobos serão calculados usando a mesma fotografia dos três líderes no início da geração. A hierarquia será atualizada somente depois de avaliar a geração inteira. Isso evita que um lobo atualizado primeiro altere os líderes usados pelos lobos seguintes.

## 2. Por que é necessária uma adaptação

O espaço de soluções do DPFSP-DD não é contínuo. Uma solução válida é uma partição dos jobs em \(F\) fábricas, com uma permutação em cada fábrica. Aplicar as equações diretamente a sequências inteiras não preservaria a validade da solução nem teria interpretação geométrica bem definida.

A adaptação escolhida usa **random keys contínuas**: o GWO continua operando em vetores reais e um decodificador determinístico transforma cada vetor em uma solução DPFSP-DD válida. Portanto, o método deve ser descrito como **GWO com representação random-key para DPFSP-DD**, e não como um GWO discreto canônico.

## 3. Codificação

Para uma instância com \(n\) jobs e \(F\) fábricas, cada lobo tem um vetor \(X\in[0,1]^{2n}\), dividido em:

- \(X^{(A)}=(x_0,\ldots,x_{n-1})\): chaves de atribuição de fábrica;
- \(X^{(P)}=(x_n,\ldots,x_{2n-1})\): chaves de prioridade/ordenação.

Cada job tem exatamente uma chave de atribuição e uma chave de prioridade. A codificação não impõe balanceamento artificial de quantidade de jobs entre fábricas.

## 4. Decodificação

Para cada job \(j\), a fábrica atribuída é:

\[
f(j)=\min(\lfloor F\cdot \operatorname{clip}(x_j,0,1)\rfloor,F-1).
\]

Assim, o valor de fronteira 1 é tratado como a última fábrica, evitando índice fora do intervalo.

Para cada fábrica \(f\), os jobs atribuídos a ela são ordenados crescentemente pelas chaves \(X^{(P)}_j\). A ordenação é estável; em caso de empate, a ordem original dos IDs de job (0-based) é preservada. O resultado é exatamente \(F\) sequências, incluindo sequências vazias quando nenhuma chave atribuir jobs a uma fábrica.

O decodificador garante:
- cada job aparece em exatamente uma fábrica;
- nenhum job é perdido ou duplicado;
- toda sequência é uma permutação do subconjunto atribuído;
- fábricas vazias são válidas, conforme a especificação do avaliador.

A função objetivo é sempre calculada pelo `DPFSPEvaluator` real, recebendo as sequências decodificadas. A representação contínua não será avaliada diretamente.

## 5. Atualização dos lobos

Para cada geração:

1. Congelar as posições dos líderes alfa, beta e delta.
2. Para cada lobo, gerar vetores aleatórios independentes por líder e dimensão e calcular as três posições candidatas pelas equações do artigo.
3. Tirar a média das três posições candidatas.
4. Projetar cada coordenada para \([0,1]\) por clipping.
5. Depois de atualizar todos os lobos, decodificar e avaliar a nova população.
6. Atualizar a hierarquia com as melhores soluções observadas até então.

Os líderes serão mantidos como arquivo *best-so-far* de três candidatos, para que uma solução líder não seja perdida caso a população atual se afaste dela. Empates de fitness serão resolvidos de modo determinístico pela ordem estável dos candidatos avaliados.

Não serão adicionados crossover, mutação, busca local ou reparo heurístico nesta primeira versão. O artigo original também mantém o GWO simples e aponta operadores evolutivos adicionais como possibilidades futuras; adicioná-los agora confundiria a avaliação da adaptação básica.

## 6. Decaimento de a

A implementação aceitará duas opções explícitas:

- `linear`: \(a(t)=2(1-t/T)\), correspondente ao GWO canônico;
- `quadratic`: \(a(t)=2(1-(t/T)^2)\), variante usada no experimento histórico chamado `exponential`.

O nome histórico `exponential` não será aceito na API nova: a fórmula não é exponencial. Resultados antigos não serão renomeados retroativamente. Para manter consistência com o protocolo experimental, \(t\) começa em zero e \(T\) é o número planejado de atualizações completas; assim, a última atualização usa \(t=T-1\), como no loop tradicional de T iterações.

## 7. Orçamento e contadores

A população inicial consome \(N\) avaliações reais. Cada geração completa consome outras \(N\), onde \(N\) é o número de lobos. Uma geração parcial não será executada. O contador reportado deve ser o número efetivo de chamadas ao avaliador, incluindo a população inicial.

O orçamento principal de 5.940 avaliações é divisível por 30 e 55:
- 30 lobos: 1 população inicial + 197 gerações;
- 55 lobos: 1 população inicial + 107 gerações.

Consultas ao Surrogate, avaliações reais de treino e reavaliações finais serão instrumentadas separadamente em etapa posterior; esta implementação inicial é somente GWO com avaliador real.

## 8. Limitações e riscos da representação

- Random keys criam regiões contínuas diferentes que decodificam para a mesma solução. Isso é inerente à representação; o número de vetores distintos não equivale ao número de soluções combinatórias distintas.
- A fronteira de atribuição divide o intervalo em regiões; pequenas mudanças dentro da mesma região não mudam a fábrica de um job.
- Clipping pode concentrar valores nos limites. O piloto deve monitorar diversidade de soluções decodificadas e proporção de coordenadas saturadas.
- Fábricas são idênticas. Permutar os rótulos das fábricas pode representar a mesma solução física. Para validação cruzada do Surrogate e contagem de soluções únicas, usar uma chave canônica que ordene lexicograficamente as sequências das fábricas; não alterar a solução entregue ao avaliador.
- Não há garantia de que random keys seja a melhor representação. Ela foi escolhida como primeira adaptação por manter as equações contínuas do artigo e permitir decodificação válida e auditável, com baixa quantidade de operadores adicionais.

## 9. Validação antes da bateria experimental

A implementação deve passar testes para:
1. limites e dimensionalidade dos vetores;
2. atribuição válida para \(F=1\), \(F>1\), \(x=0\), \(x=1\) e valores fora dos limites;
3. empates de chaves e estabilidade do desempate;
4. cobertura exata dos jobs e fábricas vazias;
5. determinismo com a mesma semente;
6. atualização síncrona e líderes congelados durante uma geração;
7. contagem exata de avaliações e respeito ao orçamento;
8. monotonicidade do melhor fitness *best-so-far*;
9. integração com o avaliador em instâncias manuais e pequenas;
10. diversidade de soluções decodificadas no piloto.

A aprovação dos testes de software não demonstra qualidade de otimização. A decisão de manter esta representação dependerá também do piloto em instâncias Small, intermediária e Large.

## 10. Referência primária

Mirjalili, S.; Mirjalili, S. M.; Lewis, A. (2014). Grey Wolf Optimizer. *Advances in Engineering Software*, 69, 46–61. https://doi.org/10.1016/j.advengsoft.2013.12.007.
