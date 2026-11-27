# Protocolo — comparação de modelos substitutos para PFSP

**Data:** 26/11/2026  
**Status:** piloto CPU executado e analisado; expansão para repetições adicionais condicionada à decisão metodológica.  
**Dependência:** análise consolidada em [surrogate_learning_curve_v2_extension_statistical_analysis.md](surrogate_learning_curve_v2_extension_statistical_analysis.md).

## 1. Objetivo

Determinar se a baixa capacidade de ordenação observada na curva v2 decorre principalmente da arquitetura MLP 64×64 ou da representação atual de permutações, antes de investir em conjuntos maiores que 32.000 amostras.

A pergunta experimental é: mantendo dados e avaliação constantes, modelos tabulares não neurais conseguem prever makespan e recuperar melhores permutações melhor que o MLP?

Esta etapa é uma extensão de pesquisa. Não altera os algoritmos GWO das Semanas 2–6 nem o requisito da disciplina.

## 2. Modelos

Comparar, inicialmente:

1. **MLP 64×64:** baseline já usado na curva v2, sem retuning.
2. **RandomForestRegressor:** baseline de árvores em ensemble.
3. **ExtraTreesRegressor:** ensemble com maior aleatoriedade, potencialmente eficiente em dados tabulares.
4. **HistGradientBoostingRegressor:** boosting de árvores, incluído após verificar custo/memória no piloto.

Todos os modelos devem receber a mesma matriz de features de posição normalizada e os mesmos alvos exatos de makespan. Pré-processamento e transformações de alvo devem ser ajustados exclusivamente no treino. Não introduzir features calculadas a partir do teste ou dos resultados do algoritmo de busca.

## 3. Desenho experimental

### Piloto inicial

- Instâncias: `ta071` (100×10) e `ta111` (500×20).
- Tamanhos: 8.000 e 32.000.
- Métodos de geração: usar primeiro um único conjunto de treino congelado por repetição (preferência: uniforme, para manter o desenho reproduzível); adicionar LHS somente se houver capacidade e se a pergunta sobre amostragem for retomada.
- Repetições: cinco, reutilizando os conjuntos já persistidos na extensão recuperada.
- Teste: o mesmo conjunto fixo de 1.000 permutações por instância.
- Seeds: usar as seeds já registradas nos NPZ/CSV de origem; não criar novos conjuntos para cada modelo.
- Ajuste: hiperparâmetros pré-fixados no protocolo; qualquer tuning deve usar validação interna derivada apenas do treino.

Para comparar diretamente a arquitetura, cada modelo recebe exatamente o mesmo X/y em cada repetição. Não comparar resultados de modelos treinados em diferentes amostras.

### Controle de custo

Executar primeiro uma repetição em `ta111` com N=8.000 para medir memória e tempo de cada modelo. Só então executar a matriz completa. Treinar um modelo por vez, liberar objetos e arrays quando possível e gravar checkpoint por ajuste. Se HistGradientBoosting exceder o limite de memória ou tempo definido no piloto, registrar a falha e não substituí-lo silenciosamente por outro estimador.

## 4. Hiperparâmetros iniciais congelados

Os valores são pontos de partida conservadores para comparação, não alegações de ótimo:

- MLP: arquitetura e parâmetros idênticos a `scripts/run_week4_surrogate.py::build_model`.
- Random Forest: 300 árvores, `min_samples_leaf=2`, `max_features=1.0`, `n_jobs=1`.
- Extra Trees: 300 árvores, `min_samples_leaf=2`, `max_features=1.0`, `n_jobs=1`.
- HistGradientBoosting: `max_iter=300`, `learning_rate=0.08`, `max_leaf_nodes=31`, `l2_regularization=1.0`, `early_stopping=True`.

Fixar `random_state` a partir da seed de repetição e manter `n_jobs=1` para limitar concorrência/memória. Não alterar parâmetros após observar métricas do teste. Se os defaults forem inadequados, uma etapa posterior de tuning deve usar validação interna e ser relatada separadamente.

## 5. Métricas

### Predição global
- RMSE, MAE e R²;
- Spearman rho e Kendall tau-b.

### Seleção de candidatos
- recall dos melhores 3, 10 e 50 do teste;
- regret do melhor candidato selecionado pelo modelo: makespan exato mínimo entre os selecionados menos o mínimo do conjunto de teste;
- média do makespan exato entre os candidatos selecionados;
- métricas top-k com tratamento explícito de empates ou, no mínimo, a mesma regra determinística para todos os modelos.

### Custo
- tempo de treinamento;
- tempo de inferência em lote e por amostra;
- memória de pico, quando disponível;
- tamanho do modelo serializado.

A métrica de decisão primária deve ser a qualidade de seleção (regret e top-k), não RMSE isolado. O objetivo prático do surrogate é priorizar boas permutações, não apenas ajustar a escala absoluta de makespan.

## 6. Análise estatística

- Reportar média, desvio padrão e IC95% t sobre as cinco repetições, sempre identificando que o teste é fixo.
- Apresentar diferenças por repetição apenas quando a mesma amostra de treino e o mesmo teste foram usados pelos dois modelos; nesse caso, usar análise pareada das diferenças.
- Para top-k, usar bootstrap por repetição ou intervalo de proporção apropriado, reconhecendo que as permutações do teste não são observações independentes em sentido amplo.
- Comparar todos os modelos nos mesmos folds/dados; evitar seleção do vencedor com base em uma única métrica.
- Tratar resultados como exploratórios: duas instâncias não sustentam generalização para todo PFSP.

## 7. Critérios de decisão

- Se outro modelo melhorar claramente Spearman e regret/top-k sem custo proibitivo, aprofundar esse modelo antes de aumentar N.
- Se os modelos tiverem desempenho semelhante, investigar representação: features estruturais da permutação, pairwise precedence, encoding de adjacências ou ranking pairwise.
- Se todos falharem sobretudo em `ta111`, investigar se a distribuição uniforme do teste é desalinhada da distribuição de candidatos que o GWO realmente visita. Isso exige coletar populações/traces do GWO sem misturar essa análise com o teste uniforme atual.
- Só considerar N>32.000 depois de demonstrar que a arquitetura/representação atual ainda melhora de forma relevante e que o custo marginal compensa.

## 8. Integridade e reprodutibilidade

- Não modificar os CSVs/NPZs originais ou a pasta de recuperação.
- Salvar resultados em nova pasta, por exemplo `results/meta_learning_surrogate_model_comparison_pilot/`.
- Registrar commit, hashes dos NPZs e testes fixos, versões de Python/NumPy/SciPy/scikit-learn, hiperparâmetros e seeds.
- Checkpoint por ajuste para permitir retomada.
- Testes devem verificar que todos os modelos recebem exatamente os mesmos arrays, que o split não muda e que as métricas de ranking/regret são calculadas corretamente.
- Não versionar modelos grandes sem decisão explícita; versionar resultados tabulares, configuração e metadados necessários à reprodução.


## 9. Runner do piloto (26/11/2026)

Implementação: [`run_surrogate_model_comparison_pilot.py`](../scripts/run_surrogate_model_comparison_pilot.py). Testes unitários: [`test_surrogate_model_comparison_pilot.py`](../../../tests/test_surrogate_model_comparison_pilot.py).

**Correção de localização dos artefatos:** os dados originais completos estão na branch `recovery/surrogate-learning-curve-v2-oom`, em `results/meta_learning_surrogate_learning_curve_v2_extension/`. A pasta `..._recovered/` contém somente os artefatos complementares da recuperação e não deve ser usada como raiz dos dados completos do piloto.

O piloto usa especificamente:
- `results/meta_learning_surrogate_learning_curve_v2_extension/ta111/ta111_uniform_permutations_n8000_rep1_diagnostics.npz`;
- `results/meta_learning_surrogate_learning_curve_v2_extension/ta111/fixed_test_set.npz`;
- `data/benchmarks/taillard/ta111.txt`.

O runner valida dimensões, unicidade, ausência de sobreposição treino/teste, reconstrução das features a partir das permutações e hashes dos três arquivos. Os alvos de treino são recalculados pelo makespan exato da instância. Os NPZs originais são somente leitura.

Execução a partir da raiz do repositório:

```bash
python -m pytest -q tests/test_surrogate_model_comparison_pilot.py
python -m experiments.meta_learning.scripts.run_surrogate_model_comparison_pilot
```

Os quatro modelos são ajustados sequencialmente, com limite de uma thread, e cada modelo concluído é gravado em `pilot_checkpoints.jsonl`. A execução pode ser retomada pelo mesmo comando. Resultados finais/estado ficam em `pilot_results.csv` e `pilot_status.json`, dentro de `results/meta_learning_surrogate_model_comparison_pilot/`. O uso de memória RSS é amostrado via `psutil`, caso esteja instalado; caso contrário, o campo é explicitamente marcado como indisponível. A medição representa o RSS do processo (inclui arrays e runtime), não memória exclusiva do estimador.




## 10. Resultados observados do piloto (ta111, N=8.000)

**Status:** execução concluída, quatro checkpoints presentes e `pilot_status.json` indica `completed`. Fonte primária: `results/meta_learning_surrogate_model_comparison_pilot/pilot_results.csv`; configuração e hashes em `pilot_metadata.json`.

Condições efetivamente registradas:
- ta111 (500 jobs × 20 máquinas), treino uniforme com 8.000 permutações, repetição 1;
- teste fixo de 1.000 permutações;
- mesma representação: posição normalizada por job;
- CPU, limite de uma thread, modelos sequenciais;
- Python 3.14.6, NumPy 2.5.1, SciPy 1.18.0, scikit-learn 1.9.0;
- RSS amostrado com psutil a cada 50 ms. O pico é do processo inteiro, incluindo dados e runtime, não memória exclusiva do estimador.

### Métricas preditivas e de seleção

| Modelo | RMSE ↓ | R² ↑ | Spearman ↑ | Kendall τ-b ↑ | Recall top-10 ↑ | Regret top-10 ↓ |
|---|---:|---:|---:|---:|---:|---:|
| MLP 64×64 | 331.24 | 0.0086 | 0.2130 | 0.1431 | 0.00 | 270 |
| Random Forest | 326.15 | 0.0387 | 0.2511 | 0.1693 | 0.00 | 367 |
| Extra Trees | 326.35 | 0.0376 | 0.2445 | 0.1646 | 0.00 | 430 |
| HistGradientBoosting | **321.02** | **0.0688** | **0.2652** | **0.1759** | 0.00 | 319 |

HistGradientBoosting liderou nas métricas globais de erro e correlação. Isso não se traduziu em recuperação dos melhores candidatos: **nenhum modelo recuperou qualquer elemento do top-3 ou top-10 real**. No top-50, o recall foi 14% para MLP, 10% para Random Forest, 12% para Extra Trees e 6% para HistGradientBoosting. O regret top-50 foi 182 para todos os modelos.

O melhor regret top-10 foi do MLP (270), apesar de sua correlação inferior. Isso ilustra por que RMSE/Spearman, isoladamente, não determinam utilidade para seleção. Também mostra que uma única repetição não permite declarar vencedor.

### Custo observado

| Modelo | Treinamento (s) ↓ | Inferência 1.000 (s) ↓ | RSS pico (MB) ↓ |
|---|---:|---:|---:|
| MLP 64×64 | **1.85** | **0.0048** | **300.4** |
| Random Forest | 526.29 | 0.0886 | 350.0 |
| Extra Trees | 173.81 | 0.0980 | 393.9 |
| HistGradientBoosting | 7.45 | 0.0183 | 337.0 |

Random Forest e Extra Trees foram muito mais lentos para treinar neste cenário. HistGradientBoosting foi o melhor compromisso de correlação entre os modelos tabulares, mas ainda não é um seletor confiável dos melhores candidatos. O MLP foi o mais rápido tanto no ajuste quanto na inferência.

### Interpretação e decisão

1. O problema não parece ser resolvido simplesmente trocando MLP por árvores: todos os modelos têm R² baixo e ranking fraco.
2. O teste uniforme mede desempenho em permutações aleatórias, não necessariamente na distribuição de candidatos visitados pelo GWO. Não extrapolar estes números para o uso online no algoritmo.
3. O resultado é apenas um piloto com uma instância, um tamanho e uma repetição. Não há base para inferência estatística nem para seleção definitiva de arquitetura.
4. **Não integrar nenhum desses modelos ao Surrogate-assisted GWO ainda.**
5. Próxima etapa recomendada: investigar a distribuição de candidatos gerados pelas populações/traços reais do GWO e medir a utilidade de ranking nessa distribuição, mantendo um conjunto de teste separado. Em paralelo, executar repetições pareadas em ta111 apenas se a avaliação sob distribuição uniforme ainda for uma pergunta relevante. Não aumentar N antes de resolver a discrepância entre métrica global e recuperação dos melhores candidatos.

Limitações de rastreabilidade: o manifesto do piloto registra versões de software e hashes dos dados, mas não registra modelo de CPU, RAM física nem commit exato do código executado. Esses campos devem ser adicionados ao runner antes de uma campanha maior. O hardware informado para a execução foi Ryzen 5 5500 e 32 GB RAM, mas esses dados não constam no manifesto da execução.

Não foram adicionadas referências bibliográficas: esta seção relata resultados empíricos do próprio repositório e não introduz alegações teóricas externas.
