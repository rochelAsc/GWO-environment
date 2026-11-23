# Análise descritiva pareada da bateria GWO PFS histórica

**Data:** 2026-11-23  
**Fonte:** seção `1_Dados_Brutos` de `relatorio_final_gwo.md`.  
**Comparação principal:** Baseline (30 lobos, linear) versus Tunado (55 lobos, configuração histórica rotulada `exponential`).  
**Natureza:** reanálise descritiva dos registros existentes; não é uma nova execução experimental.

## 1. Pareamento e cobertura

O pareamento foi feito por `(instância, seed)`, usando apenas pares presentes nas duas configurações.

| Porte | Instâncias | Pares | Cobertura |
|---|---:|---:|---|
| Small | 20 | 600 | 30 seeds por instância |
| Large | 3 | 30 | 10 seeds por instância |
| **Total** | **23** | **630** | — |

A análise Large é descritiva: três instâncias e dez sementes por instância não sustentam generalização ampla.

## 2. Baseline versus Tunado — Small

Para cada par, diferença = fitness(Tunado) − fitness(Baseline); valor negativo favorece Tunado.

- 20 pares melhores para Tunado.
- 576 empates.
- 4 pares piores para Tunado.
- 9 das 20 instâncias têm média menor com Tunado.
- 10 instâncias têm médias iguais.
- 1 instância tem média maior com Tunado.
- Diferença média dos 600 pares: **−0,95** unidades de tardiness.

A maioria esmagadora dos pares é empate (96%). O efeito observado em Small é pequeno em relação à escala de tardiness das instâncias e não deve ser descrito como uma melhoria geral robusta.

## 3. Baseline versus Tunado — Large

| Instância | Jobs | Pares | Tunado melhor | Empate | Tunado pior | Diferença média (Tunado − Baseline) |
|---|---:|---:|---:|---:|---:|---:|
| Ta031_2.txt | 50 | 10 | 7 | 0 | 3 | −272,4 |
| Ta061_2.txt | 100 | 10 | 8 | 0 | 2 | −2.247,1 |
| Ta111_2.txt | 500 | 10 | 7 | 0 | 3 | −23.530,3 |
| **Total** | — | **30** | **22** | **0** | **8** | — |

O Tunado tem menor tardiness em 22 dos 30 pares disponíveis. O resultado é promissor apenas como observação exploratória: cada instância tem dez sementes e não existem resultados Large para as duas ablações.

## 4. Limite da inferência estatística reportada

A seção `4_Testes_Estatisticos` registra Wilcoxon = 0,0 e p = 0,10880943004054568. Contudo, não informa se o teste foi aplicado aos resultados por semente, às médias por instância ou a outra unidade; tampouco registra o tratamento de empates, zeros e da cobertura desigual Small/Large.

A estatística e o p-value, portanto, **não são reproduzíveis a partir da descrição do relatório**. Não devem ser citados como evidência conclusiva até que o procedimento original seja recuperado ou o teste seja recalculado com método explicitado. Em particular, as 600 execuções Small não são 600 instâncias independentes: a instância é uma unidade de agrupamento.

## 5. Interpretação recomendada

Uma formulação defensável é:

> Na bateria histórica PFS, a configuração Tunada (55 lobos, schedule registrado como exponential) apresentou resultados iguais ao Baseline na maioria das execuções Small, com pequenas diferenças em poucos pares. Nas três instâncias Large disponíveis, obteve menor tardiness em 22 de 30 pares. Como a cobertura Large é limitada e o teste estatístico registrado não possui procedimento reproduzível no relatório, os resultados são exploratórios e não permitem afirmar superioridade estatística ou generalização.

Não chamar `exponential` de exponencial matemático: a auditoria do código identificou que a fórmula histórica é quadrática, mas os dados brutos devem preservar o rótulo original com essa ressalva.
