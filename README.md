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

A reconstrução versionada da Semana 2 usa instâncias Taillard de PFSP e minimiza makespan. Ela é independente dos experimentos históricos com tardiness e do solver DPFSP-DD. O protocolo completo está em [`docs/reports/week2_reconstruction_protocol.md`](docs/reports/week2_reconstruction_protocol.md).

Execute primeiro um piloto curto para estimar o custo no seu computador:

```bash
python -m scripts.run_week2_benchmark --seeds 3 --wolves 10 --iterations 50 --output results/week2_pilot
```

Depois da validação do piloto, execute o protocolo de 30 seeds:

```bash
python -m scripts.run_week2_benchmark
python -m pip install matplotlib
python -m scripts.plot_week2_convergence
```

Os padrões são 30 lobos, 500 iterações e seeds 0–29, nas instâncias `ta001` e `ta011`. O script gera `runs.csv`, `convergence.csv` e `metadata.json`; os gráficos são gravados em `results/week2_baseline_v1/figures/`. Não execute a bateria completa antes de conferir o tempo do piloto. Os resultados são novos e não substituem os arquivos históricos.

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

## Rastreabilidade

Decisões técnicas e metodológicas são registradas em `docs/decisions/`; auditorias e proveniência estão em `docs/audits/`. Protocolos e resultados históricos devem permanecer identificados separadamente e não ser sobrescritos retroativamente.

## Semana 4 — Surrogate para PFSP/Taillard

A reconstrução da Semana 4 treina um modelo substituto independente para cada instância Taillard, usando LHS sobre random keys, features de posição dos jobs e rótulos calculados pelo avaliador exato de makespan. O protocolo, as métricas e as limitações estão em [`docs/reports/week4_surrogate_protocol.md`](docs/reports/week4_surrogate_protocol.md).

Execute primeiro um piloto com poucas amostras para estimar custo e qualidade:

```bash
python -m scripts.run_week4_surrogate --samples 300 --output results/week4_surrogate_pilot
```

Se o piloto concluir e os artefatos estiverem íntegros, execute a configuração inicial:

```bash
python -m scripts.run_week4_surrogate --samples 2000 --output results/week4_surrogate_v1
```

O script grava dataset por instância, modelo serializado, métricas de treino/teste, tempos, análise de seleção e gráficos. O tempo de geração dos rótulos exatos, treinamento e inferência é reportado separadamente. Não interprete fitness previsto como resultado real: candidatos selecionados pelo modelo são conferidos com makespan exato.
