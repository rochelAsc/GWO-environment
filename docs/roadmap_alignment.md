# Alinhamento do roteiro acadêmico e auditoria inicial

**Data:** 2026-11-22  
**Base examinada:** commit c212951b7e3cf9516ca3742cb25889cc0a2a1e84  
**Preservação:** auditoria aditiva; nenhum artefato histórico foi modificado.

## 1. Objetivo

Confrontar o roteiro acadêmico publicado com o estado do repositório e com o protocolo proposto para a terceira rodada. Este documento registra lacunas e riscos antes de qualquer refatoração ou execução em larga escala.

## 2. Matriz de alinhamento

| Semana | Exigência | Estado observado | Ação necessária |
|---|---|---|---|
| 1 — Pesquisa | Formulação, representação, fitness e espaço de busca | Há implementação e relatórios; teoria precisa ser consolidada | Documentar formulação matemática e fontes primárias |
| 2 — Baseline | GWO do zero; pelo menos duas instâncias Taillard de PFS; 30 execuções e convergência | O script valida Rastrigin, Rosenbrock e Ackley, funções contínuas, não instâncias Taillard de Flow Shop | Acrescentar benchmark Taillard/PFS separado e testes do solver |
| 3 — Optuna | Sintonia, importância e histórico | Há integração Optuna; espaço de busca, objetivo e risco de sobreajuste precisam de auditoria | Reproduzir sintonia versionada e congelar parâmetros |
| 4 — Surrogate | LHS, MLP/RBF, métricas e custo | Existe experimento exploratório; generalização e avaliação final têm riscos | Treinar por instância, separar por permutação e validar no motor real |
| 5 — Fuzzy | Entradas de estado, regras, ajuste e histórico | Existe controlador Mamdani; há erro de variável e estado global a investigar | Corrigir em módulo novo e testar isolamento |
| 6 — Benchmark | Quatro versões, instâncias variadas, estatística e avaliações | Protocolo atual cobre quatro versões, 23 instâncias e duas ablações; ainda não executado | Piloto, auditoria de orçamento e bateria integral |
| 7 — Meta-Learning | Metacaracterísticas e recomendador de solver | Não existe etapa correspondente no protocolo atual | Especificar meta-dataset e validação por instância |
| 8 — Artigo | Artigo de 8–10 páginas e repositório reproduzível | Planejado, não iniciado | Congelar métodos, resultados, limitações e artefatos |

## 3. Risco crítico: identidade do problema e compatibilidade das instâncias

O arquivo do repositório chama-se DPFSP_DD.zip. A página do conjunto de dados original o descreve como **DPFSP with due dates**, uma extensão do benchmark de Naderi e Ruiz (2010) para Distributed Permutation Flow Shop Scheduling Problem com datas de entrega e critério de total tardiness.

Fonte: Khare, Ankit (2020), *DPFSP with due dates*, Mendeley Data, DOI https://doi.org/10.17632/4tkhdx4jjx.1. A página descreve explicitamente o conjunto como extensão do benchmark Naderi e Ruiz para DPFSP com datas de entrega. <Cite />

O motor legado em scripts/sistemas_inteligentes_entregavel.py apresenta comportamento de **Permutation Flow Shop (PFS) de uma única fábrica**:
- em evaluate(..., mode="PFS"), decodifica uma única permutação e a reutiliza em todas as máquinas;
- não há, nesse caminho, variável explícita de atribuição de jobs a fábricas nem avaliação de múltiplas fábricas;
- o parser lê jobs, máquinas, pares máquina-tempo por job e datas de entrega.

Isso cria uma incompatibilidade potencial: um conjunto DPFSP não pode ser declarado benchmark de PFS sem demonstrar que formulação, parser e função objetivo preservam o problema de origem.

Antes da terceira rodada, é obrigatório:
1. Inspecionar conteúdo e formato de cada instância do ZIP.
2. Identificar formulação matemática e regras de atribuição/roteamento do DPFSP.
3. Confrontar essas regras com parser, decoder e cálculo de conclusão/tardiness.
4. Decidir entre implementar DPFSP corretamente em implementação nova ou usar instâncias Taillard de PFS para o experimento PFS da Semana 2.
5. Se ambos forem mantidos, tratá-los como famílias experimentais distintas, com protocolos próprios.

Não converter DPFSP em PFS por conveniência nem alterar a interpretação de instâncias silenciosamente.

## 4. Lacunas e riscos técnicos confirmados no código legado

O script histórico deve permanecer intacto. Correções devem nascer em arquivos novos e ter testes.

### 4.1 GWO
- A classe GWO conta chamadas em self.n_evals, incluindo a população inicial.
- A população é atualizada sequencialmente; a hierarquia alfa/beta/delta pode mudar durante a mesma iteração. É uma variante sequencial/assíncrona, não se deve descrevê-la automaticamente como atualização síncrona canônica.
- O modo chamado exponential calcula 2 * (1 - progress**2), uma curva quadrática/polinomial. Novos experimentos devem usar o nome quadratic; dados históricos preservam o nome original.
- O contador n_evals é preferível a contagens manuais por população × iterações.

### 4.2 FlowShopEngine
- carregar_instancia_txt e calcular_lower_bound_potts estão declarados sem self e sem @staticmethod. Chamadas pela classe funcionam no padrão atual; chamadas pela instância podem falhar.
- O parser gera instância aleatória se o arquivo não existe ou se a leitura falha. Isso pode mascarar erros de dados. A implementação nova deve falhar explicitamente.
- evaluate não rejeita explicitamente modos/objetivos desconhecidos.
- bucket_sort_decode usa np.argsort; o desempate de chaves iguais não está definido.
- O modo PFS usa uma permutação comum a todas as máquinas. A semântica DPFSP precisa de implementação própria caso esse seja o problema estudado.

### 4.3 Fuzzy
- A execução atribui fuzzy = gwo_fuzzy.optimize()[1], mas imprime best_fuzzy, que não foi definido nesse trecho.
- ControlSystemSimulation é criada globalmente e reutilizada; testar possível estado/cache entre execuções antes de classificar como bug.
- A comparação deve manter a mesma dinâmica de GWO-55-Q e alterar apenas o controlador.

### 4.4 Surrogate
- O código exploratório usa a previsão da MLP como fitness final; isso não prova que a solução tenha o mesmo valor no FlowShop real.
- Split aleatório por linhas de chaves contínuas pode colocar a mesma permutação em treino e teste. Agrupar por permutação decodificada.
- Contar separadamente treino, inferências e validação real.
- Métricas de regressão não substituem a avaliação da solução otimizada no motor real.

## 5. Meta-Learning: proposta compatível com o tamanho dos dados

A Semana 7 deve ser tratada como experimento separado, dependente de benchmark válido.

### 5.1 Unidade de observação
Uma linha do meta-dataset representa uma instância, não uma execução/semente. Repetições estimam desempenho do algoritmo naquela instância; não criam novas instâncias independentes.

### 5.2 Metacaracterísticas candidatas
- Número de jobs, máquinas e, se aplicável, fábricas.
- Média, desvio padrão, coeficiente de variação, mínimo e máximo dos tempos de processamento.
- Carga total por máquina e desequilíbrio entre cargas.
- Estatísticas das datas de entrega e folgas relativas a limites inferiores/estimativas de conclusão.
- Estatísticas de diversidade/repetição das permutações amostradas.
- Família/origem da instância, quando disponível.

As características devem ser definidas antes de observar qual algoritmo venceu e ter cálculo versionado e testado.

### 5.3 Rótulo de recomendação
Não escolher o rótulo pelo melhor resultado isolado. Definir previamente métrica de decisão (por exemplo, fitness real com custo computacional) e estimar desempenho por instância com seeds pareadas. Reportar empates e diferenças pequenas; permitir classe sem diferença prática quando não houver vencedor confiável.

### 5.4 Validação e limite de generalização
- Separar treino e teste por instância, nunca por linha de execução.
- Com 23 instâncias, leave-one-instance-out é apenas análise exploratória; incluir baseline majoritário e incerteza.
- Não usar resultados da mesma instância para criar seu rótulo e avaliar sua recomendação.
- Ampliar o conjunto com instâncias independentes e famílias distintas, incluindo PFS/Taillard e DPFSP/DD separados, se possível.
- Não apresentar acurácia/F1 sobre 23 instâncias como prova de generalização ampla.

## 6. Sequência antes da bateria integral

1. Preservar e congelar os artefatos legados.
2. Inventariar o ZIP e confirmar a formulação do problema.
3. Obter/organizar instâncias Taillard de PFS se a Semana 2 exigir PFS; registrar fonte, licença e hashes.
4. Criar implementação nova e modular, com parser e motor específicos para cada variante.
5. Criar testes de caracterização do GWO legado e testes unitários do motor.
6. Corrigir Fuzzy e Surrogate em módulos novos.
7. Executar piloto em instâncias representativas de cada família de problema.
8. Congelar protocolo e hiperparâmetros antes da bateria integral.
9. Executar benchmark, depois meta-learning, e então gerar tabelas, figuras e artigo a partir de dados brutos imutáveis.

## 7. Critério de avanço

Não iniciar as 4.140 execuções até que:
- identidade/formulação das instâncias esteja confirmada;
- motor corresponda à formulação escolhida;
- parser, decoder, função objetivo e contadores tenham testes;
- quatro versões executem no piloto sem erros;
- Surrogate seja validado em permutações não vistas e reavaliado no motor real;
- custos estejam medidos e protocolo congelado.

## 8. Referência
Khare, A. (2020). *DPFSP with due dates*. Mendeley Data, Version 1. https://doi.org/10.17632/4tkhdx4jjx.1
