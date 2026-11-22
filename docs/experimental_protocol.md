# Protocolo experimental — GWO aplicado ao Flow Shop

**Status:** proposta aprovada para planejamento; parâmetros sujeitos ao piloto técnico antes da bateria completa.  
**Escopo:** comparação Baseline, Tunado, Fuzzy e Surrogate nas 23 instâncias disponíveis, com ablação fatorial dos parâmetros do GWO.

## 1. Objetivo

Avaliar, de forma reproduzível e comparável, a qualidade das soluções para o problema Flow Shop com objetivo de minimizar o Total Tardiness, o custo computacional e a contribuição individual de população, decaimento, controle Fuzzy e modelo Surrogate.

Os experimentos exploratórios anteriores em uma única instância serão preservados, mas não serão tratados como evidência de desempenho geral.

## 2. Conjunto de instâncias e repetições

- Usar as 23 instâncias existentes no pacote do projeto: 20 Small e 3 Large.
- Executar 30 sementes por instância e configuração, identificadas por 0 a 29.
- Manter o pareamento lógico por instância e índice de semente entre configurações.
- Registrar o nome, dimensão, porte e hash do arquivo de cada instância.
- Não substituir nem sobrescrever resultados históricos.

A bateria principal terá 6 configurações × 23 instâncias × 30 sementes = **4.140 execuções**. As quatro versões solicitadas estarão presentes em todas as 23 instâncias; as duas configurações extras completam a ablação fatorial.

## 3. Configurações

| ID | Configuração | Lobos | Decaimento de a | Papel |
|---|---|---:|---|---|
| GWO-30-L | Baseline | 30 | Linear | Referência |
| GWO-30-Q | Ablação | 30 | Quadrático | Isola efeito do decaimento |
| GWO-55-L | Ablação | 55 | Linear | Isola efeito da população |
| GWO-55-Q | Tunado | 55 | Quadrático | Configuração otimizada |
| GWO-Fuzzy | Fuzzy | 55 | Controlado por Fuzzy, com schedule quadrático como referência | Efeito do controlador |
| GWO-Surrogate | Surrogate | 55 | Quadrático | Busca guiada por modelo substituto |

**Nomenclatura:** a fórmula atualmente chamada `exponential` no código é `a = 2(1 - (t/T)^2)`, isto é, decaimento quadrático/polinomial. Nos novos resultados, usar o nome `quadratic`. Os registros antigos permanecem com seus nomes originais, acompanhados desta observação.

A comparação Fuzzy deve usar a mesma população e o mesmo orçamento de GWO-55-Q. Assim, a diferença observada poderá ser atribuída ao controlador com menos confundimento.

## 4. Orçamento de avaliações

### 4.1 GWO tradicional, ablação e Fuzzy

A comparação principal usará **5.940 avaliações reais da função objetivo por execução**. Esse valor é divisível pelos tamanhos de população 30 e 55:

- 30 lobos: 198 lotes completos de população (inicialização + 197 atualizações).
- 55 lobos: 108 lotes completos de população (inicialização + 107 atualizações).

Logo, o número de atualizações será ajustado por tamanho de população. O critério de parada será o contador efetivo de avaliações, não uma estimativa manual baseada apenas em iterações. O contador deverá incluir a avaliação da população inicial.

Essa faixa é próxima do orçamento histórico do Baseline (6.030 avaliações) e permite comparação exata entre populações de 30 e 55 sem interromper uma geração pela metade.

### 4.2 Surrogate

O Surrogate tem dois custos diferentes e eles não podem ser somados sob o rótulo genérico de “avaliações”:

1. **Treinamento:** começar com 500 amostras LHS por instância, avaliadas no FlowShop real. Registrar quantidade solicitada, quantidade efetivamente avaliada e quantidade de permutações decodificadas únicas.
2. **Busca:** 5.940 consultas ao modelo por execução, com 55 lobos e 107 atualizações completas.
3. **Validação final:** decodificar a melhor posição prevista e avaliá-la uma vez no FlowShop real por execução.

O treinamento será feito uma vez por instância e reutilizado nas 30 sementes daquela instância. O relatório apresentará o custo de treinamento integral e também seu custo amortizado por execução, sem ocultá-lo. Consultas ao modelo, avaliações reais de treinamento e avaliações reais de validação terão contadores separados.

O Surrogate será considerado competitivo apenas com base no **fitness real da solução reavaliada**, nunca pelo valor previsto isoladamente.

### 4.3 Piloto obrigatório

Antes da bateria completa, executar um piloto em três instâncias representativas (uma Small, uma intermediária e uma Large), com poucas sementes fixadas e todas as configurações aplicáveis. O piloto deve verificar:

- contadores de avaliações e limites de orçamento;
- ausência de vazamento entre treino e teste do Surrogate;
- qualidade da previsão em permutações não vistas;
- tempo de treinamento, inferência e avaliação real;
- viabilidade de execução e armazenamento.

Se 500 amostras não produzirem cobertura/qualidade suficiente para o Surrogate, ajustar o tamanho do conjunto de treino no piloto, registrar a justificativa e congelar essa decisão antes da bateria completa. Não alterar o protocolo no meio da execução.

## 5. Treinamento e validação do Surrogate

- Treinar um modelo independente por instância, pois a função objetivo e a escala do problema variam entre instâncias.
- Separar treino e teste por **permutação decodificada**, não por linha/amostra de chaves contínuas. Chaves diferentes que geram a mesma sequência de jobs devem permanecer no mesmo grupo.
- O conjunto de teste não poderá ser usado para otimização, seleção de hiperparâmetros ou ajuste do modelo.
- Registrar arquitetura, hiperparâmetros, scaler, semente, versões das bibliotecas e curva de treinamento.
- Reportar MAE, RMSE e R² no conjunto de teste agrupado, além do número de grupos/permutação únicos em cada partição.
- Após a busca, decodificar a melhor posição, avaliá-la no FlowShop real e registrar fitness previsto e fitness real.
- Medir separadamente tempo de geração dos dados, treinamento, inferência durante a busca e validação final.

Se uma instância tiver poucas permutações distintas para uma separação treino/teste confiável, registrar essa limitação e avaliar enumeração exata quando o espaço for computacionalmente viável. Não apresentar R² como evidência de generalização quando o teste não contiver permutações inéditas.

## 6. Reprodutibilidade e instrumentação

Cada registro de execução deverá conter, no mínimo:

- identificador do experimento e versão do protocolo;
- instância, porte, número de jobs e máquinas, hash do arquivo;
- algoritmo/configuração, população, schedule de (a), iterações e orçamento;
- semente global e semente efetivamente usada por cada componente estocástico;
- fitness previsto (quando aplicável) e fitness real final;
- avaliações reais, consultas Surrogate e avaliações de validação em campos distintos;
- tempo total e tempos de treinamento/inferência/avaliação separados;
- status da execução, erro (se houver) e motivo de parada;
- versões de Python e dependências, sistema operacional e hardware.

Usar geradores aleatórios explícitos e independentes por execução/componente. O mesmo índice de semente permite pareamento estatístico, mas não implica que duas implementações consumam a mesma sequência de números aleatórios.

A ordem de execução das configurações deve ser alternada ou aleatorizada para reduzir viés por aquecimento, carga e variação temporal da máquina. Fazer aquecimento controlado quando necessário e documentar o ambiente.

## 7. Métricas e análise

### Métricas principais

- Total Tardiness real (menor é melhor);
- tempo de parede;
- avaliações reais da função objetivo;
- consultas ao Surrogate;
- tempo de treinamento e custo amortizado;
- taxa de sucesso/falha e completude das execuções.

### Métricas complementares

- melhor, média, mediana, desvio padrão e intervalo de confiança por instância/configuração;
- curva de convergência por número de avaliações, e não apenas por iteração;
- diversidade da população e estagnação para Fuzzy;
- MAE, RMSE e R² do Surrogate em teste por permutação;
- distância relativa ao Lower Bound, quando o bound for válido e não negativo.

O GAP será descrito como distância relativa ao Lower Bound, não como distância ao ótimo. Documentar a derivação e as hipóteses do bound antes de usá-lo como métrica conclusiva. Não extrapolar resultados de Small para Large.

### Estatística

- Preservar o pareamento por instância e índice de semente.
- Apresentar resultados separados para Small e Large.
- Não tratar as 600 execuções Small como 600 instâncias independentes.
- Apresentar diferenças pareadas por instância, tamanho de efeito e intervalos de confiança.
- Para inferência agregada, usar instância como unidade de agrupamento; considerar bootstrap hierárquico (instâncias e sementes) para intervalos. Com apenas três instâncias Large, enfatizar descrição e incerteza, evitando conclusões fortes de significância.
- Quando houver testes múltiplos, corrigir p-values (Holm) e declarar hipóteses, direção e nível de significância antes de analisar os resultados.
- Reportar empates e diferenças nulas, além de vitórias/derrotas.

## 8. Integridade dos resultados históricos

- Preservar arquivos CSV, XLSX, PDFs, notebooks e scripts originais.
- Não misturar protocolos: benchmark de 200 iterações/23 instâncias, comparação exploratória de 100 iterações/uma instância e demais experimentos devem ser identificados separadamente.
- Não corrigir resultados históricos silenciosamente. Se uma contagem ou métrica estiver incorreta, registrar a divergência e gerar novos resultados com identificador de protocolo.
- Manter dados brutos imutáveis; tabelas e gráficos devem ser derivados deles por scripts reproduzíveis.

## 9. Critérios para considerar a bateria válida

1. As 23 instâncias foram identificadas e validadas; nenhuma execução usa fallback silencioso para instância sintética.
2. Cada configuração planejada tem 30 execuções por instância, ou falhas explicitamente registradas.
3. Os contadores reais correspondem ao número efetivo de chamadas e respeitam o orçamento.
4. O Surrogate é testado em grupos de permutações não vistos e sua solução final é reavaliada no motor real.
5. Tempos de treinamento e execução não são misturados nem omitidos.
6. Resultados podem ser reproduzidos a partir da configuração, sementes, dados e ambiente registrados.
7. Análises Small e Large são apresentadas separadamente, com limitações estatísticas explícitas.

## 10. Decisões ainda sujeitas ao piloto

- Se 500 amostras LHS são suficientes para cada dimensão ou se o número deve variar por porte.
- Arquitetura e hiperparâmetros finais da MLP.
- Se o espaço de permutações de alguma instância permite enumeração exata para treino/teste.
- Viabilidade de tempo/memória da bateria completa no ambiente disponível.

Essas decisões devem ser congeladas antes da execução integral e registradas na versão final do protocolo.
