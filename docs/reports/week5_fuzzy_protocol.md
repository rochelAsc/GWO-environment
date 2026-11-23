# Semana 5 — Protocolo de reconstrução do GWO com controlador Fuzzy

## 0. Versão corrigida do solver (v2)

O piloto Fuzzy v1 foi executado com a população congelada entre gerações, pois `new_positions` não era atribuída a `positions`. A diversidade observada no traço permaneceu constante; portanto, o controlador não recebeu uma medida atualizada da população. O piloto v1 é preservado como histórico, mas não valida um GWO iterativo nem um controlador adaptativo baseado em diversidade. A versão v2 corrige a evolução da população em ambos os solvers e deve comparar apenas com `results/week2_baseline_v2/runs.csv` e `results/week3_optuna_v2/final_runs.csv`. A nova saída padrão é `results/week5_fuzzy_v2/`.

## 1. Escopo e decisão de reconstrução

A reconstrução usa o mesmo problema das Semanas 2–4: PFSP de uma fábrica, instâncias Taillard `ta001` e `ta011`, random keys e minimização de makespan. Isso viabiliza uma comparação pareada com os resultados congelados das Semanas 2 e 3.

O CSV histórico `data/experimental/historico_fuzzy (1).csv` é preservado. Ele contém 100 linhas com iteração, fator de ajuste e valor de `a`, mas não registra entradas Fuzzy, funções de pertinência, regras, método de inferência, defuzzificação, instância, seed ou ligação com uma execução GWO. Portanto, não é possível recuperar com segurança o controlador original. A implementação descrita aqui é uma **reconstrução nova e versionada**, não uma reprodução alegada do controlador histórico.

## 2. Protocolo de comparação

- Instâncias: `ta001` (20 jobs, 5 máquinas) e `ta011` (20 jobs, 10 máquinas).
- População: 30 lobos.
- Orçamento: 15.030 avaliações reais por execução.
- Iterações: 500, pois 30 × (500 + 1) = 15.030.
- Seeds: 0–29.
- Comparadores: baseline corrigida v2 da Semana 2 e GWO tunado v2 da Semana 3.
- Mesmas instâncias, índices de seed e orçamento em todas as versões.
- Fitness sempre calculado pelo avaliador exato de makespan; o Fuzzy não substitui a função objetivo.

O Fuzzy usa a mesma atualização síncrona alpha/beta/delta e elitismo de líderes do solver PFSP da Semana 2. A única alteração algorítmica é o controle adaptativo do parâmetro de exploração `a`.

## 3. Entradas Fuzzy

### Diversidade

Média das distâncias L1 absolutas entre todos os pares de lobos, calculada nos vetores de random keys:

`D = mean(|x_i - x_j|), i < j`

Como as chaves pertencem a [0,1], a medida também pertence a [0,1]. Valores baixos indicam concentração da população; valores altos indicam dispersão.

### Estagnação

Número de gerações consecutivas sem melhoria do melhor fitness global, dividido por uma janela fixa de 20 gerações e limitado a [0,1]:

`S = min(g gerações sem melhoria / 20, 1)`

O contador é zerado quando o melhor fitness global melhora. A janela é um parâmetro explícito do protocolo, não ajustado usando os resultados de teste.

## 4. Funções de pertinência

Para ambas as entradas, os conjuntos linguísticos são:

- Baixo: trapezoidal (0, 0, 0,25, 0,50);
- Médio: triangular (0,20, 0,50, 0,80);
- Alto: trapezoidal (0,50, 0,75, 1,00, 1,00).

A saída é um multiplicador de exploração no intervalo [0,5; 1,5]:

- Baixo: trapezoidal (0,50, 0,50, 0,68, 0,95);
- Médio: triangular (0,75, 1,00, 1,25);
- Alto: trapezoidal (1,05, 1,32, 1,50, 1,50).

## 5. Base de regras Mamdani

Linhas representam diversidade (baixa, média, alta); colunas representam estagnação (baixa, média, alta). Cada célula é a saída:

| Diversidade \ Estagnação | Baixa | Média | Alta |
|---|---|---|---|
| Baixa | Média | Alta | Alta |
| Média | Baixa | Média | Alta |
| Alta | Baixa | Média | Alta |

Interpretação: estagnação crescente aumenta a exploração; com população pouco diversa, o controlador também favorece exploração. Diversidade alta sem estagnação permite reduzir a amplitude exploratória.

Inferência: Mamdani, operador mínimo para AND, máximo para agregação e implicação por truncamento. Defuzzificação: centroide numérico em universo de 501 pontos uniformes entre 0,5 e 1,5.

## 6. Acoplamento ao GWO

A agenda de referência é linear:

`a_base(t) = 2(1 - t/T)`

A saída Fuzzy multiplica o valor de referência:

`a(t) = clip(a_base(t) × fator_Fuzzy, 0, 2)`

Assim, o controlador modifica a amplitude de exploração sem trocar representação, decoder, atualização síncrona, líderes ou avaliador. No fim da agenda, `a_base` aproxima-se de zero e a influência do multiplicador também diminui.

## 7. Métricas e análise

Por instância e seed, registrar makespan final, tempo de parede, avaliações, permutação, convergência e traço temporal de diversidade, estagnação, fator Fuzzy e `a`.

Comparar pareadamente o Fuzzy com baseline e tunado por instância, usando os mesmos seeds. Reportar média, mediana, desvio padrão amostral, vitórias/empates/derrotas, diferença pareada e Wilcoxon bilateral exploratório. Os p-values devem ser interpretados com cautela e corrigidos por multiplicidade se forem usados para afirmações inferenciais. Não agregar as duas instâncias como se fossem uma amostra homogênea.

## 8. Limitações e interpretação

- O controlador é uma reconstrução transparente, não o controlador original do CSV.
- A diversidade é medida no espaço contínuo de random keys; ela não equivale exatamente à diversidade de permutações.
- A janela de estagnação e as funções de pertinência são escolhas de projeto fixadas antes da bateria.
- A comparação cobre duas instâncias Taillard e não sustenta generalização para todo PFSP.
- Não concluir superioridade apenas por menor média ou p-value isolado; discutir tamanho e consistência das diferenças.
- O CSV histórico não deve ser combinado com os resultados desta versão.

## 9. Execução

Piloto técnico:

```bash
python -m scripts.run_week5_fuzzy --seeds 0 1 2 --output results/week5_fuzzy_pilot_v2
```

Bateria completa:

```bash
python -m scripts.run_week5_fuzzy
```

Arquivos: `fuzzy_runs.csv`, `fuzzy_convergence.csv`, `fuzzy_trace.csv` e `summary.json`.
