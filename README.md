# GWO-environment

Repositório do projeto de Sistemas Inteligentes: estudo experimental de variantes do Grey Wolf Optimizer em problemas de Flow Shop.

## Organização

- `data/`: instâncias e dados experimentais.
- `docs/`: especificações, decisões metodológicas, protocolos e relatórios.
- `notebooks/`: notebooks históricos e de execução.
- `scripts/`: ferramentas e implementações.
- `tests/`: testes automatizados.

## DPFSP-DD

O avaliador independente do Distributed Permutation Flow Shop com due dates está em [`scripts/dpfsp_dd.py`](scripts/dpfsp_dd.py). Seu contrato, exemplo de uso e comandos de teste estão em [`docs/guides/dpfsp_dd_evaluator.md`](docs/guides/dpfsp_dd_evaluator.md).

Antes de executar experimentos com o ZIP, valide o parser em todas as instâncias:

```bash
python scripts/validate_dpfsp_parser.py data/instances/DPFSP_DD.zip
python -m pytest -q tests/test_dpfsp_dd.py
```

A implementação do avaliador não depende do GWO. A adaptação random-key do GWO está em [`scripts/discrete_gwo_dpfsp.py`](scripts/discrete_gwo_dpfsp.py), com decisão metodológica e limitações em [`docs/decisions/2026-11-22-discrete-gwo-dpfsp-dd.md`](docs/decisions/2026-11-22-discrete-gwo-dpfsp-dd.md). A especificação matemática permanece em revisão em [`docs/specifications/dpfsp_dd_spec.md`](docs/specifications/dpfsp_dd_spec.md).

Para executar os testes do avaliador e do GWO:

```bash
python -m pytest -q tests/test_dpfsp_dd.py tests/test_discrete_gwo_dpfsp.py
```

A nova implementação usa NumPy e mantém o GWO separado do avaliador. Ela não altera o notebook nem os resultados históricos.

## Rastreabilidade

Decisões técnicas e metodológicas devem ser registradas em `docs/decisions/`, incluindo alternativas consideradas, justificativa, consequências e evidências de validação. Protocolos experimentais congelados devem ter versão e não devem ser sobrescritos retroativamente.
