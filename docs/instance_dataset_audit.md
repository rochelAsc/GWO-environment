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
2. Segunda linha não vazia: número de fábricas (`F`). A interpretação foi confirmada pelo artigo de Gogos (2023), que descreve o mesmo padrão de nomes e o cabeçalho dos benchmarks Small/Large.
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

## Resultado da primeira execução

O relatório publicado registrou 1.140 arquivos estruturalmente válidos, sem arquivos inválidos, sem avisos por arquivo e sem grupos de conteúdo integralmente duplicado. Foram identificadas 84 famílias Small com cinco réplicas e 120 famílias-base Large com seis variantes de número de fábricas (`F=2..7`).

A primeira versão da auditoria gerou 120 avisos de família porque exigia que o segundo campo do cabeçalho fosse constante dentro de cada família Large. Essa exigência estava incorreta: o campo representa `F` e deve variar entre as seis variantes. A regra foi removida do script; a verificação individual de que o valor de `F` corresponde ao sufixo do nome do arquivo permanece ativa. Portanto, os arquivos `families.csv`, `issues.csv` e `summary.json` da primeira execução devem ser regenerados com a versão corrigida do script.

A comparação dos hashes também mostrou que cada família Large mantém uma única matriz de processamento entre as seis variantes de `F`, como esperado ao reutilizar instâncias-base de Taillard. As due dates variam por variante, com uma exceção observada: em `Ta021` até `Ta030`, as variantes `F=6` e `F=7` possuem vetores de due dates idênticos. Isso é uma observação para investigação, não prova de erro no dataset.

## Referências do dataset

- Gogos, C. (2023). *Solving the Distributed Permutation Flow-Shop Scheduling Problem Using Constrained Programming*. Applied Sciences, 13(23), 12562. DOI: https://doi.org/10.3390/app132312562. O artigo documenta a estrutura dos benchmarks Small/Large e identifica explicitamente o segundo campo como número de fábricas.
- Khare, A. (2020). *DPFSP with due dates*. Mendeley Data, V1. DOI: https://doi.org/10.17632/4tkhdx4jjx.1. A descrição do dataset identifica-o como extensão do benchmark Naderi e Ruiz para DPFSP com due dates, destinado ao critério de total tardiness.

## Limites da auditoria

- A auditoria verifica sintaxe e consistência interna; não prova, por si só, a formulação matemática do problema.
- O segundo inteiro do cabeçalho não recebe interpretação sem documentação da fonte do dataset.
- A validação estrutural não demonstra que o motor legado implementa DPFSP-DD. Essa compatibilidade exige uma implementação/validação do modelo distribuído, incluindo atribuição de jobs às fábricas e cálculo do objetivo.
- Os resultados desta auditoria não alteram os arquivos originais nem os resultados experimentais históricos.
