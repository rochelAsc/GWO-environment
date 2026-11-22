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

## Ambiente de desenvolvimento e testes

Os testes usam `pytest`. Instale a dependência no mesmo interpretador Python que será usado para executá-los:

```bash
python -m pip install pytest
```

Se o comando `pip` não estiver disponível nesse interpretador, inicialize-o e tente novamente:

```bash
python -m ensurepip --upgrade
python -m pip install pytest
```

Na raiz do repositório, execute:

```bash
python -m pytest -q tests/test_dpfsp_dd.py
```

No Windows, também é possível usar o caminho explícito do interpretador, por exemplo:

```powershell
C:\Python314\python.exe -m pip install pytest
C:\Python314\python.exe -m pytest -q tests\test_dpfsp_dd.py
```

## Validação do parser no ZIP real

Para validar todas as instâncias sem extrair o arquivo:

```bash
python scripts/validate_dpfsp_parser.py data/instances/DPFSP_DD.zip
```

O script lê todas as entradas candidatas diretamente do ZIP, registra distribuições de n, m e F e grava um JSON. Arquivos com codificação UTF-8 inválida ou conteúdo rejeitado pelo parser são registrados como falhas e provocam saída diferente de zero. Erros inesperados de execução não são convertidos em falhas de parsing: eles interrompem o script para não ocultar defeitos de programação. Um ZIP sem arquivos candidatos também provoca erro explícito.

Preserve o relatório junto ao commit/experimento que usar o dataset.

A validação do parser e a validação matemática do avaliador são evidências distintas. A primeira verifica se os dados são interpretados; a segunda exige testes unitários e comparação independente em instâncias pequenas.
