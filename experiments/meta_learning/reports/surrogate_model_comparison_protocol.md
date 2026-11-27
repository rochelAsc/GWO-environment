# Protocolo — comparação de modelos substitutos para PFSP

**Data:** 26/11/2026  
**Status:** runner do piloto implementado; execução local e resultados ainda pendentes.  
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

**Nenhum resultado do piloto foi fabricado ou presumido nesta atualização.** O runner e os testes foram versionados; a execução precisa ocorrer no computador que contém o checkout e os dados. Não foram adicionadas referências bibliográficas nesta etapa: os estimadores e hiperparâmetros seguem o protocolo já definido, sem nova alegação teórica que exija fonte adicional.
