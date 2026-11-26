# GWO-environment

Repositório do projeto de Sistemas Inteligentes: estudo experimental de variantes do Grey Wolf Optimizer em problemas de Flow Shop.

## Organização

- `data/`: instâncias e dados experimentais.
- `docs/`: especificações, decisões metodológicas, auditorias e guias.
- `notebooks/`: notebooks históricos e de execução.
- `scripts/`: ferramentas e implementações.
- `tests/`: testes automatizados.
- `results/`: resultados e relatórios versionados.

## Ambiente e testes locais

Ambientes verificados: Python 3.12 no CI e Python 3.14 em execução local. Requer pip. Na raiz do repositório:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

O CI executa a suíte em Python 3.12. A suíte também foi executada localmente em Python 3.14: 63 testes passaram. Um aviso de depreciação vem do plugin AnyIO instalado no ambiente, não do código do projeto.

## Semana 2 — reconstrução do baseline Taillard/PFSP

> **Auditoria da correção:** [causa, impacto, testes e sequência de reexecução](docs/audits/2026-11-23-gwo-population-freeze-correction.md).
>
> **Importante:** as baterias `week2_baseline_v1`, `week3_optuna_v1` e `week5_fuzzy_v1` foram afetadas por um bug que mantinha a população GWO congelada entre gerações. Elas foram preservadas, mas não são evidência válida de GWO iterativo. Os scripts atuais implementam a correção v2 e usam pastas de saída distintas.

A reconstrução versionada da Semana 2 usa instâncias Taillard de PFSP e minimiza makespan. Ela é independente dos experimentos históricos com tardiness e do solver DPFSP-DD. O protocolo completo está em [`docs/reports/week2_reconstruction_protocol.md`](docs/reports/week2_reconstruction_protocol.md).

Execute primeiro um piloto curto para estimar o custo no seu computador:

```bash
python -m scripts.run_week2_benchmark --seeds 3 --wolves 10 --iterations 50 --output results/week2_pilot_v2
```

Depois da validação do piloto, execute o protocolo de 30 seeds:

```bash
python -m scripts.run_week2_benchmark
python -m pip install matplotlib
python -m scripts.plot_week2_convergence --input results/week2_baseline_v2/convergence.csv --output results/week2_baseline_v2/figures
```

Os padrões são 30 lobos, 500 iterações e seeds 0–29, nas instâncias `ta001` e `ta011`. A saída padrão é `results/week2_baseline_v2/`; os gráficos devem ser gerados nessa mesma pasta. Não execute a bateria completa antes de conferir o tempo do piloto. Os resultados v2 são novos e não substituem os arquivos v1 preservados.

## Semana 3 — Optuna com GWO corrigido

Depois de gerar `results/week2_baseline_v2/runs.csv`, execute:

```bash
python -m scripts.tune_week3_optuna --output results/week3_optuna_v2
python -m scripts.run_week3_evaluation --config results/week3_optuna_v2/best_params.json --baseline results/week2_baseline_v2/runs.csv --output results/week3_optuna_v2
```

A sintonia padrão usa 30 trials, seeds de treino 100–102 e orçamento de 15.030 avaliações por execução. A avaliação final usa seeds 0–29, reservadas fora da sintonia.

## DPFSP-DD

O avaliador independente do Distributed Permutation Flow Shop com due dates está em [`scripts/dpfsp_dd.py`](scripts/dpfsp_dd.py). Seu contrato e exemplo estão em [`docs/guides/dpfsp_dd_evaluator.md`](docs/guides/dpfsp_dd_evaluator.md).

Valide todas as instâncias do ZIP antes de executar experimentos:

```bash
python scripts/validate_dpfsp_parser.py data/instances/DPFSP_DD.zip
python -m pytest -q tests/test_dpfsp_dd.py
```

O GWO random-key para DPFSP-DD está em [`scripts/discrete_gwo_dpfsp.py`](scripts/discrete_gwo_dpfsp.py). Ele mantém o algoritmo separado do avaliador. Para executar o piloto técnico reduzido:

```bash
python -m scripts.run_gwo_pilot data/instances/DPFSP_DD.zip
```

O piloto usa três instâncias representativas, quatro combinações de população/decaimento, três sementes e 990 avaliações reais por execução. Os arquivos são gravados em `results/gwo_pilot/`. É um piloto técnico, não a bateria experimental confirmatória. Fuzzy e Surrogate não estão incluídos nessa implementação DPFSP-DD.

## Notebook histórico PFS

O notebook [`notebooks/Sistemas_Inteligentes_Entregavel.ipynb`](notebooks/Sistemas_Inteligentes_Entregavel.ipynb) é um artefato histórico destinado ao Google Colab. Ele usa recursos `google.colab.files`, comandos mágicos e upload interativo. Abra o notebook no Colab e execute a partir de uma cópia/clonagem do repositório, de modo que `scripts/legacy_pfs.py` esteja disponível na raiz de trabalho.

Esse notebook espera instâncias do formato PFS legado. **Não use `data/instances/DPFSP_DD.zip` nele:** são formulações diferentes. As instâncias PFS exatas dos experimentos históricos não foram recuperadas para este repositório; portanto, não é possível prometer reprodução integral desses resultados apenas com os arquivos atualmente versionados. O export `scripts/sistemas_inteligentes_entregavel.py` contém magics do Colab e não deve ser executado como um script Python convencional.

## Guia de reprodução e limites da entrega

Consulte [`docs/guides/reproducibility.md`](docs/guides/reproducibility.md) para instalação, comandos, ambientes e limitações conhecidas. O protocolo em [`docs/experimental_protocol.md`](docs/experimental_protocol.md) registra o planejamento experimental, mas não deve ser interpretado como evidência de que a bateria completa de seis configurações foi executada.

## Semana 6 — Benchmark comparativo

O protocolo aprovado compara Baseline, Optuna, Surrogate assistido e Fuzzy em `ta001` e `ta011`, com 30 seeds pareadas. O planejamento inicial permanece preservado em `tasks/plan.md` e `tasks/todo.md`; o plano incremental desta etapa está em [`tasks/week6_plan.md`](tasks/week6_plan.md).

Antes da bateria completa, execute um piloto curto (por exemplo, 2 seeds):

```bash
python -m scripts.run_week6_benchmark --seeds 0 1 --output results/week6_benchmark_pilot_v1
```

Após auditar o piloto, execute a bateria completa:

```bash
python -m scripts.run_week6_benchmark
```

O runner reutiliza os modelos da Semana 4 e os parâmetros congelados do Optuna v2. O Surrogate prevê 30 candidatos por geração e reavalia exatamente os três melhores; previsões nunca atualizam líderes nem convergência. Por execução, são 1.530 avaliações exatas e 15.000 previsões. Baseline, Optuna e Fuzzy usam 15.030 avaliações exatas. Portanto, os orçamentos exatos são diferentes e devem ser interpretados em conjunto com tempo, custo de preparação e qualidade.

A saída é incremental e pode ser retomada: execuções já registradas em `runs.csv` são ignoradas. Não reutilize uma pasta de saída para um protocolo diferente. Os arquivos incluem resultados por seed, convergência, traces Fuzzy/Surrogate, resumo e testes estatísticos com Friedman, Wilcoxon pareado e correção de Holm.

Consulte a [decisão metodológica](docs/decisions/2026-11-25-week6-surrogate-assisted-evaluation.md) e o [protocolo completo](docs/reports/week6_benchmark_protocol.md). A auditoria final só será escrita após a bateria e a análise dos resultados.

## Rastreabilidade

Decisões técnicas e metodológicas são registradas em `docs/decisions/`; auditorias e proveniência estão em `docs/audits/`. Protocolos e resultados históricos devem permanecer identificados separadamente e não ser sobrescritos retroativamente.

## Semana 4 — Surrogate para PFSP/Taillard

A reconstrução da Semana 4 treina um modelo substituto independente para cada instância Taillard, usando LHS sobre random keys, features de posição dos jobs e rótulos calculados pelo avaliador exato de makespan. O protocolo, as métricas e as limitações estão em [`docs/reports/week4_surrogate_protocol.md`](docs/reports/week4_surrogate_protocol.md).

Execute primeiro um piloto com poucas amostras para estimar custo e qualidade:

```bash
python -m scripts.run_week4_surrogate --samples 300 --output results/week4_surrogate_pilot_v2
```

Após revisar o piloto corrigido (incluindo estabilidade dos tempos e métricas de teste), e somente se ele estiver íntegro, execute a ampliação:

```bash
python -m scripts.run_week4_surrogate --samples 2000 --output results/week4_surrogate_v2
```

O script grava dataset por instância, modelo serializado, métricas de treino/teste, tempos, análise de seleção e gráficos. O tempo de geração dos rótulos exatos, treinamento e inferência é reportado separadamente. Não interprete fitness previsto como resultado real: candidatos selecionados pelo modelo são conferidos com makespan exato.

## Semana 5 — GWO com controlador Fuzzy

A reconstrução da Semana 5 aplica um controlador Mamdani ao parâmetro de exploração `a` do GWO no mesmo PFSP/Taillard das Semanas 2–4. O CSV Fuzzy histórico é preservado, mas não contém as entradas, pertinências ou regras necessárias para reproduzir o controlador original. A implementação atual é uma reconstrução documentada; consulte [o protocolo](docs/reports/week5_fuzzy_protocol.md).

Execute primeiro o piloto pareado (3 seeds) e confira os artefatos:

```bash
python -m scripts.run_week5_fuzzy --seeds 0 1 2 --output results/week5_fuzzy_pilot_v2
```

Depois, se o piloto estiver íntegro, execute as 30 seeds:

```bash
python -m scripts.run_week5_fuzzy
```

O padrão compara 30 lobos, 500 iterações e 15.030 avaliações por execução com os resultados v2 das Semanas 2 e 3 ( nas instâncias `ta001` e `ta011`). A saída padrão é `results/week5_fuzzy_v2/`. Os resultados incluem execuções, convergência, traço temporal Fuzzy e comparações pareadas. Não misture esta reconstrução com o histórico de PFS/tardiness nem com DPFSP-DD.
