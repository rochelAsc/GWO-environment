# Especificação — DPFSP com Total Tardiness (DPFSP-DD)

- **Status:** rascunho para revisão
- **Escopo:** modelo matemático e contrato do avaliador; não especifica ainda a codificação do GWO.
- **Dataset:** `data/instances/DPFSP_DD.zip`
- **Decisões aprovadas:** fábricas vazias são permitidas; representação/decodificação do GWO será definida separadamente.

## 1. Objetivo

Definir uma especificação independente de algoritmo para avaliar soluções do Distributed Permutation Flow Shop Scheduling Problem with Due Dates (DPFSP-DD), cujo critério é minimizar o Total Tardiness.

O avaliador deve receber uma instância e uma solução já decodificada em sequências por fábrica. Não deve depender do GWO, Fuzzy, Surrogate ou de qualquer representação contínua usada por esses métodos.

## 2. Notação

- (J=\{0,\ldots,n-1\}\): conjunto de jobs.
- (M=\{0,\ldots,m-1\}\): conjunto de máquinas, na ordem fixa do fluxo.
- (F=\{0,\ldots,F-1\}\): conjunto de fábricas.
- (p_{jk}\): tempo de processamento do job (j) na máquina (k).
- (d_j\): due date do job (j).
- (\pi_f=(\pi_f(1),\ldots,\pi_f(n_f))\): sequência dos jobs atribuídos à fábrica (f).

Os tempos de processamento são comuns às fábricas, que são consideradas idênticas. O dataset fornece uma matriz de processamento por instância, não uma matriz independente por fábrica.

## 3. Hipóteses do problema

A especificação adota as seguintes hipóteses:

1. Existem (F) fábricas idênticas, cada uma com (m) máquinas em série.
2. Todas as fábricas podem processar todos os jobs.
3. Cada job é atribuído a exatamente uma fábrica e não pode ser transferido.
4. Cada job visita todas as máquinas na ordem (0,1,\ldots,m-1).
5. Em cada fábrica, todos os jobs seguem a mesma ordem nas máquinas: a sequência π_f é uma permutação comum às máquinas daquela fábrica.
6. Cada máquina processa no máximo um job por vez.
7. Cada job ocupa no máximo uma máquina por vez.
8. Os jobs estão disponíveis no instante zero.
9. Não há preempção.
10. Tempos de setup são nulos ou já estão incorporados aos tempos de processamento.
11. Não há indisponibilidade de máquinas, buffers limitantes, bloqueio, transporte entre fábricas ou restrições adicionais.
12. Uma ou mais fábricas podem ficar vazias. Isso é permitido pela representação de solução adotada neste projeto.

As hipóteses seguem a formulação clássica do DPFSP e devem ser mantidas distintas de variantes como DFSP sem a restrição de permutação, DPFSP heterogêneo, blocking, no-wait ou no-idle.

## 4. Representação matemática da solução

Uma solução é uma tupla de (F) sequências:

\[
S=(\pi_0,\pi_1,\ldots,\pi_{F-1}).
\]

As sequências devem formar uma partição de (J):

\[
\bigcup_{f=0}^{F-1}\pi_f=J,
\qquad
\pi_f\cap\pi_g=\varnothing\quad(f\ne g).
\]

Cada job deve aparecer exatamente uma vez. Uma sequência vazia é válida. A ordem das fábricas é identificável na estrutura, mas, como as fábricas são idênticas, permutar os rótulos das fábricas não altera o valor objetivo.

**Fora do escopo desta especificação:** como um vetor contínuo do GWO será convertido em atribuições e sequências. O avaliador não fará essa conversão.

## 5. Cálculo dos tempos de conclusão

Para a fábrica (f), posição (r) da sequência e máquina (k), seja (C_{f,r,k}) o instante de conclusão da operação do job π_f(r) na máquina (k).

Para (r\geq1) e (k\geq0):

\[
C_{f,r,k}
=
p_{\pi_f(r),k}
+
\max\left(
\begin{cases}
C_{f,r-1,k}, & r>1,\\
0, & r=1
\end{cases},
\begin{cases}
C_{f,r,k-1}, & k>0,\\
0, & k=0
\end{cases}
\right).
\]

A recorrência produz o cronograma de início mais cedo compatível com a sequência fixa. O completion time do job (j=\pi_f(r)) é:

\[
C_j=C_{f,r,m-1}.
\]

Jobs em fábricas diferentes não competem pelas mesmas máquinas; portanto, os cronogramas das fábricas são calculados independentemente.

## 6. Função objetivo

O atraso (tardiness) do job (j) é:

\[
T_j=\max(0,C_j-d_j).
\]

O Total Tardiness da solução é:

\[
TT(S)=\sum_{j\in J}T_j
=\sum_{j\in J}\max(0,C_j-d_j).
\]

O problema de otimização é:

\[
\boxed{\min_{S\in\mathcal{S}} TT(S)}
\]

em que \(\mathcal{S}\) é o conjunto de soluções que satisfazem a partição dos jobs e as restrições de sequenciamento descritas acima.

Não confundir Total Tardiness com makespan \(C_{\max}=\max_j C_j\), maximum tardiness \(T_{\max}=\max_j T_j\), ou total completion time \(\sum_j C_j\). O objetivo desta variante é exclusivamente o Total Tardiness não ponderado.

## 7. Contrato do avaliador

### Entrada

**Instância**
- (n\) e (m\), inteiros positivos;
- (F\), inteiro positivo;
- matriz (P\) de dimensão (n\times m\), com tempos de processamento inteiros positivos;
- vetor (d\) de dimensão (n\), com due dates inteiras não negativas.

**Solução**
- exatamente (F\) sequências;
- cada elemento é um identificador de job em (J\);
- sequências vazias são permitidas.

### Validação obrigatória

O avaliador deve rejeitar explicitamente:
- número de sequências diferente de (F\);
- identificadores fora de (J\);
- jobs duplicados;
- jobs ausentes;
- dimensões incompatíveis de (P\) ou (d\);
- tempos de processamento não positivos ou não inteiros;
- due dates negativas ou não inteiras.

Não deve gerar instâncias aleatórias, corrigir silenciosamente uma solução inválida, descartar jobs ou retornar `None` para uma entrada inválida. Deve lançar erro explícito com mensagem útil.

### Saída

O avaliador deve retornar, no mínimo:
- Total Tardiness;
- completion time de cada job;
- tardiness de cada job;
- fábrica e posição de cada job;
- completion times por fábrica/máquina, ou estrutura equivalente suficiente para auditoria.

A avaliação deve ser determinística, não modificar a instância nem a solução recebida e usar aritmética inteira, sem arredondamento de ponto flutuante.

## 8. Casos de referência para testes unitários

Os testes abaixo definem resultados esperados calculáveis manualmente.

### Caso A — uma máquina, uma fábrica

- (n=2,m=1,F=1\)
- (p_{0,0}=3, p_{1,0}=2\)
- (d_0=2, d_1=10\)
- solução: π₀ = [0,1]

Esperado: (C_0=3, C_1=5\); (T_0=1, T_1=0\); (TT=1\).

### Caso B — duas máquinas, uma fábrica

- (n=2,m=2,F=1\)
- job 0: ((2,3)\); job 1: ((4,1)\)
- (d_0=4, d_1=10\)
- solução: π₀ = [0,1]

Esperado: conclusões na última máquina (C_0=5, C_1=7\); tardiness (T_0=1, T_1=0\); (TT=1\).

### Caso C — duas fábricas independentes

- (n=2,m=1,F=2\)
- (p_{0,0}=3, p_{1,0}=4\)
- (d_0=2, d_1=3\)
- solução: π₀ = [0], π₁ = [1]

Esperado: (C_0=3, C_1=4\); (T_0=1, T_1=1\); (TT=2\).

### Caso D — fábrica vazia

- (n=2,m=1,F=2\)
- mesma instância do Caso C;
- solução: π₀ = [0,1], π₁ = []

Esperado: solução estruturalmente válida. O valor objetivo deve ser calculado normalmente; a fábrica vazia não gera operações nem atraso.

### Casos de rejeição

Testar separadamente: job duplicado, job ausente, identificador negativo, identificador igual a (n\), número incorreto de fábricas, matriz com dimensão errada, processamento zero/negativo e due date negativa.

## 9. Estratégia de validação

A implementação somente poderá ser considerada confiável depois de:

1. Passar todos os testes unitários acima.
2. Passar testes de propriedades: toda conclusão é maior ou igual à conclusão de seus predecessores; todos os tempos são inteiros e não negativos; (TT\geq0\).
3. Ser determinística para a mesma instância e solução.
4. Ser comparada com cálculo manual em instâncias minúsculas.
5. Ser comparada com uma formulação independente (por exemplo, enumeração exaustiva em instâncias minúsculas ou um modelo exato) antes de executar experimentos em lote.
6. Ter o parser do dataset testado separadamente do avaliador, com exemplos Small e Large e conferência do número de jobs, máquinas, fábricas, tempos de processamento e due dates.

A validação estrutural anterior do ZIP é uma verificação sintática do formato observado; não substitui a validação semântica do parser nem a validação matemática do avaliador.

## 10. Separação entre problemas e algoritmos

- O PFS clássico permanece um problema separado, com seu próprio avaliador e benchmarks Taillard.
- O DPFSP-DD usa este avaliador e o conjunto com due dates.
- Nenhum resultado de PFS pode ser agregado ou comparado diretamente com resultado de DPFSP-DD.
- Baseline, Tunado, Fuzzy e Surrogate poderão usar o avaliador quando suas representações forem decodificadas em soluções válidas.
- A codificação, os operadores de busca e as regras de reparo pertencem à camada do algoritmo, não ao avaliador.

## 11. Referências

1. Naderi, B.; Ruiz, R. (2010). The distributed permutation flowshop scheduling problem. *Computers & Operations Research*, 37(4), 754–768. DOI: https://doi.org/10.1016/j.cor.2009.06.019.
2. Khare, A.; Agrawal, S. (2021). Effective heuristics and metaheuristics to minimise total tardiness for the distributed permutation flowshop scheduling problem. *International Journal of Production Research*, 59(23), 7266–7282. DOI: https://doi.org/10.1080/00207543.2020.1837982.
3. Khare, A. (2020). DPFSP with due dates. *Mendeley Data*, V1. DOI: https://doi.org/10.17632/4tkhdx4jjx.1.
4. Gogos, C. (2023). Solving the Distributed Permutation Flow-Shop Scheduling Problem Using Constrained Programming. *Applied Sciences*, 13(23), 12562. DOI: https://doi.org/10.3390/app132312562.

## 12. Pontos ainda sujeitos a confirmação

- Confirmar por inspeção de exemplos brutos que o parser lê a matriz de processamento e o vetor de due dates do DPFSP-DD na ordem correta. O avaliador descrito aqui pressupõe uma matriz comum (n\times m\), consistente com fábricas idênticas.
- Confirmar a convenção de indexação dos jobs e máquinas na interface interna (recomendação: 0-based, convertendo no parser).
- Confirmar se a instância do dataset inclui alguma particularidade além das hipóteses clássicas explicitadas; não adicionar restrições sem evidência documental.
- Registrar uma divergência na descrição do benchmark Small de Gogos (2023): o texto da seção 2.1 lista jobs `{4,6,8,10,12,16}`, mas a legenda da Figura 6 inclui também `14`; o inventário do ZIP deste projeto confirma arquivos com 14 jobs. Para contagens e seleção experimental, prevalece o conteúdo efetivo do dataset, não a lista textual incompleta.

Nenhum código de algoritmo ou avaliador é implementado por este documento.
