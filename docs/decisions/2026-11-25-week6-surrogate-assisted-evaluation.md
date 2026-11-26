# Decisão metodológica — benchmarking da Semana 6 e Surrogate assistido

- **Data:** 2026-11-25
- **Status:** aceita pelo autor; implementação pendente
- **Escopo:** PFSP clássico de uma fábrica, instâncias Taillard `ta001` e `ta011`
- **Protocolo associado:** [Semana 6 — Benchmark comparativo](../reports/week6_benchmark_protocol.md)

## Contexto

As Semanas 2–5 reconstruíram quatro variantes do GWO no mesmo PFSP/Taillard: baseline, parâmetros tunados pelo Optuna, Surrogate e controlador Fuzzy. As três primeiras variantes com avaliador exato usam 15.030 avaliações por execução; o modelo Surrogate da Semana 4 é um estimador aproximado e não pode ser tratado como função objetivo verdadeira.

O benchmark precisa comparar qualidade de solução, custo de avaliação e custo de preparação sem reportar previsões como makespan real. Os resultados da Semana 4 também mostram que a inferência individual é mais lenta que a avaliação exata, embora a inferência em lote seja mais rápida no microbenchmark.

## Decisão

Implementar uma variante GWO assistida por Surrogate com as seguintes regras:

1. Usar o modelo MLP treinado na Semana 4 para a instância correspondente, sem retreinar ou ajustar hiperparâmetros com os resultados da Semana 6.
2. Inicializar 30 lobos e avaliar a população inicial pelo makespan exato.
3. Em cada uma das 500 gerações, gerar 30 posições e prever seus makespans em lote.
4. Selecionar os três candidatos com menor makespan previsto e reavaliar cada um pelo avaliador exato.
5. Atualizar o arquivo de líderes exclusivamente com soluções que tenham makespan exato conhecido. Previsões não podem entrar no arquivo de líderes, na curva de convergência ou no resultado final.
6. Retornar a melhor solução do arquivo exato. Registrar separadamente previsões, avaliações exatas, tempo de inferência e tempo de avaliação.
7. Contabilizar cada uma das três reavaliações por geração como uma chamada exata, mesmo que duas posições decodifiquem para a mesma permutação. Isso mantém o orçamento operacional fixo e evita um contador dependente de duplicatas; duplicatas devem ser registradas como diagnóstico.
8. Não atualizar o modelo durante a busca.

### Orçamento por execução Surrogate

- Avaliações exatas iniciais: 30.
- Avaliações exatas de candidatos: 3 × 500 = 1.500.
- Total de avaliações exatas: 1.530.
- Previsões: 30 × 500 = 15.000.
- Gerações: 500.

O orçamento é diferente das outras variantes e não deve ser descrito como igualdade de avaliações. O estudo reportará a economia de chamadas exatas e o custo de inferência, sem alegar equivalência de orçamento computacional.

## Bateria comparativa

- Variantes: Baseline, Optuna, Surrogate assistido e Fuzzy.
- Instâncias: `ta001` e `ta011`.
- Seeds: 0–29, pareadas por instância.
- População/iterações: Baseline 30/500; Optuna 45/333; Surrogate 30/500; Fuzzy 30/500.
- As variantes exatas mantêm 15.030 avaliações por execução.
- A bateria terá 240 execuções: quatro variantes × duas instâncias × 30 seeds.
- Novos resultados serão gravados em `results/week6_benchmark_v1/`; nenhuma pasta anterior será sobrescrita.

## Custos do Surrogate

O custo será dividido em:

1. **Preparação do modelo:** 2.000 rótulos exatos por instância, geração do dataset e treinamento MLP, conforme os artefatos/metadados da Semana 4.
2. **Busca:** 1.530 avaliações exatas e 15.000 previsões por execução.
3. **Custo amortizado:** apresentar o custo de preparação separado e também distribuído por quantidade hipotética/real de execuções. Não somar tempo de preparação ao tempo de busca sem identificar explicitamente essa soma.

Os modelos serializados e seus hashes serão registrados nos metadados da Semana 6. O teste de qualidade do modelo da Semana 4 continua sendo uma avaliação preditiva separada; o desempenho do GWO assistido será medido pelo makespan exato.

## Análise estatística

- Analisar cada instância separadamente.
- Usar seed como bloco pareado entre as quatro variantes.
- Aplicar Friedman como teste global por instância.
- Para as seis comparações pareadas entre variantes, usar Wilcoxon bilateral e correção de Holm separadamente por instância.
- Reportar valores p brutos e ajustados, diferenças pareadas, média/mediana, desvio padrão e contagens de vitórias/empates/derrotas.
- Tratar testes como evidência limitada às duas instâncias; não generalizar para todo PFSP.

## Alternativas consideradas

### Usar apenas previsões do Surrogate como fitness

Rejeitada porque permite que erros preditivos determinem líderes e resultados finais, podendo produzir falsos ótimos e tornar as métricas incomparáveis com as variantes exatas.

### Reavaliar apenas o melhor candidato previsto de cada geração

Rejeitada para esta versão porque oferece menor proteção contra erro de ranking e limita a atualização do arquivo exato a um único candidato por geração.

### Reavaliar todos os 30 candidatos

Rejeitada porque elimina a economia de avaliações exatas que justifica o Surrogate.

### Reavaliar os três melhores candidatos previstos

Aceita como compromisso explícito entre economia de avaliações exatas e proteção contra erro de previsão. A escolha de três é fixada antes da bateria e não será otimizada usando os resultados de teste.

## Consequências e limitações

- A variante Surrogate terá menos avaliações exatas, mas também 15.000 previsões por execução; as métricas devem mostrar os dois contadores.
- O ranking previsto pode falhar, e a reavaliação dos três melhores não garante que o melhor candidato real da geração seja selecionado.
- A comparação mede uma política de busca assistida, não a qualidade isolada do regressor.
- O custo de preparação da Semana 4 deve ser contabilizado, mesmo que o modelo já esteja treinado antes da bateria.
- A conclusão deve distinguir qualidade final, economia de avaliações exatas e tempo total.
- O protocolo cobre duas instâncias Taillard e não prova generalização para outras instâncias.

## Documentos relacionados

- [Atualização de escopo e separação de famílias de problemas](2026-11-22-scope-update.md)
- [Protocolo PFSP/Taillard da Semana 2](../reports/week2_reconstruction_protocol.md)
- [Protocolo Optuna da Semana 3](../reports/week3_optuna_protocol.md)
- [Protocolo Surrogate da Semana 4](../reports/week4_surrogate_protocol.md)
- [Protocolo Fuzzy da Semana 5](../reports/week5_fuzzy_protocol.md)
- [Correção do congelamento da população](../audits/2026-11-23-gwo-population-freeze-correction.md)
