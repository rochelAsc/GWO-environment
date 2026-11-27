# Plano de Meta-Learning: classificação e regressão

**Status:** planejamento metodológico aprovado para implementação futura. O pipeline de Meta-Learning que seleciona variantes GWO (classificação/regressão) ainda não foi implementado nem avaliado. Isso é distinto da extensão experimental de surrogate descrita abaixo.

Este plano define um pipeline único para comparar duas estratégias de Meta-Learning — classificação e regressão — usando a mesma base experimental. É uma extensão opcional do projeto, não uma etapa obrigatória do roteiro do professor e não substitui as Semanas 1–6.

## Trabalho concluído relacionado: curva de aprendizagem do surrogate

Foi executada e analisada uma extensão separada para avaliar o efeito do tamanho do conjunto de treinamento do MLP surrogate da Semana 4. Os resultados cobrem `ta071` e `ta111`, LHS e amostragem uniforme, de 300 a 32.000 amostras, com cinco repetições por ponto e teste fixo por instância.

- [Análise estatística consolidada e IC95%](reports/surrogate_learning_curve_v2_extension_statistical_analysis.md).
- [Protocolo da próxima etapa: comparação de modelos](reports/surrogate_model_comparison_protocol.md).
- [Protocolo v2 de amostragem e diagnósticos](reports/surrogate_learning_curve_v2_protocol.md).
- [Relatório de recuperação da execução interrompida](reports/surrogate_learning_curve_v2_recovery.md).

Essa curva **não é a meta-base de Meta-Learning** descrita neste documento: ela estuda o surrogate de makespan, não aprende a escolher entre variantes GWO. Portanto, a afirmação de que o pipeline de Meta-Learning ainda não foi executado continua válida.

## 1. Objetivo

Dada uma instância PFSP/Taillard ainda não vista, selecionar automaticamente uma das quatro estratégias GWO avaliadas na Semana 6:

- `baseline`;
- `optuna`;
- `surrogate`;
- `fuzzy`.

A camada meta aprende a escolher a estratégia. Ela **não** substitui o avaliador de makespan, não prevê diretamente permutações e não altera os algoritmos-base.

O escopo inicial é o PFSP clássico de uma fábrica, minimizando makespan. Não misturar com PFS/tardiness histórico, DPFSP-DD ou com a proposta original dengue/LSTM.

## 2. Decisão arquitetural: uma base, dois modelos

O pipeline terá duas fases separadas:

1. **Construção da meta-base:** extrair características de cada instância e obter os resultados das quatro variantes sob protocolo controlado.
2. **Treinamento e avaliação:** derivar alvos de classificação e regressão da mesma meta-base e treinar os dois modelos em paralelo.

Assim, cada instância é executada uma única vez por combinação variante × seed. Classificação e regressão não provocam uma segunda bateria GWO.

### 2.1 Classificação

Uma linha por instância. O alvo é a variante com menor desempenho médio normalizado, considerando as seeds daquela instância.

Modelo inicial: `RandomForestClassifier`.

Saídas:
- classe prevista;
- probabilidades por variante;
- confiança/margem entre as duas maiores probabilidades.

A classe-alvo será derivada dos resultados agregados por instância, nunca de uma execução individual. Registrar margem entre a melhor e a segunda melhor variante. Instâncias com diferenças muito pequenas serão sinalizadas como rótulos de baixa confiança para análise de sensibilidade; não ocultar empates ou instabilidade.

### 2.2 Regressão

A mesma linha de características terá quatro alvos numéricos: desempenho médio normalizado de Baseline, Optuna, Surrogate e Fuzzy.

Modelo inicial: `RandomForestRegressor` multioutput ou quatro regressors independentes, escolhendo uma única opção após teste técnico. A decisão é a variante com menor desempenho previsto.

Saídas:
- quatro valores previstos;
- variante selecionada;
- erro de previsão por variante;
- regret da seleção: desempenho observado da variante escolhida menos o melhor desempenho observado naquela instância.

A regressão permite analisar não apenas se o modelo acertou a classe vencedora, mas também o custo de escolher uma alternativa quase tão boa ou muito pior.

## 3. Meta-base e unidade estatística

A unidade independente de generalização é a **instância**, não a execução nem a seed.

Estrutura lógica:

- uma linha por instância;
- características calculadas apenas a partir da matriz de tempos de processamento;
- quatro alvos de desempenho agregados, um por variante;
- resultados individuais por seed mantidos em arquivo separado para auditoria e estimativa de variabilidade.

As seeds reduzem ruído na estimativa de desempenho de cada variante, mas **não aumentam o número de instâncias independentes**. Não dividir linhas de execuções/seed aleatoriamente entre treino e teste: isso causaria vazamento da mesma instância.

### 3.1 Instâncias atuais e expansão necessária

O benchmark atual usa `ta001` (20 jobs × 5 máquinas) e `ta011` (20 jobs × 10 máquinas). Duas instâncias — ambas com 20 jobs — não permitem treinar nem avaliar de forma confiável um meta-modelo.

É necessário ampliar o conjunto com instâncias Taillard de diferentes tamanhos e relações jobs/máquinas. A seleção deve ser estratificada por dimensão e cobrir diferentes regimes, não apenas muitas instâncias quase idênticas.

**Subset piloto já versionado:** `data/benchmarks/taillard/` agora contém 12 instâncias, uma de cada grupo de dimensão do benchmark clássico: 20×5, 20×10, 20×20, 50×5, 50×10, 50×20, 100×5, 100×10, 100×20, 200×10, 200×20 e 500×20. As instâncias adicionais foram obtidas do espelho PISCO; a proveniência e a seleção estão registradas em `data/benchmarks/taillard/README.md`.

Esse subconjunto serve para validar parser, características e custo em diferentes escalas. **Não deve ser tratado como meta-base suficiente para treinar ou avaliar generalização**: há apenas uma instância por grupo e doze unidades independentes no total.

Plano em fases, sujeito a medição de custo:

- **Piloto de viabilidade:** 12–20 instâncias diversas, poucas seeds (por exemplo, 3–5), apenas para validar extração, execução, persistência e custo. Não usar o piloto como evidência final de generalização.
- **Meta-base exploratória:** alvo inicial de 30–50 instâncias, com 10 seeds por variante/instância, se o custo permitir. Esse tamanho ainda pode ser insuficiente para conclusões fortes; tratar resultados como exploratórios.
- **Expansão confirmatória:** buscar 50–100 ou mais instâncias, com 20–30 seeds por variante/instância, se os recursos e o tempo permitirem. A suficiência deve ser julgada pela diversidade e pela incerteza, não apenas pela contagem.

Os números são metas de planejamento, não garantia de poder estatístico. Antes de expandir, medir tempo por instância/variante no piloto. Priorizar cobertura de dimensões e integridade dos dados.

Os resultados publicados de Semana 6 para `ta001` e `ta011` podem ser incorporados como observações históricas compatíveis, após validação de hashes, protocolo, variantes e seeds. Não duplicar essas linhas executando-as novamente sem necessidade. Registrar a proveniência de cada linha e manter o conjunto original imutável.

## 4. Características das instâncias

O extrator deve ser determinístico, independente das variantes e calculado somente da matriz de processamento (P\).

Características candidatas:

- dimensões: número de jobs, número de máquinas e razão jobs/máquinas;
- estatísticas globais dos tempos: média, desvio padrão, coeficiente de variação, mínimo, máximo e quantis;
- carga por máquina: soma, média, desvio e coeficiente de variação entre máquinas;
- carga por job: soma, média, desvio e coeficiente de variação entre jobs;
- estrutura: máquina de maior carga, proporção da carga da máquina mais carregada e correlações entre cargas de máquinas adjacentes;
- dispersão relativa de processamento por máquina e por job.

Regras:
- não usar makespan, upper bound, lower bound, resultados GWO, seeds, nome do arquivo ou identificadores como preditores;
- UB/LB podem ser usados para normalização e auditoria do alvo, mas não como feature, para evitar que o modelo dependa de informação de benchmark que pode não existir em uma instância nova;
- tratar valores ausentes e colunas constantes explicitamente;
- fixar nomes, unidades e versão do extrator;
- testar invariância do extrator a mudanças de caminho/nome do arquivo;
- calcular qualquer padronização/seleção de features dentro do fold de treino, nunca sobre o dataset completo.

## 4.1 Implementação inicial do extrator

O primeiro componente implementado é `scripts/extract_instance_features.py`. Ele calcula, exclusivamente a partir da matriz de tempos de processamento:

- dimensões e razão jobs/máquinas;
- estatísticas globais dos tempos de processamento;
- estatísticas das cargas agregadas por job;
- estatísticas das cargas agregadas por máquina;
- concentração relativa da carga nas máquinas;
- dispersão dos coeficientes de variação por máquina;
- correlações entre colunas de máquinas adjacentes, calculadas sobre os jobs.

A saída inclui identificador, SHA-256 e versão do extrator para proveniência. Esses campos são metadados e **não podem entrar como preditores**. O script não usa UB/LB, makespan, resultados de algoritmos, seed ou caminho/nome como característica.

Execução a partir da raiz do repositório:

```bash
python -m experiments.meta_learning.scripts.extract_instance_features \
  --input-dir data/benchmarks/taillard \
  --output experiments/meta_learning/data/instance_features.csv
```

Testes específicos: `python -m pytest -q tests/test_meta_learning_features.py`.

Esta implementação é inicial e ainda precisa ser executada no ambiente do projeto, revisada contra instâncias de todas as dimensões e congelada com uma versão formal antes da construção da meta-base.

## 5. Alvos e normalização

O objetivo primário permanece qualidade da solução. Para cada instância (i), variante (v) e seed (s), armazenar o makespan final (C_{i,v,s}), runtime e contadores.

Alvo primário por variante:

[
y_{i,v}=\frac{\operatorname{mean}_{s}(C_{i,v,s})}{UB_i}
]

quando um upper bound publicado confiável estiver disponível e validado. Para instâncias sem UB, usar uma normalização alternativa definida antes da execução (por exemplo, dividir pela melhor média observada entre variantes da própria instância) apenas para análise relativa; documentar que essa normalização é relativa e não comparável entre instâncias. Não misturar silenciosamente as duas convenções.

A classificação seleciona o menor (y_{i,v}). A regressão prevê os quatro (y_{i,v}) e seleciona o menor. Runtime e número de avaliações são métricas secundárias e não entram no alvo primário inicial; uma futura seleção multiobjetivo exigiria outro protocolo explícito.

Também armazenar mediana, desvio padrão, intervalo de confiança/bootstrapping por seed, mínimo, máximo e taxa de alcance do UB, sem reduzir a base a uma única média.

## 6. Protocolo de execução da meta-base

Para cada instância nova:

1. validar e calcular SHA-256 do arquivo;
2. extrair e persistir as features;
3. executar as quatro variantes com configurações congeladas da Semana 6;
4. usar o mesmo conjunto de seeds por variante dentro da instância;
5. armazenar makespan, runtime, avaliações exatas, previsões surrogate, tempo de inferência e demais contadores;
6. verificar combinações ausentes/duplicadas e consistência dos contadores;
7. agregar resultados e derivar os alvos somente após a validação.

As configurações congeladas devem corresponder ao protocolo auditado da Semana 6. O orçamento exato do Surrogate é diferente (1.530 avaliações exatas + 15.000 previsões por execução, contra 15.030 avaliações exatas nas demais variantes). Reportar essa diferença e os custos de preparação separadamente; não declarar igualdade de orçamento.

O custo de gerar a meta-base pode ser elevado: o piloto deve estimar o custo antes da expansão. Não iniciar a bateria grande automaticamente no notebook.

## 7. Divisão treino/validação/teste sem vazamento

Todas as divisões são feitas por **instância**.

Protocolo preferido:
- reservar um holdout final de instâncias nunca usadas para decisões de features/modelo;
- no conjunto de desenvolvimento, usar validação cruzada agrupada por instância (por exemplo, `GroupKFold` ou `LeaveOneGroupOut`, com cada instância como grupo);
- se houver famílias/dimensões muito relacionadas, agrupar por bloco de instâncias ou família para testar generalização mais difícil;
- executar seleção de hiperparâmetros somente dentro dos folds de desenvolvimento;
- abrir o holdout uma única vez após congelar o pipeline.

Com poucas instâncias, um holdout fixo pode ficar instável. Nesse caso, reportar validação cruzada agrupada como exploratória e não alegar teste independente robusto. Nunca usar seeds de uma mesma instância em treino e teste como se fossem instâncias diferentes.

## 8. Baselines obrigatórios

Comparar cada meta-modelo com seletores simples:

1. seleção aleatória uniforme entre as quatro variantes;
2. sempre Baseline;
3. sempre Optuna;
4. sempre Surrogate;
5. sempre Fuzzy;
6. melhor variante global escolhida apenas no conjunto de treino;
7. classificador;
8. regressor com seleção pelo menor valor previsto.

O baseline “melhor global” deve ser recalculado dentro de cada fold usando somente o treino. Não selecionar a melhor variante usando os rótulos do teste.

## 9. Métricas de avaliação

**Classificação**
- acurácia e balanced accuracy;
- macro-F1;
- matriz de confusão;
- precisão/recall por variante;
- log loss e Brier score, se probabilidades forem usadas;
- acurácia com análise separada de rótulos de baixa confiança.

**Regressão**
- MAE e RMSE por variante;
- (R^2) por alvo, com cautela em amostras pequenas;
- erro de ranking entre variantes;
- regret médio/mediano da variante selecionada;
- frequência em que a seleção regressiva escolhe a melhor ou uma variante estatisticamente/operacionalmente equivalente.

**Seleção final**
- makespan normalizado observado da estratégia selecionada no teste;
- diferença para a melhor variante-oráculo observada no teste (regret);
- comparação pareada por instância contra os baselines;
- runtime/custo da estratégia escolhida e custo adicional do meta-modelo.

A variante-oráculo do teste é apenas referência retrospectiva; não é um método disponível em produção.

## 10. Análise de incerteza e rótulos instáveis

A melhor variante por média pode mudar com as seeds. Portanto:
- preservar resultados por seed;
- estimar incerteza da diferença entre as duas melhores variantes;
- marcar rótulos com pequena margem como baixa confiança;
- repetir análise excluindo ou ponderando esses casos como sensibilidade, sem removê-los silenciosamente;
- não afirmar que a classe prevista é universal quando as diferenças observadas são praticamente equivalentes.

## 11. Estrutura de diretórios proposta

A implementação futura deve ficar isolada, sem alterar scripts/artefatos das Semanas 2–6:

```text
experiments/meta_learning/
├── README.md
├── config/
│   └── meta_learning_v1.json
├── data/
│   ├── instance_features.csv
│   ├── run_results.csv
│   └── meta_dataset.csv
├── scripts/
│   ├── extract_instance_features.py
│   ├── build_meta_dataset.py
│   ├── train_classifier.py
│   ├── train_regressor.py
│   ├── evaluate_meta_models.py
│   └── run_meta_learning.py
├── models/
├── reports/
├── tests/
└── results/
    └── meta_learning_v1/
```

Os arquivos de dados/modelos/resultados só serão criados durante a implementação/execução. Não versionar artefatos vazios nem colocar resultados fictícios no repositório. Configurações, scripts, testes e relatórios devem ser versionados. Cada execução deve registrar commit, hashes das instâncias, versão do extrator, parâmetros, seeds, ambiente e timestamp.

## 12. Pipeline operacional

```mermaid
flowchart TD
    A[Instâncias Taillard diversas] --> B[Validação e SHA-256]
    B --> C[Extração de características]
    B --> D[Execução das quatro variantes]
    D --> E[Resultados por seed e custo]
    C --> F[Meta-base por instância]
    E --> F
    F --> G[Alvos: vencedor e quatro desempenhos]
    G --> H[Divisão agrupada por instância]
    H --> I[Random Forest Classifier]
    H --> J[Random Forest Regressor]
    I --> K[Avaliação de classificação]
    J --> L[Seleção pelo menor desempenho previsto]
    K --> M[Comparação com baselines]
    L --> M
    M --> N[Relatório, incerteza e regret]
```

## 13. Critérios de aceite antes de qualquer conclusão

- [ ] Conjunto de instâncias ampliado e diversidade documentada.
- [ ] Piloto de custo concluído antes de definir a bateria final.
- [ ] Features independentes dos resultados e sem vazamento.
- [ ] Resultados das quatro variantes íntegros, com seeds e contadores auditáveis.
- [ ] Meta-base com uma linha por instância e proveniência rastreável.
- [ ] Divisões exclusivamente por instância.
- [ ] Baselines simples calculados sem consultar o teste.
- [ ] Classificação e regressão avaliadas sobre os mesmos folds/holdout.
- [ ] Regret, incerteza dos rótulos e custos reportados.
- [ ] Testes automatizados, relatório e reprodução documentados.

## 14. Limitações e decisão de escopo

- As duas instâncias atuais não sustentam treinamento/avaliação de Meta-Learning.
- A meta-base exige novas execuções e pode custar milhares de runs; não executar sem piloto e estimativa de recursos.
- Random Forest é um ponto de partida, não uma escolha comprovadamente ótima.
- O resultado será válido para a distribuição de instâncias representada no dataset; generalização para outras famílias de scheduling não está garantida.
- Meta-Learning é uma extensão independente e opcional. A entrega principal continua sendo a linha PFSP/Taillard e os resultados auditados das Semanas 2–6.
- O documento define o plano, não afirma que código, modelos ou experimentos de Meta-Learning já existem.


## Referências e curva de aprendizagem do surrogate

As referências bibliográficas utilizadas na fundamentação estão em [referencias.md](referencias.md). O protocolo de curva de aprendizagem, incluindo a justificativa da progressão geométrica, está em [surrogate_learning_curve_protocol.md](reports/surrogate_learning_curve_protocol.md).

O runner foi implementado em [run_surrogate_learning_curve.py](scripts/run_surrogate_learning_curve.py). Ele compara LHS em random keys com permutações uniformes, usa um teste externo fixo por instância e mede regressão, ranking, top-k e custo.

Execução padrão (sequencial; não paralelizar nesta primeira rodada):

```bash
python -m pytest -q tests/test_meta_learning_learning_curve.py
python -m experiments.meta_learning.scripts.run_surrogate_learning_curve
```

A configuração padrão avalia `ta071` e `ta111`, cinco tamanhos geométricos (300, 573, 1.095, 2.093 e 4.000), cinco repetições e 1.000 permutações de teste fixas por instância. Resultados são escritos em `results/meta_learning_surrogate_learning_curve_v1/`. Não sobrescrever resultados anteriores; para uma nova execução, use outro diretório `--output` e registre as seeds.


## 9. Surrogate: curva v1 e diagnóstico (26/11/2026)

A curva v1 foi executada para ta071 e ta111, com 300, 573, 1.095, 2.093 e 4.000 amostras, cinco repetições e dois braços de amostragem. Resultados e limitações estão documentados em:

- [Protocolo e resultados da curva](reports/surrogate_learning_curve_protocol.md)
- [Auditoria de representação, distribuição, literatura e plano de correção](reports/surrogate_failure_analysis_2026-11-26.md)
- Resultados brutos e agregados: results/meta_learning_surrogate_learning_curve_v1/

Conclusão: mais amostras melhoraram RMSE e ranking, mas a qualidade ainda é insuficiente, principalmente na ta111. Não aumentar N imediatamente. Primeiro comparar MLP com GBDT/HistGradientBoosting e ExtraTrees, investigar ranking pareado e avaliar candidatos extraídos de trajetórias GWO. A execução v1 chamou o braço LHS em blocos de até 512 draws; por isso, não descrevê-lo como um LHS global de N pontos.

**Meta-Learning por instância:** a expansão de 12 para 36 instâncias Taillard é recomendada como próximo piloto (três instâncias por grupo), com possível avanço para 60 e depois o benchmark completo de 120 instâncias. A quantidade de instâncias é distinta da quantidade de permutações usadas para treinar um surrogate por instância. Ver o relatório de auditoria antes de iniciar a bateria.


### Curva de aprendizagem v2 — LHS global e diagnósticos

A correção metodológica está implementada em [run_surrogate_learning_curve_v2.py](scripts/run_surrogate_learning_curve_v2.py), com testes em [test_meta_learning_learning_curve_v2.py](../../tests/test_meta_learning_learning_curve_v2.py) e protocolo em [surrogate_learning_curve_v2_protocol.md](reports/surrogate_learning_curve_v2_protocol.md). A v1 e seus resultados permanecem preservados. A curva v2 original foi executada e publicada; a extensão até 32.000 amostras foi recuperada e publicada em diretório separado. A análise estatística consolidada está em [surrogate_learning_curve_v2_extension_statistical_analysis.md](reports/surrogate_learning_curve_v2_extension_statistical_analysis.md). O próximo experimento é a comparação controlada de modelos, definida em [surrogate_model_comparison_protocol.md](reports/surrogate_model_comparison_protocol.md).


### Comparação de modelos substitutos — piloto CPU

O protocolo e runner do piloto estão documentados em [surrogate_model_comparison_protocol.md](reports/surrogate_model_comparison_protocol.md) e [run_surrogate_model_comparison_pilot.py](scripts/run_surrogate_model_comparison_pilot.py). O piloto usa os artefatos originais da branch de recuperação, sem regenerar ou modificar os NPZs.

```bash
python -m pytest -q tests/test_surrogate_model_comparison_pilot.py
python -m experiments.meta_learning.scripts.run_surrogate_model_comparison_pilot
```

A execução compara MLP 64×64, Random Forest, Extra Trees e HistGradientBoosting em `ta111`, 8.000 permutações uniformes (repetição 1) e teste fixo de 1.000 permutações. Treina sequencialmente em CPU, grava checkpoints por modelo e permite retomada. A execução foi concluída. Resultados, métricas de custo e interpretação estão na seção 10 de [surrogate_model_comparison_protocol.md](reports/surrogate_model_comparison_protocol.md). O piloto é exploratório (uma repetição, uma instância) e não autoriza integração de modelo ao GWO.


### Distribuição real de candidatos das trajetórias GWO

A coleta das populações completas das quatro variantes GWO foi executada em `ta111`, com seeds 0–4. Foram concluídas 20 execuções e registrados 300.600 candidatos com makespan exato diagnóstico. Os rótulos diagnósticos não influenciam a busca.

- [Relatório dos resultados do piloto](../../docs/reports/2026-11-26-gwo-population-distribution-pilot.md).
- [Protocolo, instrumentação e próximos passos](../../docs/reports/gwo_population_distribution_audit_protocol.md).

O piloto usou o surrogate Cost Pilot v2 para ta111, pois o artefato Week 4 original dessa instância não estava disponível. Essa diferença está registrada nos metadados e impede tratar a execução como reprodução exata do modelo Surrogate da Week 6.

Arquivos compactos versionados: `results/gwo_population_distribution_audit_v1/metadata.json` e `runs.csv`. O `populations.csv` (~551,40 MB) permanece fora do GitHub por exceder o limite de 100 MB; deve ser preservado localmente e disponibilizado externamente antes da análise de distribuição.

Antes de ampliar para 30 seeds, validar o CSV completo e revisar a deduplicação do runner para reduzir uso de memória. A análise estatística dos candidatos ainda não foi concluída. O piloto de cinco seeds é exploratório e não constitui dataset final para treino/teste.

Comandos corretos a partir da raiz do repositório:

```bash
python -m pytest -q tests/test_gwo_population_observer.py
python -m scripts.run_gwo_population_distribution_audit --surrogate-dir results/meta_learning_cost_pilot_v2/surrogates
```
