# Semana 3 — Sintonia de hiperparâmetros com Optuna

## Escopo e compatibilidade

Esta reconstrução aplica Optuna à mesma formulação da Semana 2: PFSP de uma fábrica, sem datas de entrega, com minimização do makespan, usando ta001 e ta011.

O experimento histórico de Optuna pertence a outro problema: PFS com datas de entrega e minimização de tardiness. Seus parâmetros e resultados são preservados como histórico, mas não são comparáveis à nova baseline Taillard.

## Baseline e orçamento

A baseline congelada é week2_baseline_v1: 30 lobos, 500 iterações, schedule linear de a=2 a a=0, seeds 0–29 e 15.030 avaliações por execução.

O orçamento por execução da sintonia e da avaliação final também será exatamente 15.030 avaliações. A população é escolhida entre divisores inteiros desse orçamento:

| Lobos | Iterações derivadas | Avaliações |
|---:|---:|---:|
| 9 | 1.669 | 15.030 |
| 10 | 1.502 | 15.030 |
| 15 | 1.001 | 15.030 |
| 18 | 834 | 15.030 |
| 30 | 500 | 15.030 |
| 45 | 333 | 15.030 |

## Espaço de busca

O TPE escolhe:
- n_wolves: 9, 10, 15, 18, 30 ou 45;
- a_start: uniforme em [1,5; 2,5];
- a_end: uniforme em [0; 0,5];
- a_exponent: uniforme em [0,5; 2,0].

O schedule é:

[
a(t)=a_{end}+(a_{start}-a_{end})(1-t/T)^{a_{exponent}}
]

A baseline da Semana 2 é recuperada por a_start=2, a_end=0 e a_exponent=1. Os parâmetros satisfazem a_start > a_end >= 0 e a_exponent > 0.

## Objetivo do Optuna

Cada trial executa as duas instâncias com as mesmas seeds de sintonia (100, 101 e 102). A métrica por instância é a média de best_makespan / published_upper_bound; a função objetivo é a média simples dessas duas métricas, atribuindo o mesmo peso a cada instância.

A normalização evita que a instância com maior escala numérica domine o objetivo. O upper bound publicado é referência de escala, não afirmação de ótimo provado.

Configuração inicial: 30 trials, TPESampler com seed fixa 20261123. O primeiro trial é pré-enfileirado com os parâmetros exatos da baseline da Semana 2; assim, o estudo inclui uma referência explícita e pode selecionar novamente a baseline se as demais configurações não forem melhores nas seeds de sintonia. Isso representa 30 × 2 instâncias × 3 seeds = 180 execuções, ou 2.705.400 avaliações de makespan durante a sintonia. O custo de tuning será reportado separadamente.

## Avaliação final sem reutilizar seeds de sintonia

Depois de congelar o melhor conjunto de parâmetros, executar 30 seeds (0–29) em cada instância. Essas seeds são as mesmas usadas na baseline da Semana 2, permitindo diferenças pareadas por instância e seed. Elas não foram usadas no objetivo do Optuna.

O script de avaliação carrega a configuração congelada, executa exatamente 15.030 avaliações por seed e instância, compara com o CSV original da baseline e registra fitness, diferença pareada, tempo, avaliações e permutação. Também gera histórico de convergência com média e desvio padrão amostral, além de média, mediana, desvio padrão, melhor/pior e contagens de vitórias/empates/derrotas pareadas.

O custo total da sintonia não deve ser omitido ao discutir o benefício operacional do algoritmo tunado.

## Artefatos

O script scripts/tune_week3_optuna.py gera:
- study.db: banco SQLite do estudo;
- trials.csv: histórico tabular das tentativas;
- best_params.json: parâmetros vencedores, ambiente, seeds, hashes, orçamento e custo;
- optimization_history.png: histórico da otimização;
- param_importances.png: importância estimada dos parâmetros.

O script scripts/run_week3_evaluation.py gera:
- final_runs.csv: execuções finais por instância/seed;
- final_convergence.csv: média e desvio por geração;
- evaluation_summary.json: comparação pareada e metadados.

## Limitações

A avaliação em duas instâncias e seeds independentes da sintonia reduz o risco de sobreajuste às execuções aleatórias, mas não demonstra generalização para outras instâncias Taillard. A importância de parâmetros estimada pelo Optuna é uma análise dos trials observados, não evidência causal.

O estudo histórico de PFS/tardiness permanece separado e não deve ser combinado com estes resultados.

## Execução

Instalar dependências:

```powershell
python -m pip install -r requirements.txt
```

Sintonia:

```powershell
python -m scripts.tune_week3_optuna
```

Avaliação final:

```powershell
python -m scripts.run_week3_evaluation
```
