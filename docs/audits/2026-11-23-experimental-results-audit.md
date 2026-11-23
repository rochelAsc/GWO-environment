# Auditoria de consistência dos resultados experimentais

**Data:** 2026-11-23  
**Escopo:** relatórios Markdown, CSVs históricos, protocolo experimental e resultados do piloto versionados na branch `main`.  
**Princípio:** auditoria aditiva. Nenhum dado bruto ou relatório histórico foi sobrescrito.

## 1. Conclusão executiva

O repositório contém **três conjuntos experimentais distintos** que não devem ser fundidos em uma única tabela:

1. Experimentos exploratórios PFS das etapas Optuna, Surrogate e Fuzzy, concentrados em `I_3_4_2_3.txt`.
2. Bateria GWO PFS com quatro configurações (Baseline, Tunado e duas ablações), descrita em `relatorio_final_gwo.md` e duplicada em `resultados_completos_gwo.md`.
3. Piloto novo DPFSP-DD, em `results/gwo_pilot/`, com motor, representação, instâncias e protocolo próprios.

O piloto DPFSP-DD não valida nem substitui os resultados PFS históricos. Os dados históricos também não demonstram a conclusão da bateria de seis configurações planejada em `docs/experimental_protocol.md`.

## 2. Bateria GWO PFS: cobertura incompleta em relação ao plano

O protocolo planeja 23 instâncias (20 Small e 3 Large), 30 sementes por instância e seis configurações, totalizando 4.140 execuções.

Os dados brutos em `relatorio_final_gwo.md` e `resultados_completos_gwo.md` contêm 2.460 registros, distribuídos assim:

| Configuração | Small | Large | Total |
|---|---:|---:|---:|
| Baseline (30, linear) | 20 × 30 | 3 × 10 | 630 |
| Tunado (55, exponential) | 20 × 30 | 3 × 10 | 630 |
| Ablação (30, exponential) | 20 × 30 | ausente | 600 |
| Ablação (55, linear) | 20 × 30 | ausente | 600 |
| **Total** | **2.400** | **60** | **2.460** |

Consequências:

- Baseline e Tunado têm apenas 10 sementes (0–9) nas três instâncias Large, não 30.
- As duas ablações estão ausentes das três instâncias Large.
- As configurações GWO-Fuzzy e GWO-Surrogate, previstas no protocolo, não aparecem nessa bateria.
- Portanto, 2.460 registros não equivalem à bateria completa de 4.140 execuções. A diferença de 1.680 registros inclui as duas configurações ainda não presentes e as repetições Large ausentes/incompletas.

O resumo `2_Resumo_Small` apresenta médias calculadas apenas sobre as 20 instâncias Small. Isso é coerente com o rótulo da seção, mas não deve ser descrito como resumo geral Small+Large.

## 3. Orçamento de avaliações: histórico versus protocolo novo

Os registros da bateria PFS mostram:

- Baseline e ablação com 30 lobos: 6.030 avaliações por execução.
- Tunado e ablação com 55 lobos: 11.055 avaliações por execução.

Esses valores são compatíveis com o contador histórico caracterizado como população × (iterações + 1), incluindo a avaliação da população inicial, para 200 iterações. Eles **não** correspondem ao orçamento novo de 5.940 avaliações definido em `docs/experimental_protocol.md`.

Não se deve rotular os resultados históricos como se tivessem sido executados sob o orçamento novo. A comparação entre populações também tem custos diferentes no histórico: 6.030 versus 11.055 avaliações.

## 4. Experimento exploratório das quatro versões: divergências documentais

Os arquivos `data/experimental/dados_brutos_4_versoes (1).csv`, `historico_fuzzy (1).csv`, `resultados_surrogate (1).csv`, `resumo_small.csv` e `tabela_4_versoes (1).csv` descrevem um experimento separado, em uma única instância PFS e 30 sementes por versão.

Divergências verificadas:

1. **Fuzzy — orçamento:** o CSV bruto registra 3.000 avaliações por execução; o relatório parcial afirma 5.500 avaliações para Fuzzy. A planilha-resumo também registra 3.000. Não há evidência suficiente para decidir qual número representa a execução efetiva; preservar o registro bruto e corrigir a narrativa somente após recuperar o log/código exato da execução.
2. **Surrogate — fitness:** a média reportada de 268,492 é baseada em valores previstos pelo modelo, não em fitness real. O registro de validação informa fitness real 306 e previsão 265,955. Assim, 268,492 não pode ser comparado como desempenho real às médias 306 das outras versões.
3. **Surrogate — tempo:** o CSV registra 1,317 s para o caminho Surrogate e 0,218 s para a avaliação real. A razão registrada, 0,166×, indica que o Surrogate foi mais lento nessa instância pequena, não mais rápido.
4. **Alegação de ganho em Large:** o relatório parcial menciona aceleração de 1,90× em instâncias Large, mas o CSV de métricas disponibilizado contém somente a instância Small. Não há linha bruta que sustente essa afirmação no conjunto versionado.
5. **Validação da MLP:** MSE, RMSE e R² estão registrados, mas os artefatos tabulares não demonstram separação de treino/teste por permutação decodificada nem generalização para permutações inéditas.

O relatório parcial reconhece o “falso ótimo” previsto pelo Surrogate em sua discussão, mas a conclusão de que o método é uma alternativa viável para reduzir custo em instâncias complexas é mais forte do que a evidência tabular disponível.

## 5. Estatística e GAP

- `relatorio_final_gwo.md` registra um único resultado Wilcoxon (estatística 0,0; p = 0,1088), mas não documenta ali a unidade de pareamento, o tratamento das instâncias com apenas 10 sementes, a direção da hipótese nem o procedimento de agregação entre instâncias.
- O relatório Optuna anterior afirma significância com p < 0,05. Esse resultado pertence a um experimento exploratório anterior e não deve ser apresentado como se fosse o mesmo teste da bateria posterior. Os dois valores não são diretamente comparáveis sem identificar amostras, pareamento e hipótese de cada análise.
- A tabela de GAP usa um Lower Bound atribuído a McMahon–Florian–Potts. A validade matemática e as hipóteses desse bound para cada formulação/instância não foram verificadas nesta auditoria. Até essa validação, GAP não deve ser descrito como distância ao ótimo; é, no máximo, uma distância relativa ao bound reportado.

## 6. Relação com o piloto DPFSP-DD

`results/gwo_pilot/pilot_runs.csv` registra 36 execuções: três instâncias, quatro configurações, três sementes e 990 avaliações por execução. É um piloto técnico DPFSP-DD, não uma continuação numérica da bateria PFS.

Os resultados do piloto devem permanecer em seção própria, com a identificação explícita de DPFSP-DD. Não agregar fitness, tempos, contagens ou estatísticas entre PFS e DPFSP-DD.

## 7. Recomendações para a entrega

1. Apresentar a bateria PFS como **execução parcial/incompleta**, especificando a cobertura por porte e configuração.
2. Não afirmar que foram concluídas 4.140 execuções nem que as seis configurações foram avaliadas em todas as instâncias.
3. Separar os resultados exploratórios de uma instância dos resultados da bateria PFS e do piloto DPFSP-DD.
4. Para Surrogate, reportar separadamente fitness previsto e fitness real reavaliado; não usar a média prevista como resultado competitivo.
5. Remover ou qualificar a alegação de ganho de 1,90× em Large até que os dados brutos correspondentes sejam recuperados.
6. Resolver a divergência de avaliações Fuzzy consultando logs/código da execução original; não alterar o CSV histórico por inferência.
7. Recalcular a análise estatística a partir dos dados brutos, com pareamento por instância/semente e instâncias como unidades de agrupamento. Reportar Small e Large separadamente.
8. Validar o lower bound antes de interpretar GAP.
9. Manter os resultados históricos imutáveis; quaisquer execuções novas devem receber identificador de protocolo, orçamento e família de problema explícitos.

## 8. Arquivos examinados

- `docs/experimental_protocol.md`
- `docs/decisions/2026-11-22-scope-update.md`
- `relatorio_final_gwo.md`
- `resultados_completos_gwo.md`
- `Master_Relatorio_Semanas_3_4_5.md`
- `RELATORIO_SIS_INTELIGENTE_ROCHEL_2023090100.md`
- `Relatório - Rochel Andrey dos Santos Costa.md`
- `data/experimental/*.csv`
- `results/gwo_pilot/pilot_runs.csv`
- `results/gwo_pilot/pilot_summary.json`

