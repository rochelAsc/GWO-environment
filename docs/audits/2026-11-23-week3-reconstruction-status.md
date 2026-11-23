# Semana 3 — Status da reconstrução

**Status:** experimentos concluídos; auditoria dos artefatos concluída; validação CI da correção pendente.

## Escopo e decisões metodológicas

A reconstrução da Semana 3 foi feita sobre o mesmo problema da Semana 2 para permitir comparação controlada: PFSP de Taillard, minimização do makespan. Ela não deve ser confundida com o experimento histórico de Optuna sobre PFS com due dates e tardiness.

- Instâncias: `ta001` (20 jobs, 5 máquinas) e `ta011` (20 jobs, 10 máquinas).
- Baseline: `results/week2_baseline_v1/runs.csv`, 30 lobos, 500 iterações, schedule linear.
- Orçamento fixo: 15.030 avaliações por execução.
- TPE: 30 trials, sampler seed `20261123`; trial 0 pré-enfileirado com os parâmetros da baseline.
- Seeds de sintonia: 100, 101 e 102.
- Seeds reservadas para avaliação final: 0–29, pareadas com a baseline e não utilizadas na sintonia.
- Espaço de busca: população {9, 10, 15, 18, 30, 45}; `a_start` [1,5; 2,5]; `a_end` [0; 0,5]; expoente [0,5; 2,0].
- Função objetivo: média simples, entre as duas instâncias, da média de `best_makespan / published_upper_bound`. Menor é melhor.

A curva usada foi parametrizada por
`a(t) = a_end + (a_start - a_end) * (1 - t/T)^a_exponent`.
O número de iterações foi derivado da população para manter exatamente o orçamento de avaliações.

## Implementação e artefatos

- `scripts/gwo_pfs.py`: GWO PFSP com schedule configurável e defaults compatíveis com a Semana 2.
- `scripts/tune_week3_optuna.py`: sintonia TPE, estudo SQLite, CSV de trials e gráficos.
- `scripts/run_week3_evaluation.py`: avaliação dos parâmetros congelados e comparação pareada.
- `tests/test_week3_optuna.py`: testes do schedule, orçamento e reprodutibilidade.
- `docs/reports/week3_optuna_protocol.md`: protocolo experimental.
- `results/week3_optuna_v1/`: estudo, parâmetros selecionados, gráficos, CSVs e metadados.
- `results/week2_baseline_v1/`: baseline de referência preservada.

## Resultado da sintonia

Foram concluídos 30 trials. A melhor configuração foi:

| Parâmetro | Valor |
|---|---:|
| Número de lobos | 30 |
| `a_start` | 1,5240026881 |
| `a_end` | 0,0951336645 |
| Expoente | 1,7533663556 |
| Iterações derivadas | 500 |
| Valor objetivo | 1,0070293937 |

A melhor configuração obteve score normalizado 0,9898278560 em `ta001` e 1,0242309313 em `ta011`. Esses valores são resultados do conjunto de treinamento, não evidência independente de generalização.

O custo total registrado foi de 2.705.400 avaliações e 209,08 segundos. O custo da sintonia deve ser reportado separadamente do custo da avaliação final.

## Avaliação final pareada

A avaliação utilizou as 30 seeds reservadas (0–29), com 15.030 avaliações por execução. Foram conferidos 60 registros finais e 60 registros correspondentes da baseline; todas as seeds estão presentes em ambas as instâncias e os orçamentos são iguais. O arquivo de convergência contém 1.002 linhas: 501 gerações agregadas por instância, incluindo a população inicial.

| Instância | Baseline (média) | Tunado (média) | Diferença tunado − baseline | Tunado melhor / igual / pior |
|---|---:|---:|---:|---:|
| ta001 | 1265,9667 | 1266,4333 | +0,4667 | 2 / 25 / 3 |
| ta011 | 1628,5333 | 1627,9000 | −0,6333 | 13 / 7 / 10 |

O resultado é misto: a configuração tunada foi ligeiramente pior em `ta001` e ligeiramente melhor em `ta011`. As diferenças médias são pequenas e não sustentam a afirmação de melhoria geral do GWO. Não se declara significância estatística nesta auditoria. O upper bound publicado é uma referência de benchmark; a distância a ele não deve ser descrita como gap para um ótimo provado.

## Integridade e reprodutibilidade

- Seeds de treinamento e avaliação são disjuntas.
- O conjunto final usa as mesmas instâncias, seeds e orçamento da baseline.
- Os metadados registram ambiente, versões e hashes das instâncias.
- Hash SHA-256 de `ta001`: `fa586022d3a4a759f2d26c4b61c5267e71c00e4016f3307bbe706982df2b42c3`.
- Hash SHA-256 de `ta011`: `16b1e1b2bf1464e5af0f28b7c1aaeed4d65ff00bce51d10f583dfd3fa12a02b6`.
- Ambiente experimental registrado: Python 3.14.6, Windows 11, NumPy 2.5.1 e Optuna 4.9.0.

## Correção da CI

O workflow anterior executava `compileall` indiscriminadamente em `scripts/`. Isso incluía `scripts/sistemas_inteligentes_entregavel.py`, um export destinado ao Google Colab/IPython que contém comandos mágicos como `!pip install` e, portanto, não é um módulo Python compilável diretamente.

A etapa foi ajustada para compilar todos os arquivos `.py` de `scripts/` e `tests/`, exceto esse export específico. A suíte `pytest` continua sendo executada integralmente. A correção evita tratar sintaxe própria do notebook como erro de módulo Python, sem excluir os módulos convencionais da verificação.

**Atenção:** a alteração do workflow foi publicada, mas a aprovação da CI só poderá ser declarada depois que a nova execução do GitHub Actions terminar com sucesso.

## Conclusão

A reconstrução experimental da Semana 3 está concluída e seus resultados foram preservados. A sintonia não demonstrou superioridade consistente sobre a baseline nas duas instâncias avaliadas. A limitação principal é a cobertura de apenas duas instâncias Taillard; não se deve generalizar o resultado para toda a família.

A pendência operacional é confirmar a execução bem-sucedida da CI após a correção do passo de compilação. Esta etapa não altera os resultados experimentais nem substitui a baseline da Semana 2.
