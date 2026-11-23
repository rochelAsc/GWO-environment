# Caracterização da dinâmica do GWO legado

**Data:** 2026-11-22  
**Escopo:** leitura estática do export histórico `scripts/sistemas_inteligentes_entregavel.py` e do avaliador `scripts/legacy_pfs.py`. Nenhuma dinâmica de otimização foi modificada nesta etapa.

## 1. Implementação de referência examinada

A classe `GWO` do export histórico é usada pelo wrapper `rodar_gwo_flowshop`. O vetor de busca tem dimensão igual ao número de jobs, limites `[0, 1]`, e a função objetivo é `FlowShopEngine.evaluate(..., objective="Tardiness")` por padrão.

O decoder do motor PFS converte as chaves em uma única permutação por `np.argsort(keys[:n_jobs])`; essa mesma sequência é aplicada a todas as máquinas. Portanto, trata-se de Permutation Flow Shop (PFS), não do DPFSP-DD com atribuição de fábricas.

## 2. Ciclo de execução observado

1. Inicializa `n_wolves` vetores uniformemente no domínio.
2. Avalia todos os vetores e ordena os fitness para obter alpha, beta e delta.
3. Para cada iteração, calcula um único valor de `a`.
4. Percorre os lobos em ordem crescente de índice.
5. Atualiza cada coordenada do lobo usando as posições alpha, beta e delta disponíveis naquele instante.
6. Faz clipping nos limites e avalia imediatamente o lobo atualizado.
7. Atualiza imediatamente a hierarquia alpha/beta/delta quando encontra uma solução melhor.
8. Ao fim da iteração, registra o melhor fitness histórico.

## 3. Propriedades que afetam a reprodução

### 3.1 Atualização sequencial e in-place

A matriz `positions` é modificada diretamente: `positions[i, d]` recebe o novo valor durante o laço. O próximo lobo lê a população já parcialmente atualizada.

Além disso, a hierarquia dos líderes é atualizada logo após cada avaliação. Assim, lobos posteriores na mesma iteração podem usar líderes diferentes daqueles usados pelos lobos anteriores.

**Consequência:** a implementação é assíncrona/sequencial dentro da geração. Não equivale a uma atualização síncrona que congela população e líderes no início da geração, calcula todos os novos lobos e só depois avalia/atualiza os líderes. Alterar isso mudaria o algoritmo histórico e invalidaria comparações diretas com resultados antigos.

### 3.2 Coeficiente de controle

Para o modo linear, o código usa:

\[
a(t)=2-2\frac{t}{T}, \quad t=0,\ldots,T-1.
\]

Como o laço termina em `T-1`, o valor final efetivamente utilizado é (2/T), não zero. O zero seria atingido apenas se houvesse uma iteração em (t=T).

O modo chamado `exponential` usa (a(t)=2(1-(t/T)^2)), que é uma curva quadrática, não uma exponencial. O modo `sqrt` usa (2\sqrt{1-t/T}).

### 3.3 Orçamento de avaliações

A população inicial é avaliada uma vez e cada lobo é reavaliado em cada iteração. Logo:

\[
N_{eval}=N_{wolves}(T+1).
\]

Por exemplo, com 30 lobos e `max_iter=200`, são 6.030 avaliações, não 6.000. A fórmula registrada em um bloco histórico da seção 10.5 (`max_iter * n_wolves`) subconta a população inicial em 30 avaliações. O contador interno `n_evals` da classe `GWO` contabiliza corretamente a inicialização e as atualizações.

### 3.4 Histórico

`history` começa com o melhor fitness da população inicial e recebe um valor ao fim de cada iteração. Seu comprimento é (T+1). O valor armazenado é o melhor alpha encontrado até aquele momento, portanto o histórico é best-so-far e não a média da população.

### 3.5 Decoder e representação

O vetor contém uma chave por job. A permutação é obtida ordenando as chaves. Não há variável de fábrica nem codificação de múltiplas sequências no caminho PFS padrão. Empates entre chaves são resolvidos pelo comportamento de `np.argsort` sem especificação explícita de algoritmo estável no decoder legado.

## 4. Diferenças que não devem ser apagadas silenciosamente

O GWO DPFSP-DD atual em `scripts/discrete_gwo_dpfsp.py` tem representação e dinâmica próprias, incluindo decodificação com atribuição de fábrica e atualização síncrona. Ele não deve ser tratado como uma simples refatoração do GWO PFS legado.

Para qualquer comparação histórica, devem ser preservados separadamente:
- o motor PFS e seu decoder;
- a atualização sequencial/in-place;
- a atualização imediata dos líderes;
- a fórmula e o calendário de `a`;
- a contagem de avaliações incluindo a população inicial.

## 5. Limites desta caracterização

Esta é uma caracterização estática do código versionado, não uma validação experimental de equivalência com resultados históricos. Não foram recuperadas as instâncias PFS exatas usadas nos experimentos antigos. Também não foi alterado nem validado matematicamente o lower bound de Potts nesta etapa.

## 6. Próxima etapa segura

Antes de qualquer refatoração ou comparação numérica, criar testes de caracterização que fixem:
- número exato de avaliações;
- comprimento e monotonicidade do histórico best-so-far;
- fórmula de `a` nos índices efetivamente executados;
- ordem sequencial de atualização dos lobos e dos líderes;
- decoder PFS em casos sem empate e com empate.

Só depois desses testes deve ser considerada qualquer mudança estrutural, mantendo a versão histórica como referência.
