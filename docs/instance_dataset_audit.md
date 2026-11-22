# Auditoria estrutural do dataset DPFSP_DD

## Objetivo

Validar integralmente os arquivos de instância do ZIP `data/instances/DPFSP_DD.zip`, sem extrair ou alterar o arquivo compactado. O inventário inicial lê apenas metadados e as primeiras linhas; esta auditoria lê o conteúdo completo de cada candidato.

## Execução

Na raiz do repositório:

```bash
python scripts/audit_dpfsp_instances.py data/instances/DPFSP_DD.zip
```

Opcionalmente, altere a pasta de saída:

```bash
python scripts/audit_dpfsp_instances.py data/instances/DPFSP_DD.zip --output results/instance_audit
```

## Estrutura validada

A validação usa o formato observado nas instâncias:

1. Primeira linha: dois inteiros positivos (`jobs machines`).
2. Segunda linha não vazia: um inteiro positivo. O relatório preserva esse valor sem assumir seu significado.
3. Uma linha por job, com um par `índice_da_máquina tempo_de_processamento` para cada máquina.
4. Marcador `Duedate`.
5. Uma linha por job com um inteiro não negativo de due date.

A auditoria verifica dimensões, quantidade de linhas, quantidade e ordem dos índices de máquina, tempos positivos, marcador e quantidade/formato das due dates. Também verifica padrões de nomes e completude das famílias, mas separa essas verificações de validade estrutural.

## Arquivos gerados

- `instances_audit.csv`: uma linha por instância, com dimensões, contagens, intervalos, hashes e status.
- `families.csv`: uma linha por família, com variantes presentes/ausentes, consistência dimensional e quantidade de matrizes de processamento/vetores de due dates distintos.
- `issues.csv`: problemas e avisos por arquivo ou família.
- `summary.json`: resumo agregado, contagens por diretório e hash SHA-256 do ZIP.

Status `valid` significa que não foram encontradas violações estruturais nem avisos de metadados. `valid_with_warnings` significa que a estrutura passou, mas houve alerta de nome/diretório. `invalid` indica pelo menos uma violação estrutural.

## Limites da auditoria

- A auditoria verifica sintaxe e consistência interna; não prova, por si só, a formulação matemática do problema.
- O segundo inteiro do cabeçalho não recebe interpretação sem documentação da fonte do dataset.
- A validação estrutural não demonstra que o motor legado implementa DPFSP-DD. Essa compatibilidade exige uma implementação/validação do modelo distribuído, incluindo atribuição de jobs às fábricas e cálculo do objetivo.
- Os resultados desta auditoria não alteram os arquivos originais nem os resultados experimentais históricos.
