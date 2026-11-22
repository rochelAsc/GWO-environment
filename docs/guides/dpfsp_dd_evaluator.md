# Uso do avaliador DPFSP-DD

## API mínima

O módulo `scripts/dpfsp_dd.py` oferece:

- `DPFSPInstance(processing_times, due_dates, factories)`: instância imutável.
- `parse_dpfsp_instance_text(text)` e `load_dpfsp_instance(path)`: parser do formato do benchmark.
- `DPFSPEvaluator(instance).evaluate(solution)`: cálculo do cronograma e do Total Tardiness.

Jobs e máquinas usam índices internos zero-based. A solução é uma sequência externa com exatamente F sequências internas. Cada job aparece exatamente uma vez; sequências vazias são permitidas.

## Exemplo

```python
from scripts.dpfsp_dd import DPFSPInstance, DPFSPEvaluator

instance = DPFSPInstance(
    processing_times=((2, 3), (4, 1)),
    due_dates=(4, 10),
    factories=1,
)
result = DPFSPEvaluator(instance).evaluate([[0, 1]])

print(result.total_tardiness)  # 1
print(result.completion_times)  # (5, 7)
print(result.tardiness)  # (1, 0)
```

## Testes

Na raiz do repositório:

```bash
python -m pytest -q tests/test_dpfsp_dd.py
```

## Validação do parser no ZIP real

Para validar todas as instâncias sem extrair o arquivo:

```bash
python scripts/validate_dpfsp_parser.py data/instances/DPFSP_DD.zip
```

O script lê todas as entradas candidatas diretamente do ZIP, registra distribuições de n, m e F e grava um JSON. Qualquer arquivo que não possa ser interpretado provoca saída diferente de zero. Preserve o relatório junto ao commit/experimento que usar o dataset.

A validação do parser e a validação matemática do avaliador são evidências distintas. A primeira verifica se os dados são interpretados; a segunda exige testes unitários e comparação independente em instâncias pequenas.
