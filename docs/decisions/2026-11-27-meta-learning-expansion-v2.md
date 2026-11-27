# Decisão: expandir a meta-base para Meta-Learning por instância

**Data:** 2026-11-27  
**Status:** aprovada  
**Gate:** reprodução do piloto concluída; autorização para preparar a Fase 5.

## 1. Decisão

Dar continuidade à extensão de Meta-Learning e preparar uma nova versão da meta-base, denominada **metabasis_v2**, com expansão progressiva:

- **Checkpoint 1:** 60 instâncias (5 por grupo Taillard).
- **Alvo completo:** 120 instâncias (10 por grupo), condicionado à revisão de custo, integridade e cobertura após o checkpoint de 60.

A unidade independente continua sendo a instância PFSP. Seeds, variantes, gerações e candidatos não aumentam o número de unidades independentes.

Esta decisão autorizou a preparação e a coleta progressiva. **Atualização:** inventário 120, split, scripts v2 e coleta/agregação development do checkpoint 60 já foram realizados (ver relatório do checkpoint 60). A decisão formal de avançar a 120 ou encerrar em 60 permanece pendente; holdout continua selado.

## 2. Evidência que motiva a expansão

O piloto metabasis_pilot_v1 permanece congelado e reproduzível:

- 36 instâncias × 4 variantes × 3 seeds = 432 execuções;
- 35 preditores taillard_pfsp_features_v1, derivados apenas da matriz de processamento;
- hashes do freeze 4/4 corretos;
- reprodução do LOO bit-idêntica aos artefatos publicados;
- 29 testes aprovados na rodada de reprodução.

O LOO não demonstrou ganho operacional útil do RF sobre o seletor sempre Fuzzy: regret médio 0,0029053 contra 0,0029187; placar pareado de 5 vitórias, 3 derrotas e 28 empates. O classificador teve regret médio 0,0052324. Portanto, não se declara superioridade do Meta-Learning. A expansão busca aumentar a quantidade de instâncias independentes e permitir uma avaliação externa que o piloto não comporta.

Referências:
- [Relatório LOO exploratório](../reports/2026-11-27-meta-learning-selector-loo-exploratory.md)
- [Relatório de reprodução A–D](../reports/2026-11-27-meta-learning-reproduction-ad.md)
- [Freeze do piloto](2026-11-27-metabasis-pilot-v1-freeze.md)

## 3. Preservação de versões e proveniência

1. experiments/meta_learning/data/metabasis_pilot_v1/ é imutável. Não regenerar, editar ou reutilizar seu diretório de saída.
2. A expansão será gravada em diretórios próprios:
   - dados brutos: results/meta_learning_metabasis_v2/;
   - freeze: experiments/meta_learning/data/metabasis_v2/;
   - split pré-registrado: experiments/meta_learning/data/metabasis_v2/split_manifest.csv.
3. Cada instância deve ter identificador, grupo/dimensão, origem, referência de origem, SHA-256, upper/lower bounds publicados quando disponíveis e status de elegibilidade.
4. Cada execução deve preservar instância, variante, seed, makespan, runtime, contadores, hashes da instância/modelo, commit, configuração e ambiente.
5. Resultados históricos só podem ser incorporados se hash, algoritmo, configuração, seed, métrica e contadores forem compatíveis. Caso contrário, ficam separados e não entram silenciosamente na meta-base.

## 4. Desenho amostral e holdout pré-reservado

O benchmark-alvo é organizado em 12 grupos de dimensão, com 10 instâncias por grupo (120 no total). O inventário completo deve ser verificado contra a fonte antes de assumir essa cobertura.

Os 36 casos do piloto (3 por grupo) já foram usados em desenvolvimento, LOO, inspeção e decisões metodológicas. Eles pertencem exclusivamente ao conjunto de desenvolvimento; **nenhum deles pode ser promovido a holdout confirmatório**.

Antes de observar qualquer novo resultado GWO:

1. inventariar e validar os 120 arquivos, dimensões, proveniência e SHA-256;
2. em cada grupo, separar as 3 instâncias do piloto e as 7 restantes;
3. selecionar, sem olhar resultados/targets, **5 das 7 restantes para desenvolvimento e 2 para holdout**, com split_seed=20261127 e algoritmo registrado; sortear também a ordem em cada partição para marcar 1 desenvolvimento + 1 holdout como stage=60 e as outras 4 de desenvolvimento + 1 holdout como stage=120;
4. congelar o manifesto completo de split e seu hash antes de executar novas variantes.

A composição progressiva:

| Estágio | Desenvolvimento | Holdout selado | Total |
|---|---:|---:|---:|
| Checkpoint de 60 | 48 (4 por grupo) | 12 (1 por grupo) | 60 |
| Alvo de 120 | 96 (8 por grupo) | 24 (2 por grupo) | 120 |

No checkpoint de 60, por grupo: as 3 instâncias do piloto + 1 nova instância de desenvolvimento; 1 nova instância é holdout. Na expansão para 120, entram mais 4 instâncias de desenvolvimento e 1 de holdout por grupo.

A seleção deve ser determinística, estratificada por grupo e independente de makespan, UB/LB, vencedores ou desempenho de qualquer variante. O seed e o algoritmo de split devem ser registrados. O manifesto deve marcar explicitamente development ou holdout.

**Regra de abertura do holdout:**
- Se encerrar em 60, o holdout de 12 instâncias só poderá ser aberto uma vez, após congelar features, pipeline, hiperparâmetros, baselines e critérios de sucesso.
- Se houver intenção de avançar a 120, não abrir nem consultar os targets das 12 instâncias de holdout do checkpoint de 60. Ao completar 120, o holdout final terá 24 instâncias e será aberto uma única vez.
- A avaliação de custo e integridade no checkpoint de 60 não exige abrir o holdout.

## 5. Execução GWO e política de seeds

- Manter as quatro variantes congeladas: baseline, optuna, fuzzy e surrogate.
- Começar com 3 seeds pareadas [0, 1, 2] por instância e variante, preservando a comparabilidade com metabasis_pilot_v1.
- Não aumentar seeds como substituto de instâncias independentes. Uma eventual ampliação para 5 ou mais seeds depende de análise de variância intra-instância e custo, com decisão versionada.
- Não retunar configurações, trocar o modelo MLP da variante Surrogate, alterar features ou mudar o orçamento no meio da coleta.
- Manter explícita a diferença de orçamento: Baseline/Optuna/Fuzzy usam 15.030 avaliações exatas por execução; Surrogate usa 1.530 avaliações exatas + 15.000 previsões, além do custo de preparação/inferência. Não declarar igualdade de orçamento.
- Preservar checkpoints e retomar apenas por chaves ausentes (instância, variante, seed); rejeitar duplicatas e conflitos de configuração.

Contagem esperada com 3 seeds:
- 60 instâncias: 720 execuções no total; 288 novas além do piloto de 36.
- 120 instâncias: 1.440 execuções no total; 1.008 novas além do piloto.

## 6. Custo e checkpoints

A medição anterior estimou aproximadamente 1,06 h para 36 instâncias com 3 seeds e 3,54 h com 10 seeds no hardware local usado no piloto. Extrapolação linear simples sugere cerca de 1,8 h para 60 e 3,5 h para 120 com 3 seeds, mas isso é apenas referência inicial: instâncias maiores podem elevar o tempo, e preparação do Surrogate deve ser contabilizada separadamente.

No checkpoint de 60:
- medir tempo real por grupo, variante e etapa de preparação;
- conferir completude, duplicatas, falhas, hashes e contadores;
- estimar custo real para completar 120;
- decidir avançar, ajustar o plano ou encerrar em 60 sem abrir o holdout caso a intenção seja continuar.

**Atualização 2026-11-27:** a parte de **desenvolvimento** do checkpoint 60 foi concluída (576/576 runs; holdout selado). Custo wall das 12 novas ≈ 0,33 h; extrapolação ≈ 1,3 h para as 48 development restantes até 120. Relatório: [2026-11-27-meta-learning-v2-checkpoint60-dev.md](../reports/2026-11-27-meta-learning-v2-checkpoint60-dev.md). A decisão formal 60→120 ainda não foi registrada.

## 7. Requisitos técnicos antes da bateria

**Status:** cumpridos para o checkpoint 60 development.

- runner v2: `scripts/run_meta_learning_metabasis_v2.py` (protocol `meta_learning_metabasis_v2`)
- merge/agregação: `scripts/build_meta_learning_metabasis_v2_checkpoint60_dev.py`
- freezer v2: `scripts/freeze_meta_learning_metabasis_v2.py` (recusa sobrescrita; não usa o freezer piloto)
- inventário/split: `scripts/build_meta_learning_metabasis_v2_inventory_split.py`
- testes: `tests/test_meta_learning_metabasis_v2_split.py`, `tests/test_meta_learning_metabasis_v2_runner.py`

O freezer/piloto v1 permanece intacto e não deve gravar em `metabasis_v2`.

## 8. Critérios para avançar de 60 para 120

Avançar se:
- as 60 instâncias estiverem completas e auditadas;
- não houver problemas sistemáticos de parsing, bounds, hashes, seeds ou contadores;
- o tempo observado permitir completar 120 dentro do orçamento disponível;
- os 12 holdouts permanecerem selados;
- a cobertura dos grupos e a proveniência estiverem completas.

Se não avançar, registrar a justificativa e limitar explicitamente as conclusões ao conjunto de desenvolvimento e ao holdout de 12 instâncias, caso este seja aberto após congelamento do protocolo. Não declarar que 60 instâncias garantem poder estatístico.

## 9. Critérios de avaliação confirmatória

Métrica primária: regret por instância da variante escolhida, em comparação com o melhor resultado observado entre as quatro variantes naquela instância (oráculo retrospectivo), calculado sobre o holdout e reportado por instância.

Baseline operacional obrigatório: sempre Fuzzy, além de aleatório, variantes fixas e melhor variante global escolhida somente no desenvolvimento. O objetivo não é maximizar accuracy isoladamente.

Critérios e análise devem ser congelados antes de abrir o holdout:
- diferença pareada de regret Meta-Learner vs sempre Fuzzy;
- média, mediana e intervalo de confiança do regret;
- proporção de vitórias/derrotas/empates por instância;
- análise de sensibilidade para rótulos de baixa confiança;
- métricas complementares de classificação/regressão;
- runtime e custo de inferência/meta-decisão;
- análise por grupo de dimensão, sem transformar subgrupos pequenos em alegações fortes.

Não declarar sucesso apenas por accuracy, significância isolada, ou comparação com um baseline fraco. Se o Meta-Learner não superar Fuzzy de forma útil, reportar resultado negativo/inconclusivo com honestidade.

## 10. Relação com o projeto principal

O trabalho continua sendo GWO aplicado ao PFSP/Taillard. Meta-Learning é uma camada que escolhe entre variantes GWO já existentes; não substitui GWO, não muda o problema de escalonamento e não transforma a pesquisa em um projeto genérico de ML. As Semanas 2–6 e os resultados já auditados permanecem preservados.

## 11. Documentos vinculados

- [Checkpoint 60 development](../reports/2026-11-27-meta-learning-v2-checkpoint60-dev.md)
- [Fase A inventário/split](../reports/2026-11-27-meta-learning-v2-phase-a-inventory-split.md)
- [Runbook da expansão](../reports/2026-11-27-meta-learning-next-execution-runbook.md)
- [Roadmap de conclusão](../plans/2026-11-27-meta-learning-completion-roadmap.md)
- [Status das fases](../reports/2026-11-27-meta-learning-phase-status.md)
- [Freeze imutável do piloto](2026-11-27-metabasis-pilot-v1-freeze.md)
- [README Meta-Learning](../../experiments/meta_learning/README.md)
- [Inventário Taillard](../../data/benchmarks/taillard/README.md)
